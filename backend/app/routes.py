import os
import uuid
from pathlib import Path

from flask import (
    Blueprint,
    abort,
    current_app,
    jsonify,
    request,
    send_from_directory,
)
from werkzeug.exceptions import RequestEntityTooLarge
from werkzeug.utils import secure_filename

from app import db
from app.models import Movie, User
from app.auth import create_token, token_required

api = Blueprint("api", __name__, url_prefix="/api")


POSTER_MIME_TYPES = {
    "image/jpeg",
    "image/png",
    "image/webp",
}

TRAILER_MIME_TYPES = {
    "video/mp4",
    "video/webm",
    "video/quicktime",
}


def error_response(message, status_code):
    return jsonify({"error": message}), status_code


def allowed_extension(filename, allowed_extensions):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in allowed_extensions


def save_uploaded_file(file_storage, category):
    """
    Validate and save one poster or trailer.

    Returns a relative path such as:
        posters/uuid.jpg
        trailers/uuid.mp4
    """

    if not file_storage or not file_storage.filename:
        return None

    original_filename = secure_filename(file_storage.filename)

    if not original_filename:
        raise ValueError("Invalid filename.")

    if category == "posters":
        allowed_extensions = current_app.config["ALLOWED_POSTER_EXTENSIONS"]
        allowed_mime_types = POSTER_MIME_TYPES

    elif category == "trailers":
        allowed_extensions = current_app.config["ALLOWED_TRAILER_EXTENSIONS"]
        allowed_mime_types = TRAILER_MIME_TYPES

    else:
        raise ValueError("Unsupported upload category.")

    if not allowed_extension(original_filename, allowed_extensions):
        raise ValueError(f"Unsupported {category[:-1]} file extension.")

    # Browsers commonly provide a MIME type. This check is useful,
    # but it is not a guarantee that the file contents are genuine.
    if file_storage.mimetype not in allowed_mime_types:
        raise ValueError(f"Unsupported {category[:-1]} MIME type.")

    extension = original_filename.rsplit(".", 1)[1].lower()
    unique_filename = f"{uuid.uuid4().hex}.{extension}"

    upload_directory = Path(current_app.config["UPLOAD_FOLDER"]) / category
    upload_directory.mkdir(parents=True, exist_ok=True)

    destination = upload_directory / unique_filename
    file_storage.save(destination)

    return f"{category}/{unique_filename}"


def delete_uploaded_file(relative_path):
    """Delete a stored upload if it exists inside the configured folder."""

    if not relative_path:
        return

    upload_root = Path(current_app.config["UPLOAD_FOLDER"]).resolve()
    target = (upload_root / relative_path).resolve()

    # Prevent a database value from escaping the upload directory.
    if target == upload_root or upload_root not in target.parents:
        current_app.logger.warning("Refusing to delete a path outside upload storage.")
        return

    try:
        target.unlink(missing_ok=True)
    except OSError:
        current_app.logger.exception(
            "Could not delete uploaded file: %s",
            relative_path,
        )


def validate_movie_fields(data, partial=False):
    """
    Validate movie fields.

    When partial=True, only fields supplied by the client are updated.
    """

    allowed_fields = {
        "title",
        "year",
        "genre",
        "director",
        "rating",
    }

    unknown_fields = set(data.keys()) - allowed_fields

    if unknown_fields:
        raise ValueError(f"Unknown field(s): {', '.join(sorted(unknown_fields))}")

    cleaned = {}

    for field in ("title", "genre", "director"):
        if field in data:
            value = data[field]

            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{field.capitalize()} must not be empty.")

            cleaned[field] = value.strip()

        elif not partial:
            raise ValueError(f"{field.capitalize()} is required.")

    if "year" in data:
        try:
            year = int(data["year"])
        except (TypeError, ValueError):
            raise ValueError("Year must be a valid integer.")

        if year < 1888 or year > 2100:
            raise ValueError("Year must be between 1888 and 2100.")

        cleaned["year"] = year

    elif not partial:
        raise ValueError("Year is required.")

    if "rating" in data:
        try:
            rating = float(data["rating"])
        except (TypeError, ValueError):
            raise ValueError("Rating must be a valid number.")

        if not 0 <= rating <= 10:
            raise ValueError("Rating must be between 0 and 10.")

        cleaned["rating"] = rating

    elif not partial:
        raise ValueError("Rating is required.")

    return cleaned


def movie_response(movie, status_code=200):
    return jsonify(movie.to_dict()), status_code


@api.get("/health")
def health():
    return jsonify({"status": "ok"})

# =========================================================
# GENERAL
# =========================================================

@api.route("/", methods=["GET"])
def api_home():
    return jsonify({
        "message": "Movie Manager API is running"
    })


# =========================================================
# AUTHENTICATION
# =========================================================

@api.route("/auth/register", methods=["POST"])
def register():

    data = request.get_json()

    if not data:
        return jsonify({
            "error": "Request body must contain JSON"
        }), 400

    username = data.get("username", "").strip()
    password = data.get("password", "")

    if not username or not password:
        return jsonify({
            "error": "Username and password are required"
        }), 400

    if len(username) < 3:
        return jsonify({
            "error": "Username must contain at least 3 characters"
        }), 400

    if len(password) < 6:
        return jsonify({
            "error": "Password must contain at least 6 characters"
        }), 400

    existing_user = User.query.filter_by(
        username=username
    ).first()

    if existing_user:
        return jsonify({
            "error": "Username already exists"
        }), 409

    user = User(username=username)
    user.set_password(password)

    db.session.add(user)
    db.session.commit()

    token = create_token(user.id)

    return jsonify({
        "message": "Registration successful",
        "token": token,
        "user": user.to_dict()
    }), 201


@api.route("/auth/login", methods=["POST"])
def login():

    data = request.get_json()

    if not data:
        return jsonify({
            "error": "Request body must contain JSON"
        }), 400

    username = data.get("username", "").strip()
    password = data.get("password", "")

    if not username or not password:
        return jsonify({
            "error": "Username and password are required"
        }), 400

    user = User.query.filter_by(
        username=username
    ).first()

    if not user or not user.check_password(password):
        return jsonify({
            "error": "Invalid username or password"
        }), 401

    token = create_token(user.id)

    return jsonify({
        "message": "Login successful",
        "token": token,
        "user": user.to_dict()
    })


@api.route("/auth/me", methods=["GET"])
@token_required
def current_user(user):

    return jsonify({
        "user": user.to_dict()
    })


# =========================================================
# MOVIES
# =========================================================

@api.get("/movies")
def get_movies():
    search_term = request.args.get("search", "").strip()
    genre = request.args.get("genre", "").strip()

    query = Movie.query

    if search_term:
        query = query.filter(Movie.title.ilike(f"%{search_term}%"))

    if genre:
        query = query.filter(Movie.genre.ilike(genre))

    movies = query.order_by(Movie.id.desc()).all()

    return jsonify([movie.to_dict() for movie in movies])


@api.get("/movies/<int:movie_id>")
def get_movie(movie_id):
    movie = db.session.get(Movie, movie_id)

    if movie is None:
        return error_response("Movie not found.", 404)

    return movie_response(movie)

# =========================================================
# CREATE MOVIE
# =========================================================

@api.post("/movies")
@token_required
def create_movie(user):
    data = request.form

    try:
        fields = validate_movie_fields(data)
    except ValueError as exc:
        return error_response(str(exc), 400)

    poster = request.files.get("poster")
    trailer = request.files.get("trailer")

    saved_files = []

    try:
        poster_filename = save_uploaded_file(poster, "posters")
        if poster_filename:
            saved_files.append(poster_filename)

        trailer_filename = save_uploaded_file(trailer, "trailers")
        if trailer_filename:
            saved_files.append(trailer_filename)

        movie = Movie(
            **fields,
            poster_filename=poster_filename,
            trailer_filename=trailer_filename,
        )

        db.session.add(movie)
        db.session.commit()

    except ValueError as exc:
        db.session.rollback()

        for relative_path in saved_files:
            delete_uploaded_file(relative_path)

        return error_response(str(exc), 400)

    except Exception:
        db.session.rollback()

        for relative_path in saved_files:
            delete_uploaded_file(relative_path)

        current_app.logger.exception("Failed to create movie.")
        return error_response("Could not create movie.", 500)

    return movie_response(movie, 201)


# =========================================================
# UPDATE MOVIE
# =========================================================

@api.put("/movies/<int:movie_id>")
@token_required
def update_movie(user, movie_id):
    movie = db.session.get(Movie, movie_id)

    if movie is None:
        return error_response("Movie not found.", 404)

    data = request.form

    try:
        fields = validate_movie_fields(data, partial=True)
    except ValueError as exc:
        return error_response(str(exc), 400)

    poster = request.files.get("poster")
    trailer = request.files.get("trailer")

    newly_saved_files = []
    old_files_to_delete = []

    try:
        for field, value in fields.items():
            setattr(movie, field, value)

        if poster and poster.filename:
            new_poster = save_uploaded_file(poster, "posters")

            if new_poster:
                newly_saved_files.append(new_poster)

                if movie.poster_filename:
                    old_files_to_delete.append(movie.poster_filename)

                movie.poster_filename = new_poster

        if trailer and trailer.filename:
            new_trailer = save_uploaded_file(trailer, "trailers")

            if new_trailer:
                newly_saved_files.append(new_trailer)

                if movie.trailer_filename:
                    old_files_to_delete.append(movie.trailer_filename)

                movie.trailer_filename = new_trailer

        db.session.commit()

    except ValueError as exc:
        db.session.rollback()

        for relative_path in newly_saved_files:
            delete_uploaded_file(relative_path)

        return error_response(str(exc), 400)

    except Exception:
        db.session.rollback()

        for relative_path in newly_saved_files:
            delete_uploaded_file(relative_path)

        current_app.logger.exception("Failed to update movie.")
        return error_response("Could not update movie.", 500)

    # Delete old files only after the database update succeeds.
    for relative_path in old_files_to_delete:
        delete_uploaded_file(relative_path)

    return movie_response(movie)

# =========================================================
# DELETE MOVIE
# =========================================================

@api.delete("/movies/<int:movie_id>")
@token_required
def delete_movie(user, movie_id):
    movie = db.session.get(Movie, movie_id)

    if movie is None:
        return error_response("Movie not found.", 404)

    poster_filename = movie.poster_filename
    trailer_filename = movie.trailer_filename

    try:
        db.session.delete(movie)
        db.session.commit()

    except Exception:
        db.session.rollback()
        current_app.logger.exception("Failed to delete movie.")
        return error_response("Could not delete movie.", 500)

    # Remove the physical files after the database transaction succeeds.
    delete_uploaded_file(poster_filename)
    delete_uploaded_file(trailer_filename)

    return jsonify({"message": "Movie deleted successfully."})



@api.get("/uploads/<path:filename>")
def get_uploaded_file(filename):
    """
    Serve a stored poster or trailer.

    Only serve paths beneath the configured uploads directory.
    """

    safe_filename = secure_filename(Path(filename).name)
    parent = Path(filename).parent.as_posix()

    if parent not in {"posters", "trailers"}:
        abort(404)

    if not safe_filename or safe_filename != Path(filename).name:
        abort(404)

    return send_from_directory(
        current_app.config["UPLOAD_FOLDER"],
        f"{parent}/{safe_filename}",
        conditional=True,
    )


@api.errorhandler(RequestEntityTooLarge)
def handle_large_upload(error):
    return error_response(
        "The uploaded request is too large. Reduce the file size and try again.",
        413,
    )
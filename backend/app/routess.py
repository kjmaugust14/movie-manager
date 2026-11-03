from flask import Blueprint, request, jsonify

from app import db
from app.models import Movie, User
from app.auth import create_token, token_required


api = Blueprint(
    "api",
    __name__,
    url_prefix="/api"
)


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

@api.route("/movies", methods=["GET"])
def get_movies():

    search = request.args.get(
        "search",
        "",
        type=str
    ).strip()

    genre = request.args.get(
        "genre",
        "",
        type=str
    ).strip()

    query = Movie.query

    if search:
        query = query.filter(
            db.or_(
                Movie.title.ilike(f"%{search}%"),
                Movie.director.ilike(f"%{search}%")
            )
        )

    if genre:
        query = query.filter(
            Movie.genre.ilike(genre)
        )

    movies = query.order_by(
        Movie.id.desc()
    ).all()

    return jsonify([
        movie.to_dict()
        for movie in movies
    ])


@api.route("/movies/<int:movie_id>", methods=["GET"])
def get_movie(movie_id):

    movie = Movie.query.get(movie_id)

    if not movie:
        return jsonify({
            "error": "Movie not found"
        }), 404

    return jsonify(movie.to_dict())


# =========================================================
# CREATE MOVIE
# =========================================================

@api.route("/movies", methods=["POST"])
@token_required
def create_movie(user):

    data = request.get_json()

    if not data:
        return jsonify({
            "error": "Request body must contain JSON"
        }), 400

    error = validate_movie_data(data)

    if error:
        return jsonify({
            "error": error
        }), 400

    movie = Movie(
        title=data["title"].strip(),
        year=data["year"],
        genre=data["genre"].strip(),
        director=data["director"].strip(),
        rating=data["rating"]
    )

    db.session.add(movie)
    db.session.commit()

    return jsonify({
        "message": "Movie created successfully",
        "movie": movie.to_dict()
    }), 201


# =========================================================
# UPDATE MOVIE
# =========================================================

@api.route("/movies/<int:movie_id>", methods=["PUT"])
@token_required
def update_movie(user, movie_id):

    movie = Movie.query.get(movie_id)

    if not movie:
        return jsonify({
            "error": "Movie not found"
        }), 404

    data = request.get_json()

    if not data:
        return jsonify({
            "error": "Request body must contain JSON"
        }), 400

    error = validate_movie_data(data)

    if error:
        return jsonify({
            "error": error
        }), 400

    movie.title = data["title"].strip()
    movie.year = data["year"]
    movie.genre = data["genre"].strip()
    movie.director = data["director"].strip()
    movie.rating = data["rating"]

    db.session.commit()

    return jsonify({
        "message": "Movie updated successfully",
        "movie": movie.to_dict()
    })


# =========================================================
# DELETE MOVIE
# =========================================================

@api.route("/movies/<int:movie_id>", methods=["DELETE"])
@token_required
def delete_movie(user, movie_id):

    movie = Movie.query.get(movie_id)

    if not movie:
        return jsonify({
            "error": "Movie not found"
        }), 404

    db.session.delete(movie)
    db.session.commit()

    return jsonify({
        "message": "Movie deleted successfully"
    })


# =========================================================
# VALIDATION
# =========================================================

def validate_movie_data(data):

    required_fields = [
        "title",
        "year",
        "genre",
        "director",
        "rating"
    ]

    for field in required_fields:
        if field not in data:
            return f"{field} is required"

    title = str(data["title"]).strip()
    genre = str(data["genre"]).strip()
    director = str(data["director"]).strip()

    if not title:
        return "Title cannot be empty"

    if not genre:
        return "Genre cannot be empty"

    if not director:
        return "Director cannot be empty"

    try:
        year = int(data["year"])
    except (ValueError, TypeError):
        return "Year must be a valid number"

    if year < 1888 or year > 2100:
        return "Year must be between 1888 and 2100"

    try:
        rating = float(data["rating"])
    except (ValueError, TypeError):
        return "Rating must be a valid number"

    if rating < 0 or rating > 10:
        return "Rating must be between 0 and 10"

    # Replace the original values with validated values.
    data["year"] = year
    data["rating"] = rating

    return None
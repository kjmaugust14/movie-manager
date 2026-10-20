from functools import wraps
from datetime import datetime, timedelta, timezone

import jwt

from flask import current_app, request, jsonify

from app.models import User


def create_token(user_id):
    payload = {
        "user_id": user_id,
        "exp": datetime.now(timezone.utc) + timedelta(hours=2)
    }

    token = jwt.encode(
        payload,
        current_app.config["JWT_SECRET_KEY"],
        algorithm="HS256"
    )

    return token


def token_required(function):
    @wraps(function)
    def decorated(*args, **kwargs):

        auth_header = request.headers.get("Authorization")

        if not auth_header:
            return jsonify({
                "error": "Authorization header is required"
            }), 401

        try:
            parts = auth_header.split()

            if len(parts) != 2 or parts[0].lower() != "bearer":
                raise ValueError("Invalid authorization format")

            token = parts[1]

            payload = jwt.decode(
                token,
                current_app.config["JWT_SECRET_KEY"],
                algorithms=["HS256"]
            )

            user = User.query.get(payload["user_id"])

            if not user:
                return jsonify({
                    "error": "User not found"
                }), 401

        except jwt.ExpiredSignatureError:
            return jsonify({
                "error": "Token has expired"
            }), 401

        except jwt.InvalidTokenError:
            return jsonify({
                "error": "Invalid token"
            }), 401

        except Exception:
            return jsonify({
                "error": "Invalid authorization header"
            }), 401

        return function(user, *args, **kwargs)

    return decorated
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS

from config import Config

db = SQLAlchemy()


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)

    # Allow the separate frontend to communicate
    # with the Flask API.
    CORS(
        app,
        resources={
            r"/api/*": {
                "origins": [
                    "http://localhost:5500",
                    "http://127.0.0.1:5500",
                    "https://movie-manager-ashy.vercel.app"
                ],
                "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
                "allow_headers": ["Content-Type", "Authorization"]
            }
        }
    )

    from app.routes import api
    app.register_blueprint(api)

    with app.app_context():
        db.create_all()

    return app
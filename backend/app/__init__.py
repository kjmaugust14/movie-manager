import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS
from config import Config

db = SQLAlchemy()
migrate = Migrate()

def create_app():
    app = Flask(__name__, instance_relative_config=True)

    os.makedirs(app.instance_path, exist_ok=True)
    
    app.config.from_object("config.Config")

    upload_folder = app.config["UPLOAD_FOLDER"]
    os.makedirs(os.path.join(upload_folder, "posters"), exist_ok=True)
    os.makedirs(os.path.join(upload_folder, "trailers"), exist_ok=True)

    db.init_app(app)

    migrate.init_app(app, db)

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

    from app import models #noqa: F401
    from app.routes import api
    app.register_blueprint(api)

    # with app.app_context():
    #     db.create_all()

    return app
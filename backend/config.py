import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Get the path to the backend folder
BASE_DIR = Path(__file__).resolve().parent

# Get the path to the instance folder
INSTANCE_DIR = BASE_DIR / "instance"


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "my-secret-key")

    JWT_SECRET_KEY = os.getenv(
        "JWT_SECRET_KEY",
        "my-jwt-secret-key"
    )

    # Read DATABASE_URL from Render, fallback to local SQLite
    database_url = os.getenv(
        "DATABASE_URL",
        f"sqlite:///{(INSTANCE_DIR / 'moviez.db').as_posix()}"
    )

    # Render sometimes provides 'postgres://' instead of 'postgresql://'
    if database_url and database_url.startswith("postgres://"):
        database_url = database_url.replace(
            "postgres://",
            "postgresql://",
            1
        )

    SQLALCHEMY_DATABASE_URI = database_url
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # File upload configuration
    UPLOAD_FOLDER = os.getenv(
        "UPLOAD_FOLDER",
        str(INSTANCE_DIR / "uploads")
    )

    # Maximum total request size: 110 MB
    MAX_CONTENT_LENGTH = 110 * 1024 * 1024

    # Allowed file extensions
    ALLOWED_POSTER_EXTENSIONS = {"jpg", "jpeg", "png", "webp"}
    ALLOWED_TRAILER_EXTENSIONS = {"mp4", "webm", "mov"}
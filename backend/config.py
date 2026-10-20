import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "my-secret-key")

    JWT_SECRET_KEY = os.getenv(
        "JWT_SECRET_KEY",
        "my-jwt-secret-key"
    )

    # Read DATABASE_URL from Render, fallback to local SQLite 
    database_url = os.getenv('DATABASE_URL', "sqlite:///moviez.db")

    # Render sometimes provides 'postgres://' which SQLAlchemy needs as 'postgresql://'
    if database_url and database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)

    SQLALCHEMY_DATABASE_URI = database_url
    SQLALCHEMY_TRACK_MODIFICATIONS = False
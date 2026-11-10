"""INFRASTRUCTURE: settings from .env. The only module that reads environment variables."""

import os

from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.environ["DATABASE_URL"]
JWT_SECRET_KEY = os.environ["JWT_SECRET_KEY"]
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_MINUTES = 15
STRIPE_SECRET_KEY = os.environ.get("STRIPE_SECRET_KEY", "")   # sk_test_... in .env
MONGODB_URL = os.environ.get("MONGODB_URL", "mongodb://localhost:27017")  # the Docker container
MONGODB_DB = os.environ.get("MONGODB_DB", "auth_api")

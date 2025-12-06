from flask import Blueprint
from src.config import config

# Blueprint for authentication related endpoints
auth_bp = Blueprint("auth", __name__, url_prefix=config.AUTH_API_PREFIX)

# Import routes so that they are registered with the blueprint
from src.auth import routes  # noqa: E402,F401


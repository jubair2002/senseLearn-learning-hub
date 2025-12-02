from flask import Blueprint

# Blueprint for authentication related endpoints
auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")

# Import routes so that they are registered with the blueprint
from src.auth import routes  # noqa: E402,F401


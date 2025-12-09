from flask import Blueprint, request
from src.config import config

# Blueprint for authentication related endpoints
auth_bp = Blueprint("auth", __name__, url_prefix=config.AUTH_API_PREFIX)

# Prevent Flask from trying to parse JSON for multipart/form-data requests
@auth_bp.before_request
def prevent_json_parsing_for_multipart():
    """Prevent Flask from trying to parse JSON when Content-Type is multipart/form-data."""
    if request.method == 'POST':
        content_type = request.headers.get('Content-Type', '').lower()
        if 'multipart/form-data' in content_type:
            # Tell Flask not to parse JSON for this request
            # This prevents 415 errors
            request._cached_json = None

# Import routes so that they are registered with the blueprint
from src.auth import routes  # noqa: E402,F401


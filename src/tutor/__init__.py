from flask import Blueprint
from src.config import config

tutor_bp = Blueprint('tutor', __name__, url_prefix=config.TUTOR_URL_PREFIX)

from src.tutor import routes
from src.tutor import course_routes  # Import course routes separately
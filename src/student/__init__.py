from flask import Blueprint
from src.config import config

student_bp = Blueprint('student', __name__, url_prefix=config.STUDENT_URL_PREFIX)

from src.student import routes
from flask import Blueprint
from src.config import config

tutor_bp = Blueprint('tutor', __name__, url_prefix='/tutor')

from src.tutor import routes
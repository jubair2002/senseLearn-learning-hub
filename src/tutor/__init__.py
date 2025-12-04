from flask import Blueprint

tutor_bp = Blueprint('tutor', __name__, url_prefix='/tutor')

from src.tutor import routes
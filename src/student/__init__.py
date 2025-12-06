from flask import Blueprint
from src.config import config

student_bp = Blueprint('student', __name__, url_prefix='/student')

from src.student import routes
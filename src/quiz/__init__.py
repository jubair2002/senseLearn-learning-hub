"""
Quiz module for creating and managing quizzes within courses.

This module provides functionality for tutors to create quizzes
and for students to take quizzes with automatic grading.
"""
from flask import Blueprint
from src.config import config

quiz_bp = Blueprint('quiz', __name__, url_prefix='/quiz')

from src.quiz import tutor_routes  # Import tutor routes


"""
Chatbot module for student assistance.

This module provides a chatbot interface for students to get help
with their courses, learning materials, and general questions.
"""
from flask import Blueprint
from src.config import config

chatbot_bp = Blueprint('chatbot', __name__, url_prefix='/student/chatbot')

from src.chatbot import routes


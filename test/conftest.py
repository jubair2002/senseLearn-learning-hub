# test/conftest.py
import pytest
import os
from src import create_app, db  # Import the real db from src/__init__.py

@pytest.fixture(scope='session')
def app():
    """Create Flask app for testing with SQLite in-memory DB."""
    
    os.environ['FLASK_ENV'] = 'testing'
    os.environ['SECRET_KEY'] = 'test-secret-key'
    
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    
    # Create tables for testing
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture(scope='function')
def client(app):
    """Flask test client."""
    return app.test_client()

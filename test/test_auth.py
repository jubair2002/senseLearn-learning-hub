"""
Test cases for authentication functionality - Basic endpoint tests.
"""
import pytest
from flask import json


class TestUserRegistration:
    """Test cases for user registration endpoints."""
    
    def test_register_endpoint_exists(self, client):
        """Test registration endpoint is accessible."""
        response = client.post('/api/auth/register', json={
            'email': 'test@test.com',
            'password': 'password123',
            'full_name': 'Test User',
            'user_type': 'student',
            'disability_type': 'Deaf'
        })
        # Should return 200 (success) or 400/409 (validation error), not 404
        assert response.status_code != 404
    
    def test_register_missing_fields(self, client):
        """Test registration with missing required fields."""
        response = client.post('/api/auth/register', json={
            'email': 'test@test.com'
            # Missing password, full_name, etc.
        })
        assert response.status_code == 400
    
    def test_register_invalid_email(self, client):
        """Test registration with invalid email."""
        response = client.post('/api/auth/register', json={
            'email': 'invalid-email',
            'password': 'password123',
            'full_name': 'Test User',
            'user_type': 'student',
            'disability_type': 'Deaf'
        })
        assert response.status_code == 400
    
    def test_register_invalid_password(self, client):
        """Test registration with invalid password."""
        response = client.post('/api/auth/register', json={
            'email': 'test@test.com',
            'password': '123',  # Too short
            'full_name': 'Test User',
            'user_type': 'student',
            'disability_type': 'Deaf'
        })
        assert response.status_code == 400


class TestUserLogin:
    """Test cases for user login endpoints."""
    
    def test_login_endpoint_exists(self, client):
        """Test login endpoint is accessible."""
        response = client.post('/api/auth/login', json={
            'email': 'test@test.com',
            'password': 'password123'
        })
        # Should return 200 (success) or 401 (invalid), not 404
        assert response.status_code != 404
    
    def test_login_missing_fields(self, client):
        """Test login with missing fields."""
        response = client.post('/api/auth/login', json={
            'email': 'test@test.com'
            # Missing password
        })
        assert response.status_code == 400
    
    def test_login_invalid_email_format(self, client):
        """Test login with invalid email format."""
        response = client.post('/api/auth/login', json={
            'email': 'invalid-email',
            'password': 'password123'
        })
        assert response.status_code == 400


class TestPasswordReset:
    """Test cases for password reset endpoints."""
    
    def test_forgot_password_endpoint_exists(self, client):
        """Test forgot password endpoint is accessible."""
        response = client.post('/api/auth/forgot', json={
            'email': 'test@test.com'
        })
        # Should return 200 (always returns success for security), not 404
        assert response.status_code != 404
    
    def test_forgot_password_missing_email(self, client):
        """Test forgot password without email."""
        response = client.post('/api/auth/forgot', json={})
        assert response.status_code == 400
    
    def test_reset_password_endpoint_exists(self, client):
        """Test reset password endpoint is accessible."""
        response = client.post('/api/auth/reset', json={
            'email': 'test@test.com',
            'otp': '123456',
            'new_password': 'newpassword123'
        })
        # Should return 200 (success) or 400 (invalid), not 404
        assert response.status_code != 404
    
    def test_reset_password_missing_fields(self, client):
        """Test reset password with missing fields."""
        response = client.post('/api/auth/reset', json={
            'email': 'test@test.com'
            # Missing otp and new_password
        })
        assert response.status_code == 400


class TestEmailVerification:
    """Test cases for email verification endpoints."""
    
    def test_verify_email_endpoint_exists(self, client):
        """Test verify email endpoint is accessible."""
        response = client.post('/api/auth/verify-email', json={
            'email': 'test@test.com',
            'otp': '123456'
        })
        # Should return 201 (success) or 400 (invalid), not 404
        assert response.status_code != 404
    
    def test_verify_email_missing_fields(self, client):
        """Test verify email with missing fields."""
        response = client.post('/api/auth/verify-email', json={
            'email': 'test@test.com'
            # Missing otp
        })
        assert response.status_code == 400
    
    def test_resend_otp_endpoint_exists(self, client):
        """Test resend OTP endpoint is accessible."""
        response = client.post('/api/auth/resend-otp', json={
            'email': 'test@test.com',
            'purpose': 'verification'
        })
        # Should return 200 (success) or 400 (invalid), not 404
        assert response.status_code != 404

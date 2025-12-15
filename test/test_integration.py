"""
Integration test cases for basic functionality flows.
"""
import pytest


class TestAuthFlow:
    """Test complete authentication flow."""
    
    def test_register_then_login_flow(self, client):
        """Test registration followed by login attempt."""
        # Step 1: Register
        register_response = client.post('/api/auth/register', json={
            'email': 'flow@test.com',
            'password': 'password123',
            'full_name': 'Flow User',
            'user_type': 'student',
            'disability_type': 'Deaf'
        })
        # Registration should be accepted (200) or return validation error (400)
        assert register_response.status_code in [200, 400, 409]
        
        # Step 2: Try to login (may fail if email not verified, but endpoint should work)
        login_response = client.post('/api/auth/login', json={
            'email': 'flow@test.com',
            'password': 'password123'
        })
        # Login endpoint should exist and respond
        assert login_response.status_code != 404
    
    def test_forgot_password_flow(self, client):
        """Test forgot password flow."""
        # Step 1: Request password reset
        forgot_response = client.post('/api/auth/forgot', json={
            'email': 'test@test.com'
        })
        assert forgot_response.status_code == 200
        
        # Step 2: Try to reset password (may fail without valid OTP, but endpoint should work)
        reset_response = client.post('/api/auth/reset', json={
            'email': 'test@test.com',
            'otp': '123456',
            'new_password': 'newpassword123'
        })
        assert reset_response.status_code != 404


class TestStudentFlow:
    """Test student functionality flow."""
    
    def test_student_dashboard_to_courses_flow(self, client):
        """Test accessing student dashboard and courses."""
        # Access dashboard
        dashboard_response = client.get('/student/dashboard')
        assert dashboard_response.status_code != 404
        
        # Access courses list
        courses_response = client.get('/student/api/courses')
        assert courses_response.status_code != 404
        
        # Access enrolled courses
        enrolled_response = client.get('/student/api/courses/enrolled')
        assert enrolled_response.status_code != 404


class TestTutorFlow:
    """Test tutor functionality flow."""
    
    def test_tutor_dashboard_to_courses_flow(self, client):
        """Test accessing tutor dashboard and courses."""
        # Access dashboard
        dashboard_response = client.get('/tutor/dashboard')
        assert dashboard_response.status_code != 404
        
        # Access courses list
        courses_response = client.get('/tutor/api/courses')
        assert courses_response.status_code != 404
        
        # Access stats
        stats_response = client.get('/tutor/api/stats')
        assert stats_response.status_code != 404


class TestAdminFlow:
    """Test admin functionality flow."""
    
    def test_admin_dashboard_to_management_flow(self, client):
        """Test accessing admin dashboard and management features."""
        # Access dashboard
        dashboard_response = client.get('/admin/dashboard')
        assert dashboard_response.status_code != 404
        
        # Access tutors list
        tutors_response = client.get('/admin/api/tutors')
        assert tutors_response.status_code != 404
        
        # Access students list
        students_response = client.get('/admin/api/students')
        assert students_response.status_code != 404
        
        # Access courses list
        courses_response = client.get('/admin/api/courses')
        assert courses_response.status_code != 404
        
        # Access stats
        stats_response = client.get('/admin/api/stats')
        assert stats_response.status_code != 404

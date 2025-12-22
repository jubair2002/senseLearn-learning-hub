"""
Test cases for admin functionality - Basic endpoint tests.
"""
import pytest


class TestAdminDashboard:
    """Test cases for admin dashboard."""
    
    def test_admin_dashboard_endpoint_exists(self, client):
        """Test admin dashboard endpoint is accessible."""
        response = client.get('/admin/dashboard')
        # Should redirect to login if not authenticated, but endpoint exists
        assert response.status_code in [200, 302, 401, 403]
    
    def test_admin_api_tutors_endpoint_exists(self, client):
        """Test admin tutors API endpoint exists."""
        response = client.get('/admin/api/tutors')
        # Should return 401/403 if not authenticated, but endpoint exists
        assert response.status_code != 404
    
    def test_admin_api_students_endpoint_exists(self, client):
        """Test admin students API endpoint exists."""
        response = client.get('/admin/api/students')
        # Should return 401/403 if not authenticated, but endpoint exists
        assert response.status_code != 404
    
    def test_admin_api_stats_endpoint_exists(self, client):
        """Test admin stats API endpoint exists."""
        response = client.get('/admin/api/stats')
        # Should return 401/403 if not authenticated, but endpoint exists
        assert response.status_code != 404


class TestAdminUserManagement:
    """Test cases for user management endpoints."""
    
    def test_verify_tutor_endpoint_exists(self, client):
        """Test verify tutor endpoint exists."""
        response = client.post('/admin/api/verify-tutor', json={
            'tutor_id': 1,
            'verify': True
        })
        # Should return 401/403 if not authenticated, but endpoint exists
        assert response.status_code != 404
    
    def test_create_account_endpoint_exists(self, client):
        """Test create account endpoint exists."""
        response = client.post('/admin/api/create-account', json={
            'user_type': 'student',
            'email': 'test@test.com',
            'full_name': 'Test User',
            'disability_type': 'Deaf'
        })
        # Should return 401/403 if not authenticated, but endpoint exists
        assert response.status_code != 404


class TestAdminCourseManagement:
    """Test cases for course management endpoints."""
    
    def test_list_courses_endpoint_exists(self, client):
        """Test list courses endpoint exists."""
        response = client.get('/admin/api/courses')
        # Should return 401/403 if not authenticated, but endpoint exists
        assert response.status_code != 404
    
    def test_create_course_endpoint_exists(self, client):
        """Test create course endpoint exists."""
        response = client.post('/admin/api/courses', json={
            'name': 'Test Course',
            'description': 'Test',
            'target_disability_types': 'Deaf'
        })
        # Should return 401/403 if not authenticated, but endpoint exists
        assert response.status_code != 404
    
    def test_get_course_details_endpoint_exists(self, client):
        """Test get course details endpoint exists."""
        response = client.get('/admin/api/courses/1')
        # Should return 401/403 if not authenticated, but endpoint exists
        assert response.status_code != 404
    
    def test_assign_tutors_endpoint_exists(self, client):
        """Test assign tutors endpoint exists."""
        response = client.post('/admin/api/courses/1/tutors', json={
            'tutor_ids': [1]
        })
        # Should return 401/403 if not authenticated, but endpoint exists
        assert response.status_code != 404
    
    def test_assign_students_endpoint_exists(self, client):
        """Test assign students endpoint exists."""
        response = client.post('/admin/api/courses/1/students', json={
            'student_ids': [1]
        })
        # Should return 401/403 if not authenticated, but endpoint exists
        assert response.status_code != 404

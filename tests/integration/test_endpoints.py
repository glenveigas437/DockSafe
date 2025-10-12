"""
Integration tests for DockSafe API endpoints.
"""

import pytest
import json
from unittest.mock import patch, MagicMock


class TestAuthEndpoints:
    """Test authentication endpoints."""
    
    def test_login_page(self, client):
        """Test login page loads correctly."""
        response = client.get('/auth/login')
        assert response.status_code == 200
        assert b'DockSafe' in response.data
        assert b'Continue with Google' in response.data
    
    def test_register_page(self, client):
        """Test register page redirects to login (since we use Google OAuth)."""
        response = client.get('/auth/register')
        assert response.status_code == 302  # Redirect to login
        assert '/auth/login' in response.location
    
    @patch('app.auth.google_oauth.GoogleOAuthService')
    def test_google_login(self, mock_oauth, client):
        """Test Google OAuth login initiation."""
        mock_oauth_instance = MagicMock()
        mock_oauth_instance.get_authorization_url.return_value = 'https://accounts.google.com/oauth/authorize'
        mock_oauth.return_value = mock_oauth_instance
        
        response = client.get('/auth/google/login')
        assert response.status_code == 302  # Redirect to Google OAuth
    
    def test_logout(self, client):
        """Test logout functionality."""
        response = client.post('/auth/logout')  # Use POST method
        assert response.status_code == 302  # Redirect after logout
    
    def test_profile_page_requires_auth(self, client):
        """Test profile page requires authentication."""
        response = client.get('/auth/profile')
        assert response.status_code == 302  # Redirect to login


class TestDashboardEndpoints:
    """Test dashboard endpoints."""
    
    def test_dashboard_requires_auth(self, client):
        """Test dashboard requires authentication."""
        response = client.get('/dashboard/')
        assert response.status_code == 302  # Redirect to login
    
    def test_dashboard_chart_data_requires_auth(self, client):
        """Test dashboard chart data requires authentication."""
        response = client.get('/dashboard/chart-data')
        assert response.status_code == 302  # Redirect to login


class TestScannerEndpoints:
    """Test scanner endpoints."""
    
    def test_scanner_page_requires_auth(self, client):
        """Test scanner page requires authentication."""
        response = client.get('/scanner/')
        assert response.status_code == 302  # Redirect to login
    
    def test_scan_endpoint_requires_auth(self, client):
        """Test scan endpoint requires authentication."""
        response = client.post('/scanner/scan', json={
            'image_name': 'nginx',
            'image_tag': 'latest'
        })
        assert response.status_code == 302  # Redirect to login


class TestReportsEndpoints:
    """Test reports endpoints."""
    
    def test_reports_page_requires_auth(self, client):
        """Test reports page requires authentication."""
        response = client.get('/reports/')
        assert response.status_code == 302  # Redirect to login
    
    def test_reports_api_requires_auth(self, client):
        """Test reports API requires authentication."""
        response = client.get('/reports/api')
        assert response.status_code == 302  # Redirect to login


class TestGroupsEndpoints:
    """Test groups endpoints."""
    
    def test_groups_page_requires_auth(self, client):
        """Test groups page requires authentication."""
        response = client.get('/groups/')
        assert response.status_code == 302  # Redirect to login
    
    def test_create_group_requires_auth(self, client):
        """Test create group requires authentication."""
        response = client.post('/groups/create', json={
            'name': 'Test Group',
            'description': 'A test group'
        })
        assert response.status_code == 302  # Redirect to login


class TestNotificationsEndpoints:
    """Test notifications endpoints."""
    
    def test_notifications_page_requires_auth(self, client):
        """Test notifications page requires authentication."""
        response = client.get('/notifications/')
        assert response.status_code == 302  # Redirect to login
    
    def test_notification_settings_requires_auth(self, client):
        """Test notification settings requires authentication."""
        response = client.get('/notifications/settings')
        assert response.status_code == 302  # Redirect to login


class TestHealthEndpoint:
    """Test health check endpoint."""
    
    def test_health_check(self, client):
        """Test health check endpoint."""
        response = client.get('/health')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['status'] == 'healthy'
        assert 'timestamp' in data
        assert 'version' in data
        assert 'services' in data


class TestMainEndpoints:
    """Test main application endpoints."""
    
    def test_home_page_requires_auth(self, client):
        """Test home page requires authentication."""
        response = client.get('/')
        assert response.status_code == 302  # Redirect to login
    
    def test_about_page_requires_auth(self, client):
        """Test about page requires authentication."""
        response = client.get('/about')
        assert response.status_code == 302  # Redirect to login


class TestAuthenticatedEndpoints:
    """Test endpoints that require authentication."""
    
    def test_dashboard_with_auth(self, client, sample_user, sample_group, sample_scan):
        """Test dashboard with authenticated user."""
        with client.session_transaction() as sess:
            sess['user_id'] = sample_user
            sess['selected_group_id'] = sample_group
        
        response = client.get('/dashboard/')
        assert response.status_code == 200
        assert b'Dashboard' in response.data
    
    def test_scanner_with_auth(self, client, sample_user, sample_group):
        """Test scanner page with authenticated user."""
        with client.session_transaction() as sess:
            sess['user_id'] = sample_user
            sess['selected_group_id'] = sample_group
        
        response = client.get('/scanner/')
        assert response.status_code == 200
        assert b'Scanner' in response.data
    
    def test_reports_with_auth(self, client, sample_user, sample_group):
        """Test reports page with authenticated user."""
        with client.session_transaction() as sess:
            sess['user_id'] = sample_user
            sess['selected_group_id'] = sample_group
        
        response = client.get('/reports/')
        assert response.status_code == 200
        assert b'Reports' in response.data
    
    def test_groups_with_auth(self, client, sample_user):
        """Test groups page with authenticated user."""
        with client.session_transaction() as sess:
            sess['user_id'] = sample_user  # sample_user is now an ID
        
        response = client.get('/groups/')
        assert response.status_code == 200
        assert b'Groups' in response.data
    
    def test_notifications_with_auth(self, client, sample_user, sample_group):
        """Test notifications page with authenticated user."""
        with client.session_transaction() as sess:
            sess['user_id'] = sample_user  # sample_user is now an ID
            sess['selected_group_id'] = sample_group  # sample_group is now an ID
        
        response = client.get('/notifications/')
        assert response.status_code == 200
        assert b'Notifications' in response.data
    
    def test_home_with_auth(self, client, sample_user, sample_group):
        """Test home page with authenticated user."""
        with client.session_transaction() as sess:
            sess['user_id'] = sample_user  # sample_user is now an ID
            sess['selected_group_id'] = sample_group  # sample_group is now an ID
        
        response = client.get('/')
        assert response.status_code == 200
        assert b'DockSafe' in response.data

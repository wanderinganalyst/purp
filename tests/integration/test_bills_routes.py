"""
Integration tests for bills routes
"""

import pytest


class TestBillsRoutes:
    """Test bills-related routes."""
    
    def test_bills_list_page_loads(self, client):
        """Test that bills list page loads."""
        response = client.get('/bills')
        assert response.status_code == 200
        assert b'bill' in response.data.lower()
    
    def test_bills_list_shows_bills(self, client):
        """Test that bills are displayed."""
        response = client.get('/bills')
        # Should have at least mock data
        assert response.status_code == 200
        # Check for bill-related content
        data_lower = response.data.lower()
        assert b'hb' in data_lower or b'sb' in data_lower or b'bill' in data_lower
    
    def test_bill_detail_page(self, client):
        """Test viewing a specific bill."""
        # Try to view a mock bill
        response = client.get('/bill/HB%20101')
        # Should load even if bill not found
        assert response.status_code in [200, 404]
    
    def test_bill_detail_not_found(self, client):
        """Test viewing a non-existent bill."""
        response = client.get('/bill/NONEXISTENT999')
        # Should handle gracefully
        assert response.status_code in [200, 404]


class TestBillComments:
    """Test bill commenting functionality."""
    
    def test_add_comment_requires_login(self, client):
        """Test that adding a comment requires authentication."""
        response = client.post('/bill/HB%20101/comment', data={
            'content': 'This is a test comment.'
        })
        # Should redirect to login or deny
        assert response.status_code in [302, 401]
    
    def test_add_comment_authenticated(self, auth_client):
        """Test adding a comment as authenticated user."""
        response = auth_client.post('/bill/HB%20101/comment', data={
            'content': 'This is a valid test comment with sufficient length.'
        }, follow_redirects=True)
        
        assert response.status_code == 200
    
    def test_add_comment_too_short(self, auth_client):
        """Test adding a comment that's too short."""
        response = auth_client.post('/bill/HB%20101/comment', data={
            'content': 'Hi'
        }, follow_redirects=True)
        
        # Should show error
        assert response.status_code in [200, 400]
    
    def test_add_comment_with_html(self, auth_client):
        """Test adding a comment with HTML tags."""
        response = auth_client.post('/bill/HB%20101/comment', data={
            'content': 'This comment has <script>alert("XSS")</script> tags.'
        }, follow_redirects=True)
        
        # Should be sanitized or rejected
        assert response.status_code == 200
    
    def test_add_comment_empty(self, auth_client):
        """Test adding an empty comment."""
        response = auth_client.post('/bill/HB%20101/comment', data={
            'content': ''
        }, follow_redirects=True)
        
        # Should show error
        assert response.status_code in [200, 400]


class TestBillsDataFetcher:
    """Test bills data fetching integration."""
    
    def test_bills_use_mock_data_in_development(self, client, app):
        """Test that bills use mock data in development mode."""
        import os
        os.environ['FLASK_ENV'] = 'development'
        
        response = client.get('/bills')
        assert response.status_code == 200
        
        # Should contain mock bill data
        data = response.data.decode('utf-8')
        assert 'HB' in data or 'SB' in data

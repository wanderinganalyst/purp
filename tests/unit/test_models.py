"""
Unit tests for models
"""

import pytest
from models import User, Comment
from extensions import db


class TestUserModel:
    """Test the User model."""
    
    def test_create_user(self, app, db_session):
        """Test creating a user."""
        user = User(
            username='testuser',
            role='user',
            street_address='123 Test St',
            city='Test City',
            state='MO',
            zipcode='12345'
        )
        user.set_password('TestPass123!')
        
        db_session.add(user)
        db_session.commit()
        
        assert user.id is not None
        assert user.username == 'testuser'
        assert user.role == 'user'
    
    def test_password_hashing(self, app, db_session):
        """Test that passwords are hashed."""
        user = User(username='testuser')
        user.set_password('SecurePass123!')
        
        assert user.password_hash != 'SecurePass123!'
        assert user.check_password('SecurePass123!')
        assert not user.check_password('WrongPassword')
    
    def test_user_repr(self, app, db_session):
        """Test user representation."""
        user = User(username='testuser')
        assert 'testuser' in repr(user)
    
    def test_update_representatives(self, app, db_session):
        """Test updating representative information."""
        user = User(username='testuser')
        db_session.add(user)
        db_session.commit()
        
        rep_info = {
            'senator': {
                'name': 'Sen. Test',
                'district': '5',
                'party': 'Democrat'
            },
            'representative': {
                'name': 'Rep. Test',
                'district': '10',
                'party': 'Republican'
            }
        }
        
        user.update_representatives(rep_info)
        db_session.commit()
        
        assert user.senator_name == 'Sen. Test'
        assert user.senator_district == '5'
        assert user.senator_party == 'Democrat'
        assert user.representative_name == 'Rep. Test'
        assert user.representative_district == '10'
        assert user.representative_party == 'Republican'
        assert user.reps_last_updated is not None
    
    def test_get_representatives_display(self, app, db_session):
        """Test getting representative display information."""
        user = User(
            username='testuser',
            senator_name='Sen. Test',
            senator_district='5',
            senator_party='Democrat',
            representative_name='Rep. Test',
            representative_district='10',
            representative_party='Republican'
        )
        
        display = user.get_representatives_display()
        
        assert 'senator' in display
        assert 'representative' in display
        assert display['senator']['name'] == 'Sen. Test'
        assert display['representative']['district'] == '10'
    
    def test_unique_username(self, app, db_session):
        """Test that usernames must be unique."""
        user1 = User(username='testuser')
        user1.set_password('Pass123!')
        db_session.add(user1)
        db_session.commit()
        
        user2 = User(username='testuser')
        user2.set_password('Pass456!')
        db_session.add(user2)
        
        with pytest.raises(Exception):
            db_session.commit()


class TestCommentModel:
    """Test the Comment model."""
    
    def test_create_comment(self, app, db_session):
        """Test creating a comment."""
        user = User(username='testuser')
        user.set_password('Pass123!')
        db_session.add(user)
        db_session.commit()
        
        comment = Comment(
            bill_id='HB 123',
            user_id=user.id,
            content='This is a test comment.'
        )
        db_session.add(comment)
        db_session.commit()
        
        assert comment.id is not None
        assert comment.bill_id == 'HB 123'
        assert comment.user_id == user.id
        assert comment.content == 'This is a test comment.'
        assert comment.created_at is not None
    
    def test_comment_user_relationship(self, app, db_session):
        """Test the relationship between comment and user."""
        user = User(username='testuser')
        user.set_password('Pass123!')
        db_session.add(user)
        db_session.commit()
        
        comment = Comment(
            bill_id='HB 123',
            user_id=user.id,
            content='Test comment'
        )
        db_session.add(comment)
        db_session.commit()
        
        assert comment.user == user
        assert comment in user.comments
    
    def test_comment_repr(self, app, db_session):
        """Test comment representation."""
        comment = Comment(
            bill_id='HB 123',
            user_id=1,
            content='Test'
        )
        assert 'HB 123' in repr(comment)

import pytest
from app.models import User
from app.extensions import db


class TestAuth:
    @pytest.fixture
    def client(self, app):
        return app.test_client()
    
    @pytest.fixture
    def authenticated_client(self, app, client):
        with app.app_context():
            user = User(username='testuser', full_name='Test User')
            user.set_password('password123')
            db.session.add(user)
            db.session.commit()
            with client.session_transaction() as sess:
                sess['_user_id'] = str(user.user_id)
        return client

    def test_login_page_loads(self, client):
        response = client.get('/auth/login')
        assert response.status_code == 200

    def test_register_page_loads(self, client):
        response = client.get('/auth/register')
        assert response.status_code == 200

    def test_login_success(self, app, client):
        with app.app_context():
            user = User(username='logintest', full_name='Login Test')
            user.set_password('password123')
            db.session.add(user)
            db.session.commit()
        
        response = client.post('/auth/login', data={
            'username': 'logintest',
            'password': 'password123'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert b'Welcome back' in response.data or b'Success' in response.data

    def test_login_failure(self, client):
        response = client.post('/auth/login', data={
            'username': 'nonexistent',
            'password': 'wrongpass'
        })
        
        assert response.status_code == 200
        assert b'Invalid' in response.data

    def test_register_success(self, app, client):
        response = client.post('/auth/register', data={
            'username': 'newuser',
            'email': 'newuser@test.com',
            'full_name': 'New User',
            'password': 'password123'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert b'Registration successful' in response.data or b'Success' in response.data

    def test_register_duplicate_username(self, app, client):
        with app.app_context():
            user = User(username='duplicate', full_name='Dup')
            user.set_password('password123')
            db.session.add(user)
            db.session.commit()
        
        response = client.post('/auth/register', data={
            'username': 'duplicate',
            'email': 'different@test.com',
            'full_name': 'Different User',
            'password': 'password123'
        })
        
        assert response.status_code == 200
        assert b'already exists' in response.data

    def test_logout(self, authenticated_client):
        response = authenticated_client.get('/auth/logout', follow_redirects=True)
        assert response.status_code == 200
        assert b'logged out' in response.data.lower() or b'sign in' in response.data.lower()

    def test_protected_route_redirect(self, client):
        response = client.get('/orders/history', follow_redirects=False)
        assert response.status_code == 302
        assert '/auth/login' in response.location
import pytest
from app.models import Product, User, Order, OrderItem
from app.extensions import db
from app.extensions import db


class TestOrders:
    @pytest.fixture
    def client(self, app):
        return app.test_client()
    
    @pytest.fixture
    def sample_user(self, app):
        with app.app_context():
            user = User(username='orderuser', full_name='Order User')
            user.set_password('password123')
            db.session.add(user)
            db.session.commit()
            return user.user_id
    
    @pytest.fixture
    def sample_product(self, app):
        with app.app_context():
            product = Product(
                name='Order Test Product',
                base_price=50.0,
                current_price=50.0,
                stock=20
            )
            db.session.add(product)
            db.session.commit()
            return product.product_id
    
    def test_checkout_requires_login(self, client):
        response = client.post('/orders/checkout', follow_redirects=False)
        assert response.status_code == 302
        assert '/auth/login' in response.location
    
    def test_checkout_empty_cart_redirect(self, app, client, sample_user):
        with app.app_context():
            with client.session_transaction() as sess:
                sess['_user_id'] = str(sample_user)
        
        response = client.post('/orders/checkout', follow_redirects=True)
        assert response.status_code == 200
        assert b'empty' in response.data.lower()

    def test_order_confirmation_access(self, app, client, sample_user):
        with app.app_context():
            with client.session_transaction() as sess:
                sess['_user_id'] = str(sample_user)
            
            product = Product.query.get(sample_product)
            order = Order(user_id=sample_user, total_amount=100.0)
            db.session.add(order)
            db.session.commit()
            order_id = order.order_id
        
        response = client.get(f'/orders/{order_id}')
        assert response.status_code == 200

    def test_order_history_requires_login(self, client):
        response = client.get('/orders/history', follow_redirects=False)
        assert response.status_code == 302

    def test_order_history_shows_orders(self, app, client, sample_user):
        with app.app_context():
            with client.session_transaction() as sess:
                sess['_user_id'] = str(sample_user)
            
            order = Order(user_id=sample_user, total_amount=50.0)
            db.session.add(order)
            db.session.commit()
        
        response = client.get('/orders/history')
        assert response.status_code == 200

    def test_checkout_creates_order(self, app, client, sample_user, sample_product):
        with app.app_context():
            product = Product.query.get(sample_product)
            
            with client.session_transaction() as sess:
                sess['_user_id'] = str(sample_user)
                sess['cart'] = {str(sample_product): 2}
        
        response = client.post('/orders/checkout', follow_redirects=True)
        
        with app.app_context():
            order = Order.query.filter_by(user_id=sample_user).first()
            assert order is not None
            assert order.total_amount == product.current_price * 2
            
            items = OrderItem.query.filter_by(order_id=order.order_id).all()
            assert len(items) == 1
            assert items[0].quantity == 2
            assert items[0].price_at_purchase == product.current_price
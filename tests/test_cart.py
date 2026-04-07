import pytest
from app.models import Product
from app.extensions import db


class TestCart:
    @pytest.fixture
    def client(self, app):
        return app.test_client()
    
    @pytest.fixture
    def sample_product(self, app):
        with app.app_context():
            product = Product(
                name='Test Product',
                base_price=100.0,
                current_price=100.0,
                stock=50
            )
            db.session.add(product)
            db.session.commit()
            return product.product_id
    
    def test_view_empty_cart(self, client):
        response = client.get('/cart/')
        assert response.status_code == 200

    def test_add_to_cart(self, client, sample_product):
        response = client.post(f'/cart/add/{sample_product}', data={'quantity': 2})
        assert response.status_code in [200, 302]
        
        with client.session_transaction() as sess:
            cart = sess.get('cart', {})
            assert str(sample_product) in cart

    def test_remove_from_cart(self, app, client, sample_product):
        with client.session_transaction() as sess:
            sess['cart'] = {str(sample_product): 2}
        
        response = client.post(f'/cart/remove/{sample_product}')
        assert response.status_code in [200, 302]

    def test_cart_count(self, client):
        with client.session_transaction() as sess:
            sess['cart'] = {'1': 2, '2': 3}
        
        response = client.get('/cart/count')
        assert response.status_code == 200

    def test_clear_cart(self, client):
        with client.session_transaction() as sess:
            sess['cart'] = {'1': 2}
        
        response = client.post('/cart/clear')
        assert response.status_code in [200, 302]
        
        with client.session_transaction() as sess:
            assert 'cart' not in sess
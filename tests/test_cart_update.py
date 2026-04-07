import pytest
from app.models import Product
from app.extensions import db


class TestCartUpdate:
    @pytest.fixture
    def client(self, app):
        return app.test_client()
    
    def test_update_cart_quantity(self, app, client):
        with app.app_context():
            product = Product(
                name='Update Test Product',
                base_price=25.0,
                current_price=25.0,
                stock=10
            )
            db.session.add(product)
            db.session.commit()
            product_id = product.product_id
        
        with client.session_transaction() as sess:
            sess['cart'] = {str(product_id): 1}
        
        response = client.post(f'/cart/update/{product_id}', data={'quantity': '5'}, follow_redirects=True)
        assert response.status_code == 200
        
        with client.session_transaction() as sess:
            assert sess['cart'][str(product_id)] == 5

    def test_update_cart_to_zero_removes_item(self, app, client):
        with app.app_context():
            product = Product(
                name='Remove Test Product',
                base_price=30.0,
                current_price=30.0,
                stock=5
            )
            db.session.add(product)
            db.session.commit()
            product_id = product.product_id
        
        with client.session_transaction() as sess:
            sess['cart'] = {str(product_id): 2}
        
        response = client.post(f'/cart/update/{product_id}', data={'quantity': '0'}, follow_redirects=True)
        
        with client.session_transaction() as sess:
            assert str(product_id) not in sess.get('cart', {})
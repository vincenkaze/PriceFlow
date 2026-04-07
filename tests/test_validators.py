import pytest
from utils.validators import validate_price, validate_stock, validate_product_dict


class TestValidators:
    def test_validate_price_positive(self):
        assert validate_price(100.0) == True
        assert validate_price(1) == True
        assert validate_price(0.01) == True

    def test_validate_price_zero(self):
        assert validate_price(0) == False

    def test_validate_price_negative(self):
        assert validate_price(-10) == False
        assert validate_price(-0.01) == False

    def test_validate_price_string(self):
        assert validate_price("100") == False
        assert validate_price("100.0") == False

    def test_validate_price_none(self):
        assert validate_price(None) == False

    def test_validate_stock_valid(self):
        assert validate_stock(50) == True
        assert validate_stock(0) == True

    def test_validate_stock_negative(self):
        assert validate_stock(-1) == False

    def test_validate_stock_float(self):
        assert validate_stock(50.0) == False

    def test_validate_product_dict_valid(self):
        product = {
            'product_id': 1,
            'name': 'Test Product',
            'base_price': 100.0,
            'current_price': 110.0,
            'stock': 50
        }
        is_valid, message = validate_product_dict(product)
        assert is_valid == True
        assert message == "OK"

    def test_validate_product_dict_missing_field(self):
        product = {
            'product_id': 1,
            'name': 'Test Product',
            'base_price': 100.0,
            'current_price': 110.0
        }
        is_valid, message = validate_product_dict(product)
        assert is_valid == False
        assert "Missing field: stock" in message

    def test_validate_product_dict_invalid_price(self):
        product = {
            'product_id': 1,
            'name': 'Test Product',
            'base_price': -10.0,
            'current_price': 110.0,
            'stock': 50
        }
        is_valid, message = validate_product_dict(product)
        assert is_valid == False
        assert "Invalid base_price" in message

    def test_validate_product_dict_invalid_stock(self):
        product = {
            'product_id': 1,
            'name': 'Test Product',
            'base_price': 100.0,
            'current_price': 110.0,
            'stock': -5
        }
        is_valid, message = validate_product_dict(product)
        assert is_valid == False
        assert "Invalid stock" in message
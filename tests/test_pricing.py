import pytest
from services.pricing_service import PricingService


class TestPricingService:
    @pytest.fixture
    def pricing_service(self):
        return PricingService()

    @pytest.fixture
    def base_product(self):
        return {
            'product_id': 1,
            'name': 'Test Product',
            'base_price': 100.0,
            'current_price': 100.0,
            'stock': 50
        }

    def test_zone1_high_demand_low_stock(self, pricing_service, base_product):
        product = {**base_product, 'stock': 30, 'current_price': 100.0}
        new_price, reason, zone = pricing_service.calculate_price(product, demand_score=90)
        
        assert new_price > product['base_price']
        assert zone == "Zone 1 - High demand+low stock"

    def test_zone2_rising_demand(self, pricing_service, base_product):
        product = {**base_product, 'stock': 40, 'current_price': 100.0}
        new_price, reason, zone = pricing_service.calculate_price(product, demand_score=50)
        
        assert new_price > product['base_price']
        assert zone == "Zone 2 - Rising"

    def test_zone3_weak_demand_excess_stock(self, pricing_service, base_product):
        product = {**base_product, 'stock': 95, 'current_price': 100.0}
        new_price, reason, zone = pricing_service.calculate_price(product, demand_score=3)
        
        assert new_price < product['base_price']
        assert zone == "Zone 3 - Low demand+high stock"

    def test_zone4_critical_demand(self, pricing_service, base_product):
        product = {**base_product, 'stock': 50, 'current_price': 100.0}
        new_price, reason, zone = pricing_service.calculate_price(product, demand_score=1)
        
        assert new_price < product['base_price']
        assert zone == "Zone 4 - Weak/Excess"

    def test_zone5_stable(self, pricing_service, base_product):
        product = {**base_product, 'stock': 70, 'current_price': 100.0}
        new_price, reason, zone = pricing_service.calculate_price(product, demand_score=30)
        
        assert new_price == product['base_price']
        assert zone == "Zone 5 - Stable"

    def test_zero_stock(self, pricing_service, base_product):
        product = {**base_product, 'stock': 0, 'current_price': 100.0}
        new_price, reason, zone = pricing_service.calculate_price(product, demand_score=30)
        
        assert new_price == product['current_price']
        assert zone == "Zone 5 - Stable"

    def test_extreme_high_demand(self, pricing_service, base_product):
        product = {**base_product, 'stock': 10}
        new_price, reason, zone = pricing_service.calculate_price(product, demand_score=150)
        
        assert new_price > product['base_price']
        assert zone == "Zone 1 - High demand+low stock"

    def test_no_demand(self, pricing_service, base_product):
        product = {**base_product, 'stock': 80}
        new_price, reason, zone = pricing_service.calculate_price(product, demand_score=0)
        
        assert new_price < product['base_price']

    def test_excess_stock_without_low_demand(self, pricing_service, base_product):
        product = {**base_product, 'stock': 98, 'current_price': 100.0}
        new_price, reason, zone = pricing_service.calculate_price(product, demand_score=40)
        
        assert zone == "Zone 4 - Weak/Excess"

    def test_update_prices_returns_correct_structure(self, pricing_service):
        products = [
            {'product_id': 1, 'name': 'P1', 'base_price': 100.0, 'current_price': 100.0, 'stock': 30},
            {'product_id': 2, 'name': 'P2', 'base_price': 50.0, 'current_price': 50.0, 'stock': 80}
        ]
        demand_scores = {1: 90, 2: 10}
        
        result = pricing_service.update_prices(products, demand_scores)
        
        assert 'updated' in result
        assert 'restocked' in result
        assert 'zone_counts' in result
        assert 'changes' in result

    def test_changes_recorded_when_price_moves(self, pricing_service):
        product = {'product_id': 1, 'name': 'P1', 'base_price': 100.0, 
                   'current_price': 100.0, 'stock': 30}
        result = pricing_service.update_prices([product], {1: 90})
        assert result['updated'] == 1
        assert len(result['changes']) == 1
        assert result['changes'][0]['product_id'] == 1
        assert result['changes'][0]['new_price'] > result['changes'][0]['old_price']

    def test_update_prices_with_automatic_restock(self, pricing_service):
        products = [
            {'product_id': 1, 'name': 'P1', 'base_price': 100.0, 'current_price': 100.0, 'stock': 3}
        ]
        
        result = pricing_service.update_prices(products, {})
        
        assert len(result['restocked']) == 1
        assert result['restocked'][0]['product_id'] == 1
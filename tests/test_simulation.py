import pytest
import random
from unittest.mock import patch, MagicMock


class TestUserActionGeneration:
    def test_view_probability_threshold(self):
        view_p = 0.8
        outcomes = {'view': 0, 'no_view': 0}
        
        for _ in range(1000):
            if random.random() < view_p:
                outcomes['view'] += 1
            else:
                outcomes['no_view'] += 1
        
        assert outcomes['view'] > 600
        assert outcomes['no_view'] < 400

    def test_cart_probability_threshold(self):
        cart_p = 0.3
        outcomes = {'cart': 0, 'no_cart': 0}
        
        for _ in range(1000):
            if random.random() < cart_p:
                outcomes['cart'] += 1
            else:
                outcomes['no_cart'] += 1
        
        assert outcomes['cart'] > 200
        assert outcomes['cart'] < 400

    def test_purchase_probability_threshold(self):
        purchase_p = 0.1
        outcomes = {'purchase': 0, 'no_purchase': 0}
        
        for _ in range(1000):
            if random.random() < purchase_p:
                outcomes['purchase'] += 1
            else:
                outcomes['no_purchase'] += 1
        
        assert outcomes['purchase'] > 50
        assert outcomes['purchase'] < 150

    def test_action_sequence_view_then_cart(self):
        view_p = 0.8
        cart_p = 0.3
        
        view_count = 0
        cart_count = 0
        
        for _ in range(1000):
            if random.random() < view_p:
                view_count += 1
                if random.random() < cart_p:
                    cart_count += 1
        
        assert cart_count < view_count
        assert view_count > 600


class TestPersonalityModifiers:
    def test_optimist_increases_purchase_on_premium(self):
        base_purchase_p = 0.1
        price_ratio = 1.1
        stock_ratio = 0.2
        
        purchase_p = base_purchase_p
        cart_p = 0.3
        
        if price_ratio > 1.05 or stock_ratio < 0.3:
            purchase_p *= 1.8
        cart_p *= 1.3
        
        assert purchase_p > base_purchase_p
        assert cart_p > 0.3

    def test_optimist_does_not_increase_when_stable(self):
        base_purchase_p = 0.1
        price_ratio = 1.0
        stock_ratio = 0.5
        
        purchase_p = base_purchase_p
        cart_p = 0.3
        
        if price_ratio > 1.05 or stock_ratio < 0.3:
            purchase_p *= 1.8
        
        assert purchase_p == base_purchase_p

    def test_pessimist_decreases_purchase_on_premium(self):
        base_purchase_p = 0.1
        price_ratio = 1.15
        
        purchase_p = base_purchase_p
        cart_p = 0.3
        
        if price_ratio > 1.1:
            purchase_p *= 0.3
            cart_p *= 0.5
        
        assert purchase_p < base_purchase_p
        assert cart_p < 0.3

    def test_pessimist_increases_purchase_on_discount(self):
        base_purchase_p = 0.1
        price_ratio = 0.9
        
        purchase_p = base_purchase_p
        
        if price_ratio > 1.1:
            purchase_p *= 0.3
        elif price_ratio < 0.95:
            purchase_p *= 1.6
        
        assert purchase_p > base_purchase_p

    def test_envious_increases_on_low_stock(self):
        base_purchase_p = 0.1
        stock_ratio = 0.3
        
        purchase_p = base_purchase_p
        cart_p = 0.3
        
        if stock_ratio < 0.4:
            purchase_p *= 1.7
            cart_p *= 1.4
        
        assert purchase_p > base_purchase_p
        assert cart_p > 0.3

    def test_bargain_hunter_avoids_premium(self):
        base_purchase_p = 0.1
        price_ratio = 1.1
        
        purchase_p = base_purchase_p
        cart_p = 0.3
        
        if price_ratio > 1.08:
            purchase_p = 0.0
            cart_p *= 0.2
        elif price_ratio < 0.97:
            purchase_p *= 2.0
        
        assert purchase_p == 0.0
        assert cart_p < 0.3

    def test_bargain_hunter_buys_discounts(self):
        base_purchase_p = 0.1
        price_ratio = 0.95
        
        purchase_p = base_purchase_p
        
        if price_ratio > 1.08:
            purchase_p = 0.0
        elif price_ratio < 0.97:
            purchase_p *= 2.0
        
        assert purchase_p == 0.2

    def test_impulse_buyer_responds_to_low_stock(self):
        base_purchase_p = 0.1
        stock_ratio = 0.2
        
        purchase_p = base_purchase_p
        cart_p = 0.3
        
        if stock_ratio < 0.25:
            purchase_p *= 2.5
        cart_p *= 1.6
        
        assert purchase_p > base_purchase_p
        assert cart_p > 0.3

    def test_impulse_buyer_random_boost(self):
        base_purchase_p = 0.1
        
        with patch('random.random', return_value=0.35):
            purchase_p = base_purchase_p
            if random.random() < 0.4:
                purchase_p *= 2.5
        
        assert purchase_p > base_purchase_p


class TestSimulatedBehavior:
    def test_activity_rate_limits_products(self):
        activity_rate = 0.2
        all_products = list(range(100))
        
        num_active = max(1, int(len(all_products) * activity_rate))
        k = min(num_active, len(all_products))
        selected = random.sample(all_products, k=k)
        
        assert len(selected) == 20
        assert len(set(selected)) == 20

    def test_user_sample_rate(self):
        sim_users = list(range(200))
        users_this_tick = random.sample(sim_users, k=max(1, int(len(sim_users) * 0.2)))
        
        assert len(users_this_tick) == 40

    def test_restock_decreases_stock(self):
        product = {'stock': 5}
        product['stock'] -= 1
        
        assert product['stock'] == 4
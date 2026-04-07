from datetime import datetime
from app.config import Config


class PricingService:
    def __init__(self):
        pass

    def calculate_price(self, product: dict, demand_score: int, rules: dict = None) -> tuple:
        if rules is None:
            rules = self._get_default_rules()

        demand_high = rules['demand_threshold_high']
        demand_low = rules['demand_threshold_low']
        stock_low = rules['stock_threshold_low'] / 100.0
        stock_high = rules['stock_threshold_high'] / 100.0
        stock_excess = rules['stock_threshold_excess'] / 100.0
        increase_pct = rules['price_increase_pct'] / 100.0
        decrease_pct = rules['price_decrease_pct'] / 100.0
        min_price_pct = rules['min_price_pct']
        max_price_pct = rules['max_price_pct']
        mid_price_pct = rules.get('price_mid_pct', (min_price_pct + max_price_pct) / 2)
        min_aggressive_pct = rules.get('price_min_aggressive_pct', min_price_pct * 0.95)

        old_price = product['current_price']
        base_price = product['base_price']
        stock = product.get('stock', 50)
        stock_ratio = stock / 100.0 if stock > 0 else 0.0

        new_price = old_price
        reason = "Stable"
        zone = "Zone 5 - Stable"

        if demand_score > (demand_high * 0.75) and stock_ratio < stock_high:
            new_price = min(base_price * max_price_pct, old_price * (1 + increase_pct * 0.5))
            reason = "High demand"
            zone = "Zone 1 - High demand+low stock"
        elif demand_score > (demand_high * 0.5) and stock_ratio < stock_high:
            new_price = min(base_price * mid_price_pct, old_price * (1 + increase_pct * 0.25))
            reason = "Rising demand"
            zone = "Zone 2 - Rising"
        elif demand_score < (demand_low * 0.2) and stock_ratio > (stock_excess * 0.98):
            new_price = max(base_price * min_price_pct, old_price * (1 - decrease_pct * 0.5))
            reason = "Weak demand + excess stock"
            zone = "Zone 3 - Low demand+high stock"
        elif demand_score < (demand_low * 0.1) or stock_ratio > 0.95:
            new_price = max(base_price * min_aggressive_pct, old_price * (1 - decrease_pct * 0.5))
            reason = "Critical" if demand_score < (demand_low * 0.1) else "Excess stock"
            zone = "Zone 4 - Weak/Excess"

        new_price = round(new_price, 2)
        return new_price, reason, zone

    def _get_default_rules(self):
        return {
            'demand_threshold_high': 80,
            'demand_threshold_low': 20,
            'stock_threshold_low': 10,
            'stock_threshold_high': 60,
            'stock_threshold_excess': 80,
            'price_increase_pct': 5.0,
            'price_decrease_pct': 5.0,
            'price_mid_pct': 1.1,
            'price_min_aggressive_pct': 0.65,
            'min_price_pct': 0.7,
            'max_price_pct': 1.5
        }

    def update_prices(self, products: list, demand_scores: dict, rules: dict = None) -> dict:
        if rules is None:
            rules = self._get_default_rules()

        updated = 0
        restocked = []
        changes = []
        zone_counts = {
            "Zone 1 - High demand+low stock": 0,
            "Zone 2 - Rising": 0,
            "Zone 3 - Low demand+high stock": 0,
            "Zone 4 - Weak/Excess": 0,
            "Zone 5 - Stable": 0
        }

        for product in products:
            product_id = product['product_id']
            demand_score = demand_scores.get(product_id, 0)

            old_stock = product.get('stock', 0)
            base_stock = 80
            current_stock = old_stock

            if current_stock <= Config.AUTO_RESTOCK_THRESHOLD:
                new_stock = min(current_stock + Config.AUTO_RESTOCK_AMOUNT, base_stock)
                restocked.append({
                    'product_id': product_id,
                    'product_name': product.get('name', f'Product #{product_id}'),
                    'old_stock': old_stock,
                    'new_stock': new_stock,
                    'amount_added': Config.AUTO_RESTOCK_AMOUNT
                })
                product['stock'] = new_stock
                current_stock = new_stock

            product['stock'] = current_stock

            new_price, reason, zone = self.calculate_price(product, demand_score, rules)
            product['current_price'] = new_price
            product['last_updated'] = datetime.utcnow()

            zone_counts[zone] += 1

            if abs(new_price - product['current_price']) > 0.01:
                updated += 1
                changes.append({
                    'product_id': product_id,
                    'old_price': product['base_price'],
                    'new_price': new_price,
                    'demand_score': demand_score,
                    'stock': current_stock,
                    'change_reason': reason,
                    'timestamp': datetime.utcnow()
                })

        return {
            'updated': updated,
            'restocked': restocked,
            'zone_counts': zone_counts,
            'changes': changes
        }


pricing_service = PricingService()
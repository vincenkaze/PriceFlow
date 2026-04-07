import time
import threading
import logging
from datetime import datetime, timedelta
from app.extensions import db
from app.models import Product, PriceHistory, DemandScore, PricingRule
from app.config import Config
from services.pricing_service import pricing_service
from services.inventory_service import inventory_service

try:
    from modules.websocket_emitter import ws_emitter
except ImportError:
    ws_emitter = None


class PricingEngine:
    def __init__(self):
        self.running = False
        self.thread = None
        self.app = None
        self.interval = 10

    def start(self, flask_app):
        if self.running:
            return
        self.app = flask_app
        self.running = True
        self.thread = threading.Thread(target=self._run_loop, daemon=True)
        self.thread.start()
        print("[PRICE] Engine started - checking DemandScore every {}s".format(self.interval))

    def _run_loop(self):
        with self.app.app_context():
            while self.running:
                try:
                    self._update_prices()
                except Exception as e:
                    print(f"[PRICE] Error: {e}")
                time.sleep(self.interval)

    def _get_pricing_rules(self, product):
        rule = PricingRule.query.filter(
            PricingRule.category_id == product.category_id,
            PricingRule.is_active == True
        ).first()
        
        if not rule:
            rule = PricingRule.query.filter(
                PricingRule.is_global == True,
                PricingRule.is_active == True
            ).first()
        
        if not rule:
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
        
        return {
            'demand_threshold_high': rule.demand_threshold_high,
            'demand_threshold_low': rule.demand_threshold_low,
            'stock_threshold_low': rule.stock_threshold_low,
            'stock_threshold_high': 60,
            'stock_threshold_excess': 80,
            'price_increase_pct': rule.price_increase_pct,
            'price_decrease_pct': rule.price_decrease_pct,
            'price_mid_pct': rule.price_mid_pct,
            'price_min_aggressive_pct': rule.price_min_aggressive_pct,
            'min_price_pct': rule.min_price_pct,
            'max_price_pct': rule.max_price_pct
        }

    def _update_prices(self):
        latest_scores = (
            db.session.query(DemandScore)
            .filter(DemandScore.calculated_at >= datetime.utcnow() - timedelta(minutes=20))
            .order_by(DemandScore.calculated_at.desc())
            .all()
        )

        demand_map = {}
        for score in latest_scores:
            pid = score.product_id
            if pid not in demand_map:
                demand_map[pid] = score.demand_score

        total_products_count = Product.query.count()
        active_products = len(demand_map)
        if total_products_count > 0:
            saturation_pct = (active_products / total_products_count) * 100
            if saturation_pct == 100:
                logging.warning(f"[PRICE] ALL {active_products} products have demand scores -- sim is oversaturating")
            elif saturation_pct > 80:
                logging.warning(f"[PRICE] {saturation_pct:.0f}% products active ({active_products}/{total_products_count})")
            logging.debug(f"[PRICE] Demand saturation: {active_products}/{total_products_count} ({saturation_pct:.1f}%)")

        scores = list(demand_map.values())
        if scores:
            score_min = min(scores)
            score_max = max(scores)
            score_avg = sum(scores) / len(scores)
            tier_very_high = sum(1 for s in scores if s > 100)
            tier_high = sum(1 for s in scores if 50 < s <= 100)
            tier_mid = sum(1 for s in scores if 10 < s <= 50)
            tier_low = sum(1 for s in scores if 5 < s <= 10)
            tier_very_low = sum(1 for s in scores if s <= 5)
            logging.debug(f"[DEMAND] Range: {score_min:.1f} - {score_max:.1f}, Avg: {score_avg:.1f} | Tiers: >100:{tier_very_high}, 51-100:{tier_high}, 11-50:{tier_mid}, 6-10:{tier_low}, <=5:{tier_very_low}")

        products = Product.query.all()
        
        product_dicts = []
        rules_by_category = {}
        for product in products:
            product_dict = {
                'product_id': product.product_id,
                'name': product.name,
                'base_price': float(product.base_price),
                'current_price': float(product.current_price),
                'stock': product.stock,
                'category_id': product.category_id
            }
            product_dicts.append(product_dict)
            
            cat_id = product.category_id
            if cat_id not in rules_by_category:
                rules_by_category[cat_id] = self._get_pricing_rules(product)
        
        result = pricing_service.update_prices(product_dicts, demand_map)
        
        updated = 0
        for i, product in enumerate(products):
            pd = product_dicts[i]
            if pd['current_price'] != product.current_price:
                old_price = product.current_price
                new_price = pd['current_price']
                product.current_price = new_price
                product.last_updated = datetime.utcnow()
                product.stock = pd['stock']
                
                demand_score = demand_map.get(product.product_id, 0)
                history = PriceHistory(
                    product_id=product.product_id,
                    old_price=old_price,
                    new_price=new_price,
                    demand_score=demand_score,
                    stock=product.stock,
                    change_reason="Dynamic pricing",
                    timestamp=datetime.utcnow()
                )
                db.session.add(history)
                updated += 1
        
        db.session.commit()
        
        logging.debug(f"[PRICE] Zone distribution: {result['zone_counts']}")
        
        restocked = result['restocked']
        if restocked:
            print(f"[RESTOCK] {len(restocked)} products restocked")
            if ws_emitter:
                ws_emitter.emit_restock({
                    'products': restocked,
                    'timestamp': datetime.utcnow().isoformat()
                })
        
        if updated > 0 or restocked:
            print(f"[PRICE] Updated {updated} products - some prices just moved!")
            
            if ws_emitter:
                updated_products = []
                for i, product in enumerate(products):
                    pd = product_dicts[i]
                    if pd['current_price'] != pd['base_price']:
                        demand_score = demand_map.get(product.product_id, 0)
                        
                        if demand_score >= 80:
                            demand_label = 'HIGH DEMAND'
                        elif demand_score >= 60:
                            demand_label = 'TRENDING'
                        elif demand_score <= 30:
                            demand_label = 'LOW DEMAND'
                        else:
                            demand_label = 'STABLE'
                        
                        change_pct = ((pd['current_price'] - pd['base_price']) / pd['base_price']) * 100
                        updated_products.append({
                            'product_id': product.product_id,
                            'current_price': float(pd['current_price']),
                            'base_price': float(pd['base_price']),
                            'change_percent': round(change_pct, 1),
                            'demand_label': demand_label,
                            'stock': pd['stock']
                        })
                
                ws_emitter.emit_price_change({
                    'updated_count': updated,
                    'products': updated_products,
                    'restocked': [r['product_id'] for r in restocked],
                    'timestamp': datetime.utcnow().isoformat()
                })


pricing_engine = PricingEngine()
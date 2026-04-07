from datetime import datetime, timedelta
from sqlalchemy import func


class AnalyticsService:
    def __init__(self):
        pass

    def get_dashboard_stats(self, Product, DemandScore, PriceHistory, UserAction) -> dict:
        total_products = Product.query.count()
        
        try:
            products_today = Product.query.filter(
                Product.created_at >= datetime.utcnow() - timedelta(days=1)
            ).count()
        except:
            products_today = 0
        
        latest_demand = DemandScore.query.order_by(DemandScore.calculated_at.desc()).limit(100).count()
        
        recent_changes = PriceHistory.query.filter(
            PriceHistory.timestamp >= datetime.utcnow() - timedelta(hours=24)
        ).count()
        
        price_changes_24h = PriceHistory.query.filter(
            PriceHistory.timestamp >= datetime.utcnow() - timedelta(hours=24)
        ).all()
        
        if price_changes_24h:
            total_pct_change = 0
            count = 0
            for pc in price_changes_24h:
                if pc.old_price and pc.old_price > 0:
                    pct_change = ((pc.new_price - pc.old_price) / pc.old_price) * 100
                    total_pct_change += pct_change
                    count += 1
            avg_price_change = total_pct_change / count if count > 0 else 0
        else:
            avg_price_change = 0
        
        low_stock_count = Product.query.filter(Product.stock < 10).count()
        
        today_actions = UserAction.query.filter(
            UserAction.timestamp >= datetime.utcnow() - timedelta(hours=24)
        ).count()
        
        peak_percent = min(100, int((today_actions / 1000) * 100)) if today_actions > 0 else 0
        
        return {
            'total_products': total_products,
            'products_today': products_today,
            'demand_scores_count': latest_demand,
            'price_changes_today': recent_changes,
            'avg_price_change': round(avg_price_change, 2),
            'low_stock_count': low_stock_count,
            'actions_today': today_actions,
            'peak_percent': peak_percent
        }

    def get_price_history(self, Product, PriceHistory, product_id: int, limit: int = 50) -> list:
        history = PriceHistory.query.filter_by(product_id=product_id)\
            .order_by(PriceHistory.timestamp.desc()).limit(limit).all()
        
        return [{
            'timestamp': h.timestamp.isoformat(),
            'old_price': float(h.old_price),
            'new_price': float(h.new_price),
            'demand_score': h.demand_score,
            'stock': h.stock,
            'change_reason': h.change_reason
        } for h in history]

    def get_trending_products(self, Product, DemandScore, limit: int = 10) -> list:
        latest_scores = (
            DemandScore.query
            .filter(DemandScore.calculated_at >= datetime.utcnow() - timedelta(hours=24))
            .order_by(DemandScore.demand_score.desc())
            .limit(limit)
            .all()
        )
        
        product_ids = [s.product_id for s in latest_scores]
        products = Product.query.filter(Product.product_id.in_(product_ids)).all() if product_ids else []
        product_map = {p.product_id: p for p in products}
        
        result = []
        for score in latest_scores:
            product = product_map.get(score.product_id)
            if product:
                result.append({
                    'product_id': score.product_id,
                    'name': product.name,
                    'demand_score': score.demand_score,
                    'current_price': float(product.current_price),
                    'stock': product.stock
                })
        
        return result

    def get_recent_changes(self, Product, PriceHistory, limit: int = 20) -> list:
        changes = PriceHistory.query.order_by(PriceHistory.timestamp.desc()).limit(limit).all()
        
        product_ids = list(set([c.product_id for c in changes]))
        products = Product.query.filter(Product.product_id.in_(product_ids)).all()
        product_map = {p.product_id: p.name for p in products}
        
        return [{
            'history_id': c.history_id,
            'product_id': c.product_id,
            'product_name': product_map.get(c.product_id, f'Product #{c.product_id}'),
            'old_price': float(c.old_price),
            'new_price': float(c.new_price),
            'demand_score': c.demand_score,
            'stock': c.stock,
            'change_reason': c.change_reason,
            'timestamp': c.timestamp.isoformat()
        } for c in changes]


analytics_service = AnalyticsService()
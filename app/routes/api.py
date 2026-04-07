from flask import Blueprint, jsonify, request
from app.models import Product, DemandScore, PriceHistory, UserAction
from app.extensions import db
from datetime import datetime, timedelta

api_bp = Blueprint('api', __name__, url_prefix='/api')

# ================== PUBLIC API ENDPOINTS ==================

@api_bp.route('/products', methods=['GET'])
def get_products():
    """Return all products with current dynamic pricing"""
    products = Product.query.all()
    return jsonify([{
        'id': p.product_id,
        'name': p.name,
        'base_price': float(p.base_price),
        'current_price': float(p.current_price),
        'stock': p.stock,
        'last_updated': p.last_updated.isoformat() if p.last_updated else None
    } for p in products])


@api_bp.route('/demand/latest', methods=['GET'])
def get_latest_demand():
    """Return latest demand scores for all products"""
    latest = DemandScore.query.order_by(DemandScore.calculated_at.desc()).limit(100).all()
    return jsonify([{
        'product_id': d.product_id,
        'demand_score': d.demand_score,
        'calculated_at': d.calculated_at.isoformat()
    } for d in latest])


@api_bp.route('/price-history/<int:product_id>', methods=['GET'])
def get_price_history(product_id):
    """Return price history for a specific product"""
    history = PriceHistory.query.filter_by(product_id=product_id)\
        .order_by(PriceHistory.timestamp.desc()).limit(50).all()
    
    return jsonify([{
        'timestamp': h.timestamp.isoformat(),
        'old_price': float(h.old_price),
        'new_price': float(h.new_price),
        'change_reason': h.change_reason
    } for h in history])


# ================== CONTROL ENDPOINTS (for demo / admin) ==================

@api_bp.route('/trigger/simulation', methods=['POST'])
def trigger_simulation():
    """Manually trigger one simulation tick"""
    from modules.user_simulation import simulation
    try:
        simulation._simulate_one_tick()
        return jsonify({"status": "success", "message": "Simulation tick executed"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@api_bp.route('/trigger/demand', methods=['POST'])
def trigger_demand():
    """Manually refresh demand scores"""
    from modules.demand_analysis import demand_analyzer
    demand_analyzer.refresh_active_products()
    return jsonify({"status": "success", "message": "Demand analysis refreshed"})


@api_bp.route('/trigger/pricing', methods=['POST'])
def trigger_pricing():
    """Manually run pricing update"""
    from modules.pricing_engine import pricing_engine
    pricing_engine._update_prices()
    return jsonify({"status": "success", "message": "Pricing engine executed"})


# Health check
@api_bp.route('/health', methods=['GET'])
def health():
    return jsonify({
        "status": "healthy",
        "simulation_running": True,
        "timestamp": datetime.utcnow().isoformat()
    })


# ================== ADMIN PRODUCT MANAGEMENT ==================

@api_bp.route('/admin/products', methods=['GET'])
def get_admin_products():
    """Return all products with full details for admin panel"""
    products = Product.query.order_by(Product.product_id).all()
    return jsonify([{
        'id': p.product_id,
        'name': p.name,
        'category_id': p.category_id,
        'base_price': float(p.base_price),
        'current_price': float(p.current_price),
        'min_price': float(p.min_price),
        'max_price': float(p.max_price),
        'stock': p.stock,
        'image_url': p.image_url,
        'last_updated': p.last_updated.isoformat() if p.last_updated else None
    } for p in products])


@api_bp.route('/admin/products/<int:product_id>', methods=['GET'])
def get_admin_product(product_id):
    """Return single product details"""
    product = Product.query.get_or_404(product_id)
    return jsonify({
        'id': product.product_id,
        'name': product.name,
        'category_id': product.category_id,
        'base_price': float(product.base_price),
        'current_price': float(product.current_price),
        'min_price': float(product.min_price),
        'max_price': float(product.max_price),
        'stock': product.stock,
        'image_url': product.image_url,
        'last_updated': product.last_updated.isoformat() if product.last_updated else None
    })


@api_bp.route('/admin/products/<int:product_id>', methods=['PUT'])
def update_product(product_id):
    """Update product details (name, stock, prices, image)"""
    product = Product.query.get_or_404(product_id)
    data = request.get_json()
    
    # Update allowed fields
    if 'name' in data:
        product.name = data['name']
    if 'stock' in data:
        product.stock = int(data['stock'])
    if 'base_price' in data:
        product.base_price = float(data['base_price'])
    if 'current_price' in data:
        product.current_price = float(data['current_price'])
    if 'min_price' in data:
        product.min_price = float(data['min_price'])
    if 'max_price' in data:
        product.max_price = float(data['max_price'])
    if 'image_url' in data:
        product.image_url = data['image_url']
    
    product.last_updated = datetime.utcnow()
    db.session.commit()
    
    # Emit WebSocket update for real-time UI
    try:
        from modules.websocket_emitter import emit_product_update
        emit_product_update({
            'id': product.product_id,
            'name': product.name,
            'current_price': float(product.current_price),
            'stock': product.stock,
            'image_url': product.image_url
        })
    except Exception:
        pass  # Don't fail if WebSocket not available
    
    return jsonify({
        'status': 'success',
        'message': 'Product updated',
        'product': {
            'id': product.product_id,
            'name': product.name,
            'stock': product.stock,
            'current_price': float(product.current_price),
            'image_url': product.image_url
        }
    })


# ================== DASHBOARD API ENDPOINTS ==================

@api_bp.route('/dashboard/stats', methods=['GET'])
def get_dashboard_stats():
    """Return dashboard statistics"""
    from sqlalchemy import func, case
    
    # Total products
    total_products = Product.query.count()
    
    # Products added today (fallback if created_at doesn't exist)
    try:
        products_today = Product.query.filter(
            Product.created_at >= datetime.utcnow() - timedelta(days=1)
        ).count()
    except:
        products_today = 0
    
    # Latest demand scores count
    latest_demand = DemandScore.query.order_by(DemandScore.calculated_at.desc()).limit(100).count()
    
    # Recent price changes today
    recent_changes = PriceHistory.query.filter(
        PriceHistory.timestamp >= datetime.utcnow() - timedelta(hours=24)
    ).count()
    
    # Average price change (percentage)
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
    
    # Low stock items (stock < 10)
    low_stock_count = Product.query.filter(Product.stock < 10).count()
    
    # Total actions today
    today_actions = UserAction.query.filter(
        UserAction.timestamp >= datetime.utcnow() - timedelta(hours=24)
    ).count()
    
    # Peak percentage (actions vs expected max)
    peak_percent = min(100, int((today_actions / 1000) * 100)) if today_actions > 0 else 0
    
    return jsonify({
        'total_products': total_products,
        'products_today': products_today,
        'demand_scores_count': latest_demand,
        'price_changes_today': recent_changes,
        'avg_price_change': round(avg_price_change, 2),
        'low_stock_count': low_stock_count,
        'actions_today': today_actions,
        'peak_percent': peak_percent
    })


@api_bp.route('/dashboard/recent-changes', methods=['GET'])
def get_recent_changes():
    """Return recent price changes for table"""
    changes = PriceHistory.query.order_by(PriceHistory.timestamp.desc()).limit(20).all()
    
    # Get product names map
    product_ids = list(set([c.product_id for c in changes]))
    products = Product.query.filter(Product.product_id.in_(product_ids)).all()
    product_map = {p.product_id: p.name for p in products}
    
    return jsonify([{
        'history_id': c.history_id,
        'product_id': c.product_id,
        'product_name': product_map.get(c.product_id, f'Product #{c.product_id}'),
        'old_price': float(c.old_price),
        'new_price': float(c.new_price),
        'demand_score': c.demand_score,
        'stock': c.stock,
        'change_reason': c.change_reason,
        'timestamp': c.timestamp.isoformat()
    } for c in changes])


@api_bp.route('/dashboard/chart/prices', methods=['GET'])
def get_price_chart_data():
    """Return price data for chart (last 24 hours, aggregated)"""
    # Get hourly aggregated price changes
    from sqlalchemy import func
    
    # Group by hour and get average new price
    results = db.session.query(
        func.strftime('%Y-%m-%d %H:00', PriceHistory.timestamp).label('hour'),
        func.avg(PriceHistory.new_price).label('avg_price'),
        func.count(PriceHistory.history_id).label('changes')
    ).filter(
        PriceHistory.timestamp >= datetime.utcnow() - timedelta(hours=24)
    ).group_by('hour').order_by('hour').all()
    
    return jsonify([{
        'hour': r.hour,
        'avg_price': float(r.avg_price) if r.avg_price else 0,
        'changes': r.changes
    } for r in results])


@api_bp.route('/dashboard/chart/demand', methods=['GET'])
def get_demand_chart_data():
    """Return demand score data for chart (last 7 days)"""
    from sqlalchemy import func
    
    results = db.session.query(
        func.date(DemandScore.calculated_at).label('date'),
        func.avg(DemandScore.demand_score).label('avg_score'),
        func.max(DemandScore.demand_score).label('max_score')
    ).filter(
        DemandScore.calculated_at >= datetime.utcnow() - timedelta(days=7)
    ).group_by('date').order_by('date').all()
    
    
    return jsonify([{
        'date': str(r.date),
        'avg_score': float(r.avg_score) if r.avg_score else 0,
        'max_score': r.max_score
    } for r in results])



@api_bp.route('/products/all', methods=['GET'])
def get_all_products():
    """Return all products with full details"""
    products = Product.query.all()
    return jsonify([{
        'id': p.product_id,
        'name': p.name,
        'category_id': p.category_id,
        'base_price': float(p.base_price),
        'current_price': float(p.current_price),
        'stock': p.stock,
        'min_price': float(p.min_price) if p.min_price else None,
        'max_price': float(p.max_price) if p.max_price else None,
        'last_updated': p.last_updated.isoformat() if p.last_updated else None
    } for p in products])


@api_bp.route('/dashboard/trends', methods=['GET'])
def get_trending_analysis():
    """ML-powered short-term trend analysis for top products"""
    from modules.ml.regressor import demand_regressor
    
    limit = request.args.get('limit', 10, type=int)
    
    products = Product.query.limit(limit).all()
    
    result = []
    for product in products:
        scores = (
            DemandScore.query
            .filter(DemandScore.product_id == product.product_id)
            .order_by(DemandScore.calculated_at.desc())
            .limit(30)
            .all()
        )
        
        score_history = [s.demand_score for s in scores]
        score_history.reverse()
        
        trend_data = demand_regressor.analyze_trend(score_history)
        chart_data = demand_regressor.get_chart_data(score_history)
        
        result.append({
            'id': product.product_id,
            'name': product.name,
            'current_price': float(product.current_price),
            'stock': product.stock,
            'trend': trend_data['trend'],
            'velocity': trend_data['velocity'],
            'confidence': trend_data['confidence'],
            'forecast': trend_data['forecast'],
            'ema_short': trend_data['ema_short'],
            'ema_long': trend_data['ema_long'],
            'chart_data': chart_data
        })
    
    return jsonify({'products': result})
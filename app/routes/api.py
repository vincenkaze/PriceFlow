from flask import Blueprint, jsonify, request
from app.models import Product, DemandScore, PriceHistory, UserAction
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
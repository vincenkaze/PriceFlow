from flask import Blueprint, render_template, current_app, jsonify, request
from datetime import datetime
from app.extensions import db
from app.models import Product, Category, DemandScore

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def home():
    """Homepage with dynamic product data from database"""
    import logging
    logger = logging.getLogger(__name__)
    
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    categories = Category.query.all()
    
    pagination = Product.query.order_by(Product.product_id).paginate(
        page=page, per_page=per_page, error_out=False
    )
    products_page = pagination.items
    
    if not products_page and page == 1:
        logger.warning("[HOME] No products found!")
        return render_template(
            'home.html',
            products=[], featured=[], categories=[],
            num_sim_users=current_app.config['NUM_SIMULATED_USERS'],
            tick_rate=current_app.config['SIMULATION_TICK_RATE'],
            pagination=None, error="No products in database - run seed script"
        )
    
    product_ids = [p.product_id for p in products_page]
    latest_scores = db.session.query(
        DemandScore.product_id, DemandScore.demand_score,
        DemandScore.calculated_at
    ).filter(
        DemandScore.product_id.in_(product_ids)
    ).distinct(DemandScore.product_id).all()
    
    demand_map = {}
    for pid, score, calc_at in latest_scores:
        if pid not in demand_map or calc_at > demand_map[pid][1]:
            demand_map[pid] = (score, calc_at)
    
    product_data = []
    for p in products_page:
        score, calc_at = demand_map.get(p.product_id, (50, None))
        demand_label = "Stable"
        if score >= 80:
            demand_label = "High Demand"
        elif score >= 60:
            demand_label = "Trending"
        elif score <= 30:
            demand_label = "Low Demand"
        
        price_change = ((p.current_price - p.base_price) / p.base_price * 100) if p.base_price > 0 else 0
        product_data.append({
            'id': p.product_id,
            'name': p.name,
            'current_price': p.current_price,
            'base_price': p.base_price,
            'stock': p.stock,
            'demand_label': demand_label,
            'demand_score': score,
            'price_change_pct': round(price_change, 1),
            'category_id': p.category_id,
            'image_url': p.image_url or ''
        })
    
    all_products = Product.query.all()
    all_scores = db.session.query(
        DemandScore.product_id, DemandScore.demand_score
    ).filter(DemandScore.product_id.in_([p.product_id for p in all_products]))\
     .distinct(DemandScore.product_id).all()
    score_map = {pid: score for pid, score in all_scores}
    
    featured_data = []
    for p in all_products:
        score = score_map.get(p.product_id, 50)
        price_change = ((p.current_price - p.base_price) / p.base_price * 100) if p.base_price > 0 else 0
        label = "Stable"
        if score >= 80: label = "High Demand"
        elif score >= 60: label = "Trending"
        elif score <= 30: label = "Low Demand"
        featured_data.append({
            'id': p.product_id, 'name': p.name,
            'current_price': p.current_price, 'base_price': p.base_price,
            'stock': p.stock, 'demand_label': label,
            'demand_score': score,
            'price_change_pct': round(price_change, 1),
            'category_id': p.category_id, 'image_url': p.image_url or ''
        })
    featured = sorted(featured_data, key=lambda x: x['demand_score'], reverse=True)[:4]
    
    pagination_info = {
        'page': page,
        'per_page': per_page,
        'total': pagination.total,
        'pages': pagination.pages,
        'has_prev': pagination.has_prev,
        'has_next': pagination.has_next,
        'prev_num': pagination.prev_num,
        'next_num': pagination.next_num
    }
    
    return render_template(
        'home.html',
        products=product_data,
        featured=featured,
        categories=categories,
        num_sim_users=current_app.config['NUM_SIMULATED_USERS'],
        tick_rate=current_app.config['SIMULATION_TICK_RATE'],
        pagination=pagination_info,
        total_products=Product.query.count(),
        error=None
    )

@main_bp.route('/status')
def status():
    return jsonify({
        "message": "PriceFlow is LIVE",
        "simulated_users": current_app.config['NUM_SIMULATED_USERS'],
        "simulation_tick": current_app.config['SIMULATION_TICK_RATE'],
        "timestamp": datetime.utcnow().isoformat()
    })

@main_bp.route('/product/<int:product_id>')
def product_detail(product_id):
    product = Product.query.get_or_404(product_id)
    
    latest_demand = DemandScore.query.filter_by(product_id=product_id)\
        .order_by(DemandScore.calculated_at.desc()).first()
    
    return render_template('product/detail.html', product=product, latest_demand=latest_demand)

@main_bp.route('/api/products')
def api_products():
    """API endpoint for real-time product data"""
    products = Product.query.all()
    return jsonify([{
        'id': p.product_id,
        'name': p.name,
        'current_price': p.current_price,
        'stock': p.stock
    } for p in products])
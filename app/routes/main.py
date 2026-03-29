from flask import Blueprint, render_template, current_app, jsonify
from datetime import datetime
from app.extensions import db
from app.models import Product, Category, DemandScore

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def home():
    """Homepage with dynamic product data from database"""
    try:
        # Get products with their latest demand scores
        products = Product.query.all()
        
        product_data = []
        for p in products:
            # Get latest demand score
            demand = DemandScore.query.filter_by(product_id=p.product_id)\
                .order_by(DemandScore.calculated_at.desc()).first()
            
            demand_label = "In Stock"
            demand_class = "emerald"
            
            if demand:
                score = demand.demand_score
                if score >= 80:
                    demand_label = "High Demand"
                    demand_class = "red"
                elif score >= 60:
                    demand_label = "Trending"
                    demand_class = "orange"
                elif score <= 30:
                    demand_label = "Low Demand"
                    demand_class = "emerald"
            
            # Check stock
            if p.stock <= 10:
                demand_label = "Low Stock"
                demand_class = "red"
            
            # Calculate price change indicator
            price_change = 0
            if p.base_price > 0:
                price_change = ((p.current_price - p.base_price) / p.base_price) * 100
            
            product_data.append({
                'id': p.product_id,
                'name': p.name,
                'current_price': p.current_price,
                'base_price': p.base_price,
                'stock': p.stock,
                'demand_label': demand_label,
                'demand_class': demand_class,
                'price_change_pct': round(price_change, 1),
                'category_id': p.category_id,
                'image_url': p.image_url or ''
            })
        
        # Get categories for filtering
        categories = Category.query.all()
        
        # Get featured products (first 4 by demand or stock)
        featured = sorted(product_data, key=lambda x: x['stock'], reverse=True)[:4]
        
        return render_template(
            'home.html',
            products=product_data,
            featured=featured,
            categories=categories,
            num_sim_users=current_app.config['NUM_SIMULATED_USERS'],
            tick_rate=current_app.config['SIMULATION_TICK_RATE']
        )
    except Exception as e:
        # Fallback if database not ready
        return render_template(
            'home.html',
            products=[],
            featured=[],
            categories=[],
            num_sim_users=current_app.config['NUM_SIMULATED_USERS'],
            tick_rate=current_app.config['SIMULATION_TICK_RATE']
        )

@main_bp.route('/status')
def status():
    return jsonify({
        "message": "PriceFlow is LIVE",
        "simulated_users": current_app.config['NUM_SIMULATED_USERS'],
        "simulation_tick": current_app.config['SIMULATION_TICK_RATE'],
        "timestamp": datetime.utcnow().isoformat()
    })

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
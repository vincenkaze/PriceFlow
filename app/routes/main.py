from flask import Blueprint, render_template, current_app, jsonify
from datetime import datetime
from app.extensions import db
from app.models import Product, Category, DemandScore

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def home():
    """Homepage with dynamic product data from database"""
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        # Log DB path for debugging
        db_uri = current_app.config.get('SQLALCHEMY_DATABASE_URI', 'unknown')
        logger.info(f"[HOME] Database: {db_uri}")
        
        # Get products with their latest demand scores
        products = Product.query.all()
        logger.info(f"[HOME] Found {len(products)} products in database")
        
        if not products:
            logger.warning("[HOME] No products found! Database may be empty.")
            return render_template(
                'home.html',
                products=[],
                featured=[],
                categories=[],
                num_sim_users=current_app.config['NUM_SIMULATED_USERS'],
                tick_rate=current_app.config['SIMULATION_TICK_RATE'],
                error="No products in database - run seed script"
            )
        
        product_data = []
        for p in products:
            # Get latest demand score
            demand = DemandScore.query.filter_by(product_id=p.product_id)\
                .order_by(DemandScore.calculated_at.desc()).first()
            
            demand_label = "Stable"
            demand_score = 50  # Baseline score for products with no activity
            
            if demand:
                score = demand.demand_score
                demand_score = score
                # Use actual demand score
                if score >= 80:
                    demand_label = "High Demand"
                elif score >= 60:
                    demand_label = "Trending"
                elif score <= 30:
                    demand_label = "Low Demand"
                else:
                    demand_label = "Stable"
            else:
                logger.debug(f"[HOME] No demand score for product {p.product_id} - using baseline")
            
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
                'demand_score': demand_score,  # Include for sorting
                'price_change_pct': round(price_change, 1),
                'category_id': p.category_id,
                'image_url': p.image_url or ''
            })
        
        # Get categories for filtering
        categories = Category.query.all()
        logger.info(f"[HOME] Found {len(categories)} categories")
        
        # Get featured products - sort by demand score (highest first) for hero section
        featured = sorted(product_data, key=lambda x: x['demand_score'], reverse=True)[:4]
        
        logger.info(f"[HOME] Featured products: {[p['name'] for p in featured]}")
        logger.info(f"[HOME] Demand scores: {[p['demand_score'] for p in featured]}")
        
        return render_template(
            'home.html',
            products=product_data,
            featured=featured,
            categories=categories,
            num_sim_users=current_app.config['NUM_SIMULATED_USERS'],
            tick_rate=current_app.config['SIMULATION_TICK_RATE']
        )
    except Exception as e:
        # Log the actual error instead of silently swallowing it
        logger.error(f"[HOME] Error rendering homepage: {e}", exc_info=True)
        return render_template(
            'home.html',
            products=[],
            featured=[],
            categories=[],
            num_sim_users=current_app.config['NUM_SIMULATED_USERS'],
            tick_rate=current_app.config['SIMULATION_TICK_RATE'],
            error=str(e)
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
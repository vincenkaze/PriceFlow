import os
from flask import Blueprint, render_template, redirect, url_for, request, session, flash, current_app
from flask_login import login_user, logout_user, login_required, current_user
from datetime import datetime
from functools import wraps
from app.extensions import db
from app.models import User, Admin

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

# Admin credentials from environment variables (with defaults for development)
ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME', 'admin')
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'admin123')


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('admin_logged_in'):
            flash("Please log in to access admin area", "warning")
            return redirect(url_for('admin.login', next=request.path))
        return f(*args, **kwargs)
    return decorated_function


@admin_bp.route('/login', methods=['GET', 'POST'])
def login():
    if session.get('admin_logged_in'):
        return redirect(url_for('admin.dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session.permanent = True
            session['admin_logged_in'] = True
            
            admin = Admin.query.filter_by(username=username).first()
            if admin and admin.user_id:
                user = User.query.get(admin.user_id)
                if user:
                    login_user(user)
            
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('admin.dashboard'))
        else:
            flash("Invalid credentials!", "danger")
    
    return render_template('admin/login.html')


@admin_bp.route('/logout')
@admin_required
def logout():
    logout_user()
    session.pop('admin_logged_in', None)
    return redirect(url_for('main.home'))


@admin_bp.route('/dashboard')
@admin_required
def dashboard():
    from app.models import Product
    top_products = Product.query.limit(10).all()
    return render_template('admin/dashboard.html', top_products=top_products)


@admin_bp.route('/trigger-simulation')
@admin_required
def trigger_simulation():
    from modules.user_simulation import simulation
    if simulation.running:
        flash("Simulation is already running in background.", "info")
    else:
        try:
            with current_app.app_context():
                simulation._simulate_one_tick()
            flash("Simulation tick executed manually.", "success")
        except Exception as e:
            flash(f"Error running simulation: {e}", "danger")
    
    return redirect(url_for('admin.dashboard'))


@admin_bp.route('/trigger-demand')
@admin_required
def trigger_demand():
    from modules.demand_analysis import demand_analyzer
    demand_analyzer.refresh_active_products()
    flash("Demand analysis manually refreshed!", "success")
    return redirect(url_for('admin.dashboard'))


@admin_bp.route('/trigger-pricing')
@admin_required
def trigger_pricing():
    from modules.pricing_engine import pricing_engine
    try:
        with current_app.app_context():
            pricing_engine._update_prices()
        flash("Pricing engine manually triggered!", "success")
    except Exception as e:
        flash(f"Error updating prices: {e}", "danger")
    return redirect(url_for('admin.dashboard'))


@admin_bp.route('/products')
@admin_required
def products():
    """Product management page with edit capabilities"""
    return render_template('admin/products.html')


@admin_bp.route('/pricing')
@admin_required
def pricing():
    """Pricing adjustments page"""
    return render_template('admin/pricing.html')


@admin_bp.route('/analytics')
@admin_required
def analytics():
    """Analytics page with ML trend charts"""
    from app.models import Product
    top_products = Product.query.limit(10).all()
    return render_template('admin/analytics.html', top_products=top_products)
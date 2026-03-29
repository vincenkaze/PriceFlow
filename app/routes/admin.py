import os
from flask import Blueprint, render_template, redirect, url_for, request, session, flash, current_app
from datetime import datetime

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

# Admin credentials from environment variables (with defaults for development)
ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME', 'admin')
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'admin123')

@admin_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            # Set session with security flags
            session.permanent = True
            session['admin_logged_in'] = True
            flash("Login successful!", "success")
            return redirect(url_for('admin.dashboard'))
        else:
            flash("Invalid credentials!", "danger")
    
    return render_template('admin/login.html')


@admin_bp.route('/logout')
def logout():
    session.pop('admin_logged_in', None)
    flash("Logged out successfully.", "info")
    return redirect(url_for('admin.login'))


@admin_bp.route('/dashboard')
def dashboard():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin.login'))
    
    # Dashboard data is now fetched via API for real-time updates
    return render_template('admin/dashboard.html')


@admin_bp.route('/trigger-simulation')
def trigger_simulation():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin.login'))
    
    from modules.user_simulation import simulation
    if simulation.running:
        flash("Simulation is already running in background.", "info")
    else:
        # Manually trigger one simulation tick
        try:
            with current_app.app_context():
                simulation._simulate_one_tick()
            flash("Simulation tick executed manually.", "success")
        except Exception as e:
            flash(f"Error running simulation: {e}", "danger")
    
    return redirect(url_for('admin.dashboard'))


@admin_bp.route('/trigger-demand')
def trigger_demand():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin.login'))
    
    from modules.demand_analysis import demand_analyzer
    demand_analyzer.refresh_active_products()
    flash("Demand analysis manually refreshed!", "success")
    return redirect(url_for('admin.dashboard'))


@admin_bp.route('/trigger-pricing')
def trigger_pricing():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin.login'))
    
    from modules.pricing_engine import pricing_engine
    try:
        with current_app.app_context():
            pricing_engine._update_prices()
        flash("Pricing engine manually triggered!", "success")
    except Exception as e:
        flash(f"Error updating prices: {e}", "danger")
    return redirect(url_for('admin.dashboard'))


@admin_bp.route('/products')
def products():
    """Product management page with edit capabilities"""
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin.login'))
    
    return render_template('admin/products.html')
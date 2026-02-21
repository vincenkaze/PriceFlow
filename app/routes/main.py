from flask import Blueprint, render_template, current_app
from datetime import datetime

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def home():
    return render_template(
        'home.html',
        num_sim_users=200,
        tick_rate=current_app.config['SIMULATION_TICK_RATE']
    )

@main_bp.route('/status')
def status():
    return {
        "message": "PriceFlow is LIVE",
        "simulated_users": current_app.config['NUM_SIMULATED_USERS'],
        "simulation_tick": current_app.config['SIMULATION_TICK_RATE'],
        "timestamp": datetime.utcnow()
    }
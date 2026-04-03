import os
from datetime import timedelta

class Config:
    """Base config — the vibes all configs inherit from"""
    
    # === SECURITY ===
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'super-secret-key-2026-change-this-or-i-will-roast-you-in-viva'
    
    # === DATABASE ===
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = False                     # set True in dev if you wanna see raw SQL
    
    # === SESSION ===
    PERMANENT_SESSION_LIFETIME = timedelta(minutes=60)
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SECURE = False  # Set to True in production with HTTPS
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # === PROJECT-SPECIFIC CONFIG ===
    NUM_SIMULATED_USERS = 200                   # exactly as in your prescription PDFs
    SIMULATION_TICK_RATE = 4                    # seconds between simulation cycles (feels alive)
    DEMAND_WINDOW_MINUTES = 15                  # how far back we calculate demand score
    AUTO_RESTOCK_THRESHOLD = 5                  # when stock <= this → auto restock (in simulation)
    AUTO_RESTOCK_AMOUNT = 50                    # how many units to add
    
    # === DEMAND DYNAMICS - Let demand rise AND fall ===
    DEMAND_DECAY_RATE = 0.60                    # each minute older, multiply weight by this (0.60 = 40% decay/min) - MUCH FASTER
    DEMAND_RECENT_MINUTES = 5                   # recent window for trend detection
    DEMAND_INACTIVE_PENALTY = 20                # points lost when no activity in window
    SIMULATOR_ACTIVITY_RATE = 0.2               # only 20% of products get attention per tick
    DEMAND_TREND_THRESHOLD = 1.2                # recent/older ratio to be considered "rising"
    
    # === PRICING DEFAULTS ===
    DEFAULT_PRICE_INCREASE_PCT = 5.0
    DEFAULT_PRICE_DECREASE_PCT = 5.0
    
    # === PATHS ===
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    INSTANCE_DIR = os.path.join(BASE_DIR, '..', 'instance')


class DevelopmentConfig(Config):
    """Local dev — maximum chaos, minimum pain"""
    DEBUG = True
    ENV = 'development'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///../instance/pricing_dev.db'
    SQLALCHEMY_ECHO = True                      # see every query (super helpful while building)


class ProductionConfig(Config):
    """For when you show it to external examiner / put on GitHub"""
    DEBUG = False
    ENV = 'production'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///../instance/pricing.db'


class TestingConfig(Config):
    """For pytest later (yes we’re doing tests, don’t fight me)"""
    TESTING = True
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///../instance/pricing_test.db'
    WTF_CSRF_ENABLED = False


# This is what __init__.py will use
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
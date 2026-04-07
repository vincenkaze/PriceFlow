from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from .extensions import db

class Category(db.Model):
    __tablename__ = 'categories'
    category_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    min_price_pct = db.Column(db.Float, default=0.7)
    max_price_pct = db.Column(db.Float, default=1.5)

class UserType(db.Model):
    __tablename__ = 'user_types'
    type_id = db.Column(db.Integer, primary_key=True)
    type_name = db.Column(db.String(50), nullable=False)
    view_probability = db.Column(db.Float, default=0.8)
    cart_probability = db.Column(db.Float, default=0.3)
    purchase_probability = db.Column(db.Float, default=0.1)
    price_sensitivity = db.Column(db.Float, default=0.5)

class Product(db.Model):
    __tablename__ = 'products'
    product_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.category_id'))
    base_price = db.Column(db.Float(precision=2), nullable=False)
    current_price = db.Column(db.Float(precision=2), nullable=False)
    stock = db.Column(db.Integer, nullable=False)
    min_price = db.Column(db.Float(precision=2), nullable=False, default=0.0)
    max_price = db.Column(db.Float(precision=2), nullable=False, default=99999.99)
    image_url = db.Column(db.String(500), default='')
    last_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    user_id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(100))
    email = db.Column(db.String(120))
    role = db.Column(db.String(20), default='customer')
    last_login = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    orders = db.relationship('Order', backref='user', lazy=True)

    @property
    def id(self):
        return self.user_id

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Admin(db.Model):
    __tablename__ = 'admins'
    admin_id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(100))
    email = db.Column(db.String(120))
    role = db.Column(db.String(20), default='admin')
    last_login = db.Column(db.DateTime)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=True)

    user = db.relationship('User', foreign_keys=[user_id], backref='admin_account')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class SimulatedUser(db.Model):
    __tablename__ = 'simulated_users'
    sim_user_id = db.Column(db.Integer, primary_key=True)
    type_id = db.Column(db.Integer, db.ForeignKey('user_types.type_id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class UserAction(db.Model):
    __tablename__ = 'user_actions'
    action_id = db.Column(db.Integer, primary_key=True)
    sim_user_id = db.Column(db.Integer, db.ForeignKey('simulated_users.sim_user_id'))
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'))
    product_id = db.Column(db.Integer, db.ForeignKey('products.product_id'), nullable=False)
    action_type = db.Column(db.String(20), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class DemandScore(db.Model):
    __tablename__ = 'demand_scores'
    score_id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.product_id'), nullable=False)
    demand_score = db.Column(db.Integer, nullable=False)
    period_start = db.Column(db.DateTime)
    period_end = db.Column(db.DateTime)
    calculated_at = db.Column(db.DateTime, default=datetime.utcnow)

class PriceHistory(db.Model):
    __tablename__ = 'price_history'
    history_id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.product_id'), nullable=False)
    old_price = db.Column(db.Float(precision=2))
    new_price = db.Column(db.Float(precision=2))
    demand_score = db.Column(db.Integer)
    stock = db.Column(db.Integer)
    change_reason = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class AdminAction(db.Model):
    __tablename__ = 'admin_actions'
    action_id = db.Column(db.Integer, primary_key=True)
    admin_id = db.Column(db.Integer, db.ForeignKey('admins.admin_id'), nullable=False)
    action_type = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class PricingRule(db.Model):
    __tablename__ = 'pricing_rules'
    rule_id = db.Column(db.Integer, primary_key=True)
    rule_name = db.Column(db.String(100), nullable=False)
    demand_threshold_high = db.Column(db.Integer, default=80)
    demand_threshold_low = db.Column(db.Integer, default=20)
    stock_threshold_low = db.Column(db.Integer, default=30)
    stock_threshold_high = db.Column(db.Integer, default=60)
    stock_threshold_excess = db.Column(db.Integer, default=80)
    price_increase_pct = db.Column(db.Float, default=5.0)
    price_decrease_pct = db.Column(db.Float, default=5.0)
    price_mid_pct = db.Column(db.Float, default=1.1)
    price_min_aggressive_pct = db.Column(db.Float, default=0.65)
    min_price_pct = db.Column(db.Float, default=0.7)
    max_price_pct = db.Column(db.Float, default=1.5)
    is_global = db.Column(db.Boolean, default=True)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.category_id'))
    is_active = db.Column(db.Boolean, default=True)


class Order(db.Model):
    __tablename__ = 'orders'
    order_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    status = db.Column(db.String(20), default='placed')
    total_amount = db.Column(db.Float, default=0.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    items = db.relationship('OrderItem', backref='order', lazy=True)


class OrderItem(db.Model):
    __tablename__ = 'order_items'
    item_id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.order_id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.product_id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price_at_purchase = db.Column(db.Float, nullable=False)

    product = db.relationship('Product')
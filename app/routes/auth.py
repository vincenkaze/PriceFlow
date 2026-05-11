from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_user, logout_user, login_required, current_user
from app.extensions import db
from app.models import User
from datetime import datetime
import re

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        
        if not username or not password:
            flash("Username and password are required", "danger")
            return render_template('auth/login.html', admin_login_url=url_for('admin.login'))
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user)
            user.last_login = datetime.utcnow()
            db.session.commit()
            
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('main.home'))
        else:
            flash("Invalid username or password", "danger")
    
    return render_template('auth/login.html', admin_login_url=url_for('admin.login'))


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        full_name = request.form.get('full_name', '').strip()
        password = request.form.get('password', '')
        
        if not username or not password:
            flash("Username and password are required", "danger")
            return render_template('auth/register.html')
        
        if len(username) < 3 or len(username) > 50:
            flash("Username must be 3-50 characters", "danger")
            return render_template('auth/register.html')
        
        if email and not re.match(r'^[\w\.-]+@[\w\.-]+\.\w{2,}$', email):
            flash("Invalid email format", "danger")
            return render_template('auth/register.html')
        
        if len(password) < 6:
            flash("Password must be at least 6 characters", "danger")
            return render_template('auth/register.html')
        
        if User.query.filter_by(username=username).first():
            flash("Username already exists", "danger")
            return render_template('auth/register.html')
        
        if email and User.query.filter_by(email=email).first():
            flash("Email already registered", "danger")
            return render_template('auth/register.html')
        
        user = User(
            username=username,
            email=email,
            full_name=full_name,
            role='customer'
        )
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        return redirect(url_for('auth.login'))
    
    return render_template('auth/register.html')


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.home'))
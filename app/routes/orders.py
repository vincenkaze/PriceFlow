from flask import Blueprint, render_template, redirect, url_for, request, flash, session
from flask_login import login_required, current_user
from app.models import Product, Order, OrderItem
from app.extensions import db

orders_bp = Blueprint('orders', __name__, url_prefix='/orders')


@orders_bp.route('/checkout', methods=['POST'])
@login_required
def checkout():
    cart = session.get('cart', {})
    
    if not cart:
        flash("Cart is empty", "warning")
        return redirect(url_for('cart.view_cart'))
    
    total_amount = 0
    order_items = []
    
    for product_id_str, quantity in cart.items():
        product_id = int(product_id_str)
        product = Product.query.get(product_id)
        
        if not product:
            flash(f"Product not found: {product_id}", "danger")
            return redirect(url_for('cart.view_cart'))
        
        if product.stock < quantity:
            flash(f"Insufficient stock for {product.name}", "warning")
            return redirect(url_for('cart.view_cart'))
        
        subtotal = product.current_price * quantity
        total_amount += subtotal
        
        order_items.append({
            'product': product,
            'quantity': quantity,
            'price_at_purchase': product.current_price
        })
        
        product.stock -= quantity
    
    order = Order(
        user_id=current_user.user_id,
        status='placed',
        total_amount=total_amount
    )
    db.session.add(order)
    db.session.flush()
    
    for item in order_items:
        order_item = OrderItem(
            order_id=order.order_id,
            product_id=item['product'].product_id,
            quantity=item['quantity'],
            price_at_purchase=item['price_at_purchase']
        )
        db.session.add(order_item)
    
    db.session.commit()
    
    session.pop('cart', None)
    
    flash(f"Order #{order.order_id} placed successfully!", "success")
    return redirect(url_for('orders.order_confirmation', order_id=order.order_id))


@orders_bp.route('/<int:order_id>')
@login_required
def order_confirmation(order_id):
    order = Order.query.get_or_404(order_id)
    
    if order.user_id != current_user.user_id:
        flash("Access denied", "danger")
        return redirect(url_for('orders.order_history'))
    
    return render_template('orders/confirmation.html', order=order)


@orders_bp.route('/history')
@login_required
def order_history():
    orders = Order.query.filter_by(user_id=current_user.user_id)\
        .order_by(Order.created_at.desc()).all()
    
    return render_template('orders/history.html', orders=orders)
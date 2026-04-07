from flask import Blueprint, render_template, redirect, url_for, request, flash, session
from flask_login import login_required, current_user
from app.models import Product
from app.extensions import db

cart_bp = Blueprint('cart', __name__, url_prefix='/cart')


@cart_bp.route('/')
def view_cart():
    cart = session.get('cart', {})
    
    cart_items = []
    total = 0
    
    for product_id_str, quantity in cart.items():
        product_id = int(product_id_str)
        product = Product.query.get(product_id)
        
        if product:
            subtotal = product.current_price * quantity
            cart_items.append({
                'product': product,
                'quantity': quantity,
                'subtotal': subtotal
            })
            total += subtotal
    
    return render_template('cart/cart.html', cart_items=cart_items, total=total)


@cart_bp.route('/add/<int:product_id>', methods=['POST'])
def add_to_cart(product_id):
    product = Product.query.get_or_404(product_id)
    quantity = int(request.form.get('quantity', 1))
    
    if product.stock < quantity:
        flash(f"Only {product.stock} units available", "warning")
        return redirect(url_for('main.product_detail', product_id=product_id))
    
    cart = session.get('cart', {})
    cart[str(product_id)] = cart.get(str(product_id), 0) + quantity
    session['cart'] = cart
    
    flash(f"Added {quantity} x {product.name} to cart", "success")
    
    next_page = request.args.get('next')
    return redirect(next_page) if next_page else redirect(url_for('cart.view_cart'))


@cart_bp.route('/remove/<int:product_id>', methods=['POST'])
def remove_from_cart(product_id):
    cart = session.get('cart', {})
    
    if str(product_id) in cart:
        del cart[str(product_id)]
        session['cart'] = cart
        flash("Item removed from cart", "success")
    
    return redirect(url_for('cart.view_cart'))


@cart_bp.route('/update/<int:product_id>', methods=['POST'])
def update_cart(product_id):
    quantity = int(request.form.get('quantity', 1))
    cart = session.get('cart', {})
    
    if quantity <= 0:
        if str(product_id) in cart:
            del cart[str(product_id)]
            flash("Item removed from cart", "success")
    else:
        product = Product.query.get(product_id)
        if product and product.stock >= quantity:
            cart[str(product_id)] = quantity
            flash("Cart updated", "success")
        else:
            flash(f"Only {product.stock if product else 0} units available", "warning")
            return redirect(url_for('cart.view_cart'))
    
    session['cart'] = cart
    return redirect(url_for('cart.view_cart'))


@cart_bp.route('/clear', methods=['POST'])
def clear_cart():
    session.pop('cart', None)
    flash("Cart cleared", "info")
    return redirect(url_for('cart.view_cart'))


@cart_bp.route('/count')
def cart_count():
    cart = session.get('cart', {})
    return sum(cart.values())
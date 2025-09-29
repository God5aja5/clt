import os
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app
from flask import jsonify
from models import Product, Lead, Visitor, SiteSettings, ProductImage, Category, db
from forms import LeadForm
from werkzeug.utils import secure_filename
import hashlib
import requests
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import json
from datetime import datetime
import re

bp = Blueprint('main', __name__)

# Helper functions
def get_or_create_visitor():
    """Get or create visitor record based on IP hash"""
    ip_address = request.remote_addr
    ip_hash = hashlib.sha256(ip_address.encode()).hexdigest()
    
    visitor = Visitor.query.filter_by(ip_hash=ip_hash).first()
    if not visitor:
        visitor = Visitor(ip_hash=ip_hash)
        db.session.add(visitor)
    else:
        visitor.views_count += 1
        visitor.last_seen = datetime.utcnow()
    
    db.session.commit()
    return visitor

def get_site_settings():
    """Get site settings, create default if not exists"""
    settings = SiteSettings.query.first()
    if not settings:
        settings = SiteSettings()
        db.session.add(settings)
        db.session.commit()
    return settings

def calculate_discounted_price(original_price, discount_percent):
    """Calculate discounted price"""
    return round(original_price * (1 - discount_percent / 100), 2)

def validate_phone_number(phone):
    """Validate phone number format (10-15 digits)"""
    # Remove any non-digit characters
    digits_only = re.sub(r'\D', '', phone)
    return len(digits_only) >= 10 and len(digits_only) <= 15

def validate_telegram_username(username):
    """Validate telegram username format"""
    if not username:
        return True  # Username is optional
    # Remove @ if present and validate
    username = username.lstrip('@')
    return re.match(r'^[a-zA-Z][a-zA-Z0-9_]{4,31}$', username) is not None

def notify_admin_via_telegram(message_text):
    """Send notification to admin via Telegram"""
    # Get bot token and chat ID from database settings
    settings = get_site_settings()
    bot_token = settings.telegram_bot_token
    chat_id = settings.admin_telegram_chat_id
    
    if not bot_token or not chat_id:
        print("Telegram credentials not set in site settings")
        return False
    
    try:
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        payload = {
            'chat_id': chat_id,
            'text': message_text,
            'parse_mode': 'HTML'
        }
        response = requests.post(url, json=payload)
        return response.status_code == 200
    except Exception as e:
        print(f"Error sending Telegram notification: {e}")
        return False

def send_admin_email(subject, body):
    """Send email notification to admin"""
    # Get SMTP settings from environment variables (for security)
    smtp_host = os.environ.get('SMTP_HOST')
    smtp_port = int(os.environ.get('SMTP_PORT', 587))
    smtp_user = os.environ.get('SMTP_USER')
    smtp_pass = os.environ.get('SMTP_PASS')
    admin_email = smtp_user  # Using admin's email as recipient
    
    if not all([smtp_host, smtp_port, smtp_user, smtp_pass]):
        print("SMTP credentials not set in environment variables")
        return False
    
    try:
        msg = MIMEMultipart()
        msg['From'] = smtp_user
        msg['To'] = admin_email
        msg['Subject'] = subject
        
        msg.attach(MIMEText(body, 'html'))
        
        server = smtplib.SMTP(smtp_host, smtp_port)
        server.starttls()
        server.login(smtp_user, smtp_pass)
        
        text = msg.as_string()
        server.sendmail(smtp_user, admin_email, text)
        server.quit()
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False

# Routes
@bp.route('/')
def index():
    get_or_create_visitor()  # Track visitor
    settings = get_site_settings()
    
    # Get active products, ordered by newest first
    products = Product.query.filter_by(active=True).order_by(Product.created_at.desc()).all()
    
    # Get hot products to display prominently
    hot_products = Product.query.filter_by(active=True, is_hot_product=True).limit(4).all()
    
    # Calculate discounted prices for each product
    for product in products:
        product.discounted_price = product.get_discounted_price(settings.global_discount_percent)
    
    for product in hot_products:
        product.discounted_price = product.get_discounted_price(settings.global_discount_percent)
    
    return render_template('public/index.html', 
                         products=products, 
                         hot_products=hot_products,
                         settings=settings)

@bp.route('/product/<int:product_id>')
def product_detail(product_id):
    get_or_create_visitor()  # Track visitor
    settings = get_site_settings()
    
    product = Product.query.get_or_404(product_id)
    if not product.active:
        flash('Product not found', 'error')
        return redirect(url_for('main.index'))
    
    # Increment product view count
    product.views += 1
    db.session.commit()
    
    # Calculate discounted price
    product.discounted_price = product.get_discounted_price(settings.global_discount_percent)
    
    return render_template('public/product_detail.html', product=product, settings=settings)

@bp.route('/cart')
def cart():
    cart_items = session.get('cart', [])
    settings = get_site_settings()
    
    # Get product details for items in cart
    products_in_cart = []
    subtotal = 0
    
    for item in cart_items:
        product = Product.query.get(item['product_id'])
        if product:
            discounted_price = product.get_discounted_price(settings.global_discount_percent)
            line_total = discounted_price * item['quantity']
            
            products_in_cart.append({
                'product': product,
                'quantity': item['quantity'],
                'unit_price': discounted_price,
                'line_total': line_total
            })
            subtotal += line_total
    
    return render_template('public/cart.html', 
                          products_in_cart=products_in_cart, 
                          subtotal=subtotal, 
                          settings=settings)

@bp.route('/cart/add', methods=['POST'])
def add_to_cart():
    product_id = request.form.get('product_id', type=int)
    quantity = request.form.get('quantity', type=int, default=1)
    
    if not product_id or quantity <= 0:
        flash('Invalid product or quantity', 'error')
        return redirect(request.referrer or url_for('main.index'))
    
    # Check if product exists and is active
    product = Product.query.filter_by(id=product_id, active=True).first()
    if not product:
        flash('Product not available', 'error')
        return redirect(request.referrer or url_for('main.index'))
    
    # Check stock if stock tracking is enabled
    if product.stock is not None and quantity > product.stock:
        flash(f'Only {product.stock} items available in stock', 'error')
        return redirect(request.referrer or url_for('main.index'))
    
    # Increment add_to_cart_count
    product.add_to_cart_count += quantity
    db.session.commit()
    
    # Add to cart session
    cart = session.get('cart', [])
    
    # Check if product already in cart
    item_exists = False
    for item in cart:
        if item['product_id'] == product_id:
            item['quantity'] += quantity
            item_exists = True
            break
    
    if not item_exists:
        cart.append({
            'product_id': product_id,
            'quantity': quantity
        })
    
    session['cart'] = cart
    flash('Product added to cart!', 'success')
    
    return redirect(url_for('main.cart'))

@bp.route('/cart/remove', methods=['POST'])
def remove_from_cart():
    product_id = request.form.get('product_id', type=int)
    
    if product_id:
        cart = session.get('cart', [])
        cart = [item for item in cart if item['product_id'] != product_id]
        session['cart'] = cart
    
    return redirect(url_for('main.cart'))

@bp.route('/checkout', methods=['GET', 'POST'])
def checkout():
    cart_items = session.get('cart', [])
    if not cart_items:
        flash('Your cart is empty', 'error')
        return redirect(url_for('main.index'))
    
    settings = get_site_settings()
    
    # Get product details for items in cart
    products_in_cart = []
    subtotal = 0
    
    for item in cart_items:
        product = Product.query.get(item['product_id'])
        if product:
            discounted_price = product.get_discounted_price(settings.global_discount_percent)
            line_total = discounted_price * item['quantity']
            
            products_in_cart.append({
                'product': product,
                'quantity': item['quantity'],
                'unit_price': discounted_price,
                'line_total': line_total
            })
            subtotal += line_total
    
    form = LeadForm()
    if form.validate_on_submit():
        # Validate phone number
        if not validate_phone_number(form.phone_number.data):
            flash('Phone number must be 10-15 digits', 'error')
            return render_template('public/checkout.html', form=form, 
                                 products_in_cart=products_in_cart, 
                                 subtotal=subtotal, 
                                 settings=settings)
        
        # Validate telegram username if provided
        if form.telegram_username.data and not validate_telegram_username(form.telegram_username.data):
            flash('Invalid Telegram username format', 'error')
            return render_template('public/checkout.html', form=form, 
                                 products_in_cart=products_in_cart, 
                                 subtotal=subtotal, 
                                 settings=settings)
        
        # Generate unique order ID
        import uuid
        order_id = f"ORD{int(datetime.utcnow().timestamp())}{str(uuid.uuid4())[:8].upper()}"
        
        # Create lead record
        lead = Lead(
            order_id=order_id,
            full_name=form.full_name.data,
            email=form.email.data,
            phone_number=form.phone_number.data,
            telegram_username=form.telegram_username.data,
            products_json=json.dumps(cart_items),
            total_amount=subtotal,
            message=form.message.data
        )
        
        db.session.add(lead)
        db.session.commit()
        
        # Prepare notification message for Telegram
        product_titles = []
        product_ids = []
        for item in cart_items:
            product = Product.query.get(item['product_id'])
            if product:
                product_titles.append(f"{product.title} (x{item['quantity']})")
                product_ids.append(str(product.id))
        
        telegram_message = f"""
🆕 <b>New Lead Received!</b>

👤 <b>Name:</b> {lead.full_name}
📧 <b>Email:</b> {lead.email}
📱 <b>Phone:</b> {lead.phone_number}
💬 <b>Telegram:</b> {lead.telegram_username or 'N/A'}

🛍️ <b>Products:</b>
{chr(10).join([f'• {title}' for title in product_titles])}

💰 <b>Total Amount:</b> ₹{lead.total_amount:.2f}

📋 <b>Message:</b> {lead.message or 'N/A'}

🆔 <b>Lead ID:</b> {lead.id}
🕒 <b>Time:</b> {lead.created_at.strftime('%Y-%m-%d %H:%M:%S')}
        """
        
        # Send Telegram notification
        notify_admin_via_telegram(telegram_message)
        
        # Prepare email notification
        email_subject = f"New Baign Mart Lead: {lead.full_name} - {' & '.join(product_titles[:3])}"
        email_body = f"""
        <h2>New Lead Received!</h2>
        <p><strong>Name:</strong> {lead.full_name}</p>
        <p><strong>Email:</strong> {lead.email}</p>
        <p><strong>Phone:</strong> {lead.phone_number}</p>
        <p><strong>Telegram:</strong> {lead.telegram_username or 'N/A'}</p>
        
        <h3>Products Ordered:</h3>
        <ul>
        {"".join([f'<li>{title}</li>' for title in product_titles])}
        </ul>
        
        <p><strong>Total Amount:</strong> ₹{lead.total_amount:.2f}</p>
        <p><strong>Message:</strong> {lead.message or 'N/A'}</p>
        
        <p><strong>Lead ID:</strong> {lead.id}</p>
        <p><strong>Time:</strong> {lead.created_at.strftime('%Y-%m-%d %H:%M:%S')}</p>
        """
        
        # Send email notification
        send_admin_email(email_subject, email_body)
        
        # Store order ID in session for user reference
        session['last_order_id'] = lead.order_id
        
        # Clear cart after successful checkout
        session.pop('cart', None)
        
        return render_template('public/checkout_success.html', settings=settings, order_id=lead.order_id)
    
    return render_template('public/checkout.html', form=form, 
                         products_in_cart=products_in_cart, 
                         subtotal=subtotal, 
                         settings=settings)


@bp.route('/my-orders')
def my_orders():
    settings = get_site_settings()
    
    # Get user's last order from session
    last_order_id = session.get('last_order_id')
    user_orders = []
    
    if last_order_id:
        # Try to find the specific order
        order = Lead.query.filter_by(order_id=last_order_id).first()
        if order:
            user_orders = [order]
    
    # Prepare product information for each order
    for order in user_orders:
        products_data = order.get_products()
        order.processed_products = []
        for item in products_data:
            product_id = item.get('product_id')
            quantity = item.get('quantity', 1)
            if product_id:
                product = Product.query.get(product_id)
                if product:
                    order.processed_products.append({
                        'product': product,
                        'quantity': quantity,
                        'unit_price': product.get_discounted_price(settings.global_discount_percent),
                        'line_total': product.get_discounted_price(settings.global_discount_percent) * quantity
                    })
                else:
                    order.processed_products.append({
                        'product': None,
                        'quantity': quantity,
                        'unit_price': 0,
                        'line_total': 0,
                        'title': f'Product {product_id} (Unavailable)'
                    })
            else:
                order.processed_products.append({
                    'product': None,
                    'quantity': quantity,
                    'unit_price': 0,
                    'line_total': 0,
                    'title': f'Unknown Product'
                })
    
    return render_template('public/my_orders.html', 
                         user_orders=user_orders, 
                         settings=settings)


@bp.route('/order-lookup', methods=['GET', 'POST'])
def order_lookup():
    settings = get_site_settings()
    order_id = request.form.get('order_id', '') if request.method == 'POST' else ''
    order = None
    
    if order_id:
        # Find the specific order
        order = Lead.query.filter_by(order_id=order_id).first()
        
        # Prepare product information for the order if it exists
        if order:
            products_data = order.get_products()
            order.processed_products = []
            for item in products_data:
                product_id = item.get('product_id')
                quantity = item.get('quantity', 1)
                if product_id:
                    product = Product.query.get(product_id)
                    if product:
                        order.processed_products.append({
                            'product': product,
                            'quantity': quantity,
                            'unit_price': product.get_discounted_price(settings.global_discount_percent),
                            'line_total': product.get_discounted_price(settings.global_discount_percent) * quantity
                        })
                    else:
                        order.processed_products.append({
                            'product': None,
                            'quantity': quantity,
                            'unit_price': 0,
                            'line_total': 0,
                            'title': f'Product {product_id} (Unavailable)'
                        })
                else:
                    order.processed_products.append({
                        'product': None,
                        'quantity': quantity,
                        'unit_price': 0,
                        'line_total': 0,
                        'title': f'Unknown Product'
                    })
        # If no order is found, order remains None, which is handled in the template
    else:
        # If no order_id was provided, don't set processed_products
        pass
    
    return render_template('public/order_lookup.html', 
                         order=order, 
                         order_id=order_id,
                         settings=settings)


@bp.route('/contact-telegram/<order_id>')
def contact_telegram(order_id):
    # Redirect to Telegram with the order ID
    telegram_username = "@wctw_private"
    # You can customize the message that gets pre-filled when the user opens Telegram
    message = f"Hello, I'm contacting you about my order {order_id}."
    telegram_url = f"https://t.me/{telegram_username.lstrip('@')}?start={order_id}"
    
    return redirect(telegram_url)


@bp.route('/contact-telegram-general')
def contact_telegram_general():
    # Redirect to Telegram for general contact
    telegram_username = "@wctw_private"
    telegram_url = f"https://t.me/{telegram_username.lstrip('@')}"
    
    return redirect(telegram_url)

@bp.route('/privacy')
def privacy():
    settings = get_site_settings()
    return render_template('public/page.html', content=settings.privacy_policy, title='Privacy Policy', settings=settings)

@bp.route('/terms')
def terms():
    settings = get_site_settings()
    return render_template('public/page.html', content=settings.terms, title='Terms & Conditions', settings=settings)

@bp.route('/about')
def about():
    settings = get_site_settings()
    return render_template('public/page.html', content=settings.about, title='About Us', settings=settings)

@bp.route('/cart/update_quantity', methods=['POST'])
def update_cart_quantity():
    product_id = request.form.get('product_id', type=int)
    quantity = request.form.get('quantity', type=int)
    
    if product_id and quantity and quantity > 0:
        cart = session.get('cart', [])
        for item in cart:
            if item['product_id'] == product_id:
                item['quantity'] = quantity
                break
        session['cart'] = cart
    
    return redirect(url_for('main.cart'))


@bp.route('/category/<int:category_id>')
def category_products(category_id):
    get_or_create_visitor()  # Track visitor
    settings = get_site_settings()
    
    category = Category.query.get_or_404(category_id)
    
    # Get active products in this category, ordered by newest first
    products = Product.query.filter_by(category_id=category_id, active=True).order_by(Product.created_at.desc()).all()
    
    # Calculate discounted prices for each product
    for product in products:
        product.discounted_price = product.get_discounted_price(settings.global_discount_percent)
    
    return render_template('public/index.html', 
                         products=products, 
                         settings=settings, 
                         selected_category=category)


@bp.route('/categories')
def all_categories():
    get_or_create_visitor()  # Track visitor
    settings = get_site_settings()
    
    # Get all active categories
    categories = Category.query.filter_by(is_active=True).all()
    
    return render_template('public/categories.html', 
                         categories=categories, 
                         settings=settings)
import os
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask import session
from werkzeug.utils import secure_filename
from models import Product, Lead, Visitor, SiteSettings, AdminUser, ProductImage, Category, db
from forms import LoginForm, ProductForm, SiteSettingsForm, AdminPageForm, CategoryForm
from datetime import datetime, timedelta
import json
import csv
from io import StringIO

bp = Blueprint('admin', __name__)

# Default route - redirect to login
@bp.route('/')
def index():
    return redirect(url_for('admin.login'))

# Helper function to check admin authentication
def admin_required(f):
    def decorated_function(*args, **kwargs):
        if not session.get('admin_logged_in'):
            return redirect(url_for('admin.login'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

# Allowed image extensions
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_site_settings():
    """Get site settings, create default if not exists"""
    settings = SiteSettings.query.first()
    if not settings:
        settings = SiteSettings()
        db.session.add(settings)
        db.session.commit()
    return settings

def calculate_analytics():
    """Calculate analytics for dashboard"""
    # Total visitors
    total_visitors = Visitor.query.count()
    
    # Total product views (sum of all product views)
    total_product_views = db.session.query(db.func.sum(Product.views)).scalar() or 0
    
    # Recent orders (last 10)
    recent_orders = Lead.query.order_by(Lead.created_at.desc()).limit(10).all()
    
    # Visitors in last 30 days
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    recent_visitors = Visitor.query.filter(Visitor.last_seen >= thirty_days_ago).count()
    
    # Product views in last 30 days
    recent_products = Product.query.filter(Product.created_at >= thirty_days_ago).all()
    recent_product_views = sum([p.views for p in recent_products])
    
    # Orders in last 30 days
    recent_orders_count = Lead.query.filter(Lead.created_at >= thirty_days_ago).count()
    
    return {
        'total_visitors': total_visitors,
        'total_product_views': total_product_views,
        'recent_orders': recent_orders,
        'recent_visitors': recent_visitors,
        'recent_product_views': recent_product_views,
        'recent_orders_count': recent_orders_count
    }

@bp.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        admin_user = AdminUser.query.filter_by(username=form.username.data).first()
        
        # SECURITY NOTE: In production, use hashed passwords!
        # This is a simple check for development as requested
        if admin_user and admin_user.check_password(form.password.data):
            session['admin_logged_in'] = True
            session.permanent = True  # Store login in session
            flash('Login successful!', 'success')
            return redirect(url_for('admin.dashboard'))
        else:
            flash('Invalid username or password', 'error')
    
    return render_template('admin/login.html', form=form)

@bp.route('/logout')
def logout():
    session.pop('admin_logged_in', None)
    flash('You have been logged out', 'info')
    return redirect(url_for('admin.login'))

@bp.route('/dashboard')
@admin_required
def dashboard():
    analytics = calculate_analytics()
    settings = get_site_settings()
    
    # Top products by views
    top_products = Product.query.order_by(Product.views.desc()).limit(5).all()
    
    return render_template('admin/dashboard.html', 
                         analytics=analytics,
                         settings=settings,
                         top_products=top_products)

@bp.route('/products')
@admin_required
def products():
    products = Product.query.all()
    settings = get_site_settings()
    return render_template('admin/products.html', products=products, settings=settings)

@bp.route('/products/new', methods=['GET', 'POST'])
@admin_required
def new_product():
    form = ProductForm()
    settings = get_site_settings()
    
    if form.validate_on_submit():
        # Validate uploaded images count (1-4)
        uploaded_files = request.files.getlist('images')
        if not uploaded_files or len([f for f in uploaded_files if f and f.filename != '']) < 1:
            flash('Please upload at least 1 image for the product', 'error')
            return render_template('admin/product_form.html', form=form, settings=settings, title="Add New Product")
        
        if len([f for f in uploaded_files if f and f.filename != '']) > 4:
            flash('You can upload maximum 4 images per product', 'error')
            return render_template('admin/product_form.html', form=form, settings=settings, title="Add New Product")
        
        # Get category_id from form if available
        category_id = request.form.get('category_id', type=int)
        
        # Create product
        product = Product(
            title=form.title.data,
            description=form.description.data,
            price_inr=float(form.price_inr.data),
            active=form.active.data,
            stock=form.stock.data if form.stock.data != '' else None,
            featured=form.featured.data,
            is_hot_product=form.is_hot_product.data if hasattr(form, 'is_hot_product') else False,
            discount_override=form.discount_override.data if form.discount_override.data is not None else None,
            per_product_discount=form.per_product_discount.data if form.per_product_discount.data is not None else None,
            category_id=category_id
        )
        
        db.session.add(product)
        db.session.flush()  # To get the product ID before committing
        
        # Handle image uploads
        valid_files = [f for f in uploaded_files if f and f.filename != '']
        for i, file in enumerate(valid_files):
            if file and file.filename != '' and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                # Add a timestamp to avoid conflicts
                name, ext = os.path.splitext(filename)
                timestamp = int(datetime.utcnow().timestamp())
                filename = f"{product.id}_{name}_{timestamp}_{i}{ext}"
                file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
                
                # Create upload directory if it doesn't exist
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                
                file.save(file_path)
                
                # Add to product images
                image = ProductImage(
                    product_id=product.id,
                    filename=filename,
                    position=i
                )
                db.session.add(image)
        
        db.session.commit()
        flash('Product added successfully!', 'success')
        return redirect(url_for('admin.products'))
    
    categories = Category.query.all()
    return render_template('admin/product_form.html', form=form, settings=settings, categories=categories, title="Add New Product")

@bp.route('/products/<int:product_id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_product(product_id):
    product = Product.query.get_or_404(product_id)
    form = ProductForm(obj=product)
    settings = get_site_settings()
    
    if request.method == 'GET':
        # Populate form with existing data
        form.title.data = product.title
        form.description.data = product.description
        form.price_inr.data = product.price_inr
        form.active.data = product.active
        form.stock.data = product.stock
        form.featured.data = product.featured
        form.discount_override.data = product.discount_override
    
    if form.validate_on_submit():
        # Update product
        product.title = form.title.data
        product.description = form.description.data
        product.price_inr = float(form.price_inr.data)
        product.active = form.active.data
        product.stock = form.stock.data if form.stock.data != '' else None
        product.featured = form.featured.data
        product.is_hot_product = form.is_hot_product.data if hasattr(form, 'is_hot_product') else False
        product.discount_override = form.discount_override.data if form.discount_override.data is not None else None
        product.per_product_discount = form.per_product_discount.data if form.per_product_discount.data is not None else None
        
        # Update category
        category_id = request.form.get('category_id', type=int)
        product.category_id = category_id
        
        # Handle image uploads
        # Check if user wants to replace images
        replace_images = request.form.get('replace_images', False)
        
        if replace_images:
            # Delete old images from filesystem
            for old_image in list(product.images):
                old_path = os.path.join(current_app.config['UPLOAD_FOLDER'], old_image.filename)
                if os.path.exists(old_path):
                    os.remove(old_path)
                db.session.delete(old_image)
            
            # Add new images
            uploaded_files = request.files.getlist('images')
            valid_files = [f for f in uploaded_files if f and f.filename != '']
            
            if len(valid_files) < 1:
                flash('Please upload at least 1 image for the product', 'error')
                return render_template('admin/product_form.html', form=form, settings=settings, product=product, title="Edit Product")
            
            if len(valid_files) > 4:
                flash('You can upload maximum 4 images per product', 'error')
                return render_template('admin/product_form.html', form=form, settings=settings, product=product, title="Edit Product")
            
            for i, file in enumerate(valid_files):
                if file and file.filename != '' and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    # Add a timestamp to avoid conflicts
                    name, ext = os.path.splitext(filename)
                    timestamp = int(datetime.utcnow().timestamp())
                    filename = f"{product.id}_{name}_{timestamp}_{i}{ext}"
                    file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
                    
                    # Create upload directory if it doesn't exist
                    os.makedirs(os.path.dirname(file_path), exist_ok=True)
                    
                    file.save(file_path)
                    
                    # Add to product images
                    image = ProductImage(
                        product_id=product.id,
                        filename=filename,
                        position=i
                    )
                    db.session.add(image)
        else:
            # Add new images without replacing existing ones
            uploaded_files = request.files.getlist('images')
            valid_files = [f for f in uploaded_files if f and f.filename != '']
            
            if len(valid_files) > 0:
                if len(valid_files) > 4:
                    flash('You can upload maximum 4 images at a time', 'error')
                    return render_template('admin/product_form.html', form=form, settings=settings, product=product, title="Edit Product")
                
                # Calculate the next position for new images
                next_position = len(product.images)
                
                for i, file in enumerate(valid_files):
                    if file and file.filename != '' and allowed_file(file.filename):
                        filename = secure_filename(file.filename)
                        # Add a timestamp to avoid conflicts
                        name, ext = os.path.splitext(filename)
                        timestamp = int(datetime.utcnow().timestamp())
                        filename = f"{product.id}_{name}_{timestamp}_{next_position + i}{ext}"
                        file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
                        
                        # Create upload directory if it doesn't exist
                        os.makedirs(os.path.dirname(file_path), exist_ok=True)
                        
                        file.save(file_path)
                        
                        # Add to product images
                        image = ProductImage(
                            product_id=product.id,
                            filename=filename,
                            position=next_position + i
                        )
                        db.session.add(image)
        
        db.session.commit()
        flash('Product updated successfully!', 'success')
        return redirect(url_for('admin.products'))
    
    categories = Category.query.all()
    return render_template('admin/product_form.html', form=form, settings=settings, product=product, categories=categories, title="Edit Product")

@bp.route('/products/<int:product_id>/toggle', methods=['POST'])
@admin_required
def toggle_product(product_id):
    product = Product.query.get_or_404(product_id)
    product.active = not product.active
    db.session.commit()
    
    status = "activated" if product.active else "deactivated"
    flash(f'Product {status} successfully!', 'success')
    return redirect(url_for('admin.products'))

@bp.route('/products/<int:product_id>/delete', methods=['POST'])
@admin_required
def delete_product(product_id):
    product = Product.query.get_or_404(product_id)
    
    # Delete product images from filesystem
    for image in product.images:
        image_path = os.path.join(current_app.config['UPLOAD_FOLDER'], image.filename)
        if os.path.exists(image_path):
            os.remove(image_path)
    
    db.session.delete(product)
    db.session.commit()
    
    flash('Product deleted successfully!', 'success')
    return redirect(url_for('admin.products'))


# Category management routes
@bp.route('/categories')
@admin_required
def categories():
    categories = Category.query.all()
    settings = get_site_settings()
    return render_template('admin/categories.html', categories=categories, settings=settings)


@bp.route('/categories/new', methods=['GET', 'POST'])
@admin_required
def new_category():
    form = CategoryForm()
    settings = get_site_settings()
    
    if form.validate_on_submit():
        category = Category(
            name=form.name.data,
            description=form.description.data,
            is_active=form.is_active.data,
            featured=form.featured.data
        )
        
        db.session.add(category)
        db.session.commit()
        flash('Category added successfully!', 'success')
        return redirect(url_for('admin.categories'))
    
    return render_template('admin/category_form.html', form=form, settings=settings, title="Add New Category")


@bp.route('/categories/<int:category_id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_category(category_id):
    category = Category.query.get_or_404(category_id)
    form = CategoryForm(obj=category)
    settings = get_site_settings()
    
    if request.method == 'GET':
        # Populate form with existing data
        form.name.data = category.name
        form.description.data = category.description
        form.is_active.data = category.is_active
        form.featured.data = category.featured
    
    if form.validate_on_submit():
        # Update category
        category.name = form.name.data
        category.description = form.description.data
        category.is_active = form.is_active.data
        category.featured = form.featured.data
        
        db.session.commit()
        flash('Category updated successfully!', 'success')
        return redirect(url_for('admin.categories'))
    
    return render_template('admin/category_form.html', form=form, settings=settings, category=category, title="Edit Category")


@bp.route('/categories/<int:category_id>/toggle', methods=['POST'])
@admin_required
def toggle_category(category_id):
    category = Category.query.get_or_404(category_id)
    category.is_active = not category.is_active
    db.session.commit()
    
    status = "activated" if category.is_active else "deactivated"
    flash(f'Category {status} successfully!', 'success')
    return redirect(url_for('admin.categories'))


@bp.route('/categories/<int:category_id>/delete', methods=['POST'])
@admin_required
def delete_category(category_id):
    category = Category.query.get_or_404(category_id)
    
    # Check if category has products
    if category.products:
        flash('Cannot delete category that has products assigned to it', 'error')
        return redirect(url_for('admin.categories'))
    
    db.session.delete(category)
    db.session.commit()
    
    flash('Category deleted successfully!', 'success')
    return redirect(url_for('admin.categories'))

@bp.route('/settings', methods=['GET', 'POST'])
@admin_required
def settings():
    settings = get_site_settings()
    form = SiteSettingsForm(obj=settings)
    
    if request.method == 'GET':
        # Populate form with existing data
        form.store_name.data = settings.store_name
        form.banner_text.data = settings.banner_text
        form.global_discount_percent.data = settings.global_discount_percent
        form.theme_name.data = settings.theme_name
        form.contact_email.data = settings.contact_email
        form.contact_phone.data = settings.contact_phone
        form.contact_address.data = settings.contact_address
        form.telegram_bot_token.data = settings.telegram_bot_token
        form.admin_telegram_chat_id.data = settings.admin_telegram_chat_id
        form.privacy_policy.data = settings.privacy_policy
        form.terms.data = settings.terms
        form.about.data = settings.about
    
    if form.validate_on_submit():
        # Update settings
        settings.store_name = form.store_name.data
        settings.banner_text = form.banner_text.data
        settings.global_discount_percent = form.global_discount_percent.data
        settings.theme_name = form.theme_name.data
        settings.contact_email = form.contact_email.data
        settings.contact_phone = form.contact_phone.data
        settings.contact_address = form.contact_address.data
        settings.telegram_bot_token = form.telegram_bot_token.data
        settings.admin_telegram_chat_id = form.admin_telegram_chat_id.data
        settings.privacy_policy = form.privacy_policy.data
        settings.terms = form.terms.data
        settings.about = form.about.data
        
        db.session.commit()
        flash('Settings updated successfully!', 'success')
        return redirect(url_for('admin.settings'))
    
    return render_template('admin/settings.html', form=form, settings=settings)

@bp.route('/leads')
@admin_required
def leads():
    leads = Lead.query.order_by(Lead.created_at.desc()).all()
    settings = get_site_settings()
    
    # Get product titles for each lead
    for lead in leads:
        products_data = json.loads(lead.products_json) if lead.products_json else []
        product_titles = []
        for item in products_data:
            product = Product.query.get(item['product_id'])
            if product:
                product_titles.append(f"{product.title} (x{item['quantity']})")
        lead.product_titles = product_titles
    
    return render_template('admin/leads.html', leads=leads, settings=settings)

@bp.route('/orders')
@admin_required
def orders():
    # Get all orders
    orders = Lead.query.order_by(Lead.created_at.desc()).all()
    settings = get_site_settings()
    
    pending_orders = [order for order in orders if order.status == 'pending']
    completed_orders = [order for order in orders if order.status == 'completed']
    other_orders = [order for order in orders if order.status not in ['pending', 'completed']]
    
    # Get product titles for each order
    for order in orders:
        products_data = json.loads(order.products_json) if order.products_json else []
        product_titles = []
        for item in products_data:
            product = Product.query.get(item['product_id'])
            if product:
                product_titles.append(f"{product.title} (x{item['quantity']})")
        order.product_titles = product_titles
    
    return render_template('admin/orders.html', 
                         pending_orders=pending_orders,
                         completed_orders=completed_orders,
                         other_orders=other_orders,
                         settings=settings)

@bp.route('/order/<string:order_id>')
@admin_required
def order_detail(order_id):
    order = Lead.query.filter_by(order_id=order_id).first_or_404()
    settings = get_site_settings()
    
    # Get product details for the order
    products_data = json.loads(order.products_json) if order.products_json else []
    product_details = []
    for item in products_data:
        product = Product.query.get(item['product_id'])
        if product:
            product_details.append({
                'product': product,
                'quantity': item['quantity'],
                'unit_price': product.get_discounted_price(settings.global_discount_percent),
                'subtotal': product.get_discounted_price(settings.global_discount_percent) * item['quantity']
            })
    
    order.product_details = product_details
    
    return render_template('admin/order_detail.html', order=order, settings=settings)

@bp.route('/order/<string:order_id>/update_status', methods=['POST'])
@admin_required
def update_order_status(order_id):
    order = Lead.query.filter_by(order_id=order_id).first_or_404()
    new_status = request.form.get('status')
    
    if new_status in ['pending', 'completed', 'contacted']:
        order.status = new_status
        db.session.commit()
        flash(f'Order status updated to {new_status.title()}', 'success')
    else:
        flash('Invalid status', 'error')
    
    return redirect(url_for('admin.order_detail', order_id=order_id))

@bp.route('/order-lookup', methods=['GET', 'POST'])
@admin_required
def order_lookup():
    order_id = request.form.get('order_id', '') if request.method == 'POST' else request.args.get('order_id', '')
    lead = None
    leads = Lead.query.order_by(Lead.created_at.desc()).limit(10).all()  # Get recent orders
    settings = get_site_settings()
    
    if order_id:
        lead = Lead.query.filter_by(order_id=order_id).first()
        if lead:
            products_data = json.loads(lead.products_json) if lead.products_json else []
            product_details = []
            for item in products_data:
                product = Product.query.get(item['product_id'])
                if product:
                    product_details.append({
                        'product': product,
                        'quantity': item['quantity']
                    })
            lead.product_details = product_details
    
    return render_template('admin/order_lookup.html', lead=lead, order_id=order_id, leads=leads, settings=settings)

@bp.route('/analytics')
@admin_required
def analytics():
    settings = get_site_settings()
    analytics_data = calculate_analytics()
    
    # Get product analytics
    all_products = Product.query.all()
    
    return render_template('admin/analytics.html', 
                         analytics=analytics_data,
                         products=all_products,
                         settings=settings)

@bp.route('/export/orders.csv')
@admin_required
def export_orders():
    # Create CSV for orders
    orders = Lead.query.all()
    
    # Create a StringIO object to write CSV data
    output = StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow(['ID', 'Full Name', 'Email', 'Phone', 'Telegram', 'Products', 'Total Amount', 'Status', 'Created At'])
    
    # Write data
    for order in orders:
        products_data = json.loads(order.products_json) if order.products_json else []
        product_titles = []
        for item in products_data:
            product = Product.query.get(item['product_id'])
            if product:
                product_titles.append(f"{product.title} (x{item['quantity']})")
        
        writer.writerow([
            order.id,
            order.full_name,
            order.email,
            order.phone_number,
            order.telegram_username,
            '; '.join(product_titles),
            order.total_amount,
            order.status,
            order.created_at.strftime('%Y-%m-%d %H:%M:%S')
        ])
    
    # Convert StringIO to string and return as response
    csv_data = output.getvalue()
    output.close()
    
    from flask import Response
    return Response(
        csv_data,
        mimetype='text/csv',
        headers={'Content-Disposition': 'attachment; filename=orders.csv'}
    )

@bp.route('/export/leads.csv')
@admin_required
def export_leads():
    # Create CSV for leads (same as orders in this implementation)
    leads = Lead.query.all()
    
    # Create a StringIO object to write CSV data
    output = StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow(['ID', 'Full Name', 'Email', 'Phone', 'Telegram', 'Products', 'Total Amount', 'Status', 'Created At'])
    
    # Write data
    for lead in leads:
        products_data = json.loads(lead.products_json) if lead.products_json else []
        product_titles = []
        for item in products_data:
            product = Product.query.get(item['product_id'])
            if product:
                product_titles.append(f"{product.title} (x{item['quantity']})")
        
        writer.writerow([
            lead.id,
            lead.full_name,
            lead.email,
            lead.phone_number,
            lead.telegram_username,
            '; '.join(product_titles),
            lead.total_amount,
            lead.status,
            lead.created_at.strftime('%Y-%m-%d %H:%M:%S')
        ])
    
    # Convert StringIO to string and return as response
    csv_data = output.getvalue()
    output.close()
    
    from flask import Response
    return Response(
        csv_data,
        mimetype='text/csv',
        headers={'Content-Disposition': 'attachment; filename=leads.csv'}
    )


@bp.route('/products/<int:product_id>/toggle_hot', methods=['POST'])
@admin_required
def toggle_hot_product(product_id):
    product = Product.query.get_or_404(product_id)
    product.is_hot_product = not product.is_hot_product
    db.session.commit()
    
    status = "marked as hot" if product.is_hot_product else "removed from hot"
    flash(f'Product {status} successfully!', 'success')
    return redirect(url_for('admin.products'))
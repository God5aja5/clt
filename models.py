from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json

# Initialize db instance globally
db = SQLAlchemy()

class Product(db.Model):
    __tablename__ = 'products'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    price_inr = db.Column(db.Float, nullable=False)
    active = db.Column(db.Boolean, default=True)
    stock = db.Column(db.Integer, default=None)  # Optional stock tracking
    views = db.Column(db.Integer, default=0)
    add_to_cart_count = db.Column(db.Integer, default=0)
    featured = db.Column(db.Boolean, default=False)
    discount_override = db.Column(db.Float, default=None)  # Per-product discount override
    per_product_discount = db.Column(db.Float, default=None)  # Additional per product discount
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship with images
    images = db.relationship('ProductImage', backref='product', lazy=True, cascade='all, delete-orphan')
    
    # Relationship with category
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=True)
    # Add hot/featured product functionality
    is_hot_product = db.Column(db.Boolean, default=False)  # For hot products on homepage
    
    def get_first_image(self):
        """Get the first image for this product"""
        if self.images:
            # Sort by position and return the first one
            first_img = sorted(self.images, key=lambda x: x.position or 0)[0]
            return first_img
        return None
    
    def get_discounted_price(self, global_discount_percent):
        """Calculate discounted price based on global, per product, or override discount"""
        # Priority: discount_override (specific for this product) > per_product_discount > global_discount
        if self.discount_override is not None and self.discount_override >= 0:
            discount_percent = self.discount_override
        elif self.per_product_discount is not None and self.per_product_discount >= 0:
            discount_percent = self.per_product_discount
        else:
            discount_percent = global_discount_percent
        return round(self.price_inr * (1 - discount_percent / 100), 2)
    
    def to_dict(self):
        """Convert product to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'price_inr': self.price_inr,
            'active': self.active,
            'stock': self.stock,
            'views': self.views,
            'add_to_cart_count': self.add_to_cart_count,
            'featured': self.featured,
            'is_hot_product': self.is_hot_product,
            'discount_override': self.discount_override,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'images': [img.to_dict() for img in self.images],
            'category_id': self.category_id,
            'category_name': self.category.name if self.category else None
        }


class ProductImage(db.Model):
    __tablename__ = 'product_images'
    
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    filename = db.Column(db.String(200), nullable=False)
    position = db.Column(db.Integer, default=0)  # For ordering images
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'product_id': self.product_id,
            'filename': self.filename,
            'position': self.position,
            'created_at': self.created_at.isoformat()
        }


class Lead(db.Model):
    __tablename__ = 'leads'
    
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.String(20), unique=True, nullable=False)  # Unique order ID
    full_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    phone_number = db.Column(db.String(20), nullable=False)
    telegram_username = db.Column(db.String(50), nullable=True)
    products_json = db.Column(db.Text, nullable=False)  # JSON string of product IDs and quantities
    total_amount = db.Column(db.Float, nullable=False)
    message = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(20), default='new')  # new, contacted, completed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def get_products(self):
        """Parse products_json to get actual product data"""
        try:
            products_data = json.loads(self.products_json) if self.products_json else []
            return products_data
        except:
            return []
    
    def to_dict(self):
        return {
            'id': self.id,
            'order_id': self.order_id,
            'full_name': self.full_name,
            'email': self.email,
            'phone_number': self.phone_number,
            'telegram_username': self.telegram_username,
            'products_json': self.products_json,
            'total_amount': self.total_amount,
            'message': self.message,
            'status': self.status,
            'created_at': self.created_at.isoformat(),
            'products': self.get_products()
        }


class Visitor(db.Model):
    __tablename__ = 'visitors'
    
    id = db.Column(db.Integer, primary_key=True)
    ip_hash = db.Column(db.String(64), nullable=False, unique=True)  # Hash of IP address for privacy
    first_seen = db.Column(db.DateTime, default=datetime.utcnow)
    last_seen = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    views_count = db.Column(db.Integer, default=1)  # Number of pages viewed by this visitor
    
    def to_dict(self):
        return {
            'id': self.id,
            'ip_hash': self.ip_hash,
            'first_seen': self.first_seen.isoformat(),
            'last_seen': self.last_seen.isoformat(),
            'views_count': self.views_count
        }


class AdminUser(db.Model):
    __tablename__ = 'admin_users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)  # In production, store hashed passwords
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def check_password(self, password):
        # SECURITY NOTE: This is a simple check for development.
        # For production, use hashed passwords with werkzeug.security
        # Example: return check_password_hash(self.password_hash, password)
        # For this implementation, using simple check as requested
        # In production, set these via environment variables or a more secure method
        import os
        admin_username = os.environ.get('ADMIN_USERNAME', 'admin')
        admin_password = os.environ.get('ADMIN_PASSWORD', 'admin @root')
        return self.username == admin_username and password == admin_password


class Category(db.Model):
    __tablename__ = 'categories'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.Text, nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    featured = db.Column(db.Boolean, default=False)  # For highlighting popular categories
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship with products
    products = db.relationship('Product', backref='category', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'is_active': self.is_active,
            'featured': self.featured,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'product_count': len(self.products)
        }


class SiteSettings(db.Model):
    __tablename__ = 'site_settings'
    
    id = db.Column(db.Integer, primary_key=True)
    store_name = db.Column(db.String(100), default='Baign Mart')
    banner_text = db.Column(db.String(200), default='Navratri Sale')
    global_discount_percent = db.Column(db.Float, default=40.0)
    theme_name = db.Column(db.String(50), default='light')
    privacy_policy = db.Column(db.Text, default='')
    terms = db.Column(db.Text, default='')
    about = db.Column(db.Text, default='')
    contact_email = db.Column(db.String(100), default='support@baignmart.com')
    contact_phone = db.Column(db.String(20), default='+91 XXXX-XXXX-XX')
    contact_address = db.Column(db.Text, default='123 Business Street, City, State - 123456')
    telegram_bot_token = db.Column(db.String(200), default='')
    admin_telegram_chat_id = db.Column(db.String(50), default='')
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'banner_text': self.banner_text,
            'global_discount_percent': self.global_discount_percent,
            'theme_name': self.theme_name,
            'privacy_policy': self.privacy_policy,
            'terms': self.terms,
            'about': self.about,
            'updated_at': self.updated_at.isoformat()
        }
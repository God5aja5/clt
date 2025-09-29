import unittest
import tempfile
import os
import sys
import models
from app import create_app
from datetime import datetime

class BaignMartTestCase(unittest.TestCase):
    def setUp(self):
        # Create a temporary database for testing
        self.db_fd, self.db_path = tempfile.mkstemp()
        
        # Set up the app
        self.app, self.db = create_app()
        self.app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{self.db_path}'
        self.app.config['TESTING'] = True
        self.app.config['WTF_CSRF_ENABLED'] = False  # Disable CSRF for testing
        
        # Import models after db is created
        from models import db, Product, Lead, SiteSettings
        
        with self.app.app_context():
            self.db.create_all()
            
            # Create a test site settings
            settings = SiteSettings(
                banner_text='Test Sale',
                global_discount_percent=40.0
            )
            self.db.session.add(settings)
            self.db.session.commit()
            
            # Create some test products
            product1 = Product(
                title='Test Product 1',
                description='This is a test product',
                price_inr=100.0,
                active=True
            )
            self.db.session.add(product1)
            self.db.session.commit()
            
            self.product_id = product1.id
    
    def tearDown(self):
        # Close the database connection and remove the temporary database
        from models import db
        with self.app.app_context():
            self.db.session.remove()
            self.db.drop_all()
        os.close(self.db_fd)
        os.unlink(self.db_path)
    
    def test_discounted_price_calculation(self):
        """Test that discounted price is calculated correctly"""
        from models import Product
        with self.app.app_context():
            # Get the test product
            product = Product.query.get(self.product_id)
            
            # Use the method to calculate discounted price
            discounted_price = product.get_discounted_price(40.0)  # 40% discount
            
            expected_price = round(100.0 * (1 - 40.0/100), 2)  # Should be 60.0
            self.assertEqual(discounted_price, expected_price)
    
    def test_product_active_status(self):
        """Test that we can toggle product active status"""
        from models import Product, db
        with self.app.app_context():
            product = Product.query.get(self.product_id)
            
            # Initially active
            self.assertTrue(product.active)
            
            # Toggle status
            product.active = False
            db.session.commit()
            
            # Refresh from database
            updated_product = Product.query.get(self.product_id)
            self.assertFalse(updated_product.active)
    
    def test_lead_creation(self):
        """Test creating a lead record"""
        from models import Lead, db
        with self.app.app_context():
            lead = Lead(
                full_name='Test User',
                email='test@example.com',
                phone_number='1234567890',
                telegram_username='@testuser',
                products_json='[{"product_id": 1, "quantity": 2}]',
                total_amount=120.0,
                message='Test message'
            )
            db.session.add(lead)
            db.session.commit()
            
            # Verify the lead was created
            saved_lead = Lead.query.filter_by(email='test@example.com').first()
            self.assertIsNotNone(saved_lead)
            self.assertEqual(saved_lead.full_name, 'Test User')
    
    def test_add_to_cart_functionality(self):
        """Test adding products to cart"""
        with self.app.test_client() as client:
            # Add a product to cart using the endpoint
            response = client.post('/cart/add', data={
                'product_id': self.product_id,
                'quantity': 2
            })
            
            # Check that we're redirected to the cart page
            self.assertEqual(response.status_code, 302)
            
            # Follow the redirect to check cart contents
            cart_response = client.get('/cart')
            self.assertEqual(cart_response.status_code, 200)
    
    def test_site_settings_exist(self):
        """Test that site settings exist and have default values"""
        from models import SiteSettings
        with self.app.app_context():
            settings = SiteSettings.query.first()
            self.assertIsNotNone(settings)
            self.assertEqual(settings.banner_text, 'Test Sale')
            self.assertEqual(settings.global_discount_percent, 40.0)

if __name__ == '__main__':
    unittest.main()
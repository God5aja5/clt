import os
from app import create_app
from models import db, Category

app, database = create_app()

def init_database():
    """Initialize the database with proper schema"""
    with app.app_context():
        # Create all tables
        db.create_all()
        print("Database tables created successfully!")
        
        # Check if categories already exist
        existing_categories = Category.query.all()
        if not existing_categories:
            # Create default categories
            default_categories = [
                {'name': 'Andrew Tate Course', 'description': 'Courses by Andrew Tate'},
                {'name': 'Grant Cardone Course', 'description': 'Courses by Grant Cardone'},
                {'name': 'Dating Course', 'description': 'Courses about dating and relationships'},
                {'name': 'Fitness Course', 'description': 'Courses about fitness and health'},
                {'name': 'Business Course', 'description': 'Courses about business and entrepreneurship'},
            ]
            
            for cat_data in default_categories:
                category = Category(
                    name=cat_data['name'],
                    description=cat_data['description'],
                    is_active=True
                )
                db.session.add(category)
            
            db.session.commit()
            print("Default categories created successfully!")
        else:
            print("Categories already exist, skipping initialization.")

if __name__ == "__main__":
    init_database()
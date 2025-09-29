import os
from app import create_app
from models import db, Category

app, database = create_app()

def init_production():
    """Initialize the application for production"""
    with app.app_context():
        # Create all tables
        db.create_all()
        print("Database tables created successfully!")
        
        # Initialize default categories if they don't exist
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
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--init":
        init_production()
    else:
        # Run the application
        port = int(os.environ.get('PORT', 5000))
        app.run(host='0.0.0.0', port=port, debug=False)
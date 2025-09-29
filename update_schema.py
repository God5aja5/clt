from app import create_app
from models import db

app, database = create_app()

with app.app_context():
    # Add missing columns to products table
    print("Adding missing columns to products table...")
    
    # Check if category_id column exists, if not add it
    result = db.session.execute(db.text("PRAGMA table_info(products)")).fetchall()
    col_names = [row[1] for row in result]
    
    if 'category_id' not in col_names:
        try:
            db.session.execute(db.text("ALTER TABLE products ADD COLUMN category_id INTEGER"))
            print("✓ Added category_id column to products table")
        except Exception as e:
            print(f"! Could not add category_id column: {e}")
    
    if 'is_hot_product' not in col_names:
        try:
            db.session.execute(db.text("ALTER TABLE products ADD COLUMN is_hot_product BOOLEAN DEFAULT 0"))
            print("✓ Added is_hot_product column to products table")
        except Exception as e:
            print(f"! Could not add is_hot_product column: {e}")
    
    # Create categories table if it doesn't exist
    try:
        db.session.execute(db.text("""
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name VARCHAR(100) NOT NULL UNIQUE,
                description TEXT,
                is_active BOOLEAN DEFAULT 1,
                featured BOOLEAN DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """))
        print("✓ Created/verified categories table")
    except Exception as e:
        print(f"! Could not create categories table: {e}")
    
    db.session.commit()
    print("Database schema updated successfully!")
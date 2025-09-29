from app import create_app
from models import Product
app, db = create_app()

with app.app_context():
    result = db.session.execute(db.text('PRAGMA table_info(products)')).fetchall()
    print('Current products table columns:')
    for row in result:
        print(row)
    
    print("\nChecking for category_id and is_hot_product columns...")
    col_names = [row[1] for row in result]
    if 'category_id' in col_names:
        print("✓ category_id column exists")
    else:
        print("✗ category_id column missing")
        
    if 'is_hot_product' in col_names:
        print("✓ is_hot_product column exists")
    else:
        print("✗ is_hot_product column missing")
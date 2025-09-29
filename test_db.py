from app import create_app
from models import Category, Product

app, db = create_app()

with app.app_context():
    print('Categories count:', Category.query.count())
    sample_category = Category.query.first()
    if sample_category:
        print('Sample category:', sample_category.name)
    print('Models imported and accessible')
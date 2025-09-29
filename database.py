from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json

# Create db instance to be initialized later
db = None

def init_db(app):
    """Initialize database with the app"""
    global db
    if db is None:
        db = SQLAlchemy(app)
        
        # Import models after db is created
        from . import models
        models.db = db
        
        # Set up all the models
        models.Product.__table__.tometadata(db.metadata)
        models.ProductImage.__table__.tometadata(db.metadata)
        models.Lead.__table__.tometadata(db.metadata)
        models.Visitor.__table__.tometadata(db.metadata)
        models.AdminUser.__table__.tometadata(db.metadata)
        models.SiteSettings.__table__.tometadata(db.metadata)
    
    return db
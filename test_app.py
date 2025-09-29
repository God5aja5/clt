from app import create_app

app, db = create_app()

from main import bp
app.register_blueprint(bp)

from admin import bp as admin_bp
app.register_blueprint(admin_bp, url_prefix='/admin-pn')

print("App created successfully")
with app.app_context():
    print("App context works")
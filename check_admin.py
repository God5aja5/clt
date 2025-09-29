from app import create_app
from models import AdminUser

app, db = create_app()

with app.app_context():
    print('Admin users:', AdminUser.query.all())
    print('Count:', AdminUser.query.count())
    for admin in AdminUser.query.all():
        print(f'ID: {admin.id}, Username: {admin.username}')
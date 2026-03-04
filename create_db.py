from fixedcut_app import app
from fixedcut_app import db

with app.app_context():
    db.create_all()
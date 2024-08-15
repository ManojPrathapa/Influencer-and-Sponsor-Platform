from app import app
from models import db
with app.app_context():
    db.drop_all()   # Drop all tables
    db.create_all()   # Create all tables according to the models
print("Database tables created successfully.")

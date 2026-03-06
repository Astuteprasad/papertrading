from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    risk_level = db.Column(db.String(50))  # Low / Medium / High
    income = db.Column(db.String(50))
    purpose = db.Column(db.String(100))
    experience = db.Column(db.String(50))
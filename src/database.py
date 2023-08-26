from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import string
import random

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True,)
    username = db.Column(db.String(50),unique=True,nullable=False)
    email = db.Column(db.String(120),unique=True,nullable=False)
    password = db.Column(db.Text(),nullable=False)
    created_at = db.Column(db.DateTime,default=datetime.now())
    updated_at = db.Column(db.DateTime,default=datetime.now(),onupdate=datetime.now())
    bookmarks = db.relationship('Bookmark',backref="user")

    def __repr__(self):
        return f"User>>> {self.username}"
    
class Bookmark(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.Text,nullable=True)
    url = db.Column(db.Text,nullable=False)
    short_url = db.Column(db.String(3),nullable=False)
    visits = db.Column(db.Integer,nullable=False,default=0)
    user_id = db.Column(db.Integer,db.ForeignKey("user.id"))
    created_at = db.Column(db.DateTime,nullable=False,default=datetime.now())
    updated_at = db.Column(db.DateTime,nullable=False,default=datetime.now(),onupdate=datetime.now())

    def __repr__(self):
        return f"Bookmark>>> {self.url}"

    def generate_short_chars(self):
        chars = string.digits+string.ascii_letters
        picked_chars = "".join(random.choices(chars, k=3))

        link = self.query.filter_by(short_url=picked_chars).first()

        if link:
            return self.generate_short_chars()
        else :
            return picked_chars

    def __init__(self,**kwargs):
        super().__init__(**kwargs)

        self.short_url = self.generate_short_chars()
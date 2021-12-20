#!/usr/bin/python
# -*- coding: utf-8 -*-
from flask import current_app
from panelstudenta import db, login_manager
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from flask_login import UserMixin
import datetime


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    image_file = db.Column(db.String(20), nullable=False, default='default.png')
    password = db.Column(db.String(60), nullable=False)
    files = db.relationship('File', backref='owner', lazy=True)
    registered_on = db.Column(db.DateTime, nullable=False)
    confirmed = db.Column(db.Boolean, nullable=False, default=False)
    confirmed_on = db.Column(db.DateTime, nullable=True)

    def __init__(self, username, email, password, confirmed, confirmed_on=None):
        self.username = username
        self.email = email
        self.password = password
        self.confirmed = confirmed
        self.registered_on = datetime.datetime.now()
        self.confirmed_on = confirmed_on

    def get_token(self, expires_sec=1800):
        s = Serializer(current_app.config["SECRET_KEY"], expires_sec)
        return s.dumps({'user_id': self.id}, salt=current_app.config['SECURITY_PASSWORD_SALT']).decode('utf-8')

    @staticmethod
    def verify_token(token):
        s = Serializer(current_app.config["SECRET_KEY"])
        try:
            user_id = s.loads(token, salt=current_app.config['SECURITY_PASSWORD_SALT'])['user_id']
        except:
            return None
        return User.query.get(user_id)

    def __repr__(self):
        return f"User('{self.username}', '{self.email}', {self.confirmed}, {self.confirmed_on})"


class File(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(), nullable=False)
    text = db.Column(db.JSON(), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def __repr__(self):
        return f"File('{self.name}', '{self.id}')"

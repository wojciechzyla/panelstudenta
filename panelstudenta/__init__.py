#!/usr/bin/python
# -*- coding: utf-8 -*-
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from flask_mail import Mail
from panelstudenta.config import Config


mail = Mail()
db = SQLAlchemy()
bcrypt = Bcrypt()
login_manager = LoginManager()
login_manager.login_view = 'users.home'
login_manager.login_message = 'Aby dostać się na to stronę, należy się zalogować'
login_manager.login_message_category = 'info'


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)

    from panelstudenta.users.routes import users
    from panelstudenta.img2txt.routes import img2txt
    from panelstudenta.accounting.routes import accounting
    app.register_blueprint(users)
    app.register_blueprint(img2txt)
    app.register_blueprint(accounting)

    return app


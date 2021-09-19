#!/usr/bin/python
# -*- coding: utf-8 -*-
from functools import wraps
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from panelstudenta.models import User
from flask import current_app, request, redirect, url_for


def token_required(a_type):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            user_id = int(kwargs["user_id"])
            user = User.query.get(user_id)
            s = Serializer(current_app.config["SECRET_KEY"])
            data = request.get_json()
            has_valid_token = False
            if "token" in data.keys():
                try:
                    username = s.loads(data["token"], salt=current_app.config['SECURITY_PASSWORD_SALT'])["username"]
                    app_type = s.loads(data["token"], salt=current_app.config['SECURITY_PASSWORD_SALT'])["app"]
                    if username == user.username and app_type == a_type:
                        has_valid_token = True
                except:
                    pass
            if has_valid_token:
                return func(*args, **kwargs)
            else:
                return redirect(url_for('img2txt.user_files'))
        return wrapper
    return decorator
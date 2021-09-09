#!/usr/bin/python
# -*- coding: utf-8 -*-
from panelstudenta.models import User, File
from panelstudenta import db
from flask import current_app
from flask_login import logout_user
import datetime
import os
import requests


URL_USER_FILES = os.environ.get("URL_USER_FILES")
USER_FILES_LOGIN = os.environ.get("USER_FILES_LOGIN")
USER_FILES_PASSWORD = os.environ.get("USER_FILES_PASSWORD")
files_authentication = {"USER_LOGIN": USER_FILES_LOGIN, "USER_PASSWORD": USER_FILES_PASSWORD}


def delete_unconfirmed(time_to_delete):
    unconfirmed = User.query.filter_by(confirmed=False)
    date_now = datetime.datetime.now()

    for user in unconfirmed:
        time_delta = (date_now - user.registered_on).total_seconds()/60
        if time_delta > time_to_delete:
            # remove files of this user
            remove_user_url = URL_USER_FILES + "delete_user/" + str(user.id)
            with current_app.test_request_context():
                requests.post(remove_user_url, json=files_authentication)

            if user.is_authenticated:
                logout_user()

            files_to_del = File.query.filter_by(owner=user).all()
            for f in files_to_del:
                db.session.delete(f)
            db.session.delete(user)
            db.session.commit()

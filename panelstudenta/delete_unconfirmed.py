#!/usr/bin/python
# -*- coding: utf-8 -*-
from panelstudenta.models import User, File
from panelstudenta import db
from flask import current_app
import datetime
import os
import shutil


def delete_unconfirmed(time_to_delete):
    """
    Function used to delete unconfirmed users
    :param time_to_delete: Users who didn't confirm their
    account since this time given in minutes will have their accounts deleted
    """
    unconfirmed = User.query.filter_by(confirmed=False)
    date_now = datetime.datetime.now()

    for user in unconfirmed:
        time_delta = (date_now - user.registered_on).total_seconds() / 60
        if time_delta > time_to_delete:
            dir_to_files = os.path.join(current_app.root_path, "static/users_files", user.username)
            # remove files directory of this user
            shutil.rmtree(dir_to_files)
            if user.image_file != "default.png":
                # remove profile picture of this user
                path_to_profile_pic = os.path.join(current_app.root_path, "static/profile_pics", user.image_file)
                os.remove(path_to_profile_pic)
            files_to_del = File.query.filter_by(owner=user).all()
            # remove files paths from database
            for f in files_to_del:
                db.session.delete(f)
            db.session.delete(user)
            db.session.commit()

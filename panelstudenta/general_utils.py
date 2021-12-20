#!/usr/bin/python
# -*- coding: utf-8 -*-
from functools import wraps
from flask_login import current_user
from flask import flash, redirect, url_for


def check_confirmed(func):
    """
    Function to check if user confirmed account
    """
    @wraps(func)
    def decorated_function(*args, **kwargs):
        if current_user.confirmed is False:
            flash('Potwierdź swój adres email!', 'warning')
            return redirect(url_for('users.unconfirmed'))
        return func(*args, **kwargs)

    return decorated_function

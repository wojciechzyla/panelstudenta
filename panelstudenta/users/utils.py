#!/usr/bin/python
# -*- coding: utf-8 -*-
from flask import url_for, abort, current_app
from panelstudenta import mail
import secrets
import os
import json
import base64
import requests
from flask_mail import Message


def send_reset_email(user):
    try:
        token = user.get_token()
        msg = Message('Resetowanie hasła - panel studenta',
                      sender='noreply@panel.com',
                      recipients=[user.email])
        msg.body = f'''W celu zresetowania hasła wejdź w poniższy link:
        {url_for('users.token_reset', token=token, _external=True)} 
    
        Jeśli nie chcesz resetować hasła zignoruj tą wiadomość.
        '''
        mail.send(msg)
    except AttributeError:
        pass


def send_delete_email(user):
    token = user.get_token()
    msg = Message('Usuwanie konta - panel studenta',
                  sender='noreply@panel.com',
                  recipients=[user.email])
    msg.body = f'''Aby usunąć konto wejdź w poniższy link:
    {url_for('users.delete_account', token=token, _external=True)} 

    Jeśli nie chcesz usuwać konta zignoruj tą wiadomość.
    '''
    mail.send(msg)


def send_confirm_email(user):
    token = user.get_token()
    msg = Message('Potwierdzenie adresu email - panel studenta',
                  sender='noreply@panel.com',
                  recipients=[user.email])
    msg.body = f'''Aby aktywować konto wejdź w poniższy link:
        {url_for('users.confirm_email', token=token, _external=True)} 

        Jeśli nie chcesz zakładać konta zignoruj tą wiadomość.
        '''
    mail.send(msg)


def save_profile_pic(form_picture, user_id):
    USER_FILES_LOGIN = os.environ.get("USER_FILES_LOGIN")
    USER_FILES_PASSWORD = os.environ.get("USER_FILES_PASSWORD")
    files_authentication = {"USER_LOGIN": USER_FILES_LOGIN,
                            "USER_PASSWORD": USER_FILES_PASSWORD}

    random_hex = secrets.token_hex(8)
    _, extention = os.path.splitext(form_picture.filename)
    filename = random_hex + extention

    URL_USER_FILES = os.environ.get("URL_USER_FILES")
    add_profile_url = URL_USER_FILES+"/upload_profile/"+str(user_id)

    im_b64 = base64.b64encode(form_picture.read()).decode("utf8")
    headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}
    files_authentication["image"] = im_b64
    files_authentication["filename"] = filename

    add_resp = requests.post(add_profile_url, data=json.dumps(files_authentication), headers=headers)
    if 400 <= add_resp.status_code < 500:
        abort(add_resp.status_code, add_resp.json())
    return filename

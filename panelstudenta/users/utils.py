#!/usr/bin/python
# -*- coding: utf-8 -*-
from flask import url_for, current_app
from panelstudenta import mail
import secrets
import os
from PIL import Image
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


def save_profile_pic(form_picture):
    random_hex = secrets.token_hex(8)
    _, extention = os.path.splitext(form_picture.filename)
    filename = random_hex + extention
    picture_path = os.path.join(current_app.root_path, "static/profile_pics", filename)
    output_size = 125, 125
    i = Image.open(form_picture)
    i.thumbnail(output_size)
    i.save(picture_path)
    return filename

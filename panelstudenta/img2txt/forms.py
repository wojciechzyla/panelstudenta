#!/usr/bin/python
# -*- coding: utf-8 -*-
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, FileSize
from wtforms import StringField, SubmitField, IntegerField
from wtforms.validators import DataRequired, ValidationError
from flask_login import current_user
from panelstudenta.models import File
from flask import current_app
import os
import re

class NewFileForm(FlaskForm):
    file = FileField("Dodaj nowy plik", validators=[FileAllowed(['pdf', 'png', 'jpg', 'jpeg'],
                                                     message="Tylko rozszerzenia pdf, jpg, png, jpeg"),
                                         FileSize(max_size=2 * 10**6,
                                                  message="Plik może mieć maksymalnie 2MB"),
                                         DataRequired(message='Pole wymagane')])
    submit = SubmitField('Dodaj plik')

    def validate_file(self, file):
        filename, _ = os.path.splitext(file.data.filename)
        if re.findall(r"[^a-zA-Z0-9_]", filename):
            raise ValidationError("Nazwa pliku może zawierać tylko angielskie litery, cyfry "
                                  "oraz znak _.")
        filepath = os.path.join(current_app.root_path, "static/users_files", current_user.username, file.data.filename)
        path_exists = os.path.exists(filepath)
        if path_exists:
            raise ValidationError("Już istnieje plik o takiej samej nazwie.")


class FindFileForm(FlaskForm):
    searchbox = StringField('Wyszukaj', validators=[DataRequired(message='Pole wymagane')],
                            render_kw={"placeholder": "Co chcesz znaleźć?"})

    amount = IntegerField("Ile plików chcesz wyświetlić", validators=[DataRequired(message='Pole wymagane')])

    def validate_amount(self, amount):
        if type(amount.data) != int:
            raise ValidationError("Ilość wyświetlanych elementów musi być liczbą całkowitą")
        if amount.data < 1:
            raise ValidationError("Trzeba wyświetlić minimum jeden plik")

    submit = SubmitField('Szukaj')
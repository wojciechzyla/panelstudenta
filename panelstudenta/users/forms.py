#!/usr/bin/python
# -*- coding: utf-8 -*-
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, FileSize
from wtforms import StringField, PasswordField, SubmitField, BooleanField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError
from panelstudenta.models import User
from flask_login import current_user
import re

MIN_PASS = 11
MAX_PASS = 50
MIN_USR = 5
MAX_USR = 20


class RegistrationForm(FlaskForm):
    username = StringField('Nazwa użytkownika', validators=[DataRequired(message='Pole wymagane'),
                                                            Length(min=MIN_USR, max=MAX_USR,
                                                                   message='Nazwa uzytkownika '
                                                                           'musi zawierać się między '
                                                                           f'{MIN_USR} a {MAX_USR} znaków')],
                           render_kw={"placeholder": "Nazwa użytkownika"})
    email = StringField('Email', validators=[DataRequired(message='Pole wymagane'),
                                             Email(message='Niepoprawny format email')],
                        render_kw={"placeholder": "Email"})

    password = PasswordField(f'Hasło (między {MIN_PASS} a {MAX_PASS} znaków)',
                             validators=[DataRequired(message='Pole wymagane'),
                                         Length(min=MIN_PASS, max=MAX_PASS, message='Hasło musi zawierać się '
                                                                                    f'między {MIN_PASS} a {MAX_PASS} znaków')],
                             render_kw={"placeholder": f'Hasło (między {MIN_PASS} a {MAX_PASS} znaków)'})

    confirm_password = PasswordField('Powtórz hasło', validators=[DataRequired(message='Pole wymagane'),
                                                                    EqualTo('password', message='Hasła '
                                                                                                'muszą się zgadzać')],
                                     render_kw={"placeholder": "Powtórz hasło"})
    submit = SubmitField('Sign Up')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError("Nazwa jest już zajęta")

        if re.findall(r"[^a-zA-Z0-9_]", username.data):
            raise ValidationError("Nazwa użytkownika może zawierać tylko angielskie litery, cyfry "
                                  "oraz znak _")

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError("Email jest już zajęty")

    def validate_password(self, password):
        if re.findall(r"[^a-zA-Z0-9_!@#$%^&*]", password.data):
            raise ValidationError("Hasło może zawierać tylko angielskie litery, cyfry "
                                  "oraz znaki _!@#$%^&*")


class LoginForm(FlaskForm):
    email = StringField('Email',
                        validators=[DataRequired(message='Pole wymagane'), Email(message='Niepoprawny format email')],
                        render_kw={"placeholder": "Email"})
    password = PasswordField('Hasło', validators=[DataRequired(message='Pole wymagane')],
                             render_kw={"placeholder": "Hasło"})
    remember = BooleanField("Zapamiętaj")
    submit = SubmitField('Login')


class UpdateAccountForm(FlaskForm):
    username = StringField('Nazwa użytkownika', validators=[DataRequired(message='Pole wymagane'),
                                                            Length(min=MIN_USR, max=MAX_USR,
                                                                   message='Nazwa uzytkownika '
                                                                           'musi zawierać się między '
                                                                           f'{MIN_USR} a {MAX_USR} znaków')],
                           render_kw={"placeholder": "Nazwa użytkownika"})

    email = StringField('Email', validators=[DataRequired(message='Pole wymagane'),
                                             Email(message='Niepoprawny format email')],
                        render_kw={"placeholder": "Email"})

    picture = FileField("Załaduj nowe zdjęcie profilowe", validators=[FileAllowed(['jpg', 'png'],
                                                                             message="Tylko rozszerzenia jpg i png"),
                                                                 FileSize(max_size=200 * 1000,
                                                                          message="Plik może mieć maksymalnie 200KB")])
    reset_picture = BooleanField("Usuń zdjęcie profilowe")

    submit = SubmitField('Zaktualizuj')

    def validate_username(self, username):
        if username.data != current_user.username:
            user = User.query.filter_by(username=username.data).first()
            if user:
                raise ValidationError("Nazwa jest już zajęa")
            if re.findall(r"[^a-zA-Z0-9_]", username.data):
                raise ValidationError("Nazwa użytkownika może zawierać tylko angielskie litery, cyfry "
                                      "oraz znak _")

    def validate_email(self, email):
        if email.data != current_user.email:
            user = User.query.filter_by(email=email.data).first()
            if user:
                raise ValidationError("Email jest już zajęty")


class RequestResetForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(message='Pole wymagane'),
                                             Email(message='Niepoprawny format email')],
                        render_kw={"placeholder": "Email"})
    submit = SubmitField('Wyślij link z dalszymi instrukcjami ')


class ResetPasswordForm(FlaskForm):
    password = PasswordField('Hasło', validators=[DataRequired(message='Pole wymagane'),
                                                  Length(min=MIN_PASS, max=MAX_PASS, message='Hasło musi zawierać się '
                                                                                             f'między {MIN_PASS} a {MAX_PASS} znaków')],
                             render_kw={"placeholder": "Hasło"})

    confirm_password = PasswordField('Potwierdź hasło', validators=[DataRequired(message='Pole wymagane'),
                                                                    EqualTo('password', message='Hasła '
                                                                                                'muszą się zgadzać')],
                                     render_kw={"placeholder": "Powtórz hasło"})
    submit = SubmitField('Zresetuj hasło')


class ChangePasswordForm(FlaskForm):
    old_password = PasswordField('Stare hasło', validators=[DataRequired(message='Pole wymagane')],
                                 render_kw={"placeholder": "Sare hasło"})
    password = PasswordField('Nowe hasło', validators=[DataRequired(message='Pole wymagane'),
                                                       Length(min=MIN_PASS, max=MAX_PASS,
                                                              message='Hasło musi zawierać się '
                                                                      f'między {MIN_PASS} a {MAX_PASS} znaków')],
                             render_kw={"placeholder": "Nowe hasło"})

    confirm_password = PasswordField('Powtórz nowe hasło', validators=[DataRequired(message='Pole wymagane'),
                                                                         EqualTo('password', message='Hasła '
                                                                                                     'muszą się zgadzać')],
                                     render_kw={"placeholder": "Powtórz nowe hasło"})
    submit = SubmitField('Zmień hasło')


class DeleteAccountForm(FlaskForm):
    submit = SubmitField('Chcę usunąć konto')

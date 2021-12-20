#!/usr/bin/python
# -*- coding: utf-8 -*-
import shutil
from flask import render_template, url_for, flash, redirect, Blueprint, request, current_app
from panelstudenta.users.forms import RegistrationForm, UpdateAccountForm, \
    RequestResetForm, ResetPasswordForm, ChangePasswordForm, DeleteAccountForm, LoginForm
from panelstudenta.users.utils import send_reset_email, send_delete_email, save_profile_pic, send_confirm_email
from panelstudenta.general_utils import check_confirmed
from panelstudenta import db, bcrypt
from panelstudenta.models import User, File
from flask_login import current_user, logout_user, login_required, login_user
import os
import datetime
import threading

users = Blueprint('users', __name__, template_folder='templates')


@users.route("/", methods=['GET', 'POST'])
def home():
    """
    Return home page. This page is different for logged and
    not logged in users.
    """
    if current_user.is_authenticated:
        return render_template("home_logged.html")
    form_log = LoginForm()
    if form_log.validate_on_submit():
        user = User.query.filter_by(email=form_log.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form_log.password.data):
            login_user(user, remember=form_log.remember.data)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('users.home'))
        else:
            flash('Niepoprawne logowanie. Sprawdź email i hasło', 'danger')
    return render_template("home_login.html", form_log=form_log)


@users.route("/register", methods=['GET', 'POST'])
def register():
    """
    Endpoint for registering new users. If user is already logged in he is
    redirected to home page.
    """
    if current_user.is_authenticated:
        return redirect(url_for('users.home'))
    form_reg = RegistrationForm()
    if form_reg.validate_on_submit():
        hashed_pass = bcrypt.generate_password_hash(form_reg.password.data).decode('utf-8')
        user = User(username=form_reg.username.data, email=form_reg.email.data, password=hashed_pass, confirmed=False)

        if not os.path.exists(os.path.join(current_app.root_path, "static/users_files", form_reg.username.data)):
            # create directory for uploaded files
            os.makedirs(os.path.join(current_app.root_path, "static/users_files", form_reg.username.data))

        db.session.add(user)
        db.session.commit()

        # Send confirmation email on different thread.
        thread = threading.Thread(target=send_confirm_email, kwargs={'user': user, "app": current_app._get_current_object()})
        thread.start()

        login_user(user)
        flash(f'Utworzono konto dla: {form_reg.username.data}! Na podany adres email za chwilę zostanie wysłana wiadomość z potwierdzeniem.', 'success')
        return redirect(url_for('users.unconfirmed'))
    return render_template("registration.html", form_reg=form_reg, title="Rejestracja")


@users.route('/unconfirmed')
@login_required
def unconfirmed():
    """
    If users email is not confirmed he is shown this page.
    """
    if current_user.confirmed:
        return redirect('users.home')
    return render_template('unconfirmed.html')


@users.route('/confirm/<token>')
@login_required
def confirm_email(token):
    """
   Confirm user's email. If token is expired or invalid or user is already
   confirmed, appropriate message is flashed.
   """
    user = User.verify_token(token)
    if user is None:
        flash("Link aktywujący konto wygasł lub jest nieważny", "warning")
        return redirect(url_for('users.home'))
    if user.confirmed:
        flash('Konto zostało już aktywowane. Proszę się zalogować', 'success')
    else:
        user.confirmed = True
        user.confirmed_on = datetime.datetime.now()
        db.session.commit()
        flash('Email został potwierdzony', 'success')
    return redirect(url_for('users.home'))


@users.route('/resend')
@login_required
def resend_confirmation():
    """
    Resend link to confirm email.
    """
    thread = threading.Thread(target=send_confirm_email, kwargs={'user': current_user._get_current_object(), "app": current_app._get_current_object()})
    thread.start()
    flash('Nowy email z potwierdzeniem został wysłany', 'success')
    return redirect(url_for('users.unconfirmed'))


@users.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('users.home'))


@users.route("/account", methods=['GET', 'POST'])
@login_required
@check_confirmed
def account():
    """
    Page to display and update account details.
    """
    form = UpdateAccountForm()

    if form.validate_on_submit():
        path_to_profile_pic = os.path.join(current_app.root_path, "static/profile_pics", current_user.image_file)
        if form.picture.data:
            # save new profile image
            picture_file = save_profile_pic(form.picture.data)
            if current_user.image_file != "default.png":
                # Remove  previous profile picture
                os.remove(path_to_profile_pic)
            current_user.image_file = picture_file
        if form.reset_picture.data and current_user.image_file != "default.png":
            # Reset profile picture
            os.remove(path_to_profile_pic)
            current_user.image_file = "default.png"

        # Change user's name and name of user files directory.
        path_to_user_files = os.path.join(current_app.root_path, "static/users_files", current_user.username)
        path_to_new_user_files = os.path.join(current_app.root_path, "static/users_files", form.username.data)
        os.rename(path_to_user_files, path_to_new_user_files)
        current_user.username = form.username.data

        # Confirm new email
        if form.email.data != current_user.email:
            current_user.confirmed = False
            current_user.confirmed_on = None
            current_user.email = form.email.data

            thread = threading.Thread(target=send_confirm_email, kwargs={'user': current_user._get_current_object(), "app": current_app._get_current_object()})
            thread.start()

            flash("Aby móc dalej korzystać z konta proszę potwierdzić swój nowy adres email!", "info")
        db.session.commit()
        flash("Dane zostały zaktualizowane", "success")
        return redirect(url_for("users.account"))

    image_file = url_for("static", filename="profile_pics/" + current_user.image_file)
    return render_template("account.html", title="Konto", image_file=image_file, form=form)


@users.route("/delete_account", methods=['GET', 'POST'])
@login_required
@check_confirmed
def request_delete():
    """
    Page to request account deletion.
    """
    del_form = DeleteAccountForm()
    if del_form.validate_on_submit():
        thread = threading.Thread(target=send_delete_email, kwargs={'user': current_user._get_current_object(), "app": current_app._get_current_object()})
        thread.start()
        flash("Jeśli podany adres email jest powiązany z kontem została na niego wysłana "
              "informacja dotycząca usuwania konta.", 'info')
        return redirect(url_for('users.account'))
    return render_template("request_delete.html", title="Usuń konto", del_form=del_form)


@users.route("/account/<token>", methods=['GET', 'POST'])
def delete_account(token):
    """
    Delete user's account.
    """
    user = User.verify_token(token)
    if user is None:
        # If token is expired or invalid flash information and redirect to home page.
        flash("Link usuwający konto wygasł lub jest nieważny", "warning")
        return redirect(url_for('users.home'))
    else:
        dir_to_files = os.path.join(current_app.root_path, "static/users_files", user.username)
        if current_user.is_authenticated:
            logout_user()
        # remove files directory of this user
        shutil.rmtree(dir_to_files)
        if user.image_file != "default.png":
            # remove profile picture of this user
            path_to_profile_pic = os.path.join(current_app.root_path, "static/profile_pics", user.image_file)
            os.remove(path_to_profile_pic)

        # remove files paths from database
        files_to_del = File.query.filter_by(owner=user).all()
        # remove files path from database
        for f in files_to_del:
            db.session.delete(f)
        db.session.delete(user)
        db.session.commit()
        flash(f'Konto zostało usunięte', 'success')
        return redirect(url_for('users.home'))


@users.route("/reset_password", methods=['GET', 'POST'])
def request_reset():
    """
    Page for sending link to reset password for not logged in users.
    """
    if current_user.is_authenticated:
        return render_template("home_logged.html")
    form = RequestResetForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        thread = threading.Thread(target=send_reset_email, kwargs={'user': user, "app": current_app._get_current_object()})
        thread.start()
        flash("Jeśli podany adres email jest powiązany z kontem została na niego wysłana "
              "informacja dotycząca zresetowania hasła.", 'info')
        return redirect(url_for('users.home'))
    return render_template("request_reset.html", title="Zresetuj hasło", form=form)


@users.route("/reset_password/<token>", methods=['GET', 'POST'])
def token_reset(token):
    """
    Reset password.
    """
    if current_user.is_authenticated:
        return render_template("home_logged.html")
    user = User.verify_token(token)
    if user is None:
        # If token is expired or invalid flash information and redirect to home page.
        flash("Link resetujący hasło wygasł lub jest nieważny", "warning")
        return redirect(url_for('users.request_reset'))
    else:
        form = ResetPasswordForm()
        if form.validate_on_submit():
            hashed_pass = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
            user.password = hashed_pass
            db.session.commit()
            flash(f'Hasło zostało zresetowane', 'success')
            return redirect(url_for('users.home'))
        return render_template("token_reset.html", title="Zresetuj hasło", form=form)


@users.route("/change_password", methods=['GET', 'POST'])
@login_required
@check_confirmed
def change_password():
    """
    Page for changing password for logged in users.
    """
    form = ChangePasswordForm()
    if form.validate_on_submit():
        if bcrypt.check_password_hash(current_user.password, form.old_password.data):
            hashed_pass = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
            current_user.password = hashed_pass
            db.session.commit()
            flash(f'Hasło zostało zmienione', 'success')
            return redirect(url_for('users.account'))
        else:
            flash("Złe hasło", "danger")
            return redirect(url_for('users.account'))
    return render_template("password_change.html", title="Zmiana hasła", form=form)

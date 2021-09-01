#!/usr/bin/python
# -*- coding: utf-8 -*-
from flask import render_template, url_for, flash, redirect, Blueprint, request, current_app
from panelstudenta.users.forms import RegistrationForm, UpdateAccountForm, \
    RequestResetForm, ResetPasswordForm, ChangePasswordForm, DeleteAccountForm, LoginForm
from panelstudenta.users.utils import send_reset_email, send_delete_email, save_profile_pic, send_confirm_email
from panelstudenta.general_utils import check_confirmed
from panelstudenta import db, bcrypt
from panelstudenta.models import User, File
from flask_login import current_user, logout_user, login_required, login_user
import os
import shutil
import datetime

users = Blueprint('users', __name__, template_folder='templates')


@users.route("/", methods=['GET', 'POST'])
def home():
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
    if current_user.is_authenticated:
        return redirect(url_for('users.home'))
    form_reg = RegistrationForm()
    if form_reg.validate_on_submit():
        hashed_pass = bcrypt.generate_password_hash(form_reg.password.data).decode('utf-8')
        user = User(username=form_reg.username.data, email=form_reg.email.data, password=hashed_pass, confirmed=False)
        if not os.path.exists(os.path.join(current_app.root_path, "static/users_files", form_reg.username.data)):
            os.makedirs(os.path.join(current_app.root_path, "static/users_files", form_reg.username.data))
        db.session.add(user)
        db.session.commit()
        send_confirm_email(user)
        login_user(user)
        flash(f'Utworzono konto dla: {form_reg.username.data}! Na podany adres email została wysłana wiadomość z potwierdzeniem', 'success')
        return redirect(url_for('users.unconfirmed'))
    return render_template("registration.html", form_reg=form_reg, title="Rejestracja")


@users.route('/unconfirmed')
@login_required
def unconfirmed():
    if current_user.confirmed:
        return redirect('users.home')
    #flash('Proszę potwierdzić swój adres email!', 'warning')
    return render_template('unconfirmed.html')


@users.route('/confirm/<token>')
@login_required
def confirm_email(token):
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
    send_confirm_email(current_user)
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
    form = UpdateAccountForm()

    if form.validate_on_submit():
        path_to_profile_pic = os.path.join(current_app.root_path, "static/profile_pics", current_user.image_file)
        if form.picture.data:
            picture_file = save_profile_pic(form.picture.data)
            if current_user.image_file != "default.png":
                # Remove  previous profile picture
                os.remove(path_to_profile_pic)
            current_user.image_file = picture_file
        if form.reset_picture.data and current_user.image_file != "default.png":
            # Reset profile picture
            os.remove(path_to_profile_pic)
            current_user.image_file = "default.png"
        path_to_user_files = os.path.join(current_app.root_path, "static/users_files", current_user.username)
        path_to_new_user_files = os.path.join(current_app.root_path, "static/users_files", form.username.data)
        os.rename(path_to_user_files, path_to_new_user_files)
        current_user.username = form.username.data

        # confirm new email
        if form.email.data != current_user.email:
            current_user.confirmed = False
            current_user.confirmed_on = None
            current_user.email = form.email.data
            send_confirm_email(current_user)
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
    del_form = DeleteAccountForm()
    if del_form.validate_on_submit():
        send_delete_email(current_user)
        flash("Jeśli podany adres email jest powiązany z kontem została na niego wysłana "
              "informacja dotycząca usuwania konta.", 'info')
        return redirect(url_for('users.account'))
    return render_template("request_delete.html", title="Usuń konto", del_form=del_form)


@users.route("/account/<token>", methods=['GET', 'POST'])
def delete_account(token):
    user = User.verify_token(token)
    if user is None:
        flash("Link usuwający konto wygasł lub jest nieważny", "warning")
        return redirect(url_for('users.home'))
    else:
        dir_to_files = os.path.join(current_app.root_path, "static/users_files", user.username)
        if current_user.is_authenticated:
            logout_user()
        # remove files of this user
        shutil.rmtree(dir_to_files)
        if user.image_file != "default.png":
            # remove profile picture of this user
            path_to_profile_pic = os.path.join(current_app.root_path, "static/profile_pics", user.image_file)
            os.remove(path_to_profile_pic)
        files_to_del = File.query.filter_by(owner=user).all()
        for f in files_to_del:
            db.session.delete(f)
        db.session.delete(user)
        db.session.commit()
        flash(f'Konto zostało usunięte', 'success')
        return redirect(url_for('users.home'))


@users.route("/reset_password", methods=['GET', 'POST'])
def request_reset():
    if current_user.is_authenticated:
        return render_template("home_logged.html")
    form = RequestResetForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        send_reset_email(user)
        flash("Jeśli podany adres email jest powiązany z kontem została na niego wysłana "
              "informacja dotycząca zresetowania hasła.", 'info')
        return redirect(url_for('users.home'))
    return render_template("request_reset.html", title="Zresetuj hasło", form=form)


@users.route("/reset_password/<token>", methods=['GET', 'POST'])
def token_reset(token):
    if current_user.is_authenticated:
        return render_template("home_logged.html")
    user = User.verify_token(token)
    if user is None:
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

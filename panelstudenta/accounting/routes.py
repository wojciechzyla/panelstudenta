#!/usr/bin/python
# -*- coding: utf-8 -*-
from flask import render_template, url_for, flash, redirect, \
    request, abort, session, Blueprint, send_file, current_app
from dotenv import load_dotenv, find_dotenv
from flask_login import login_required, current_user
from panelstudenta.general_utils import check_confirmed
import os

load_dotenv(find_dotenv())
accounting = Blueprint('accounting', __name__, template_folder='templates')
URL_ACCOUNTING = os.environ.get("ACCOUNTING_URL")


@accounting.route("/accounting", methods=['GET'])
@login_required
@check_confirmed
def groups():
    return render_template("groups.html", user_id=current_user.id, accounting_url=URL_ACCOUNTING)


@accounting.route("/accounting/<group_id>", methods=['GET'])
@login_required
@check_confirmed
def group(group_id):
    return render_template("group.html", user_id=current_user.id, accounting_url=URL_ACCOUNTING, group_id=group_id)

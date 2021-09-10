#!/usr/bin/python
# -*- coding: utf-8 -*-
from flask import render_template, url_for, flash, redirect, \
    request, abort, session, Blueprint, send_file, current_app
from werkzeug.utils import secure_filename
from panelstudenta.img2txt.forms import NewFileForm, FindFileForm
from panelstudenta import db
from panelstudenta.img2txt.utils import token_required
from panelstudenta.models import File, User
from panelstudenta.general_utils import check_confirmed
from flask_login import current_user, login_required
import os
import requests
import base64
import json
from io import BytesIO
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from dotenv import load_dotenv, find_dotenv
import threading

load_dotenv(find_dotenv())


img2txt = Blueprint('img2txt', __name__, template_folder='templates')
URL_USER_FILES = os.environ.get("URL_USER_FILES")
USER_FILES_LOGIN = os.environ.get("USER_FILES_LOGIN")
USER_FILES_PASSWORD = os.environ.get("USER_FILES_PASSWORD")
files_authentication = {"USER_LOGIN": USER_FILES_LOGIN,
                        "USER_PASSWORD": USER_FILES_PASSWORD}
URL_NLP = os.environ.get("URL_NLP")


@img2txt.route("/imgtxt/<file_name>", methods=['GET'])
@check_confirmed
@login_required
def file(file_name):
    get_file_url = URL_USER_FILES+"/get/"+str(current_user.id)+"/"+file_name
    headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}

    get_file = requests.get(get_file_url, data=json.dumps(files_authentication), headers=headers)
    if 400 <= get_file.status_code < 600:
        abort(get_file.status_code, get_file.json())
    else:
        file_b64 = get_file.json()["file"]
        file_display = base64.b64decode(file_b64.encode('utf-8'))
        file_name = get_file.json()["filename"]
        return send_file(BytesIO(file_display), download_name=file_name)


@img2txt.route("/imgtxt/<int:file_id>/<filename>/delete_file", methods=['POST'])
@login_required
@check_confirmed
def delete_file(file_id, filename):
    remove_url = URL_USER_FILES + "/delete_file/" + str(current_user.id) + "/" + str(filename)
    remove_resp = requests.post(remove_url, json=files_authentication)
    if 400 <= remove_resp.status_code < 600:
        abort(remove_resp.status_code, remove_resp.json())

    file_to_delete = File.query.get_or_404(file_id)
    db.session.delete(file_to_delete)
    db.session.commit()
    flash("Plik został usunięty!", "success")
    return redirect(url_for('img2txt.user_files'))


@img2txt.route("/imgtxt/files", methods=['GET', 'POST'])
@login_required
@check_confirmed
def user_files():
    form = NewFileForm()

    # Adding new img2txt
    if form.validate_on_submit():

        pdf_b64 = base64.b64encode(form.file.data.read()).decode("utf8")
        files_authentication["file"] = pdf_b64
        files_authentication["filename"] = secure_filename(form.file.data.filename)
        headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}

        file_upload_url = URL_USER_FILES + "/upload/" + str(current_user.id)
        add_resp = requests.post(file_upload_url, data=json.dumps(files_authentication), headers=headers)
        if 400 <= add_resp.status_code < 500:
            abort(add_resp.status_code, add_resp.json())

        filename = secure_filename(form.file.data.filename)
        files = {'file': pdf_b64, "filename": filename}
        URL_img = os.environ.get("URL_IMG")+"/"+str(current_user.id)

        s = Serializer(current_app.config["SECRET_KEY"], 1800)
        token = s.dumps({"username": current_user.username, "app": "img2txt"},
                        salt=current_app.config['SECURITY_PASSWORD_SALT']).decode('utf-8')
        files["token"] = token

        try:
            requests.post(URL_img, data=json.dumps(files), headers=headers)
        except requests.exceptions.ConnectionError:
            remove_url = URL_USER_FILES + "/delete_file/" + str(current_user.id) + "/" + str(filename)
            requests.post(remove_url, json=files_authentication)
            flash("Problem z połączeniem z aplikacją zczytującą tekst", "danger")

    page = request.args.get('page', 1, type=int)
    files_display = File.query.filter_by(owner=current_user).paginate(page=page, per_page=5)
    return render_template("user_files.html", title="Wyszukiwarka plików", form=form, files_display=files_display)


@img2txt.route("/imgtxt/files/img_receive/<filename>/<user_id>", methods=['POST'])
@token_required("img2txt")
def img_receive(filename, user_id):
    data = request.get_json()
    user = User.query.get(int(user_id))
    s = Serializer(current_app.config["SECRET_KEY"], 1800)
    salt = current_app.config['SECURITY_PASSWORD_SALT']

    def call_nlp(**kwargs):
        params = kwargs.get('post_data')
        status_code = int(params['status_code'])
        if status_code < 400:
            params.pop("status_code", None)
            params.pop("token", None)
            if user is not None:
                token = s.dumps({"username": user.username, "app": "nlp"}, salt=salt).decode('utf-8')
                params["token"] = token
                try:
                    requests.post(URL_NLP+"/preprocess/"+filename+"/"+user_id, json=params)
                except requests.exceptions.ConnectionError:
                    remove_url = URL_USER_FILES + "/delete_file/" + str(user_id) + "/" + str(filename)
                    requests.post(remove_url, json=files_authentication)
                    flash("Problem z połączeniem z aplikacją analizującą tekst", "danger")
            else:
                remove_url = URL_USER_FILES + "/delete_file/" + str(user_id) + "/" + str(filename)
                requests.post(remove_url, json=files_authentication)
        else:
            remove_url = URL_USER_FILES + "/delete_file/" + str(user_id) + "/" + str(filename)
            requests.post(remove_url, json=files_authentication)

    with current_app.app_context():
        thread = threading.Thread(target=call_nlp, kwargs={'post_data': data})
        thread.start()
    return {"info": "accepted"}, 202


@img2txt.route("/imgtxt/files/nlp_receive/<filename>/<user_id>", methods=['POST'])
@token_required("nlp")
def nlp_receive(filename, user_id):
    data = request.get_json()
    status_code = int(data["status_code"])

    if status_code < 400:
        data.pop("status_code", None)
        user = User.query.get(int(user_id))
        new_file = File(name=filename, owner=user, text=data)
        db.session.add(new_file)
        db.session.commit()
    else:
        remove_url = URL_USER_FILES + "/delete_file/" + str(user_id) + "/" + str(filename)
        requests.post(remove_url, json=files_authentication)

    return {"info": "accepted"}, 202


@img2txt.route("/imgtxt", methods=['GET', 'POST'])
@login_required
@check_confirmed
def imgtxt():
    search_form = FindFileForm()
    all_files = File.query.filter_by(owner=current_user).all()
    # Searching documents
    if search_form.validate_on_submit():
        URL_nlp = URL_NLP+"/rank"
        query = search_form.searchbox.data
        documents_amount = search_form.amount.data if search_form.amount.data < len(all_files) else len(all_files)
        documents = []
        if len(all_files) > 0:
            for f in all_files:
                # Loop over all documents and add them
                # to 'documents' list
                pages = []
                for i in range((len(f.text) - 1) // 2):
                    # Text field is a JSON object which
                    # consists of following fields: Document embedding,
                    # tokenized pages from 1st to the last and pages
                    # embeddings from 1st to the last.
                    # That's why in the loop over the length of dictionary we
                    # subtract key of document embedding and then divide it by 2
                    # to get the amount of  pages.
                    pages.append(f.text[f"Embedding{i}"])
                doc = {"name": f.name,
                       "embedding": f.text["Doc_embedding"],
                       "pages": pages}
                documents.append(doc)

            request_json = {"query": query,
                            "documents": documents,
                            "doc_amount": documents_amount}
            try:
                response = requests.post(URL_nlp, json=request_json)
            except requests.exceptions.ConnectionError:
                flash("Problem z połączeniem", "danger")
                return redirect(url_for("img2txt.imgtxt"))

            if response.status_code == 200:
                results = response.json()["results"]
            else:
                abort(response.status_code, response.json())
            session["RANKED_DOCS"] = results
            return redirect(url_for("img2txt.imgtxt"))
        else:
            session["NO_DOCS_TO_RANK"] = True
            return redirect(url_for("img2txt.imgtxt"))


    # Rendering template
    title = "Wyszukiwarka plików"
    if session.get("RANKED_DOCS", None) is not None:
        template = render_template("img2txt.html", title=title, search_form=search_form,
                                   ranked_docs=session["RANKED_DOCS"], user_files_amount=len(all_files))
        session.pop("RANKED_DOCS")
    elif session.get("NO_DOCS_TO_RANK", None) is not None:
        template = render_template("img2txt.html", title=title, search_form=search_form,
                                   no_docs=session["NO_DOCS_TO_RANK"], user_files_amount=len(all_files))
        session.pop("NO_DOCS_TO_RANK")
    else:
        template = render_template("img2txt.html", title=title, search_form=search_form, user_files_amount=len(all_files))
    return template

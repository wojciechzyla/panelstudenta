#!/usr/bin/python
# -*- coding: utf-8 -*-
from flask import render_template, url_for, flash, redirect, \
    request, abort, session, Blueprint, send_from_directory, current_app
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
from werkzeug.utils import safe_join
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from dotenv import load_dotenv, find_dotenv
import threading

load_dotenv(find_dotenv())


img2txt = Blueprint('img2txt', __name__, template_folder='templates')
URL_NLP = os.environ.get("URL_NLP")


@img2txt.route("/imgtxt/<file_name>", methods=['GET'])
@check_confirmed
@login_required
def file(file_name):
    """
    Display requested file
    """
    filepath = os.path.join(current_app.root_path, "static/users_files", current_user.username)
    if os.path.exists(safe_join(filepath, file_name)):
        return send_from_directory(filepath, file_name)
    else:
        abort(404)


@img2txt.route("/imgtxt/<int:file_id>/delete_file", methods=['POST'])
@login_required
@check_confirmed
def delete_file(file_id):
    """
    Remove user's file.
    """
    file_to_delete = File.query.get_or_404(file_id)
    path_to_file = os.path.join(current_app.root_path, "static/users_files", current_user.username, file_to_delete.name)
    os.remove(path_to_file)
    db.session.delete(file_to_delete)
    db.session.commit()
    flash("Plik został usunięty!", "success")
    return redirect(url_for('img2txt.user_files'))


@img2txt.route("/imgtxt/files", methods=['GET', 'POST'])
@login_required
@check_confirmed
def user_files():
    """
    List and add user files. Adding files works in such a way that
    this app connects with app responsible for extracting text from images.
    That other app processes the file and then returns result to endpoint (img_receive) of
    this app.
    """
    form = NewFileForm()

    # Adding new img2txt
    if form.validate_on_submit():
        if not os.path.exists(os.path.join(current_app.root_path, "static/users_files", current_user.username)):
            # Create file directory for user.
            os.makedirs(os.path.join(current_app.root_path, "static/users_files", current_user.username))
        file_path = os.path.join(current_app.root_path, "static/users_files", current_user.username,
                                 form.file.data.filename)
        # Save file
        form.file.data.save(file_path)

        # Create json file to be sent to image processing app
        with open(file_path, 'rb') as f:
            pdf_b64 = base64.b64encode(f.read()).decode("utf8")
        s = Serializer(current_app.config["SECRET_KEY"], 1800)
        token = s.dumps({"username": current_user.username, "app": "img2txt"},
                        salt=current_app.config['SECURITY_PASSWORD_SALT']).decode('utf-8')
        headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}
        filename = secure_filename(form.file.data.filename)
        files = {'file': pdf_b64, "filename": filename, "token": token}

        URL_img = os.environ.get("URL_IMG") + "/" + str(current_user.id)
        try:
            # Connect with app responsible for extracting text from files.
            requests.post(URL_img, data=json.dumps(files), headers=headers)
        except requests.exceptions.ConnectionError:
            flash("Problem z połączeniem z aplikacją zczytującą tekst", "danger")
            os.remove(file_path)
            return redirect(url_for("img2txt.user_files"))

    page = request.args.get('page', 1, type=int)
    files_display = File.query.filter_by(owner=current_user).paginate(page=page, per_page=5)
    return render_template("user_files.html", title="Wyszukiwarka plików", form=form, files_display=files_display)


@img2txt.route("/imgtxt/files/img_receive/<filename>/<user_id>", methods=['POST'])
@token_required("img2txt")
def img_receive(filename, user_id):
    """
    This endpoint receives preprocessed image file from image processing app
    and then sends this data to text processing app where NLP actions will be taken.
    """
    data = request.get_json()
    user = User.query.get(int(user_id))
    s = Serializer(current_app.config["SECRET_KEY"], 1800)
    salt = current_app.config['SECURITY_PASSWORD_SALT']
    def call_nlp(**kwargs):
        """
        This function is called on another thread while response is returned to
        image processing app.
        """
        params = kwargs.get('post_data')
        status_code = int(params['status_code'])
        if status_code < 400:
            # Remove previous status code and token
            # from call received from image processing app.
            params.pop("status_code", None)
            params.pop("token", None)
            if user is not None:
                # Create new token
                token = s.dumps({"username": user.username, "app": "nlp"}, salt=salt).decode('utf-8')
                params["token"] = token
                try:
                    # Connect with app responsible for NLP functionality.
                    requests.post(URL_NLP+"/preprocess/"+filename+"/"+user_id, json=params)
                except requests.exceptions.ConnectionError:
                    file_path = os.path.join(current_app.root_path, "static/users_files", current_user.username,
                                             str(filename))
                    os.remove(file_path)
                    flash("Problem z połączeniem z aplikacją analizującą tekst", "danger")
            else:
                file_path = os.path.join(current_app.root_path, "static/users_files", current_user.username,
                                         str(filename))
                os.remove(file_path)
        else:
            file_path = os.path.join(current_app.root_path, "static/users_files", current_user.username,
                                     str(filename))
            os.remove(file_path)

    # Connect with NLP app on different thread and return response to image processing app.
    with current_app.app_context():
        thread = threading.Thread(target=call_nlp, kwargs={'post_data': data})
        thread.start()
    return {"info": "accepted"}, 202


@img2txt.route("/imgtxt/files/nlp_receive/<filename>/<user_id>", methods=['POST'])
@token_required("nlp")
def nlp_receive(filename, user_id):
    """
    This endpoint receives preprocessed date from NLP app and saves vectorized
    representation of documents in database.
    """
    data = request.get_json()
    status_code = int(data["status_code"])

    if status_code < 400:
        data.pop("status_code", None)
        user = User.query.get(int(user_id))
        new_file = File(name=filename, owner=user, text=data)
        db.session.add(new_file)
        db.session.commit()
    else:
        file_path = os.path.join(current_app.root_path, "static/users_files", current_user.username,
                                 str(filename))
        os.remove(file_path)

    return {"info": "accepted"}, 202


@img2txt.route("/imgtxt", methods=['GET', 'POST'])
@login_required
@check_confirmed
def imgtxt():
    """
    Search files based on user query and display amount of all user files.
    """
    search_form = FindFileForm()
    all_files = File.query.filter_by(owner=current_user).all()

    # Searching documents
    if search_form.validate_on_submit():
        URL_nlp = URL_NLP+"/rank"
        query = search_form.searchbox.data  # user query
        documents_amount = search_form.amount.data if search_form.amount.data < len(all_files) else len(all_files)
        documents = []
        if len(all_files) > 0:
            for f in all_files:
                # Loop over all documents and add them
                # to 'documents' list
                pages = []
                for i in range((len(f.text) - 1) // 2):
                    # text column in File database is a JSON object which
                    # consists of following fields: Document embedding,
                    # tokenized pages from 1st to the last page
                    # and pages embeddings from 1st to the last page.
                    # That's why in the loop over the length of dictionary we
                    # subtract key of document embedding and then divide it by 2
                    # to get the amount of pages.
                    pages.append(f.text[f"Embedding{i}"])
                doc = {"name": f.name,
                       "embedding": f.text["Doc_embedding"],
                       "pages": pages}
                documents.append(doc)

            request_json = {"query": query,
                            "documents": documents,
                            "doc_amount": documents_amount}
            try:
                # Connect to NLP app and find documents most appropriate
                # for user's query.
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
        # Template to be rendered when user searched something.
        template = render_template("img2txt.html", title=title, search_form=search_form,
                                   ranked_docs=session["RANKED_DOCS"], user_files_amount=len(all_files))
        session.pop("RANKED_DOCS")
    elif session.get("NO_DOCS_TO_RANK", None) is not None:
        # Template to be rendered when user searched something but there are no documents
        # on tthe server.
        template = render_template("img2txt.html", title=title, search_form=search_form,
                                   no_docs=session["NO_DOCS_TO_RANK"], user_files_amount=len(all_files))
        session.pop("NO_DOCS_TO_RANK")
    else:
        # Default template.
        template = render_template("img2txt.html", title=title, search_form=search_form, user_files_amount=len(all_files))
    return template

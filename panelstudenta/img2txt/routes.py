#!/usr/bin/python
# -*- coding: utf-8 -*-
from flask import render_template, url_for, flash, redirect, \
    request, abort, session, Blueprint, current_app, send_from_directory
from werkzeug.utils import safe_join
from panelstudenta.img2txt.forms import NewFileForm, FindFileForm
from panelstudenta import db
from panelstudenta.models import File
from panelstudenta.general_utils import check_confirmed
from flask_login import current_user, login_required
import os
import requests
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())


img2txt = Blueprint('img2txt', __name__, template_folder='templates')


@img2txt.route("/imgtxt/<file_name>", methods=['GET', 'POST'])
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
    form = NewFileForm()

    # Adding new img2txt
    if form.validate_on_submit():
        if not os.path.exists(os.path.join(current_app.root_path, "static/users_files", current_user.username)):
            # Create file directory for user.
            os.makedirs(os.path.join(current_app.root_path, "static/users_files", current_user.username))
        file_path = os.path.join(current_app.root_path, "static/users_files", current_user.username,
                                 form.file.data.filename)
        form.file.data.save(file_path)

        # SEKCJA DO EDYCJI
        files = {'file': open(file_path, 'rb')}
        URL_img = os.environ.get("URL_IMG")
        URL_nlp = os.environ.get("URL_NLP_PREP")
        try:
            response = requests.post(URL_img, files=files)
        except requests.exceptions.ConnectionError:
            flash("Problem z połączeniem", "danger")
            os.remove(file_path)
            return redirect(url_for("img2txt.user_files"))

        if response.status_code == 200:
            ocr_response = response.json()
        else:
            os.remove(file_path)
            abort(response.status_code, response.json())
        # KONIEC SEKCJI

        response = requests.post(URL_nlp, json=ocr_response)
        if response.status_code == 200:
            new_file = File(name=form.file.data.filename, owner=current_user, text=response.json())
            db.session.add(new_file)
            db.session.commit()
            flash("Dodano nowy plik!", "success")
            return redirect(url_for("img2txt.user_files"))
        else:
            os.remove(file_path)
            abort(response.status_code, response.json())

    page = request.args.get('page', 1, type=int)
    files_display = File.query.filter_by(owner=current_user).paginate(page=page, per_page=5)
    return render_template("user_files.html", title="Wyszukiwarka plików", form=form, files_display=files_display)


@img2txt.route("/imgtxt", methods=['GET', 'POST'])
@login_required
@check_confirmed
def imgtxt():
    search_form = FindFileForm()
    all_files = File.query.filter_by(owner=current_user).all()
    # Searching documents
    if search_form.validate_on_submit():
        URL_nlp = os.environ.get("URL_NLP_RANK")
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

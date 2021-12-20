#!/usr/bin/python
# -*- coding: utf-8 -*-
from flask.cli import FlaskGroup
from panelstudenta import create_app, db
from panelstudenta.delete_unconfirmed import delete_unconfirmed

app = create_app()
app.app_context().push()
cli = FlaskGroup(app)


@cli.command("create_db")
def create_db():
    db.drop_all()
    db.create_all()
    db.session.commit()


@cli.command("delete_unconfirmed")
def del_un():
    delete_unconfirmed(1)


if __name__ == '__main__':
    cli()

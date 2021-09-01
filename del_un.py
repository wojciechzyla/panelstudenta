#!/usr/bin/python
# -*- coding: utf-8 -*-
from panelstudenta import create_app
from panelstudenta.delete_unconfirmed import delete_unconfirmed

app = create_app()
app.app_context().push()
delete_unconfirmed(2)

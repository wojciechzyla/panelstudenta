#!/usr/bin/python
# -*- coding: utf-8 -*-
from panelstudenta import create_app, db
from flask_migrate import Migrate
app = create_app()
migrate = Migrate(app, db)

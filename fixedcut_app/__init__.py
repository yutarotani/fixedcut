from flask import Flask
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__, static_folder='./templates/static')
app.config.from_object('fixedcut_app.config') 

db = SQLAlchemy(app)
from.models import fixedcut, senkyo_person, senkyo_sendgroup

import fixedcut_app.views
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import os

UPLOAD_FOLDER = './upload'
ALLOWED_EXTENSIONS = set(['eps'])
EPS_MIMETYPE = 'application/postscript'

app = Flask(__name__, static_folder='./templates/static')
app.config.from_object('fixedcut_app.config') 
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.secret_key = 'secret_key'

db = SQLAlchemy(app)
from.models import fixedcut, senkyo_person, senkyo_sendgroup

import fixedcut_app.views
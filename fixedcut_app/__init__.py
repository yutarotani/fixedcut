from flask import Flask
from flask_sqlalchemy import SQLAlchemy

UPLOAD_FOLDER = './upload'
ALLOWED_EXTENSIONS = set(['eps'])

app = Flask(__name__, static_folder='./templates/static')
app.config.from_object('fixedcut_app.config') 
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

db = SQLAlchemy(app)
from.models import fixedcut, senkyo_person, senkyo_sendgroup

import fixedcut_app.views
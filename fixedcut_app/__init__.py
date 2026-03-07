from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import logging
from logging.handlers import RotatingFileHandler
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

if not os.path.exists('logs'):
    os.mkdir('logs')

handler = RotatingFileHandler('logs/app.log', maxBytes=1000000, backupCount=5)
formatter = logging.Formatter(
    '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
handler.setFormatter(formatter)
handler.setLevel(logging.INFO)

app.logger.addHandler(handler)
app.logger.setLevel(logging.INFO)
app.logger.info('Application startup')
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import logging
from logging.handlers import RotatingFileHandler
import os
import glob
from datetime import datetime, timedelta

UPLOAD_FOLDER = './upload'
ALLOWED_EXTENSIONS = set(['eps'])
EPS_MIMETYPE = 'application/postscript'

app = Flask(__name__, static_folder='./templates/static')
app.config.from_object('fixedcut_app.config') 
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.secret_key = 'secret_key'

db = SQLAlchemy(app)

# ログ設定
if not os.path.exists('logs'):
    os.mkdir('logs')

handler = RotatingFileHandler('logs/app.log', maxBytes=1000000, backupCount=5)
formatter = logging.Formatter(
    '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
handler.setFormatter(formatter)
handler.setLevel(logging.INFO)

app.logger.addHandler(handler)
app.logger.setLevel(logging.INFO)

# 古いログファイルを削除する関数
def cleanup_old_logs(log_dir='logs', days=7):
    """
    指定日数以上前のログファイルを削除
    """
    cutoff_date = datetime.now() - timedelta(days=days)
    log_pattern = os.path.join(log_dir, 'app.log*')  # app.log と app.log.1 など
    
    for log_file in glob.glob(log_pattern):
        if os.path.isfile(log_file):
            file_mtime = datetime.fromtimestamp(os.path.getmtime(log_file))
            if file_mtime < cutoff_date:
                try:
                    os.remove(log_file)
                    app.logger.info(f"古いログファイルを削除: {log_file}")
                except OSError as e:
                    app.logger.warning(f"ログファイル削除失敗: {log_file} - {e}")

# アプリ起動時にログクリーンアップを実行
cleanup_old_logs()

app.logger.info('Application startup')

from.models import fixedcut, m_jyochu_image_cnv, senkyo_person, senkyo_sendgroup

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
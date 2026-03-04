from fixedcut_app import db
from datetime import datetime

class SenkyoSendGroup(db.Model):
    ___tablename__ = "SenkyoSendGroup"
    id = db.Column(db.Integer, primary_key=True) 
    syubetu = db.Column(db.String(5)) #選挙種別
    area = db.Column(db.String(5)) #エリア名
    syosenkyoNum = db.Column(db.Integer) #小選挙数
    sendGroup = db.Column(db.String(2)) #配信グループ
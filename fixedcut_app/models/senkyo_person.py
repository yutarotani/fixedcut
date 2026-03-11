from fixedcut_app import db
from datetime import datetime

class SenkyoPerson(db.Model):
    ___tablename__ = "SenkyoPerson"
    id = db.Column(db.Integer, primary_key=True) #候補者番号
    syubetu = db.Column(db.String(5)) #選挙種別(選挙区、比例、重複)
    senkyoku = db.Column(db.String(10)) #選挙区（福島）
    senkyokuNo = db.Column(db.String(5)) #選挙区番号（1区）
    sendGroup = db.Column(db.String(2)) #配信グループ（A～C）
    hirei = db.Column(db.String(10))  #比例選挙単位（東北ブロック）
    name = db.Column(db.String(20))  #氏名
    hurigana = db.Column(db.String(20))  #指名読み仮名
    name_jikai = db.Column(db.String(100))  #指名字解
    kyodo_name = db.Column(db.String(20))  #共同表記氏名
    seibetsu = db.Column(db.String(5))  #性別
    seito = db.Column(db.String(30))  #政党
    genshinbetu = db.Column(db.String(2))  #現新別
    facefilename = db.Column(db.String(100))  #顔写真ファイル名
    photo_date = db.Column(db.DateTime)  #撮影日
    CD_No = db.Column(db.String(5))  #配信CD
    fixedcutID = db.Column(db.String(20))  #固定カットID
    updateCount = db.Column(db.Integer) #更新回数
    store_date = db.Column(db.DateTime)
    operater = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now)  # 作成日時
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)  # 更新日時
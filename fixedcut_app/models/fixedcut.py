from fixedcut_app import db
from datetime import datetime

class FixedCut(db.Model):
    ___tablename__ = "fixedcut"
    id = db.Column(db.String(20), primary_key=True) #固定カットID
    midashi = db.Column(db.String(30)) #仮見出し
    Str = db.Column(db.String(100)) #一体化時文字列
    colorUrl = db.Column(db.String(100)) #カラー画像のURL
    monoUrl = db.Column(db.String(100)) #モノクロ画像のURL
    GWFlg = db.Column(db.Boolean, default=False) #GW登録対象
    prodFlg = db.Column(db.Boolean, default=False) #組版本番登録済みか
    OTFlg = db.Column(db.Boolean, default=False) #組版OT系登録済みか
    comment = db.Column(db.String(255)) #コメント
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now)  # 作成日時
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)  # 更新日時

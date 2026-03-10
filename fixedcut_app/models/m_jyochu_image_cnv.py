from fixedcut_app import db


class MJyochuImageCnv(db.Model):
    __tablename__ = "m_jyochu_image_cnv"

    # Excelの先頭列「データ説明」も保持する
    data_description = db.Column(db.String(255), default="")
    fixed_cut_id = db.Column(db.String(100), primary_key=True)  # 固定カットID
    fixed_cut_img_explanation = db.Column(db.String(255), default="")
    upd_count = db.Column(db.Integer, default=0)
    created_datetime = db.Column(db.String(30), default="CURRENT_TIMESTAMP")
    created_user = db.Column(db.String(30), default="Initial")
    created_term = db.Column(db.String(30), default="")
    created_pgm = db.Column(db.String(30), default="")
    created_trn_id = db.Column(db.String(30), default="")
    updated_datetime = db.Column(db.String(30), default="CURRENT_TIMESTAMP")
    updated_user = db.Column(db.String(30), default="Initial")
    updated_term = db.Column(db.String(30), default="")
    updated_pgm = db.Column(db.String(30), default="")
    updated_trn_id = db.Column(db.String(30), default="")
    patch_no = db.Column(db.String(30), default="")
    patch_datetime = db.Column(db.String(30), default="[NULL]")
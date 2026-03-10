from flask import render_template, request, redirect, url_for, flash, send_from_directory, send_file
from datetime import datetime
from fixedcut_app import app, db
from fixedcut_app.models.fixedcut import FixedCut
from fixedcut_app.models.m_jyochu_image_cnv import MJyochuImageCnv
from fixedcut_app.models.senkyo_person import SenkyoPerson
from fixedcut_app.models.senkyo_sendgroup import SenkyoSendGroup
import os, pathlib, sqlite3, shutil
from sqlalchemy import and_
from werkzeug.utils import secure_filename
from openpyxl import load_workbook, Workbook
from io import BytesIO
import csv


@app.route('/')
def index():
    return render_template('index.html', name='Flask Beginner')


def _to_text(value):
    if value is None:
        return ""
    return str(value).strip()


def _to_int(value, default=0):
    if value is None or value == "":
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _xlsx_base_dir():
    return pathlib.Path(app.static_folder) / 'xlsx'


def _senkyo_data_extensions():
    return {'.xlsx', '.xlsm', '.xls', '.csv'}


def _normalize_senkyoku(value):
    text = _to_text(value)
    for ch in ('\u3000', '0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '０', '１', '２', '３', '４', '５', '６', '７', '８', '９'):
        text = text.replace(ch, '')
    return text.strip().strip('区')


def _to_int_or_none(value):
    text = _to_text(value)
    if text == '':
        return None
    try:
        return int(float(text))
    except (TypeError, ValueError):
        return None


def _parse_date_or_none(value):
    text = _to_text(value).strip()
    if text == '':
        return None
    for fmt in ('%Y/%m/%d', '%Y-%m-%d', '%Y.%m.%d', '%Y%m%d'):
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            continue
    return None


def _match_sendgroup_value(syubetu, senkyoku, senkyoku_no_num, hirei):
    query = db.session.query(SenkyoSendGroup)
    sendgroup = None

    if syubetu == '比例':
        if hirei:
            sendgroup = query.filter(SenkyoSendGroup.area == hirei).order_by(SenkyoSendGroup.id.asc()).first()
    else:
        if senkyoku and senkyoku_no_num is not None:
            sendgroup = query.filter(
                SenkyoSendGroup.area == senkyoku,
                SenkyoSendGroup.syosenkyoNum == senkyoku_no_num,
            ).order_by(SenkyoSendGroup.id.asc()).first()
        if sendgroup is None and senkyoku:
            sendgroup = query.filter(SenkyoSendGroup.area == senkyoku).order_by(SenkyoSendGroup.id.asc()).first()

    if sendgroup is None and hirei:
        sendgroup = query.filter(SenkyoSendGroup.area == hirei).order_by(SenkyoSendGroup.id.asc()).first()

    return sendgroup.sendGroup if sendgroup else ''


def _iter_upload_rows(file_path):
    ext = file_path.suffix.lower()
    if ext == '.csv':
        rows = None
        for enc in ('cp932', 'shift_jis', 'utf-8-sig', 'utf-8'):
            try:
                with open(file_path, 'r', encoding=enc, newline='') as f:
                    rows = list(csv.reader(f))
                break
            except UnicodeDecodeError:
                continue
        if rows is None:
            raise ValueError('CSVの文字コードを判定できませんでした')
        for row in rows[1:]:
            yield row
        return

    wb = load_workbook(file_path, data_only=True)
    ws = wb.active
    for row in ws.iter_rows(min_row=2, max_row=ws.max_row, values_only=True):
        yield list(row)


def _upsert_senkyo_person_from_cd_file(file_path):
    inserted = 0
    updated = 0
    skipped = 0

    for row in _iter_upload_rows(file_path):
        if row is None or len(row) < 16:
            skipped += 1
            continue

        personid = _to_int_or_none(row[5])
        if personid is None:
            skipped += 1
            continue

        syubetu = _to_text(row[1])
        if syubetu in ('選挙区', '重複'):
            senkyoku = _normalize_senkyoku(row[3])
        else:
            senkyoku = ''

        senkyoku_no_num = _to_int_or_none(row[2])
        if syubetu == '比例' or senkyoku_no_num is None:
            senkyoku_no = ''
        else:
            senkyoku_no = f'{senkyoku_no_num}区'

        hirei = _to_text(row[4]).replace('\u3000', '')
        send_group = _match_sendgroup_value(syubetu, senkyoku, senkyoku_no_num, hirei)

        payload = {
            'syubetu': syubetu,
            'senkyoku': senkyoku,
            'senkyokuNo': senkyoku_no,
            'sendGroup': send_group,
            'hirei': hirei,
            'name': _to_text(row[6]).replace('\u3000', ''),
            'hurigana': _to_text(row[7]).replace('\u3000', ''),
            'name_jikai': _to_text(row[8]).replace('\u3000', ''),
            'kyodo_name': _to_text(row[9]).replace('\u3000', ''),
            'seibetsu': _to_text(row[10]),
            'seito': _to_text(row[11]).replace('\u3000', ''),
            'genshinbetu': _to_text(row[12]),
            'facefilename': _to_text(row[13]),
            'photo_date': _parse_date_or_none(row[15]),
            'CD_No': _to_text(row[14]),
            'fixedcutID': '',
            'updateCount': 0,
        }

        record = db.session.query(SenkyoPerson).filter(SenkyoPerson.id == personid).first()
        if record is None:
            record = SenkyoPerson(id=personid, **payload)
            db.session.add(record)
            inserted += 1
        else:
            for key, value in payload.items():
                setattr(record, key, value)
            updated += 1

    return inserted, updated, skipped


@app.route('/m_jyochu_image_cnv/upload', methods=['POST'])
def upload_m_jyochu_excel():
    upload_file = request.files.get('excelFile')
    if not upload_file or upload_file.filename == '':
        flash('※Excelファイルを選択してください※')
        return redirect(url_for('index'))

    ext = pathlib.Path(upload_file.filename).suffix.lower()
    if ext not in {'.xlsx', '.xlsm', '.xls', '.csv'}:
        flash('※Excel/CSV形式(.xlsx/.xlsm/.xls/.csv)のファイルを選択してください※')
        return redirect(url_for('index'))

    xlsx_dir = _xlsx_base_dir()
    xlsx_dir.mkdir(parents=True, exist_ok=True)

    safe_name = secure_filename(upload_file.filename)
    if not safe_name:
        safe_name = 'uploaded_m_jyochu_image_cnv.xlsx'

    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    save_path = xlsx_dir / f'{timestamp}_{safe_name}'
    upload_file.save(save_path)

    if ext == '.csv':
        rows = None
        for enc in ('utf-8-sig', 'cp932', 'shift_jis'):
            try:
                with open(save_path, 'r', encoding=enc, newline='') as f:
                    rows = list(csv.reader(f))
                break
            except UnicodeDecodeError:
                continue
        if rows is None:
            flash('※CSVの文字コード判定に失敗しました※')
            return redirect(url_for('index'))
        if len(rows) < 2:
            flash('※データ行がありません※')
            return redirect(url_for('index'))

        headers = [_to_text(x) for x in rows[0]]
        data_rows = rows[1:]
    else:
        try:
            wb = load_workbook(save_path, data_only=True)
            ws = wb.active
        except Exception as exc:
            flash(f'※Excel読込に失敗しました※ {exc}')
            return redirect(url_for('index'))

        if ws.max_row < 2:
            flash('※データ行がありません※')
            return redirect(url_for('index'))

        headers = [_to_text(ws.cell(1, c).value) for c in range(1, ws.max_column + 1)]
        data_rows = list(ws.iter_rows(min_row=2, max_row=ws.max_row, min_col=1, max_col=max(ws.max_column, 16), values_only=True))

    header_index = {h: i for i, h in enumerate(headers)}

    def pick(row, header_name, fallback_index):
        idx = header_index.get(header_name)
        if idx is not None and idx < len(row):
            return row[idx]
        if fallback_index < len(row):
            return row[fallback_index]
        return None

    inserted = 0
    updated = 0
    unchanged = 0
    skipped = 0

    try:
        for row in data_rows:
            fixed_cut_id = _to_text(pick(row, 'fixed_cut_id', 1))
            if not fixed_cut_id:
                skipped += 1
                continue

            new_values = {
                'data_description': _to_text(pick(row, 'データ説明', 0)),
                'fixed_cut_img_explanation': _to_text(pick(row, 'fixed_cut_img_explanation', 2)),
                'upd_count': _to_int(pick(row, 'upd_count', 3), 0),
                'created_datetime': _to_text(pick(row, 'created_datetime', 4)) or 'CURRENT_TIMESTAMP',
                'created_user': _to_text(pick(row, 'created_user', 5)) or 'Initial',
                'created_term': _to_text(pick(row, 'created_term', 6)),
                'created_pgm': _to_text(pick(row, 'created_pgm', 7)),
                'created_trn_id': _to_text(pick(row, 'created_trn_id', 8)),
                'updated_datetime': _to_text(pick(row, 'updated_datetime', 9)) or 'CURRENT_TIMESTAMP',
                'updated_user': _to_text(pick(row, 'updated_user', 10)) or 'Initial',
                'updated_term': _to_text(pick(row, 'updated_term', 11)),
                'updated_pgm': _to_text(pick(row, 'updated_pgm', 12)),
                'updated_trn_id': _to_text(pick(row, 'updated_trn_id', 13)),
                'patch_no': _to_text(pick(row, 'patch_no', 14)),
                'patch_datetime': _to_text(pick(row, 'patch_datetime', 15)) or '[NULL]',
            }

            record = db.session.get(MJyochuImageCnv, fixed_cut_id)
            if record is None:
                record = MJyochuImageCnv(fixed_cut_id=fixed_cut_id, **new_values)
                db.session.add(record)
                inserted += 1
                continue

            changed = False
            for key, val in new_values.items():
                if getattr(record, key) != val:
                    setattr(record, key, val)
                    changed = True

            if changed:
                updated += 1
            else:
                unchanged += 1

        db.session.commit()
    except Exception as exc:
        db.session.rollback()
        flash(f'※差分反映に失敗しました※ {exc}')
        return redirect(url_for('index'))

    flash('Excel取込と差分反映が完了しました')
    flash(f'保存先: {save_path}')
    flash(f'追加: {inserted}件 / 更新: {updated}件 / 変更なし: {unchanged}件 / スキップ: {skipped}件')
    return redirect(url_for('index'))


@app.route('/m_jyochu_image_cnv/download', methods=['GET'])
def download_m_jyochu_excel():
    records = db.session.query(MJyochuImageCnv).order_by(MJyochuImageCnv.fixed_cut_id.asc()).all()

    wb = Workbook()
    ws = wb.active
    ws.title = 'm_jyochu_image_cnv'

    ws.append([
        'データ説明',
        'fixed_cut_id',
        'fixed_cut_img_explanation',
        'upd_count',
        'created_datetime',
        'created_user',
        'created_term',
        'created_pgm',
        'created_trn_id',
        'updated_datetime',
        'updated_user',
        'updated_term',
        'updated_pgm',
        'updated_trn_id',
        'patch_no',
        'patch_datetime',
    ])

    for rec in records:
        ws.append([
            rec.data_description,
            rec.fixed_cut_id,
            rec.fixed_cut_img_explanation,
            rec.upd_count,
            rec.created_datetime,
            rec.created_user,
            rec.created_term,
            rec.created_pgm,
            rec.created_trn_id,
            rec.updated_datetime,
            rec.updated_user,
            rec.updated_term,
            rec.updated_pgm,
            rec.updated_trn_id,
            rec.patch_no,
            rec.patch_datetime,
        ])

    output = BytesIO()
    wb.save(output)
    output.seek(0)

    file_name = f"m_jyochu_image_cnv_{datetime.now().strftime('%Y%m%d%H%M%S')}.xlsx"
    return send_file(
        output,
        as_attachment=True,
        download_name=file_name,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    )


@app.route('/senkyo')
def senkyo():
    cd_dir = _xlsx_base_dir() / 'CD'
    cd_excel_files = []
    if cd_dir.exists():
        for file_path in cd_dir.iterdir():
            if file_path.is_file() and file_path.suffix.lower() in _senkyo_data_extensions():
                cd_excel_files.append(file_path.name)

    cd_excel_files.sort()
    return render_template('senkyo.html', name='Senkyo page', cd_excel_files=cd_excel_files)


def _save_excel_to_static_subdir(upload_file, sub_dir_name, default_name):
    if not upload_file or upload_file.filename == '':
        return False, '※Excelファイルを選択してください※'

    ext = pathlib.Path(upload_file.filename).suffix.lower()
    if ext not in _senkyo_data_extensions():
        return False, '※Excel/CSV形式(.xlsx/.xlsm/.xls/.csv)のファイルを選択してください※'

    base_dir = _xlsx_base_dir() / sub_dir_name
    base_dir.mkdir(parents=True, exist_ok=True)

    safe_name = secure_filename(upload_file.filename) or default_name
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    save_path = base_dir / f'{timestamp}_{safe_name}'
    upload_file.save(save_path)

    return True, f'保存完了: {save_path}'


@app.route('/senkyo/upload_cd', methods=['POST'])
def upload_senkyo_cd_excel():
    upload_file = request.files.get('cdExcelFile')
    ok, message = _save_excel_to_static_subdir(upload_file, 'CD', 'cd_upload.xlsx')
    flash(message)

    if ok:
        saved_path = pathlib.Path(message.split(': ', 1)[1])
        try:
            inserted, updated, skipped = _upsert_senkyo_person_from_cd_file(saved_path)
            db.session.commit()
            flash(f'SenkyoPerson 追加: {inserted}件 / 更新: {updated}件 / スキップ: {skipped}件')
        except Exception as exc:
            db.session.rollback()
            flash(f'※SenkyoPerson取込に失敗しました※ {exc}')

    return redirect(url_for('senkyo'))


@app.route('/senkyo/upload_sendgroup', methods=['POST'])
def upload_senkyo_sendgroup_excel():
    upload_file = request.files.get('sendgroupExcelFile')
    ok, message = _save_excel_to_static_subdir(upload_file, 'sendgroup', 'sendgroup_upload.xlsx')
    flash(message)
    return redirect(url_for('senkyo'))


def _build_excel_response(records, sheet_title, file_prefix):
    wb = Workbook()
    ws = wb.active
    ws.title = sheet_title

    if records:
        columns = [c.name for c in records[0].__table__.columns]
    else:
        columns = []

    if columns:
        ws.append(columns)
        for rec in records:
            ws.append([getattr(rec, col) for col in columns])

    output = BytesIO()
    wb.save(output)
    output.seek(0)

    file_name = f"{file_prefix}_{datetime.now().strftime('%Y%m%d%H%M%S')}.xlsx"
    return send_file(
        output,
        as_attachment=True,
        download_name=file_name,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    )


@app.route('/senkyo/download_person_excel', methods=['GET'])
def download_senkyo_person_excel():
    records = db.session.query(SenkyoPerson).order_by(SenkyoPerson.id.asc()).all()
    return _build_excel_response(records, 'SenkyoPerson', 'senkyo_person')


@app.route('/senkyo/download_sendgroup_excel', methods=['GET'])
def download_senkyo_sendgroup_excel():
    records = db.session.query(SenkyoSendGroup).order_by(SenkyoSendGroup.id.asc()).all()
    return _build_excel_response(records, 'SenkyoSendGroup', 'senkyo_sendgroup')


@app.route('/senkyo/reset_cd_person', methods=['POST'])
def reset_cd_person_data():
    cd_dir = _xlsx_base_dir() / 'CD'
    deleted_files = 0

    try:
        if cd_dir.exists():
            for file_path in cd_dir.glob('*'):
                if file_path.is_file() and file_path.suffix.lower() in _senkyo_data_extensions():
                    file_path.unlink()
                    deleted_files += 1

        deleted_rows = db.session.query(SenkyoPerson).delete(synchronize_session=False)
        db.session.commit()

        flash('CDフォルダのExcel削除とSenkyoPerson全削除を実行しました')
        flash(f'削除ファイル数: {deleted_files}件 / 削除レコード数: {deleted_rows}件')
    except Exception as exc:
        db.session.rollback()
        flash(f'※削除処理に失敗しました※ {exc}')

    return redirect(url_for('senkyo'))


@app.route('/senkyo_person_table')
def senkyo_person_table():
    person_rows = db.session.query(SenkyoPerson).order_by(SenkyoPerson.id.asc()).all()
    person_columns = [c.name for c in SenkyoPerson.__table__.columns]

    return render_template(
        'senkyo_person_table.html',
        person_rows=person_rows,
        person_columns=person_columns,
    )


@app.route('/senkyo_sendgroup_table')
def senkyo_sendgroup_table():
    sendgroup_rows = db.session.query(SenkyoSendGroup).order_by(SenkyoSendGroup.id.asc()).all()
    sendgroup_columns = [c.name for c in SenkyoSendGroup.__table__.columns]

    return render_template(
        'senkyo_sendgroup_table.html',
        sendgroup_rows=sendgroup_rows,
        sendgroup_columns=sendgroup_columns,
    )


@app.route('/senkyo_serch', methods=['POST'])
def senkyo_serch():
    print("データを受け取りました")
    req = request.form["ID"]
    print(req)
    return f'POSTdata:{req}' 


@app.route('/general', methods=['GET', 'POST'])
@app.route('/general/<int:page>', methods=['GET', 'POST'])
def general(page=1):
    per_page = 100
    
    # 検索条件を取得（POSTまたはGETパラメータから）
    res = {}
    res["midashi"] = request.values.get("midashi", "")
    res["ID"] = request.values.get("ID", "")
    res["Str"] = request.values.get("Str", "")
    res["GWFlg"] = request.values.get("GWFlg", "")
    res["prodFlg"] = request.values.get("prodFlg", "")
    res["OTFlg"] = request.values.get("OTFlg", "")
    res["startdate"] = request.values.get("startdate", "")
    res["enddate"] = request.values.get("enddate", "")

    savelist = [res["midashi"], res["ID"], res["Str"],
                res["GWFlg"], res["prodFlg"], res["OTFlg"],
                res["startdate"], res["enddate"]]

    # クエリ構築
    query = db.session.query(FixedCut)
    
    # AND検索：固定カットID、仮見出し、一体化文字列
    if res["ID"]:
        query = query.filter(FixedCut.id.contains(res["ID"]))
    if res["midashi"]:
        query = query.filter(FixedCut.midashi.contains(res["midashi"]))
    if res["Str"]:
        query = query.filter(FixedCut.Str.contains(res["Str"]))
    
    # 追加フィルタ：GWFlg, prodFlg, OTFlg, startdate, enddate
    if res["GWFlg"] == "on":
        query = query.filter(FixedCut.GWFlg == True)
    if res["prodFlg"] == "on":
        query = query.filter(FixedCut.prodFlg == True)
    if res["OTFlg"] == "on":
        query = query.filter(FixedCut.OTFlg == True)
    if res["startdate"]:
        start_date = datetime.strptime(res["startdate"], '%Y-%m-%d')
        query = query.filter(FixedCut.created_at >= start_date)
    if res["enddate"]:
        end_date = datetime.strptime(res["enddate"], '%Y-%m-%d')
        query = query.filter(FixedCut.created_at <= end_date)
    
    # ページネーション適用
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    results = pagination.items
    
    return render_template('general.html', name='General page', results=results, savelist=savelist, pagination=pagination) 


@app.route('/general_add', methods=['GET', 'POST'])
def general_add():
    if request.method == 'GET':
        savelist = ["","","","","","","","",""]
        return render_template('general_add.html', savelist=savelist)
    
    # フォームデータを取得
    form_id = (request.form.get("id") or "").strip()
    form_midashi = request.form.get("midashi")
    form_Str = request.form.get("Str")
    form_colorUrl = request.files.get("colorUrl")
    form_monoUrl = request.files.get("monoUrl")
    form_GWFlg = request.form.get("GWFlg") == "on"
    form_prodFlg = request.form.get("prodFlg") == "on"
    form_OTFlg = request.form.get("OTFlg") == "on"
    form_comment = request.form.get("comment")

    savelist = [form_id, form_midashi, form_Str, form_colorUrl, form_monoUrl,
                form_GWFlg, form_prodFlg, form_OTFlg, form_comment]

    # 固定カットIDは必須
    if form_id == "":
        flash("※固定カットIDは必須です※")
        flash("固定カットIDを入力してから追加してください")
        return render_template('general_add.html', savelist=savelist)

    # 許可する拡張子
    ALLOWED_EXTENSIONS = {".eps", ".jpg", ".jpeg", ".svg"}

    # 拡張子チェック関数
    def is_valid_file(file):
        if not file or file.filename == "":
            return True  # ファイルなしはOK
        ext = pathlib.Path(file.filename).suffix.lower()
        return ext in ALLOWED_EXTENSIONS

    # 拡張子検証
    color_valid = is_valid_file(form_colorUrl)
    mono_valid = is_valid_file(form_monoUrl)

    # 無効な拡張子の場合、エラーメッセージを表示して終了
    if not color_valid or not mono_valid:
        flash("※画像ファイルが登録対象外の拡張子です※")
        flash('".eps", ".jpg", ".jpeg", ".svg"のみが登録できます')
        
        if form_colorUrl and form_colorUrl.filename and not color_valid:
            flash(f"カラー画像ファイル：{form_colorUrl.filename}")
        if form_monoUrl and form_monoUrl.filename and not mono_valid:
            flash(f"モノクロ画像ファイル：{form_monoUrl.filename}")
        
        app.logger.warning("Invalid file extension attempt by %s", request.remote_addr)
        return render_template('general_add.html', savelist=savelist)

    # ここから先は有効な拡張子のみ
    try:
        # ディレクトリ作成
        os.makedirs(f'fixedcut_app/templates/static/img/{form_id}/color', exist_ok=True)
        os.makedirs(f'fixedcut_app/templates/static/img/{form_id}/mono', exist_ok=True)

        # ファイル保存
        color_name = form_colorUrl.filename if form_colorUrl and form_colorUrl.filename else ""
        mono_name = form_monoUrl.filename if form_monoUrl and form_monoUrl.filename else ""

        if color_name:
            color_path = pathlib.Path(f'fixedcut_app/templates/static/img/{form_id}/color', color_name)
            form_colorUrl.save(color_path)

        if mono_name:
            mono_path = pathlib.Path(f'fixedcut_app/templates/static/img/{form_id}/mono', mono_name)
            form_monoUrl.save(mono_path)

        # DB登録
        fixedcut = FixedCut(
            id=form_id,
            midashi=form_midashi,
            Str=form_Str,
            colorUrl=f'img/{form_id}/color/{color_name}' if color_name else "",
            monoUrl=f'img/{form_id}/mono/{mono_name}' if mono_name else "",
            GWFlg=form_GWFlg,
            prodFlg=form_prodFlg,
            OTFlg=form_OTFlg,
            comment=form_comment,
        )
        db.session.add(fixedcut)

        # m_jyochu_image_cnv は fixed_cut_img_explanation を基準に分岐
        matched_jyochu = db.session.query(MJyochuImageCnv).filter(
            MJyochuImageCnv.fixed_cut_img_explanation == (form_Str or "")
        ).first()

        if matched_jyochu is None:
            new_jyochu = MJyochuImageCnv(
                fixed_cut_id=form_id,
                fixed_cut_img_explanation=form_Str or "",
            )
            db.session.add(new_jyochu)
        else:
            matched_jyochu.fixed_cut_img_explanation = form_Str or ""

        db.session.commit()

        flash(f"{form_id}をレコード追加しました！")
        app.logger.info("Added record id=%s by %s", form_id, request.remote_addr)

    except Exception as e:
        # クリーンアップ
        try:
            shutil.rmtree(f'fixedcut_app/templates/static/img/{form_id}/')
        except:
            pass

        print(f"例外args: {e.args}")
        
        if form_id == "":
            flash("※固定カットIDが入力されていません※")
            flash("固定カットIDを入力してレコード追加してください")
        else:
            flash("※すでに登録済みの固定カットIDです※")
            flash("固定カットIDを変更してレコード追加してください")
        
        app.logger.warning("Failed to add record id=%s by %s", form_id, request.remote_addr)

    return render_template('general_add.html', savelist=savelist)


@app.route('/general_detail/<string:id>', methods=['GET', 'POST'])
def general_detail(id):
    if request.method == 'GET':
        results = db.session.query(FixedCut).filter(FixedCut.id == id).all()
        if not results:
            return render_template('error_404.html'), 404
        print(results[0].GWFlg)
        jyochu_result = db.session.query(MJyochuImageCnv).filter(MJyochuImageCnv.fixed_cut_id == id).first()
        return render_template('general_detail.html', results=results, jyochu_result=jyochu_result)
    
    if request.method == 'POST':
        # フォームデータを取得（IDは変更しない）
        form_midashi = request.form.get("midashi")
        form_Str = request.form.get("Str")
        form_GWFlg = request.form.get("GWFlg") == "on"
        form_prodFlg = request.form.get("prodFlg") == "on"
        form_OTFlg = request.form.get("OTFlg") == "on"
        form_comment = request.form.get("comment")

        try:
            # 既存レコードを取得
            fixedcut = db.session.query(FixedCut).filter(FixedCut.id == id).first()
            if not fixedcut:
                flash("※指定されたレコードが見つかりません※")
                results = db.session.query(FixedCut).filter(FixedCut.id == id).all()
                jyochu_result = db.session.query(MJyochuImageCnv).filter(MJyochuImageCnv.fixed_cut_id == id).first()
                return render_template('general_detail.html', results=results, jyochu_result=jyochu_result)

            # レコード更新（ID以外）
            fixedcut.midashi = form_midashi
            fixedcut.Str = form_Str
            fixedcut.GWFlg = form_GWFlg
            fixedcut.prodFlg = form_prodFlg
            fixedcut.OTFlg = form_OTFlg
            fixedcut.comment = form_comment

            # 同一固定カットIDが m_jyochu_image_cnv に存在する場合は、説明を一体化時文字列で同期
            jyochu = db.session.query(MJyochuImageCnv).filter(MJyochuImageCnv.fixed_cut_id == id).first()
            if jyochu:
                jyochu.fixed_cut_img_explanation = form_Str or ""

            db.session.commit()

            flash(f"{id}をレコード更新しました！")
            app.logger.info("Updated record id=%s by %s", id, request.remote_addr)

        except Exception as e:
            print(f"例外args: {e.args}")
            
            flash("※レコード更新に失敗しました※")
            flash("入力内容を確認してください")
            
            app.logger.warning("Failed to update record id=%s by %s", id, request.remote_addr)

        # 更新後のデータを再取得して表示
        results = db.session.query(FixedCut).filter(FixedCut.id == id).all()
        jyochu_result = db.session.query(MJyochuImageCnv).filter(MJyochuImageCnv.fixed_cut_id == id).first()
        return render_template('general_detail.html', results=results, jyochu_result=jyochu_result)



@app.route('/general_delete/<string:id>')
def general_delete(id):
    print(f"DEBUG: general_delete called with id={id}")
    try:
        # 既存レコードを取得
        fixedcut = db.session.query(FixedCut).filter(FixedCut.id == id).first()
        print(f"DEBUG: Found record: {fixedcut}")
        if not fixedcut:
            flash("※指定されたレコードが見つかりません※")
            return redirect(url_for('general'))

        # 画像ファイルとフォルダの削除
        try:
            # IDと同名のフォルダを丸ごと削除（colorとmonoフォルダを含む）
            base_dir = pathlib.Path(f'fixedcut_app/templates/static/img/{id}')
            print(f"DEBUG: Attempting to delete directory: {base_dir}")
            print(f"DEBUG: Directory exists: {base_dir.exists()}")
            
            if base_dir.exists():
                print(f"DEBUG: Directory contents before deletion:")
                try:
                    for item in base_dir.iterdir():
                        print(f"DEBUG:   {item}")
                except Exception as e:
                    print(f"DEBUG: Error listing contents: {e}")
                
                print(f"DEBUG: Starting rmtree...")
                shutil.rmtree(base_dir)
                print(f"DEBUG: rmtree completed")
                
                # 削除確認
                if not base_dir.exists():
                    print(f"DEBUG: SUCCESS - Directory deleted: {base_dir}")
                    app.logger.info(f"Deleted image directory: {base_dir}")
                else:
                    print(f"DEBUG: ERROR - Directory still exists after rmtree: {base_dir}")
                    app.logger.error(f"Failed to delete directory after rmtree: {base_dir}")
            else:
                print(f"DEBUG: Directory does not exist: {base_dir}")
        except Exception as e:
            print(f"DEBUG: Exception during directory deletion: {e}")
            print(f"DEBUG: Exception type: {type(e)}")
            import traceback
            print(f"DEBUG: Traceback: {traceback.format_exc()}")
            app.logger.warning(f"Failed to delete image directory {id}: {e}")

        # DBからレコード削除
        print("DEBUG: Deleting record from DB")
        db.session.delete(fixedcut)
        db.session.commit()
        print("DEBUG: Committed deletion")

        # 削除後の確認
        deleted_check = db.session.query(FixedCut).filter(FixedCut.id == id).first()
        if deleted_check:
            flash("※レコード削除に失敗しました※")
            app.logger.error("Record still exists after delete attempt: %s", id)
            print("DEBUG: Record still exists after deletion!")
        else:
            flash(f"レコード {id} を削除しました")
            app.logger.info("Successfully deleted record id=%s by %s", id, request.remote_addr)
            print(f"DEBUG: Successfully deleted record {id}")

    except Exception as e:
        print(f"DEBUG: Exception in delete: {e}")
        print(f"例外args: {e.args}")
        flash("※レコード削除に失敗しました※")
        app.logger.warning("Failed to delete record id=%s by %s", id, request.remote_addr)

    # 削除後は1ページ目にリダイレクト
    print("DEBUG: Redirecting to general page 1")
    return redirect(url_for('general', page=1))



@app.route('/download/<path:filename>')
def download(filename):
    """
    filename には 'img/eeee/color/xxx.eps' のような
    static に対する相対パスが渡ってくる想定。
    """
    # セキュリティのためにパスが static_folder の外に出ないか
    # 必要なら検証を入れる（省略可）

    return send_from_directory(
        app.static_folder,      # __init__.py で static_folder='./templates/static' に設定済
        filename,
        as_attachment=True
    )

@app.errorhandler(404)
def not_found(error):
    flash(error)
    return render_template("error_404.html"), 404


@app.route('/api/check_id/<string:id>')
def check_id(id):
    """
    IDが存在するかチェックするAPI
    """
    record = db.session.query(FixedCut).filter(FixedCut.id == id).first()
    if record:
        return {'exists': True}
    else:
        return {'exists': False}


@app.before_request
def log_request():
    app.logger.info("Request: %s %s from %s", request.method, request.path, request.remote_addr)
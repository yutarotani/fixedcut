from flask import render_template, request, redirect, url_for
from datetime import datetime
from fixedcut_app import app
from fixedcut_app.models.fixedcut import FixedCut
import os, pathlib


@app.route('/')
def index():
    return render_template('index.html', name='Flask Beginner')


@app.route('/senkyo')
def senkyo():
    return render_template('senkyo.html', name='Senkyo page')


@app.route('/senkyo_serch', methods=['POST'])
def senkyo_serch():
    print("データを受け取りました")
    req = request.form["ID"]
    print(req)
    return f'POSTdata:{req}' 


@app.route('/general', methods=['GET', 'POST'])
def general():
    if request.method == 'GET':
        return render_template('general.html', name='General page')
    
    if request.method == 'POST':
        results = []
        print("データを受け取りました")
        res1 = {}
        res1["midashi"] = request.form["midashi"]
        res1["ID"]  = request.form["ID"]
        res1["Str"]  = request.form["Str"]

        print(res1)

        results.append(res1)

        return render_template('general.html', results=results) 


@app.route('/general_add', methods=['GET', 'POST'])
def general_add():
    if request.method == 'GET':
        return render_template('general_add.html')
    
    if request.method == 'POST':
        form_id = request.form.get("id")
        form_midashi = request.form.get("midashi")
        form_Str = request.form.get("Str")
        form_colorUrl = request.files.get("colorUrl")
        form_monoUrl = request.files.get("monoUrl")
        form_updateFlg = request.form.get("updateFlg")

        try:
            os.makedirs(f'fixedcut_app/upload/{form_id}/color')
        except(FileExistsError):
            pass
            
        try: 
            os.makedirs(f'fixedcut_app/upload/{form_id}/mono')
        except(FileExistsError):
            pass
        
        color_name = form_colorUrl.filename
        mono_name = form_monoUrl.filename

        color_path = pathlib.Path(f'fixedcut_app/upload/{form_id}/color' ,color_name)
        mono_path = pathlib.Path(f'fixedcut_app/upload/{form_id}/mono' ,mono_name)
        try:
            form_colorUrl.save(color_path)
        except(PermissionError):
            pass
        
        try:
            form_monoUrl.save(mono_path)
        except(PermissionError):
            pass

        fixedcut = FixedCut(
            id = form_id, #固定カットID
            midashi = form_midashi, #仮見出し
            Str = form_Str, #一体化時文字列
            colorUrl = color_path, #カラー画像のURL
            monoUrl = mono_path, #モノクロ画像のURL
            updateFlg = form_updateFlg, #モノクロ画像のURL
            created_at = datetime.now,  # 作成日時
            updated_at = datetime.now #更新日時
        )
        print(fixedcut)
        #db.session.add(fixedcut)
        #db.session.commit()
        return render_template('general_add.html')

@app.route('/general_detail')
def general_detail():
    return render_template('general_detail.html')


def allwed_file(filename):
    # .があるかどうかのチェックと、拡張子の確認
    # OKなら１、だめなら0
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

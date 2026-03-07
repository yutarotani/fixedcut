from flask import render_template, request, redirect, url_for, flash, send_from_directory, send_file
from datetime import datetime
from fixedcut_app import app, db
from fixedcut_app.models.fixedcut import FixedCut
import os, pathlib, sqlite3
from sqlalchemy import and_


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
        results = db.session.query(FixedCut).all()
        savelist = ["","","","","","","",""]
        return render_template('general.html', name='General page', results=results, savelist=savelist)
    
    if request.method == 'POST':
        print("データを受け取りました")
        res = {}
        res["midashi"] = request.form.get("midashi")
        res["ID"]  = request.form.get("ID")
        res["Str"]  = request.form.get("Str")
        res["GWFlg"]  = request.form.get("GWFlg")
        res["prodFlg"]  = request.form.get("prodFlg")
        res["OTFlg"]  = request.form.get("OTFlg")
        res["startdate"] = request.form.get("startdate")
        res["enddate"] = request.form.get("enddate")

        savelist = [res["midashi"], res["ID"], res["Str"],
                    res["GWFlg"], res["prodFlg"], res["OTFlg"],
                    res["startdate"], res["enddate"]]

        if res["GWFlg"] == "on":
            res.update(GWFlg=True)
        else:
            res.update(GWFlg=False)

        if res["prodFlg"] == "on":
            res.update(prodFlg=True)
        else:
            res.update(prodFlg=False)

        if res["OTFlg"] == "on":
            res.update(OTFlg=True)
        else:
            res.update(OTFlg=False)
        
        print(f"res:{res}")
        print(res["ID"])

        if res['midashi']=='' and res['ID']=='' and res['Str']=='' and res['GWFlg']==False and res['prodFlg']==False and res['OTFlg']==False and res['startdate']=='' and res['enddate']=='':
            results = db.session.query(FixedCut).all()
        else:
            results = db.session.query(FixedCut).filter(FixedCut.id.contains(res["ID"])).all()
            #results = result.
             #   FixedCut.id.contains(res["ID"]),
             #   FixedCut.Str.contains(res["Str"])#,
                #FixedCut.GWFlg == res["GWFlg"],
                #FixedCut.prodFlg == res["prodFlg"],
                #FixedCut.OTFlg == res["OTFlg"]
              #  )
               # ).all()


        print(f"results:{results}")
        print(type(results[0]))

        return render_template('general.html', results=results, savelist=savelist) 


@app.route('/general_add', methods=['GET', 'POST'])
def general_add():
    if request.method == 'GET':
        savelist=["","","","","","","","",""]
        return render_template('general_add.html', savelist=savelist)
    
    if request.method == 'POST':
        form_id = request.form.get("id")
        form_midashi = request.form.get("midashi")
        form_Str = request.form.get("Str")
        form_colorUrl = request.files.get("colorUrl")
        form_monoUrl = request.files.get("monoUrl")
        form_GWFlg = request.form.get("GWFlg")
        form_prodFlg = request.form.get("prodFlg")
        form_OTFlg = request.form.get("OTFlg")
        form_comment = request.form.get("comment")

        savelist = [form_id, form_midashi, form_Str, form_colorUrl, form_monoUrl,
                    form_GWFlg, form_prodFlg, form_OTFlg,form_comment]

        print(f"form_GWFlg:{form_GWFlg}")

        bool_list = [form_GWFlg, form_prodFlg, form_OTFlg]
        bool_res = []
        for item in bool_list:
            if item == "on":
                bool_res.append(True)
            else:
                bool_res.append(False)


        print(datetime.now)
        print(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

        try:
            os.makedirs(f'fixedcut_app/templates/static/img/{form_id}/color')
        except(FileExistsError):
            pass
            
        try: 
            os.makedirs(f'fixedcut_app/templates/static/img/{form_id}/mono')
        except(FileExistsError):
            pass
        
        color_name = form_colorUrl.filename
        mono_name = form_monoUrl.filename

        color_path = pathlib.Path(f'fixedcut_app/templates/static/img/{form_id}/color', color_name)
        mono_path = pathlib.Path(f'fixedcut_app/templates/static/img/{form_id}/mono', mono_name)

        try:
            form_colorUrl.save(color_path)
        except(PermissionError):
            pass
        
        try:
            form_monoUrl.save(mono_path)
        except(PermissionError):
            pass


        try:
            fixedcut = FixedCut(
                id = form_id, #固定カットID
                midashi = form_midashi, #仮見出し
                Str = form_Str, #一体化時文字列
                colorUrl = f'img/{form_id}/color/{color_name}', #カラー画像のURL
                monoUrl = f'img/{form_id}/mono/{mono_name}', #モノクロ画像のURL
                GWFlg = bool_res[0], #GW登録対象
                prodFlg = bool_res[1], #組版本番登録済みか
                OTFlg = bool_res[2], #組版OT系登録済みか
                comment = form_comment, #コメント
                )
            db.session.add(fixedcut)
            db.session.commit()
            flash(f"{form_id}をレコード追加しました！")
            app.logger.info("Added record id=%s by %s", form_id, request.remote_addr)
        except Exception as e:
            print(print("例外args:", e.args))
            if form_id == "":
                flash("※固定カットIDが入力されていません※")
                flash("固定カットIDを入力してレコード追加してください")
                app.logger.warning("Failed to add record id=%s by %s", form_id, request.remote_addr)
            else:
                flash("※すでに登録済みの固定カットIDです※")
                flash("固定カットIDを変更してレコード追加してください")
                app.logger.warning("Failed to add record id=%s by %s", form_id, request.remote_addr)

        del bool_list
        del bool_res
        return render_template('general_add.html', savelist=savelist)


@app.route('/general_detail/<string:id>', methods=['GET', 'POST'])
def general_detail(id):
    if request.method == 'GET':
        results = db.session.query(FixedCut).filter(FixedCut.id.contains(id)).all()
        print(results[0].GWFlg)
        return render_template('general_detail.html', results=results)



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


@app.before_request
def log_request():
    app.logger.info("Request: %s %s from %s", request.method, request.path, request.remote_addr)
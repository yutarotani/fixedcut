from flask import render_template, request, redirect, url_for, flash, send_from_directory, send_file
from datetime import datetime
from fixedcut_app import app, db
from fixedcut_app.models.fixedcut import FixedCut
import os, pathlib, sqlite3, shutil
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
    form_id = request.form.get("id")
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
        return render_template('general_detail.html', results=results)
    
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
                return render_template('general_detail.html', results=results)

            # レコード更新（ID以外）
            fixedcut.midashi = form_midashi
            fixedcut.Str = form_Str
            fixedcut.GWFlg = form_GWFlg
            fixedcut.prodFlg = form_prodFlg
            fixedcut.OTFlg = form_OTFlg
            fixedcut.comment = form_comment

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
        return render_template('general_detail.html', results=results)



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
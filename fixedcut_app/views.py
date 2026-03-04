from flask import render_template, request
from fixedcut_app import app

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
    return render_template('general_add')


@app.route('/general_detail')
def general_detail():
    return render_template('general_detail.html')
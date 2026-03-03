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


@app.route('/general')
def general():
    return render_template('general.html', name='General page')


@app.route('/general_serch', methods=['GET', 'POST'])
def general_serch():
    if request.method == 'GET':
        return render_template('general.html', name='General page')
    
    if request.method == 'POST':
        print("データを受け取りました")
        req1 = request.form["midashi"]
        req2 = request.form["ID"]
        req3 = request.form["midashi"]
        print([req1, req2,req3])
        return f'POSTdata:{req1};{req2};{req3}' 

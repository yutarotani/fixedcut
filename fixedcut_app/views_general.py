from datetime import datetime
from flask import request, render_template

from fixedcut_app import db
from fixedcut_app.models.fixedcut import FixedCut


def general_handler(page=1):
    per_page = 100

    res = {}
    res['midashi'] = request.values.get('midashi', '')
    res['ID'] = request.values.get('ID', '')
    res['Str'] = request.values.get('Str', '')
    res['GWFlg'] = request.values.get('GWFlg', '')
    res['prodFlg'] = request.values.get('prodFlg', '')
    res['OTFlg'] = request.values.get('OTFlg', '')
    res['startdate'] = request.values.get('startdate', '')
    res['enddate'] = request.values.get('enddate', '')

    savelist = [
        res['midashi'],
        res['ID'],
        res['Str'],
        res['GWFlg'],
        res['prodFlg'],
        res['OTFlg'],
        res['startdate'],
        res['enddate'],
    ]

    query = db.session.query(FixedCut)

    if res['ID']:
        query = query.filter(FixedCut.id.contains(res['ID']))
    if res['midashi']:
        query = query.filter(FixedCut.midashi.contains(res['midashi']))
    if res['Str']:
        query = query.filter(FixedCut.Str.contains(res['Str']))

    if res['GWFlg'] == 'on':
        query = query.filter(FixedCut.GWFlg == True)
    if res['prodFlg'] == 'on':
        query = query.filter(FixedCut.prodFlg == True)
    if res['OTFlg'] == 'on':
        query = query.filter(FixedCut.OTFlg == True)
    if res['startdate']:
        start_date = datetime.strptime(res['startdate'], '%Y-%m-%d')
        query = query.filter(FixedCut.created_at >= start_date)
    if res['enddate']:
        end_date = datetime.strptime(res['enddate'], '%Y-%m-%d')
        query = query.filter(FixedCut.created_at <= end_date)

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    results = pagination.items

    return render_template('general.html', name='General page', results=results, savelist=savelist, pagination=pagination)

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
    res['men_name'] = request.values.get('men_name', '')
    res['GWFlg'] = request.values.get('GWFlg', '')
    res['prodFlg'] = request.values.get('prodFlg', '')
    res['OTFlg'] = request.values.get('OTFlg', '')
    res['startdate'] = request.values.get('startdate', '')
    res['enddate'] = request.values.get('enddate', '')
    res['sort_by'] = request.values.get('sort_by', 'created_at')
    res['sort_dir'] = request.values.get('sort_dir', 'desc')

    savelist = [
        res['midashi'],
        res['ID'],
        res['Str'],
        res['men_name'],
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
    if res['men_name']:
        query = query.filter(FixedCut.men_name.contains(res['men_name']))

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

    sortable_columns = {
        'id': FixedCut.id,
        'midashi': FixedCut.midashi,
        'Str': FixedCut.Str,
        'men_name': FixedCut.men_name,
        'colorUrl': FixedCut.colorUrl,
        'monoUrl': FixedCut.monoUrl,
        'GWFlg': FixedCut.GWFlg,
        'prodFlg': FixedCut.prodFlg,
        'OTFlg': FixedCut.OTFlg,
        'comment': FixedCut.comment,
        'created_at': FixedCut.created_at,
        'updated_at': FixedCut.updated_at,
    }

    sort_by = res['sort_by'] if res['sort_by'] in sortable_columns else 'created_at'
    sort_dir = 'asc' if res['sort_dir'] == 'asc' else 'desc'

    sort_column = sortable_columns[sort_by]
    if sort_dir == 'asc':
        query = query.order_by(sort_column.asc(), FixedCut.id.asc())
    else:
        query = query.order_by(sort_column.desc(), FixedCut.id.asc())

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    results = pagination.items

    return render_template(
        'general.html',
        name='General page',
        results=results,
        savelist=savelist,
        pagination=pagination,
        sort_by=sort_by,
        sort_dir=sort_dir,
    )

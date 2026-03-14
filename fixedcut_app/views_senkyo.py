from flask import render_template
from fixedcut_app import db
from fixedcut_app.models.senkyo_person import SenkyoPerson

from fixedcut_app.views import _xlsx_base_dir, _senkyo_data_extensions


def senkyo_handler():
    cd_dir = _xlsx_base_dir() / 'CD'
    cd_excel_files = []
    if cd_dir.exists():
        for file_path in cd_dir.iterdir():
            if file_path.is_file() and file_path.suffix.lower() in _senkyo_data_extensions():
                cd_excel_files.append(file_path.name)

    cd_excel_files.sort()
    return render_template('senkyo.html', name='Senkyo page', cd_excel_files=cd_excel_files)


def _to_text(value):
    if value is None:
        return ""
    return str(value).strip()


def _to_fullwidth_alnum(value):
    text = _to_text(value)
    converted = []
    for ch in text:
        code = ord(ch)
        if 48 <= code <= 57 or 65 <= code <= 90 or 97 <= code <= 122:
            converted.append(chr(code + 65248))
        else:
            converted.append(ch)
    return ''.join(converted)


def _build_senkyo_sendgroup_text_lines():
    rows = db.session.query(SenkyoPerson).order_by(SenkyoPerson.id.asc()).all()

    lines = {
        'hirei': [],
        'A': [],
        'B': [],
        'C': [],
    }

    for row in rows:
        syubetu = _to_text(row.syubetu)
        send_group = _to_text(row.sendGroup).upper()
        name = _to_text(row.name)
        fixedcut_id = _to_fullwidth_alnum(row.fixedcutID)

        if syubetu in ('比例', '重複'):
            area = _to_text(row.hirei).replace('ブロック', '')
            lines['hirei'].append(f"比例代表＿{area}＿{name},{fixedcut_id}")

        if syubetu in ('選挙区', '小選挙区', '重複') and send_group in ('A', 'B', 'C'):
            area1 = _to_text(row.senkyoku)
            area2 = _to_text(row.senkyokuNo)
            lines[send_group].append(f"{area1}＿{area2}＿{name},{fixedcut_id}")

    return lines


def senkyo_sendgroup_text_handler():
    lines = _build_senkyo_sendgroup_text_lines()
    sections = [
        {
            'key': 'hirei',
            'title': '固定カット比例',
            'lines': lines['hirei'],
        },
        {
            'key': 'A',
            'title': '固定カット小選挙区A',
            'lines': lines['A'],
        },
        {
            'key': 'B',
            'title': '固定カット小選挙区B',
            'lines': lines['B'],
        },
        {
            'key': 'C',
            'title': '固定カット小選挙区C',
            'lines': lines['C'],
        },
    ]

    total_line_count = sum(len(section['lines']) for section in sections)

    return render_template(
        'senkyo_sendgroup_text.html',
        sections=sections,
        total_line_count=total_line_count,
    )

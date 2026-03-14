from flask import render_template

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

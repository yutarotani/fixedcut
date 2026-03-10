#!/usr/bin/env python3
"""
DB初期化スクリプト。
テーブル作成後、m_jyochu_image_cnv の初期データ（Excel）を投入する。
"""

import sys

from fixedcut_app import app
from fixedcut_app import db
from create_m_jyochu_image_cnv_data import import_excel_data


def main() -> int:
    with app.app_context():
        db.create_all()
    print("✅ テーブル作成完了")

    if not import_excel_data():
        print("❌ m_jyochu_image_cnv のデータ投入に失敗しました")
        return 1

    print("✅ create_db.py の全処理が完了しました")
    return 0


if __name__ == "__main__":
    sys.exit(main())
#!/usr/bin/env python3
"""
DB初期化スクリプト。
テーブル作成後、m_jyochu_image_cnv の初期データ（Excel）を投入する。
"""

import sys
from sqlalchemy import inspect, text

from fixedcut_app import app
from fixedcut_app import db
from create_m_jyochu_image_cnv_data import import_excel_data
from fixedcut_app.models.fixedcut import FixedCut


def ensure_fixedcut_schema() -> None:
    table_name = FixedCut.__table__.name
    inspector = inspect(db.engine)
    table_names = set(inspector.get_table_names())

    if table_name not in table_names:
        # モデル定義と既存DBの差異を吸収するため、旧名テーブルも探索する。
        for legacy_name in ("fixedcut", "fixed_cut"):
            if legacy_name in table_names:
                table_name = legacy_name
                break

    if table_name not in table_names:
        print("⚠️ fixedcut系テーブルが見つからないためスキーマ更新をスキップしました")
        return

    existing_columns = {col["name"] for col in inspector.get_columns(table_name)}
    if "men_name" not in existing_columns:
        with db.engine.begin() as conn:
            conn.execute(text(f'ALTER TABLE "{table_name}" ADD COLUMN men_name VARCHAR(30)'))
        print(f"✅ {table_name}.men_name を追加しました")
    else:
        print(f"ℹ️ {table_name}.men_name は既に存在します")


def main() -> int:
    with app.app_context():
        db.create_all()
        ensure_fixedcut_schema()
    print("✅ テーブル作成完了")

    if not import_excel_data():
        print("❌ m_jyochu_image_cnv のデータ投入に失敗しました")
        return 1

    print("✅ create_db.py の全処理が完了しました")
    return 0


if __name__ == "__main__":
    sys.exit(main())
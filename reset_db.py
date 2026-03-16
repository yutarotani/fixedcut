#!/usr/bin/env python3
"""
DBリセットスクリプト。
全テーブルを削除(drop_all)し、最新モデル定義で再作成(create_all)する。

Usage:
  python reset_db.py --yes
  python reset_db.py --yes --with-initial-m-jyochu
"""

import argparse
import sys

from fixedcut_app import app, db


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Drop and recreate all database tables.")
    parser.add_argument(
        "--yes",
        action="store_true",
        help="確認プロンプトなしで実行します（必須フラグ）。",
    )
    parser.add_argument(
        "--with-initial-m-jyochu",
        action="store_true",
        help="再作成後に m_jyochu_image_cnv の初期データ投入(create_m_jyochu_image_cnv_data.py)を実行します。",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    if not args.yes:
        print("この処理はDBの全テーブルと全データを削除して再作成します。")
        print("実行するには --yes を付けてください。")
        return 1

    with app.app_context():
        db.drop_all()
        db.create_all()

    print("✅ 全テーブルの削除と再作成が完了しました")

    if args.with_initial_m_jyochu:
        from create_m_jyochu_image_cnv_data import import_excel_data

        ok = import_excel_data()
        if not ok:
            print("❌ m_jyochu_image_cnv の初期データ投入に失敗しました")
            return 1
        print("✅ m_jyochu_image_cnv の初期データ投入が完了しました")

    return 0


if __name__ == "__main__":
    sys.exit(main())

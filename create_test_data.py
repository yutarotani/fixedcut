#!/usr/bin/env python3
"""
テストデータ作成スクリプト
300件のテストデータをFixedCutテーブルに挿入します。
"""

import sys
import os
import random
import string

# Flaskアプリケーションのディレクトリに移動
sys.path.insert(0, os.path.dirname(__file__))

from fixedcut_app import app, db
from fixedcut_app.models.fixedcut import FixedCut

def create_test_data():
    """300件のテストデータを生成してDBに挿入"""

    with app.app_context():
        print("テストデータの作成を開始します...")

        # 既存データを確認
        existing_count = db.session.query(FixedCut).count()
        print(f"現在のレコード数: {existing_count}")

        # テストデータの生成
        test_data = []
        for i in range(1, 301):  # 1から300まで
            # ランダムなID生成（例: TEST001, TEST002, ...）
            test_id = f"TEST{i:03d}"

            # ランダムな見出し生成
            midashi = f"テスト見出し{i:03d}"

            # ランダムな文字列生成
            test_str = f"テスト一体化文字列{i:03d}"

            # ランダムなブール値
            gw_flg = random.choice([True, False])
            prod_flg = random.choice([True, False])
            ot_flg = random.choice([True, False])

            # コメント
            comment = f"テストコメント{i:03d}"

            test_data.append({
                'id': test_id,
                'midashi': midashi,
                'Str': test_str,
                'colorUrl': '',
                'monoUrl': '',
                'GWFlg': gw_flg,
                'prodFlg': prod_flg,
                'OTFlg': ot_flg,
                'comment': comment
            })

        # DBに一括挿入
        try:
            for data in test_data:
                fixedcut = FixedCut(**data)
                db.session.add(fixedcut)

            db.session.commit()
            print("✅ 300件のテストデータを正常に挿入しました！")

            # 挿入後の確認
            new_count = db.session.query(FixedCut).count()
            print(f"挿入後のレコード数: {new_count}")
            print(f"追加されたレコード数: {new_count - existing_count}")

        except Exception as e:
            db.session.rollback()
            print(f"❌ エラーが発生しました: {e}")
            return False

    return True

if __name__ == "__main__":
    success = create_test_data()
    if success:
        print("\n🎉 テストデータ作成完了！")
        print("ブラウザで /general にアクセスしてページング機能をテストしてください。")
    else:
        print("\n💥 テストデータ作成失敗")
        sys.exit(1)
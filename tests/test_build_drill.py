# -*- coding: utf-8 -*-
"""ドリルの型の回帰テスト（golden）: 全定義がテンプレートから実ファイルとバイト一致で再生成できること。
実行: リポ直下で  python tests/test_build_drill.py   （依存なし）
テンプレート・定義・生成済みドリルのどれかを触ったら必ず回す。
バイト一致＝挙動同一の保証。NG が出たら「定義かテンプレの反映漏れ」＝型の腐りをその場で直す。"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts"))
import build_drill

if __name__ == "__main__":
    sys.exit(0 if build_drill.check() else 1)

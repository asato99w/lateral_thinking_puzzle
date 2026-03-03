"""data_src.json → data.json 整形スクリプト

_ プレフィックスのフィールドを除去して data.json を出力する。
"""

import json
import sys
from pathlib import Path


def strip_underscore_fields(obj):
    """再帰的に _ プレフィックスのキーを除去する"""
    if isinstance(obj, dict):
        return {k: strip_underscore_fields(v) for k, v in obj.items() if not k.startswith("_")}
    elif isinstance(obj, list):
        return [strip_underscore_fields(item) for item in obj]
    return obj


def export(src_path: str) -> str:
    """data_src.json を読み込み、_ フィールドを除去した data.json を出力する。

    戻り値: 出力先パス
    """
    src = Path(src_path)
    with open(src, encoding="utf-8") as f:
        data = json.load(f)

    cleaned = strip_underscore_fields(data)

    dst = src.parent / "data.json"
    with open(dst, "w", encoding="utf-8") as f:
        json.dump(cleaned, f, ensure_ascii=False, indent=2)
        f.write("\n")

    return str(dst)


def main():
    if len(sys.argv) < 2:
        print("Usage: python export_data.py <data_src.json>", file=sys.stderr)
        sys.exit(2)

    src_path = sys.argv[1]
    if not Path(src_path).exists():
        print(f"Error: {src_path} が見つかりません", file=sys.stderr)
        sys.exit(2)

    dst = export(src_path)
    print(f"[export_data] {src_path} → {dst}")


if __name__ == "__main__":
    main()

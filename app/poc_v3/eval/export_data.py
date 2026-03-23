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

    # 命題に必須フィールドを補完（Swift Codable 互換）
    PROP_DEFAULTS = {
        "negation_of": None,
        "entailment_conditions": None,
        "formation_conditions": None,
        "rejection_conditions": None,
    }
    for prop in cleaned.get("propositions", []):
        for key, default in PROP_DEFAULTS.items():
            if key not in prop:
                prop[key] = default

    # data_src の短縮キーをエンジン互換に変換
    if "S" in cleaned and "statement" not in cleaned:
        cleaned["statement"] = cleaned.pop("S")
    if "T" in cleaned and "truth" not in cleaned:
        cleaned["truth"] = cleaned.pop("T")
    if "id" not in cleaned and "title" in cleaned:
        cleaned["id"] = cleaned["title"]

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

"""全チェック実行 (v3)

check_integrity → check_reachability の順に実行し、全体サマリーを出力する。
整合性が壊れている場合、到達可能性チェックの結果は信頼できないため順序に意味がある。

data_src.json の場合（_ フィールド検出で自動判別）:
  既存チェック + check_chain_consistency
data.json の場合:
  既存チェックのみ
"""

import json
import sys
from pathlib import Path

from check_integrity import run as run_integrity
from check_reachability import run as run_reachability
from check_chain_consistency import run as run_chain_consistency


def _has_underscore_fields(path: str) -> bool:
    """データファイルに _ プレフィックスフィールドが含まれるか判定"""
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    # トップレベルに _ フィールドがあるか
    for key in data:
        if key.startswith("_"):
            return True
    # descriptors や pieces 内に _ フィールドがあるか
    for d in data.get("descriptors", []):
        if any(k.startswith("_") for k in d):
            return True
    for p in data.get("pieces", []):
        if any(k.startswith("_") for k in p):
            return True
    return False


def main():
    if len(sys.argv) < 2:
        print("Usage: python run_all.py <data.json|data_src.json>", file=sys.stderr)
        sys.exit(2)

    path = sys.argv[1]
    if not Path(path).exists():
        print(f"Error: {path} が見つかりません", file=sys.stderr)
        sys.exit(2)

    is_src = _has_underscore_fields(path)
    mode = "data_src" if is_src else "data"
    print(f"=== eval: {path} (mode: {mode}) ===\n")

    results: list[tuple[str, bool]] = []

    print("[check_integrity]")
    ok_integrity, _ = run_integrity(path)
    results.append(("check_integrity", ok_integrity))
    print()

    if not ok_integrity:
        print("[check_reachability] SKIP（整合性エラーのため）")
        results.append(("check_reachability", False))
    else:
        print("[check_reachability]")
        ok_reach, _ = run_reachability(path)
        results.append(("check_reachability", ok_reach))
    print()

    # data_src.json の場合、追加チェック
    if is_src and ok_integrity:
        print("[check_chain_consistency]")
        ok_chain, _ = run_chain_consistency(path)
        results.append(("check_chain_consistency", ok_chain))
        print()

    print("=== summary ===")
    all_pass = True
    for name, ok in results:
        status = "PASS" if ok else "FAIL"
        print(f"  {name}: {status}")
        if not ok:
            all_pass = False

    print()
    if all_pass:
        print("Result: ALL PASS")
    else:
        print("Result: FAIL")

    sys.exit(0 if all_pass else 1)


if __name__ == "__main__":
    main()

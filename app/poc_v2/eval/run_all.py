"""全チェック実行

check_integrity → check_reachability の順に実行し、全体サマリーを出力する。
整合性が壊れている場合、到達可能性チェックの結果は信頼できないため順序に意味がある。
"""

import sys
from pathlib import Path

from check_integrity import run as run_integrity
from check_reachability import run as run_reachability


def main():
    if len(sys.argv) < 2:
        print("Usage: python run_all.py <data.json>", file=sys.stderr)
        sys.exit(2)

    path = sys.argv[1]
    if not Path(path).exists():
        print(f"Error: {path} が見つかりません", file=sys.stderr)
        sys.exit(2)

    print(f"=== eval: {path} ===\n")

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

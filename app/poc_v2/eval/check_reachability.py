"""到達可能性チェック

initial_facts 以外の全事実が question の reveals 経由で到達可能かを検証する。
"""

import json
import sys
from pathlib import Path


def load_data(path: str) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def check_truth_fact_reachability(data: dict) -> list[str]:
    """initial_facts に含まれない全事実が、いずれかの question の reveals に含まれるか。"""
    errors = []
    initial = set(data.get("initial_facts", []))
    revealed: set[str] = set()
    for q in data.get("questions", []):
        revealed.update(q.get("reveals", []))

    for f in data.get("facts", []):
        fid = f["id"]
        if fid not in initial and fid not in revealed:
            errors.append(f"事実 '{fid}' ({f.get('label', '')}) が到達不能（initial_facts にも reveals にも含まれない）")
    return errors


def check_piece_fact_reachability(data: dict) -> list[str]:
    """各ピースの facts が全て到達可能か。"""
    errors = []
    initial = set(data.get("initial_facts", []))
    revealed: set[str] = set()
    for q in data.get("questions", []):
        revealed.update(q.get("reveals", []))
    reachable = initial | revealed

    for piece in data.get("pieces", []):
        pid = piece["id"]
        for fref in piece.get("facts", []):
            if fref not in reachable:
                errors.append(f"piece '{pid}' の構成事実 '{fref}' が到達不能")
    return errors


def check_orphan_facts(data: dict) -> list[str]:
    """孤立事実の検出。"""
    warnings = []
    initial = set(data.get("initial_facts", []))
    revealed: set[str] = set()
    for q in data.get("questions", []):
        revealed.update(q.get("reveals", []))

    for f in data.get("facts", []):
        fid = f["id"]
        if fid not in initial and fid not in revealed:
            warnings.append(f"孤立事実: '{fid}' ({f.get('label', '')})")
    return warnings


def run(path: str) -> tuple[bool, list[str]]:
    data = load_data(path)
    checks = [
        ("T 事実の到達可能性", check_truth_fact_reachability),
        ("ピース構成事実の到達可能性", check_piece_fact_reachability),
        ("孤立事実の検出", check_orphan_facts),
    ]

    all_errors: list[str] = []
    for label, fn in checks:
        errors = fn(data)
        if errors:
            print(f"  FAIL: {label}")
            for e in errors:
                print(f"    - {e}")
            all_errors.extend(errors)
        else:
            print(f"  PASS: {label}")

    return len(all_errors) == 0, all_errors


def main():
    if len(sys.argv) < 2:
        print("Usage: python check_reachability.py <data.json>", file=sys.stderr)
        sys.exit(2)

    path = sys.argv[1]
    if not Path(path).exists():
        print(f"Error: {path} が見つかりません", file=sys.stderr)
        sys.exit(2)

    print("[check_reachability]")
    ok, _ = run(path)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()

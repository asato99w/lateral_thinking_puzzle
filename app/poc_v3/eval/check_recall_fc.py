"""recall = fc 整合性チェック (v3)

各質問の recall_conditions が reveals される命題の formation_conditions と一致するかを検証する。
data_src.json 専用。

recall_conditions が質問に存在しない場合（rc 廃止後の形式）はチェックをスキップする。
"""

from __future__ import annotations

import json
import sys
from pathlib import Path


def load_data(path: str) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _get_reveals(q: dict) -> list[str]:
    """reveals を文字列・リスト両対応でリストとして返す"""
    r = q.get("reveals", [])
    if isinstance(r, str):
        return [r] if r else []
    return r


def _normalize_conditions(conditions: list[list[str]] | None) -> list[list[str]]:
    """条件を正規化する（ソートして比較可能にする）"""
    if conditions is None:
        return []
    return sorted([sorted(group) for group in conditions])


def check_recall_equals_fc(data: dict) -> list[str]:
    """各質問の recall_conditions が reveals される命題の fc と一致するか。

    recall_conditions が質問に存在しない場合（rc 廃止後）は全スキップ。
    """
    errors = []
    descriptors = data.get("propositions", data.get("descriptors", []))
    descriptor_map = {d["id"]: d for d in descriptors}

    # rc 廃止後: いずれかの質問に recall_conditions がなければスキップ
    questions = data.get("questions", [])
    has_rc = any("recall_conditions" in q for q in questions)
    if not has_rc:
        return errors

    for q in questions:
        qid = q["id"]
        recall = q.get("recall_conditions", [])
        reveals = _get_reveals(q)

        if not reveals:
            continue

        if not recall:
            continue

        # reveals される命題の fc と比較
        for rev_id in reveals:
            d = descriptor_map.get(rev_id)
            if d is None:
                continue
            fc = d.get("formation_conditions")

            # fc が None（基礎命題）の場合、recall は空であるべき
            expected = _normalize_conditions(fc)
            actual = _normalize_conditions(recall)

            if expected != actual:
                fc_str = fc if fc else "[]"
                recall_str = recall if recall else "[]"
                errors.append(
                    f"question '{qid}': recall_conditions と "
                    f"reveals '{rev_id}' の formation_conditions が不一致\n"
                    f"      recall: {recall_str}\n"
                    f"      fc:     {fc_str}"
                )
            # 最初の reveals 命題のみチェック（v3 では 1 質問 1 主命題が基本）
            break

    return errors


def run(path: str) -> tuple[bool, list[str]]:
    data = load_data(path)

    checks = [
        ("recall = fc 整合性", check_recall_equals_fc),
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
        print("Usage: python check_recall_fc.py <data_src.json>", file=sys.stderr)
        sys.exit(2)

    path = sys.argv[1]
    if not Path(path).exists():
        print(f"Error: {path} が見つかりません", file=sys.stderr)
        sys.exit(2)

    print("[check_recall_fc]")
    ok, _ = run(path)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()

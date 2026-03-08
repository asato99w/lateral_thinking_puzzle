"""戦術連鎖の整合性チェック

_tactical_chains / _piece_chains と questions の整合性を検証する。
data_src.json 専用（_ プレフィックスフィールドが必要）。
"""

from __future__ import annotations

import json
import sys
from pathlib import Path


def load_data(path: str) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def check_chain_question_coverage(data: dict) -> list[str]:
    """全連鎖ステップに対応する質問が存在するか"""
    errors = []
    question_ids = {q["id"] for q in data.get("questions", [])}

    for chain in data.get("_piece_chains", []):
        chain_id = chain.get("id", "?")
        for i, step in enumerate(chain.get("steps", [])):
            step_questions = step.get("questions", [])
            for qid in step_questions:
                if qid not in question_ids:
                    errors.append(f"_piece_chains '{chain_id}' step[{i}] の質問 '{qid}' が questions に存在しない")

    for chain in data.get("_tactical_chains", []):
        chain_id = chain.get("id", "?")
        for i, step in enumerate(chain.get("steps", [])):
            step_questions = step.get("questions", [])
            for qid in step_questions:
                if qid not in question_ids:
                    errors.append(f"_tactical_chains '{chain_id}' step[{i}] の質問 '{qid}' が questions に存在しない")

    return errors


def check_output_coverage(data: dict) -> list[str]:
    """ステップの output が質問群の reveals 合集合で全カバーされるか"""
    errors = []
    question_map = {q["id"]: q for q in data.get("questions", [])}

    for chain in data.get("_piece_chains", []):
        chain_id = chain.get("id", "?")
        for i, step in enumerate(chain.get("steps", [])):
            outputs = set(step.get("output", []))
            if not outputs:
                continue
            # 質問群の reveals を合集合にする
            collective_reveals: set[str] = set()
            for qid in step.get("questions", []):
                q = question_map.get(qid)
                if q is None:
                    continue
                collective_reveals.update(q.get("reveals", []))
            uncovered = outputs - collective_reveals
            if uncovered:
                errors.append(
                    f"_piece_chains '{chain_id}' step[{i}]: "
                    f"output のうち質問群が reveals しない命題がある: {sorted(uncovered)}"
                )

    return errors


def check_reveals_scope(data: dict) -> list[str]:
    """質問が reveals する命題がステップの output 範囲内か"""
    errors = []
    question_map = {q["id"]: q for q in data.get("questions", [])}

    for chain in data.get("_piece_chains", []):
        chain_id = chain.get("id", "?")
        for i, step in enumerate(chain.get("steps", [])):
            outputs = set(step.get("output", []))
            for qid in step.get("questions", []):
                q = question_map.get(qid)
                if q is None:
                    continue
                reveals = set(q.get("reveals", []))
                overflow = reveals - outputs
                if overflow:
                    errors.append(
                        f"_piece_chains '{chain_id}' step[{i}]: "
                        f"質問 '{qid}' が output 外の命題を reveals: {sorted(overflow)}"
                    )

    return errors


def _derivable_from(
    available: set[str],
    formation_conditions: dict[str, list[list[str]]],
    entailment_conditions: dict[str, list[list[str]]],
    rejection_conditions: dict[str, list[list[str]]] | None = None,
) -> set[str]:
    """available から v3 の 2 段階導出で到達可能な命題を返す。

    1. 論理的導出（entailment）: confirmed → confirmed の不動点計算
    2. 仮説導出（formation）: confirmed → derived の 1 回パス
    """
    # Step 1: 論理的導出（不動点計算）
    confirmed = set(available)
    changed = True
    while changed:
        changed = False
        for did, conditions in entailment_conditions.items():
            if did in confirmed:
                continue
            for cond_group in conditions:
                if all(ref in confirmed for ref in cond_group):
                    confirmed.add(did)
                    changed = True
                    break

    # Step 2: 棄却集合の計算
    rejected = set()
    if rejection_conditions:
        for did, conditions in rejection_conditions.items():
            if any(all(c in confirmed for c in group) for group in conditions):
                rejected.add(did)

    # Step 3: 仮説導出（1 回パス）
    derived = set()
    for did, conditions in formation_conditions.items():
        if did in confirmed or did in rejected:
            continue
        for cond_group in conditions:
            if all(ref in confirmed for ref in cond_group):
                derived.add(did)
                break

    return (confirmed | derived) - available


def check_recall_derivability(data: dict) -> list[str]:
    """recall_conditions が対応ステップの input から導出可能か"""
    errors = []
    question_map = {q["id"]: q for q in data.get("questions", [])}

    # 導出条件の収集
    formation_conditions: dict[str, list[list[str]]] = {}
    entailment_conditions: dict[str, list[list[str]]] = {}
    rejection_conditions: dict[str, list[list[str]]] = {}
    for d in data.get("descriptors", []):
        if "formation_conditions" in d:
            formation_conditions[d["id"]] = d["formation_conditions"]
        if "entailment_conditions" in d:
            entailment_conditions[d["id"]] = d["entailment_conditions"]
        if "rejection_conditions" in d:
            rejection_conditions[d["id"]] = d["rejection_conditions"]

    for chain in data.get("_piece_chains", []):
        chain_id = chain.get("id", "?")
        # 累積 input: 前のステップの output も利用可能
        cumulative_available: set[str] = set()
        for i, step in enumerate(chain.get("steps", [])):
            step_input = set(step.get("input", []))
            cumulative_available.update(step_input)

            # cumulative_available から導出可能な命題を計算（v3 の 2 段階導出）
            derivable = _derivable_from(cumulative_available, formation_conditions, entailment_conditions, rejection_conditions or None)
            reachable = cumulative_available | derivable

            for qid in step.get("questions", []):
                q = question_map.get(qid)
                if q is None:
                    continue
                for j, cond_group in enumerate(q.get("recall_conditions", [])):
                    for ref in cond_group:
                        if ref not in reachable:
                            errors.append(
                                f"_piece_chains '{chain_id}' step[{i}]: "
                                f"質問 '{qid}' の recall_conditions[{j}] の '{ref}' が "
                                f"ステップ input から導出不可能"
                            )

            # output を次のステップで利用可能に
            cumulative_available.update(step.get("output", []))

    return errors


def check_reveals_piece_membership(data: dict) -> list[str]:
    """reveals する命題のピース帰属が正しいか"""
    errors = []
    question_map = {q["id"]: q for q in data.get("questions", [])}

    # descriptor → piece mapping
    descriptor_to_piece: dict[str, str] = {}
    for piece in data.get("pieces", []):
        for mid in piece.get("members", []):
            descriptor_to_piece[mid] = piece["id"]

    for chain in data.get("_piece_chains", []):
        chain_id = chain.get("id", "?")
        expected_piece = chain.get("piece_id")
        if expected_piece is None:
            continue

        for i, step in enumerate(chain.get("steps", [])):
            for qid in step.get("questions", []):
                q = question_map.get(qid)
                if q is None:
                    continue
                for rev_id in q.get("reveals", []):
                    actual_piece = descriptor_to_piece.get(rev_id)
                    if actual_piece is not None and actual_piece != expected_piece:
                        errors.append(
                            f"_piece_chains '{chain_id}' step[{i}]: "
                            f"質問 '{qid}' が reveals する '{rev_id}' は "
                            f"ピース '{actual_piece}' に帰属（期待: '{expected_piece}'）"
                        )

    return errors


def run(path: str) -> tuple[bool, list[str]]:
    data = load_data(path)

    # _piece_chains も _tactical_chains もなければスキップ
    has_chains = "_piece_chains" in data or "_tactical_chains" in data
    if not has_chains:
        print("  SKIP: 連鎖メタ情報なし")
        return True, []

    checks = [
        ("連鎖ステップの質問存在", check_chain_question_coverage),
        ("output の網羅性", check_output_coverage),
        ("reveals のステップ範囲", check_reveals_scope),
        ("recall_conditions の導出可能性", check_recall_derivability),
        ("reveals のピース帰属", check_reveals_piece_membership),
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
        print("Usage: python check_chain_consistency.py <data_src.json>", file=sys.stderr)
        sys.exit(2)

    path = sys.argv[1]
    if not Path(path).exists():
        print(f"Error: {path} が見つかりません", file=sys.stderr)
        sys.exit(2)

    print("[check_chain_consistency]")
    ok, _ = run(path)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()

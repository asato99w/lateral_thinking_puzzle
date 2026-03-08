"""戦術連鎖の整合性チェック

_tactical_chains / _piece_chains と questions の整合性を検証する。
data_src.json 専用（_ プレフィックスフィールドが必要）。
"""

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
                    f"output のうち質問群が reveals しない記述素がある: {sorted(uncovered)}"
                )

    return errors


def check_reveals_scope(data: dict) -> list[str]:
    """質問が reveals する記述素がステップの output 範囲内か"""
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
                        f"質問 '{qid}' が output 外の記述素を reveals: {sorted(overflow)}"
                    )

    return errors


def _derivable_from(available: set[str], derived_conditions: dict[str, list[list[str]]]) -> set[str]:
    """available から不動点計算で導出可能な記述素を返す"""
    derived = set(available)
    changed = True
    while changed:
        changed = False
        for did, conditions in derived_conditions.items():
            if did in derived:
                continue
            for cond_group in conditions:
                if all(ref in derived for ref in cond_group):
                    derived.add(did)
                    changed = True
                    break
    return derived - available


def check_recall_derivability(data: dict) -> list[str]:
    """recall_conditions が対応ステップの input から導出可能か（OR-of-AND 意味論）

    少なくとも1つの recall グループが全要素 reachable であれば OK。
    """
    errors = []
    question_map = {q["id"]: q for q in data.get("questions", [])}
    initial = set(data.get("initial_confirmed", []))

    # 導出記述素の formation_conditions + entailment_conditions
    derived_conditions: dict[str, list[list[str]]] = {}
    for d in data.get("descriptors", []):
        conds = d.get("formation_conditions", []) + d.get("entailment_conditions", [])
        if conds:
            derived_conditions[d["id"]] = conds

    for chain in data.get("_piece_chains", []):
        chain_id = chain.get("id", "?")
        # 累積 input: initial_confirmed + 前のステップの output も利用可能
        cumulative_available: set[str] = set(initial)
        for i, step in enumerate(chain.get("steps", [])):
            step_input = set(step.get("input", []))
            cumulative_available.update(step_input)

            # cumulative_available から導出可能な記述素を計算
            derivable = _derivable_from(cumulative_available, derived_conditions)
            reachable = cumulative_available | derivable

            for qid in step.get("questions", []):
                q = question_map.get(qid)
                if q is None:
                    continue
                recall = q.get("recall_conditions", [])
                if not recall:
                    continue
                # OR-of-AND: 少なくとも1つのグループが全要素 reachable
                has_valid_group = any(
                    all(ref in reachable for ref in cond_group)
                    for cond_group in recall
                )
                if not has_valid_group:
                    errors.append(
                        f"_piece_chains '{chain_id}' step[{i}]: "
                        f"質問 '{qid}' の recall_conditions のいずれのグループも "
                        f"ステップ累積 input から充足不可能"
                    )

            # output を次のステップで利用可能に
            cumulative_available.update(step.get("output", []))

    return errors


def check_reveals_piece_membership(data: dict) -> list[str]:
    """reveals する記述素のピース帰属が正しいか"""
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

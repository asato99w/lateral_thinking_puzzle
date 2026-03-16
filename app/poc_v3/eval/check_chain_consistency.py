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


def _get_reveals(q: dict) -> list[str]:
    """reveals を文字列・リスト両対応でリストとして返す"""
    r = q.get("reveals", [])
    if isinstance(r, str):
        return [r] if r else []
    return r


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
                collective_reveals.update(_get_reveals(q))
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
                reveals = set(_get_reveals(q))
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


def _get_availability_fc(q: dict, descriptor_map: dict) -> list[list[str]] | None:
    """質問の利用可能条件を返す。

    - 回答が「はい」→ reveals 先の命題の fc
    - 回答が「いいえ」→ reveals 先の命題の negation_of が指す命題の fc
    """
    reveals = _get_reveals(q)
    if not reveals:
        return None
    d = descriptor_map.get(reveals[0])
    if d is None:
        return None
    if q.get("answer") == "いいえ":
        neg = d.get("negation_of")
        if neg is not None:
            target = descriptor_map.get(neg)
            if target is not None:
                return target.get("formation_conditions")
    return d.get("formation_conditions")


def check_availability_derivability(data: dict) -> list[str]:
    """質問の利用可能条件が対応ステップの input から導出可能か。

    利用可能条件は OR-of-AND なので、少なくとも1つのグループが
    完全にステップの累積入力から導出可能であれば OK。
    cumulative_available のベースラインには initial_confirmed を含める。
    """
    errors = []
    question_map = {q["id"]: q for q in data.get("questions", [])}
    initial = set(data.get("initial_confirmed", []))

    # 命題マップの構築（v2: descriptors, v3: propositions）
    descriptors = data.get("propositions", data.get("descriptors", []))
    descriptor_map = {d["id"]: d for d in descriptors}

    # 導出条件の収集
    formation_conditions: dict[str, list[list[str]]] = {}
    entailment_conditions: dict[str, list[list[str]]] = {}
    rejection_conditions: dict[str, list[list[str]]] = {}
    for d in descriptors:
        if "formation_conditions" in d:
            formation_conditions[d["id"]] = d["formation_conditions"]
        if "entailment_conditions" in d:
            entailment_conditions[d["id"]] = d["entailment_conditions"]
        if "rejection_conditions" in d:
            rejection_conditions[d["id"]] = d["rejection_conditions"]

    for chain in data.get("_piece_chains", []):
        chain_id = chain.get("id", "?")
        # 累積 input: initial_confirmed + 前のステップの output も利用可能
        cumulative_available: set[str] = set(initial)
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
                fc = _get_availability_fc(q, descriptor_map)
                if not fc:
                    continue
                # OR-of-AND: 少なくとも1つのグループが全て reachable なら OK
                has_valid_group = any(
                    all(ref in reachable for ref in cond_group)
                    for cond_group in fc
                )
                if not has_valid_group:
                    out_of_scope = []
                    for j, cond_group in enumerate(fc):
                        unreachable = [ref for ref in cond_group if ref not in reachable]
                        if unreachable:
                            out_of_scope.append(f"[{j}]: {unreachable}")
                    errors.append(
                        f"_piece_chains '{chain_id}' step[{i}]: "
                        f"質問 '{qid}' の利用可能条件にステップ input から "
                        f"導出可能なグループがない（{', '.join(out_of_scope)}）"
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
                for rev_id in _get_reveals(q):
                    actual_piece = descriptor_to_piece.get(rev_id)
                    if actual_piece is not None and actual_piece != expected_piece:
                        errors.append(
                            f"_piece_chains '{chain_id}' step[{i}]: "
                            f"質問 '{qid}' が reveals する '{rev_id}' は "
                            f"ピース '{actual_piece}' に帰属（期待: '{expected_piece}'）"
                        )

    return errors


def check_fc_chain_consistency(data: dict) -> list[str]:
    """_phase4.tactical_chains の連鎖構造と propositions の fc が整合するか。

    連鎖 source → intermediates → target において:
    - target の fc は最後の intermediate を参照すべき
    - 各 intermediate の fc は前段（source または前の intermediate）を参照すべき
    fc が source を直接参照し intermediate をスキップしている場合、
    連鎖が段階的オープンとして機能しない。
    """
    errors = []
    phase4 = data.get("_phase4", {})
    chains = phase4.get("tactical_chains", [])
    if not chains:
        return []

    # 命題マップ
    props = {p["id"]: p for p in data.get("propositions", [])}
    initial = set(data.get("initial_confirmed", []))

    for chain in chains:
        cid = chain.get("id", "?")
        source = chain.get("source", [])
        intermediates = chain.get("intermediates", [])
        target = chain.get("target", "")

        if not intermediates:
            errors.append(f"連鎖 '{cid}': intermediates が空（中間命題なし）")
            continue

        # 連鎖のステップ列を構築: source → intermediates[0] → ... → intermediates[-1] → target
        steps = intermediates + [target]

        for i, step_id in enumerate(steps):
            prop = props.get(step_id)
            if prop is None:
                errors.append(f"連鎖 '{cid}': ステップ '{step_id}' が propositions に存在しない")
                continue

            fc = prop.get("formation_conditions")
            if fc is None:
                errors.append(f"連鎖 '{cid}': '{step_id}' に formation_conditions がない")
                continue

            # 前段の命題を特定
            if i == 0:
                # 最初の intermediate: 前段は source
                expected_predecessors = set(source)
                predecessor_label = f"source {source}"
            else:
                # 後続: 前段は直前の intermediate
                prev_id = steps[i - 1]
                expected_predecessors = {prev_id}
                predecessor_label = f"前段 '{prev_id}'"

            # fc のいずれかの AND グループが前段を参照しているか
            refs_predecessor = False
            all_fc_refs: set[str] = set()
            for and_group in fc:
                all_fc_refs.update(and_group)
                if expected_predecessors & set(and_group):
                    refs_predecessor = True

            if not refs_predecessor:
                # 前段をスキップしている
                # source のみ参照（intermediate をスキップ）のケースを特定
                source_set = set(source)
                refs_only_source = all_fc_refs and all_fc_refs <= (source_set | initial)
                if i > 0 and refs_only_source:
                    errors.append(
                        f"連鎖 '{cid}': '{step_id}' の fc={fc} が "
                        f"{predecessor_label} をスキップし source を直接参照 "
                        f"→ 段階的オープンが機能しない"
                    )
                elif i > 0:
                    errors.append(
                        f"連鎖 '{cid}': '{step_id}' の fc={fc} が "
                        f"{predecessor_label} を参照していない"
                    )
                else:
                    # 最初の intermediate が source を参照していない
                    # source が全て initial_confirmed なら fc は initial のみでも可
                    if not (source_set <= initial and all_fc_refs <= initial):
                        errors.append(
                            f"連鎖 '{cid}': '{step_id}' の fc={fc} が "
                            f"{predecessor_label} を参照していない"
                        )

    return errors


def run(path: str) -> tuple[bool, list[str]]:
    data = load_data(path)

    # _piece_chains も _tactical_chains もなければスキップ
    has_chains = "_piece_chains" in data or "_tactical_chains" in data
    has_phase4 = "_phase4" in data and "tactical_chains" in data.get("_phase4", {})
    if not has_chains and not has_phase4:
        print("  SKIP: 連鎖メタ情報なし")
        return True, []

    checks = [
        ("連鎖ステップの質問存在", check_chain_question_coverage),
        ("output の網羅性", check_output_coverage),
        ("reveals のステップ範囲", check_reveals_scope),
        ("利用可能条件の導出可能性", check_availability_derivability),
        ("reveals のピース帰属", check_reveals_piece_membership),
        ("連鎖構造と fc の整合性", check_fc_chain_consistency),
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

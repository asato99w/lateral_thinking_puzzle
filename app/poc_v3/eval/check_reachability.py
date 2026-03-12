"""到達可能性チェック

initial_confirmed 以外の全命題が question の reveals 経由で到達可能かを検証する。
v2（descriptors, pieces）と v3（propositions）の両形式に対応。
"""

from __future__ import annotations

import json
import sys
from pathlib import Path


def load_data(path: str) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _is_v3(data: dict) -> bool:
    return "propositions" in data


def _get_descriptors(data: dict) -> list[dict]:
    return data.get("propositions", data.get("descriptors", []))


def _get_reveals(q: dict) -> list[str]:
    """reveals を文字列・リスト両対応でリストとして返す"""
    r = q.get("reveals", [])
    if isinstance(r, str):
        return [r] if r else []
    return r


def _is_base(d: dict) -> bool:
    """基礎命題かどうか（formation_conditions も entailment_conditions も持たない）"""
    return "formation_conditions" not in d and "entailment_conditions" not in d


def _has_formation(d: dict) -> bool:
    return "formation_conditions" in d


def _has_entailment(d: dict) -> bool:
    return "entailment_conditions" in d


def check_base_descriptor_reachability(data: dict) -> list[str]:
    """initial_confirmed に含まれない全基礎命題が、いずれかの question の reveals に含まれるか。"""
    errors = []
    initial = set(data.get("initial_confirmed", []))
    revealed: set[str] = set()
    for q in data.get("questions", []):
        revealed.update(_get_reveals(q))

    for d in _get_descriptors(data):
        if not _is_base(d):
            continue
        did = d["id"]
        if did not in initial and did not in revealed:
            errors.append(f"基礎命題 '{did}' ({d.get('label', '')}) が到達不能（initial_confirmed にも reveals にも含まれない）")
    return errors


def _derivable_descriptors(
    allowed_confirmed: set[str],
    formation_conditions: dict[str, list[list[str]]],
    entailment_conditions: dict[str, list[list[str]]],
    rejection_conditions: dict[str, list[list[str]]] | None = None,
) -> set[str]:
    """allowed_confirmed から到達可能な全命題を求める。"""
    # Step 1: 論理的導出（不動点計算）
    confirmed = set(allowed_confirmed)
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

    return (confirmed | derived) - allowed_confirmed


def check_proposition_reachability(data: dict) -> list[str]:
    """v3: 全 propositions が reveals または導出で到達可能か"""
    errors = []
    initial = set(data.get("initial_confirmed", []))
    revealed: set[str] = set()
    for q in data.get("questions", []):
        revealed.update(_get_reveals(q))

    descriptors = _get_descriptors(data)
    formation_conds = {d["id"]: d["formation_conditions"] for d in descriptors if _has_formation(d)}
    entailment_conds = {d["id"]: d["entailment_conditions"] for d in descriptors if _has_entailment(d)}
    rejection_conds: dict[str, list[list[str]]] = {}
    for d in descriptors:
        rc = d.get("rejection_conditions")
        if rc is not None:
            rejection_conds[d["id"]] = rc

    derivable = _derivable_descriptors(initial | revealed, formation_conds, entailment_conds, rejection_conds or None)
    reachable = initial | revealed | derivable

    for d in descriptors:
        did = d["id"]
        if did not in reachable:
            errors.append(f"命題 '{did}' ({d.get('label', '')}) が到達不能")
    return errors


def check_piece_member_reachability(data: dict) -> list[str]:
    """v2: 各ピースの members が全て到達可能か。"""
    if _is_v3(data):
        return []
    errors = []
    initial = set(data.get("initial_confirmed", []))
    revealed: set[str] = set()
    for q in data.get("questions", []):
        revealed.update(_get_reveals(q))

    descriptors = _get_descriptors(data)
    formation_conds = {d["id"]: d["formation_conditions"] for d in descriptors if _has_formation(d)}
    entailment_conds = {d["id"]: d["entailment_conditions"] for d in descriptors if _has_entailment(d)}
    rejection_conds: dict[str, list[list[str]]] = {}
    for d in descriptors:
        rc = d.get("rejection_conditions")
        if rc is not None:
            rejection_conds[d["id"]] = rc

    derivable = _derivable_descriptors(initial | revealed, formation_conds, entailment_conds, rejection_conds or None)
    reachable = initial | revealed | derivable

    for piece in data.get("pieces", []):
        pid = piece["id"]
        for mref in piece.get("members", []):
            if mref not in reachable:
                errors.append(f"piece '{pid}' の構成命題 '{mref}' が到達不能")
    return errors


def _transitive_deps(pid: str, piece_deps: dict[str, set[str]]) -> set[str]:
    visited: set[str] = set()
    stack = list(piece_deps.get(pid, set()))
    while stack:
        dep = stack.pop()
        if dep not in visited:
            visited.add(dep)
            stack.extend(piece_deps.get(dep, set()) - visited)
    return visited


def check_recall_scope(data: dict) -> list[str]:
    """v2: 各ピースの想起スコープの検証。"""
    if _is_v3(data):
        return []
    errors = []
    initial = set(data.get("initial_confirmed", []))

    descriptor_to_piece: dict[str, str] = {}
    for piece in data.get("pieces", []):
        for mid in piece.get("members", []):
            descriptor_to_piece[mid] = piece["id"]

    piece_deps = {p["id"]: set(p.get("depends_on", [])) for p in data.get("pieces", [])}
    piece_members: dict[str, set[str]] = {}
    for p in data.get("pieces", []):
        ids = set(p.get("members", []))
        for group in p.get("trigger", []):
            ids.update(group)
        piece_members[p["id"]] = ids

    reveals_map: dict[str, list[dict]] = {}
    for q in data.get("questions", []):
        for did in _get_reveals(q):
            reveals_map.setdefault(did, []).append(q)

    descriptors = _get_descriptors(data)
    formation_conds = {d["id"]: d["formation_conditions"] for d in descriptors if _has_formation(d)}
    entailment_conds = {d["id"]: d["entailment_conditions"] for d in descriptors if _has_entailment(d)}
    rejection_conds: dict[str, list[list[str]]] = {}
    for d in descriptors:
        rc = d.get("rejection_conditions")
        if rc is not None:
            rejection_conds[d["id"]] = rc

    for piece in data.get("pieces", []):
        pid = piece["id"]
        deps = _transitive_deps(pid, piece_deps)

        allowed_confirmed = set(initial)
        allowed_confirmed.update(piece_members.get(pid, set()))
        for dep_pid in deps:
            allowed_confirmed.update(piece_members.get(dep_pid, set()))

        derivable = _derivable_descriptors(allowed_confirmed, formation_conds, entailment_conds, rejection_conds or None)
        allowed = allowed_confirmed | derivable

        for mid in piece.get("members", []):
            for q in reveals_map.get(mid, []):
                qid = q["id"]
                # recall_conditions があればそれを使用、なければ reveals 先の fc
                recall = q.get("recall_conditions")
                if recall is None:
                    reveals = _get_reveals(q)
                    if reveals:
                        d_lookup = {dd["id"]: dd for dd in descriptors}
                        dd = d_lookup.get(reveals[0])
                        if dd is not None:
                            recall = dd.get("formation_conditions")
                if not recall:
                    continue
                has_valid_group = any(
                    all(ref in allowed for ref in cond_group)
                    for cond_group in recall
                )
                if not has_valid_group:
                    out_of_scope = []
                    for i, cond_group in enumerate(recall):
                        for ref in cond_group:
                            if ref not in allowed:
                                out_of_scope.append(f"[{i}]:'{ref}'")
                    errors.append(
                        f"ピース '{pid}': question '{qid}' の "
                        f"recall_conditions にスコープ内のグループがない（スコープ外: {', '.join(out_of_scope)}）"
                    )
    return errors


def check_orphan_descriptors(data: dict) -> list[str]:
    """孤立基礎命題の検出。"""
    warnings = []
    initial = set(data.get("initial_confirmed", []))
    revealed: set[str] = set()
    for q in data.get("questions", []):
        revealed.update(_get_reveals(q))

    for d in _get_descriptors(data):
        if not _is_base(d):
            continue
        did = d["id"]
        if did not in initial and did not in revealed:
            warnings.append(f"孤立命題: '{did}' ({d.get('label', '')})")
    return warnings


def check_recall_reachability_v3(data: dict) -> list[str]:
    """v3: 各質問の想起条件（reveals 先の fc）が initial_confirmed + 先行 reveals から到達可能か。

    recall_conditions は reveals される命題の formation_conditions から導出される。
    質問に recall_conditions フィールドがある場合（v2 互換）はそちらを使用する。
    """
    errors = []
    initial = set(data.get("initial_confirmed", []))
    descriptors = _get_descriptors(data)
    descriptor_map = {d["id"]: d for d in descriptors}
    formation_conds = {d["id"]: d["formation_conditions"] for d in descriptors if _has_formation(d)}
    entailment_conds = {d["id"]: d["entailment_conditions"] for d in descriptors if _has_entailment(d)}
    rejection_conds: dict[str, list[list[str]]] = {}
    for d in descriptors:
        rc = d.get("rejection_conditions")
        if rc is not None:
            rejection_conds[d["id"]] = rc

    # 全 reveals を集めた confirmed で最大到達可能集合を求める
    all_reveals: set[str] = set()
    for q in data.get("questions", []):
        all_reveals.update(_get_reveals(q))

    max_confirmed = initial | all_reveals
    derivable = _derivable_descriptors(max_confirmed, formation_conds, entailment_conds, rejection_conds or None)
    reachable = max_confirmed | derivable

    for q in data.get("questions", []):
        qid = q["id"]
        # recall_conditions があればそれを使用、なければ reveals 先の fc を使用
        recall = q.get("recall_conditions")
        if recall is None:
            reveals = _get_reveals(q)
            if reveals:
                d = descriptor_map.get(reveals[0])
                if d is not None:
                    recall = d.get("formation_conditions")
        if not recall:
            continue
        has_valid_group = any(
            all(ref in reachable for ref in cond_group)
            for cond_group in recall
        )
        if not has_valid_group:
            out_of_scope = []
            for i, cond_group in enumerate(recall):
                unreachable = [ref for ref in cond_group if ref not in reachable]
                if unreachable:
                    out_of_scope.append(f"[{i}]: {unreachable}")
            errors.append(
                f"question '{qid}' の想起条件（reveals 先の fc）が到達不能: {', '.join(out_of_scope)}"
            )
    return errors


def run(path: str) -> tuple[bool, list[str]]:
    data = load_data(path)
    is_v3 = _is_v3(data)

    if is_v3:
        checks = [
            ("命題の到達可能性", check_proposition_reachability),
            ("想起条件の到達可能性", check_recall_reachability_v3),
            ("孤立命題の検出", check_orphan_descriptors),
        ]
    else:
        checks = [
            ("基礎命題の到達可能性", check_base_descriptor_reachability),
            ("ピース構成命題の到達可能性", check_piece_member_reachability),
            ("想起スコープの整合性", check_recall_scope),
            ("孤立命題の検出", check_orphan_descriptors),
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

"""到達可能性チェック

initial_confirmed 以外の全記述素が question の reveals 経由で到達可能かを検証する。
"""

import json
import sys
from pathlib import Path


def load_data(path: str) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _is_base(d: dict) -> bool:
    """基礎記述素かどうか（formation_conditions を持たない）"""
    return "formation_conditions" not in d


def _is_derived(d: dict) -> bool:
    """導出記述素かどうか（formation_conditions を持つ）"""
    return "formation_conditions" in d


def check_base_descriptor_reachability(data: dict) -> list[str]:
    """initial_confirmed に含まれない全基礎記述素が、いずれかの question の reveals に含まれるか。"""
    errors = []
    initial = set(data.get("initial_confirmed", []))
    revealed: set[str] = set()
    for q in data.get("questions", []):
        revealed.update(q.get("reveals", []))

    for d in data.get("descriptors", []):
        if not _is_base(d):
            continue
        did = d["id"]
        if did not in initial and did not in revealed:
            errors.append(f"基礎記述素 '{did}' ({d.get('label', '')}) が到達不能（initial_confirmed にも reveals にも含まれない）")
    return errors


def check_piece_member_reachability(data: dict) -> list[str]:
    """各ピースの members が全て到達可能か。"""
    errors = []
    initial = set(data.get("initial_confirmed", []))
    revealed: set[str] = set()
    for q in data.get("questions", []):
        revealed.update(q.get("reveals", []))
    reachable = initial | revealed

    for piece in data.get("pieces", []):
        pid = piece["id"]
        for mref in piece.get("members", []):
            if mref not in reachable:
                errors.append(f"piece '{pid}' の構成記述素 '{mref}' が到達不能")
    return errors


def _transitive_deps(pid: str, piece_deps: dict[str, set[str]]) -> set[str]:
    """depends_on の推移的閉包を計算する。"""
    visited: set[str] = set()
    stack = list(piece_deps.get(pid, set()))
    while stack:
        dep = stack.pop()
        if dep not in visited:
            visited.add(dep)
            stack.extend(piece_deps.get(dep, set()) - visited)
    return visited


def _derivable_descriptors(allowed_confirmed: set[str], descriptors: dict[str, list[list[str]]]) -> set[str]:
    """allowed_confirmed から導出可能な全記述素を不動点計算で求める。

    導出ロジック:
    1. 導出済み集合を allowed_confirmed で初期化
    2. 記述素が導出済み集合内と一致 → 導出
    3. 形成条件のいずれかのグループが全て導出済み → 導出
    4. 変化がなくなるまで繰り返す
    """
    derived = set(allowed_confirmed)
    changed = True
    while changed:
        changed = False
        for did, conditions in descriptors.items():
            if did in derived:
                continue
            # 記述素が confirmed と一致する場合
            if did in allowed_confirmed:
                derived.add(did)
                changed = True
                continue
            # 形成条件が全て導出済みの場合
            for cond_group in conditions:
                if all(ref in derived for ref in cond_group):
                    derived.add(did)
                    changed = True
                    break
    # 導出済み集合のうち導出記述素IDに該当するものを返す
    return {did for did in derived if did in descriptors}


def check_recall_scope(data: dict) -> list[str]:
    """各ピースの想起スコープの検証。

    recall_conditions は記述素IDで構成される。
    各ピースのスコープ内の記述素集合から導出可能な記述素のみが許可される。
    独立ピース: S の記述素 + 自身の記述素から導出可能
    依存ピース: 上記 + 依存先ピース（推移的）の記述素から導出可能
    """
    errors = []
    initial = set(data.get("initial_confirmed", []))

    # descriptor → piece mapping
    descriptor_to_piece: dict[str, str] = {}
    for piece in data.get("pieces", []):
        for mid in piece.get("members", []):
            descriptor_to_piece[mid] = piece["id"]

    piece_deps = {p["id"]: set(p.get("depends_on", [])) for p in data.get("pieces", [])}
    # members + trigger の全記述素をピースの記述素とする
    piece_members: dict[str, set[str]] = {}
    for p in data.get("pieces", []):
        ids = set(p.get("members", []))
        for group in p.get("trigger", []):
            ids.update(group)
        piece_members[p["id"]] = ids

    # question reveals mapping: descriptor_id → [question, ...]
    reveals_map: dict[str, list[dict]] = {}
    for q in data.get("questions", []):
        for did in q.get("reveals", []):
            reveals_map.setdefault(did, []).append(q)

    # 導出記述素: formation_conditions を持つもの
    derived_descriptors = {d["id"]: d.get("formation_conditions", []) for d in data.get("descriptors", []) if _is_derived(d)}

    for piece in data.get("pieces", []):
        pid = piece["id"]
        deps = _transitive_deps(pid, piece_deps)
        is_independent = len(piece.get("depends_on", [])) == 0
        piece_type = "独立" if is_independent else "依存"

        # allowed confirmed = initial + own + transitive deps
        allowed_confirmed = set(initial)
        allowed_confirmed.update(piece_members.get(pid, set()))
        for dep_pid in deps:
            allowed_confirmed.update(piece_members.get(dep_pid, set()))

        # allowed = base descriptors in scope + derived descriptors from scope
        derivable = _derivable_descriptors(allowed_confirmed, derived_descriptors)
        allowed = allowed_confirmed | derivable

        # check each question that reveals this piece's members
        for mid in piece.get("members", []):
            for q in reveals_map.get(mid, []):
                qid = q["id"]
                for i, cond_group in enumerate(q.get("recall_conditions", [])):
                    for ref in cond_group:
                        if ref not in allowed:
                            errors.append(
                                f"{piece_type}ピース '{pid}': question '{qid}' の "
                                f"recall_conditions[{i}] の記述素 '{ref}' がスコープ外"
                            )
    return errors


def check_orphan_descriptors(data: dict) -> list[str]:
    """孤立基礎記述素の検出。"""
    warnings = []
    initial = set(data.get("initial_confirmed", []))
    revealed: set[str] = set()
    for q in data.get("questions", []):
        revealed.update(q.get("reveals", []))

    for d in data.get("descriptors", []):
        if not _is_base(d):
            continue
        did = d["id"]
        if did not in initial and did not in revealed:
            warnings.append(f"孤立記述素: '{did}' ({d.get('label', '')})")
    return warnings


def run(path: str) -> tuple[bool, list[str]]:
    data = load_data(path)
    checks = [
        ("基礎記述素の到達可能性", check_base_descriptor_reachability),
        ("ピース構成記述素の到達可能性", check_piece_member_reachability),
        ("想起スコープの整合性", check_recall_scope),
        ("孤立記述素の検出", check_orphan_descriptors),
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

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


def _derivable_hypotheses(allowed_facts: set[str], hypotheses: dict[str, list[list[str]]]) -> set[str]:
    """allowed_facts から導出可能な全仮説を不動点計算で求める。

    導出ロジック（structure/仮説導出.md）:
    1. 導出済み集合を allowed_facts で初期化
    2. 仮説が導出済み集合内の事実と一致 → 導出
    3. 形成条件（仮説のみ）のいずれかのグループが全て導出済み → 導出
    4. 変化がなくなるまで繰り返す
    """
    derived = set(allowed_facts)
    changed = True
    while changed:
        changed = False
        for hid, conditions in hypotheses.items():
            if hid in derived:
                continue
            # 仮説が事実と一致する場合
            if hid in allowed_facts:
                derived.add(hid)
                changed = True
                continue
            # 形成条件が全て導出済みの場合
            for cond_group in conditions:
                if all(ref in derived for ref in cond_group):
                    derived.add(hid)
                    changed = True
                    break
    # 導出済み集合のうち仮説IDに該当するものを返す。
    # H-* が事実と仮説の両方のIDを持つ場合、allowed_facts にあっても仮説として返す。
    return {hid for hid in derived if hid in hypotheses}


def check_recall_scope(data: dict) -> list[str]:
    """各ピースの想起スコープの検証。

    recall_conditions は仮説のみで構成される。
    各ピースのスコープ内の事実集合から導出可能な仮説のみが許可される。
    独立ピース: S の事実 + 自身の事実から導出可能な仮説
    依存ピース: 上記 + 依存先ピース（推移的）の事実から導出可能な仮説
    """
    errors = []
    initial = set(data.get("initial_facts", []))

    # fact → piece mapping
    fact_to_piece: dict[str, str] = {}
    for piece in data.get("pieces", []):
        for fid in piece.get("facts", []):
            fact_to_piece[fid] = piece["id"]

    piece_deps = {p["id"]: set(p.get("depends_on", [])) for p in data.get("pieces", [])}
    piece_facts = {p["id"]: set(p.get("facts", [])) for p in data.get("pieces", [])}

    # question reveals mapping: fact_id → [question, ...]
    reveals_map: dict[str, list[dict]] = {}
    for q in data.get("questions", []):
        for fid in q.get("reveals", []):
            reveals_map.setdefault(fid, []).append(q)

    hypotheses = {h["id"]: h.get("formation_conditions", []) for h in data.get("hypotheses", [])}

    for piece in data.get("pieces", []):
        pid = piece["id"]
        deps = _transitive_deps(pid, piece_deps)
        is_independent = len(piece.get("depends_on", [])) == 0
        piece_type = "独立" if is_independent else "依存"

        # allowed facts = initial + own + transitive deps
        allowed_facts = set(initial)
        allowed_facts.update(piece_facts.get(pid, set()))
        for dep_pid in deps:
            allowed_facts.update(piece_facts.get(dep_pid, set()))

        # derivable hypotheses from allowed facts
        derivable = _derivable_hypotheses(allowed_facts, hypotheses)
        allowed = derivable

        # check each question that reveals this piece's facts
        for fid in piece.get("facts", []):
            for q in reveals_map.get(fid, []):
                qid = q["id"]
                for i, cond_group in enumerate(q.get("recall_conditions", [])):
                    for ref in cond_group:
                        if ref not in allowed:
                            errors.append(
                                f"{piece_type}ピース '{pid}': question '{qid}' の "
                                f"recall_conditions[{i}] の仮説 '{ref}' がスコープ外"
                            )
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
        ("想起スコープの整合性", check_recall_scope),
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

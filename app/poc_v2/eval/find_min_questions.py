"""最小質問集合の算出

クリア条件に到達するために必要な最小の質問数と
その質問集合・順序を BFS で探索する。

クリア判定は confirmed（観測）のみで行う。
仮説（formation_conditions 由来の derived）ではクリアできない。
"""

import json
import sys
from collections import deque
from pathlib import Path

MAX_SOLUTIONS = 200


def load_data(path: str) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def derive(confirmed: frozenset, formation_map: dict) -> frozenset:
    """confirmed から導出可能な仮説を全て求め、confirmed ∪ derived を返す"""
    known = set(confirmed)
    changed = True
    while changed:
        changed = False
        for did, conditions in formation_map.items():
            if did in known:
                continue
            for cond_group in conditions:
                if all(ref in known for ref in cond_group):
                    known.add(did)
                    changed = True
                    break
    return frozenset(known)


def check_clear(confirmed: frozenset, clear_conditions: list) -> bool:
    """クリア判定: confirmed（観測）のみで判定"""
    for cond_group in clear_conditions:
        if all(d in confirmed for d in cond_group):
            return True
    return False


def find_minimum_questions(data: dict):
    """BFS で最小質問集合を探索する。

    状態は confirmed（観測のみ）で管理。
    想起条件の判定には derived（confirmed + 仮説）を使う。
    クリア判定は confirmed のみ。
    """
    initial = frozenset(data["initial_confirmed"])
    clear_conds = data["clear_conditions"]
    questions = data["questions"]

    formation_map = {}
    for d in data["descriptors"]:
        if "formation_conditions" in d:
            formation_map[d["id"]] = d["formation_conditions"]

    # 初期状態で既にクリアか
    if check_clear(initial, clear_conds):
        return 0, [[]]

    # BFS: state = confirmed frozenset（観測のみ）
    queue: deque = deque()
    queue.append((initial, []))
    visited: dict[frozenset, int] = {initial: 0}

    solutions: list[list[str]] = []
    min_depth = float("inf")

    while queue:
        confirmed, path = queue.popleft()
        depth = len(path)

        if depth >= min_depth:
            continue

        # 想起条件の判定には known（confirmed + derived）を使う
        known = derive(confirmed, formation_map)
        asked_ids = frozenset(path)

        for q in questions:
            qid = q["id"]
            if qid in asked_ids:
                continue

            recall_met = any(
                all(ref in known for ref in cg) for cg in q["recall_conditions"]
            )
            if not recall_met:
                continue

            # reveals を confirmed に追加（観測）
            new_confirmed = confirmed | frozenset(q["reveals"])
            new_path = path + [qid]
            new_depth = len(new_path)

            # クリア判定は confirmed のみ
            if check_clear(new_confirmed, clear_conds):
                if new_depth < min_depth:
                    min_depth = new_depth
                    solutions = [new_path]
                elif new_depth == min_depth and len(solutions) < MAX_SOLUTIONS:
                    solutions.append(new_path)
                continue

            prev = visited.get(new_confirmed)
            if prev is None or prev > new_depth:
                visited[new_confirmed] = new_depth
                queue.append((new_confirmed, new_path))

    return min_depth, solutions


def main():
    if len(sys.argv) < 2:
        print("Usage: python find_min_questions.py <data.json>", file=sys.stderr)
        sys.exit(2)

    path = sys.argv[1]
    if not Path(path).exists():
        print(f"Error: {path} が見つかりません", file=sys.stderr)
        sys.exit(2)

    data = load_data(path)
    min_depth, solutions = find_minimum_questions(data)

    if not solutions:
        print("クリア不能: 質問の組み合わせでクリア条件に到達できません")
        sys.exit(1)

    # 質問集合でグループ化
    unique_sets: dict[frozenset, list[str]] = {}
    for sol in solutions:
        key = frozenset(sol)
        if key not in unique_sets:
            unique_sets[key] = sol

    print(f"最小質問数: {min_depth}")
    print(f"最小質問集合の種類: {len(unique_sets)}")
    print(f"順序バリエーション総数: {len(solutions)}")
    print()

    formation_map = {}
    for d in data["descriptors"]:
        if "formation_conditions" in d:
            formation_map[d["id"]] = d["formation_conditions"]

    q_map = {q["id"]: q for q in data["questions"]}
    d_map = {d["id"]: d["label"] for d in data["descriptors"]}

    for i, (qset, example_order) in enumerate(unique_sets.items(), 1):
        print(f"=== 質問集合 {i}: {{{', '.join(sorted(qset))}}} ===")
        print()

        confirmed = frozenset(data["initial_confirmed"])

        for step, qid in enumerate(example_order, 1):
            q = q_map[qid]
            confirmed_before = confirmed
            new_reveals = frozenset(q["reveals"])
            confirmed = confirmed | new_reveals
            known = derive(confirmed, formation_map)
            derived_new = sorted(known - confirmed)

            print(f"  {step}. {qid} 「{q['text']}」 → {q['answer']}")
            for r in q["reveals"]:
                print(f"     reveals: {r} ({d_map[r]})")
            if derived_new:
                for dd in derived_new:
                    print(f"     導出:   {dd} ({d_map[dd]})")

        clear_met = check_clear(confirmed, data["clear_conditions"])
        print(f"\n  クリア: {'✓' if clear_met else '✗'}")
        print()


if __name__ == "__main__":
    main()

"""クリアチェーンの骨格構造を表示する

find_clear_chains で得た最小質問集合について、
クリア条件からの逆算依存ツリーを表示する。
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Optional

from find_clear_chains import run as find_chains


def load_data(path: str) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def build_indices(data: dict) -> tuple:
    questions = {q["id"]: q for q in data["questions"]}
    # 導出記述素の formation_conditions
    derived_conds: dict[str, list[list[str]]] = {}
    descriptor_labels: dict[str, str] = {}
    for d in data["descriptors"]:
        descriptor_labels[d["id"]] = d["label"]
        if "formation_conditions" in d:
            derived_conds[d["id"]] = d["formation_conditions"]
    # descriptor_id → 質問（question_set 内のもののみ後で絞る）
    descriptor_to_q: dict[str, list[str]] = {}
    for q in data["questions"]:
        for did in q["reveals"]:
            descriptor_to_q.setdefault(did, []).append(q["id"])
    return questions, derived_conds, descriptor_labels, descriptor_to_q


def show_tree(
    data: dict,
    qset: frozenset[str],
):
    """クリア条件から逆算した依存ツリーを表示"""
    questions, derived_conds, descriptor_labels, descriptor_to_q = build_indices(data)
    clear_conditions = data["clear_conditions"]
    initial = set(data.get("initial_confirmed", []))

    shown: set[str] = set()  # 重複表示を防ぐ

    def label(id_: str) -> str:
        return descriptor_labels.get(id_, id_)

    def find_q_for_descriptor(descriptor_id: str) -> Optional[str]:
        """qset 内で descriptor_id を reveals する質問を返す"""
        for qid in descriptor_to_q.get(descriptor_id, []):
            if qid in qset:
                return qid
        return None

    def find_how_derived(did: str) -> tuple[str, list[str] | None]:
        """記述素がどう形成されるか"""
        # initial_confirmed は無条件で到達済み
        if did in initial:
            return ("initial", None)
        # reveals match 経由の質問が qset にあるか
        qid = find_q_for_descriptor(did)
        if qid is not None:
            return ("reveals_match", qid)
        # formation_conditions 経由
        for cond_group in derived_conds.get(did, []):
            if all(is_reachable(d) for d in cond_group):
                return ("formation", cond_group)
        return ("unknown", None)

    def is_reachable(did: str) -> bool:
        kind, detail = find_how_derived(did)
        return kind != "unknown"

    def print_derived(did: str, indent: int):
        if did in shown:
            prefix = "  " * indent
            print(f"{prefix}  ({did} は上述)")
            return
        shown.add(did)

        kind, detail = find_how_derived(did)
        prefix = "  " * indent

        if kind == "initial":
            print(f"{prefix}  ← [初期確認済み]")
        elif kind == "reveals_match":
            qid = detail
            q = questions[qid]
            recall = q["recall_conditions"]
            recall_str = format_recall(recall)
            print(f"{prefix}  ← {qid}「{q['text']}」{recall_str}")
            # recall の記述素を再帰
            for cond_group in recall:
                for dep_did in cond_group:
                    print(f"{prefix}    requires ★{dep_did}({descriptor_labels.get(dep_did, '')})")
                    print_derived(dep_did, indent + 2)
        elif kind == "formation":
            cond_group = detail
            cond_str = " + ".join(f"★{d}" for d in cond_group)
            print(f"{prefix}  ← formation: [{cond_str}]")
            for dep_did in cond_group:
                print_derived(dep_did, indent + 1)

    def format_recall(recall: list[list[str]]) -> str:
        if not recall:
            return ""
        groups = []
        for cg in recall:
            if not cg:
                groups.append("入口")
            else:
                groups.append(" + ".join(f"★{d}" for d in cg))
        return "  [recall: " + " | ".join(groups) + "]"

    # メイン表示
    for cond_group in clear_conditions:
        descriptors_str = " AND ".join(f"{d}({label(d)})" for d in cond_group)
        print(f"  クリア条件: {descriptors_str}")
        print()

        for descriptor_id in cond_group:
            print(f"  {descriptor_id}({label(descriptor_id)})")
            kind, detail = find_how_derived(descriptor_id)
            if kind == "reveals_match":
                qid = detail
                q = questions[qid]
                recall = q["recall_conditions"]
                recall_str = format_recall(recall)
                print(f"    ← {qid}「{q['text']}」{recall_str}")
                for cond_group_r in recall:
                    for did in cond_group_r:
                        print(f"      requires ★{did}({descriptor_labels.get(did, '')})")
                        print_derived(did, 3)
            elif kind == "formation":
                cond_str = " + ".join(f"★{d}({label(d)})" for d in detail)
                print(f"    ← formation: [{cond_str}]")
                for dep_did in detail:
                    print_derived(dep_did, 2)
            else:
                print(f"    到達不能")

        print()


def main():
    if len(sys.argv) < 2:
        print("Usage: python show_clear_flows.py <data.json>", file=sys.stderr)
        sys.exit(2)

    path = sys.argv[1]
    if not Path(path).exists():
        print(f"Error: {path} が見つかりません", file=sys.stderr)
        sys.exit(2)

    data = load_data(path)
    chains = find_chains(path)
    chains_sorted = sorted(chains, key=lambda s: (len(s), sorted(s)))

    for i, qset in enumerate(chains_sorted, 1):
        ids = sorted(qset)
        print(f"{'='*60}")
        print(f"チェーン #{i}（{len(ids)}問）: {ids}")
        print(f"{'='*60}")
        show_tree(data, qset)


if __name__ == "__main__":
    main()

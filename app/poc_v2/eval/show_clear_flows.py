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
    hypo_conds = {h["id"]: h["formation_conditions"] for h in data["hypotheses"]}
    hypo_labels = {h["id"]: h["label"] for h in data["hypotheses"]}
    fact_labels = {f["id"]: f["label"] for f in data["facts"]}
    # fact_id → 質問（question_set 内のもののみ後で絞る）
    fact_to_q: dict[str, list[str]] = {}
    for q in data["questions"]:
        for fid in q["reveals"]:
            fact_to_q.setdefault(fid, []).append(q["id"])
    return questions, hypo_conds, hypo_labels, fact_labels, fact_to_q


def show_tree(
    data: dict,
    qset: frozenset[str],
):
    """クリア条件から逆算した依存ツリーを表示"""
    questions, hypo_conds, hypo_labels, fact_labels, fact_to_q = build_indices(data)
    clear_conditions = data["clear_conditions"]

    shown: set[str] = set()  # 重複表示を防ぐ

    def label(id_: str) -> str:
        return fact_labels.get(id_, hypo_labels.get(id_, id_))

    def find_q_for_fact(fact_id: str) -> Optional[str]:
        """qset 内で fact_id を reveals する質問を返す"""
        for qid in fact_to_q.get(fact_id, []):
            if qid in qset:
                return qid
        return None

    def find_how_hypo_formed(hid: str) -> tuple[str, list[str] | None]:
        """仮説がどう形成されるか: ("fact_match", None) or ("formation", [条件仮説群])"""
        # fact match 経由の質問が qset にあるか
        qid = find_q_for_fact(hid)
        if qid is not None:
            return ("fact_match", qid)
        # formation_conditions 経由
        for cond_group in hypo_conds.get(hid, []):
            if all(is_reachable(h) for h in cond_group):
                return ("formation", cond_group)
        return ("unknown", None)

    def is_reachable(hid: str) -> bool:
        kind, detail = find_how_hypo_formed(hid)
        return kind != "unknown"

    def print_hypo(hid: str, indent: int):
        if hid in shown:
            prefix = "  " * indent
            print(f"{prefix}  ({hid} は上述)")
            return
        shown.add(hid)

        kind, detail = find_how_hypo_formed(hid)
        prefix = "  " * indent

        if kind == "fact_match":
            qid = detail
            q = questions[qid]
            recall = q["recall_conditions"]
            recall_str = format_recall(recall)
            print(f"{prefix}  ← {qid}「{q['text']}」{recall_str}")
            # recall の仮説を再帰
            for cond_group in recall:
                for dep_hid in cond_group:
                    print(f"{prefix}    requires ★{dep_hid}({hypo_labels.get(dep_hid, '')})")
                    print_hypo(dep_hid, indent + 2)
        elif kind == "formation":
            cond_group = detail
            cond_str = " + ".join(f"★{h}" for h in cond_group)
            print(f"{prefix}  ← formation: [{cond_str}]")
            for dep_hid in cond_group:
                print_hypo(dep_hid, indent + 1)

    def format_recall(recall: list[list[str]]) -> str:
        if not recall:
            return ""
        groups = []
        for cg in recall:
            if not cg:
                groups.append("入口")
            else:
                groups.append(" + ".join(f"★{h}" for h in cg))
        return "  [recall: " + " | ".join(groups) + "]"

    # メイン表示
    for cond_group in clear_conditions:
        facts_str = " AND ".join(f"{f}({label(f)})" for f in cond_group)
        print(f"  クリア条件: {facts_str}")
        print()

        for fact_id in cond_group:
            qid = find_q_for_fact(fact_id)
            if qid is None:
                print(f"  {fact_id}: 到達不能")
                continue

            q = questions[qid]
            recall = q["recall_conditions"]
            recall_str = format_recall(recall)
            print(f"  {fact_id}({label(fact_id)})")
            print(f"    ← {qid}「{q['text']}」{recall_str}")

            # recall の仮説を展開
            for cond_group_r in recall:
                for hid in cond_group_r:
                    print(f"      requires ★{hid}({hypo_labels.get(hid, '')})")
                    print_hypo(hid, 3)

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

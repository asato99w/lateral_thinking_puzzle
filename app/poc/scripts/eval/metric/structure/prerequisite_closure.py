"""前提閉包性レポート（L3-6）。

各パラダイムの Q(P) について、質問の prerequisites がパラダイム内で
充足されるかを検証し、不足記述素を列挙する。

前提閉包条件: Q(P) 内の各質問 q の prerequisites に含まれる記述素 d が、
  - Ps（初期観測）に含まれる、または
  - Q(P) 内の別の質問の effect に含まれる
のいずれかを満たすこと。満たさない記述素を「前提不足記述素」として報告する。

OK/NG 判定は行わない（品質メトリクスの定量報告のみ）。

使い方:
  python prerequisite_closure.py                       # turtle_soup.json
  python prerequisite_closure.py --data bar_man.json   # bar_man.json
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from common import load_data, derive_qp  # noqa: E402
from engine import compute_effect  # noqa: E402


def compute_qp_producers(qp):
    """Q(P) 内の質問群から、各記述素を生産する質問の集合を返す。"""
    producers = {}
    for q in qp:
        eff = compute_effect(q)
        if q.correct_answer == "irrelevant":
            continue
        for d, v in eff:
            producers.setdefault(d, set()).add(q.id)
    return producers


def find_missing_prerequisites(qp, ps_values):
    """Q(P) 内の前提不足記述素を列挙する。

    Returns:
        {q.id: [不足記述素のリスト]}（不足がある質問のみ）
    """
    initial_ds = set(ps_values.keys())
    producers = compute_qp_producers(qp)

    missing = {}
    for q in qp:
        prereqs = q.prerequisites or []
        if not prereqs:
            continue
        q_missing = []
        for d in prereqs:
            if d in initial_ds:
                continue
            # Q(P) 内の他の質問が生産するか
            prod_qids = producers.get(d, set())
            # 自分自身は除外
            other_prods = prod_qids - {q.id}
            if not other_prods:
                q_missing.append(d)
        if q_missing:
            missing[q.id] = q_missing
    return missing


def report_paradigm(pid, paradigm, questions, ps_values):
    """1つのパラダイムの前提閉包性を報告する。"""
    qp = derive_qp(questions, paradigm)
    if not qp:
        print(f"  Q({pid}) は空です。")
        return

    print(f"  |Q({pid})| = {len(qp)}")

    missing = find_missing_prerequisites(qp, ps_values)

    if not missing:
        print("  前提不足: なし")
    else:
        print(f"  前提不足: {len(missing)} 件")
        print()
        for qid, ds in sorted(missing.items()):
            q = next(q for q in qp if q.id == qid)
            prereqs_str = ", ".join(q.prerequisites)
            print(f"    {qid} (prerequisites: [{prereqs_str}])")
            for d in ds:
                print(f"      不足: {d} (Q({pid}) 内に生産元なし)")


def main():
    paradigms, questions, all_ids, ps_values, init_pid, _caps, _tp = load_data()

    print("=" * 65)
    print("前提閉包性レポート (L3-6)")
    print("=" * 65)
    print()

    for pid in paradigms:
        p = paradigms[pid]
        print(f"{'=' * 60}")
        print(f"{pid}: {p.name}")
        print(f"{'=' * 60}")
        report_paradigm(pid, p, questions, ps_values)
        print()


if __name__ == "__main__":
    main()

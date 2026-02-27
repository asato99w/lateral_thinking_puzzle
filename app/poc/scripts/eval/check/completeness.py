"""完全性検証スクリプト（L2-1）。

各パラダイム P（T を除く）の固有アノマリー記述素が
Q(P) のいずれかの質問の effect でカバーされることを検証する。

固有アノマリー = Anomaly(P) - SharedAnomaly(P)
SharedAnomaly(P) = Union of Anomaly(P') for all P' with depth(P') < depth(P)

上位パラダイムと共有されたアノマリーは先行フェーズで O に入るため、
Q(P) 自身でのカバーを要求しない。

使い方:
  python completeness.py                       # turtle_soup.json
  python completeness.py --data bar_man.json   # bar_man.json
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from common import load_data, derive_qp, get_truth  # noqa: E402
from engine import compute_effect  # noqa: E402


def compute_anomaly_sets(paradigms, truth):
    """各パラダイムのアノマリー記述素集合を計算する。"""
    return {
        pid: {
            d for d, pred in p.p_pred.items()
            if truth.get(d) is not None and pred != truth[d]
        }
        for pid, p in paradigms.items()
    }


def compute_unique_anomalies(pid, paradigms, anomaly_sets):
    """固有アノマリー = Anomaly(P) \\ SharedAnomaly(P) を計算する。

    SharedAnomaly(P) = ∪_{P' : depth(P') < depth(P)} Anomaly(P')
    """
    my_depth = paradigms[pid].depth
    shared = set()
    for other_pid, other_p in paradigms.items():
        if other_pid == pid:
            continue
        if other_p.depth < my_depth:
            shared |= anomaly_sets[other_pid]
    return anomaly_sets[pid] - shared


def check_completeness(pid, paradigm, paradigms, questions, truth, anomaly_sets):
    """パラダイムの完全性を検証する。

    Returns:
        (ok, all_anomaly, unique_anomaly, covered, uncovered)
    """
    qp = derive_qp(questions, paradigm)

    all_anomaly = anomaly_sets[pid]
    unique_anomaly = compute_unique_anomalies(pid, paradigms, anomaly_sets)

    if not unique_anomaly:
        return True, all_anomaly, unique_anomaly, set(), set()

    # Q(P) の effect でカバーされる固有アノマリー記述素
    covered = set()
    for q in qp:
        if q.correct_answer == "irrelevant":
            continue
        eff = compute_effect(q)
        for d, v in eff:
            if d in unique_anomaly:
                covered.add(d)

    uncovered = unique_anomaly - covered
    return len(uncovered) == 0, all_anomaly, unique_anomaly, covered, uncovered


def main():
    paradigms, questions, all_ids, ps_values, init_pid = load_data()
    truth = get_truth(questions)
    anomaly_sets = compute_anomaly_sets(paradigms, truth)

    print("=" * 65)
    print("完全性検証 (L2-1)")
    print("=" * 65)
    print()

    all_ok = True

    for pid, paradigm in paradigms.items():
        ok, all_anom, unique_anom, covered, uncovered = check_completeness(
            pid, paradigm, paradigms, questions, truth, anomaly_sets,
        )

        print(f"-" * 50)
        print(f"{pid}: {paradigm.name} (depth={paradigm.depth})")
        print(f"-" * 50)

        if not all_anom:
            print(f"  アノマリー記述素なし（最終パラダイム）")
        else:
            shared = all_anom - unique_anom
            print(f"  アノマリー記述素: {len(all_anom)}個")
            if shared:
                print(f"    上位共有: {len(shared)}個 {sorted(shared)}")
            print(f"    固有: {len(unique_anom)}個 {sorted(unique_anom)}")
            print(f"  固有カバー済み: {len(covered)}個")
            if uncovered:
                print(f"  未カバー固有: {sorted(uncovered)}")
                print(f"  結果: NG")
                all_ok = False
            else:
                print(f"  結果: OK")

        print()

    print("=" * 65)
    print(f"総合結果: {'OK — 全パラダイムで完全性充足' if all_ok else 'NG — 未カバーあり'}")
    print("=" * 65)


if __name__ == "__main__":
    main()

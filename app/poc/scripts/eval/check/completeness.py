"""完全性検証スクリプト（L2-1）。

2段階で検証する:
  局所条件: 各 P の RequiredAnomaly が Q(P) でカバーされること
  大域条件: 全アノマリー記述素がいずれかの Q(P') でカバーされること

RequiredAnomaly(P) = Anomaly(P) - UpperShared(P)
  - UpperShared(P): より深いパラダイムと共有するアノマリー（免除対象）
  - 固有・下位共有・同一depth共有はカバー必須

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


def classify_anomalies(pid, paradigms, anomaly_sets):
    """アノマリーを 固有 / 上位共有 / 下位共有 / 同一depth共有 に分類する。

    Returns:
        (unique, upper_shared, lower_shared, same_depth_shared)
    """
    p = paradigms[pid]
    my_anom = anomaly_sets[pid]
    my_depth = p.depth or 0

    upper_shared = set()  # より深いパラダイムと共有
    lower_shared = set()  # より浅いパラダイムと共有
    same_depth_shared = set()  # 同一depthと共有

    for other_pid, other_anom in anomaly_sets.items():
        if other_pid == pid:
            continue
        other_depth = paradigms[other_pid].depth or 0
        shared = my_anom & other_anom
        if not shared:
            continue
        if other_depth > my_depth:
            upper_shared |= shared
        elif other_depth < my_depth:
            lower_shared |= shared
        else:
            same_depth_shared |= shared

    # 重複除去（複数カテゴリに該当する場合の優先: upper > lower > same_depth）
    lower_shared -= upper_shared
    same_depth_shared -= upper_shared | lower_shared

    unique = my_anom - upper_shared - lower_shared - same_depth_shared
    return unique, upper_shared, lower_shared, same_depth_shared


def compute_required_anomalies(pid, paradigms, anomaly_sets):
    """RequiredAnomaly(P) = Anomaly(P) - UpperShared(P)。"""
    unique, upper_shared, lower_shared, same_depth_shared = classify_anomalies(
        pid, paradigms, anomaly_sets,
    )
    return anomaly_sets[pid] - upper_shared


def compute_covered_by_qp(paradigm, questions):
    """Q(P) の effect でカバーされる記述素を返す。"""
    qp = derive_qp(questions, paradigm)
    covered = set()
    for q in qp:
        if q.correct_answer == "irrelevant":
            continue
        eff = compute_effect(q)
        for d, v in eff:
            covered.add(d)
    return covered


def main():
    paradigms, questions, all_ids, ps_values, init_pid, _caps = load_data()
    truth = get_truth(questions)
    anomaly_sets = compute_anomaly_sets(paradigms, truth)

    # 全 Q(P) の effect でカバーされる記述素（大域条件用）
    global_covered = set()
    for pid, p in paradigms.items():
        global_covered |= compute_covered_by_qp(p, questions)

    print("=" * 65)
    print("完全性検証 (L2-1)")
    print("=" * 65)
    print()

    local_ok = True
    global_ok = True

    # --- 局所条件 ---
    for pid, paradigm in paradigms.items():
        all_anom = anomaly_sets[pid]
        unique, upper_shared, lower_shared, same_depth_shared = classify_anomalies(
            pid, paradigms, anomaly_sets,
        )
        required = all_anom - upper_shared

        print(f"-" * 50)
        print(f"{pid}: {paradigm.name} (depth={paradigm.depth})")
        print(f"-" * 50)

        if not all_anom:
            print(f"  アノマリー記述素なし（最終パラダイム）")
            print()
            continue

        print(f"  アノマリー記述素: {len(all_anom)}個")
        print(f"    固有: {len(unique)}個", end="")
        if unique:
            print(f" {sorted(unique)}")
        else:
            print()
        print(f"    上位共有（免除）: {len(upper_shared)}個", end="")
        if upper_shared:
            print(f" {sorted(upper_shared)}")
        else:
            print()
        if lower_shared:
            print(f"    下位共有: {len(lower_shared)}個 {sorted(lower_shared)}")
        if same_depth_shared:
            print(f"    同一depth共有: {len(same_depth_shared)}個 {sorted(same_depth_shared)}")
        print(f"  カバー必須 (Required): {len(required)}個")

        if not required:
            print(f"  局所条件: OK（カバー必須アノマリーなし）")
            print()
            continue

        # Q(P) でカバーされる Required アノマリー
        qp_covered = compute_covered_by_qp(paradigm, questions)
        covered_required = required & qp_covered
        uncovered_required = required - qp_covered

        print(f"  カバー済み: {len(covered_required)}個")
        if uncovered_required:
            print(f"  未カバー: {sorted(uncovered_required)}")
            print(f"  局所条件: NG")
            local_ok = False
        else:
            print(f"  局所条件: OK")

        print()

    # --- 大域条件 ---
    print(f"-" * 50)
    print("大域条件: 全アノマリーがいずれかの Q(P) でカバー")
    print(f"-" * 50)

    all_anomaly_ds = set()
    for anom in anomaly_sets.values():
        all_anomaly_ds |= anom

    globally_uncovered = all_anomaly_ds - global_covered
    print(f"  全アノマリー記述素: {len(all_anomaly_ds)}個")
    print(f"  いずれかの Q(P) でカバー済み: {len(all_anomaly_ds - globally_uncovered)}個")
    if globally_uncovered:
        print(f"  未カバー: {sorted(globally_uncovered)}")
        # どのパラダイムのアノマリーか表示
        for d in sorted(globally_uncovered):
            owners = [pid for pid, anom in anomaly_sets.items() if d in anom]
            print(f"    {d}: Anomaly of {owners}")
        print(f"  大域条件: NG")
        global_ok = False
    else:
        print(f"  大域条件: OK")

    print()

    # --- 総合結果 ---
    all_ok = local_ok and global_ok
    print("=" * 65)
    if all_ok:
        print("総合結果: OK — 局所・大域とも完全性充足")
    else:
        parts = []
        if not local_ok:
            parts.append("局所NG")
        if not global_ok:
            parts.append("大域NG")
        print(f"総合結果: NG — {', '.join(parts)}")
    print("=" * 65)


if __name__ == "__main__":
    main()

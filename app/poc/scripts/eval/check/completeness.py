"""完全性検証スクリプト（L2-1）。

各パラダイム P（T を除く）の全アノマリー記述素が
Q(P) のいずれかの質問の effect でカバーされることを検証する。

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


def check_completeness(pid, paradigm, questions, truth):
    """パラダイムの完全性を検証する。

    Returns:
        (ok, anomaly_descriptors, covered, uncovered)
    """
    qp = derive_qp(questions, paradigm)

    # アノマリー記述素: P_pred が T と矛盾する記述素
    anomaly_descriptors = {
        d for d, pred in paradigm.p_pred.items()
        if truth.get(d) is not None and pred != truth[d]
    }

    if not anomaly_descriptors:
        return True, set(), set(), set()

    # Q(P) の effect でカバーされるアノマリー記述素
    covered = set()
    for q in qp:
        if q.correct_answer == "irrelevant":
            continue
        eff = compute_effect(q)
        for d, v in eff:
            if d in anomaly_descriptors:
                covered.add(d)

    uncovered = anomaly_descriptors - covered
    return len(uncovered) == 0, anomaly_descriptors, covered, uncovered


def main():
    paradigms, questions, all_ids, ps_values, init_pid = load_data()
    truth = get_truth(questions)

    print("=" * 65)
    print("完全性検証 (L2-1)")
    print("=" * 65)
    print()

    all_ok = True

    for pid, paradigm in paradigms.items():
        ok, anomaly_ds, covered, uncovered = check_completeness(
            pid, paradigm, questions, truth,
        )

        print(f"-" * 50)
        print(f"{pid}: {paradigm.name}")
        print(f"-" * 50)

        if not anomaly_ds:
            print(f"  アノマリー記述素なし（最終パラダイム）")
        else:
            print(f"  アノマリー記述素: {len(anomaly_ds)}個")
            print(f"  カバー済み: {len(covered)}個")
            if uncovered:
                print(f"  未カバー: {sorted(uncovered)}")
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

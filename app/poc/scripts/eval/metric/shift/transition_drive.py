"""遷移駆動集合の静的分析スクリプト。

P_pred の比較だけでパラダイム間の構造的な方向性を測定する。
shift_direction.py（動的検証）とは相補的な静的分析。

各メインパス遷移 P_i → P_{i+1} について:
  1. Q(P_i) の各質問を effect(q) の (d, v) ごとに P_i / P_{i+1} と比較
  2. anomaly_count と net_direction の 2 軸で 4 分類
  3. 遷移方向スコアと駆動率を算出

使い方:
  python transition_drive.py                       # turtle_soup.json
  python transition_drive.py --data bar_man.json   # bar_man.json
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "check"))

from common import load_data  # noqa: E402
from engine import compute_effect  # noqa: E402
from shift_direction import derive_qp, compute_main_path  # noqa: E402


# ── 質問レベルの量 ───────────────────────────────────


def compute_question_metrics(q, p_from, p_to):
    """質問レベルの量を算出する。

    Returns:
        (anomaly_count, support, oppose, net_direction)
    """
    eff = compute_effect(q)
    if q.correct_answer == "irrelevant":
        return (0, 0, 0, 0)

    anomaly_count = 0
    support = 0
    oppose = 0

    for d, v in eff:
        # P_i にアノマリーを生むか
        pred_from = p_from.prediction(d)
        if pred_from is not None and pred_from != v:
            anomaly_count += 1

        # P_{i+1} と整合するか / 矛盾するか
        pred_to = p_to.prediction(d)
        if pred_to is not None:
            if pred_to == v:
                support += 1
            else:
                oppose += 1

    net_direction = support - oppose
    return (anomaly_count, support, oppose, net_direction)


# ── 質問の 4 分類 ────────────────────────────────────


def classify_transition(q, p_from, p_to):
    """質問を 4 分類する。

    Returns:
        カテゴリ文字列: "遷移駆動" | "駆動・逆方向" | "方向支持" | "中立"
    """
    anomaly_count, support, oppose, net_direction = compute_question_metrics(
        q, p_from, p_to,
    )

    if anomaly_count > 0 and net_direction > 0:
        return "遷移駆動"
    elif anomaly_count > 0 and net_direction <= 0:
        return "駆動・逆方向"
    elif anomaly_count == 0 and net_direction > 0:
        return "方向支持"
    else:
        return "中立"


# ── main ─────────────────────────────────────────────


def main():
    paradigms, questions, all_ids, ps_values, init_pid = load_data()

    # メインパスを導出
    main_path = compute_main_path(init_pid, paradigms, questions, all_ids)

    print("=" * 65)
    print("遷移駆動集合の静的分析")
    print("=" * 65)
    print(f"メインパス: {' → '.join(main_path)}")
    print()

    for i in range(len(main_path) - 1):
        pid_from = main_path[i]
        pid_to = main_path[i + 1]
        p_from = paradigms[pid_from]
        p_to = paradigms[pid_to]

        print("-" * 50)
        print(f"遷移: {pid_from} → {pid_to}")
        print("-" * 50)

        # Q(P_i) を導出
        qp = derive_qp(questions, p_from)
        print(f"  |Q({pid_from})| = {len(qp)}")
        print(f"  threshold({pid_from}) = {p_from.threshold}")
        print()

        # 各質問を分類
        categories = {"遷移駆動": [], "駆動・逆方向": [], "方向支持": [], "中立": []}
        metrics_by_q = {}

        for q in qp:
            metrics = compute_question_metrics(q, p_from, p_to)
            cat = classify_transition(q, p_from, p_to)
            categories[cat].append(q)
            metrics_by_q[q.id] = (metrics, cat)

        # 4 分類の件数
        print("  【4 分類】")
        total_classified = 0
        for cat_name in ["遷移駆動", "駆動・逆方向", "方向支持", "中立"]:
            count = len(categories[cat_name])
            total_classified += count
            print(f"    {cat_name}: {count}")
        print(f"    合計: {total_classified}")
        print()

        # 集合レベルの指標
        sum_net = 0
        sum_support_oppose = 0
        for q in qp:
            anomaly_count, support, oppose, net_direction = metrics_by_q[q.id][0]
            sum_net += net_direction
            sum_support_oppose += support + oppose

        if sum_support_oppose > 0:
            direction_score = sum_net / sum_support_oppose
        else:
            direction_score = 0.0

        n_drive = len(categories["遷移駆動"])
        n_drive_reverse = len(categories["駆動・逆方向"])
        if n_drive + n_drive_reverse > 0:
            drive_rate = n_drive / (n_drive + n_drive_reverse)
        else:
            drive_rate = float("nan")

        print("  【集合レベルの指標】")
        print(f"    遷移方向スコア: {direction_score:+.4f}")
        if n_drive + n_drive_reverse > 0:
            print(f"    駆動率: {drive_rate:.4f} ({n_drive}/{n_drive + n_drive_reverse})")
        else:
            print(f"    駆動率: N/A（アノマリー質問なし）")
        print()

        # 遷移駆動集合のサイズ vs threshold
        print("  【遷移の十分性】")
        print(f"    遷移駆動集合サイズ: {n_drive}")
        if p_from.threshold is not None:
            if n_drive > p_from.threshold:
                print(f"    > threshold({p_from.threshold}): 十分")
            else:
                print(f"    ≤ threshold({p_from.threshold}): 不十分")
        else:
            print(f"    threshold 未定義")
        print()

        # 質問ごとの詳細
        print("  【質問ごとの詳細】")
        print(f"    {'質問ID':<8} {'anomaly':>7} {'support':>7} {'oppose':>7} {'net_dir':>7}  分類")
        print(f"    {'-'*8} {'-'*7} {'-'*7} {'-'*7} {'-'*7}  {'-'*12}")
        for q in qp:
            (anomaly_count, support, oppose, net_direction), cat = metrics_by_q[q.id]
            print(
                f"    {q.id:<8} {anomaly_count:>7} {support:>7} "
                f"{oppose:>7} {net_direction:>+7}  {cat}"
            )
        print()


if __name__ == "__main__":
    main()

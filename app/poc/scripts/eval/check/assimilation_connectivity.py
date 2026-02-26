"""同化接続性検証スクリプト（L2-2）。

各近傍ペア (P, P') について:
  1. P フェーズの全質問回答後の推定 O_P を計算
  2. Consistent(O_P, P') と Anomaly(O_P, P') を計算
  3. R(P') で Consistent と Anomaly の両方から到達可能なターゲット記述素 T_reach を計算
  4. T_reach の各 t について、t を effect に含む未回答質問の存在を確認
  5. OK/NG と診断情報を出力

使い方:
  python assimilation_connectivity.py                       # turtle_soup.json
  python assimilation_connectivity.py --data bar_man.json   # bar_man.json
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from common import load_data, derive_qp, neighbor_pairs  # noqa: E402
from engine import compute_effect, _reachable  # noqa: E402


def compute_estimated_o(paradigm, questions, ps_values):
    """P フェーズの全質問を回答した推定 O_P を計算する。"""
    qp = derive_qp(questions, paradigm)
    o_p = dict(ps_values)
    for q in qp:
        if q.correct_answer == "irrelevant":
            continue
        eff = compute_effect(q)
        for d, v in eff:
            o_p[d] = v
    return o_p


def check_question_coverage(
    consistent_reach, anomaly_reach, paradigm_next, questions, answered_ids,
):
    """到達可能ターゲットの各 t について、t を effect に含む未回答質問の存在を確認する。

    Returns:
        covered: {t: [q.id, ...]} - カバーされたターゲット記述素と質問
        uncovered: set - カバーされないターゲット記述素
    """
    t_reach = consistent_reach | anomaly_reach
    covered = {}
    uncovered = set()

    for t in t_reach:
        covering_qs = []
        for q in questions:
            if q.id in answered_ids:
                continue
            if q.correct_answer == "irrelevant":
                continue
            eff = compute_effect(q)
            for d, v in eff:
                if d == t:
                    if t in consistent_reach:
                        pred = paradigm_next.prediction(t)
                        if pred is not None and pred == v:
                            covering_qs.append(q.id)
                            break
                    if t in anomaly_reach:
                        covering_qs.append(q.id)
                        break
        if covering_qs:
            covered[t] = covering_qs
        else:
            uncovered.add(t)

    return covered, uncovered


def main():
    paradigms, questions, all_ids, ps_values, init_pid = load_data()

    pairs = neighbor_pairs(paradigms)

    print("=" * 65)
    print("同化接続性検証 (L2-2)")
    print("=" * 65)
    print(f"近傍ペア数: {len(pairs)}")
    print()

    all_ok = True

    for pid_from, pid_to in pairs:
        p_from = paradigms[pid_from]
        p_to = paradigms[pid_to]

        print(f"-" * 50)
        print(f"近傍ペア: {pid_from} → {pid_to}")
        print(f"-" * 50)

        # Step 1: P フェーズ終了時の推定 O_P
        o_p = compute_estimated_o(p_from, questions, ps_values)

        # P フェーズで回答済みの質問 ID
        qp_from = derive_qp(questions, p_from)
        answered_ids = {q.id for q in qp_from}

        print(f"  |O_P| = {len(o_p)} ({pid_from} 全質問回答後)")

        # Step 2: Consistent(O_P, P') と Anomaly(O_P, P')
        consistent = {d for d, v in o_p.items()
                      if p_to.prediction(d) is not None and p_to.prediction(d) == v}
        anomaly_origins = {d for d, v in o_p.items()
                          if p_to.prediction(d) is not None and p_to.prediction(d) != v}
        print(f"  Consistent(O_P, {pid_to}): {len(consistent)}個")
        if consistent:
            c_list = sorted(consistent)
            if len(c_list) <= 10:
                print(f"    {c_list}")
            else:
                print(f"    {c_list[:10]} ... (他{len(c_list)-10}個)")
        print(f"  Anomaly(O_P, {pid_to}): {len(anomaly_origins)}個")
        if anomaly_origins:
            a_list = sorted(anomaly_origins)
            if len(a_list) <= 10:
                print(f"    {a_list}")
            else:
                print(f"    {a_list[:10]} ... (他{len(a_list)-10}個)")

        # Step 3: 到達可能ターゲット
        consistent_reach = _reachable(consistent, p_to)
        anomaly_reach = _reachable(anomaly_origins, p_to)
        t_reach = consistent_reach | anomaly_reach
        print(f"  到達可能ターゲット (T_reach): {len(t_reach)}個")
        print(f"    Consistent経由: {len(consistent_reach)}個, Anomaly経由: {len(anomaly_reach)}個")
        if t_reach:
            t_list = sorted(t_reach)
            if len(t_list) <= 10:
                print(f"    {t_list}")
            else:
                print(f"    {t_list[:10]} ... (他{len(t_list)-10}個)")

        # Step 4: 質問カバレッジ
        covered, uncovered = check_question_coverage(
            consistent_reach, anomaly_reach, p_to, questions, answered_ids,
        )

        if covered:
            print(f"  カバー済みターゲット: {len(covered)}個")
            for t, qids in sorted(covered.items()):
                print(f"    {t} ← {qids}")

        if uncovered:
            print(f"  未カバーターゲット: {sorted(uncovered)}")

        if not t_reach:
            print(f"  警告: Consistent/Anomaly からの到達可能ターゲットが空")
            print(f"  → R({pid_to}) に Consistent/Anomaly からの関係が不足")
            print(f"  結果: NG")
            all_ok = False
        elif uncovered:
            print(f"  結果: NG (未カバーターゲットあり)")
            all_ok = False
        else:
            print(f"  結果: OK")

        print()

    # サマリ
    print("=" * 65)
    print(f"総合結果: {'OK — 全近傍ペアで同化接続性あり' if all_ok else 'NG — 接続性不足あり'}")
    print("=" * 65)


if __name__ == "__main__":
    main()

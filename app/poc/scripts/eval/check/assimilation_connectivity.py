"""同化接続性検証スクリプト（S1 Step 2 対応）。

各遷移 P_i → P_{i+1} について:
  1. P_i フェーズの全質問回答後の推定 O_i を計算
  2. 同化起点 = {d ∈ O_i : P_pred(P_{i+1}, d) ∈ {0,1} かつ P_pred(P_{i+1}, d) == O_i[d]}
  3. R(P_{i+1}) で同化起点から到達可能なターゲット記述素 T_reach を計算
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

from common import load_data  # noqa: E402
from engine import compute_effect, init_game, select_shift_target  # noqa: E402

# shift_direction の helpers を再利用
sys.path.insert(0, str(Path(__file__).resolve().parent))
from shift_direction import compute_main_path, derive_qp, classify_questions  # noqa: E402


def compute_estimated_o(
    paradigm,
    questions,
    ps_values,
):
    """P_i フェーズの全質問を回答した推定 O_i を計算する。"""
    qp = derive_qp(questions, paradigm)
    o_i = dict(ps_values)
    for q in qp:
        if q.correct_answer == "irrelevant":
            continue
        eff = compute_effect(q)
        for d, v in eff:
            o_i[d] = v
    return o_i


def compute_assimilation_origins(o_i, paradigm_next):
    """同化起点を特定する。

    {d ∈ O_i : P_pred(P_{i+1}, d) ∈ {0,1} かつ P_pred(P_{i+1}, d) == O_i[d]}
    """
    origins = set()
    for d, v in o_i.items():
        pred = paradigm_next.prediction(d)
        if pred is not None and pred == v:
            origins.add(d)
    return origins


def compute_reachable_targets(origins, paradigm_next):
    """R(P_{i+1}) で同化起点から到達可能なターゲット記述素を計算する。"""
    reachable = set()
    frontier = set(origins)
    visited = set()

    while frontier:
        current = frontier.pop()
        if current in visited:
            continue
        visited.add(current)
        for src, tgt, w in paradigm_next.relations:
            if src == current and tgt not in visited:
                reachable.add(tgt)
                frontier.add(tgt)

    return reachable


def check_question_coverage(t_reach, paradigm_next, questions, answered_ids):
    """T_reach の各 t について、t を effect に含む未回答質問の存在を確認する。

    Returns:
        covered: {t: [q.id, ...]} - カバーされたターゲット記述素と質問
        uncovered: set - カバーされないターゲット記述素
    """
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
                    # effect(q)[t] の値が P_pred(P_{i+1}, t) と一致するか確認
                    pred = paradigm_next.prediction(t)
                    if pred is not None and pred == v:
                        covering_qs.append(q.id)
                    break
        if covering_qs:
            covered[t] = covering_qs
        else:
            uncovered.add(t)

    return covered, uncovered


def main():
    paradigms, questions, all_ids, ps_values, init_pid = load_data()

    main_path = compute_main_path(init_pid, paradigms, questions)

    print("=" * 65)
    print("同化接続性検証 (S1 Step 2)")
    print("=" * 65)
    print(f"メインパス: {' → '.join(main_path)}")
    print()

    all_ok = True

    for i in range(len(main_path) - 1):
        pid_from = main_path[i]
        pid_to = main_path[i + 1]
        p_from = paradigms[pid_from]
        p_to = paradigms[pid_to]

        print(f"-" * 50)
        print(f"遷移: {pid_from} → {pid_to}")
        print(f"-" * 50)

        # Step 1: P_i フェーズ終了時の推定 O_i
        o_i = compute_estimated_o(p_from, questions, ps_values)

        # P_i フェーズで回答済みの質問 ID
        qp_from = derive_qp(questions, p_from)
        answered_ids = {q.id for q in qp_from}

        print(f"  |O_i| = {len(o_i)} (P_{pid_from} 全質問回答後)")

        # Step 2: 同化起点
        origins = compute_assimilation_origins(o_i, p_to)
        print(f"  同化起点: {len(origins)}個")
        if origins:
            origin_list = sorted(origins)
            if len(origin_list) <= 10:
                print(f"    {origin_list}")
            else:
                print(f"    {origin_list[:10]} ... (他{len(origin_list)-10}個)")

        # Step 3: 到達可能ターゲット
        t_reach = compute_reachable_targets(origins, p_to)
        print(f"  到達可能ターゲット (T_reach): {len(t_reach)}個")
        if t_reach:
            t_list = sorted(t_reach)
            if len(t_list) <= 10:
                print(f"    {t_list}")
            else:
                print(f"    {t_list[:10]} ... (他{len(t_list)-10}個)")

        # Step 4: 質問カバレッジ
        covered, uncovered = check_question_coverage(
            t_reach, p_to, questions, answered_ids,
        )

        if covered:
            print(f"  カバー済みターゲット: {len(covered)}個")
            for t, qids in sorted(covered.items()):
                print(f"    {t} ← {qids}")

        if uncovered:
            print(f"  未カバーターゲット: {sorted(uncovered)}")

        if not t_reach:
            print(f"  警告: 同化起点からの到達可能ターゲットが空")
            print(f"  → R({pid_to}) に同化起点からの関係が不足")
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
    print(f"総合結果: {'OK — 全遷移で同化接続性あり' if all_ok else 'NG — 接続性不足あり'}")
    print("=" * 65)


if __name__ == "__main__":
    main()

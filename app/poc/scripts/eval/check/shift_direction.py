"""シフト方向検証スクリプト（L2-5）。

到達パス（L2-0）の各遷移 P_i → P_{i+1} について:
  1. P_i フェーズの質問を順に回答するシミュレーション
  2. 各回答後に select_shift_target（近傍 + tension strict < + resolve >= N）を適用
  3. 選択結果が P_{i+1} と一致することを検証

ゲーム状態は到達パス全体でチェーンする（前パラダイムの蓄積を引き継ぐ）。

使い方:
  python shift_direction.py                       # turtle_soup.json
  python shift_direction.py --data bar_man.json   # bar_man.json
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from common import (  # noqa: E402
    load_data,
    derive_qp,
    classify_questions,
    compute_reachability_path,
)
from engine import (  # noqa: E402
    compute_effect,
    init_game,
    open_questions,
    update,
    tension,
    select_shift_target,
)


# ── simulation ───────────────────────────────────────


def simulate_shift_direction(
    pid_from: str,
    pid_to: str,
    paradigms: dict,
    questions: list,
    state,
    current_open: list,
) -> dict:
    """P_from フェーズの質問を順に回答し、シフト時点で select_shift_target を適用する。

    state と current_open は呼び出し元から引き継ぐ（チェーン方式）。
    state は破壊的に更新されるため、呼び出し後に次の遷移でそのまま使える。

    Returns:
        {
            "shift_triggered": bool,
            "shift_step": int | None,
            "tension_at_shift": int | None,
            "shift_threshold": int | None,
            "selected_pid": str | None,
            "candidate_details": [(pid, tension, attention, resolve, meets_threshold)],
            "target_matches": bool,
            "total_steps": int,
        }
    """
    p_from = paradigms[pid_from]

    # P_from がアクティブな状態を設定
    state.p_current = pid_from

    # Q(P_from) の質問を分類
    qp = derive_qp(questions, p_from)
    safe_qs, anomaly_qs = classify_questions(qp, p_from)

    # current_open を更新: Q(P_from) のうち未回答の質問を open_questions で判定
    newly_opened = open_questions(state, questions, paradigms)
    for oq in newly_opened:
        if oq not in current_open:
            current_open.append(oq)

    # Q(P_from) の safe 質問のうち未回答をキューに投入
    anomaly_ids = {q.id for q in anomaly_qs}
    answer_queue = [q for q in qp if q.id not in state.answered and q.id not in anomaly_ids]
    queued_ids = {q.id for q in answer_queue}

    # anomaly 質問のうち既にオープンしているものもキューに追加
    for q in anomaly_qs:
        if q.id not in state.answered and q in current_open and q.id not in queued_ids:
            answer_queue.append(q)
            queued_ids.add(q.id)

    result = {
        "shift_triggered": False,
        "shift_step": None,
        "tension_at_shift": None,
        "shift_threshold": p_from.shift_threshold,
        "selected_pid": None,
        "candidate_details": [],
        "target_matches": False,
        "total_steps": 0,
    }

    step = 0
    while answer_queue:
        q = answer_queue.pop(0)
        if q.id in state.answered:
            continue

        step += 1

        state, current_open = update(
            state, q, paradigms, questions, current_open,
        )

        # シフト判定: select_shift_target で候補が見つかるかチェック
        if not result["shift_triggered"]:
            current_tension = tension(state.o, p_from)
            selected = select_shift_target(state.o, p_from, paradigms)
            if selected is not None:
                result["shift_triggered"] = True
                result["shift_step"] = step
                result["tension_at_shift"] = current_tension
                result["selected_pid"] = selected

                # 候補詳細を計算（表示用）
                anomalies = {
                    d for d, pred in p_from.p_pred.items()
                    if d in state.o and pred != state.o[d]
                }
                details = []
                for pid, p in paradigms.items():
                    if pid == pid_from:
                        continue
                    if pid not in p_from.neighbors:
                        continue
                    t = tension(state.o, p)
                    if t >= current_tension:
                        continue
                    att = len({d for d in anomalies if d in p.p_pred})
                    res = len({d for d in anomalies
                               if p.prediction(d) is not None and p.prediction(d) == state.o[d]})
                    meets_th = p.shift_threshold is None or res >= p.shift_threshold
                    details.append((pid, t, att, res, meets_th))
                details.sort(key=lambda x: (-x[3], -x[2], x[0]))
                result["candidate_details"] = details

                result["target_matches"] = selected == pid_to

        # 新規オープンの質問をキューに追加
        for oq in current_open:
            if oq.id not in queued_ids and oq.id not in state.answered:
                answer_queue.append(oq)
                queued_ids.add(oq.id)

    result["total_steps"] = step
    return result


# ── main ─────────────────────────────────────────────


def main():
    paradigms, questions, all_ids, ps_values, init_pid = load_data()

    # 到達パスを導出（L2-0 と同じ計算）
    reach_path = compute_reachability_path(init_pid, paradigms, questions)

    print("=" * 65)
    print("シフト方向検証 (L2-5)")
    print("=" * 65)
    print(f"到達パス: {' → '.join(reach_path)}")
    print()

    # ゲーム状態を初期化し、到達パス全体でチェーンする
    state = init_game(ps_values, paradigms, init_pid, all_ids)
    current_open = open_questions(state, questions, paradigms)

    all_ok = True

    for i in range(len(reach_path) - 1):
        pid_from = reach_path[i]
        pid_to = reach_path[i + 1]
        p_from = paradigms[pid_from]

        print(f"-" * 50)
        print(f"遷移: {pid_from} → {pid_to}")
        print(f"-" * 50)

        # Q(P) サイズ
        qp = derive_qp(questions, p_from)
        safe_qs, anomaly_qs = classify_questions(qp, p_from)
        nb_str = ", ".join(sorted(p_from.neighbors)) if p_from.neighbors else "–"
        print(f"  |Q({pid_from})| = {len(qp)} (safe: {len(safe_qs)}, anomaly: {len(anomaly_qs)})")
        print(f"  neighbors({pid_from}) = [{nb_str}]")
        print(f"  shift_threshold({pid_from}) = {p_from.shift_threshold}")
        print(f"  |O| at start = {len(state.o)}")

        result = simulate_shift_direction(
            pid_from, pid_to, paradigms, questions, state, current_open,
        )

        print(f"  回答ステップ数: {result['total_steps']}")

        if not result["shift_triggered"]:
            print(f"  シフト未発動: 近傍候補が3条件（近傍・tension<・resolve>=N）を満たさなかった")
            print(f"  結果: NG")
            all_ok = False
        else:
            print(f"  シフト発動: step {result['shift_step']}, "
                  f"tension={result['tension_at_shift']}")

            if result["candidate_details"]:
                print(f"  候補（近傍 + resolve 閾値）:")
                for item in result["candidate_details"]:
                    pid, t, att, res, meets_th = item
                    marker = " ★" if pid == result["selected_pid"] else ""
                    target = " (想定シフト先)" if pid == pid_to else ""
                    th_flag = "" if meets_th else " [resolve<N]"
                    print(f"    {pid}: tension={t} att={att} res={res}{th_flag}{marker}{target}")
            else:
                print(f"  候補パラダイムなし")

            if result["target_matches"]:
                print(f"  選択 = {result['selected_pid']} = 想定シフト先: OK")
            elif result["selected_pid"] is not None:
                print(f"  選択 = {result['selected_pid']} ≠ 想定シフト先 {pid_to}: NG")
                all_ok = False
            else:
                print(f"  候補なし ≠ 想定シフト先 {pid_to}: NG")
                all_ok = False

        print()

    # サマリ
    print("=" * 65)
    print(f"総合結果: {'OK — 全遷移でシフト方向一致' if all_ok else 'NG — 不一致あり'}")
    print("=" * 65)


if __name__ == "__main__":
    main()

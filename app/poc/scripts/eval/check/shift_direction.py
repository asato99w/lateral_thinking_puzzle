"""シフト方向検証スクリプト。

各メインパス遷移 P_i → P_{i+1} について:
  1. P_i フェーズの質問を順に回答するシミュレーション
  2. 各回答後に select_shift_target（近傍 + tension strict < + resolve >= N）を適用
  3. 選択結果が P_{i+1} と一致することを検証

使い方:
  python shift_direction.py                       # turtle_soup.json
  python shift_direction.py --data bar_man.json   # bar_man.json
"""
from __future__ import annotations

import copy
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from common import load_data  # noqa: E402
from engine import (  # noqa: E402
    compute_effect,
    init_game,
    open_questions,
    update,
    tension,
    alignment,
    explained_o,
    select_shift_target,
)


# ── helpers ──────────────────────────────────────────


def derive_qp(questions, paradigm):
    """p_pred(P) から Q(P) を導出する。"""
    qp = []
    for q in questions:
        if q.correct_answer == "irrelevant":
            continue
        eff = compute_effect(q)
        eff_ds = {d for d, v in eff}
        if eff_ds & set(paradigm.p_pred.keys()):
            qp.append(q)
    return qp


def classify_questions(questions, paradigm):
    """質問を safe / anomaly に分類する。"""
    safe, anomaly = [], []
    for q in questions:
        eff = compute_effect(q)
        if q.correct_answer == "irrelevant":
            safe.append(q)
            continue
        has_anomaly = False
        for d_id, v in eff:
            pred = paradigm.prediction(d_id)
            if pred is not None and pred != v:
                has_anomaly = True
                break
        if has_anomaly:
            anomaly.append(q)
        else:
            safe.append(q)
    return safe, anomaly


def compute_main_path(init_pid, paradigms, questions):
    """O* ベースの遷移グラフからメインパスを導出する（最小緩和原理）。"""
    o_star = {}
    for q in questions:
        if q.correct_answer == "irrelevant":
            continue
        eff = compute_effect(q)
        for d_id, v in eff:
            o_star[d_id] = v

    path = [init_pid]
    visited = {init_pid}
    current = init_pid
    while True:
        p_cur = paradigms[current]
        nxt = select_shift_target(o_star, p_cur, paradigms)
        if nxt is None or nxt in visited:
            break
        path.append(nxt)
        visited.add(nxt)
        current = nxt

    return path


# ── simulation ───────────────────────────────────────


def simulate_shift_direction(
    pid_from: str,
    pid_to: str,
    paradigms: dict,
    questions: list,
    all_ids: list,
    ps_values: dict,
    init_pid: str,
) -> dict:
    """P_from フェーズの質問を順に回答し、シフト時点で select_shift_target を適用する。

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

    # ゲーム初期化
    state = init_game(ps_values, paradigms, init_pid, all_ids)

    # P_from がアクティブな状態を想定
    state.p_current = pid_from

    # Q(P_from) の質問を分類
    qp = derive_qp(questions, p_from)
    safe_qs, anomaly_qs = classify_questions(qp, p_from)

    # シミュレーション用: Q(P_from) の safe 質問を初期オープンとする
    # （データ駆動の init_questions に依存しない独立したシミュレーション）
    current_open = list(safe_qs)
    anomaly_ids = {q.id for q in anomaly_qs}

    # 回答キュー: safe 質問から開始
    answer_queue = [q for q in current_open if q.id not in anomaly_ids]
    queued_ids = {q.id for q in answer_queue}

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

        # 新規オープンの anomaly 質問をキューに追加
        for oq in current_open:
            if oq.id not in queued_ids and oq.id not in state.answered:
                answer_queue.append(oq)
                queued_ids.add(oq.id)

    result["total_steps"] = step
    return result


# ── main ─────────────────────────────────────────────


def main():
    paradigms, questions, all_ids, ps_values, init_pid = load_data()

    # メインパスを導出
    main_path = compute_main_path(init_pid, paradigms, questions)

    print("=" * 65)
    print("シフト方向検証")
    print("=" * 65)
    print(f"メインパス: {' → '.join(main_path)}")
    print()

    all_ok = True

    for i in range(len(main_path) - 1):
        pid_from = main_path[i]
        pid_to = main_path[i + 1]
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

        result = simulate_shift_direction(
            pid_from, pid_to, paradigms, questions, all_ids, ps_values, init_pid,
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

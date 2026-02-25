"""シフト方向検証スクリプト。

統合アルゴリズム Phase 4d の実装。
各メインパス遷移 P_i → P_{i+1} について:
  1. P_i フェーズの質問を順に回答するシミュレーション
  2. tension > threshold 時点での alignment を全候補に対して計算
  3. P_{i+1} が argmax であることを検証

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
    init_questions,
    open_questions,
    update,
    tension,
    alignment,
    explained_o,
)


# ── helpers ──────────────────────────────────────────


def derive_qp(questions, paradigm):
    """conceivable(P) から Q(P) を導出する。"""
    qp = []
    for q in questions:
        if q.correct_answer == "irrelevant":
            continue
        eff = compute_effect(q)
        eff_ds = {d for d, v in eff}
        if eff_ds & paradigm.conceivable:
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


def compute_main_path(init_pid, paradigms, questions, all_ids):
    """O* ベースの遷移グラフからメインパスを導出する。"""
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
        cur_eo = explained_o(o_star, p_cur)

        # 仮想 H: P に完全同化
        h_pi = {d: 0.5 for d in all_ids}
        for d, pred_val in p_cur.p_pred.items():
            h_pi[d] = float(pred_val)

        candidates = []
        for pid in paradigms:
            if pid == current:
                continue
            if explained_o(o_star, paradigms[pid]) > cur_eo:
                a = alignment(h_pi, paradigms[pid])
                candidates.append((pid, a))

        if not candidates:
            break
        candidates.sort(key=lambda x: -x[1])
        nxt = candidates[0][0]
        if nxt in visited:
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
    """P_from フェーズの質問を順に回答し、シフト時点の alignment を計算する。

    Returns:
        {
            "shift_triggered": bool,
            "shift_step": int | None,
            "tension_at_shift": int | None,
            "threshold": int | None,
            "alignment_scores": [(pid, alignment)] sorted desc,
            "argmax_pid": str | None,
            "target_matches": bool,
            "margin": float | None,
            "total_steps": int,
        }
    """
    p_from = paradigms[pid_from]

    # ゲーム初期化
    state = init_game(ps_values, paradigms, init_pid, all_ids)

    # P_from がアクティブな状態を想定
    # init_pid から pid_from までの遷移をシミュレーションするのは複雑なため、
    # P_from の conceivable に基づく質問のみで簡易シミュレーションを行う
    state.p_current = pid_from

    # Q(P_from) の質問を分類
    qp = derive_qp(questions, p_from)
    safe_qs, anomaly_qs = classify_questions(qp, p_from)

    # safe 質問から初期オープンを構成
    current_open = init_questions(p_from, questions, state.o)
    anomaly_ids = {q.id for q in anomaly_qs}

    # 回答キュー: safe 質問から開始
    answer_queue = [q for q in current_open if q.id not in anomaly_ids]
    queued_ids = {q.id for q in answer_queue}

    result = {
        "shift_triggered": False,
        "shift_step": None,
        "tension_at_shift": None,
        "threshold": p_from.threshold,
        "alignment_scores": [],
        "argmax_pid": None,
        "target_matches": False,
        "margin": None,
        "total_steps": 0,
    }

    step = 0
    while answer_queue:
        q = answer_queue.pop(0)
        if q.id in state.answered:
            continue

        step += 1

        # 回答前の状態を保持
        p_before = state.p_current

        state, current_open = update(
            state, q, paradigms, questions, current_open,
        )

        # tension チェック（P_from に対して）
        current_tension = tension(state.o, p_from)
        if (p_from.threshold is not None
                and current_tension > p_from.threshold
                and not result["shift_triggered"]):
            result["shift_triggered"] = True
            result["shift_step"] = step
            result["tension_at_shift"] = current_tension

            # シフト時点の alignment を計算
            cur_eo = explained_o(state.o, p_from)
            scores = []
            for pid in paradigms:
                if pid == pid_from:
                    continue
                p = paradigms[pid]
                if explained_o(state.o, p) > cur_eo:
                    a = alignment(state.h, p)
                    scores.append((pid, a))
            scores.sort(key=lambda x: -x[1])
            result["alignment_scores"] = scores

            if scores:
                result["argmax_pid"] = scores[0][0]
                result["target_matches"] = scores[0][0] == pid_to
                if len(scores) >= 2:
                    result["margin"] = scores[0][1] - scores[1][1]
                else:
                    result["margin"] = scores[0][1]

            # シフト発動後も続行して全ステップ数を記録

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
    main_path = compute_main_path(init_pid, paradigms, questions, all_ids)

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
        print(f"  |Q({pid_from})| = {len(qp)} (safe: {len(safe_qs)}, anomaly: {len(anomaly_qs)})")
        print(f"  threshold({pid_from}) = {p_from.threshold}")

        result = simulate_shift_direction(
            pid_from, pid_to, paradigms, questions, all_ids, ps_values, init_pid,
        )

        print(f"  回答ステップ数: {result['total_steps']}")

        if not result["shift_triggered"]:
            print(f"  シフト未発動: tension が threshold を超えなかった")
            print(f"  結果: NG")
            all_ok = False
        else:
            print(f"  シフト発動: step {result['shift_step']}, "
                  f"tension={result['tension_at_shift']}")

            if result["alignment_scores"]:
                print(f"  alignment スコア（シフト時点）:")
                for pid, a in result["alignment_scores"]:
                    marker = " ★" if pid == result["argmax_pid"] else ""
                    target = " (想定シフト先)" if pid == pid_to else ""
                    print(f"    {pid}: {a:.4f}{marker}{target}")
            else:
                print(f"  候補パラダイムなし")

            if result["target_matches"]:
                print(f"  argmax = {result['argmax_pid']} = 想定シフト先: OK")
                if result["margin"] is not None:
                    margin_status = "OK" if result["margin"] > 0.05 else "注意（マージン小）"
                    print(f"  マージン: {result['margin']:.4f} ({margin_status})")
            else:
                print(f"  argmax = {result['argmax_pid']} ≠ 想定シフト先 {pid_to}: NG")
                all_ok = False

        print()

    # サマリ
    print("=" * 65)
    print(f"総合結果: {'OK — 全遷移でシフト方向一致' if all_ok else 'NG — 不一致あり'}")
    print("=" * 65)


if __name__ == "__main__":
    main()

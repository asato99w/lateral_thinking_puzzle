"""パラダイムシフトの質を計測する。

シフト発生時の決定性と影響度を分析する:
- alignment margin: 新パラダイムの alignment - 旧パラダイムの alignment
- explained_o gain: Δexplained_o（新 - 旧）
- H disruption: シフトによるH変化量（同化再適用による）
- tension解消率: シフト後 tension / シフト前 tension
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from common import load_data  # noqa: E402
from engine import (  # noqa: E402
    init_game,
    init_questions,
    compute_effect,
    tension,
    alignment,
    explained_o,
    open_questions,
    _assimilate_descriptor,
    _assimilate_from_paradigm,
    EPSILON,
)


def _h_l1(h_before: dict[str, float], h_after: dict[str, float]) -> float:
    """H ベクトル間の L1 距離。"""
    total = 0.0
    all_keys = set(h_before) | set(h_after)
    for d in all_keys:
        total += abs(h_after.get(d, 0.5) - h_before.get(d, 0.5))
    return total


def _count_changed(h_before: dict[str, float], h_after: dict[str, float]) -> int:
    """変化した記述素の数。"""
    count = 0
    all_keys = set(h_before) | set(h_after)
    for d in all_keys:
        if abs(h_after.get(d, 0.5) - h_before.get(d, 0.5)) > 0.001:
            count += 1
    return count


def update_with_shift_tracking(state, question, paradigms, all_questions, current_open):
    """update() の処理を再現し、シフト発生時の前後情報を詳細に記録する。

    返り値: (state, new_open, shift_info)
    shift_info: シフトなし → None
                シフトあり → dict with keys:
                  old_pid, new_pid, step_qid,
                  old_alignment, new_alignment, margin,
                  old_explained, new_explained, gain,
                  h_disruption, h_changed_count,
                  old_tension, new_tension, tension_resolution_rate
    """
    # === Phase 1: 直接更新 ===
    eff = compute_effect(question)
    if question.correct_answer == "irrelevant":
        for d_id in eff:
            state.r.add(d_id)
    else:
        for d_id, v in eff:
            state.h[d_id] = float(v)
            state.o[d_id] = v

    state.answered.add(question.id)

    # === Phase 2: 同化 ===
    p_current = paradigms[state.p_current]
    if question.correct_answer != "irrelevant":
        for d_id, v in eff:
            pred = p_current.prediction(d_id)
            if pred is not None and pred == v:
                _assimilate_descriptor(state.h, d_id, p_current)
        for d, v in state.o.items():
            state.h[d] = float(v)

    # === Phase 3: パラダイムシフト判定（詳細記録付き）===
    shift_info = None
    current_tension = tension(state.o, p_current)
    if p_current.threshold is not None and current_tension > p_current.threshold:
        current_explained = explained_o(state.o, p_current)
        candidates = [
            p_id for p_id in paradigms
            if p_id != state.p_current
            and explained_o(state.o, paradigms[p_id]) > current_explained
        ]

        if candidates:
            best_id = candidates[0]
            best_score = alignment(state.h, paradigms[candidates[0]])
            for p_id in candidates[1:]:
                score = alignment(state.h, paradigms[p_id])
                if score > best_score:
                    best_score = score
                    best_id = p_id

            # シフト前の状態を記録
            old_pid = state.p_current
            old_alignment = alignment(state.h, p_current)
            old_explained = current_explained
            old_tension = current_tension
            h_before_shift = dict(state.h)

            # シフト実行
            state.p_current = best_id
            p_new = paradigms[best_id]
            _assimilate_from_paradigm(state.h, state.o, p_new)

            # シフト後の状態を記録
            new_alignment = alignment(state.h, p_new)
            new_explained = explained_o(state.o, p_new)
            new_tension = tension(state.o, p_new)
            h_disruption = _h_l1(h_before_shift, state.h)
            h_changed_count = _count_changed(h_before_shift, state.h)

            tension_resolution = 0.0
            if old_tension > 0:
                tension_resolution = (old_tension - new_tension) / old_tension * 100

            shift_info = {
                "old_pid": old_pid,
                "new_pid": best_id,
                "old_p_name": p_current.name,
                "new_p_name": p_new.name,
                "old_alignment": old_alignment,
                "new_alignment": new_alignment,
                "margin": new_alignment - old_alignment,
                "old_explained": old_explained,
                "new_explained": new_explained,
                "gain": new_explained - old_explained,
                "h_disruption": h_disruption,
                "h_changed_count": h_changed_count,
                "old_tension": old_tension,
                "new_tension": new_tension,
                "tension_resolution_rate": tension_resolution,
            }

    # Step 4: オープン更新
    remaining = [q for q in current_open if q.id != question.id]
    remaining_ids = {q.id for q in remaining}
    newly_opened = [
        q for q in open_questions(state, all_questions, paradigms)
        if q.id not in remaining_ids and q.id not in state.answered
    ]
    new_open = remaining + newly_opened

    return state, new_open, shift_info


def main():
    paradigms, questions, all_ids, ps_values, init_pid = load_data()

    state = init_game(ps_values, paradigms, init_pid, all_ids)
    p_init = paradigms[init_pid]
    current_open = init_questions(p_init, questions)

    print(f"初期パラダイム: {p_init.name}")
    print(f"初期オープン: {len(current_open)}問")
    print()

    shifts: list[dict] = []
    step = 0

    all_questions_to_process = list(current_open)

    while all_questions_to_process or current_open:
        if not all_questions_to_process:
            all_questions_to_process = list(current_open)
            if not all_questions_to_process:
                break

        q = all_questions_to_process.pop(0)
        if q.id in state.answered:
            continue

        step += 1

        state, current_open, shift_info = update_with_shift_tracking(
            state, q, paradigms, questions, current_open
        )

        if shift_info:
            shift_info["step"] = step
            shift_info["question_id"] = q.id
            shifts.append(shift_info)

        # 新たにオープンした質問を処理キューに追加
        existing_ids = {qq.id for qq in all_questions_to_process}
        for qq in current_open:
            if qq.id not in existing_ids and qq.id not in state.answered:
                all_questions_to_process.append(qq)
                existing_ids.add(qq.id)

    print(f"総ステップ: {step}")
    print(f"シフト発生: {len(shifts)}回")
    print()

    if not shifts:
        print("パラダイムシフトは発生しませんでした。")
        return

    for i, s in enumerate(shifts, 1):
        print(f"=== シフト {i}: {s['old_pid']} → {s['new_pid']} "
              f"(step {s['step']}, {s['question_id']}) ===")
        print(f"  {s['old_p_name']} → {s['new_p_name']}")
        print(f"  alignment: {s['old_alignment']:.4f} → {s['new_alignment']:.4f} "
              f"(margin={s['margin']:+.4f})")
        print(f"  explained_o: {s['old_explained']} → {s['new_explained']} "
              f"(gain={s['gain']:+d})")
        print(f"  H disruption: ΣΔH={s['h_disruption']:.2f} "
              f"({s['h_changed_count']}記述素が変化)")
        print(f"  tension: {s['old_tension']} → {s['new_tension']} "
              f"(解消率={s['tension_resolution_rate']:.0f}%)")
        print()

    # サマリ
    if len(shifts) > 1:
        print("--- サマリ ---")
        avg_margin = sum(s["margin"] for s in shifts) / len(shifts)
        avg_disruption = sum(s["h_disruption"] for s in shifts) / len(shifts)
        avg_resolution = sum(s["tension_resolution_rate"] for s in shifts) / len(shifts)
        print(f"平均 margin: {avg_margin:+.4f}")
        print(f"平均 H disruption: {avg_disruption:.2f}")
        print(f"平均 tension解消率: {avg_resolution:.0f}%")


if __name__ == "__main__":
    main()

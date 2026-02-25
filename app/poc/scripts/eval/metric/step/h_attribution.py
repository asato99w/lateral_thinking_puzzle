"""H変化の帰属分析。

各ステップのH値変化を3つの原因に帰属する:
- 直接観測: update() の Step 1 で O に追加 → H = v
- 同化: _assimilate_descriptor による伝播 → H が relations 経由で変化
- パラダイムシフト: _assimilate_from_paradigm による一括再同化 → H が大幅変化

update() を段階的にシミュレートし、各段階の前後でH差分を取る。
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


def _h_delta(h_before: dict[str, float], h_after: dict[str, float]) -> float:
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


def simulate_update_phases(state, question, paradigms, all_questions, current_open):
    """update() を3段階に分解してH差分を計測する。

    返り値: (state, new_open, direct_delta, assimil_delta, shift_delta,
             direct_count, assimil_count, shift_count, shifted)
    """
    from copy import deepcopy

    h_0 = dict(state.h)

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
    h_1 = dict(state.h)

    # === Phase 2: 同化 ===
    p_current = paradigms[state.p_current]
    if question.correct_answer != "irrelevant":
        for d_id, v in eff:
            pred = p_current.prediction(d_id)
            if pred is not None and pred == v:
                _assimilate_descriptor(state.h, d_id, p_current)
        # 観測済み記述素の H は O の値を維持する
        for d, v in state.o.items():
            state.h[d] = float(v)

    h_2 = dict(state.h)

    # === Phase 3: パラダイムシフト判定 ===
    shifted = False
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
            state.p_current = best_id
            p_new = paradigms[best_id]
            _assimilate_from_paradigm(state.h, state.o, p_new)
            shifted = True

    h_3 = dict(state.h)

    # Step 4: オープン更新
    remaining = [q for q in current_open if q.id != question.id]
    remaining_ids = {q.id for q in remaining}
    newly_opened = [
        q for q in open_questions(state, all_questions, paradigms)
        if q.id not in remaining_ids and q.id not in state.answered
    ]
    new_open = remaining + newly_opened

    direct_delta = _h_delta(h_0, h_1)
    assimil_delta = _h_delta(h_1, h_2)
    shift_delta = _h_delta(h_2, h_3)
    direct_count = _count_changed(h_0, h_1)
    assimil_count = _count_changed(h_1, h_2)
    shift_count = _count_changed(h_2, h_3)

    return (state, new_open,
            direct_delta, assimil_delta, shift_delta,
            direct_count, assimil_count, shift_count, shifted)


def main():
    paradigms, questions, all_ids, ps_values, init_pid = load_data()

    state = init_game(ps_values, paradigms, init_pid, all_ids)
    p_init = paradigms[init_pid]
    current_open = init_questions(p_init, questions)

    print(f"初期パラダイム: {p_init.name}")
    print(f"初期オープン: {len(current_open)}問")
    print()

    header = (
        f"{'Step':>4}  {'質問ID':<12} "
        f"{'直接':>5} {'同化':>5} {'シフト':>6}  {'合計ΔH':>7}"
    )
    print(header)
    print("-" * len(header))

    total_direct = 0.0
    total_assimil = 0.0
    total_shift = 0.0
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

        (state, current_open,
         dd, ad, sd,
         dc, ac, sc, shifted) = simulate_update_phases(
            state, q, paradigms, questions, current_open
        )

        total = dd + ad + sd
        total_direct += dd
        total_assimil += ad
        total_shift += sd

        shift_mark = " *SHIFT*" if shifted else ""
        print(
            f"{step:>4}  {q.id + '(' + q.correct_answer + ')':<12} "
            f"{dc:>5} {ac:>5} {sc:>6}  "
            f"Σ={total:.2f}{shift_mark}"
        )

        # 新たにオープンした質問を処理キューに追加
        existing_ids = {qq.id for qq in all_questions_to_process}
        for qq in current_open:
            if qq.id not in existing_ids and qq.id not in state.answered:
                all_questions_to_process.append(qq)
                existing_ids.add(qq.id)

    print()
    print("-" * len(header))
    grand = total_direct + total_assimil + total_shift
    if grand > 0:
        print(
            f"全体: 直接={total_direct / grand * 100:.0f}% "
            f"同化={total_assimil / grand * 100:.0f}% "
            f"シフト={total_shift / grand * 100:.0f}%"
        )
        print(
            f"  (直接={total_direct:.2f}, "
            f"同化={total_assimil:.2f}, "
            f"シフト={total_shift:.2f}, "
            f"合計={grand:.2f})"
        )
    else:
        print("全体: H変化なし")


if __name__ == "__main__":
    main()

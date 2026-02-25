"""質問インパクトプロファイル。

各質問回答による状態変化の大きさを計測する:
- δ|O|: 新たに確定した観測数
- δtension: tension の変化
- δalignment: alignment の変化
- 新規オープン数
- H変化量の合計（L1ノルム）
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from common import load_data  # noqa: E402
from engine import (  # noqa: E402
    init_game,
    init_questions,
    update,
    tension,
    alignment,
)


def _h_l1(h_before: dict[str, float], h_after: dict[str, float]) -> float:
    """H ベクトル間の L1 距離。"""
    total = 0.0
    all_keys = set(h_before) | set(h_after)
    for d in all_keys:
        total += abs(h_after.get(d, 0.5) - h_before.get(d, 0.5))
    return total


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
        f"{'δ|O|':>5} {'δtension':>9} {'δalignment':>11} "
        f"{'新規open':>8} {'ΣΔH':>7}"
    )
    print(header)
    print("-" * len(header))

    step = 0
    impact_records: list[tuple[str, float]] = []  # (q_id, sum_dh)

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

        # 回答前の状態をスナップショット
        h_before = dict(state.h)
        o_size_before = len(state.o)
        p_cur = paradigms[state.p_current]
        t_before = tension(state.o, p_cur)
        a_before = alignment(state.h, p_cur)
        open_ids_before = {qq.id for qq in current_open}

        state, current_open = update(state, q, paradigms, questions, current_open)

        # 回答後の状態
        p_cur_after = paradigms[state.p_current]
        o_size_after = len(state.o)
        t_after = tension(state.o, p_cur_after)
        a_after = alignment(state.h, p_cur_after)
        open_ids_after = {qq.id for qq in current_open}
        newly_opened = open_ids_after - open_ids_before
        sum_dh = _h_l1(h_before, state.h)

        d_o = o_size_after - o_size_before
        d_t = t_after - t_before
        d_a = a_after - a_before

        impact_records.append((q.id, sum_dh))

        print(
            f"{step:>4}  {q.id + '(' + q.correct_answer + ')':<12} "
            f"{d_o:>5} {d_t:>+9} {d_a:>+11.4f} "
            f"{len(newly_opened):>8} {sum_dh:>7.2f}"
        )

        # 新たにオープンした質問を処理キューに追加
        existing_ids = {qq.id for qq in all_questions_to_process}
        for qq in current_open:
            if qq.id not in existing_ids and qq.id not in state.answered:
                all_questions_to_process.append(qq)
                existing_ids.add(qq.id)

    print()
    print("-" * len(header))

    # ピボット質問（ΣΔH上位3）
    if impact_records:
        sorted_records = sorted(impact_records, key=lambda x: x[1], reverse=True)
        top_n = min(3, len(sorted_records))
        pivot_ids = [f"{r[0]}(ΣΔH={r[1]:.2f})" for r in sorted_records[:top_n]]
        print(f"ピボット質問（ΣΔH上位{top_n}）: {', '.join(pivot_ids)}")


if __name__ == "__main__":
    main()

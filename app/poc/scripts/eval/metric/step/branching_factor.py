"""分岐度の推移を計測する。

各ステップでのオープン質問数（選択可能な質問数）を追跡し、
プレイヤーの選択余地がどう変化するかを可視化する。
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
)


def main():
    paradigms, questions, all_ids, ps_values, init_pid = load_data()

    state = init_game(ps_values, paradigms, init_pid, all_ids)
    p_init = paradigms[init_pid]
    current_open = init_questions(p_init, questions)

    print(f"初期パラダイム: {p_init.name}")
    print(f"初期オープン: {len(current_open)}問")
    print()

    header = f"{'Step':>4}  {'質問ID':<12} {'分岐度':>6}  {'新規開放':>8}  {'閉鎖':>4}"
    print(header)
    print("-" * len(header))

    branching_values: list[int] = []
    step = 0

    for q in list(current_open):
        step += 1
        open_ids_before = {qq.id for qq in current_open}
        bf_before = len(current_open)

        state, current_open = update(state, q, paradigms, questions, current_open)

        open_ids_after = {qq.id for qq in current_open}
        newly_opened = open_ids_after - open_ids_before
        closed = (open_ids_before - open_ids_after) - {q.id}

        bf_after = len(current_open)
        branching_values.append(bf_after)

        print(
            f"{step:>4}  {q.id + '(' + q.correct_answer + ')':<12} "
            f"{bf_after:>6}  "
            f"{'+' + str(len(newly_opened)):>8}  "
            f"{'-' + str(len(closed) + 1):>4}"
        )

    # 2巡目以降: current_open の残りを処理
    while current_open:
        q = current_open[0]
        step += 1
        open_ids_before = {qq.id for qq in current_open}
        bf_before = len(current_open)

        state, current_open = update(state, q, paradigms, questions, current_open)

        open_ids_after = {qq.id for qq in current_open}
        newly_opened = open_ids_after - open_ids_before
        closed = (open_ids_before - open_ids_after) - {q.id}

        bf_after = len(current_open)
        branching_values.append(bf_after)

        print(
            f"{step:>4}  {q.id + '(' + q.correct_answer + ')':<12} "
            f"{bf_after:>6}  "
            f"{'+' + str(len(newly_opened)):>8}  "
            f"{'-' + str(len(closed) + 1):>4}"
        )

    print()
    print("-" * len(header))
    if branching_values:
        mn = min(branching_values)
        mx = max(branching_values)
        mean = sum(branching_values) / len(branching_values)
        variance = sum((x - mean) ** 2 for x in branching_values) / len(branching_values)
        std = variance ** 0.5
        print(f"統計: min={mn}, max={mx}, mean={mean:.1f}, std={std:.1f}")
    else:
        print("統計: データなし")


if __name__ == "__main__":
    main()

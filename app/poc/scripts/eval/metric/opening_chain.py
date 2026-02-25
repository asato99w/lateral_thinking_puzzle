"""初期質問群の回答後に新たにオープンされる質問群を検証する。

init_questions で開く質問をすべて回答し、
その結果 open_questions で新たに開く質問群を表示する。
質問の提示順はスクリプトの恣意的な順（init_questions の返却順）。
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from common import load_data  # noqa: E402
from engine import (
    init_game,
    init_questions,
    update,
    open_questions,
    get_answer,
    compute_effect,
    tension,
    alignment,
)


def main():
    paradigms, questions, all_ids, ps_values, init_pid = load_data()

    state = init_game(ps_values, paradigms, init_pid, all_ids)
    p_init = paradigms[init_pid]
    current_open = init_questions(p_init, questions)

    print(f"パラダイム: {p_init.name} ({init_pid})")
    print(f"初期オープン: {len(current_open)} 問")
    print()

    # 初期質問群の一覧
    for q in current_open:
        eff = compute_effect(q)
        ans = q.correct_answer
        if ans == "irrelevant":
            eff_str = ", ".join(eff)
        else:
            eff_str = ", ".join(f"{d}={v}" for d, v in eff)
        print(f"  {q.id} [{ans:3s}] effect=[{eff_str}]  {q.text}")
    print()

    # 初期質問群をすべて回答
    for q in list(current_open):
        state, current_open = update(
            state, q, paradigms, questions, current_open,
        )

    # 結果
    p_cur = paradigms[state.p_current]
    t = tension(state.o, p_cur)
    a = alignment(state.h, p_cur)

    print(f"回答後: パラダイム={state.p_current}, tension={t}, alignment={a:.4f}")
    print(f"新たにオープン: {len(current_open)} 問")
    print()

    if current_open:
        for q in current_open:
            eff = compute_effect(q)
            ans = q.correct_answer
            if ans == "irrelevant":
                eff_str = ", ".join(eff)
            else:
                eff_str = ", ".join(f"{d}={v}" for d, v in eff)
            print(f"  {q.id} [{ans:3s}] effect=[{eff_str}]  {q.text}")
    else:
        print("  (なし)")


if __name__ == "__main__":
    main()

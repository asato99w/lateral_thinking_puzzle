"""H の波及を検証する。初期質問を逐次回答し、同化による H の変化と新規オープンを追跡する。"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from common import load_data  # noqa: E402
from engine import (
    init_game,
    init_questions,
    update,
    open_questions,
    compute_effect,
    EPSILON,
)


def main():
    paradigms, questions, all_ids, ps_values, init_pid = load_data()

    state = init_game(ps_values, paradigms, init_pid, all_ids)
    p_init = paradigms[init_pid]
    current_open = init_questions(p_init, questions)
    init_ids = {q.id for q in current_open}

    print(f"初期パラダイム: {p_init.name}")
    print(f"初期オープン: {len(current_open)}問")
    print()

    # 初期 H の状態（0.5 以外）
    h_moved_init = {d: v for d, v in state.h.items() if abs(v - 0.5) > 0.01}
    print(f"初期 H(≠0.5): {len(h_moved_init)}件")
    for d in sorted(h_moved_init):
        print(f"  H[{d}] = {h_moved_init[d]:.3f}")
    print()

    # 初期質問を逐次回答し、同化の効果を追跡
    print("逐次回答による H の波及:")
    print("-" * 60)

    for q in list(current_open):
        # 回答前の H スナップショット
        h_before = dict(state.h)
        open_before = {a.id for a in current_open}

        state, current_open = update(state, q, paradigms, questions, current_open)

        # H の変化を検出
        h_changes = {}
        for d, v in state.h.items():
            old = h_before.get(d, 0.5)
            if abs(v - old) > 0.001:
                h_changes[d] = (old, v)

        # 新規オープン
        new_opens = {a.id for a in current_open} - open_before - {q.id}

        # 表示
        eff = compute_effect(q)
        if isinstance(eff, list) and len(eff) > 0 and isinstance(eff[0], tuple):
            eff_str = ", ".join(f"{d}={v}" for d, v in eff)
        else:
            eff_str = ", ".join(eff)

        print(f"{q.id}({q.correct_answer}) effect=[{eff_str}]")

        # H の変化（effect による直接変化を除く＝同化による変化のみ）
        direct_ds = set()
        if q.correct_answer != "irrelevant":
            for d, v in compute_effect(q):
                direct_ds.add(d)

        assimilation_changes = {d: (old, new) for d, (old, new) in h_changes.items() if d not in direct_ds}
        if assimilation_changes:
            for d in sorted(assimilation_changes):
                old, new = assimilation_changes[d]
                opens = any(
                    abs(new - v) < EPSILON
                    for qq in questions
                    if qq.correct_answer != "irrelevant" and qq.id not in state.answered
                    for d2, v in compute_effect(qq)
                    if d2 == d
                )
                mark = " → open可能" if opens else ""
                print(f"  同化: H[{d}] {old:.3f} → {new:.3f}{mark}")
        else:
            print(f"  同化: なし")

        if new_opens:
            print(f"  新規オープン: {sorted(new_opens)}")

    print()
    print("-" * 60)

    # 最終 H 状態（0.5 以外、O に含まれないもの）
    h_moved = {d: v for d, v in state.h.items()
               if abs(v - 0.5) > 0.01 and d not in state.o}
    print(f"最終 H 移動（未観測）: {len(h_moved)}件")
    for d in sorted(h_moved):
        print(f"  H[{d}] = {h_moved[d]:.3f}")

    # 残りのオープン質問
    remaining = [q for q in current_open if q.id not in state.answered]
    print(f"残オープン: {len(remaining)}問 {[q.id for q in remaining]}")


if __name__ == "__main__":
    main()

"""ゲームシミュレーション: open(H) に基づく完全なゲーム進行シミュレーション。

trajectory.py（固定順回答）の代替。エンジンの update 関数を使い、
open(H) → 質問選択 → 回答 → 同化 → パラダイムシフト判定
という実際のゲームループを忠実に再現する。

検証項目:
  1. open(H) で質問が段階的に利用可能になるか
  2. パラダイムシフトが発生し、P1→...→P5 の進行が達成されるか
  3. ゲームが途中で行き詰まらないか（オープン質問がなくなる）
  4. クリア質問に到達できるか
"""
from common import load_data, MAIN_PATH
from engine import (
    init_game,
    init_questions,
    update,
    tension,
    alignment,
    compute_effect,
)


def classify_question(q, paradigms):
    """質問の effect 記述素がどのメインパラダイムに属するかを返す。"""
    eff = compute_effect(q)
    if q.correct_answer == "irrelevant":
        return "irr", set()
    eff_ds = {d for d, v in eff}
    homes = set()
    for pid in MAIN_PATH:
        if pid not in paradigms:
            continue
        if eff_ds & paradigms[pid].d_all:
            homes.add(pid)
    if not homes:
        return "orphan", set()
    return "/".join(sorted(homes)), homes


def anomaly_details(o, paradigm):
    """アノマリーとなっている記述素の詳細を返す。"""
    details = []
    for d in sorted(paradigm.d_all & set(o.keys())):
        pred = paradigm.prediction(d)
        if pred != o[d]:
            details.append((d, o[d], pred))
    return details


def main():
    paradigms, questions, all_ids, ps_values, init_pid = load_data()

    state = init_game(ps_values, paradigms, init_pid, all_ids)
    p_init = paradigms[init_pid]
    current_open = init_questions(p_init, questions)

    print("=" * 70)
    print("ゲームシミュレーション（open(H) ベース）")
    print("=" * 70)
    print()

    # 初期状態
    print(f"初期パラダイム: {state.p_current} ({p_init.name})")
    print(f"初期オープン: {len(current_open)}問")
    for q in sorted(current_open, key=lambda x: x.id):
        kind, _ = classify_question(q, paradigms)
        print(f"  {q.id} [{kind}] ({q.correct_answer})")
    print()

    def show_paradigm_state():
        for pid in MAIN_PATH:
            if pid not in paradigms:
                continue
            p = paradigms[pid]
            t = tension(state.o, p)
            a = alignment(state.o, p)
            overlap = len(p.d_all & set(state.o.keys()))
            marker = " <-- current" if pid == state.p_current else ""
            details = anomaly_details(state.o, p)
            anom_str = ""
            if details:
                anom_str = " anomaly=[" + ",".join(d for d, _, _ in details) + "]"
            print(f"    {pid}: t={t} a={a:.3f} |D∩O|={overlap}{anom_str}{marker}")

    show_paradigm_state()
    print()

    # ゲームループ
    step = 0
    shifts = []
    visited_paradigms = [init_pid]

    while current_open:
        # オープン質問のうち ID 順で最初を選択
        current_open_sorted = sorted(current_open, key=lambda q: q.id)
        q = current_open_sorted[0]

        step += 1
        old_p = state.p_current

        state, current_open = update(state, q, paradigms, questions, current_open)

        shifted = state.p_current != old_p
        kind, _ = classify_question(q, paradigms)

        # effect 表示
        eff = compute_effect(q)
        if q.correct_answer == "irrelevant":
            eff_str = "irr:" + ",".join(eff)
        else:
            eff_str = ",".join(f"{d}={v}" for d, v in eff)

        p_cur = paradigms[state.p_current]
        t = tension(state.o, p_cur)
        a = alignment(state.o, p_cur)

        line = (
            f"{step:2d}. {q.id}({q.correct_answer:3s}) [{kind:12s}] "
            f"P={state.p_current} t={t} a={a:.3f} open={len(current_open)}"
        )

        if shifted:
            shifts.append((step, q.id, old_p, state.p_current))
            if state.p_current not in visited_paradigms:
                visited_paradigms.append(state.p_current)
            line += f"  ** SHIFT {old_p} -> {state.p_current} **"
            print(line)
            # シフト時の全パラダイム状態を表示
            show_paradigm_state()
        else:
            print(line)

        # クリア質問チェック
        if q.is_clear:
            print()
            print("  >>> CLEAR! ゲームクリア <<<")
            break

    # 最終サマリ
    print()
    print("=" * 70)
    print("結果サマリ")
    print("=" * 70)
    print(f"回答数: {step}")
    print(f"最終パラダイム: {state.p_current} ({paradigms[state.p_current].name})")
    print(f"|O|={len(state.o)}, |R|={len(state.r)}")
    print(f"訪問パラダイム: {' -> '.join(visited_paradigms)}")
    print()

    # パラダイムシフト一覧
    if shifts:
        print("パラダイムシフト履歴:")
        for s, qid, old, new in shifts:
            print(f"  Step {s:2d}: {qid} -- {old} -> {new}")
    else:
        print("パラダイムシフト: なし")
    print()

    # 最終パラダイム状態
    print("最終パラダイム状態:")
    show_paradigm_state()
    print()

    # 到達性判定
    reached_t = state.p_current == "P5"
    reached_clear = any(q.is_clear and q.id in state.answered for q in questions)
    print("到達性判定:")
    print(f"  T(P5) 到達: {'OK' if reached_t else 'NG'}")
    print(f"  クリア質問: {'OK' if reached_clear else 'NG'}")
    print(f"  全パラダイム訪問: {'OK' if len(visited_paradigms) == len(MAIN_PATH) else 'NG'} ({len(visited_paradigms)}/{len(MAIN_PATH)})")
    print()

    # 未回答・行き詰まり分析
    unanswered = [q for q in questions if q.id not in state.answered]
    if unanswered:
        print(f"未回答: {len(unanswered)}問")
        if not current_open and not reached_clear:
            print("  *** 行き詰まり: オープン質問なし ***")
            print()
            print("  行き詰まり原因（各未回答質問の H 状態）:")
            for q in unanswered:
                eff = compute_effect(q)
                if q.correct_answer == "irrelevant":
                    continue
                h_info = []
                for d, v in eff:
                    h_val = state.h.get(d, 0.5)
                    gap = abs(h_val - v)
                    h_info.append(f"H[{d}]={h_val:.3f}(need={v},gap={gap:.3f})")
                kind, _ = classify_question(q, paradigms)
                print(f"    {q.id} [{kind}] {'; '.join(h_info)}")


if __name__ == "__main__":
    main()

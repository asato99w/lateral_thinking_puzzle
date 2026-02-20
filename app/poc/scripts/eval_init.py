"""初期状態の評価: init_questions の構成と、回答後の H 移動・新規オープンを確認する。"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from models import Paradigm, Question
from engine import (
    init_game,
    init_questions,
    update,
    open_questions,
    tension,
    alignment,
    compute_effect,
    EPSILON,
)


def load_data():
    data_path = Path(__file__).parent.parent / "data" / "turtle_soup.json"
    with open(data_path, encoding="utf-8") as f:
        data = json.load(f)

    paradigms = {}
    for p in data["paradigms"]:
        paradigms[p["id"]] = Paradigm(
            id=p["id"],
            name=p["name"],
            d_plus=set(p["d_plus"]),
            d_minus=set(p["d_minus"]),
            relations=[(r[0], r[1], r[2]) for r in p["relations"]],
        )

    questions = []
    for q in data["questions"]:
        questions.append(Question(
            id=q["id"],
            text=q["text"],
            ans_yes=[(a[0], a[1]) for a in q["ans_yes"]],
            ans_no=[(a[0], a[1]) for a in q["ans_no"]],
            ans_irrelevant=q["ans_irrelevant"],
            correct_answer=q["correct_answer"],
            is_clear=q.get("is_clear", False),
        ))

    return (
        paradigms,
        questions,
        data["all_descriptor_ids"],
        {d[0]: d[1] for d in data["ps_values"]},
        data["init_paradigm"],
    )


def paradigm_homes(q, paradigms):
    """質問の effect が一致するパラダイム群を返す。"""
    eff = compute_effect(q)
    if not (isinstance(eff, list) and len(eff) > 0 and isinstance(eff[0], tuple)):
        return []
    homes = []
    for pid, p in paradigms.items():
        for d_id, v in eff:
            if p.prediction(d_id) == v:
                homes.append(pid)
                break
    return homes


def main():
    paradigms, questions, all_ids, ps_values, init_pid = load_data()
    q_by_id = {q.id: q for q in questions}
    p_init = paradigms[init_pid]

    state = init_game(ps_values, paradigms, init_pid, all_ids)
    init_qs = init_questions(p_init, questions)
    init_ids = {q.id for q in init_qs}

    # --- 初期オープン質問の一覧 ---
    print(f"初期パラダイム: {p_init.name} ({p_init.id})")
    print(f"初期オープン: {len(init_qs)}問 / 全{len(questions)}問")
    print()

    yes_count = sum(1 for q in init_qs if q.correct_answer == "yes")
    no_count = sum(1 for q in init_qs if q.correct_answer == "no")
    irr_count = sum(1 for q in init_qs if q.correct_answer == "irrelevant")
    print(f"正答分布: はい={yes_count}, いいえ={no_count}, 関係ない={irr_count}")
    print()

    print("質問一覧:")
    for q in init_qs:
        eff = compute_effect(q)
        homes = paradigm_homes(q, paradigms)
        eff_ds = [d for d, v in eff] if isinstance(eff[0], tuple) else eff
        print(f"  {q.id} [{q.correct_answer:4s}] {', '.join(eff_ds):12s} パラダイム: {homes}")
        print(f"       {q.text}")
    print()

    # --- 1問ずつ回答して H 移動と新規オープンを追跡 ---
    print("=" * 60)
    print("逐次回答トレース")
    print("=" * 60)

    available = list(init_qs)
    total_opened = 0

    for q in init_qs:
        old_p = state.p_current
        old_avail_ids = {a.id for a in available}
        state, available = update(state, q, paradigms, questions, available)

        new_ids = {a.id for a in available} - init_ids
        p_cur = paradigms[state.p_current]
        t = tension(state.o, p_cur)
        a = alignment(state.o, p_cur)

        shifted = state.p_current != old_p
        newly = sorted(new_ids - old_avail_ids)

        line = f"{q.id}({q.correct_answer:3s}) → 残{len(available)}問 tension={t} align={a:.3f}"
        if shifted:
            line += f" ★シフト→{p_cur.name}"
        if newly:
            total_opened += len(newly)
            line += f" +{newly}"
        print(line)

    print()
    print(f"P1 全回答後:")
    print(f"  パラダイム: {paradigms[state.p_current].name}")
    print(f"  残オープン: {len(available)}問 {[a.id for a in available]}")
    print(f"  新規追加計: {total_opened}問")

    # H が 0.5 から動いた未観測記述素
    moved = {d: v for d, v in state.h.items()
             if abs(v - 0.5) > 0.01 and d not in state.o}
    if moved:
        print(f"  H移動(未観測): {len(moved)}件")
        for d in sorted(moved):
            print(f"    H[{d}] = {moved[d]:.3f}")
    else:
        print(f"  H移動(未観測): なし")


if __name__ == "__main__":
    main()

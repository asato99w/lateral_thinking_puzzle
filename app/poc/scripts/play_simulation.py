"""ゲームの自動シミュレーション。全質問を順番に選択し、状態遷移を表示する。"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from models import Paradigm, Question, GameState
from engine import (
    init_game,
    init_questions,
    get_answer,
    update,
    check_clear,
    tension,
    alignment,
    open_questions,
)
from threshold import build_o_star, compute_thresholds

ANSWER_DISPLAY = {"yes": "YES", "no": "NO", "irrelevant": "関係ない"}


def load_and_build(data_path: Path):
    import json
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

    ps_values = {d[0]: d[1] for d in data["ps_values"]}
    all_descriptor_ids = data["all_descriptor_ids"]
    init_paradigm_id = data["init_paradigm"]

    o_star = build_o_star(questions, ps_values)
    compute_thresholds(paradigms, o_star)

    return data, paradigms, questions, all_descriptor_ids, ps_values, init_paradigm_id


def print_paradigm_state(state: GameState, paradigms: dict[str, Paradigm]):
    """全パラダイムの tension / alignment を表示。"""
    current = state.p_current
    for pid, p in paradigms.items():
        t = tension(state.o, p)
        a = alignment(state.h, p)
        marker = " ◀" if pid == current else ""
        th_str = f"th={p.threshold}" if p.threshold is not None else "th=–"
        print(f"    {pid} ({p.name}): tension={t} {th_str} alignment={a:.3f}{marker}")


def main():
    data_dir = Path(__file__).parent.parent / "data"

    # コマンドライン引数でデータ選択
    data_name = "turtle_soup.json"
    for i, arg in enumerate(sys.argv):
        if arg == "--data" and i + 1 < len(sys.argv):
            data_name = sys.argv[i + 1]

    data_path = data_dir / data_name
    data, paradigms, questions, all_descriptor_ids, ps_values, init_paradigm_id = \
        load_and_build(data_path)

    state = init_game(ps_values, paradigms, init_paradigm_id, all_descriptor_ids)
    p_init = paradigms[init_paradigm_id]
    current_open = init_questions(p_init, questions)

    print("=" * 60)
    print(f"  {data['title']}")
    print("=" * 60)
    print()
    print(data["statement"])
    print()
    print(f"パラダイム数: {len(paradigms)}")
    print(f"質問数: {len(questions)}")
    print(f"記述素数: {len(all_descriptor_ids)}")
    print()

    # 閾値の表示
    print("── 閾値 ──")
    for pid, p in paradigms.items():
        th_str = str(p.threshold) if p.threshold is not None else "–(シフト元にならない)"
        print(f"  {pid} ({p.name}): threshold = {th_str}")
    print()

    # 初期状態
    print("── 初期状態 ──")
    print(f"  現パラダイム: {init_paradigm_id} ({p_init.name})")
    print(f"  初期オープン質問数: {len(current_open)}")
    print()
    print_paradigm_state(state, paradigms)
    print()

    step = 0
    while current_open:
        # 常に最初の質問を選択（自動プレイ）
        selected = current_open[0]
        step += 1
        answer = get_answer(selected)

        print(f"── Step {step} ──")
        print(f"  選択: {selected.text}")
        print(f"  回答: {ANSWER_DISPLAY[answer]}")

        # クリア判定
        if check_clear(selected):
            print()
            print("  ★ クリア！")
            print()
            print(f"  総質問数: {step}")
            break

        p_before = state.p_current

        state, current_open = update(state, selected, paradigms, questions, current_open)

        # パラダイムシフト検出
        if state.p_current != p_before:
            p_new = paradigms[state.p_current]
            print(f"  ▶ パラダイムシフト: {p_before} → {state.p_current} ({p_new.name})")

        print(f"  オープン質問数: {len(current_open)}")
        print_paradigm_state(state, paradigms)
        print()

    if not current_open and step > 0 and not check_clear(selected):
        print("  ※ オープン質問なし — ゲーム停止")
        print(f"  総質問数: {step}")


if __name__ == "__main__":
    main()

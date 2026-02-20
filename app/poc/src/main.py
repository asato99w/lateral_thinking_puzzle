import json
import sys
from pathlib import Path

from models import Descriptor, Paradigm, Question, GameState
from engine import (
    init_game,
    init_questions,
    get_answer,
    update,
    check_clear,
    consistency,
    open_questions,
)

ANSWER_DISPLAY = {
    "yes": "YES",
    "no": "NO",
    "irrelevant": "関係ない",
}


def load_quiz(path: str) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def build_paradigms(data: dict) -> dict[str, Paradigm]:
    paradigms = {}
    for p in data["paradigms"]:
        paradigms[p["id"]] = Paradigm(
            id=p["id"],
            name=p["name"],
            d_plus=set(p["d_plus"]),
            d_minus=set(p["d_minus"]),
            relations=[(r[0], r[1], r[2]) for r in p["relations"]],
        )
    return paradigms


def build_questions(data: dict) -> list[Question]:
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
    return questions


def main():
    data_path = Path(__file__).parent.parent / "data" / "turtle_soup.json"
    data = load_quiz(str(data_path))

    paradigms = build_paradigms(data)
    questions = build_questions(data)
    all_descriptor_ids = data["all_descriptor_ids"]
    ps_values = {d[0]: d[1] for d in data["ps_values"]}
    init_paradigm_id = data["init_paradigm"]

    # ゲーム初期化
    state = init_game(ps_values, paradigms, init_paradigm_id, all_descriptor_ids)

    # 初期質問の決定: init_questions(P_init)
    p_init = paradigms[init_paradigm_id]
    current_open = init_questions(p_init, questions)

    print("=" * 50)
    print(data["title"])
    print("=" * 50)
    print()
    print(data["statement"])
    print()

    while True:
        # 現在のパラダイムと consistency を表示
        p_cur = paradigms[state.p_current]
        con = consistency(state.o, p_cur)
        print(f"[パラダイム: {p_cur.name} | consistency: {con:.2f}]")
        print()

        if not current_open:
            print("オープンな質問がありません。ゲーム終了。")
            break

        # オープン質問の表示
        print("--- 質問を選んでください ---")
        for i, q in enumerate(current_open):
            print(f"  {i + 1}. {q.text}")
        print(f"  0. 終了")
        print()

        # 入力
        try:
            choice = input("> ").strip()
            if choice == "0":
                print("ゲームを終了します。")
                break
            idx = int(choice) - 1
            if idx < 0 or idx >= len(current_open):
                print("無効な選択です。")
                continue
        except (ValueError, EOFError):
            print("無効な入力です。")
            continue

        selected = current_open[idx]

        # 回答の表示
        answer = get_answer(selected)
        print(f"\n→ {ANSWER_DISPLAY[answer]}")
        print()

        # クリア判定
        if check_clear(selected):
            print("=" * 50)
            print("クリア！真相に到達しました。")
            print("=" * 50)
            break

        # 状態更新（オープン質問は追加のみ）
        state, current_open = update(state, selected, paradigms, questions, current_open)

        # 選択済み質問の表示
        print("--- 選択済み ---")
        for q in questions:
            if q.id in state.answered:
                ans = ANSWER_DISPLAY[get_answer(q)]
                print(f"  [{ans}] {q.text}")
        print()


if __name__ == "__main__":
    main()

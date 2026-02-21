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
    tension,
    alignment,
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


def select_quiz(data_dir: Path) -> Path:
    """data_dir 内の .json ファイルを走査し、ユーザーに選択させる。"""
    candidates = sorted(data_dir.glob("*.json"))
    if not candidates:
        print("データファイルが見つかりません。")
        sys.exit(1)

    if len(candidates) == 1:
        data = load_quiz(str(candidates[0]))
        print(f"クイズ: {data.get('title', candidates[0].stem)}")
        return candidates[0]

    print("=== クイズ選択 ===")
    titles = []
    for i, path in enumerate(candidates):
        data = load_quiz(str(path))
        title = data.get("title", path.stem)
        titles.append(title)
        print(f"  {i + 1}. {title}")
    print()

    while True:
        try:
            choice = input("番号を選択 > ").strip()
            idx = int(choice) - 1
            if 0 <= idx < len(candidates):
                return candidates[idx]
            print("無効な番号です。")
        except (ValueError, EOFError):
            print("無効な入力です。")


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


def print_history(questions: list[Question], answered: set[str]):
    """回答済み質問の履歴を表示する。"""
    entries = [q for q in questions if q.id in answered]
    if not entries:
        print("  (まだ回答がありません)")
        return
    for q in entries:
        ans = ANSWER_DISPLAY[get_answer(q)]
        print(f"  [{ans}] {q.text}")


def print_summary(questions: list[Question], answered: set[str], step: int):
    """ゲーム終了時のサマリーを表示する。"""
    yes_count = 0
    no_count = 0
    irr_count = 0
    for q in questions:
        if q.id in answered:
            ans = get_answer(q)
            if ans == "yes":
                yes_count += 1
            elif ans == "no":
                no_count += 1
            else:
                irr_count += 1

    print()
    print("── 結果 ──")
    print(f"  質問数: {step}")
    print(f"  YES: {yes_count} / NO: {no_count} / 関係ない: {irr_count}")


def main():
    data_dir = Path(__file__).parent.parent / "data"
    quiz_path = select_quiz(data_dir)
    data = load_quiz(str(quiz_path))

    paradigms = build_paradigms(data)
    questions = build_questions(data)
    all_descriptor_ids = data["all_descriptor_ids"]
    ps_values = {d[0]: d[1] for d in data["ps_values"]}
    init_paradigm_id = data["init_paradigm"]

    # シフト制御パラメータ
    tension_threshold = data.get("tension_threshold", 2)
    shift_candidates = data.get("shift_candidates", None)

    # ゲーム初期化
    state = init_game(ps_values, paradigms, init_paradigm_id, all_descriptor_ids)

    # 初期質問の決定
    p_init = paradigms[init_paradigm_id]
    current_open = init_questions(p_init, questions)

    step = 0
    debug_mode = False

    print()
    print("=" * 50)
    print(data["title"])
    print("=" * 50)
    print()
    print(data["statement"])
    print()
    print("操作: 番号=質問選択 / h=履歴 / d=デバッグ / 0=終了")
    print()

    while True:
        # デバッグモード表示
        if debug_mode:
            p_cur = paradigms[state.p_current]
            t = tension(state.o, p_cur)
            a = alignment(state.o, p_cur)
            print(f"[DEBUG パラダイム: {p_cur.name} ({state.p_current}) | tension: {t} | alignment: {a:.3f}]")
            print()

        if not current_open:
            print("オープンな質問がありません。ゲーム終了。")
            print_summary(questions, state.answered, step)
            break

        # オープン質問の表示
        print(f"── 質問 {step + 1} ──")
        for i, q in enumerate(current_open):
            print(f"  {i + 1}. {q.text}")
        print(f"  0. 終了 / h. 履歴 / d. デバッグ{'(ON)' if debug_mode else ''}")
        print()

        # 入力
        try:
            choice = input("> ").strip().lower()
        except EOFError:
            print()
            print_summary(questions, state.answered, step)
            break

        if choice == "0":
            print("ゲームを終了します。")
            print_summary(questions, state.answered, step)
            break

        if choice == "h":
            print()
            print("── 回答履歴 ──")
            print_history(questions, state.answered)
            print()
            continue

        if choice == "d":
            debug_mode = not debug_mode
            print(f"デバッグモード: {'ON' if debug_mode else 'OFF'}")
            print()
            continue

        try:
            idx = int(choice) - 1
            if idx < 0 or idx >= len(current_open):
                print("無効な選択です。")
                continue
        except ValueError:
            print("無効な入力です。")
            continue

        selected = current_open[idx]
        step += 1

        # 回答の表示
        answer = get_answer(selected)
        print(f"\n→ {ANSWER_DISPLAY[answer]}")
        print()

        # クリア判定
        if check_clear(selected):
            print("=" * 50)
            print("クリア！真相に到達しました。")
            print("=" * 50)
            print_summary(questions, state.answered | {selected.id}, step)
            break

        # パラダイムシフト検出用: 更新前のパラダイムIDを保持
        p_before = state.p_current

        # 状態更新
        state, current_open = update(state, selected, paradigms, questions, current_open,
                                     tension_threshold=tension_threshold,
                                     shift_candidates=shift_candidates)

        # パラダイムシフトの演出
        if state.p_current != p_before:
            p_new = paradigms[state.p_current]
            print("─── 物語の空気が変わった ───")
            print(f"  「{p_new.name}」")
            print()


if __name__ == "__main__":
    main()

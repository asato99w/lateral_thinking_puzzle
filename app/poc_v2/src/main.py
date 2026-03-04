"""v2 POC: パズルエンジン - CLI シミュレーション"""

from __future__ import annotations

import sys
from pathlib import Path

from engine import (
    AnswerResult,
    PuzzleData,
    answer_question,
    available_questions,
    check_complete,
    init_game,
    load_puzzle,
)
from models import GameState


def display_state(state: GameState, puzzle: PuzzleData) -> None:
    """現在の状態を表示"""
    print("\n" + "=" * 60)
    print("【現在の状態】")
    print("-" * 60)

    print(f"\n📋 確認済み記述素 ({len(state.confirmed)}件):")
    for did in sorted(state.confirmed):
        d = puzzle.descriptors[did]
        print(f"  {d.label}")

    if state.derived:
        print(f"\n💭 導出済み記述素 ({len(state.derived)}件):")
        for did in sorted(state.derived):
            d = puzzle.descriptors[did]
            print(f"  {d.label}")

    # 発見済みピース
    if state.discovered_pieces:
        print(f"\n🧩 発見済みピース ({len(state.discovered_pieces)}/{len(puzzle.pieces)}):")
        for pid in sorted(state.discovered_pieces):
            piece = puzzle.pieces[pid]
            print(f"  [{pid}] {piece.label}")
    else:
        print(f"\n🧩 発見済みピース (0/{len(puzzle.pieces)})")

    print()


def display_answer_result(
    result: AnswerResult, puzzle: PuzzleData, *, show_ids: bool = True
) -> None:
    """回答結果を表示"""
    print()

    # 新たに確認された記述素
    if result.new_confirmed:
        for did in result.new_confirmed:
            d = puzzle.descriptors[did]
            print(f"  💡 新記述素: {d.label}")

    # 新たに導出された記述素
    if result.new_derived:
        for did in result.new_derived:
            d = puzzle.descriptors[did]
            print(f"  💭 導出: {d.label}")

    # 棄却された記述素
    if result.new_rejected:
        for did in result.new_rejected:
            d = puzzle.descriptors[did]
            print(f"  ❌ 棄却: {d.label}")

    # メカニズム表示
    if result.is_link:
        print("  🔗 【リンク】複数の事実が結びつきました！")
    elif result.is_anomaly:
        print("  ⚡ 【アノマリー】矛盾が検出されました！再解釈が必要です。")

    # 新たに発見されたピース
    if result.new_pieces:
        for pid in result.new_pieces:
            piece = puzzle.pieces[pid]
            dep_type = "独立" if not piece.depends_on else "依存"
            if show_ids:
                print(f"  🧩 ピース発見 [{pid}] {piece.label} ({dep_type})")
            else:
                print(f"  🧩 ピース発見: {piece.label}（{dep_type}）")

    if not result.new_confirmed and not result.new_pieces and not result.new_derived and not result.new_rejected:
        print("  （新しい発見はありませんでした）")


def run_simulation(puzzle_path: str | Path) -> None:
    """CLI シミュレーション実行"""
    puzzle = load_puzzle(puzzle_path)
    state = init_game(puzzle)

    print("=" * 60)
    print(f"🐢 {puzzle.title}")
    print("=" * 60)
    print(f"\n{puzzle.statement}")
    print("\n質問を選んで真相を解き明かしましょう。")

    while True:
        display_state(state, puzzle)

        if check_complete(state, puzzle):
            print("🎉 全ピースが揃いました！パズルクリア！")
            print(f"\n【真相】\n{puzzle.truth}")
            print(f"\n回答数: {len(state.answered)}問")
            print(f"回答順: {' → '.join(state.history)}")
            break

        questions = available_questions(state, puzzle)

        if not questions:
            print("⚠️  利用可能な質問がありません。行き詰まりました。")
            break

        print(f"❓ 利用可能な質問 ({len(questions)}件):")
        for i, q in enumerate(questions, 1):
            mech_icon = {"observation": "👁", "link": "🔗", "anomaly": "⚡"}.get(
                q.mechanism, "?"
            )
            print(f"  {i}. {q.text}  {mech_icon}")

        print(f"  0. 終了")

        try:
            choice = input("\n番号を選択 > ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n終了します。")
            break

        if choice == "0":
            print("終了します。")
            break

        try:
            idx = int(choice) - 1
            if idx < 0 or idx >= len(questions):
                print("無効な番号です。")
                continue
        except ValueError:
            print("数字を入力してください。")
            continue

        selected = questions[idx]
        print(f"\n📝 Q: {selected.text}")
        print(f"💬 A: {selected.answer}")

        result = answer_question(state, selected, puzzle)
        display_answer_result(result, puzzle)


def run_auto_simulation(puzzle_path: str | Path, *, show_ids: bool = True) -> None:
    """自動シミュレーション: 利用可能な質問を順に全て回答"""
    puzzle = load_puzzle(puzzle_path)
    state = init_game(puzzle)

    print("=" * 60)
    print(f"🐢 {puzzle.title} (自動シミュレーション)")
    print("=" * 60)
    print(f"\n{puzzle.statement}\n")

    if state.derived:
        print("💭 初期導出:")
        for did in sorted(state.derived):
            d = puzzle.descriptors[did]
            print(f"  {d.label}")
        print()

    step = 0
    answered_texts: list[str] = []
    while not check_complete(state, puzzle):
        questions = available_questions(state, puzzle)
        if not questions:
            print("⚠️  行き詰まり: 利用可能な質問がありません。")
            if show_ids:
                print(f"  確認済み記述素: {sorted(state.confirmed)}")
                print(f"  発見済みピース: {sorted(state.discovered_pieces)}")
            break

        q = questions[0]
        step += 1
        answered_texts.append(q.text)

        print(f"--- Step {step} ---")
        print(f"Q: {q.text}")
        print(f"A: {q.answer}")

        result = answer_question(state, q, puzzle)
        display_answer_result(result, puzzle, show_ids=show_ids)
        print()

    if check_complete(state, puzzle):
        print("=" * 60)
        print(f"🎉 クリア！ ({step}問で解決)")
        if show_ids:
            print(f"回答順: {' → '.join(state.history)}")
    else:
        if show_ids:
            print(f"\n未発見ピース: {set(puzzle.pieces.keys()) - state.discovered_pieces}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python main.py <data.json> [--auto]", file=sys.stderr)
        sys.exit(2)

    puzzle_path = sys.argv[1]
    if not Path(puzzle_path).exists():
        print(f"Error: {puzzle_path} が見つかりません", file=sys.stderr)
        sys.exit(2)

    show_ids = "--no-id" not in sys.argv
    if "--auto" in sys.argv:
        run_auto_simulation(puzzle_path, show_ids=show_ids)
    else:
        run_simulation(puzzle_path)

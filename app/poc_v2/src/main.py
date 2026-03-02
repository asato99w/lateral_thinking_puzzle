"""v2 POC: パズルエンジン - CLI シミュレーション"""

from __future__ import annotations

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

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def display_state(state: GameState, puzzle: PuzzleData) -> None:
    """現在の状態を表示"""
    print("\n" + "=" * 60)
    print("【現在の状態】")
    print("-" * 60)

    # 観測済み事実
    print(f"\n📋 観測済み事実 ({len(state.observed_facts)}件):")
    for fid in sorted(state.observed_facts):
        fact = puzzle.facts[fid]
        marker = "S" if fid.startswith("Ps") else "T"
        print(f"  [{marker}] {fact.label}")

    # 形成済み仮説
    if state.formed_hypotheses:
        print(f"\n💭 形成済み仮説 ({len(state.formed_hypotheses)}件):")
        for hid in sorted(state.formed_hypotheses):
            hyp = puzzle.hypotheses[hid]
            print(f"  {hyp.label}")

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
    result: AnswerResult, puzzle: PuzzleData
) -> None:
    """回答結果を表示"""
    print()

    # 新たに判明した事実
    if result.new_facts:
        for fid in result.new_facts:
            fact = puzzle.facts[fid]
            print(f"  💡 新事実: {fact.label}")

    # 新たに形成された仮説
    if result.new_hypotheses:
        for hid in result.new_hypotheses:
            hyp = puzzle.hypotheses[hid]
            print(f"  💭 仮説形成: {hyp.label}")

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
            print(f"  🧩 ピース発見 [{pid}] {piece.label} ({dep_type})")

    if not result.new_facts and not result.new_pieces and not result.new_hypotheses:
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


def run_auto_simulation(puzzle_path: str | Path) -> None:
    """自動シミュレーション: 利用可能な質問を順に全て回答"""
    puzzle = load_puzzle(puzzle_path)
    state = init_game(puzzle)

    print("=" * 60)
    print(f"🐢 {puzzle.title} (自動シミュレーション)")
    print("=" * 60)
    print(f"\n{puzzle.statement}\n")

    # 初期仮説の表示
    if state.formed_hypotheses:
        print("💭 初期仮説:")
        for hid in sorted(state.formed_hypotheses):
            hyp = puzzle.hypotheses[hid]
            print(f"  {hyp.label}")
        print()

    step = 0
    while not check_complete(state, puzzle):
        questions = available_questions(state, puzzle)
        if not questions:
            print("⚠️  行き詰まり: 利用可能な質問がありません。")
            print(f"  観測済み事実: {sorted(state.observed_facts)}")
            print(f"  形成済み仮説: {sorted(state.formed_hypotheses)}")
            print(f"  発見済みピース: {sorted(state.discovered_pieces)}")
            break

        q = questions[0]
        step += 1

        print(f"--- Step {step} ---")
        print(f"Q: {q.text}")
        print(f"A: {q.answer}")

        result = answer_question(state, q, puzzle)
        display_answer_result(result, puzzle)
        print()

    if check_complete(state, puzzle):
        print("=" * 60)
        print(f"🎉 クリア！ ({step}問で解決)")
        print(f"回答順: {' → '.join(state.history)}")
    else:
        print(f"\n未発見ピース: {set(puzzle.pieces.keys()) - state.discovered_pieces}")


if __name__ == "__main__":
    import sys

    puzzle_path = DATA_DIR / "turtle_soup.json"

    if len(sys.argv) > 1 and sys.argv[1] == "--auto":
        run_auto_simulation(puzzle_path)
    else:
        run_simulation(puzzle_path)

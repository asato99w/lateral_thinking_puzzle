"""v2 POC: パズルエンジン - コアロジック"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from models import (
    Descriptor,
    GameState,
    Piece,
    Question,
)


@dataclass
class PuzzleData:
    """パズル定義データの集約"""

    id: str
    title: str
    statement: str
    truth: str
    descriptors: dict[str, Descriptor]
    initial_confirmed: list[str]
    clear_conditions: list[list[str]]  # OR of AND: クリア条件（記述素IDの族）
    pieces: dict[str, Piece]
    questions: dict[str, Question]


def load_puzzle(path: str | Path) -> PuzzleData:
    """JSON ファイルからパズルデータを読み込む"""
    with open(path, encoding="utf-8") as f:
        raw = json.load(f)

    descriptors = {}
    for item in raw["descriptors"]:
        d = Descriptor(
            id=item["id"],
            label=item["label"],
            formation_conditions=item.get("formation_conditions"),
            rejection_conditions=item.get("rejection_conditions"),
        )
        descriptors[d.id] = d

    pieces = {}
    for item in raw["pieces"]:
        p = Piece(
            id=item["id"],
            label=item["label"],
            members=item["members"],
            depends_on=item.get("depends_on", []),
        )
        pieces[p.id] = p

    questions = {}
    for item in raw["questions"]:
        q = Question(
            id=item["id"],
            text=item["text"],
            answer=item["answer"],
            recall_conditions=item["recall_conditions"],
            reveals=item["reveals"],
            mechanism=item["mechanism"],
            prerequisites=item.get("prerequisites", []),
        )
        questions[q.id] = q

    return PuzzleData(
        id=raw["id"],
        title=raw["title"],
        statement=raw["statement"],
        truth=raw["truth"],
        descriptors=descriptors,
        initial_confirmed=raw["initial_confirmed"],
        clear_conditions=raw.get("clear_conditions", []),
        pieces=pieces,
        questions=questions,
    )


def init_game(puzzle: PuzzleData) -> GameState:
    """ゲーム初期化: initial_confirmed を confirmed に設定し、導出チェック"""
    state = GameState(confirmed=set(puzzle.initial_confirmed))
    evaluate_derivations(state, puzzle)
    return state


def evaluate_derivations(state: GameState, puzzle: PuzzleData) -> tuple[list[str], list[str]]:
    """confirmed 集合から導出可能な記述素を不動点計算で求め、state.derived を更新する。

    state.confirmed は変更しない。導出結果は state.derived に格納される。
    戻り値: (newly_derived, newly_rejected)
    - newly_derived: 新たに導出された記述素のリスト
    - newly_rejected: 今回棄却された（derived から除去された）記述素のリスト
    """
    # Step 1: 棄却集合の計算（confirmed のみ参照、O(n)）
    rejected = set()
    for d in puzzle.descriptors.values():
        if d.rejection_conditions is not None:
            if any(all(c in state.confirmed for c in group) for group in d.rejection_conditions):
                rejected.add(d.id)

    # Step 2: 不動点計算（rejected をスキップ）
    known = set(state.confirmed)
    changed = True
    while changed:
        changed = False
        for d in puzzle.descriptors.values():
            if d.formation_conditions is None:
                continue
            if d.id in known or d.id in rejected:
                continue
            for condition_set in d.formation_conditions:
                if all(c in known for c in condition_set):
                    known.add(d.id)
                    changed = True
                    break
    # derived = known から confirmed を除いた部分
    new_derived_set = known - state.confirmed
    newly_derived = sorted(new_derived_set - state.derived)
    newly_rejected = sorted((state.derived - new_derived_set) - state.confirmed)
    state.derived = new_derived_set
    return newly_derived, newly_rejected


def _check_conditions(conditions: list[list[str]], state: GameState) -> bool:
    """OR of AND の条件判定: いずれかの条件セットが全て known（confirmed ∪ derived）であれば True。"""
    known = state.known
    return any(
        all(c in known for c in condition_set)
        for condition_set in conditions
    )


def available_questions(state: GameState, puzzle: PuzzleData) -> list[Question]:
    """利用可能な質問を返す: 前提条件・想起条件が満たされ、未回答のもの

    - 前提条件（prerequisites）: confirmed のみで判定。対話上で確立された事実。
    - 想起条件（recall_conditions）: known（confirmed ∪ derived）で判定。仮説の導出。
    """
    result = []
    for q in puzzle.questions.values():
        if q.id in state.answered:
            continue
        if q.prerequisites and not all(p in state.confirmed for p in q.prerequisites):
            continue
        if _check_conditions(q.recall_conditions, state):
            result.append(q)
    return result


@dataclass
class AnswerResult:
    """質問回答の結果"""

    new_confirmed: list[str]
    new_derived: list[str]
    new_rejected: list[str]
    new_pieces: list[str]
    mechanism: str
    is_link: bool
    is_anomaly: bool


def answer_question(
    state: GameState, question: Question, puzzle: PuzzleData
) -> AnswerResult:
    """質問に回答し、状態を更新する"""
    new_confirmed: list[str] = []
    new_pieces: list[str] = []

    # reveals の記述素を confirmed に追加
    for descriptor_id in question.reveals:
        if descriptor_id not in state.confirmed:
            state.confirmed.add(descriptor_id)
            new_confirmed.append(descriptor_id)

    # 導出の再評価
    new_derived, new_rejected = evaluate_derivations(state, puzzle)

    # ピースの構成記述素がすべて揃ったかチェック（confirmed ∪ derived で判定）
    known = state.known
    for piece in puzzle.pieces.values():
        if piece.id in state.discovered_pieces:
            continue
        if not all(m in known for m in piece.members):
            continue
        if not all(dep in state.discovered_pieces for dep in piece.depends_on):
            continue
        state.discovered_pieces.add(piece.id)
        new_pieces.append(piece.id)

    # 履歴に記録
    state.answered.add(question.id)
    state.history.append(question.id)

    return AnswerResult(
        new_confirmed=new_confirmed,
        new_derived=new_derived,
        new_rejected=new_rejected,
        new_pieces=new_pieces,
        mechanism=question.mechanism,
        is_link=question.mechanism == "link",
        is_anomaly=question.mechanism == "anomaly",
    )


def check_complete(state: GameState, puzzle: PuzzleData) -> bool:
    """クリア判定: clear_conditions（記述素の族）のいずれかのグループが全て confirmed"""
    return any(
        all(descriptor_id in state.confirmed for descriptor_id in condition_set)
        for condition_set in puzzle.clear_conditions
    )

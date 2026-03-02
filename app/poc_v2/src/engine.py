"""v2 POC: パズルエンジン - コアロジック"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from models import (
    Fact,
    GameState,
    Hypothesis,
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
    facts: dict[str, Fact]
    initial_facts: list[str]
    pieces: dict[str, Piece]
    hypotheses: dict[str, Hypothesis]
    questions: dict[str, Question]


def load_puzzle(path: str | Path) -> PuzzleData:
    """JSON ファイルからパズルデータを読み込む"""
    with open(path, encoding="utf-8") as f:
        raw = json.load(f)

    facts = {item["id"]: Fact(**item) for item in raw["facts"]}
    pieces = {item["id"]: Piece(**item) for item in raw["pieces"]}
    hypotheses = {item["id"]: Hypothesis(**item) for item in raw["hypotheses"]}
    questions = {item["id"]: Question(**item) for item in raw["questions"]}

    return PuzzleData(
        id=raw["id"],
        title=raw["title"],
        statement=raw["statement"],
        truth=raw["truth"],
        facts=facts,
        initial_facts=raw["initial_facts"],
        pieces=pieces,
        hypotheses=hypotheses,
        questions=questions,
    )


def init_game(puzzle: PuzzleData) -> GameState:
    """ゲーム初期化: S の事実を observed_facts に設定し、仮説を評価"""
    state = GameState(observed_facts=set(puzzle.initial_facts))
    evaluate_hypotheses(state, puzzle)
    return state


def evaluate_hypotheses(state: GameState, puzzle: PuzzleData) -> list[str]:
    """f(facts) -> hypotheses: 観測事実から仮説を評価し、新たに形成された仮説を返す"""
    newly_formed: list[str] = []
    changed = True
    while changed:
        changed = False
        for h in puzzle.hypotheses.values():
            if h.id in state.formed_hypotheses:
                continue
            for condition_set in h.formation_conditions:
                if all(
                    c in state.observed_facts or c in state.formed_hypotheses
                    for c in condition_set
                ):
                    state.formed_hypotheses.add(h.id)
                    newly_formed.append(h.id)
                    changed = True
                    break
    return newly_formed


def _check_conditions(conditions: list[list[str]], state: GameState) -> bool:
    """OR of AND の条件判定: いずれかの条件セットが全て満たされていれば True"""
    return any(
        all(
            c in state.observed_facts or c in state.formed_hypotheses
            for c in condition_set
        )
        for condition_set in conditions
    )


def available_questions(state: GameState, puzzle: PuzzleData) -> list[Question]:
    """利用可能な質問を返す: 想起条件が満たされ、未回答のもの"""
    result = []
    for q in puzzle.questions.values():
        if q.id in state.answered:
            continue
        if _check_conditions(q.recall_conditions, state):
            result.append(q)
    return result


@dataclass
class AnswerResult:
    """質問回答の結果"""

    new_facts: list[str]
    new_hypotheses: list[str]
    new_pieces: list[str]
    mechanism: str
    is_link: bool
    is_anomaly: bool


def answer_question(
    state: GameState, question: Question, puzzle: PuzzleData
) -> AnswerResult:
    """g(question, answer) -> facts: 質問に回答し、状態を更新する"""
    new_facts: list[str] = []
    new_pieces: list[str] = []

    # reveals の事実を observed_facts に追加
    for fact_id in question.reveals:
        if fact_id not in state.observed_facts:
            state.observed_facts.add(fact_id)
            new_facts.append(fact_id)

    # 仮説の再評価
    new_hypotheses = evaluate_hypotheses(state, puzzle)

    # ピースの構成事実がすべて揃ったかチェック
    for piece in puzzle.pieces.values():
        if piece.id in state.discovered_pieces:
            continue
        if not all(f in state.observed_facts for f in piece.facts):
            continue
        if not all(dep in state.discovered_pieces for dep in piece.depends_on):
            continue
        state.discovered_pieces.add(piece.id)
        new_pieces.append(piece.id)

    # 履歴に記録
    state.answered.add(question.id)
    state.history.append(question.id)

    return AnswerResult(
        new_facts=new_facts,
        new_hypotheses=new_hypotheses,
        new_pieces=new_pieces,
        mechanism=question.mechanism,
        is_link=question.mechanism == "link",
        is_anomaly=question.mechanism == "anomaly",
    )


def check_complete(state: GameState, puzzle: PuzzleData) -> bool:
    """全ピース発見でクリア判定"""
    return all(p_id in state.discovered_pieces for p_id in puzzle.pieces)

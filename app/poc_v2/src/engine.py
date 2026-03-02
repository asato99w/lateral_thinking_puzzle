"""v2 POC: 探索領域ベースのパズルエンジン - コアロジック"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from models import (
    ExplorationDomain,
    Fact,
    GameState,
    Piece,
    Question,
    Strategy,
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
    domains: dict[str, ExplorationDomain]
    strategies: dict[str, Strategy]
    questions: dict[str, Question]


def load_puzzle(path: str | Path) -> PuzzleData:
    """JSON ファイルからパズルデータを読み込む"""
    with open(path, encoding="utf-8") as f:
        raw = json.load(f)

    facts = {item["id"]: Fact(**item) for item in raw["facts"]}
    pieces = {item["id"]: Piece(**item) for item in raw["pieces"]}
    domains = {
        item["id"]: ExplorationDomain(**item) for item in raw["exploration_domains"]
    }
    strategies = {item["id"]: Strategy(**item) for item in raw["strategies"]}
    questions = {item["id"]: Question(**item) for item in raw["questions"]}

    return PuzzleData(
        id=raw["id"],
        title=raw["title"],
        statement=raw["statement"],
        truth=raw["truth"],
        facts=facts,
        initial_facts=raw["initial_facts"],
        pieces=pieces,
        domains=domains,
        strategies=strategies,
        questions=questions,
    )


def init_game(puzzle: PuzzleData) -> GameState:
    """ゲーム初期化: S の事実を observed_facts に設定"""
    return GameState(
        observed_facts=set(puzzle.initial_facts),
        discovered_pieces=set(),
        opened_domains=set(),
        answered=set(),
        history=[],
    )


def available_questions(state: GameState, puzzle: PuzzleData) -> list[Question]:
    """利用可能な質問を返す: preconditions が満たされ、未回答のもの"""
    result = []
    for q in puzzle.questions.values():
        if q.id in state.answered:
            continue
        if all(pc in state.observed_facts for pc in q.preconditions):
            result.append(q)
    return result


@dataclass
class AnswerResult:
    """質問回答の結果"""

    new_facts: list[str]
    new_pieces: list[str]
    new_domains: list[str]
    mechanism: str
    is_link: bool
    is_anomaly: bool


def answer_question(
    state: GameState, question: Question, puzzle: PuzzleData
) -> AnswerResult:
    """質問に回答し、状態を更新する"""
    new_facts: list[str] = []
    new_pieces: list[str] = []
    new_domains: list[str] = []

    # reveals の事実を observed_facts に追加
    for fact_id in question.reveals:
        if fact_id not in state.observed_facts:
            state.observed_facts.add(fact_id)
            new_facts.append(fact_id)

    # ピースの構成事実がすべて揃ったかチェック
    for piece in puzzle.pieces.values():
        if piece.id in state.discovered_pieces:
            continue
        # 構成事実がすべて観測済みか
        if not all(f in state.observed_facts for f in piece.facts):
            continue
        # 依存ピースがすべて発見済みか
        if not all(dep in state.discovered_pieces for dep in piece.depends_on):
            continue
        state.discovered_pieces.add(piece.id)
        new_pieces.append(piece.id)

    # 独立ピース発見 → 探索領域を開放
    for domain in puzzle.domains.values():
        if domain.id in state.opened_domains:
            continue
        if domain.root_piece in state.discovered_pieces:
            state.opened_domains.add(domain.id)
            new_domains.append(domain.id)

    # 履歴に記録
    state.answered.add(question.id)
    state.history.append(question.id)

    return AnswerResult(
        new_facts=new_facts,
        new_pieces=new_pieces,
        new_domains=new_domains,
        mechanism=question.mechanism,
        is_link=question.mechanism == "link",
        is_anomaly=question.mechanism == "anomaly",
    )


def check_complete(state: GameState, puzzle: PuzzleData) -> bool:
    """全ピース発見でクリア判定"""
    return all(p_id in state.discovered_pieces for p_id in puzzle.pieces)

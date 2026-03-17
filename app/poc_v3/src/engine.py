"""v3 POC: パズルエンジン - コアロジック

v3 の導出は 2 段階:
1. 論理的導出（entailment_conditions）: confirmed → confirmed の不動点計算
2. 仮説導出（formation_conditions）: confirmed → derived の 1 回パス
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from models import (
    GameState,
    Piece,
    Proposition,
    Question,
)


@dataclass
class PuzzleData:
    """パズル定義データの集約"""

    id: str
    title: str
    statement: str
    truth: str
    propositions: dict[str, Proposition]
    initial_confirmed: list[str]
    clear_conditions: list[list[str]]  # OR of AND: クリア条件（命題IDの族）
    pieces: dict[str, Piece]
    questions: dict[str, Question]


def load_puzzle(path: str | Path) -> PuzzleData:
    """JSON ファイルからパズルデータを読み込む"""
    with open(path, encoding="utf-8") as f:
        raw = json.load(f)

    propositions = {}
    for item in raw["descriptors"]:
        p = Proposition(
            id=item["id"],
            label=item["label"],
            negation_of=item.get("negation_of"),
            formation_conditions=item.get("formation_conditions"),
            entailment_conditions=item.get("entailment_conditions"),
            rejection_conditions=item.get("rejection_conditions"),
        )
        propositions[p.id] = p

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
        propositions=propositions,
        initial_confirmed=raw["initial_confirmed"],
        clear_conditions=raw.get("clear_conditions", []),
        pieces=pieces,
        questions=questions,
    )


def init_game(puzzle: PuzzleData) -> GameState:
    """ゲーム初期化: initial_confirmed を confirmed に設定し、導出チェック"""
    state = GameState(confirmed=set(puzzle.initial_confirmed))
    evaluate_entailments(state, puzzle)
    evaluate_hypotheses(state, puzzle)
    return state


def evaluate_entailments(state: GameState, puzzle: PuzzleData) -> list[str]:
    """論理的導出: confirmed → confirmed の不動点計算。

    entailment_conditions が confirmed で満たされる命題を confirmed に追加する。
    論理的帰結であり連鎖は許容される。
    戻り値: 新たに confirmed に追加された命題のリスト
    """
    newly_confirmed = []
    changed = True
    while changed:
        changed = False
        for p in puzzle.propositions.values():
            if p.entailment_conditions is None:
                continue
            if p.id in state.confirmed:
                continue
            for cond_group in p.entailment_conditions:
                if all(c in state.confirmed for c in cond_group):
                    state.confirmed.add(p.id)
                    newly_confirmed.append(p.id)
                    changed = True
                    break
    return newly_confirmed


def evaluate_hypotheses(state: GameState, puzzle: PuzzleData) -> tuple[list[str], list[str]]:
    """仮説導出: confirmed → derived の 1 回パス。

    formation_conditions が confirmed で満たされる命題を derived とする。
    不動点計算は行わない（derived からの連鎖なし）。
    戻り値: (newly_derived, newly_rejected)
    """
    # Step 1: 棄却集合の計算（confirmed のみ参照）
    rejected = set()
    for p in puzzle.propositions.values():
        if p.rejection_conditions is not None:
            if any(all(c in state.confirmed for c in group) for group in p.rejection_conditions):
                rejected.add(p.id)

    # Step 2: 1 回パス（confirmed のみ参照、連鎖なし）
    new_derived = set()
    for p in puzzle.propositions.values():
        if p.formation_conditions is None:
            continue
        if p.id in state.confirmed or p.id in rejected:
            continue
        for cond_group in p.formation_conditions:
            if all(c in state.confirmed for c in cond_group):
                new_derived.add(p.id)
                break

    newly_derived = sorted(new_derived - state.derived)
    newly_rejected = sorted((state.derived - new_derived) - state.confirmed)
    state.derived = new_derived
    return newly_derived, newly_rejected


def _check_conditions(conditions: list[list[str]], state: GameState) -> bool:
    """OR of AND の条件判定: いずれかの条件セットが全て confirmed であれば True。

    v3 では confirmed のみで判定する。derived に入った命題を利用して
    質問を飛ばせる問題（可視化と実態の不一致）を防ぐ。
    """
    return any(
        all(c in state.confirmed for c in condition_set)
        for condition_set in conditions
    )


def _question_availability_conditions(q: Question, puzzle: PuzzleData) -> list[list[str]] | None:
    """質問の利用可能条件を返す。

    - 回答が「はい」→ reveals 先の命題の fc
    - 回答が「いいえ」→ reveals 先の命題の negation_of が指す命題の fc
    """
    if not q.reveals:
        return None
    prop = puzzle.propositions.get(q.reveals[0])
    if prop is None:
        return None
    if q.answer == "いいえ" and prop.negation_of is not None:
        target = puzzle.propositions.get(prop.negation_of)
        if target is not None:
            return target.formation_conditions
    return prop.formation_conditions


def available_questions(state: GameState, puzzle: PuzzleData) -> list[Question]:
    """利用可能な質問を返す: 前提条件が満たされ、reveals 先の命題が形成可能で、未回答のもの

    - 前提条件（prerequisites）: confirmed のみで判定。対話上で確立された事実。
    - 形成条件: reveals 先の命題の formation_conditions を confirmed のみで判定。
    """
    result = []
    for q in puzzle.questions.values():
        if q.id in state.answered:
            continue
        # reveals 先が全て confirmed なら表示しない（既知の情報）
        if q.reveals and all(r in state.confirmed for r in q.reveals):
            continue
        if q.prerequisites and not all(p in state.confirmed for p in q.prerequisites):
            continue
        fc = _question_availability_conditions(q, puzzle)
        if fc is None or _check_conditions(fc, state):
            result.append(q)
    return result


@dataclass
class AnswerResult:
    """質問回答の結果"""

    new_confirmed: list[str]  # reveals + 論理的導出
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

    # 1. reveals の命題を confirmed に追加
    for prop_id in question.reveals:
        if prop_id not in state.confirmed:
            state.confirmed.add(prop_id)
            new_confirmed.append(prop_id)

    # 2. 論理的導出（confirmed → confirmed の不動点計算）
    entailed = evaluate_entailments(state, puzzle)
    new_confirmed.extend(entailed)

    # 3. 仮説導出（confirmed → derived の 1 回パス）
    new_derived, new_rejected = evaluate_hypotheses(state, puzzle)

    # 4. ピースの構成命題がすべて揃ったかチェック（confirmed ∪ derived で判定）
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
    """クリア判定: clear_conditions（命題の族）のいずれかのグループが全て confirmed"""
    return any(
        all(prop_id in state.confirmed for prop_id in condition_set)
        for condition_set in puzzle.clear_conditions
    )

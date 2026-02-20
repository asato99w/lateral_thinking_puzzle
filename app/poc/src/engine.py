from __future__ import annotations
from typing import Dict, List, Tuple, Union
from models import Paradigm, Question, GameState

EPSILON = 0.2  # H(d) ≈ v の閾値
TENSION_THRESHOLD = 2  # パラダイムシフト発動の緊張閾値


def compute_effect(question: Question) -> list[tuple[str, int]] | list[str]:
    return question.effect


def init_game(
    ps_values: dict[str, int],
    paradigms: dict[str, Paradigm],
    init_paradigm_id: str,
    all_descriptor_ids: list[str],
) -> GameState:
    h = {d: 0.5 for d in all_descriptor_ids}
    o = {}

    # Ps を O に追加、H に反映
    for d_id, val in ps_values.items():
        h[d_id] = float(val)
        o[d_id] = val

    # 初期パラダイムで同化
    p_init = paradigms[init_paradigm_id]
    _assimilate_from_paradigm(h, o, p_init)

    return GameState(
        h=h,
        o=o,
        r=set(),
        p_current=init_paradigm_id,
    )


def init_questions(
    paradigm: Paradigm,
    questions: list[Question],
) -> list[Question]:
    result = []
    for q in questions:
        eff = compute_effect(q)
        if isinstance(eff, list) and len(eff) > 0 and isinstance(eff[0], tuple):
            for d_id, v in eff:
                pred = paradigm.prediction(d_id)
                if pred is not None and pred == v:
                    result.append(q)
                    break
    return result


def get_answer(question: Question) -> str:
    return question.correct_answer


def update(
    state: GameState,
    question: Question,
    paradigms: dict[str, Paradigm],
    all_questions: list[Question],
    current_open: list[Question],
) -> tuple[GameState, list[Question]]:
    # Step 1: 直接更新
    eff = compute_effect(question)
    if question.correct_answer == "irrelevant":
        for d_id in eff:
            state.r.add(d_id)
    else:
        for d_id, v in eff:
            state.h[d_id] = float(v)
            state.o[d_id] = v

    state.answered.add(question.id)

    p_current = paradigms[state.p_current]

    # Step 2: 同化
    if question.correct_answer != "irrelevant":
        for d_id, v in eff:
            pred = p_current.prediction(d_id)
            if pred is not None and pred == v:
                _assimilate_descriptor(state.h, d_id, p_current)

    # Step 3: パラダイムシフト判定
    current_tension = tension(state.o, p_current)
    if current_tension > TENSION_THRESHOLD:
        current_alignment = alignment(state.o, p_current)
        best_id = state.p_current
        best_score = current_alignment
        for p_id, p in paradigms.items():
            if p_id == state.p_current:
                continue
            score = alignment(state.o, p)
            if score > best_score:
                best_score = score
                best_id = p_id
        if best_id != state.p_current:
            state.p_current = best_id
            p_new = paradigms[best_id]
            _assimilate_from_paradigm(state.h, state.o, p_new)

    # Step 4: オープン更新（追加のみ、回答済みを除外）
    remaining = [q for q in current_open if q.id != question.id]
    remaining_ids = {q.id for q in remaining}
    newly_opened = [
        q for q in open_questions(state, all_questions)
        if q.id not in remaining_ids and q.id not in state.answered
    ]

    return state, remaining + newly_opened


def tension(o: dict[str, int], paradigm: Paradigm) -> int:
    """アノマリーの数。D(P) 内の観測で P の予測と矛盾するものを数える。"""
    overlap = paradigm.d_all & set(o.keys())
    return sum(
        1 for d in overlap if paradigm.prediction(d) != o[d]
    )


def alignment(o: dict[str, int], paradigm: Paradigm) -> float:
    """候補パラダイムの説明力。全観測に対する一致の割合。"""
    if not o:
        return 0.0
    match_count = sum(
        1 for d in paradigm.d_all & set(o.keys())
        if paradigm.prediction(d) == o[d]
    )
    return match_count / len(o)


def open_questions(
    state: GameState,
    questions: list[Question],
) -> list[Question]:
    result = []
    for q in questions:
        if q.id in state.answered:
            continue
        eff = compute_effect(q)
        if isinstance(eff, list) and len(eff) > 0 and isinstance(eff[0], tuple):
            for d_id, v in eff:
                if abs(state.h.get(d_id, 0.5) - v) < EPSILON:
                    result.append(q)
                    break
    return result


def check_clear(question: Question) -> bool:
    return question.is_clear


def _assimilate_descriptor(h: dict[str, float], d_id: str, paradigm: Paradigm):
    for src, tgt, w in paradigm.relations:
        if src == d_id:
            pred = paradigm.prediction(tgt)
            if pred is not None:
                h[tgt] = h.get(tgt, 0.5) + w * (float(pred) - h.get(tgt, 0.5))


def _assimilate_from_paradigm(
    h: dict[str, float],
    o: dict[str, int],
    paradigm: Paradigm,
):
    for d_id in set(o.keys()) & paradigm.d_all:
        pred = paradigm.prediction(d_id)
        if pred is not None and pred == o[d_id]:
            _assimilate_descriptor(h, d_id, paradigm)

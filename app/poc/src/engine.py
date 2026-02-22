from __future__ import annotations
from typing import Dict, List, Tuple, Union
from models import Paradigm, Question, GameState

EPSILON = 0.2  # H(d) ≈ v の閾値


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
    o: dict[str, int] | None = None,
) -> list[Question]:
    result = []
    for q in questions:
        if o is not None and not all(d in o for d in q.prerequisites):
            continue
        eff = compute_effect(q)
        if isinstance(eff, list) and len(eff) > 0 and isinstance(eff[0], tuple):
            has_match = False
            has_conflict = False
            for d_id, v in eff:
                pred = paradigm.prediction(d_id)
                if pred is not None:
                    if pred == v:
                        has_match = True
                    else:
                        has_conflict = True
            if has_match and not has_conflict:
                result.append(q)
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
        # 観測済み記述素の H は O の値を維持する（同化による上書きを防止）
        for d, v in state.o.items():
            state.h[d] = float(v)

    # Step 3: パラダイムシフト判定
    current_tension = tension(state.o, p_current)
    if p_current.threshold is not None and current_tension >= p_current.threshold:
        # シフト候補: 近傍かつアノマリーがより少ないパラダイム
        current_anomalies = current_tension
        candidates = [
            p_id for p_id in paradigms
            if p_id != state.p_current
            and paradigms[p_id].d_all & p_current.d_all
            and tension(state.o, paradigms[p_id]) < current_anomalies
        ]

        if candidates:
            best_id = candidates[0]
            best_score = alignment(state.h, paradigms[candidates[0]])
            for p_id in candidates[1:]:
                score = alignment(state.h, paradigms[p_id])
                if score > best_score:
                    best_score = score
                    best_id = p_id
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


def alignment(h: dict[str, float], paradigm: Paradigm) -> float:
    """H ベースの alignment。

    alignment_h(H, P) = (Σ_{d∈D⁺} H[d] + Σ_{d∈D⁻} (1 - H[d])) / |D(P)|

    H は連続値（0〜1）なので同点が実質的に発生しない。
    同化により H は現パラダイムの予測方向に押されているため、
    構造的に近いパラダイムが自然に高スコアになる。
    未観測・未同化の記述素は H[d] = 0.5 で中立的に寄与する。
    """
    d_all = paradigm.d_all
    if not d_all:
        return 0.0
    score = 0.0
    for d in d_all:
        h_val = h.get(d, 0.5)
        if d in paradigm.d_plus:
            score += h_val
        else:  # d in d_minus
            score += 1.0 - h_val
    return score / len(d_all)


def open_questions(
    state: GameState,
    questions: list[Question],
) -> list[Question]:
    result = []
    for q in questions:
        if q.id in state.answered:
            continue
        if not all(d in state.o for d in q.prerequisites):
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
    # 観測済み記述素の H は O の値を維持する
    for d, v in o.items():
        h[d] = float(v)

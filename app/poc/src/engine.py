from __future__ import annotations
from typing import Dict, List, Tuple, Union
from models import Paradigm, Question, GameState

EPSILON = 0.2  # H(d) ≈ v の閾値


def _question_all_descriptors(q: Question) -> set[str]:
    """質問が参照する全記述素（効果記述素 + 関連記述素の和集合）。"""
    ds: set[str] = set()
    for d, v in q.ans_yes:
        ds.add(d)
    for d, v in q.ans_no:
        ds.add(d)
    for d in q.ans_irrelevant:
        ds.add(d)
    for d in q.related_descriptors:
        ds.add(d)
    return ds


def _conceivable_blocked(q: Question, conceivable: set[str]) -> bool:
    """質問の参照記述素のいずれかが Conceivable(P) 外ならブロック。"""
    for d in _question_all_descriptors(q):
        if d not in conceivable:
            return True
    return False


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
        if _conceivable_blocked(q, paradigm.conceivable):
            continue
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


def explained_o(o: dict[str, int], paradigm: Paradigm) -> int:
    """O ∩ Predictions(P) のうち一致するものの数。"""
    count = 0
    for d_id, v in o.items():
        pred = paradigm.prediction(d_id)
        if pred is not None and pred == v:
            count += 1
    return count


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

    # Step 3: パラダイムシフト判定（最小緩和原理）
    current_tension = tension(state.o, p_current)
    if p_current.threshold is not None and current_tension > p_current.threshold:
        best_id = select_shift_target(state.o, p_current, paradigms)
        if best_id is not None:
            state.p_current = best_id
            p_new = paradigms[best_id]
            _assimilate_from_paradigm(state.h, state.o, p_new)

    # Step 4: オープン更新（追加のみ、回答済みを除外）
    remaining = [q for q in current_open if q.id != question.id]
    remaining_ids = {q.id for q in remaining}
    newly_opened = [
        q for q in open_questions(state, all_questions, paradigms)
        if q.id not in remaining_ids and q.id not in state.answered
    ]

    return state, remaining + newly_opened


def select_shift_target(
    o: dict[str, int],
    p_current: Paradigm,
    paradigms: dict[str, Paradigm],
) -> str | None:
    """最小緩和原理に基づくシフト先選択。

    候補: tension(O, P') <= tension(O, P_current) かつ P' != P_current
    多段タイブレーク:
      1. tension DESC（最小緩和 = tension が最大の候補を優先）
      2. attention DESC（P_current のアノマリーのうち P' の Conceivable に含まれる数）
      3. resolve ASC（P_current のアノマリーのうち P' が正しく予測する数が少ない方）
      4. pid ASC（決定的にするため）
    """
    # P_current のアノマリー集合
    anomalies = {
        d for d in p_current.conceivable
        if d in o and p_current.prediction(d) is not None
        and p_current.prediction(d) != o[d]
    }
    cur_tension = tension(o, p_current)

    candidates = []
    for pid, p in paradigms.items():
        if pid == p_current.id:
            continue
        t = tension(o, p)
        if t <= cur_tension:
            att = len({d for d in anomalies if d in p.conceivable})
            res = len({d for d in anomalies
                       if d in p.conceivable
                       and p.prediction(d) is not None and p.prediction(d) == o[d]})
            candidates.append((pid, t, att, res))

    if not candidates:
        return None

    # tension DESC → attention DESC → resolve ASC → pid ASC
    candidates.sort(key=lambda x: (-x[1], -x[2], x[3], x[0]))
    return candidates[0][0]


def tension(o: dict[str, int], paradigm: Paradigm) -> int:
    """アノマリーの数。Conceivable(P) ∩ O で P の予測と矛盾するものを数える。"""
    count = 0
    for d in paradigm.conceivable:
        if d in o:
            pred = paradigm.prediction(d)
            if pred is not None and pred != o[d]:
                count += 1
    return count


def alignment(h: dict[str, float], paradigm: Paradigm) -> float:
    """H ベースの alignment。

    P_pred で予測がある d について H(d) と p_pred(d) の一致度を計算。
    P_pred の大きさに依存しない（P_pred 絞り込みとは分離）。
    """
    pred_items = paradigm.p_pred
    if not pred_items:
        return 0.0
    score = 0.0
    count = 0
    for d, pred_val in pred_items.items():
        h_val = h.get(d, 0.5)
        if pred_val == 1:
            score += h_val
        else:  # pred_val == 0
            score += 1.0 - h_val
        count += 1
    return score / count if count > 0 else 0.0


def open_questions(
    state: GameState,
    questions: list[Question],
    paradigms: dict[str, Paradigm] | None = None,
) -> list[Question]:
    conceivable = set()
    if paradigms and state.p_current in paradigms:
        conceivable = paradigms[state.p_current].conceivable
    result = []
    for q in questions:
        if q.id in state.answered:
            continue
        if conceivable and _conceivable_blocked(q, conceivable):
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
    for d_id in set(o.keys()) & paradigm.conceivable:
        pred = paradigm.prediction(d_id)
        if pred is not None and pred == o[d_id]:
            _assimilate_descriptor(h, d_id, paradigm)
    # 観測済み記述素の H は O の値を維持する
    for d, v in o.items():
        h[d] = float(v)

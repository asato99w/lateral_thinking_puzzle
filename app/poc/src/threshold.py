"""パラダイムの緊張閾値を近傍と完全確定 O* から導出する。"""
from __future__ import annotations

from models import Paradigm, Question
from engine import tension


def build_o_star(
    questions: list[Question],
    ps_values: dict[str, int],
) -> dict[str, int]:
    """完全確定 O* を構築する。全質問の正解と Ps から観測状態を集約。"""
    o_star: dict[str, int] = {}
    for d_id, val in ps_values.items():
        o_star[d_id] = val
    for q in questions:
        if q.correct_answer == "irrelevant":
            continue
        for d_id, v in q.effect:
            o_star[d_id] = v
    return o_star


def compute_thresholds(
    paradigms: dict[str, Paradigm],
    o_star: dict[str, int],
) -> None:
    """各パラダイムの threshold を近傍と O* から導出し、Paradigm に設定する。

    threshold(P) = max { anomalies(O*, P') | P' ∈ N(P), anomalies(O*, P') < anomalies(O*, P) }
    """
    anomalies = {}
    for pid, p in paradigms.items():
        anomalies[pid] = tension(o_star, p)

    for pid, p in paradigms.items():
        my_anomalies = anomalies[pid]
        better_neighbor_anomalies = [
            anomalies[pid2]
            for pid2, p2 in paradigms.items()
            if pid2 != pid
            and p.d_all & p2.d_all
            and anomalies[pid2] < my_anomalies
        ]
        if better_neighbor_anomalies:
            p.threshold = max(better_neighbor_anomalies)
        else:
            p.threshold = None

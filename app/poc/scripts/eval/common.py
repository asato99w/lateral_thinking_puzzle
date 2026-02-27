"""評価スクリプト共通モジュール。"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from models import Paradigm, Question  # noqa: E402
from engine import compute_effect, select_shift_target  # noqa: E402
from threshold import build_o_star, compute_neighborhoods, compute_resolve_caps, compute_depths  # noqa: E402


DATA_DIR = Path(__file__).parent.parent.parent / "data"
DEFAULT_DATA = "turtle_soup.json"


def resolve_data_path() -> Path:
    """コマンドライン引数 --data <name> があればそのファイルを返す。"""
    for i, arg in enumerate(sys.argv):
        if arg == "--data" and i + 1 < len(sys.argv):
            name = sys.argv[i + 1]
            path = DATA_DIR / name
            if not path.exists():
                path = Path(name)
            return path
    return DATA_DIR / DEFAULT_DATA


def load_raw(data_path: Path | None = None) -> dict:
    """JSON データを辞書として読み込む。"""
    if data_path is None:
        data_path = resolve_data_path()
    with open(data_path, encoding="utf-8") as f:
        return json.load(f)


def load_data(data_path: Path | None = None):
    """データを読み込む。

    data_path を省略すると --data 引数 → デフォルト(turtle_soup.json) の順で決定。
    返り値: (paradigms, questions, all_descriptor_ids, ps_values, init_paradigm)
    """
    data = load_raw(data_path)

    paradigms = {}
    for p in data["paradigms"]:
        paradigms[p["id"]] = Paradigm(
            id=p["id"],
            name=p["name"],
            p_pred={d: v for d, v in p["p_pred"]},
            relations=[(r[0], r[1], r[2]) for r in p["relations"]],
        )

    questions = []
    for q in data["questions"]:
        questions.append(Question(
            id=q["id"],
            text=q["text"],
            ans_yes=[(a[0], a[1]) for a in q["ans_yes"]],
            ans_no=[(a[0], a[1]) for a in q["ans_no"]],
            ans_irrelevant=q["ans_irrelevant"],
            correct_answer=q["correct_answer"],
            is_clear=q.get("is_clear", False),
            prerequisites=q.get("prerequisites", []),
            related_descriptors=q.get("related_descriptors", []),
            topic_category=q.get("topic_category", ""),
            paradigms=q.get("paradigms", []),
        ))

    ps_values = {d[0]: d[1] for d in data["ps_values"]}

    # JSON に shift_threshold があれば読み込む
    paradigm_map = {p["id"]: p for p in data["paradigms"]}
    for pid, p in paradigms.items():
        raw = paradigm_map.get(pid, {})
        if "shift_threshold" in raw:
            p.shift_threshold = raw["shift_threshold"]

    # 完全確定 O* から近傍・resolve上限・深度を導出
    o_star = build_o_star(questions, ps_values)
    compute_neighborhoods(paradigms, o_star)
    resolve_caps = compute_resolve_caps(paradigms, o_star)
    compute_depths(paradigms, o_star)

    return (
        paradigms,
        questions,
        data["all_descriptor_ids"],
        ps_values,
        data["init_paradigm"],
        resolve_caps,
    )


# ---------------------------------------------------------------------------
# 共通ヘルパー
# ---------------------------------------------------------------------------


def derive_qp(questions, paradigm):
    """Q(P) を導出する。データの所属パラダイム (question.paradigms) に基づく。"""
    pid = paradigm.id
    return [q for q in questions if pid in q.paradigms]


def get_truth(questions):
    """全質問の correct_answer から各記述素の真理値（T に相当）を導出する。"""
    truth = {}
    for q in questions:
        if q.correct_answer == "irrelevant":
            continue
        eff = compute_effect(q)
        for d, v in eff:
            truth[d] = v
    return truth


def classify_questions(questions, paradigm):
    """質問を safe / anomaly に分類する。"""
    safe, anomaly = [], []
    for q in questions:
        eff = compute_effect(q)
        if q.correct_answer == "irrelevant":
            safe.append(q)
            continue
        has_anomaly = False
        for d_id, v in eff:
            pred = paradigm.prediction(d_id)
            if pred is not None and pred != v:
                has_anomaly = True
                break
        if has_anomaly:
            anomaly.append(q)
        else:
            safe.append(q)
    return safe, anomaly


def neighbor_pairs(paradigms):
    """全近傍ペア (P, P') を返す。P' ∈ neighbors(P) となるペア。"""
    pairs = []
    for pid, p in paradigms.items():
        for nb_pid in sorted(p.neighbors):
            pairs.append((pid, nb_pid))
    return pairs


def compute_o_star_shift_chain(init_pid, paradigms, questions, resolve_caps=None):
    """O*（全質問回答の理想観測）のもとでシフト連鎖を計算する。"""
    o_star = {}
    for q in questions:
        if q.correct_answer == "irrelevant":
            continue
        eff = compute_effect(q)
        for d_id, v in eff:
            o_star[d_id] = v

    path = [init_pid]
    visited = {init_pid}
    current = init_pid
    while True:
        p_cur = paradigms[current]
        nxt = select_shift_target(o_star, p_cur, paradigms, resolve_caps)
        if nxt is None or nxt in visited:
            break
        path.append(nxt)
        visited.add(nxt)
        current = nxt

    return path

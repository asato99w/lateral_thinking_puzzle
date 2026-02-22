"""評価スクリプト共通モジュール。"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from models import Paradigm, Question  # noqa: E402
from threshold import build_o_star, compute_thresholds  # noqa: E402


DATA_DIR = Path(__file__).parent.parent.parent / "data"
DEFAULT_DATA = "turtle_soup.json"

# 後方互換: 既存スクリプトが MAIN_PATH を参照している場合のデフォルト
MAIN_PATH = ["P1", "P2", "P3", "P4", "P5"]


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
    global MAIN_PATH

    data = load_raw(data_path)

    # main_path: データに定義があればそちらを使う（in-place 更新で import 先にも反映）
    if "main_path" in data:
        MAIN_PATH[:] = data["main_path"]

    paradigms = {}
    for p in data["paradigms"]:
        paradigms[p["id"]] = Paradigm(
            id=p["id"],
            name=p["name"],
            d_plus=set(p["d_plus"]),
            d_minus=set(p["d_minus"]),
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
        ))

    ps_values = {d[0]: d[1] for d in data["ps_values"]}

    # 完全確定 O* から threshold を導出
    o_star = build_o_star(questions, ps_values)
    compute_thresholds(paradigms, o_star)

    return (
        paradigms,
        questions,
        data["all_descriptor_ids"],
        ps_values,
        data["init_paradigm"],
    )

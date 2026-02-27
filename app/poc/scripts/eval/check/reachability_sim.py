"""到達パス検証スクリプト（L2-5）。

ゲームシミュレーションにより、行き詰まり（T に到達する前に
オープン質問が尽きる状態）が存在しないことを検証する。

全ての質問選択順で T に到達すべきであり、1つでも行き詰まりが
あれば NG とする。複数の選択順で試行する:
  - 先頭順（決定的）
  - ランダムシャッフル（確率的、N_RANDOM 回）

使い方:
  python reachability_sim.py                       # turtle_soup.json
  python reachability_sim.py --data bar_man.json   # bar_man.json
"""
from __future__ import annotations

import copy
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from common import load_data, load_raw  # noqa: E402
from engine import (  # noqa: E402
    init_game,
    open_questions,
    update,
)


def get_init_open(data_raw, questions):
    """データの init_question_ids から初期オープン質問を返す。"""
    if "init_question_ids" not in data_raw:
        return []
    id_set = set(data_raw["init_question_ids"])
    return [q for q in questions if q.id in id_set]

N_RANDOM = 50
MAX_STEPS = 500


def find_truth_paradigm(paradigms):
    """後方互換用。load_data の truth_paradigm を使うことを推奨。"""
    return max(paradigms, key=lambda pid: paradigms[pid].depth or 0)


def simulate_game(paradigms, questions, ps_values, all_ids, init_pid, t_pid,
                  init_open, resolve_caps=None, order="sequential", seed=None):
    """ゲームを1回シミュレーションする。

    Args:
        init_open: 初期オープン質問リスト
        order: "sequential"（先頭順）or "random"（ランダム）
        seed: ランダムシード

    Returns:
        {
            "reached_t": bool,
            "path": [pid, ...],  # パラダイム遷移の履歴
            "steps": int,
            "final_paradigm": str,
        }
    """
    rng = random.Random(seed)
    state = init_game(ps_values, paradigms, init_pid, all_ids)
    current_open = list(init_open)

    path = [init_pid]
    step = 0

    while step < MAX_STEPS:
        # オープンかつ未回答の質問を取得
        available = [q for q in current_open if q.id not in state.answered]
        if not available:
            break

        # 質問選択
        if order == "random":
            q = rng.choice(available)
        else:
            q = available[0]

        step += 1
        pid_before = state.p_current

        state, current_open = update(
            state, q, paradigms, questions, current_open, resolve_caps,
        )

        # パラダイムシフト検出
        if state.p_current != pid_before:
            path.append(state.p_current)
            if state.p_current == t_pid:
                return {
                    "reached_t": True,
                    "path": path,
                    "steps": step,
                    "final_paradigm": state.p_current,
                }

    return {
        "reached_t": state.p_current == t_pid,
        "path": path,
        "steps": step,
        "final_paradigm": state.p_current,
    }


def main():
    paradigms, questions, all_ids, ps_values, init_pid, resolve_caps, t_pid = load_data()
    data_raw = load_raw()
    init_open = get_init_open(data_raw, questions)

    print("=" * 65)
    print("到達パス検証 (L2-5)")
    print("=" * 65)
    print(f"init: {init_pid}")
    print(f"T: {t_pid}")
    print(f"試行: 先頭順 × 1 + ランダム × {N_RANDOM}")
    print()

    results = []

    # 先頭順
    print("-" * 50)
    print("先頭順シミュレーション")
    print("-" * 50)
    r = simulate_game(paradigms, questions, ps_values, all_ids, init_pid, t_pid,
                      init_open, resolve_caps, order="sequential")
    results.append(r)
    status = "OK" if r["reached_t"] else "NG"
    print(f"  結果: {status}")
    print(f"  パス: {' → '.join(r['path'])}")
    print(f"  ステップ数: {r['steps']}")
    print(f"  最終パラダイム: {r['final_paradigm']}")
    print()

    # ランダム試行
    print("-" * 50)
    print(f"ランダムシミュレーション ({N_RANDOM}回)")
    print("-" * 50)
    reached_count = 0
    paths_seen = {}
    for i in range(N_RANDOM):
        r = simulate_game(paradigms, questions, ps_values, all_ids, init_pid, t_pid,
                          init_open, resolve_caps, order="random", seed=i)
        results.append(r)
        if r["reached_t"]:
            reached_count += 1
        path_key = " → ".join(r["path"])
        if path_key not in paths_seen:
            paths_seen[path_key] = {"count": 0, "steps_min": r["steps"],
                                     "steps_max": r["steps"], "reached": r["reached_t"]}
        paths_seen[path_key]["count"] += 1
        paths_seen[path_key]["steps_min"] = min(paths_seen[path_key]["steps_min"], r["steps"])
        paths_seen[path_key]["steps_max"] = max(paths_seen[path_key]["steps_max"], r["steps"])

    print(f"  T到達: {reached_count}/{N_RANDOM}")
    print(f"  観測されたパス:")
    for path_key, info in sorted(paths_seen.items(), key=lambda x: -x[1]["count"]):
        status = "OK" if info["reached"] else "NG"
        print(f"    [{status}] {path_key} (×{info['count']}, "
              f"steps {info['steps_min']}-{info['steps_max']})")
    print()

    # 総合結果
    total_reached = sum(1 for r in results if r["reached_t"])
    total_trials = len(results)
    deadlocks = total_trials - total_reached

    print("=" * 65)
    if deadlocks == 0:
        print(f"総合結果: OK — 全試行で T に到達 ({total_trials}/{total_trials})")
    else:
        print(f"総合結果: NG — 行き詰まりあり ({deadlocks}/{total_trials} 試行で T 未到達)")
    print("=" * 65)


if __name__ == "__main__":
    main()

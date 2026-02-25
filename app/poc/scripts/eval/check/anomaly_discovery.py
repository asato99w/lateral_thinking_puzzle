"""anomaly質問の発掘検証スクリプト。

Part 1: 初期オープンにanomaly質問が含まれていないかチェック
Part 2: 同化連鎖によるanomaly発掘シミュレーション
"""
from __future__ import annotations

import copy
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from common import load_data, MAIN_PATH  # noqa: E402
from engine import (
    compute_effect,
    init_game,
    init_questions,
    open_questions,
    update,
    EPSILON,
)


# ── helpers ──────────────────────────────────────────


def classify_questions(
    questions: list,
    p_init,
) -> tuple[list, list]:
    """質問を safe / anomaly に分類する。

    safe:    effectの全(d, v)がP_initの予測と一致
    anomaly: effectに1つでもP_initの予測と矛盾する(d, v)を含む
    """
    safe, anomaly = [], []
    for q in questions:
        eff = compute_effect(q)
        if q.correct_answer == "irrelevant":
            safe.append(q)
            continue
        has_anomaly = False
        for d_id, v in eff:
            pred = p_init.prediction(d_id)
            if pred is not None and pred != v:
                has_anomaly = True
                break
        if has_anomaly:
            anomaly.append(q)
        else:
            safe.append(q)
    return safe, anomaly


# ── Part 1 ───────────────────────────────────────────


def check_init_contamination(
    paradigms: dict,
    questions: list,
    init_paradigm_id: str,
) -> list:
    """初期オープンにanomaly質問が含まれているかチェック。"""
    p_init = paradigms[init_paradigm_id]
    init_qs = init_questions(p_init, questions)
    _, anomaly_qs = classify_questions(questions, p_init)
    anomaly_ids = {q.id for q in anomaly_qs}

    contaminated = [q for q in init_qs if q.id in anomaly_ids]
    return contaminated


# ── Part 2 ───────────────────────────────────────────


def simulate_discovery(
    paradigms: dict,
    questions: list,
    all_descriptor_ids: list,
    ps_values: dict,
    init_paradigm_id: str,
) -> tuple[list[dict], set[str], set[str]]:
    """同化連鎖によるanomaly発掘シミュレーション。

    Returns:
        chain: 発掘チェーンのリスト (各ステップの情報)
        discovered: 発掘されたanomaly質問IDの集合
        undiscovered: 発掘できなかったanomaly質問IDの集合
    """
    p_init = paradigms[init_paradigm_id]
    safe_qs, anomaly_qs = classify_questions(questions, p_init)
    anomaly_ids = {q.id for q in anomaly_qs}

    if not anomaly_ids:
        return [], set(), set()

    # ゲーム初期化
    state = init_game(ps_values, paradigms, init_paradigm_id, all_descriptor_ids)

    # safe質問のみで初期オープンを構成
    init_safe = [q for q in init_questions(p_init, questions)
                 if q.id not in anomaly_ids]
    current_open = list(init_safe)

    discovered = set()
    chain = []
    q_by_id = {q.id: q for q in questions}

    # 回答キュー: safe質問から開始
    answer_queue = list(init_safe)
    queued_ids = {q.id for q in answer_queue}

    step = 0
    while answer_queue:
        q = answer_queue.pop(0)
        if q.id in state.answered:
            continue

        step += 1
        open_before = {oq.id for oq in current_open}
        h_before = copy.copy(state.h)
        p_before = state.p_current

        state, current_open = update(
            state, q, paradigms, questions, current_open,
        )

        open_after = {oq.id for oq in current_open}
        newly_opened = open_after - open_before - {q.id}

        # H変化の検出
        h_changes = {}
        for d_id in state.h:
            old = h_before.get(d_id, 0.5)
            new = state.h[d_id]
            if abs(new - old) > 1e-9:
                h_changes[d_id] = (old, new)

        # 新規オープンの中でanomalyを発掘
        new_anomalies = newly_opened & anomaly_ids
        if new_anomalies:
            discovered |= new_anomalies
            chain.append({
                "step": step,
                "answered": q.id,
                "paradigm_before": p_before,
                "paradigm_after": state.p_current,
                "h_changes": h_changes,
                "newly_opened_all": sorted(newly_opened),
                "anomalies_discovered": sorted(new_anomalies),
            })
            # 発掘されたanomaly質問もキューに追加
            for aid in sorted(new_anomalies):
                if aid not in queued_ids:
                    answer_queue.append(q_by_id[aid])
                    queued_ids.add(aid)

        # 新規オープンのsafe質問もキューに追加
        for nid in sorted(newly_opened - anomaly_ids):
            if nid not in queued_ids:
                answer_queue.append(q_by_id[nid])
                queued_ids.add(nid)

    undiscovered = anomaly_ids - discovered
    return chain, discovered, undiscovered


# ── main ─────────────────────────────────────────────


def main():
    paradigms, questions, all_ids, ps_values, init_pid = load_data()
    p_init = paradigms[init_pid]

    print("=" * 60)
    print("anomaly発掘検証")
    print("=" * 60)

    # ── classify ──
    safe_qs, anomaly_qs = classify_questions(questions, p_init)
    print(f"\n全質問数: {len(questions)}")
    print(f"  safe質問: {len(safe_qs)}")
    print(f"  anomaly質問: {len(anomaly_qs)}")
    if anomaly_qs:
        print(f"  anomaly IDs: {[q.id for q in anomaly_qs]}")

    # ── Part 1 ──
    print("\n" + "-" * 60)
    print("Part 1: 初期オープンanomaly汚染チェック")
    print("-" * 60)

    contaminated = check_init_contamination(paradigms, questions, init_pid)
    init_qs = init_questions(p_init, questions)
    print(f"\n初期オープン質問数: {len(init_qs)}")
    print(f"  うちanomaly質問: {len(contaminated)}")
    if contaminated:
        print(f"  汚染質問: {[q.id for q in contaminated]}")
        for q in contaminated:
            eff = compute_effect(q)
            anomaly_ds = []
            if q.correct_answer != "irrelevant":
                for d_id, v in eff:
                    pred = p_init.prediction(d_id)
                    if pred is not None and pred != v:
                        anomaly_ds.append(f"{d_id}(pred={pred},actual={v})")
            print(f"    {q.id}: anomaly ds = {anomaly_ds}")
    print(f"\n結果: {'NG — anomaly質問が初期オープンに含まれている' if contaminated else 'OK'}")

    # ── Part 2 ──
    print("\n" + "-" * 60)
    print("Part 2: 同化連鎖によるanomaly発掘シミュレーション")
    print("-" * 60)

    if not anomaly_qs:
        print("\nanomaly質問がないためスキップ。")
        return

    chain, discovered, undiscovered = simulate_discovery(
        paradigms, questions, all_ids, ps_values, init_pid,
    )

    print(f"\n発掘チェーン ({len(chain)} ステップでanomaly発掘):")
    for entry in chain:
        print(f"\n  Step {entry['step']}: {entry['answered']} を回答")
        if entry["paradigm_before"] != entry["paradigm_after"]:
            print(f"    パラダイムシフト: {entry['paradigm_before']} → {entry['paradigm_after']}")
        if entry["h_changes"]:
            top_changes = sorted(
                entry["h_changes"].items(),
                key=lambda x: abs(x[1][1] - x[1][0]),
                reverse=True,
            )[:5]
            for d_id, (old, new) in top_changes:
                print(f"    H変化: {d_id}: {old:.3f} → {new:.3f}")
            if len(entry["h_changes"]) > 5:
                print(f"    ... 他 {len(entry['h_changes']) - 5} 件")
        print(f"    新規オープン: {entry['newly_opened_all']}")
        print(f"    → anomaly発掘: {entry['anomalies_discovered']}")

    print(f"\n--- 発掘サマリ ---")
    print(f"  発掘可能: {sorted(discovered)} ({len(discovered)}/{len(anomaly_qs)})")
    if undiscovered:
        print(f"  発掘不可: {sorted(undiscovered)}")
    print(f"\n結果: {'OK — 全anomaly質問が発掘可能' if not undiscovered else 'NG — 発掘不可のanomaly質問がある'}")


if __name__ == "__main__":
    main()

"""動的発掘連鎖検証スクリプト（L2-3）。

ゲーム全体をシミュレーションし:
  1. データ駆動の init_questions（なければ Q(P_init) の safe 質問で代替）から開始
  2. 各回答 → O 更新 → R(P) 到達性によるオープン判定 → 新規質問オープンを追跡
  3. 各パラダイムフェーズで:
     - オープンされた質問の順序
     - アノマリー導入質問が実際にオープンされたか
     - シフト発動のタイミングと遷移先
  4. 全パラダイムを通じて固有アノマリーが発掘されたかの最終確認

固有アノマリー = Anomaly(P) - SharedAnomaly(P)
上位パラダイムと共有されたアノマリーは先行フェーズで O に入るため除外する。

使い方:
  python excavation_chain.py                       # turtle_soup.json
  python excavation_chain.py --data bar_man.json   # bar_man.json
"""
from __future__ import annotations

import sys
from pathlib import Path
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from common import (  # noqa: E402
    load_data,
    load_raw,
    derive_qp,
    classify_questions,
    compute_o_star_shift_chain,
    get_truth,
)
from engine import (  # noqa: E402
    compute_effect,
    init_game,
    update,
    tension,
    select_shift_target,
)


def get_init_open(data_raw, paradigms, questions, init_pid, ps_values, all_ids):
    """初期オープン質問を決定する。"""
    if "init_question_ids" in data_raw:
        id_set = set(data_raw["init_question_ids"])
        return [q for q in questions if q.id in id_set], "data-driven"

    # フォールバック: Q(P_init) の safe 質問
    p_init = paradigms[init_pid]
    qp = derive_qp(questions, p_init)
    safe_qs, _ = classify_questions(qp, p_init)
    return safe_qs, "fallback (Q(P_init) safe)"


def compute_anomaly_sets(paradigms, truth):
    """各パラダイムのアノマリー記述素集合を計算する。"""
    return {
        pid: {
            d for d, pred in p.p_pred.items()
            if truth.get(d) is not None and pred != truth[d]
        }
        for pid, p in paradigms.items()
    }


def compute_unique_anomalies(pid, anomaly_sets):
    """固有アノマリー = Anomaly(P) のうち他のどのパラダイムにも属さないもの。"""
    others = set()
    for other_pid, other_anom in anomaly_sets.items():
        if other_pid != pid:
            others |= other_anom
    return anomaly_sets[pid] - others


def main():
    paradigms, questions, all_ids, ps_values, init_pid, _caps, _tp = load_data()
    data_raw = load_raw()
    reach_path = compute_o_star_shift_chain(init_pid, paradigms, questions)
    truth = get_truth(questions)
    anomaly_sets = compute_anomaly_sets(paradigms, truth)

    print("=" * 65)
    print("動的発掘連鎖検証 (L2-3)")
    print("=" * 65)
    print(f"O*シフト連鎖: {' → '.join(reach_path)}")
    print()

    # ゲーム初期化
    state = init_game(ps_values, paradigms, init_pid, all_ids)

    # 初期オープン質問
    init_open, init_mode = get_init_open(
        data_raw, paradigms, questions, init_pid, ps_values, all_ids,
    )
    current_open = list(init_open)
    print(f"初期オープン方式: {init_mode}")
    print(f"初期オープン質問: {[q.id for q in current_open]}")
    print()

    # 追跡用データ
    phase_log = defaultdict(lambda: {
        "opened_order": [],
        "anomaly_opened": [],
        "shift_step": None,
        "shift_target": None,
    })
    step = 0
    all_discovered_anomalies = set()

    # 回答キュー
    answer_queue = list(current_open)
    queued_ids = {q.id for q in answer_queue}

    # フェーズごとのアノマリー質問 ID
    phase_anomaly_qids = {}
    for pid in reach_path:
        p = paradigms[pid]
        qp = derive_qp(questions, p)
        _, anomaly_qs = classify_questions(qp, p)
        phase_anomaly_qids[pid] = {q.id for q in anomaly_qs}

    while answer_queue:
        q = answer_queue.pop(0)
        if q.id in state.answered:
            continue

        step += 1
        pid_before = state.p_current

        # 記録: オープン順序
        phase_log[pid_before]["opened_order"].append(q.id)
        if q.id in phase_anomaly_qids.get(pid_before, set()):
            phase_log[pid_before]["anomaly_opened"].append(q.id)

        # 回答 → O 更新 → 同化 → 新規オープン
        state, current_open = update(
            state, q, paradigms, questions, current_open,
        )

        # アノマリー記述素の発掘追跡
        for pid in reach_path:
            p = paradigms[pid]
            for d, pred in p.p_pred.items():
                if d in state.o and pred != state.o[d]:
                    all_discovered_anomalies.add((pid, d))

        # シフト検出
        if state.p_current != pid_before:
            phase_log[pid_before]["shift_step"] = step
            phase_log[pid_before]["shift_target"] = state.p_current

        # 新規オープンをキューに追加
        for oq in current_open:
            if oq.id not in queued_ids and oq.id not in state.answered:
                answer_queue.append(oq)
                queued_ids.add(oq.id)

    # 結果出力
    all_ok = True

    for pid in reach_path:
        p = paradigms[pid]
        log = phase_log[pid]
        all_anom = anomaly_sets[pid]
        unique_anom = compute_unique_anomalies(pid, anomaly_sets)

        print(f"-" * 50)
        print(f"パラダイム: {pid} ({p.name})")
        print(f"-" * 50)

        # オープン順序
        opened = log["opened_order"]
        print(f"  回答した質問数: {len(opened)}")
        if opened:
            print(f"  回答順序: {opened}")

        # アノマリー質問のオープン状況
        expected_anomaly = phase_anomaly_qids.get(pid, set())
        actual_anomaly = set(log["anomaly_opened"])
        missed_anomaly = expected_anomaly - actual_anomaly
        print(f"  アノマリー質問:")
        print(f"    期待: {sorted(expected_anomaly)}")
        print(f"    実際にオープン: {sorted(actual_anomaly)}")
        if missed_anomaly:
            print(f"    未オープン: {sorted(missed_anomaly)}")
        else:
            if expected_anomaly:
                print(f"    全アノマリー質問オープン: OK")

        # アノマリー記述素の発掘状況（固有アノマリーのみ判定）
        discovered_for_pid = {d for (p2, d) in all_discovered_anomalies if p2 == pid}
        discovered_unique = discovered_for_pid & unique_anom
        undiscovered_unique = unique_anom - discovered_for_pid
        shared = all_anom - unique_anom
        print(f"  アノマリー記述素:")
        print(f"    全体: {len(all_anom)}個 {sorted(all_anom)}")
        if shared:
            print(f"    上位共有: {len(shared)}個 {sorted(shared)}")
        print(f"    固有: {len(unique_anom)}個 {sorted(unique_anom)}")
        print(f"    固有発掘済み: {len(discovered_unique)}個 {sorted(discovered_unique)}")
        if undiscovered_unique:
            print(f"    未発掘固有: {sorted(undiscovered_unique)}")
            all_ok = False
        else:
            if unique_anom:
                print(f"    固有完全性: OK")

        # シフト
        if log["shift_step"] is not None:
            print(f"  シフト: step {log['shift_step']} → {log['shift_target']}")
        else:
            if pid != reach_path[-1]:
                print(f"  シフト: 未発動")

        print()

    # 横方向探索の動的検証サマリ
    print(f"-" * 50)
    print("横方向探索サマリ")
    print(f"-" * 50)
    print(f"  総回答ステップ: {step}")
    print(f"  オープンした質問総数: {len(queued_ids)}")

    # 全パラダイムの固有アノマリー記述素の合計
    total_unique = set()
    total_discovered_unique = set()
    for pid in reach_path:
        unique = compute_unique_anomalies(pid, anomaly_sets)
        for d in unique:
            total_unique.add((pid, d))
        discovered_for_pid = {d for (p2, d) in all_discovered_anomalies if p2 == pid}
        for d in (discovered_for_pid & unique):
            total_discovered_unique.add((pid, d))

    total_undiscovered = total_unique - total_discovered_unique
    print(f"  固有アノマリー記述素: {len(total_unique)}個")
    print(f"  発掘済み: {len(total_discovered_unique)}個")
    if total_undiscovered:
        print(f"  未発掘: {sorted(total_undiscovered)}")
        all_ok = False
    else:
        print(f"  全固有アノマリー発掘: OK")

    print()

    # 総合結果
    print("=" * 65)
    print(f"総合結果: {'OK — 動的発掘連鎖が成立' if all_ok else 'NG — 発掘連鎖に問題あり'}")
    print("=" * 65)


if __name__ == "__main__":
    main()

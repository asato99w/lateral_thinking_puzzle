"""層間連鎖性レポート（L3-7）。

各パラダイムの Q(P) について、層構造における R(P) 到達性を検証し、
到達不足記述素を列挙する。

連鎖条件: 層 k までの Q(P) 回答で得られる O + R(P) 到達範囲が、
層 k+1 の各質問の effect 記述素をカバーすること。
カバーされない記述素を「到達不足記述素」として報告する。

オープン条件（engine.py open_questions）に基づく判定:
  - consistent_reach 内かつ P の予測と一致 → 到達
  - anomaly_reach 内 → 到達

OK/NG 判定は行わない（品質メトリクスの定量報告のみ）。

使い方:
  python layer_connectivity.py                       # turtle_soup.json
  python layer_connectivity.py --data bar_man.json   # bar_man.json
"""
from __future__ import annotations

import sys
from pathlib import Path
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from common import load_data, derive_qp  # noqa: E402
from engine import compute_effect, _reachable  # noqa: E402


def build_layer_structure(qp, ps_values):
    """Q(P) 内の前提関係から層を構築する。（qp_report.py と同一ロジック）"""
    qp_ids = {q.id for q in qp}

    producer = defaultdict(set)
    for q in qp:
        eff = compute_effect(q)
        if q.correct_answer == "irrelevant":
            continue
        for d, v in eff:
            producer[d].add(q.id)

    initial_ds = set(ps_values.keys())

    deps = {}
    for q in qp:
        prereqs = q.prerequisites or []
        dep_qids = set()
        for d in prereqs:
            if d in initial_ds:
                continue
            for prod_qid in producer.get(d, set()):
                if prod_qid != q.id:
                    dep_qids.add(prod_qid)
        deps[q.id] = dep_qids

    layers = {}

    def get_layer(qid, visiting=None):
        if qid in layers:
            return layers[qid]
        if visiting is None:
            visiting = set()
        if qid in visiting:
            layers[qid] = 0
            return 0
        visiting.add(qid)
        dep_layers = [get_layer(d_qid, visiting)
                      for d_qid in deps.get(qid, set()) if d_qid in qp_ids]
        layer = max(dep_layers, default=-1) + 1
        layers[qid] = layer
        return layer

    for q in qp:
        get_layer(q.id)

    return layers


def find_unreachable(paradigm, qp, layers, ps_values):
    """各層遷移で到達不足な記述素を列挙する。

    Returns:
        {layer_k: [(質問ID, 到達不足記述素, 値)]}（不足がある層のみ）
    """
    max_layer = max(layers.values()) if layers else 0
    results = {}

    for layer_k in range(max_layer):
        layer_k1_qs = [q for q in qp if layers[q.id] == layer_k + 1]
        if not layer_k1_qs:
            continue

        # 層 0..k の質問回答後の推定 O
        o_est = dict(ps_values)
        for lk in range(layer_k + 1):
            for q in qp:
                if layers[q.id] != lk:
                    continue
                eff = compute_effect(q)
                if q.correct_answer == "irrelevant":
                    continue
                for d, v in eff:
                    o_est[d] = v

        # Consistent / Anomaly
        consistent = {d for d, v in o_est.items()
                      if paradigm.prediction(d) is not None
                      and paradigm.prediction(d) == v}
        anomaly = {d for d, v in o_est.items()
                   if paradigm.prediction(d) is not None
                   and paradigm.prediction(d) != v}

        consistent_reach = _reachable(consistent, paradigm)
        anomaly_reach = _reachable(anomaly, paradigm)

        # 層 k+1 の各質問の effect 記述素について到達性を検証
        layer_missing = []
        for q in layer_k1_qs:
            eff = compute_effect(q)
            if q.correct_answer == "irrelevant":
                continue
            # open_questions のロジック: effect 内に1つでも到達可能な記述素があればオープン
            has_reachable = False
            unreachable_ds = []
            for d, v in eff:
                if d in consistent_reach and paradigm.prediction(d) == v:
                    has_reachable = True
                elif d in anomaly_reach:
                    has_reachable = True
                else:
                    unreachable_ds.append((d, v))

            if not has_reachable:
                # 質問全体が到達不可能
                for d, v in unreachable_ds:
                    layer_missing.append((q.id, d, v))

        if layer_missing:
            results[layer_k] = layer_missing

    return results


def report_paradigm(pid, paradigm, questions, ps_values):
    """1つのパラダイムの層間連鎖性を報告する。"""
    qp = derive_qp(questions, paradigm)
    if not qp:
        print(f"  Q({pid}) は空です。")
        return

    layers = build_layer_structure(qp, ps_values)
    max_layer = max(layers.values()) if layers else 0

    print(f"  |Q({pid})| = {len(qp)}, 層数: {max_layer + 1}")

    unreachable = find_unreachable(paradigm, qp, layers, ps_values)

    if not unreachable:
        print("  到達不足: なし")
    else:
        total_missing = sum(len(items) for items in unreachable.values())
        print(f"  到達不足: {total_missing} 件")
        print()
        for layer_k in sorted(unreachable):
            items = unreachable[layer_k]
            print(f"    層{layer_k}→層{layer_k+1}:")
            for qid, d, v in items:
                pred = paradigm.prediction(d)
                pred_str = f"P_pred={pred}" if pred is not None else "P_pred=不定"
                print(f"      {qid}: {d}={v} ({pred_str}, R(P) 到達不可)")


def main():
    paradigms, questions, all_ids, ps_values, init_pid, _caps = load_data()

    print("=" * 65)
    print("層間連鎖性レポート (L3-7)")
    print("=" * 65)
    print()

    for pid in paradigms:
        p = paradigms[pid]
        print(f"{'=' * 60}")
        print(f"{pid}: {p.name}")
        print(f"{'=' * 60}")
        report_paradigm(pid, p, questions, ps_values)
        print()


if __name__ == "__main__":
    main()

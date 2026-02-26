"""Q(P) 構造レポート（L3-4, L3-5）。

各パラダイムの Q(P) について品質メトリクスを報告する:
- L3-4 ゲート開放率: 各層間の R(P) 到達性によるゲート開放比率
- L3-5 層形状: 各層の質問数分布

OK/NG 判定は行わない（品質メトリクスの定量報告のみ）。

使い方:
  python qp_report.py                       # turtle_soup.json
  python qp_report.py --data bar_man.json   # bar_man.json
"""
from __future__ import annotations

import sys
from pathlib import Path
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from common import load_data, derive_qp, get_truth  # noqa: E402
from engine import compute_effect, _reachable  # noqa: E402


# ---------------------------------------------------------------------------
# アノマリー判定
# ---------------------------------------------------------------------------

def count_anomalies(question, paradigm):
    """質問が P に対して生むアノマリー数を返す。"""
    eff = compute_effect(question)
    count = 0
    for d, v in eff:
        pred = paradigm.prediction(d)
        if pred is not None and pred != v:
            count += 1
    return count


# ---------------------------------------------------------------------------
# 層構造の構築
# ---------------------------------------------------------------------------

def build_layer_structure(qp, ps_values):
    """Q(P) 内の前提関係から層を構築する。"""
    qp_ids = {q.id for q in qp}

    producer = defaultdict(set)
    for q in qp:
        eff = compute_effect(q)
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
        dep_layers = [get_layer(d_qid, visiting) for d_qid in deps.get(qid, set()) if d_qid in qp_ids]
        layer = max(dep_layers, default=-1) + 1
        layers[qid] = layer
        return layer

    for q in qp:
        get_layer(q.id)

    return layers, deps


# ---------------------------------------------------------------------------
# L3-4: ゲート開放率
# ---------------------------------------------------------------------------

def analyze_gate_opening(paradigm, qp, layers, ps_values):
    """各層間の R(P) 到達性によるゲート開放率を計算する。

    Returns: {layer_k: {gate_total, gate_opened, rate}}
    """
    max_layer = max(layers.values()) if layers else 0

    results = {}
    for layer_k in range(max_layer):
        layer_k1_qs = [q for q in qp if layers[q.id] == layer_k + 1]
        if not layer_k1_qs:
            continue

        # 層 k+1 の質問の effect 記述素
        gate_ds = set()
        for q in layer_k1_qs:
            eff = compute_effect(q)
            for d, v in eff:
                gate_ds.add((d, v))

        # 層 0..k の質問回答後の推定 O
        o_est = dict(ps_values)
        for lk in range(layer_k + 1):
            for q in qp:
                if layers[q.id] != lk:
                    continue
                eff = compute_effect(q)
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

        gates_opened = 0
        for d, v in gate_ds:
            if d in consistent_reach and paradigm.prediction(d) == v:
                gates_opened += 1
                continue
            if d in anomaly_reach:
                gates_opened += 1

        results[layer_k] = {
            "gate_total": len(gate_ds),
            "gate_opened": gates_opened,
            "rate": gates_opened / len(gate_ds) if gate_ds else 0,
        }

    return results


# ---------------------------------------------------------------------------
# メイン
# ---------------------------------------------------------------------------

def report_paradigm(pid, paradigm, questions, ps_values):
    """1つのパラダイムの Q(P) 品質メトリクスを報告する。"""
    qp = derive_qp(questions, paradigm)
    if not qp:
        print(f"  Q({pid}) は空です。")
        return

    layers, deps = build_layer_structure(qp, ps_values)
    max_layer = max(layers.values()) if layers else 0

    # --- L3-5: 層形状 ---
    print(f"  |Q({pid})| = {len(qp)}")
    print()
    print("  [層形状 (L3-5)]")
    for lk in range(max_layer + 1):
        layer_qs = [q for q in qp if layers[q.id] == lk]
        anomaly_qs = [q for q in layer_qs if count_anomalies(q, paradigm) > 0]
        anom_str = f"  (anomaly: {len(anomaly_qs)})" if anomaly_qs else ""
        print(f"    層{lk}: {len(layer_qs)}問{anom_str}")

        for q in layer_qs:
            ac = count_anomalies(q, paradigm)
            marker = f" *anomaly({ac})" if ac > 0 else ""
            eff = compute_effect(q)
            eff_str = ", ".join(f"{d}={v}" for d, v in eff)
            print(f"      {q.id}({q.correct_answer}) [{eff_str}]{marker}")

    # --- L3-4: ゲート開放率 ---
    print()
    print("  [ゲート開放率 (L3-4)]")
    gate_results = analyze_gate_opening(paradigm, qp, layers, ps_values)
    if gate_results:
        for lk in sorted(gate_results):
            r = gate_results[lk]
            print(f"    層{lk}→層{lk+1}: "
                  f"ゲート {r['gate_opened']}/{r['gate_total']} "
                  f"(開放率 {r['rate']:.0%})")
    else:
        print("    （単層のため分析なし）")

    # --- R(P) 関係構造（参考情報） ---
    print()
    print("  [R(P) 関係]")
    truth = get_truth(questions)
    for src, tgt, w in paradigm.relations:
        pred_tgt = paradigm.prediction(tgt)
        truth_tgt = truth.get(tgt)
        anomaly_mark = ""
        if pred_tgt is not None and truth_tgt is not None and pred_tgt != truth_tgt:
            anomaly_mark = " *"
        print(f"    {src} --({w})--> {tgt}{anomaly_mark}")


def main():
    paradigms, questions, all_ids, ps_values, init_pid = load_data()

    print("=" * 65)
    print("Q(P) 構造レポート (L3-4, L3-5)")
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

"""パラダイム内の Q(P) 構造を分析する。

p_pred(P) から Q(P) を導出し、前提関係による層構造を構築して評価する:
- 層の形状（深さ、各層の幅、漏斗性）
- アノマリーの配置（到達深さ、層分布）
- 経路の構造（アノマリーへの経路数、ボトルネック）
- R(P) の波及（ゲート開放率、同化カバー率）
"""
from __future__ import annotations

import sys
from pathlib import Path
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from common import load_data  # noqa: E402
from engine import compute_effect, _assimilate_descriptor, EPSILON  # noqa: E402


# ---------------------------------------------------------------------------
# 1. Q(P) 導出
# ---------------------------------------------------------------------------

def derive_qp(questions, paradigm):
    """p_pred(P) から Q(P) を導出する。"""
    qp = []
    for q in questions:
        if q.correct_answer == "irrelevant":
            continue
        eff = compute_effect(q)
        eff_ds = {d for d, v in eff}
        if eff_ds & set(paradigm.p_pred.keys()):
            qp.append(q)
    return qp


# ---------------------------------------------------------------------------
# 2. 真理値の導出
# ---------------------------------------------------------------------------

def get_truth(questions):
    """全質問の correct_answer から各記述素の真理値を導出する。"""
    truth = {}
    for q in questions:
        if q.correct_answer == "irrelevant":
            continue
        eff = compute_effect(q)
        for d, v in eff:
            truth[d] = v
    return truth


# ---------------------------------------------------------------------------
# 3. アノマリー判定
# ---------------------------------------------------------------------------

def count_anomalies(question, paradigm, truth):
    """質問が P に対して生むアノマリー数を返す。"""
    eff = compute_effect(question)
    count = 0
    for d, v in eff:
        pred = paradigm.prediction(d)
        if pred is not None and pred != v:
            count += 1
    return count


def anomaly_details(question, paradigm, truth):
    """アノマリーの詳細を返す。"""
    eff = compute_effect(question)
    details = []
    for d, v in eff:
        pred = paradigm.prediction(d)
        if pred is not None and pred != v:
            details.append((d, v, pred))
    return details


# ---------------------------------------------------------------------------
# 4. 層構造の構築
# ---------------------------------------------------------------------------

def build_layer_structure(qp, ps_values):
    """Q(P) 内の前提関係から層を構築する。

    返り値: (layers, deps, producer)
      layers: {q.id: layer_number}
      deps: {q.id: set of prerequisite q.ids within Q(P)}
      producer: {descriptor_id: set of q.ids that produce it}
    """
    qp_ids = {q.id for q in qp}

    # 記述素 -> それを生む Q(P) 内の質問
    producer = defaultdict(set)
    for q in qp:
        eff = compute_effect(q)
        for d, v in eff:
            producer[d].add(q.id)

    # 初期利用可能な記述素
    initial_ds = set(ps_values.keys())

    # 各質問の Q(P) 内での依存関係
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

    # 層の割り当て（各質問の層 = 依存先の最大層 + 1）
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
        dep_layers = []
        for d_qid in deps.get(qid, set()):
            if d_qid in qp_ids:
                dep_layers.append(get_layer(d_qid, visiting))
        layer = max(dep_layers, default=-1) + 1
        layers[qid] = layer
        return layer

    for q in qp:
        get_layer(q.id)

    return layers, deps, producer


# ---------------------------------------------------------------------------
# 5. 経路分析
# ---------------------------------------------------------------------------

def find_paths_to_targets(target_qid, deps, qp_ids, max_paths=50):
    """target_qid から依存関係を遡り、層0までの全パスを返す。"""
    all_paths = []

    def dfs(current, path):
        if len(all_paths) >= max_paths:
            return
        predecessors = [d for d in deps.get(current, set()) if d in qp_ids]
        if not predecessors:
            all_paths.append(list(reversed(path)))
            return
        for pred_qid in predecessors:
            if pred_qid not in path:
                dfs(pred_qid, path + [pred_qid])

    dfs(target_qid, [target_qid])
    return all_paths


def find_bottlenecks(all_paths):
    """全パスに共通して現れる質問（ボトルネック）を検出する。"""
    if not all_paths:
        return set()
    common = set(all_paths[0])
    for path in all_paths[1:]:
        common &= set(path)
    return common


# ---------------------------------------------------------------------------
# 6. R(P) 波及分析
# ---------------------------------------------------------------------------

def analyze_rp_spread(paradigm, qp, layers, truth, ps_values):
    """各層での R(P) 同化による波及を分析する。

    返り値: {layer: {gate_open_count, gate_total, spread_descriptors}}
    """
    q_by_id = {q.id: q for q in qp}
    max_layer = max(layers.values()) if layers else 0

    # 各層の質問が生む記述素
    layer_effects = defaultdict(set)
    for q in qp:
        eff = compute_effect(q)
        for d, v in eff:
            layer_effects[layers[q.id]].add(d)

    # 次の層のゲート条件 = 次の層の質問の effect 記述素
    # ゲートが開く = H がその記述素の真理値に近づく
    results = {}
    for layer_k in range(max_layer):
        layer_k1_qs = [q for q in qp if layers[q.id] == layer_k + 1]
        if not layer_k1_qs:
            continue

        # 層 k+1 のゲート = 層 k+1 の質問の effect 記述素のうち、
        # 閾値条件 |H(d) - v| < EPSILON が必要なもの
        gate_ds = set()
        for q in layer_k1_qs:
            eff = compute_effect(q)
            for d, v in eff:
                gate_ds.add(d)

        # 層 k の質問を全て回答した際の R(P) 同化による波及先
        # 簡易シミュレーション: H を構築して同化を適用
        h = {d: 0.5 for d in paradigm.p_pred}
        for d, v in ps_values.items():
            if d in h:
                h[d] = float(v)

        # 層 0..k の質問を全て回答
        for lk in range(layer_k + 1):
            for q in qp:
                if layers[q.id] != lk:
                    continue
                eff = compute_effect(q)
                for d, v in eff:
                    h[d] = float(v)
                # 同化
                for d, v in eff:
                    pred = paradigm.prediction(d)
                    if pred is not None and pred == v:
                        _assimilate_descriptor(h, d, paradigm)

        # ゲートの開放状態をチェック
        gates_opened = 0
        spread_ds = set()
        for d in gate_ds:
            tv = truth.get(d)
            if tv is not None and abs(h.get(d, 0.5) - tv) < EPSILON:
                gates_opened += 1
                spread_ds.add(d)

        results[layer_k] = {
            "gate_total": len(gate_ds),
            "gate_opened": gates_opened,
            "rate": gates_opened / len(gate_ds) if gate_ds else 0,
        }

    return results


# ---------------------------------------------------------------------------
# メイン
# ---------------------------------------------------------------------------

def analyze_paradigm(pid, paradigm, questions, ps_values, truth):
    """1つのパラダイムの Q(P) 構造を分析する。"""
    qp = derive_qp(questions, paradigm)
    if not qp:
        print(f"  Q({pid}) は空です。")
        return

    layers, deps, producer = build_layer_structure(qp, ps_values)
    q_by_id = {q.id: q for q in qp}
    max_layer = max(layers.values()) if layers else 0

    # --- 層の形状 ---
    print(f"  |Q({pid})| = {len(qp)}")
    print()
    print("  [層の形状]")
    for lk in range(max_layer + 1):
        layer_qs = [q for q in qp if layers[q.id] == lk]
        anomaly_qs = [q for q in layer_qs if count_anomalies(q, paradigm, truth) > 0]
        normal_qs = [q for q in layer_qs if count_anomalies(q, paradigm, truth) == 0]
        anom_str = f"  (anomaly: {len(anomaly_qs)})" if anomaly_qs else ""
        print(f"    層{lk}: {len(layer_qs)}問{anom_str}")

        for q in layer_qs:
            ac = count_anomalies(q, paradigm, truth)
            marker = f" ★anomaly({ac})" if ac > 0 else ""
            eff = compute_effect(q)
            eff_str = ", ".join(f"{d}={v}" for d, v in eff)
            print(f"      {q.id}({q.correct_answer}) [{eff_str}]{marker}")

    # --- アノマリーの配置 ---
    print()
    print("  [アノマリーの配置]")
    anomaly_qids = []
    for q in qp:
        ac = count_anomalies(q, paradigm, truth)
        if ac > 0:
            anomaly_qids.append(q.id)
            details = anomaly_details(q, paradigm, truth)
            det_str = ", ".join(f"{d}(truth={v},pred={p})" for d, v, p in details)
            print(f"    {q.id} 層{layers[q.id]}: {det_str}")

    if not anomaly_qids:
        print("    アノマリー質問なし")
        return

    anomaly_layers = [layers[qid] for qid in anomaly_qids]
    print(f"    初回到達深さ: 層{min(anomaly_layers)}")
    print(f"    最深: 層{max(anomaly_layers)}")

    layer_dist = defaultdict(int)
    for l in anomaly_layers:
        layer_dist[l] += 1
    dist_str = ", ".join(f"層{l}:{c}" for l, c in sorted(layer_dist.items()))
    print(f"    層分布: {dist_str}")

    # --- 経路の構造 ---
    print()
    print("  [経路の構造]")
    all_anomaly_paths = []
    for target_qid in anomaly_qids:
        paths = find_paths_to_targets(target_qid, deps, {q.id for q in qp})
        all_anomaly_paths.extend(paths)
        if paths:
            print(f"    {target_qid} への経路: {len(paths)}本")
            for i, path in enumerate(paths[:3]):
                path_str = " → ".join(path)
                print(f"      [{i+1}] {path_str}")
            if len(paths) > 3:
                print(f"      ... 他{len(paths)-3}本")
        else:
            print(f"    {target_qid}: 前提なし（層0から直接到達）")

    # ボトルネック検出
    if all_anomaly_paths:
        bottlenecks = find_bottlenecks(all_anomaly_paths)
        # アノマリー自身は除外
        bottlenecks -= set(anomaly_qids)
        if bottlenecks:
            bn_str = ", ".join(f"{qid}(層{layers[qid]})" for qid in sorted(bottlenecks))
            print(f"    ボトルネック: {bn_str}")
        else:
            print(f"    ボトルネック: なし")

    # --- R(P) の波及 ---
    print()
    print("  [R(P) 波及]")
    rp_results = analyze_rp_spread(paradigm, qp, layers, truth, ps_values)
    if rp_results:
        for lk in sorted(rp_results):
            r = rp_results[lk]
            print(f"    層{lk}→層{lk+1}: "
                  f"ゲート {r['gate_opened']}/{r['gate_total']} "
                  f"(開放率 {r['rate']:.0%})")
    else:
        print("    （単層のため波及分析なし）")

    # --- 完全性検証 ---
    print()
    print("  [完全性検証]")
    # パラダイムの全アノマリー記述素を列挙
    anomaly_descriptors = {
        d for d, pred in paradigm.p_pred.items()
        if truth.get(d) is not None and pred != truth[d]
    }
    # 各アノマリー記述素が Q(P) のいずれかの質問の effect に含まれるかを確認
    covered_anomalies = set()
    for q in qp:
        eff = compute_effect(q)
        if q.correct_answer == "irrelevant":
            continue
        for d, v in eff:
            if d in anomaly_descriptors:
                covered_anomalies.add(d)
    uncovered = anomaly_descriptors - covered_anomalies
    if anomaly_descriptors:
        print(f"    アノマリー記述素: {len(anomaly_descriptors)}個")
        print(f"    質問でカバー済み: {len(covered_anomalies)}個")
        if uncovered:
            print(f"    未カバー: {sorted(uncovered)}")
            print(f"    完全性: NG")
        else:
            print(f"    完全性: OK")
    else:
        print("    アノマリー記述素なし（最終パラダイム）")

    # --- R(P) 関係構造 ---
    print()
    print("  [R(P) 関係]")
    for src, tgt, w in paradigm.relations:
        pred_src = paradigm.prediction(src)
        pred_tgt = paradigm.prediction(tgt)
        truth_tgt = truth.get(tgt)
        anomaly_mark = ""
        if pred_tgt is not None and truth_tgt is not None and pred_tgt != truth_tgt:
            anomaly_mark = " ★"
        print(f"    {src}(pred={pred_src}) --({w})--> {tgt}(pred={pred_tgt}){anomaly_mark}")


def main():
    paradigms, questions, all_ids, ps_values, init_pid = load_data()
    truth = get_truth(questions)

    for pid in paradigms:
        p = paradigms[pid]
        print(f"{'=' * 60}")
        print(f"{pid}: {p.name}")
        print(f"{'=' * 60}")
        analyze_paradigm(pid, p, questions, ps_values, truth)
        print()


if __name__ == "__main__":
    main()

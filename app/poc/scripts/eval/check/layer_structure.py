"""多層構造検証スクリプト（L2-4）。

各パラダイムの Q(P) の層構造について 3 条件を検証する:
  1. 層0アノマリー比率 ≤ 0.3
  2. ボトルネック制限
  3. アノマリー層分散 ≥ 2

使い方:
  python layer_structure.py                       # turtle_soup.json
  python layer_structure.py --data bar_man.json   # bar_man.json
"""
from __future__ import annotations

import sys
from pathlib import Path
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from common import load_data, derive_qp, get_truth  # noqa: E402
from engine import compute_effect  # noqa: E402

# 閾値
LAYER0_ANOMALY_THRESHOLD = 0.7
BOTTLENECK_LIMIT = 3
MIN_ANOMALY_LAYERS = 1


def count_anomalies(question, paradigm):
    """質問が P に対して生むアノマリー数を返す。"""
    if question.correct_answer == "irrelevant":
        return 0
    eff = compute_effect(question)
    count = 0
    for d, v in eff:
        pred = paradigm.prediction(d)
        if pred is not None and pred != v:
            count += 1
    return count


def build_layer_structure(qp, ps_values):
    """Q(P) 内の前提関係から層を構築する。"""
    qp_ids = {q.id for q in qp}

    producer = defaultdict(set)
    for q in qp:
        if q.correct_answer == "irrelevant":
            continue
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


def find_paths_to_target(target_qid, deps, qp_ids, max_paths=50):
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


def check_paradigm(pid, paradigm, questions, ps_values, truth):
    """1つのパラダイムの多層構造3条件を検証する。

    Returns:
        (results_dict, has_anomalies)
        results_dict: {condition_name: (ok, detail_str)}
    """
    qp = derive_qp(questions, paradigm)
    if not qp:
        return {}, False

    layers, deps = build_layer_structure(qp, ps_values)
    qp_ids = {q.id for q in qp}

    # アノマリー質問の特定
    anomaly_qids = [q.id for q in qp if count_anomalies(q, paradigm) > 0]

    if not anomaly_qids:
        return {}, False

    total_anomaly = len(anomaly_qids)
    anomaly_layers = [layers[qid] for qid in anomaly_qids]

    results = {}

    # 条件1: 層0アノマリー比率
    layer0_anomaly = sum(1 for l in anomaly_layers if l == 0)
    ratio = layer0_anomaly / total_anomaly if total_anomaly > 0 else 0
    ok1 = ratio <= LAYER0_ANOMALY_THRESHOLD
    results["層0アノマリー比率"] = (
        ok1,
        f"{ratio:.2f} (={layer0_anomaly}/{total_anomaly}, 閾値≤{LAYER0_ANOMALY_THRESHOLD})",
    )

    # 条件2: ボトルネック
    all_paths = []
    for target_qid in anomaly_qids:
        paths = find_paths_to_target(target_qid, deps, qp_ids)
        all_paths.extend(paths)

    if all_paths:
        common = set(all_paths[0])
        for path in all_paths[1:]:
            common &= set(path)
        common -= set(anomaly_qids)
        bottleneck_count = len(common)
    else:
        common = set()
        bottleneck_count = 0

    ok2 = bottleneck_count <= BOTTLENECK_LIMIT
    bn_str = f"{sorted(common)}" if common else "なし"
    results["ボトルネック"] = (
        ok2,
        f"{bottleneck_count}個 {bn_str} (制限≤{BOTTLENECK_LIMIT})",
    )

    # 条件3: アノマリー層分散
    distinct_layers = len(set(anomaly_layers))
    ok3 = distinct_layers >= MIN_ANOMALY_LAYERS
    dist = defaultdict(int)
    for l in anomaly_layers:
        dist[l] += 1
    dist_str = ", ".join(f"層{l}:{c}" for l, c in sorted(dist.items()))
    results["アノマリー層分散"] = (
        ok3,
        f"{distinct_layers}層 ({dist_str}, 閾値≥{MIN_ANOMALY_LAYERS})",
    )

    return results, True


def main():
    paradigms, questions, all_ids, ps_values, init_pid, _caps, _tp = load_data()
    truth = get_truth(questions)

    print("=" * 65)
    print("多層構造検証 (L2-4)")
    print("=" * 65)
    print()

    all_ok = True

    for pid, paradigm in paradigms.items():
        results, has_anomalies = check_paradigm(
            pid, paradigm, questions, ps_values, truth,
        )

        print(f"-" * 50)
        print(f"{pid}: {paradigm.name}")
        print(f"-" * 50)

        if not has_anomalies:
            print(f"  アノマリー質問なし（検証対象外）")
            print()
            continue

        paradigm_ok = True
        for cond_name, (ok, detail) in results.items():
            status = "OK" if ok else "NG"
            print(f"  {cond_name}: {status} — {detail}")
            if not ok:
                paradigm_ok = False
                all_ok = False

        print(f"  パラダイム結果: {'OK' if paradigm_ok else 'NG'}")
        print()

    print("=" * 65)
    print(f"総合結果: {'OK — 全パラダイムで多層構造条件充足' if all_ok else 'NG — 条件不充足あり'}")
    print("=" * 65)


if __name__ == "__main__":
    main()

"""固有記述素からのオープン連鎖到達性を構造的に検証する。

各メインパスパラダイム P_i について:
  1. 固有記述素 E(P_i) = p_pred(P_i) - ∪_{j≠i} p_pred(P_j) を特定
  2. R(P_i) の推移閉包で E(P_i) から到達可能な記述素を算出
  3. 到達可能な記述素を通じて開ける質問のうち anomaly を生むものを特定
  4. anomaly の上界が shift_threshold 以上かを検証

質問が「開ける」条件:
  効果記述素のうち少なくとも一つが到達可能で、かつ P_i が正しく予測する
  （同化で H が正解方向に押され、H(d) ≈ v を満たしうる）

質問が anomaly を生む条件:
  効果記述素のうち少なくとも一つについて P_i の予測が真値と異なる

使い方:
  python opening_reach.py                       # turtle_soup.json
  python opening_reach.py --data bar_man.json   # bar_man.json
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from common import load_data, load_raw, MAIN_PATH  # noqa: E402
from engine import compute_effect, tension
from threshold import build_o_star


def compute_exclusive_descriptors(paradigm, all_paradigms):
    """P_i の固有記述素: p_pred(P_i) にのみ属し他のどの p_pred(P_j) にも属さない。"""
    other_pred_keys = set()
    for pid, p in all_paradigms.items():
        if pid != paradigm.id:
            other_pred_keys |= set(p.p_pred.keys())
    return set(paradigm.p_pred.keys()) - other_pred_keys


def compute_reachable(seeds, relations):
    """seeds から relations の推移閉包で到達可能な記述素を算出する。"""
    reachable = set(seeds)
    frontier = set(seeds)
    while frontier:
        next_frontier = set()
        for src, tgt, w in relations:
            if src in frontier and tgt not in reachable:
                next_frontier.add(tgt)
                reachable.add(tgt)
        frontier = next_frontier
    return reachable


def analyze_paradigm(pid, paradigms, questions, o_star):
    """一つのパラダイムについて構造的到達性を分析する。"""
    paradigm = paradigms[pid]

    # Step 1: 固有想起記述素
    exclusive = compute_exclusive_descriptors(paradigm, paradigms)
    pred_keys = set(paradigm.p_pred.keys())
    shared = pred_keys - exclusive

    pred_1 = sum(1 for v in paradigm.p_pred.values() if v == 1)
    pred_0 = sum(1 for v in paradigm.p_pred.values() if v == 0)
    print(f"  |p_pred|={len(paradigm.p_pred)} (1:{pred_1}, 0:{pred_0})")
    print(f"  固有記述素: {len(exclusive)}, 共有記述素: {len(shared)}")

    # Step 2: R(P) による到達可能性
    reachable = compute_reachable(exclusive, paradigm.relations)
    reachable_shared = reachable & shared
    reachable_from_exclusive = reachable - exclusive

    print(f"  R(P) 到達可能: {len(reachable)} "
          f"(固有{len(reachable & exclusive)} + 新規{len(reachable_from_exclusive)})")
    print(f"  到達可能な共有想起記述素: {len(reachable_shared)}")

    # Step 3 & 4: 到達可能記述素で開ける質問と anomaly
    openable_via_reach = []  # (question, opening_ds, anomaly_ds)
    for q in questions:
        eff = compute_effect(q)
        if q.correct_answer == "irrelevant":
            continue

        # 開ける条件: 効果記述素の中に到達可能かつ P_i が正しく予測するものがある
        opening_ds = []
        anomaly_ds = []
        for d, v in eff:
            pred = paradigm.prediction(d)
            if pred is None:
                continue
            if d in reachable and pred == v:
                opening_ds.append(d)
            if pred != v:
                anomaly_ds.append(d)

        if opening_ds and anomaly_ds:
            openable_via_reach.append((q, opening_ds, anomaly_ds))

    # anomaly の上界: 全到達可能質問の anomaly 記述素を集約
    all_anomaly_ds = set()
    for q, opening_ds, anomaly_ds in openable_via_reach:
        all_anomaly_ds.update(anomaly_ds)

    # O* での anomaly 数（参考: 完全確定での anomaly）
    o_star_anomalies = tension(o_star, paradigm)

    print(f"  到達可能な anomaly 生成質問: {len(openable_via_reach)}問")
    print(f"  anomaly 上界: {len(all_anomaly_ds)}記述素")
    print(f"  shift_threshold (N): {paradigm.shift_threshold}")
    print(f"  (参考) O* での anomaly: {o_star_anomalies}")

    if openable_via_reach:
        print(f"  anomaly 生成質問:")
        for q, opening_ds, anomaly_ds in openable_via_reach:
            print(f"    {q.id}: 開口={opening_ds} anomaly={anomaly_ds}")

    # 判定
    ok = False
    if paradigm.shift_threshold is None:
        print(f"  → シフト元にならない（shift_threshold なし）")
        ok = True
    elif len(all_anomaly_ds) >= paradigm.shift_threshold:
        print(f"  → anomaly 上界({len(all_anomaly_ds)}) >= N({paradigm.shift_threshold}): OK")
        ok = True
    else:
        print(f"  → anomaly 上界({len(all_anomaly_ds)}) < N({paradigm.shift_threshold}): NG")

    # 到達不能な共有記述素の内訳（NG の場合の診断情報）
    if not ok:
        unreachable_shared = shared - reachable
        if unreachable_shared:
            print(f"  [診断] 到達不能な共有想起記述素: {len(unreachable_shared)}")
            print(f"    {sorted(unreachable_shared)}")

        # 固有記述素からの関係が少ない場合
        outgoing_from_excl = [(s, t, w) for s, t, w in paradigm.relations
                              if s in exclusive and t not in exclusive]
        print(f"  [診断] 固有→非固有の関係数: {len(outgoing_from_excl)}")

    return ok


def main():
    paradigms, questions, all_ids, ps_values, init_pid = load_data()
    data = load_raw()

    o_star_data = build_o_star(questions, ps_values)

    print(f"メインパス: {' → '.join(MAIN_PATH)}")
    print(f"パラダイム数: {len(paradigms)}, 質問数: {len(questions)}")
    print()

    results = {}
    for pid in MAIN_PATH[:-1]:
        if pid not in paradigms:
            continue
        p = paradigms[pid]
        print("=" * 60)
        print(f"{pid} ({p.name})")
        print("=" * 60)
        ok = analyze_paradigm(pid, paradigms, questions, o_star_data)
        results[pid] = ok
        print()

    # サマリ
    print("=" * 60)
    print("サマリ")
    print("=" * 60)
    all_ok = True
    for pid, ok in results.items():
        status = "OK" if ok else "NG"
        if not ok:
            all_ok = False
        print(f"  {pid}: {status}")
    print()
    print(f"全体: {'OK' if all_ok else 'NG'}")


if __name__ == "__main__":
    main()

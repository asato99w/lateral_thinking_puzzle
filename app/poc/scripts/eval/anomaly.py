"""完全確定におけるアノマリーの単調減少を検証する。"""
from common import load_data, MAIN_PATH
from engine import tension, alignment, compute_effect


def main():
    paradigms, questions, *_ = load_data()

    # 全質問の effect を O* に集約
    o_star = {}
    r_star = set()
    for q in questions:
        eff = compute_effect(q)
        if q.correct_answer == "irrelevant":
            for d_id in eff:
                r_star.add(d_id)
        else:
            for d_id, v in eff:
                o_star[d_id] = v

    print(f"O* 記述素数: {len(o_star)}")
    print(f"R* 記述素数: {len(r_star)}")
    print()
    print(f"メインパス: {' → '.join(MAIN_PATH)}")
    print()

    prev_anomalies = None
    monotonic = True
    for pid in MAIN_PATH:
        if pid not in paradigms:
            print(f"  {pid}: パラダイムが存在しない")
            continue
        p = paradigms[pid]
        t = tension(o_star, p)
        a = alignment(o_star, p)
        overlap = p.d_all & set(o_star.keys())
        anomaly_ds = [d for d in overlap if p.prediction(d) != o_star[d]]

        mark = ""
        if prev_anomalies is not None and t >= prev_anomalies:
            mark = " ← 単調減少していない"
            monotonic = False
        prev_anomalies = t

        print(f"  {pid} ({p.name})")
        print(f"    anomalies={t}, alignment={a:.3f}, |D(P)∩O*|={len(overlap)}")
        if anomaly_ds:
            print(f"    アノマリー記述素: {sorted(anomaly_ds)}")
        if mark:
            print(f"    {mark}")

    print()
    print(f"単調減少: {'OK' if monotonic else 'NG'}")


if __name__ == "__main__":
    main()

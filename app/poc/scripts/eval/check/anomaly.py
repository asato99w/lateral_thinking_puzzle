"""完全確定におけるアノマリーの単調減少を検証する。"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from common import load_data, load_raw, MAIN_PATH  # noqa: E402
from engine import tension, alignment, compute_effect


def build_o_star(questions):
    """全質問の正解から O* を構築。"""
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
    return o_star, r_star


def o_star_to_h(o_star, all_ids):
    """O* を H 相当の dict に変換する。"""
    h = {d: 0.5 for d in all_ids}
    for d, v in o_star.items():
        h[d] = float(v)
    return h


def main():
    paradigms, questions, all_ids, *_ = load_data()

    o_star, r_star = build_o_star(questions)
    h_star = o_star_to_h(o_star, all_ids)

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
        a = alignment(h_star, p)
        overlap = set(p.p_pred.keys()) & set(o_star.keys())
        anomaly_ds = [d for d in overlap if p.prediction(d) != o_star[d]]

        mark = ""
        if prev_anomalies is not None and t >= prev_anomalies:
            mark = " ← 単調減少していない"
            monotonic = False
        prev_anomalies = t

        print(f"  {pid} ({p.name})")
        print(f"    anomalies={t}, alignment={a:.3f}, |Conceivable∩O*|={len(overlap)}")
        if anomaly_ds:
            print(f"    アノマリー記述素: {sorted(anomaly_ds)}")
        if mark:
            print(f"    {mark}")

    print()
    print(f"単調減少: {'OK' if monotonic else 'NG'}")


if __name__ == "__main__":
    main()

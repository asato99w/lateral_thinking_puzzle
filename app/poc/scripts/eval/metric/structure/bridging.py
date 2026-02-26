"""架橋質問・共有質問を分類する。"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from common import load_data, MAIN_PATH  # noqa: E402
from engine import compute_effect


def main():
    paradigms, questions, *_ = load_data()

    main_paradigms = {pid: paradigms[pid] for pid in MAIN_PATH if pid in paradigms}

    bridging = []
    shared_qs = []
    single = []

    for q in questions:
        eff = compute_effect(q)
        if q.correct_answer == "irrelevant":
            continue
        eff_ds = {d for d, v in eff}

        homes = {}
        for pid, p in main_paradigms.items():
            overlap = eff_ds & set(p.p_pred.keys())
            if overlap:
                homes[pid] = overlap

        if len(homes) < 2:
            single.append((q, homes))
            continue

        # 固有想起記述素にまたがるか判定
        all_pids = list(homes.keys())
        is_bridge = False
        for idx, pid1 in enumerate(all_pids):
            for pid2 in all_pids[idx+1:]:
                p1 = main_paradigms[pid1]
                p2 = main_paradigms[pid2]
                excl_1 = homes[pid1] - set(p2.p_pred.keys())
                excl_2 = homes[pid2] - set(p1.p_pred.keys())
                if excl_1 and excl_2:
                    is_bridge = True
        if is_bridge:
            bridging.append((q, homes))
        else:
            shared_qs.append((q, homes))

    print(f"架橋質問: {len(bridging)}問")
    for q, homes in bridging:
        home_str = ", ".join(f"{pid}:{sorted(ds)}" for pid, ds in homes.items())
        print(f"  {q.id} [{q.correct_answer}] {home_str}")
        print(f"    {q.text}")
    print()

    print(f"共有質問: {len(shared_qs)}問")
    for q, homes in shared_qs:
        home_str = ", ".join(f"{pid}:{sorted(ds)}" for pid, ds in homes.items())
        print(f"  {q.id} [{q.correct_answer}] {home_str}")
        print(f"    {q.text}")
    print()

    print(f"単一パラダイム質問: {len(single)}問")
    for q, homes in single:
        if homes:
            home_str = ", ".join(f"{pid}:{sorted(ds)}" for pid, ds in homes.items())
        else:
            eff = compute_effect(q)
            eff_ds = [d for d, v in eff]
            home_str = f"所属なし effect={eff_ds}"
        print(f"  {q.id} [{q.correct_answer}] {home_str}")


if __name__ == "__main__":
    main()

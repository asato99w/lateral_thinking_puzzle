"""Ps と p_pred(P) の関係を検証する。"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from common import load_data  # noqa: E402


def main():
    paradigms, _, _, ps_values, _ = load_data()

    ps_ids = set(ps_values.keys())
    print(f"Ps 記述素: {sorted(ps_ids)}")
    print()

    for pid, p in paradigms.items():
        overlap = ps_ids & set(p.p_pred.keys())
        if overlap:
            pred_1 = sorted(d for d in overlap if p.p_pred.get(d) == 1)
            pred_0 = sorted(d for d in overlap if p.p_pred.get(d) == 0)
            parts = []
            if pred_1:
                parts.append(f"p_pred=1: {pred_1}")
            if pred_0:
                parts.append(f"p_pred=0: {pred_0}")
            print(f"  {pid}: {', '.join(parts)}")
        else:
            print(f"  {pid}: (なし)")

    no_home = ps_ids - set().union(*(set(p.p_pred.keys()) for p in paradigms.values()))
    if no_home:
        print()
        print(f"どの p_pred(P) にも含まれない Ps: {sorted(no_home)}")


if __name__ == "__main__":
    main()

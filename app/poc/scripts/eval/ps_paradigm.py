"""Ps と D(P) の関係を検証する。"""
from common import load_data


def main():
    paradigms, _, _, ps_values, _ = load_data()

    ps_ids = set(ps_values.keys())
    print(f"Ps 記述素: {sorted(ps_ids)}")
    print()

    for pid, p in paradigms.items():
        overlap = ps_ids & p.d_all
        if overlap:
            in_plus = overlap & p.d_plus
            in_minus = overlap & p.d_minus
            parts = []
            if in_plus:
                parts.append(f"D⁺={sorted(in_plus)}")
            if in_minus:
                parts.append(f"D⁻={sorted(in_minus)}")
            print(f"  {pid}: {', '.join(parts)}")
        else:
            print(f"  {pid}: (なし)")

    no_home = ps_ids - set().union(*(p.d_all for p in paradigms.values()))
    if no_home:
        print()
        print(f"どの D(P) にも含まれない Ps: {sorted(no_home)}")


if __name__ == "__main__":
    main()

"""到達性検証スクリプト（L2-0）。

O* のもとで init_paradigm から T に至るシフト連鎖が存在することを検証する。

使い方:
  python reachability.py                       # turtle_soup.json
  python reachability.py --data bar_man.json   # bar_man.json
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from common import load_data, compute_o_star_shift_chain  # noqa: E402


def main():
    paradigms, questions, all_ids, ps_values, init_pid = load_data()

    path = compute_o_star_shift_chain(init_pid, paradigms, questions)

    # T の特定: depth が最大のパラダイム
    t_pid = max(paradigms, key=lambda pid: paradigms[pid].depth or 0)

    print("=" * 65)
    print("到達性検証 (L2-0)")
    print("=" * 65)
    print(f"init: {init_pid}")
    print(f"T: {t_pid}")
    print(f"O*シフト連鎖: {' → '.join(path)}")
    print()

    ok = t_pid in path
    if ok:
        print(f"結果: OK — {init_pid} から {t_pid} に到達可能")
    else:
        print(f"結果: NG — {init_pid} から {t_pid} に到達不可（到達先: {path[-1]}）")

    print("=" * 65)


if __name__ == "__main__":
    main()

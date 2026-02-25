"""パラダイム間の共有・固有想起記述素を分析する。"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from common import load_data, MAIN_PATH  # noqa: E402


def main():
    paradigms, *_ = load_data()

    main_paradigms = [(pid, paradigms[pid]) for pid in MAIN_PATH if pid in paradigms]

    for i, (pid1, p1) in enumerate(main_paradigms):
        for pid2, p2 in main_paradigms[i+1:]:
            shared = p1.conceivable & p2.conceivable
            excl_1 = p1.conceivable - p2.conceivable
            excl_2 = p2.conceivable - p1.conceivable
            if shared or True:  # 隣接でなくても表示
                print(f"{pid1} vs {pid2}:")
                print(f"  共有想起: {sorted(shared) if shared else '(なし)'}")
                print(f"  {pid1}固有想起: {len(excl_1)}個 {sorted(excl_1)}")
                print(f"  {pid2}固有想起: {len(excl_2)}個 {sorted(excl_2)}")
                print()


if __name__ == "__main__":
    main()

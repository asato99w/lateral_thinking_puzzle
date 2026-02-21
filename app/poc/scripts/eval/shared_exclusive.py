"""パラダイム間の共有・固有記述素を分析する。"""
from common import load_data, MAIN_PATH


def main():
    paradigms, *_ = load_data()

    main_paradigms = [(pid, paradigms[pid]) for pid in MAIN_PATH if pid in paradigms]

    for i, (pid1, p1) in enumerate(main_paradigms):
        for pid2, p2 in main_paradigms[i+1:]:
            shared = p1.d_all & p2.d_all
            excl_1 = p1.d_all - p2.d_all
            excl_2 = p2.d_all - p1.d_all
            if shared or True:  # 隣接でなくても表示
                print(f"{pid1} vs {pid2}:")
                print(f"  共有: {sorted(shared) if shared else '(なし)'}")
                print(f"  {pid1}固有: {len(excl_1)}個 {sorted(excl_1)}")
                print(f"  {pid2}固有: {len(excl_2)}個 {sorted(excl_2)}")
                print()


if __name__ == "__main__":
    main()

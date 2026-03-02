"""初期質問カバレッジ検証スクリプト。

初期パラダイムの質問数および初期オープン質問数の下限を検証する。
Q3（トピックカテゴリ分類）の適用可能性の前提条件チェックとしても機能する。

検証項目:
  L-init-1: 初期パラダイム質問数の下限（絶対数）
  L-init-2: 初期パラダイム質問比率の下限（全体に対する割合）
  L-init-3: 初期オープン質問数の下限（絶対数）
  L-init-4: 初期オープン質問比率の下限（全体に対する割合）

使い方:
  python initial_question_coverage.py                       # turtle_soup.json
  python initial_question_coverage.py --data bar_man.json   # bar_man.json
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from common import load_data, derive_qp  # noqa: E402

# ---------------------------------------------------------------------------
# 閾値
# ---------------------------------------------------------------------------
MIN_INIT_PARADIGM_QUESTIONS = 5       # 初期パラダイム質問の最小数
MIN_INIT_PARADIGM_RATIO = 0.25        # 初期パラダイム質問の最小比率 (25%)
MIN_INIT_OPEN_QUESTIONS = 5           # 初期オープン質問の最小数
MIN_INIT_OPEN_RATIO = 0.15            # 初期オープン質問の最小比率 (15%)


def get_init_open_questions(questions):
    """初期オープン質問（prerequisites が空）を返す。"""
    return [q for q in questions if not q.prerequisites]


def main():
    paradigms, questions, all_ids, ps_values, init_pid, _caps, _tp = load_data()
    total = len(questions)

    init_paradigm = paradigms[init_pid]
    init_paradigm_qs = derive_qp(questions, init_paradigm)
    init_open_qs = get_init_open_questions(questions)

    init_paradigm_count = len(init_paradigm_qs)
    init_open_count = len(init_open_qs)
    init_paradigm_ratio = init_paradigm_count / total if total > 0 else 0
    init_open_ratio = init_open_count / total if total > 0 else 0

    print("=" * 65)
    print("初期質問カバレッジ検証")
    print("=" * 65)
    print()
    print(f"全質問数: {total}")
    print(f"初期パラダイム: {init_pid} ({init_paradigm.name})")
    print()

    all_ok = True
    results = []

    # L-init-1: 初期パラダイム質問数
    ok1 = init_paradigm_count >= MIN_INIT_PARADIGM_QUESTIONS
    results.append(("L-init-1", "初期パラダイム質問数", ok1,
                     f"{init_paradigm_count}問 (下限≥{MIN_INIT_PARADIGM_QUESTIONS})"))

    # L-init-2: 初期パラダイム質問比率
    ok2 = init_paradigm_ratio >= MIN_INIT_PARADIGM_RATIO
    results.append(("L-init-2", "初期パラダイム質問比率", ok2,
                     f"{init_paradigm_ratio:.1%} (下限≥{MIN_INIT_PARADIGM_RATIO:.0%})"))

    # L-init-3: 初期オープン質問数
    ok3 = init_open_count >= MIN_INIT_OPEN_QUESTIONS
    results.append(("L-init-3", "初期オープン質問数", ok3,
                     f"{init_open_count}問 (下限≥{MIN_INIT_OPEN_QUESTIONS})"))

    # L-init-4: 初期オープン質問比率
    ok4 = init_open_ratio >= MIN_INIT_OPEN_RATIO
    results.append(("L-init-4", "初期オープン質問比率", ok4,
                     f"{init_open_ratio:.1%} (下限≥{MIN_INIT_OPEN_RATIO:.0%})"))

    # --- 結果表示 ---
    print("-" * 50)
    for label, name, ok, detail in results:
        status = "OK" if ok else "NG"
        print(f"  {label} {name}: {status} — {detail}")
        if not ok:
            all_ok = False
    print("-" * 50)
    print()

    # --- 初期オープン質問一覧 ---
    print("初期オープン質問一覧:")
    for q in init_open_qs:
        paradigm_str = ", ".join(q.paradigms)
        print(f"  {q.id}: {q.text} [{paradigm_str}]")
    print()

    # --- Q3 適用可能性 ---
    print("-" * 50)
    q3_applicable = ok3 and ok4
    if q3_applicable:
        print("Q3（トピックカテゴリ分類）適用可能性: OK")
        print("  初期オープン質問数が十分であり、カテゴリ定義が可能です")
    else:
        print("Q3（トピックカテゴリ分類）適用可能性: NG")
        if not ok3:
            print(f"  初期オープン質問が{MIN_INIT_OPEN_QUESTIONS}問未満のため、"
                  f"カテゴリ定義に十分なトピック多様性が得られません")
        if not ok4:
            print(f"  初期オープン質問比率が{MIN_INIT_OPEN_RATIO:.0%}未満のため、"
                  f"ゲーム開始時の探索範囲が限定的です")
    print("-" * 50)
    print()

    # --- 総合結果 ---
    print("=" * 65)
    if all_ok:
        print("総合結果: OK — 初期質問カバレッジ充足")
    else:
        ng_labels = [label for label, _, ok, _ in results if not ok]
        print(f"総合結果: NG — {', '.join(ng_labels)}")
    print("=" * 65)


if __name__ == "__main__":
    main()

"""パラダイムシフト経路の検証。

テーマ1: alignment 順序の検証
  - H*（全真値をHに変換）に対する各パラダイムの alignment を計算
  - alignment 順序がメインパス順と整合するか確認
  - メインパスの後のパラダイムほど alignment が高いことはデータの構造的性質

テーマ2: シフト先選択の到達性検証（仮想 H ベース）
  - 全パラダイム（サブ含む）について仮想 H_Pi を構築し遷移先を計算
  - 遷移グラフを構築し、全パラダイムから最終パラダイム P_T に到達可能か検証
  - サブパラダイムへの寄り道は許容（引っ掛け）、復帰できるかが問題

使い方:
  python shift_path.py                       # turtle_soup.json
  python shift_path.py --data bar_man.json   # bar_man.json
"""
from __future__ import annotations

from common import load_data, load_raw, MAIN_PATH
from engine import tension, alignment, compute_effect


def infer_main_path(data: dict, paradigms: dict) -> list[str]:
    """データから main_path を推定する。

    1. data["main_path"] があればそのまま使う
    2. どちらもなければ MAIN_PATH（デフォルト）を使う
    """
    if "main_path" in data:
        return data["main_path"]

    return list(MAIN_PATH)


def build_o_star(questions) -> tuple[dict[str, int], set[str]]:
    """全質問の正解から O*（完全観測）と R*（無関係集合）を構築。"""
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


def o_star_to_h(o_star: dict[str, int], all_ids: list[str]) -> dict[str, float]:
    """O* を H 相当の dict に変換する。観測済みは真値、未観測は 0.5。"""
    h = {d: 0.5 for d in all_ids}
    for d, v in o_star.items():
        h[d] = float(v)
    return h


def check_alignment_ordering(paradigms, main_path, o_star, all_ids):
    """テーマ1: alignment_h(H*, P) の順序を検証する。"""
    print("=" * 65)
    print("テーマ1: alignment 順序（H* ベース）")
    print("=" * 65)
    print()

    # O* を H に変換（全真値が観測された状態）
    h_star = o_star_to_h(o_star, all_ids)

    # 全パラダイムの alignment を計算
    all_scores = []
    for pid in sorted(paradigms.keys()):
        p = paradigms[pid]
        a = alignment(h_star, p)
        t = tension(o_star, p)
        overlap = len(p.d_all & set(o_star.keys()))
        all_scores.append((pid, a, t, overlap))

    print("alignment_h(H*, P) — 全パラダイム:")
    all_scores.sort(key=lambda x: -x[1])
    for pid, a, t, ov in all_scores:
        marker = " ◀ main" if pid in main_path else ""
        print(f"  {pid:4s}: alignment={a:.4f}  tension={t}  |D∩O*|={ov}{marker}")
    print()

    # メインパスの alignment 順序
    main_scores = [(pid, alignment(h_star, paradigms[pid])) for pid in main_path if pid in paradigms]
    print("メインパスの alignment 順序:")
    for pid, a in main_scores:
        print(f"  {pid}: {a:.4f}")

    # 漸進性チェック: P_{i+1} の alignment は P_i より高いべき
    issues = []
    for i in range(len(main_scores) - 1):
        pid_cur, a_cur = main_scores[i]
        pid_next, a_next = main_scores[i + 1]
        if a_next <= a_cur:
            issues.append(f"  {pid_cur}({a_cur:.4f}) → {pid_next}({a_next:.4f}): 非増加")

    if issues:
        print()
        print("⚠ alignment が非増加な遷移あり（正常: 後のパラダイムほど高い）:")
        for issue in issues:
            print(issue)
    else:
        print("  → メインパス順に alignment が単調増加: OK")
    print()

    return not bool(issues)


def build_virtual_h(paradigm, all_ids):
    """パラダイム P に完全同化した仮想 H を構築する。

    D⁺(P) → 1.0, D⁻(P) → 0.0, それ以外 → 0.5
    """
    h = {d: 0.5 for d in all_ids}
    for d in paradigm.d_plus:
        h[d] = 1.0
    for d in paradigm.d_minus:
        h[d] = 0.0
    return h


def select_shift_target(pid_cur, paradigms, o_star, all_ids):
    """仮想 H_Pi で engine のシフト先選択を再現する。

    返り値: (選択先ID or None, 候補リスト[(pid, alignment)])
    """
    p_cur = paradigms[pid_cur]
    h_pi = build_virtual_h(p_cur, all_ids)

    cur_tension = tension(o_star, p_cur)
    candidates = []
    for p_id in paradigms:
        if p_id == pid_cur:
            continue
        p = paradigms[p_id]
        if not (p.d_all & p_cur.d_all):
            continue
        if tension(o_star, p) >= cur_tension:
            continue
        candidates.append(p_id)

    if not candidates:
        return None, []

    candidate_scores = []
    for p_id in candidates:
        a = alignment(h_pi, paradigms[p_id])
        candidate_scores.append((p_id, a))
    candidate_scores.sort(key=lambda x: -x[1])

    return candidate_scores[0][0], candidate_scores


def check_shift_selection(paradigms, main_path, o_star, all_ids):
    """テーマ2: 全パラダイムからの遷移先と P_T への到達性を検証する。

    1. 全パラダイム（サブ含む）で仮想 H_Pi を構築しシフト先を計算
    2. 遷移グラフを構築
    3. 全パラダイムから P_T（メインパス終点）に到達可能か検証
    """
    print("=" * 65)
    print("テーマ2: シフト先選択と到達性（仮想 H_Pi ベース）")
    print("=" * 65)
    print()

    p_goal = main_path[-1]
    main_set = set(main_path)

    # 全パラダイムの遷移先を計算
    transitions = {}  # pid -> 選択先
    for pid in paradigms:
        if pid == p_goal:
            continue
        target, candidate_scores = select_shift_target(
            pid, paradigms, o_star, all_ids,
        )
        transitions[pid] = target

        is_main = "main" if pid in main_set else "sub"
        t = tension(o_star, paradigms[pid])
        print(f"  {pid} [{is_main}] (tension={t}):")
        if target is None:
            print(f"    → 候補なし（危機状態）")
        else:
            for p_id, a in candidate_scores:
                marker = " ★" if p_id == target else ""
                print(f"    {p_id}: alignment={a:.4f}{marker}")
            print(f"    → {target}")
        print()

    # 到達性チェック: 各パラダイムから遷移を辿って P_T に到達できるか
    print("-" * 40)
    print(f"到達性チェック（目標: {p_goal}）")
    print("-" * 40)

    issues = []
    for start_pid in paradigms:
        if start_pid == p_goal:
            continue

        visited = set()
        current = start_pid
        path = [current]

        while current != p_goal and current is not None and current not in visited:
            visited.add(current)
            current = transitions.get(current)
            if current is not None:
                path.append(current)

        path_str = " → ".join(path)
        if current == p_goal:
            print(f"  {start_pid}: {path_str}  OK")
        elif current is None:
            print(f"  {start_pid}: {path_str} → 行き止まり  NG")
            issues.append(f"{start_pid}: 行き止まり（{path_str}）")
        else:
            # ループ検出
            print(f"  {start_pid}: {path_str} → ループ  NG")
            issues.append(f"{start_pid}: ループ（{path_str}）")

    print()
    if issues:
        print("⚠ 到達不能なパラダイムあり:")
        for issue in issues:
            print(f"  {issue}")
    else:
        print(f"全パラダイムから {p_goal} に到達可能: OK")
    print()

    return not bool(issues)


def main():
    paradigms, questions, all_ids, ps_values, init_pid = load_data()
    data = load_raw()

    main_path = infer_main_path(data, paradigms)
    print(f"データファイル: {data.get('title', '不明')}")
    print(f"メインパス: {' → '.join(main_path)}")
    print(f"パラダイム数: {len(paradigms)} (メイン: {len(main_path)})")
    print(f"質問数: {len(questions)}")
    print()

    # O* の構築
    o_star, r_star = build_o_star(questions)
    print(f"|O*| = {len(o_star)}, |R*| = {len(r_star)}")
    print()

    check_alignment_ordering(paradigms, main_path, o_star, all_ids)
    check_shift_selection(paradigms, main_path, o_star, all_ids)


if __name__ == "__main__":
    main()

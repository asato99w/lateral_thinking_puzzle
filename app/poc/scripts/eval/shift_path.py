"""パラダイムシフト経路の検証。

テーマ 2: alignment 選択の経路正当性
  - O*（全真値観測）に対する各パラダイムの alignment を計算
  - alignment 順序がメインパス順と整合するか確認
  - 各シフトポイントで alignment 選択が正しいパラダイムを選ぶか検証

テーマ 3: 同化接続性
  - 各シフト P_i → P_{i+1} で、同化の起点となる記述素が存在するか
  - R(P_{i+1}) で到達可能な未回答質問の記述素があるか

使い方:
  python shift_path.py                       # turtle_soup.json
  python shift_path.py --data bar_man.json   # bar_man.json
"""
from __future__ import annotations

from common import load_data, load_raw, MAIN_PATH
from engine import (
    init_game,
    init_questions,
    tension,
    alignment,
    compute_effect,
    EPSILON,
)


def infer_main_path(data: dict, paradigms: dict) -> list[str]:
    """データから main_path を推定する。

    1. data["main_path"] があればそのまま使う
    2. data["shift_candidates"] から init → ... → 終端 のチェーンを探す
    3. どちらもなければ MAIN_PATH（デフォルト）を使う
    """
    if "main_path" in data:
        return data["main_path"]

    sc = data.get("shift_candidates")
    if sc:
        # shift_candidates から最長チェーンを探索
        init = data["init_paradigm"]
        # サブパラダイム（S*）を除外してメインパスを構成
        main_ids = {pid for pid in paradigms if not pid.startswith("S")}

        path = [init]
        current = init
        visited = {init}
        while True:
            candidates = sc.get(current, [])
            # メインパラダイムのみ、未訪問のもの
            nexts = [c for c in candidates if c in main_ids and c not in visited]
            if not nexts:
                break
            # 番号順で最初のもの（P1→P2→P3→...）
            nexts.sort()
            current = nexts[0]
            path.append(current)
            visited.add(current)
        return path

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
    """テーマ 2: alignment_h(H*, P) の順序を検証する。"""
    print("=" * 65)
    print("テーマ 2: alignment 選択の経路正当性（H ベース）")
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

    # alignment 選択の問題検出: 各シフトで正しい次パラダイムが選ばれるか
    print("シフト先選択の検証（H* に対する alignment 比較）:")
    selection_ok = True
    for i in range(len(main_path) - 1):
        pid_cur = main_path[i]
        pid_next = main_path[i + 1]
        if pid_cur not in paradigms or pid_next not in paradigms:
            continue

        a_next = alignment(h_star, paradigms[pid_next])

        # pid_cur 以外の全パラダイムとの比較
        competitors = []
        for pid, p in paradigms.items():
            if pid == pid_cur:
                continue
            a_p = alignment(h_star, p)
            competitors.append((pid, a_p))
        competitors.sort(key=lambda x: -x[1])

        best_pid, best_a = competitors[0]
        ok = best_pid == pid_next
        if not ok:
            selection_ok = False

        marker = "OK" if ok else f"NG (alignment は {best_pid}={best_a:.4f} が最大)"
        print(f"  {pid_cur} → 期待: {pid_next}({a_next:.4f}) | 実際の最大: {best_pid}({best_a:.4f}) [{marker}]")

    print()
    if not selection_ok:
        print("結論: alignment_h(H*) による選択ではメインパス順のシフトが保証されない")
        print("  → H* は全真値観測後の状態であり、漸進性は部分観測（実際のプレイ）で自然に成立する")
        print("  → 同化により H は現パラダイムの予測方向に偏るため、近傍パラダイムが優先される")
    else:
        print("結論: alignment_h(H*) による選択でメインパス順のシフトが成立")
    print()

    return selection_ok


def check_assimilation_connectivity(paradigms, questions, main_path, o_star, ps_values, all_ids):
    """テーマ 3: 各シフトにおける同化接続性を検証する。"""
    print("=" * 65)
    print("テーマ 3: 同化接続性")
    print("=" * 65)
    print()

    # 各パラダイムフェーズで回答される質問を推定
    # P_i の D(P_i) に effect 記述素が含まれる質問 = P_i フェーズの質問
    phase_questions = {pid: [] for pid in main_path}
    for q in questions:
        eff = compute_effect(q)
        if q.correct_answer == "irrelevant":
            continue
        eff_ds = {d for d, v in eff}
        for pid in main_path:
            if pid not in paradigms:
                continue
            if eff_ds & paradigms[pid].d_all:
                phase_questions[pid].append(q)
                break  # 最初に所属するフェーズに割り当て

    # 各シフトポイントでの観測推定
    # P_i 終了時の O ≈ Ps + P_1 ~ P_i の質問の effect
    cumulative_o = dict(ps_values)

    all_ok = True
    for i in range(len(main_path) - 1):
        pid_cur = main_path[i]
        pid_next = main_path[i + 1]
        if pid_cur not in paradigms or pid_next not in paradigms:
            continue

        # P_i フェーズの質問回答を O に追加
        for q in phase_questions[pid_cur]:
            eff = compute_effect(q)
            if q.correct_answer != "irrelevant":
                for d, v in eff:
                    cumulative_o[d] = v

        p_next = paradigms[pid_next]

        print(f"--- シフト {pid_cur} → {pid_next} ---")
        print(f"  推定 |O| at shift: {len(cumulative_o)}")

        # 条件 1: O ∩ D(P_{i+1}) の大きさ
        overlap = set(cumulative_o.keys()) & p_next.d_all
        print(f"  O ∩ D({pid_next}): {len(overlap)} 記述素")
        if not overlap:
            print(f"  ⚠ O と D({pid_next}) の重なりなし — 同化起点がない")
            all_ok = False
            print()
            continue

        # 条件 2: prediction が一致する記述素（同化起点）
        assimilation_sources = []
        for d in sorted(overlap):
            pred = p_next.prediction(d)
            obs = cumulative_o[d]
            match = pred == obs
            if match:
                assimilation_sources.append(d)

        print(f"  同化起点（prediction 一致）: {len(assimilation_sources)} 記述素")
        if not assimilation_sources:
            print(f"  ⚠ prediction が一致する記述素なし — 同化が発火しない")
            mismatch_detail = []
            for d in sorted(overlap):
                pred = p_next.prediction(d)
                obs = cumulative_o[d]
                mismatch_detail.append(f"    {d}: O={obs}, pred={pred}")
            for line in mismatch_detail[:10]:
                print(line)
            all_ok = False
            print()
            continue

        # 条件 3: R(P_{i+1}) でソースから到達可能なターゲット
        reachable_targets = set()
        for src, tgt, w in p_next.relations:
            if src in assimilation_sources:
                reachable_targets.add(tgt)

        print(f"  R({pid_next}) 到達可能ターゲット: {len(reachable_targets)} 記述素")
        if reachable_targets:
            for t in sorted(reachable_targets):
                pred_t = p_next.prediction(t)
                h_current = float(cumulative_o.get(t, 0.5))  # 未観測なら 0.5
                observed = t in cumulative_o
                print(f"    {t}: pred={pred_t}, observed={'Y' if observed else 'N'}")
        else:
            print(f"  ⚠ R({pid_next}) のソースに同化起点がない — H が動かない")
            # 関係のソースと同化起点の不一致を表示
            rel_sources = {src for src, _, _ in p_next.relations}
            print(f"    R({pid_next}) のソース: {sorted(rel_sources)}")
            print(f"    同化起点: {sorted(assimilation_sources)}")
            print(f"    交差: {sorted(rel_sources & set(assimilation_sources))}")
            all_ok = False
            print()
            continue

        # 条件 4: ターゲット記述素を含む未回答質問が存在するか
        answered_ids = {q.id for q in phase_questions[pid_cur]}  # 簡易推定
        for j in range(i):
            answered_ids |= {q.id for q in phase_questions[main_path[j]]}

        openable_via_target = []
        for q in questions:
            if q.id in answered_ids:
                continue
            eff = compute_effect(q)
            if q.correct_answer == "irrelevant":
                continue
            for d, v in eff:
                if d in reachable_targets:
                    pred_d = p_next.prediction(d)
                    # 同化で H[d] が pred_d 方向に動く
                    # open 条件: H[d] ≈ v
                    # 動く方向と正解が一致すれば開く可能性あり
                    if pred_d == v:
                        openable_via_target.append((q.id, d, v))
                        break

        print(f"  同化で開く可能性のある質問: {len(openable_via_target)}")
        if openable_via_target:
            for qid, d, v in openable_via_target:
                print(f"    {qid}: H[{d}] → {v} で open")
        else:
            print(f"  ⚠ 同化ターゲットを含む未回答質問がない")
            all_ok = False

        print()

    print("=" * 65)
    if all_ok:
        print("結論: 全シフトで同化接続性が成立")
    else:
        print("結論: 同化接続性に問題あり — 内部構造(R(P))または質問設計の見直しが必要")
    print()

    return all_ok


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

    # テーマ 2
    check_alignment_ordering(paradigms, main_path, o_star, all_ids)

    # テーマ 3
    check_assimilation_connectivity(paradigms, questions, main_path, o_star, ps_values, all_ids)


if __name__ == "__main__":
    main()

"""パラダイムシフト経路の検証。

メインパスは固定リストではなく、遷移グラフから最短パスとして導出する。
  - T（tension(O*, T)=0）を特定
  - 各パラダイムの O* ベース遷移先を最小緩和原理で計算
  - init_paradigm から T への遷移チェーンがメインパス

テーマ1: tension 順序の検証
  - O* に対する各パラダイムの tension を計算
  - メインパス順に tension が単調減少であることを確認
  - メインパスの後のパラダイムほど tension が低いことはデータの構造的性質

テーマ2: シフト先選択の到達性検証（最小緩和原理）
  - 全パラダイム（サブ含む）について最小緩和原理で遷移先を計算
  - 遷移グラフを構築し、全パラダイムから T に到達可能か検証
  - サブパラダイムへの寄り道は許容（引っ掛け）、復帰できるかが問題

テーマ3: 正解予測の包含検査（eo 単調性の構造的保証）
  - メインパスの連続ペア Pi, Pi+1 について、O* 上の正解予測集合の包含を検証
  - { d ∈ O* | Pi が正しく予測 } ⊆ { d ∈ O* | Pi+1 が正しく予測 }
  - この包含が成り立てば、任意の部分的 O に対して eo(Pi+1) >= eo(Pi) が保証される

テーマ4: シフトドライバーの到達性検査
  - メインパスの連続ペア Pi, Pi+1 について:
    - eo ドライバー記述素を特定（Pi+1 が正しく予測し、Pi が不正解 or 予測なし）
    - ドライバーに紐づく質問が Pi の active 時にオープン可能か検証
    - オープン可能なドライバー質問がなければ、部分 O でシフトが起きない
  - スキップドライバーとの競合:
    - Pi+2 のドライバー質問が Pi からオープン可能な場合、Pi+1 がスキップされうる
    - Pi+1 ドライバーが 0 なら構造的にスキップ確定

使い方:
  python shift_path.py                       # turtle_soup.json
  python shift_path.py --data bar_man.json   # bar_man.json
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from common import load_data, load_raw  # noqa: E402
from engine import tension, alignment, compute_effect, explained_o, select_shift_target, _question_all_descriptors


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


def build_virtual_h(paradigm, all_ids):
    """パラダイム P に完全同化した仮想 H を構築する。

    p_pred(d)=1 → 1.0, p_pred(d)=0 → 0.0, それ以外 → 0.5
    """
    h = {d: 0.5 for d in all_ids}
    for d, pred_val in paradigm.p_pred.items():
        h[d] = float(pred_val)
    return h


def select_shift_target_with_details(pid_cur, paradigms, o_star):
    """engine の select_shift_target を呼び出し、詳細情報も返す。

    方式: 最小緩和原理（tension → attention → resolve → pid）。

    返り値: (選択先ID or None, 候補リスト[(pid, tension, attention, resolve)])
    """
    p_cur = paradigms[pid_cur]
    # P_current のアノマリー集合
    anomalies = {
        d for d in p_cur.conceivable
        if d in o_star and p_cur.prediction(d) is not None
        and p_cur.prediction(d) != o_star[d]
    }
    cur_tension = tension(o_star, p_cur)

    candidates = []
    for pid, p in paradigms.items():
        if pid == pid_cur:
            continue
        t = tension(o_star, p)
        if t <= cur_tension:
            att = len({d for d in anomalies if d in p.conceivable})
            res = len({d for d in anomalies
                       if d in p.conceivable
                       and p.prediction(d) is not None and p.prediction(d) == o_star[d]})
            candidates.append((pid, t, att, res))

    if not candidates:
        return None, []

    # tension DESC → attention DESC → resolve ASC → pid ASC
    candidates.sort(key=lambda x: (-x[1], -x[2], x[3], x[0]))
    return candidates[0][0], candidates


def compute_main_path(
    init_pid: str,
    paradigms: dict,
    o_star: dict[str, int],
) -> tuple[list[str], dict[str, str | None]]:
    """遷移グラフから init → T のメインパスを導出する。

    各パラダイムの O* ベース遷移先を最小緩和原理で計算し、init から遷移を辿る。
    遷移先がないパラダイムが終端 T となる。

    返り値: (メインパス, 遷移グラフ全体)
    """
    # 全パラダイムの遷移先を計算（engine の select_shift_target を使用）
    transitions = {}
    for pid in paradigms:
        target = select_shift_target(o_star, paradigms[pid], paradigms)
        transitions[pid] = target

    # init から遷移を辿ってメインパスを導出
    path = [init_pid]
    visited = {init_pid}
    current = init_pid
    while True:
        nxt = transitions.get(current)
        if nxt is None or nxt in visited:
            break
        path.append(nxt)
        visited.add(nxt)
        current = nxt

    return path, transitions


def check_tension_ordering(paradigms, main_path, o_star, all_ids):
    """テーマ1: tension(O*, P) の順序を検証する。

    メインパス順に tension が単調減少であることを確認する。
    """
    print("=" * 65)
    print("テーマ1: tension 順序（O* ベース）")
    print("=" * 65)
    print()

    # 参考: H* ベースの alignment も表示
    h_star = o_star_to_h(o_star, all_ids)

    # 全パラダイムの tension を計算
    all_scores = []
    main_set = set(main_path)
    for pid in sorted(paradigms.keys()):
        p = paradigms[pid]
        a = alignment(h_star, p)
        t = tension(o_star, p)
        overlap = len(p.conceivable & set(o_star.keys()))
        all_scores.append((pid, t, a, overlap))

    print("tension(O*, P) — 全パラダイム:")
    all_scores.sort(key=lambda x: -x[1])
    for pid, t, a, ov in all_scores:
        marker = " ◀ main" if pid in main_set else ""
        print(f"  {pid:4s}: tension={t}  alignment={a:.4f}  |Conceivable∩O*|={ov}{marker}")
    print()

    # メインパスの tension 順序
    main_tensions = [(pid, tension(o_star, paradigms[pid])) for pid in main_path if pid in paradigms]
    print("メインパスの tension 順序:")
    for pid, t in main_tensions:
        print(f"  {pid}: tension={t}")

    # 漸進性チェック: P_{i+1} の tension は P_i より低い（または同じ）べき
    issues = []
    for i in range(len(main_tensions) - 1):
        pid_cur, t_cur = main_tensions[i]
        pid_next, t_next = main_tensions[i + 1]
        if t_next > t_cur:
            issues.append(f"  {pid_cur}(tension={t_cur}) → {pid_next}(tension={t_next}): 非減少")

    if issues:
        print()
        print("⚠ tension が非減少な遷移あり（正常: 後のパラダイムほど低い）:")
        for issue in issues:
            print(issue)
    else:
        print("  → メインパス順に tension が単調減少: OK")
    print()

    return not bool(issues)


def check_shift_selection(paradigms, main_path, transitions, o_star):
    """テーマ2: 全パラダイムからの遷移先と T への到達性を検証する。

    1. 全パラダイム（サブ含む）の遷移先を最小緩和原理で表示
    2. 遷移グラフを構築
    3. 全パラダイムから T に到達可能か検証
    """
    print("=" * 65)
    print("テーマ2: シフト先選択と到達性（最小緩和原理）")
    print("=" * 65)
    print()

    p_goal = main_path[-1]
    main_set = set(main_path)

    # 全パラダイムの遷移先を表示
    for pid in sorted(paradigms.keys()):
        if pid == p_goal:
            continue
        target, candidate_details = select_shift_target_with_details(
            pid, paradigms, o_star,
        )

        is_main = "main" if pid in main_set else "sub"
        t = tension(o_star, paradigms[pid])
        print(f"  {pid} [{is_main}] (tension={t}):")
        if target is None:
            print(f"    → 候補なし（危機状態）")
        else:
            for c_pid, c_t, c_att, c_res in candidate_details:
                marker = " ★" if c_pid == target else ""
                print(f"    {c_pid}: tension={c_t} attention={c_att} resolve={c_res}{marker}")
            print(f"    → {target}")
        print()

    # 到達性チェック: 各パラダイムから遷移を辿って T に到達できるか
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


def correct_prediction_set(o_star: dict[str, int], paradigm) -> set[str]:
    """O* のうち P が正しく予測する記述素の集合。"""
    return {
        d for d, v in o_star.items()
        if paradigm.prediction(d) is not None and paradigm.prediction(d) == v
    }


def check_eo_inclusion(paradigms, main_path, o_star):
    """テーマ3: 正解予測の包含検査。

    メインパスの連続するパラダイム Pi, Pi+1 について、
    Pi の O* 正解予測集合が Pi+1 の部分集合であることを検証する。

    この包含関係が成り立てば、O の任意の部分集合に対して
    eo(Pi+1) >= eo(Pi) が保証される。
    """
    print("=" * 65)
    print("テーマ3: 正解予測の包含検査（eo 単調性の構造的保証）")
    print("=" * 65)
    print()

    # 各パラダイムの正解予測集合を計算
    correct_sets = {}
    for pid in main_path:
        if pid not in paradigms:
            continue
        cs = correct_prediction_set(o_star, paradigms[pid])
        correct_sets[pid] = cs
        print(f"  {pid}: |正解予測| = {len(cs)}")
    print()

    # 連続ペアの包含検査
    issues = []
    for i in range(len(main_path) - 1):
        pid_cur = main_path[i]
        pid_next = main_path[i + 1]
        if pid_cur not in correct_sets or pid_next not in correct_sets:
            continue

        cs_cur = correct_sets[pid_cur]
        cs_next = correct_sets[pid_next]
        diff = cs_cur - cs_next  # Pi にあって Pi+1 にない正解予測

        if diff:
            print(f"  {pid_cur} → {pid_next}: NG — {pid_cur} のみ正解の記述素 ({len(diff)}個):")
            for d in sorted(diff):
                pred_cur = paradigms[pid_cur].prediction(d)
                pred_next = paradigms[pid_next].prediction(d)
                o_val = o_star[d]
                print(f"    {d}: O*={o_val}, {pid_cur} pred={pred_cur}(✓), "
                      f"{pid_next} pred={pred_next}({'✗' if pred_next != o_val else '✓'})")
            issues.append((pid_cur, pid_next, diff))
        else:
            print(f"  {pid_cur} → {pid_next}: OK — 包含関係成立")

    print()
    if issues:
        print("⚠ 包含関係が崩れているペアあり:")
        print("  シミュレーション中の部分的 O で eo 逆転が起こりうる")
    else:
        print("全連続ペアで包含関係成立: 任意の部分 O で eo 単調性保証")
    print()

    return not bool(issues)


def check_shift_driver_reachability(paradigms, main_path, questions, o_star):
    """テーマ4: シフトドライバーの到達性検査。

    メインパスの連続ペア Pi→Pi+1 について:
    1. eo ドライバー記述素を特定
       - Pi+1 が正しく予測し、Pi が不正解 or 予測なし
       - これが O に追加されると eo(Pi+1) > eo(Pi) になりうる
    2. ドライバーに紐づく質問が Pi active 時にオープン可能か
       - _conceivable_blocked で判定
    3. 同時に、Pi+2 のドライバー質問が Pi からオープン可能かも検査
       - Pi+1 のドライバーが到達不能で Pi+2 のドライバーが到達可能なら
         Pi+1 がスキップされる構造的リスク
    """
    print("=" * 65)
    print("テーマ4: シフトドライバーの到達性検査")
    print("=" * 65)
    print()

    issues = []

    for i in range(len(main_path) - 1):
        pid_cur = main_path[i]
        pid_next = main_path[i + 1]
        p_cur = paradigms[pid_cur]
        p_next = paradigms[pid_next]

        # eo ドライバー記述素: Pi+1 正解 & (Pi 不正解 or Pi 予測なし)
        drivers_wrong = []   # Pi が不正解
        drivers_no_pred = [] # Pi が予測なし
        for d, o_val in o_star.items():
            next_pred = p_next.prediction(d)
            if next_pred is None or next_pred != o_val:
                continue
            cur_pred = p_cur.prediction(d)
            if cur_pred is not None and cur_pred != o_val:
                drivers_wrong.append(d)
            elif cur_pred is None:
                drivers_no_pred.append(d)

        all_drivers = sorted(drivers_wrong) + sorted(drivers_no_pred)

        # ドライバーに紐づく質問と Pi からのオープン可能性
        driver_questions = {}  # d -> [(q_id, openable)]
        openable_count = 0
        openable_qs = set()

        for d in all_drivers:
            driver_questions[d] = []
            for q in questions:
                if q.correct_answer == "irrelevant":
                    continue
                eff = compute_effect(q)
                if not any(d_id == d for d_id, v in eff):
                    continue
                # Pi からオープン可能か
                all_descs = _question_all_descriptors(q)
                blocked = any(dd not in p_cur.conceivable for dd in all_descs)
                driver_questions[d].append((q.id, not blocked))
                if not blocked:
                    openable_qs.add(q.id)

        openable_driver_ds = set()
        for d, qs in driver_questions.items():
            if any(ok for _, ok in qs):
                openable_driver_ds.add(d)

        print(f"  {pid_cur} → {pid_next}:")
        print(f"    ドライバー記述素: {len(all_drivers)}"
              f" (Pi不正解: {len(drivers_wrong)}, Pi予測なし: {len(drivers_no_pred)})")
        print(f"    オープン可能なドライバー記述素: {len(openable_driver_ds)}/{len(all_drivers)}")
        print(f"    オープン可能なドライバー質問: {len(openable_qs)}")

        if not openable_driver_ds:
            print(f"    NG: {pid_cur} active 時に {pid_next} の eo ドライバーに到達する質問がない")
            print(f"    → 部分 O で eo({pid_next}) > eo({pid_cur}) が実現不可能")

            # 詳細: ブロックされているドライバー記述素
            print(f"    ブロック詳細:")
            for d in all_drivers[:10]:  # 上位10個
                d_type = "Pi不正解" if d in drivers_wrong else "Pi予測なし"
                qs_info = driver_questions.get(d, [])
                if qs_info:
                    qs_str = ", ".join(f"{qid}({'open' if ok else 'blocked'})"
                                       for qid, ok in qs_info)
                else:
                    qs_str = "(質問なし)"
                print(f"      {d} [{d_type}]: {qs_str}")
            if len(all_drivers) > 10:
                print(f"      ... 他 {len(all_drivers) - 10} 個")

            issues.append((pid_cur, pid_next, "no_reachable_driver"))
        else:
            print(f"    OK")

            # オープン可能なドライバーの内訳
            for d in sorted(openable_driver_ds):
                d_type = "Pi不正解" if d in drivers_wrong else "Pi予測なし"
                qs_str = ", ".join(f"{qid}" for qid, ok in driver_questions[d] if ok)
                print(f"      {d} [{d_type}]: {qs_str}")

        # スキップリスク: Pi+2 のドライバーが Pi からオープン可能か
        if i + 2 < len(main_path):
            pid_skip = main_path[i + 2]
            p_skip = paradigms[pid_skip]

            skip_drivers = []
            for d, o_val in o_star.items():
                skip_pred = p_skip.prediction(d)
                if skip_pred is None or skip_pred != o_val:
                    continue
                cur_pred = p_cur.prediction(d)
                if cur_pred is not None and cur_pred != o_val:
                    skip_drivers.append(d)
                elif cur_pred is None:
                    skip_drivers.append(d)

            skip_openable = set()
            for d in skip_drivers:
                for q in questions:
                    if q.correct_answer == "irrelevant":
                        continue
                    eff = compute_effect(q)
                    if not any(d_id == d for d_id, v in eff):
                        continue
                    all_descs = _question_all_descriptors(q)
                    if not any(dd not in p_cur.conceivable for dd in all_descs):
                        skip_openable.add(d)
                        break

            if skip_openable and not openable_driver_ds:
                print(f"    スキップリスク: {pid_skip} のドライバー {len(skip_openable)}個が"
                      f" {pid_cur} からオープン可能")
                print(f"    → {pid_next} がスキップされ {pid_cur}→{pid_skip} 直接遷移の可能性")
                issues.append((pid_cur, pid_next, "skip_risk",
                               pid_skip, len(skip_openable)))
            elif skip_openable:
                print(f"    (参考) {pid_skip} ドライバーも {len(skip_openable)}個オープン可能"
                      f" — {pid_next} ドライバーも到達可能なので即座の問題ではない")

        print()

    # サマリ
    if issues:
        print("⚠ シフトドライバー到達性の問題あり:")
        for issue in issues:
            if issue[2] == "no_reachable_driver":
                print(f"  {issue[0]}→{issue[1]}: ドライバー到達不能（シフト構造的不可能）")
            elif issue[2] == "skip_risk":
                print(f"  {issue[0]}→{issue[1]}: スキップリスク"
                      f"（{issue[3]} ドライバー {issue[4]}個が先にオープン）")
    else:
        print("全連続ペアでドライバー到達性 OK")
    print()

    return not bool(issues)


def main():
    paradigms, questions, all_ids, ps_values, init_pid = load_data()
    data = load_raw()

    # O* の構築
    o_star, r_star = build_o_star(questions)

    # メインパスを遷移グラフから導出
    main_path, transitions = compute_main_path(
        init_pid, paradigms, o_star,
    )
    terminal = main_path[-1]
    terminal_tension = tension(o_star, paradigms[terminal])

    print(f"データファイル: {data.get('title', '不明')}")
    print(f"初期パラダイム: {init_pid}")
    print(f"終端パラダイム: {terminal} (tension(O*)={terminal_tension})")
    print(f"メインパス（導出）: {' → '.join(main_path)}")
    print(f"パラダイム数: {len(paradigms)} (メインパス: {len(main_path)})")
    print(f"質問数: {len(questions)}")
    print(f"|O*| = {len(o_star)}, |R*| = {len(r_star)}")
    print()

    if terminal_tension > 0:
        print(f"⚠ 終端パラダイム {terminal} の tension(O*)={terminal_tension} > 0")
        print()

    check_tension_ordering(paradigms, main_path, o_star, all_ids)
    check_shift_selection(paradigms, main_path, transitions, o_star)
    check_eo_inclusion(paradigms, main_path, o_star)
    check_shift_driver_reachability(paradigms, main_path, questions, o_star)


if __name__ == "__main__":
    main()

"""段階的オープンの連鎖におけるアノマリーの出現を分析する。

固有質問 → 共有質問 → 次パラダイムの質問 と進む中で、
各パラダイムに対する tension と alignment がどう変化するかを追跡する。
"""
from common import load_data, MAIN_PATH
from engine import (
    init_game,
    compute_effect,
    _assimilate_descriptor,
    tension,
    alignment,
    EPSILON,
)


def classify_effect(q, paradigms):
    """質問の effect 記述素がどのパラダイムに属するかを返す。"""
    eff = compute_effect(q)
    if q.correct_answer == "irrelevant":
        return {}
    eff_ds = {d for d, v in eff}
    homes = {}
    for pid in MAIN_PATH:
        if pid not in paradigms:
            continue
        overlap = eff_ds & paradigms[pid].d_all
        if overlap:
            homes[pid] = overlap
    return homes


def check_anomaly_detail(o, paradigm):
    """アノマリーの詳細を返す。"""
    anomalies = []
    for d in paradigm.d_all & set(o.keys()):
        pred = paradigm.prediction(d)
        if pred != o[d]:
            anomalies.append((d, o[d], pred))
    return anomalies


def simulate_answer(state, q, paradigms):
    """質問に回答し、同化を実行する（シフトなし）。"""
    eff = compute_effect(q)
    if q.correct_answer == "irrelevant":
        for d_id in eff:
            state.r.add(d_id)
    else:
        for d_id, v in eff:
            state.h[d_id] = float(v)
            state.o[d_id] = v

    state.answered.add(q.id)

    p_cur = paradigms[state.p_current]
    if q.correct_answer != "irrelevant":
        for d_id, v in eff:
            pred = p_cur.prediction(d_id)
            if pred is not None and pred == v:
                _assimilate_descriptor(state.h, d_id, p_cur)


def find_openable(state, questions, paradigms):
    """H に基づいてオープン可能な未回答質問を返す。"""
    result = []
    for q in questions:
        if q.id in state.answered:
            continue
        eff = compute_effect(q)
        if q.correct_answer == "irrelevant":
            continue
        for d, v in eff:
            if abs(state.h.get(d, 0.5) - v) < EPSILON:
                result.append(q)
                break
    return result


def main():
    paradigms, questions, all_ids, ps_values, init_pid = load_data()
    q_by_id = {q.id: q for q in questions}

    state = init_game(ps_values, paradigms, init_pid, all_ids)

    # 全質問を分類
    exclusive = {pid: [] for pid in MAIN_PATH}
    shared = []
    orphan = []
    for q in questions:
        if q.correct_answer == "irrelevant":
            continue
        homes = classify_effect(q, paradigms)
        if not homes:
            orphan.append(q)
        elif len(homes) == 1:
            pid = list(homes.keys())[0]
            if pid in exclusive:
                exclusive[pid].append(q)
        else:
            shared.append((q, homes))

    # 初期状態の tension/alignment
    print("各パラダイムの予測構造:")
    for pid in MAIN_PATH:
        if pid not in paradigms:
            continue
        p = paradigms[pid]
        print(f"  {pid}: |D⁺|={len(p.d_plus)}, |D⁻|={len(p.d_minus)}, |R(P)|={len(p.relations)}")
    print()

    def show_state(label):
        print(f"  [{label}] |O|={len(state.o)}")
        for pid in MAIN_PATH:
            if pid not in paradigms:
                continue
            p = paradigms[pid]
            t = tension(state.o, p)
            a = alignment(state.o, p)
            overlap = len(p.d_all & set(state.o.keys()))
            anomaly_detail = check_anomaly_detail(state.o, p)
            line = f"    {pid}: t={t} a={a:.3f} |D∩O|={overlap}"
            if anomaly_detail:
                ads = [f"{d}(O={ov},P={pv})" for d, ov, pv in anomaly_detail]
                line += f" anomaly={ads}"
            print(line)

    show_state("初期")
    print()

    # フェーズ1: P1 固有質問
    print("=" * 60)
    print(f"Phase 1: {init_pid} 固有質問 ({len(exclusive[init_pid])}問)")
    print("=" * 60)

    for q in exclusive[init_pid]:
        simulate_answer(state, q, paradigms)
        eff = compute_effect(q)
        eff_str = ", ".join(f"{d}={v}" for d, v in eff)

        # このステップでのアノマリー変化
        new_anomalies = []
        for pid in MAIN_PATH:
            if pid not in paradigms:
                continue
            detail = check_anomaly_detail(state.o, paradigms[pid])
            if detail:
                new_anomalies.extend([(pid, d, ov, pv) for d, ov, pv in detail])

        line = f"  {q.id}({q.correct_answer}) [{eff_str}]"
        if new_anomalies:
            for pid, d, ov, pv in new_anomalies:
                line += f" ★{pid}:anomaly({d} O={ov}≠P={pv})"
        print(line)

    print()
    show_state(f"{init_pid}固有 完了")
    print()

    # open(H) で開く共有質問
    openable = find_openable(state, questions, paradigms)
    openable_shared = [(q, classify_effect(q, paradigms)) for q in openable
                       if len(classify_effect(q, paradigms)) >= 2]

    print(f"  → open(H) で開く共有質問: {len(openable_shared)}問")
    for q, homes in openable_shared:
        print(f"    {q.id} [{' & '.join(homes.keys())}]")
    print()

    # フェーズ2: 共有質問
    if openable_shared:
        print("=" * 60)
        print(f"Phase 2: 共有質問 ({len(openable_shared)}問)")
        print("=" * 60)

        for q, homes in openable_shared:
            simulate_answer(state, q, paradigms)
            eff = compute_effect(q)
            eff_str = ", ".join(f"{d}={v}" for d, v in eff)

            new_anomalies = []
            for pid in MAIN_PATH:
                if pid not in paradigms:
                    continue
                detail = check_anomaly_detail(state.o, paradigms[pid])
                if detail:
                    new_anomalies.extend([(pid, d, ov, pv) for d, ov, pv in detail])

            line = f"  {q.id}({q.correct_answer}) [{eff_str}]"
            if new_anomalies:
                for pid, d, ov, pv in new_anomalies:
                    line += f" ★{pid}:anomaly({d} O={ov}≠P={pv})"
            print(line)

        print()
        show_state("共有質問 完了")
        print()

        # さらに開く質問
        openable2 = find_openable(state, questions, paradigms)
        newly = [q for q in openable2 if q.id not in {qq.id for qq, _ in openable_shared}]
        if newly:
            print(f"  → さらに開く質問: {len(newly)}問")
            for q in newly:
                homes = classify_effect(q, paradigms)
                home_str = " & ".join(homes.keys()) if homes else "orphan"
                print(f"    {q.id} [{home_str}] 「{q.text}」")
        else:
            print(f"  → さらに開く質問: なし")
        print()

    # 残りのパラダイムの質問を順に回答
    for pid in MAIN_PATH[1:]:
        if pid not in paradigms:
            continue
        remaining = [q for q in exclusive[pid] if q.id not in state.answered]
        if not remaining:
            continue

        print("=" * 60)
        print(f"Phase: {pid} 固有質問 ({len(remaining)}問)")
        print("=" * 60)

        for q in remaining:
            simulate_answer(state, q, paradigms)
            eff = compute_effect(q)
            eff_str = ", ".join(f"{d}={v}" for d, v in eff)

            new_anomalies = []
            for pid2 in MAIN_PATH:
                if pid2 not in paradigms:
                    continue
                detail = check_anomaly_detail(state.o, paradigms[pid2])
                if detail:
                    new_anomalies.extend([(pid2, d, ov, pv) for d, ov, pv in detail])

            line = f"  {q.id}({q.correct_answer}) [{eff_str}]"
            if new_anomalies:
                for apid, d, ov, pv in new_anomalies:
                    line += f" ★{apid}:anomaly({d} O={ov}≠P={pv})"
            print(line)

        print()
        show_state(f"{pid}固有 完了")
        print()

    # 最終サマリ
    print("=" * 60)
    print("最終サマリ")
    print("=" * 60)
    show_state("全回答後")
    print()
    print(f"未回答: {len(questions) - len(state.answered)}問")
    unanswered = [q for q in questions if q.id not in state.answered]
    for q in unanswered:
        print(f"  {q.id}: 「{q.text}」")


if __name__ == "__main__":
    main()

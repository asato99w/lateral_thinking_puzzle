"""シフト未発動のデバッグスクリプト（チェーン方式）。"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "src"))

from common import load_data, derive_qp, classify_questions, compute_reachability_path
from engine import init_game, open_questions, update, tension, select_shift_target

paradigms, questions, all_ids, ps_values, init_pid = load_data()

path = compute_reachability_path(init_pid, paradigms, questions)
print(f"到達パス: {' → '.join(path)}")

state = init_game(ps_values, paradigms, init_pid, all_ids)
current_open = open_questions(state, questions, paradigms)

for idx in range(len(path) - 1):
    pid_from = path[idx]
    pid_to = path[idx + 1]
    p_from = paradigms[pid_from]
    p_to = paradigms[pid_to]

    state.p_current = pid_from

    qp = derive_qp(questions, p_from)
    safe_qs, anomaly_qs = classify_questions(qp, p_from)

    # 前パラダイムの蓄積後のオープン質問を更新
    newly_opened = open_questions(state, questions, paradigms)
    for oq in newly_opened:
        if oq not in current_open:
            current_open.append(oq)

    already_answered = [q.id for q in qp if q.id in state.answered]
    remaining_safe = [q.id for q in safe_qs if q.id not in state.answered]
    remaining_anom = [q.id for q in anomaly_qs if q.id not in state.answered]
    open_anom = [q.id for q in anomaly_qs if q in current_open and q.id not in state.answered]

    print(f"\n=== {pid_from} → {pid_to} ===")
    print(f"  |O| = {len(state.o)}, |answered| = {len(state.answered)}")
    print(f"  Q({pid_from}): {len(qp)} (safe={len(safe_qs)}, anom={len(anomaly_qs)})")
    print(f"  既回答: {already_answered}")
    print(f"  未回答 safe: {remaining_safe}")
    print(f"  未回答 anomaly: {remaining_anom}")
    print(f"  オープン済み anomaly: {open_anom}")

    # tension/resolve の現在値
    t_from = tension(state.o, p_from)
    t_to = tension(state.o, p_to)
    anom_set = {d for d, pred in p_from.p_pred.items() if d in state.o and pred != state.o[d]}
    res = len({d for d in anom_set if p_to.prediction(d) is not None and p_to.prediction(d) == state.o[d]})
    print(f"  開始時: tension({pid_from})={t_from}, tension({pid_to})={t_to}, resolve={res}, N={p_to.shift_threshold}")

    # シミュレーション
    anomaly_ids = {q.id for q in anomaly_qs}
    answer_queue = [q for q in qp if q.id not in state.answered and q.id not in anomaly_ids]
    queued_ids = {q.id for q in answer_queue}
    for q in anomaly_qs:
        if q.id not in state.answered and q in current_open and q.id not in queued_ids:
            answer_queue.append(q)
            queued_ids.add(q.id)

    step = 0
    shift_fired = False
    while answer_queue:
        q = answer_queue.pop(0)
        if q.id in state.answered:
            continue
        step += 1

        state, current_open = update(state, q, paradigms, questions, current_open)

        t_from = tension(state.o, p_from)
        t_to = tension(state.o, p_to)
        anom_set = {d for d, pred in p_from.p_pred.items() if d in state.o and pred != state.o[d]}
        res = len({d for d in anom_set if p_to.prediction(d) is not None and p_to.prediction(d) == state.o[d]})
        selected = select_shift_target(state.o, p_from, paradigms)

        new_opens = [oq.id for oq in current_open if oq.id not in queued_ids and oq.id not in state.answered]

        if selected is not None and not shift_fired:
            print(f"  ★ step {step}: {q.id} → shift={selected}, t({pid_from})={t_from}, t({pid_to})={t_to}, res={res}, N={p_to.shift_threshold}")
            shift_fired = True
        elif q.id in anomaly_ids:
            print(f"  step {step}: {q.id} (anom) t({pid_from})={t_from}, t({pid_to})={t_to}, res={res}")

        if new_opens:
            print(f"    新規オープン: {new_opens}")
            for oq in current_open:
                if oq.id not in queued_ids and oq.id not in state.answered:
                    answer_queue.append(oq)
                    queued_ids.add(oq.id)

    if not shift_fired:
        t_from = tension(state.o, p_from)
        t_to = tension(state.o, p_to)
        anom_set = {d for d, pred in p_from.p_pred.items() if d in state.o and pred != state.o[d]}
        res = len({d for d in anom_set if p_to.prediction(d) is not None and p_to.prediction(d) == state.o[d]})
        print(f"  ✗ 未発動 (steps={step})")
        print(f"    最終: |O|={len(state.o)}, t({pid_from})={t_from}, t({pid_to})={t_to}, res={res}, N={p_to.shift_threshold}")
        not_answered = [q.id for q in qp if q.id not in state.answered]
        print(f"    未回答: {not_answered}")

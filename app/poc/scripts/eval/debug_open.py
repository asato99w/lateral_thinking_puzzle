"""open_questions のトレース。"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "src"))

from common import load_data, derive_qp, classify_questions
from engine import init_game, open_questions, update, tension, _reachable, compute_effect

paradigms, questions, all_ids, ps_values, init_pid = load_data()

# チェーンで P1 をシミュレーション
state = init_game(ps_values, paradigms, init_pid, all_ids)
current_open = open_questions(state, questions, paradigms)

state.p_current = "P1"
p1 = paradigms["P1"]
qp1 = derive_qp(questions, p1)
safe1, anom1 = classify_questions(qp1, p1)
anom_ids1 = {q.id for q in anom1}
queue = [q for q in qp1 if q.id not in anom_ids1]
queued = {q.id for q in queue}
for q in anom1:
    if q in current_open and q.id not in queued:
        queue.append(q)
        queued.add(q.id)

while queue:
    q = queue.pop(0)
    if q.id in state.answered:
        continue
    state, current_open = update(state, q, paradigms, questions, current_open)
    for oq in current_open:
        if oq.id not in queued and oq.id not in state.answered:
            queue.append(oq)
            queued.add(oq.id)

print(f"P1 phase 完了: |O|={len(state.o)}, |answered|={len(state.answered)}")

# P2 に切り替え
state.p_current = "P2"
p2 = paradigms["P2"]

# P2 safe 質問を回答
qp2 = derive_qp(questions, p2)
safe2, anom2 = classify_questions(qp2, p2)
for q in safe2:
    if q.id not in state.answered:
        state, current_open = update(state, q, paradigms, questions, current_open)

print(f"P2 safe 完了: |O|={len(state.o)}, |answered|={len(state.answered)}")

# open_questions のトレース
consistent = set()
anomaly_set = set()
for d, v in state.o.items():
    pred = p2.prediction(d)
    if pred is None:
        continue
    if pred == v:
        consistent.add(d)
    else:
        anomaly_set.add(d)

consistent_reach = _reachable(consistent, p2)
anomaly_reach = _reachable(anomaly_set, p2)

print(f"|Consistent| = {len(consistent)}, |Anomaly| = {len(anomaly_set)}")
print(f"Anomaly descriptors: {sorted(anomaly_set)}")
print(f"|consistent_reach| = {len(consistent_reach)}, |anomaly_reach| = {len(anomaly_reach)}")

# q29-q32 のトレース
for q in anom2:
    prereqs_met = all(d in state.o for d in q.prerequisites)
    eff = compute_effect(q)
    reasons = []
    opened = False
    for d_id, v in eff:
        in_c = d_id in consistent_reach
        pred_match = p2.prediction(d_id) == v
        in_a = d_id in anomaly_reach
        if in_c and pred_match:
            reasons.append(f"{d_id}: 3a OK (consistent_reach + pred={v})")
            opened = True
        elif in_a:
            reasons.append(f"{d_id}: 3b OK (anomaly_reach)")
            opened = True
        else:
            reasons.append(f"{d_id}: NG (in_c_reach={in_c}, pred={p2.prediction(d_id)}, v={v}, in_a_reach={in_a})")
    print(f"\n  {q.id}: prereqs_met={prereqs_met}, would_open={opened}")
    for r in reasons:
        print(f"    {r}")

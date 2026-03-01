# Round 1: Structural Fixes

Date: 2026-03-01

## Initial L2 Results (all NG)
- L2-0: NG — truth_paradigm missing, shift chain P0→P1→S1→P3
- L2-1: NG — P0 Ft-1, P1 Fs-39/Fs-40/Ft-18/Ft-22, P2 Ft-13 uncovered
- L2-4: NG — P0 layer0 anomaly ratio 0.80, P2 bottleneck 4
- L2-5: NG — 0/51 reach T

## Fixes Applied

### Fix 1: Add truth_paradigm
- Added `truth_paradigm: "P3"` to JSON root

### Fix 2: Remove S1 and S2 paradigms
- S1 ("Wild Animal Threat") and S2 ("Self-Harm Avoidance") removed
- These disrupted neighbor computation: P2 resolved ALL P1 anomalies → Remaining(P2,P1)=∅ → Hasse diagram selected S1/S2 as closer neighbors instead of P2
- Also removed S1/S2 from all question paradigm lists

### Fix 3: Fix Explained containment for P2
- Added Fs-16=1 and Fs-28=1 to P2's p_pred
- Without these, Explained(P1) ⊄ Explained(P2), breaking depth computation (P2 got depth=1 instead of expected 2)
- Note: P2 depth remains 1 after fix due to P1/P2 being siblings (both neighbors of P0)

### Fix 4: Cover P0 anomaly Ft-1
- Added P0 to q09's paradigms (q09: "Was Mr. A lost?" — covers Ft-1)

### Fix 5: Cover P1 anomalies Fs-39, Fs-40, Ft-18, Ft-22
- Added P1 to q18's paradigms (covers Fs-40)
- Added P1 to q19's paradigms (covers Fs-39, Ft-18, Ft-22)

### Fix 6: Cover P2 anomaly Ft-13
- Added P2 to q24's paradigms (covers Ft-13)

### Fix 7: Reduce P2 bottleneck
- Removed Ft-1 from q22's prerequisites
- Original chain: q07→q08→q09→q22→q23 (bottleneck=4)
- New chain: q22→q23 (bottleneck=1)

## Results After Round 1
- L2-0: OK
- L2-1: OK
- L2-4: OK
- L2-5: NG — 0/51 reach T (stuck at P1, no questions can open)

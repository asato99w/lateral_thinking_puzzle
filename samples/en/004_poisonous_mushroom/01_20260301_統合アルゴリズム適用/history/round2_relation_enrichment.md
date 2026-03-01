# Round 2: Relation and P_pred Enrichment

Date: 2026-03-01

## Problem
L2-5 stuck at P1: after P0→P1 shift, `open_questions()` returns empty — no Q(P1) question effects reachable via R(P1) from consistent/anomaly descriptors.

Root cause: P1 had only 9 relations, insufficient to connect observed descriptors to target question effects.

## Fixes Applied

### P0: +1 relation (8→9 total, later reverted to 8 by data structure)
- Fs-5 → Ft-1 (danger implies lost)

### P1: +7 p_pred entries, +16 relations (9→25)
p_pred additions: Ft-1=1, Ft-2=1, Ft-3=1, Fs-25=1, Fs-26=1, Fs-28=1, D-8=1

Relations added (consistent exploration chains):
- Fs-5 → Ft-1 → Ft-2 → D-8 (danger→lost→mountains→detail)
- Ft-1 → Ft-3 (lost→didn't know way)
- Fs-13 → Fs-28 (nature→outdoor activity)
- Fs-11 → Ft-17 (mushroom knowledge→evidence connection)

Relations added (anomaly exploration chains):
- Fs-32 → Fs-10 (no purpose→absence)
- Fs-10 → Fs-21 (absence→sign)
- Fs-21 → Fs-19 (sign→importance)
- Fs-10 → Fs-18 (absence→no edible)
- Fs-18 → Fs-40 (no edible→human activity)
- Fs-40 → Fs-39 (human activity→area visited)
- Fs-39 → Fs-38 (area visited→others in area)
- Fs-38 → Fs-30 (others→relief)
- Fs-40 → Ft-18 (human activity→other pickers)
- Ft-18 → Ft-22 (other pickers→accessible)
- Fs-44 → Fs-46 (reasoning trigger→logical)
- Fs-46 → Fs-22 (logical→reasoning)

### P2: +12 p_pred entries, +13 relations (17→30)
p_pred additions: Ft-1=1, Ft-2=1, Ft-3=1, D-8=1, Ft-15=1, Ft-19=1, Pt-4=1, Ft-10=1, Ft-23=1, Ft-33=1, Ft-11=1, Ft-40=1

Relations added (consistent exploration):
- Fs-5 → Ft-1 → Ft-2 → D-8 (carried from P1)
- Ft-1 → Ft-3
- Fs-18 → Fs-40 → Fs-39 → Fs-38 → Fs-30
- Fs-44 → Fs-46 → Fs-22 → Fs-21 → Fs-19
- Ft-17 → D-3 → Ft-18 → Ft-22 → Ft-29 → Ft-30
- Fs-11 → Ft-17
- Ft-14 → Ft-15 → Ft-19, Ft-15 → Pt-4

Relations added (anomaly exploration):
- Fs-28 → Ft-10 (outdoor activity→foraging connection)
- Ft-22 → Ft-23 → Ft-33 (accessible→trails)
- Ft-8 → Ft-13 → Ft-40 (foraging→lost→consequence)
- Ft-8 → Ft-11 (foraging→activity detail)

## Results After Round 2
- L2-0: OK
- L2-1: OK
- L2-4: OK
- L2-5: NG — 49/50 random OK, 1/50 stuck at P2

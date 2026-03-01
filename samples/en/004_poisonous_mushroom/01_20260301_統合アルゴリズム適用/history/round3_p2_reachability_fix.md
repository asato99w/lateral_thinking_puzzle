# Round 3: P2 Reachability Fix

Date: 2026-03-01

## Problem
L2-5: 1/50 random trial stuck at P2. Seed=38 fails because q22's effect descriptors (Fs-28, D-4) are unreachable from P2's consistent descriptors. No relation leads TO Fs-28 in P2.

## Fix Applied

### P2: +1 relation (30→31)
- Ft-1 → Fs-28 (being lost implies outdoor activity context)

This enables q22 to open in P2 by making Fs-28 reachable from Ft-1 (which is consistently observed).

## Final Results
- L2-0: OK — P0 → P1 → P2 → P3
- L2-1: OK — local + global completeness
- L2-4: OK — all paradigms pass layer structure
- L2-5: OK — 51/51 trials reach T

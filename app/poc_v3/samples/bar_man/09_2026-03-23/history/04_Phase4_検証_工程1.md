# Phase 4: 検証（工程1: 真側）

## 適用規則
- `rules/検証_工程1_v3.md`

## 自動検証結果（run_all.py）
```
check_integrity: PASS
check_reachability: PASS
check_chain_consistency: PASS (SKIP: 連鎖メタ情報省略)
Result: ALL PASS
```

## 手動検証

### Step 1: 構造的整合性 → PASS
- 全38命題のID一意 ✓
- 全6質問のID一意 ✓
- 全reveals参照先存在 ✓
- 全fc/ec参照先存在 ✓

### Step 2: 利用可能条件の到達可能性 → PASS
| Q | reveals | fc条件 | 到達可能性 |
|---|---|---|---|
| Q1 | D-CA1 | [[D-3,D-S10]] | D-3:EC開始時, D-S10:initial ✓ |
| Q2 | D-5 | [[D-4]] | D-4:EC開始時 ✓ |
| Q3 | D-TB3 | [[D-4]] | D-4:EC開始時, prereq D-5:Q2 ✓ |
| Q4 | D-TA1 | [[D-8]] | D-8:EC(Q1+Q3後) ✓ |
| Q5 | D-TA2 | [[D-9]] | D-9:EC(Q4後), prereq D-TA1:Q4 ✓ |
| Q6 | D-10 | [[D-9,D-1]] | D-9:EC(Q4後), D-1:EC開始時 ✓ |

N*/NF*なし ✓, 循環依存なし ✓

### Step 3: 否定関係 → PASS（真側のみ、いいえ質問なし）

### Step 4: reveals網羅性 → PASS
FC-derived命題: D-CA1(Q1), D-5(Q2), D-TB3(Q3), D-TA1(Q4), D-TA2(Q5), D-10(Q6) 全て質問あり ✓
EC-derived命題: D-1,D-2,D-3,D-4,D-6,D-7,D-8,D-9,D-11,D-12,D-13,D-TB2,D-TA3,D-TB4,FPC1,FPC2,FP = EC経由で確認可能 ✓

### Step 5: T整合性 → PASS（Phase 3で検証済み）

### Step 6: reveals厳密性 → PASS（Phase 3で検証済み）

### Step 7: prerequisites確立可能性 → PASS
- Q3.prereq[D-5] = Q2.reveals ✓
- Q5.prereq[D-TA1] = Q4.reveals ✓
- Q6.prereq[D-TA1] = Q4.reveals ✓

### Step 7.5: 質問文含意検証 → PASS（Phase 3で検証済み）

### Step 8: 1段階推論 → PASS

### Step 9: パストレース（エンジンシミュレーション実施）

**Path 1: Q1→Q2→Q3→Q4→Q5 → COMPLETE（5問）**
```
Start: confirmed=19, derived=3 {D-CA1,D-5,D-TB3}
Q1→ D-CA1 confirmed
Q2→ D-5 confirmed
Q3→ D-TB3 confirmed → EC: D-6,D-TB2,D-7,D-8 → FC: D-TA1 derived
Q4→ D-TA1 confirmed → EC: D-9 → FC: D-10,D-TA2 derived
Q5→ D-TA2 confirmed → EC: D-11,D-12,D-TA3,D-13,D-TB4,FPC1,FPC2,FP → COMPLETE
```

**Path 2: Q2→Q3→Q1→Q4→Q5 → COMPLETE（5問）**
```
Q2→ D-5 confirmed
Q3→ D-TB3 confirmed (prereq D-5✓)
Q1→ D-CA1 confirmed → EC: D-6,D-TB2,D-7,D-8 → FC: D-TA1 derived
Q4→ D-TA1 confirmed → FC: D-10,D-TA2 derived
Q5→ D-TA2 confirmed → EC chain → COMPLETE
```

**Path 3: Q2→Q1→Q3→Q4→Q6→Q5 → COMPLETE（6問）**
```
Q2→ D-5 confirmed
Q1→ D-CA1 confirmed
Q3→ D-TB3 confirmed → EC chain
Q4→ D-TA1 confirmed
Q6→ D-10 confirmed (追加情報)
Q5→ D-TA2 confirmed → COMPLETE
```

## 総合結果: ALL PASS

## 注記
- models.py に entailment_conditions フィールドを追加（エンジンとの整合性修正）

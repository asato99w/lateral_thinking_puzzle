# Phase 3: 質問生成

## 適用規則
- `rules/質問生成_v4.md`

## 質問一覧（真側、全6問）

| ID | 質問文 | 回答 | reveals | mechanism | prerequisites |
|---|---|---|---|---|---|
| Q1 | 男が水を求めたのは、渇き以外の理由がありましたか？ | はい | D-CA1 | observation | - |
| Q2 | 男はバーに入る前から何かに困っていましたか？ | はい | D-5 | observation | - |
| Q3 | BTの行為で、男が困っていたことは解決しましたか？ | はい | D-TB3 | observation | D-5 |
| Q4 | 男は体に何か異変がありましたか？ | はい | D-TA1 | observation | - |
| Q5 | BTは男の異変に気づいていましたか？ | はい | D-TA2 | observation | D-TA1 |
| Q6 | BTが銃を向けたのは、男の異変に気づいたからですか？ | はい | D-10 | link | D-TA1 |

## YES進行原則の遵守
全質問が「はい」回答。「いいえ」質問なしでクリア可能。✓

## 質問の1次チェック

### Q1: 渇き以外の理由
- T文脈: しゃっくり対処が理由 → 渇き以外 → はい ✓
- reveals厳密性: 「渇き以外の理由がある→はい」→「渇き以外の理由があった」= D-CA1 ✓
- 前提分析: 「男が水を求めた」→ D-S10 (initial) ✓

### Q2: 困っていたか
- T文脈: しゃっくりが止まらず困っていた → はい ✓
- reveals: 「困っていた→はい」→「困っていた」= D-5 ✓
- 前提: なし（基本的な質問）✓

### Q3: 解決したか
- T文脈: しゃっくりが止まった → はい ✓
- reveals: 「解決した→はい」→ D-TB3 ✓
- 前提: 「困っていたこと」→ D-5 (prerequisites) ✓

### Q4: 体に異変
- T文脈: しゃっくり = 身体的異変 → はい ✓
- reveals: 「異変があった→はい」→ D-TA1 ✓
- 前提: なし ✓

### Q5: BTが気づいた
- T文脈: BTはしゃっくりに気づいた → はい ✓
- reveals: 「気づいていた→はい」→ D-TA2 ✓
- 前提: 「異変」→ D-TA1 (prerequisites) ✓

### Q6: 異変に気づいたから銃を向けた
- T文脈: しゃっくりに気づき驚かせようとした → はい ✓
- reveals: 「気づいたから→はい」→ D-10 ✓
- 前提: 「異変」→ D-TA1 (prerequisites) ✓

## 探索パスの検証

### Path 1: Q1 → Q2 → Q3 → Q4 → Q5（標準順）
1. Q1: D-CA1 confirmed. EC: -
2. Q2: D-5 confirmed. FC: D-TB3 derived.
3. Q3: D-TB3 confirmed. EC: D-6, D-7, D-8, D-TB2. FC: D-TA1 derived.
4. Q4: D-TA1 confirmed. EC: D-9. FC: D-TA2, D-10 derived.
5. Q5: D-TA2 confirmed. EC: D-11,D-12,D-TA3,D-13,D-TB4,FPC1,FPC2,FP. **COMPLETE**

### Path 2: Q2 → Q3 → Q1 → Q4 → Q5（問題発見先行）
1. Q2: D-5 confirmed.
2. Q3: D-TB3 confirmed (prereq D-5✓). EC: D-6 待ち (D-CA1未確認).
3. Q1: D-CA1 confirmed. EC: D-6→D-7→D-8→D-TB2. FC: D-TA1 derived.
4. Q4: D-TA1 confirmed.
5. Q5: D-TA2 confirmed → EC chain → FP. **COMPLETE**

### Path 3: Q2 → Q1 → Q3 → Q4 → Q6 → Q5（D-10経由）
1. Q2: D-5 confirmed.
2. Q1: D-CA1 confirmed.
3. Q3: D-TB3 confirmed. EC chain → D-8.
4. Q4: D-TA1 confirmed.
5. Q6: D-10 confirmed. (D-TA2はまだderived)
6. Q5: D-TA2 confirmed → **COMPLETE**

全パス合理的。各質問の開放は fc/prerequisites により自然に説明される。✓

## fc確定（Phase 2からの変更なし）

Phase 2で確定したfc/ecをそのまま使用。質問のreveals対象:
- D-CA1.fc = [[D-3, D-S10]]: Q1で確認
- D-5.fc = [[D-4]]: Q2で確認
- D-TB3.fc = [[D-4]]: Q3で確認
- D-TA1.fc = [[D-8]]: Q4で確認
- D-TA2.fc = [[D-9]]: Q5で確認
- D-10.fc = [[D-9, D-1]]: Q6で確認

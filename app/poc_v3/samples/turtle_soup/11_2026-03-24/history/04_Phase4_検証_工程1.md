# Phase 4: 検証（工程1: 真側）

## Step 1: 構造的整合性 → PASS

- 命題ID: 25個（I×12, P×11, FP, N1a, H1a）全て一意
- 質問ID: 24個（Q1a〜Q12）全て一意
- reveals: 全て存在する命題IDを参照
- fc/negation_of: 全て存在する命題IDを参照
- initial_confirmed: S1-S17全て_phase2.s_propositionsに定義あり

## Step 2: 利用可能条件の到達可能性 → PASS

- 全fcがS命題またはP/I命題（はい質問のreveals）のみを参照
- N*/NF*がfcに含まれない（YES進行原則）
- 循環依存なし

## Step 3: 否定関係の整合性 → PASS

- Q1a(いいえ) → N1a.negation_of = H1a ✓
- H1a.negation_of = N1a ✓（対称）
- H1a.fc = [[S5,S6,S16]] ✓

## Step 4: reveals の網羅性 → PASS

- 全23命題（H1a除く）にrevealsする質問が存在
- 全24質問がrevealsを持つ

## Step 5: T整合性と命題品質 → PASS

- 全回答がTと整合
- 全命題の真偽がTから一意に定まる
- 全命題の意味が確定的

## Step 6: reveals の厳密性 → PASS（修正後）

修正: I3/Q3aの整合性
- 旧I3: "名称と実態が異なっていた"（Q3aの「可能性がありますか」と不整合）
- 新I3: "今回の本物のウミガメのスープと以前飲んだスープは同一の料理ではない"
- 新Q3a: "今回の本物のウミガメのスープと以前飲んだスープは、同じ料理ではなかったということですか？"

## Step 7: prerequisites の対話上確立可能性 → PASS

全prerequisites命題がいずれかの質問のrevealsに含まれる:
- I2 → Q2a, P2 → Q4b, P4 → Q5b, P7 → Q9b, P8 → Q10b, P5 → Q8b, P9 → Q11b

## Step 7.5: 質問文の含意検証 → PASS

各質問の前提がfc/prerequisitesで保証されていることを確認。

## Step 8: 1段階推論原則 → PASS

全fcが単一の推論ステップとして妥当。FP.fc（6命題）は全背景が揃った時の一括推論として許容。

## Step 8.5: 連鎖構造とfcの整合性 → PASS

- 8.5a: 全targetのfcが直前の中間命題を参照 ✓
- 8.5b: 全連鎖で戦術ステップ数 ≤ 中間命題数 ✓

## Step 9: パストレース → PASS

3パスを検証:

### パス1（味から入る）
初手: Q1b(I1)→Q1c(P1)→Q2a(I2)→Q2b(P10)
並行: Q4a(I4)→Q4b(P2)→Q5a(I5)→Q5b(P4)
合流: Q7a(I7)→Q7b(P3)→Q8a(I9)→Q8b(P5)
継続: Q6a(I6)→Q6b(P6)→Q9a(I10)→Q9b(P7)→Q10a(I11)→Q10b(P8)→Q11a(I12)→Q11b(P9)
解消: Q3a(I3)→Q3b(P11)→Q12(FP)

### パス2（過去の苦境から入る）
初手: Q4a→Q4b→Q5a→Q5b→Q6a→Q6b
並行: Q7a→Q7b→Q8a→Q8b
継続: Q9a→Q9b→Q10a→Q10b→Q11a→Q11b
味: Q1b→Q1c→Q2a→Q2b→Q3a→Q3b→Q12

### パス3（死の経験から入る）
初手: Q7a→Q7b→Q4a→Q4b→Q5a→Q5b→Q8a→Q8b
継続: Q6a→Q6b→Q9a→Q9b→Q10a→Q10b→Q11a→Q11b
味: Q1b→Q1c→Q2a→Q2b→Q3a→Q3b→Q12

全パスでFPに到達可能。行き詰まりなし。

## 総合結果: PASS

# Phase 7: 調整

## Step A: 間引き

### 冗長ペア（不十分）
1. KRA1→IM6: "身体的異変"→"外見で認識可能な症状" → **IM6を間引き**（KRA1のラベルが優れている）
2. IM8→KRB3: "対処成功"→"問題解消" → **IM8を間引き**（デフォルト: 導出元を間引く）

### fc付け替え
- KRA2.fc: [[IM6]] → [[KRA1]]
- KRB3.fc: [[IM8]] → [[KRA3, KRB1]]

### 削除
- 命題: IM6, IM8, HF15, NF15, HF17, NF17（6件）
- 質問: QT9, QT13, QF15, QF17（4件）

## Step B: 演繹関係

| ソース | 対象 | 判定 | 理由 |
|---|---|---|---|
| KRA1+KRA2+KRA3 | FPC1 | 演繹 | 3命題の論理的結合 |
| KRB1+KRB2+KRB3+KRB4 | FPC2 | 演繹 | 4命題の論理的結合 |

FPC1, FPC2にentailment_conditionsを設定。

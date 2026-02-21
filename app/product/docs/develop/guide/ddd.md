# DDD (Domain-Driven Design) ガイド

## 概要

本プロジェクトではドメイン駆動設計を採用し、
水平思考パズルのゲーム理論をそのままコードに反映する。
POCで検証済みの理論用語（パラダイム、記述素、同化、緊張等）を
ユビキタス言語としてコード全体で統一する。

## ユビキタス言語

理論・POC・製品コードで同じ用語を使う。

| ドメイン用語 | 英語名 | 意味 |
|-------------|--------|------|
| 記述素 | Descriptor | パズルの最小意味単位 |
| パラダイム | Paradigm | プレイヤーの解釈枠組み |
| 肯定記述素 | D⁺ (dPlus) | パラダイムが「成立する」と予測する記述素 |
| 否定記述素 | D⁻ (dMinus) | パラダイムが「成立しない」と予測する記述素 |
| 関係辺 | Relation | 記述素間の伝播経路と重み |
| 質問 | Question | プレイヤーが選択する質問 |
| 効果 | Effect | 質問回答による記述素への影響 |
| 仮説状態 | H | 各記述素の確率値 [0, 1] |
| 観測 | O | 確定した記述素の値 |
| 不関与 | R | 問題に関係ないと判明した記述素 |
| 緊張 | Tension | パラダイムと観測の矛盾数 |
| 適合度 | Alignment | H値に基づくパラダイム適合度 |
| 同化 | Assimilate | パラダイムを通じた情報伝播 |
| パラダイムシフト | Paradigm Shift | 解釈枠組みの切り替え |
| オープン質問 | Open Questions | 現在選択可能な質問群 |
| クリア質問 | Clear Question | 選択するとクリアになる質問 |
| 前提事実 | Ps (Premise) | ゲーム開始時に確定済みの事実 |

## 境界づけられたコンテキスト

本プロジェクトは単一の境界づけられたコンテキストで構成する。

```
[パズルゲームコンテキスト]
├── パラダイムシフトモデル  ← 中核ドメイン
├── 質問・回答モデル
└── ゲーム進行モデル
```

## ドメインモデルの設計方針

### 値オブジェクト (Value Object)

不変で、同値性で比較される。

- **Descriptor**: id + label で識別
- **Relation**: src + tgt + weight の組
- **Effect**: 質問回答による記述素変化のリスト

### エンティティ (Entity)

一意のIDで識別される。

- **Paradigm**: id で識別。D⁺, D⁻, Relations を持つ
- **Question**: id で識別。効果と正解を持つ
- **PuzzleData**: パズル全体を表す集約ルート

### ドメインサービス

エンティティに属さないドメインロジック。

- **GameEngine**: tension, alignment, update, assimilate 等の計算
  - 特定のエンティティに属さない、複数モデルにまたがる振る舞い

### 集約 (Aggregate)

- **PuzzleData** が集約ルート
  - 配下に Paradigm, Question, Descriptor を保持
  - パズルデータの整合性はこの集約内で保証する

## 命名規則

ドメイン用語をそのままコードに使う。略語や別名を使わない。

```swift
// Good: ドメイン用語をそのまま使う
struct Paradigm { ... }
func tension(o:paradigm:) -> Int
func alignment(h:paradigm:) -> Double
func assimilate(h:descriptor:paradigm:)

// Bad: 汎用的な名前や独自略語
struct Framework { ... }
func calcScore(...)
func propagate(...)
```

## ドメインイベント

状態遷移を明示的にモデル化する。

| イベント | 発生条件 |
|---------|---------|
| QuestionAnswered | プレイヤーが質問を選択 |
| ParadigmShifted | tension > threshold かつ別パラダイムの alignment が上回る |
| QuestionsOpened | 新規質問がオープン条件を満たす |
| PuzzleCleared | クリア質問が選択される |

## POCとの対応

POCの Python コードとドメイン用語を一致させる。

| POC (Python) | 製品 (Swift) | ドメイン概念 |
|-------------|-------------|------------|
| `Paradigm.d_plus` | `Paradigm.dPlus` | D⁺(P) |
| `Paradigm.d_minus` | `Paradigm.dMinus` | D⁻(P) |
| `Paradigm.relations` | `Paradigm.relations` | R(P) |
| `tension()` | `tension()` | 緊張 |
| `alignment()` | `alignment()` | 適合度 |
| `_assimilate_descriptor()` | `assimilateDescriptor()` | 同化 |
| `GameState.h` | `GameState.h` | 仮説状態 |
| `GameState.o` | `GameState.o` | 観測 |
| `GameState.r` | `GameState.r` | 不関与 |

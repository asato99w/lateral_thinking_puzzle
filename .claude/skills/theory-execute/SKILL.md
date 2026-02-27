---
name: theory-execute
description: 統合アルゴリズムの各Phaseを、4階層の参照ファイルを展開しながら確実に遂行する。sample-generateから呼ばれる。
argument-hint: [Phase番号またはStep番号]
disable-model-invocation: true
allowed-tools: Read, Write, Edit, Bash, Glob, Grep
---

# /theory-execute — アルゴリズム遂行

引数: `$ARGUMENTS`（開始位置の指定。省略時は Phase 1 から）
- 例: `/theory-execute Phase 2` — Phase 2 から開始
- 例: `/theory-execute Step 2-3` — Step 2-3 から開始

## 目的

統合アルゴリズムの各ステップを、4階層（統合アルゴリズム・統合ルール・個別アルゴリズム・個別ルール）を実際に展開しながら遂行する。「読め」ではなく「展開して目の前に置く」ことで手順の見落としを防ぐ。

## 遂行の原則

1. **各ステップの開始時に、参照すべきファイルを全て読む**。上位だけで判断しない
2. **各ステップの完了時に、完了チェックを実行する**。チェック項目はステップごとに定義される
3. **ステップの出力を次のステップの入力として明示的に受け渡す**。暗黙の引き継ぎをしない
4. **判断に迷った場合はユーザーに確認する**。独自に作戦レベルの判断を行わない

## Phase 別の遂行手順

以下は現行の統合アルゴリズムに基づく。アルゴリズムが更新された場合は、更新後の文書が優先される。

---

### Phase 1: 空間構築

#### 参照ファイル展開

Phase 1 の開始時に以下を全て読む:

| 階層 | ファイル |
|------|---------|
| 統合アルゴリズム | `integration/algorithms/統合アルゴリズム.md` — Phase 1 セクション |
| 統合ルール | `integration/rules/空間構築.md` |
| 個別アルゴリズム | `expansion/algorithms/E1.md`（または `E2.md`）、`paradigm/group/algorithms/A_深度階層型.md`、`paradigm/internal/algorithms/A_内部構造構成.md` |
| 個別ルール | `expansion/rules/展開規則一覧.md`、`paradigm/group/rules/近傍.md`、`paradigm/internal/rules/所属記述素の決定.md`、`paradigm/internal/rules/関係構造の構成.md`、`paradigm/internal/rules/コア記述素.md`、`paradigm/internal/rules/健全性条件.md` |

#### ステップ遂行

- **Step 1-1（記述素展開）**: E1/E2 を適用。出力: 記述素空間 F'
- **Step 1-2（パラダイム発見）**: A_深度階層型を適用。出力: パラダイム群（メインパス、サブパス）
- **Step 1-3（内部構造構成）**: A_内部構造構成を各パラダイムに適用。出力: 各 P_pred, R(P)（横辺のみ、ゲート辺は Phase 2 で追加）

#### Phase 1 完了チェック

- [ ] 全パラダイムの P_pred が構成されている
- [ ] 基準パス上で Explained 包含連鎖が成立している: Explained(P_1) ⊂ Explained(P_2) ⊂ ... ⊂ Explained(T)
- [ ] 各 P_pred の健全性条件（条件1〜5）を満たしている
- [ ] R(P) の横辺（Rule 1〜4）が構成されている
- [ ] **ゲート辺は未追加であること**を確認（Phase 2 で追加する）

---

### Phase 2: 質問構造設計

#### 参照ファイル展開

Phase 2 の開始時に以下を全て読む:

| 階層 | ファイル |
|------|---------|
| 統合アルゴリズム | `integration/algorithms/統合アルゴリズム.md` — Phase 2 セクション |
| 統合ルール | `integration/rules/質問構造設計.md` |
| 個別アルゴリズム | `question/algorithms/質問構造設計.md` |
| 個別ルール | `paradigm/internal/rules/関係構造の構成.md`（Rule 5: ゲート辺）、`question/rules/パラダイム駆動型.md` |

#### ステップ遂行

- **Step 2-1（アノマリー目標設定）**: 各パラダイムのアノマリー目標を設定。出力: 各 P のアノマリー記述素リスト
- **Step 2-2（認知的到達経路の逆算）**: アノマリーから逆算で到達経路を設計。出力: 各アノマリー質問への到達経路
- **Step 2-3（層構造への配置）**: 逆算結果を層に配置し、**ゲート辺を設計して R(P) に追加する**。出力: 層構造、更新された R(P)
- **Step 2-4（素材不足の検出）**: 不足があれば Phase 1 への差し戻し情報を記録。出力: 素材不足レポート（あれば）

#### Phase 2 完了チェック

- [ ] 各パラダイムにアノマリー目標が設定されている
- [ ] 認知的到達経路が逆算で設計されている（正方向ではない）
- [ ] 層構造が配置されている
- [ ] **ゲート辺が R(P) に追加されている**（Phase 1 の R(P) に書き戻し済み）
- [ ] 素材不足がある場合は Phase 1 への差し戻し情報が記録されている

---

### Phase 3: 質問生成

#### 参照ファイル展開

Phase 3 の開始時に以下を全て読む:

| 階層 | ファイル |
|------|---------|
| 統合アルゴリズム | `integration/algorithms/統合アルゴリズム.md` — Phase 3 セクション |
| 統合ルール | `integration/rules/質問生成.md` |
| 個別アルゴリズム | `question/algorithms/Q1_パラダイム構造準拠型.md`、`question/algorithms/Q2_内部構造活用型.md`、`question/algorithms/Q3_ユーザー向け質問分類.md` |
| 個別ルール | `question/rules/パラダイム駆動型.md`、`question/rules/記述素直接変換型.md`、`question/rules/緊張解消型.md`、`question/rules/大区分段階型.md`、`question/rules/フェーズ到達保証.md` |

#### ステップ遂行

- **Step 3-1（質問候補生成）**: Phase 2 の層配置を尊重して質問候補を生成。出力: 質問候補群
- **Step 3-2（認知的前提の設定）**: Phase 2 の逆算結果から prerequisites を導出。出力: 各質問の prerequisites
- **Step 3-3（役割付与・大区分配置）**: 役割と大区分を設定。出力: 役割・大区分付き質問群
- **Step 3-4（フェーズ到達の検証）**: フェーズ到達保証を検証。出力: 検証結果

#### Phase 3 完了チェック

- [ ] 質問群が Phase 2 の層構造と整合している
- [ ] 各質問に prerequisites が設定されている
- [ ] 各質問に役割と大区分が設定されている
- [ ] フェーズ到達保証が検証されている

---

### Phase 4: 検証と反復

#### 参照ファイル展開

Phase 4 の開始時に以下を全て読む:

| 階層 | ファイル |
|------|---------|
| 統合アルゴリズム | `integration/algorithms/統合アルゴリズム.md` — Phase 4 セクション |
| 統合ルール | `integration/rules/補完検証.md`、`integration/rules/多層構造検証.md`、`integration/rules/シフト方向検証.md`、`integration/rules/不足ルーティング.md` |
| 個別アルゴリズム | `supplementary/algorithms/S1.md` |
| 個別ルール | `supplementary/rules/発掘連鎖到達性.md` |
| メトリクス | `integration/evaluation/メトリクス.md` |

#### ステップ遂行

統合アルゴリズム Phase 4 の Step 4a〜4g に従う。検証は形式化（JSON 変換）後に検証スクリプトで実行する。

#### Phase 4 完了チェック

- [ ] 形式化が完了し JSON が生成されている
- [ ] 全検証スクリプトが実行されている
- [ ] NG がある場合、不足ルーティングに従い差し戻し先が特定されている
- [ ] 全検証 OK、または差し戻し情報がユーザーに報告されている

---

## sample-generate との連携

sample-generate の手順2（アルゴリズム適用）でこのスキルを使用する。

1. sample-generate がディレクトリ作成・状態判定を行う
2. `/theory-execute` が Phase ごとにファイルを展開し遂行する
3. 各 Phase の出力をサンプルファイルとして保存する
4. Phase 4 完了後、sample-generate が形式化・反復判定を行う

## フィードバック

遂行中に以下の問題が見つかった場合は記録し、ユーザーに報告する:

- **参照ファイルの不整合**: ステップが参照するファイルが存在しない、または内容が矛盾する
- **形式の不明確さ**: ステップの入出力や検証条件が曖昧で判断できない
- **チェック項目の不足**: 完了チェックでカバーされていない重要な確認事項がある

これらのフィードバックは `/theory-update` でアルゴリズム文書の形式改善に活用する。

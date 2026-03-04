---
name: v2-generate
description: v2統合アルゴリズムを適用し、パズルのサンプルデータを段階的に生成する。
argument-hint: [パズル名]
disable-model-invocation: true
allowed-tools: Read, Write, Edit, Bash, Glob, Grep
---

# /v2-generate — v2 サンプル生成

引数: `$ARGUMENTS`（パズル名）
- 例: `/v2-generate turtle_soup`

## 事前条件

- 問題文（S）と真相（T）が提示されていること

## 入力制約

- 入力は **理論（`theory_v2/`）と問題文（S, T）のみ**
- 既存のサンプルや JSON データを参考にしてはならない
- **読むことも禁止**。フォーマット確認等の理由であっても既存サンプルを開いてはならない。一度読むと全工程にわたりアンカリングが生じ、再生成の意味が失われるほど出力が類似する（実証済み）

## 手順

### 1. 準備

1. `app/poc_v2/samples/{puzzle}/` を確認し、次の連番を決定する
2. `{nn}_{YYYY-MM-DD}/` ディレクトリと `history/` を作成する

### 2. アルゴリズムの段階的適用

`theory_v2/integration/algorithms/統合アルゴリズム.md` を読み、記載された全 Phase に従い data_src.json を**段階的に**構築する。

各 Phase で:
1. アルゴリズムが指定する規則ファイル（`theory_v2/integration/rules/`）を読む
2. 規則に従い Phase を適用する
3. 結果を data_src.json に追加・更新する（データ形式は `app/poc_v2/src/models.py` に準拠）
4. `history/` にそのステップの実施記録を書く（ファイル名はアルゴリズムの Phase 番号と名称に従う）

### 3. エクスポート

`python3 app/poc_v2/eval/export_data.py` で data_src.json から data.json を生成する。

### 4. 検証

`python3 app/poc_v2/eval/run_all.py` で data_src.json を検証する。

## 参照ファイル

- `theory_v2/integration/algorithms/統合アルゴリズム.md` — アルゴリズム定義（Phase 構成・使用規則・出力形式を含む）
- `theory_v2/integration/rules/` — 各 Phase の規則
- `theory_v2/terms.md` — 用語定義
- `theory_v2/structure/汎用戦術.md` — 汎用戦術リスト
- `theory_v2/structure/仮説導出.md` — 仮説導出の不動点計算
- `app/poc_v2/src/models.py` — データ形式の定義元

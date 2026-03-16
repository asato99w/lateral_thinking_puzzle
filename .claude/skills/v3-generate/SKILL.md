---
name: v3-generate
description: v3統合アルゴリズムを適用し、パズルのサンプルデータを段階的に生成する。
argument-hint: [パズル名] [--algo v1|v2|v3|v4|v5]
allowed-tools: Read, Write, Edit, Bash, Glob, Grep
---

# /v3-generate — v3 サンプル生成

引数: `$ARGUMENTS`（パズル名 + オプション）
- 例: `/v3-generate desert_man`（デフォルト: v5 アルゴリズム）
- 例: `/v3-generate turtle_soup --algo v4`

## アルゴリズム選択

`--algo` オプションでアルゴリズムバージョンを指定する。

| オプション | アルゴリズムファイル |
|-----------|-------------------|
| `--algo v1` | `theory_v3/integration/algorithms/統合アルゴリズム.md` |
| `--algo v2` | `theory_v3/integration/algorithms/統合アルゴリズムv2.md` |
| `--algo v3` | `theory_v3/integration/algorithms/統合アルゴリズムv3.md` |
| `--algo v4` | `theory_v3/integration/algorithms/統合アルゴリズムv4.md` |
| `--algo v5`（デフォルト） | `theory_v3/integration/algorithms/統合アルゴリズムv5.md` |

各 Phase で使用する規則ファイルは、選択されたアルゴリズムファイル内の記載に従う。

## パズルの特定

`quizzes/` から該当パズルを特定し、S（問題）と T（正解）を取得する。

- パス: `quizzes/{nnn}_{パズル名}.md`
- `## 問題` → S
- `## 正解` → T

## 入力制約

- 入力は **理論（`theory_v3/`）と問題文（S, T）のみ**
- 既存のサンプルや JSON データを参考にしてはならない
- **読むことも禁止**。フォーマット確認等の理由であっても既存サンプルを開いてはならない。一度読むと全工程にわたりアンカリングが生じ、再生成の意味が失われるほど出力が類似する（実証済み）

## 手順

### 1. 準備

1. `$ARGUMENTS` から `--algo` オプションを解析する（なければ v4）
2. `app/poc_v3/samples/{puzzle}/` を確認し、次の連番を決定する
3. `{nn}_{YYYY-MM-DD}/` ディレクトリと `history/` を作成する

### 2. アルゴリズムの段階的適用

選択されたアルゴリズムファイルを読み、記載された全 Phase に従い data_src.json を**段階的に**構築する。

各 Phase で:
1. アルゴリズムが指定する規則ファイル（`theory_v3/integration/rules/`）を読む
2. 規則に従い Phase を適用する
3. 結果を data_src.json に追加・更新する（データ形式は `app/poc_v3/src/models.py` に準拠）
4. `history/` にそのステップの実施記録を書く（ファイル名はアルゴリズムの Phase 番号と名称に従う）

### 3. エクスポート

`python3 app/poc_v3/eval/export_data.py` で data_src.json から data.json を生成する。

### 4. 検証

`python3 app/poc_v3/eval/run_all.py` で data_src.json を検証する。

## 参照ファイル

- `theory_v3/integration/algorithms/` — アルゴリズム定義（選択されたもの）
- `theory_v3/integration/rules/` — 各 Phase の規則（アルゴリズムが指定するもの）
- `theory_v3/integration/precedents/` — 判例集
- `theory_v3/terms.md` — 用語定義
- `theory_v3/structure/汎用戦術.md` — 汎用戦術リスト
- `theory_v3/structure/仮説導出.md` — 仮説導出の不動点計算
- `app/poc_v3/src/models.py` — データ形式の定義元

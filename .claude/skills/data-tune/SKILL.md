---
name: data-tune
description: 検証スクリプトの結果に基づきJSONデータを直接調律する反復改善スキル
argument-hint: [JSONデータパス] [アルゴリズムパス]
disable-model-invocation: true
allowed-tools: Read, Write, Edit, Bash, Glob, Grep
---

# /data-tune — データ調律

引数: `$ARGUMENTS`（JSON データのパスとアルゴリズムのパス）
- 例: `/data-tune app/poc/data/forbidden_basement.json theory/integration/algorithms/データ調律アルゴリズム.md`
- `$0` = JSON データパス、`$1` = アルゴリズムパス
- アルゴリズムが指定されていない場合、ユーザーに確認する

## 事前条件

- Phase A（サンプル生成 → JSON 変換 → 初回検証）が完了していること
- 対象 JSON データが `app/poc/data/` に存在すること

## 手順

指定されたアルゴリズムの手順に従って実行する。以下はアルゴリズムの各 Step に対応するスキル側の実行指針。

### 1. 全検証の実行（Step 1）

`app/poc/scripts/eval/` 配下の全スクリプトを `$0` に対して実行し、結果サマリを表示する。

- `check/` 配下: L2 検証（OK/NG 判定）
- `metric/` 配下: L3 品質メトリクス（定量報告）
- 実行はすべて `app/poc/scripts/` をカレントディレクトリとして行う

全 L2 が OK の場合、調律完了を報告して終了する。

### 2. 診断（Step 2）

アルゴリズムの対応表と優先順位に従い、NG の根本原因を特定する。

診断には**アルゴリズム不備の検討**を含む。NG の原因がアルゴリズムの修正分類では対処できない場合、その旨を履歴に記録しユーザーに報告して終了する。

### 3. 修正・再検証・記録（Step 3〜6）

アルゴリズムの Step 3〜6 に従い、修正計画の策定・JSON 編集・再検証・履歴記録を実行する。

- 履歴記録先: `samples/{puzzle}/{iteration}/history/NNNN_YYYYMMDD.md`
- 形式: アルゴリズムの履歴記録テンプレートに従う

### 4. 継続判定（Step 7）

- **全 L2 OK** → 完了を報告
- **NG 残存** → 手順2に戻る

## 参照ファイル

- 指定されたアルゴリズム — 手順の定義元
- `theory/integration/evaluation/メトリクス.md` — メトリクス定義
- `app/poc/src/models.py` — データ構造
- `app/poc/scripts/eval/` — 検証スクリプト群（実行対象）

## 制約

- **アルゴリズム厳守**: アルゴリズムに規定された手順のみを実行する。アルゴリズム外の行動は一切行わない
- **変更不可**: `app/poc/src/`、`app/poc/scripts/eval/`、`theory/`
- **変更対象**: `app/poc/data/` 配下の JSON データのみ
- 検証スクリプト・エンジン・理論は基本的に正しい前提で運用する。矛盾・不備が見つかった場合は報告して停止する

---
name: sample-import
description: 形式化済みサンプルからJSONを生成し、app/poc/data/に配置した上で全検証スクリプトを実行する。
argument-hint: [サンプル反復ディレクトリパス]
disable-model-invocation: true
allowed-tools: Read, Bash, Glob, Grep
---

# /sample-import — データ取り込み

引数: `$ARGUMENTS`（対象サンプルの反復ディレクトリパス）
- 例: `/sample-import samples/ja/005_禁じられた地下室/01_20260227_統合アルゴリズム適用`
- 例: `/sample-import samples/en/001_turtle_soup/01_20260301_統合アルゴリズム適用`

## 事前条件

- 対象反復ディレクトリに形式化ファイルが存在すること

## 手順

### 1. 言語の判定

パスから言語コードを判定する（`samples/{lang}/...` の `{lang}` 部分）。

### 2. 形式化ファイルの確認

`$ARGUMENTS` ディレクトリ内の形式化ファイルの存在を確認し、`app/poc/src/models.py` のデータ構造が要求する全フィールドが揃っているか検証する。

### 3. JSON 変換

形式化ファイルの内容を `app/poc/data/` 配下の JSON ファイルに変換する。

- 変換スクリプト: `.claude/skills/sample-import/scripts/convert_formalization.py`
- 出力先: `app/poc/data/{パズル名}.json`

### 4. 製品データへのコピー

生成した JSON を製品アプリの対応ロケールディレクトリにもコピーする。

- 出力先: `app/product/LateralThinkingPuzzle/LateralThinkingPuzzle/Resources/Puzzles/{lang}/{パズル名}.json`

### 5. 検証スクリプト実行

`app/poc/scripts/eval/` 配下の全スクリプトを実行する。`check/` は OK/NG 判定、`metric/` は定量報告。実行はすべて `app/poc/scripts/` をカレントディレクトリとして行う。

### 6. 結果サマリの報告

各スクリプトの実行結果をまとめて報告する。NG がある場合は要修正箇所と差し戻し先を提示する。

## 参照ファイル

- `app/poc/src/models.py` — データ構造の定義元
- `app/poc/scripts/eval/` — 検証スクリプト群（実行時にスキャン）

## 注意事項

- 検証 NG の場合、データを `app/poc/data/` に残すかどうかをユーザーに確認する

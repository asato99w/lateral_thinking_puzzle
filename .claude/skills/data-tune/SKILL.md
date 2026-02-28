---
name: data-tune
description: 検証スクリプトの結果に基づきJSONデータを直接調律する反復改善スキル
argument-hint: [JSONデータパス]
disable-model-invocation: true
allowed-tools: Read, Write, Edit, Bash, Glob, Grep
---

# /data-tune — データ調律

引数: `$ARGUMENTS`（対象 JSON データのパス）
- 例: `/data-tune app/poc/data/forbidden_basement.json`

## 事前条件

- Phase A（サンプル生成 → JSON 変換 → 初回検証）が完了していること
- 対象 JSON データが `app/poc/data/` に存在すること

## 手順

### 1. 全検証の実行

`app/poc/scripts/eval/` 配下の全スクリプトを `$ARGUMENTS` に対して実行し、結果サマリを表示する。

- `check/` 配下: L2 検証（OK/NG 判定）
- `metric/` 配下: L3 品質メトリクス（定量報告）
- 実行はすべて `app/poc/scripts/` をカレントディレクトリとして行う

全 L2 が OK の場合、調律完了を報告して終了する。

### 2. NG の診断

アルゴリズムの対応表と優先順位（L2-0 > L2-1 > L2-4 > L2-5）に従い、NG の根本原因を特定する。

L2-5 が NG の場合は、L3-6（前提閉包性）と L3-7（層間連鎖性）の結果を確認し、不足記述素を特定する。

### 3. 修正計画の提示

診断結果に基づく修正計画をユーザーに提示する。以下を含む:
- 修正対象の JSON フィールド
- 修正内容と根拠
- 修正分類（パラダイム構造 / 質問効果 / 所属・前提 / 初期設定）
- 想定される影響範囲

**ユーザーの承認を得てから次に進む。**

### 4. JSON 編集と再検証

承認された修正計画に基づき JSON データを編集し、全検証スクリプトを再実行する。

- 対象検証の改善を確認する
- 回帰チェック: 修正前に OK だった検証が NG に変わっていないこと
- 結果に応じて継続（手順2へ戻る）または完了

### 5. 履歴の記録

各ラウンドの記録を対象パズルの反復ディレクトリ内 `history/` に追記する。

- 記録先: `samples/{puzzle}/{iteration}/history/NNNN_YYYYMMDD.md`
- 形式: アルゴリズムの履歴記録テンプレートに従う

## 参照ファイル

- `theory/integration/algorithms/データ調律アルゴリズム.md` — 手順の定義元
- `theory/integration/evaluation/メトリクス.md` — メトリクス定義
- `app/poc/src/models.py` — データ構造
- `app/poc/scripts/eval/` — 検証スクリプト群（実行対象）

## 制約

- **変更不可**: `app/poc/src/`、`app/poc/scripts/eval/`、`theory/`
- **変更対象**: `app/poc/data/` 配下の JSON データのみ
- 各修正はユーザー承認後に実行する
- 検証スクリプトとエンジンは正しい前提で運用する

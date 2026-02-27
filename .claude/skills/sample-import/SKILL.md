# /sample-import — データ取り込み

## 概要

形式化済みサンプルから JSON を生成し、`app/poc/data/` に配置した上で全検証スクリプトを実行する。

## 引数

- `$ARGUMENTS`: 対象サンプルのパス（例: `samples/001_ウミガメのスープ/09_20260219_統合アルゴリズム適用`）

## 事前条件

- 対象反復ディレクトリに形式化ファイルが存在すること

## 手順

### 1. 形式化ファイルの確認

形式化ファイルの存在を確認し、`app/poc/src/models.py` のデータ構造が要求する全フィールドが揃っているか検証する。

### 2. JSON 変換

形式化ファイルの内容を `app/poc/data/` 配下の JSON ファイルに変換する。

- 変換スクリプト: `app/poc/scripts/convert_formalization.py`（存在する場合）
- 出力先: `app/poc/data/{パズル名}.json`

### 3. 検証スクリプト実行

以下の検証スクリプトを全て実行する:

#### check（OK/NG 判定）

| スクリプト | 検証内容 | Phase 4 対応 |
|-----------|---------|-------------|
| `eval/check/completeness.py` | 完全性検証 | Step 4a |
| `eval/check/layer_structure.py` | 多層構造検証 | Step 4c |
| `eval/check/reachability.py` | 到達パス検証 | Step 4e |
| `eval/check/reachability_sim.py` | 到達パスシミュレーション | Step 4e |
| `eval/check/assimilation_connectivity.py` | 同化接続性（保留中） | Step 4b |
| `eval/check/excavation_chain.py` | 発掘連鎖（保留中） | Step 4b |

#### metric（定量報告）

| スクリプト | 検証内容 | Phase 4 対応 |
|-----------|---------|-------------|
| `eval/metric/shift/transition_drive.py` | シフト方向・駆動率 | Step 4d |
| `eval/metric/structure/prerequisite_closure.py` | 前提閉包性（L3-6） | Step 4f |
| `eval/metric/structure/layer_connectivity.py` | 層間連鎖性（L3-7） | Step 4f |
| `eval/metric/structure/qp_report.py` | Q(P) 構造レポート | 補助 |

実行はすべて `app/poc/scripts/` をカレントディレクトリとして行う。

### 4. 結果サマリの報告

全スクリプトの実行結果を以下の形式で報告する:

```
## インポート結果: {パズル名}

### JSON 変換
- 出力先: app/poc/data/{ファイル名}.json
- ステータス: OK / NG

### 検証結果

| 検証 | 結果 | 備考 |
|------|------|------|
| 完全性 (4a) | OK/NG | ... |
| 多層構造 (4c) | OK/NG | ... |
| シフト方向 (4d) | スコア: X.XX | ... |
| 到達パス (4e) | OK/NG | ... |
| 前提閉包性 (4f/L3-6) | 不足: N件 | ... |
| 層間連鎖性 (4f/L3-7) | 不足: N件 | ... |

### 総合判定
- OK: 全検証通過
- NG: 要修正箇所の特定と差し戻し先の提示
```

## 参照ファイル

- `app/poc/src/models.py` — データ構造の定義元
- `app/poc/scripts/eval/` — 検証スクリプト群
- `theory/integration/algorithms/統合アルゴリズム.md` — Phase 4 の検証定義

## 注意事項

- 検証 NG の場合、データを `app/poc/data/` に残すかどうかをユーザーに確認する
- Step 4b（同化接続性・発掘連鎖）は適用保留中だが、スクリプトが存在する場合は参考情報として実行する

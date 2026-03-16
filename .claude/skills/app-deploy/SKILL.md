---
name: app-deploy
description: v3サンプルデータをアプリに配置し、カタログとの整合性を検証する。
argument-hint: [パズル名] [イテレーションパス]
allowed-tools: Read, Write, Edit, Bash, Glob, Grep
---

# /app-deploy — アプリ配置

引数: `$ARGUMENTS`（パズル名、またはイテレーションディレクトリのパス）
- 例: `/app-deploy poison_mushroom`（最新イテレーションを自動検出）
- 例: `/app-deploy app/poc_v3/samples/poison_mushroom/02_2026-03-16`（パス直接指定）

## パス解決

### パズル名が指定された場合

1. `app/poc_v3/samples/{パズル名}/` 内の最新イテレーション（連番最大）を特定
2. そのイテレーションの `data.json` を使用

### パスが指定された場合

1. 指定パス内の `data.json` を使用

## アプリ内のパズル名マッピング

サンプルディレクトリ名とアプリ内ファイル名が異なる場合がある。

| サンプル名 | アプリ内ファイル名 |
|-----------|------------------|
| poison_mushroom | poisonous_mushroom.json |
| turtle_soup | turtle_soup.json |
| bar_man | bar_man.json |
| desert_man | desert_man.json |
| forbidden_basement | forbidden_basement.json |

マッピングは `app/product/LateralThinkingPuzzle/LateralThinkingPuzzle/Resources/Puzzles/ja/` 内のファイル名に従う。不明な場合は既存ファイルから推定する。

## 手順

### 1. 検証

配置前に以下を実行し、ALL PASS を確認する。FAIL の場合は配置しない。

```
python3 app/poc_v3/eval/run_all.py {イテレーションパス}/data_src.json
```

### 2. エクスポート

data_src.json から data.json を生成する（既に存在する場合も再生成して最新にする）。

```
python3 app/poc_v3/eval/export_data.py {イテレーションパス}/data_src.json
```

### 3. 配置

以下の 2 箇所に data.json をコピーする:

1. **iOSアプリリソース**: `app/product/LateralThinkingPuzzle/LateralThinkingPuzzle/Resources/Puzzles/ja/{アプリ内ファイル名}`
2. **POCデータ**: `app/poc_v3/data/{パズル名}.json`

### 4. カタログ整合性

`app/product/LateralThinkingPuzzle/LateralThinkingPuzzle/Resources/catalog.json` を確認する:

1. パズルがカタログに存在すること
2. `engine_version` がデータ形式と一致すること:
   - `propositions` キーを持つ → `"v3"`
   - `descriptors` キーのみ + `formation_conditions` あり → `"v2"`
   - それ以外 → `"v1"`
3. 不一致があれば修正する

### 5. 可視化

```
python3 app/poc_v3/eval/visualize.py {イテレーションパス}/data_src.json
```

### 6. 結果報告

- 配置先パス
- カタログの engine_version（変更があれば変更前→変更後）
- data.json の命題数・質問数

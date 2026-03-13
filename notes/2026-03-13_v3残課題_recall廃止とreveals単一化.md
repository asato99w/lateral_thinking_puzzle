# v3 残課題: recall 廃止と reveals 単一化

## 1. recall_conditions の除去

### 現状

- **エンジン (engine.py)**: `_derive_recall_conditions()` で reveals 先命題の formation_conditions から動的導出。Question モデルに recall_conditions フィールドなし → **廃止済み**
- **データ (data_src.json, data.json)**: 全質問に `recall_conditions` フィールドが残存 → **未廃止**
- **eval スクリプト**: 「recall_conditions があれば使用、なければ fc から導出」の互換コード → **中途半端**
- **アルゴリズム文書 (theory_v3/)**: `recall_conditions` を概念として多用（recall = fc 原則の記述が多数）

### 対応方針

- data_src.json / data.json から `recall_conditions` フィールドを除去する
- eval スクリプトの互換分岐を削除し、一律 reveals 先の fc を参照するように統一する
- export_data.py で recall_conditions を除去する処理は不要（データ側で消えるため）
- アルゴリズム文書の記述を整理する（recall_conditions という用語自体を減らし、「想起条件は reveals 先の fc から導出」という記述に統一）

## 2. reveals の単一化 (list → str)

### 現状

- **models.py**: `reveals: list[str]` — リスト型
- **engine.py**: `reveals[0]` で先頭1個のみ使用（recall 導出）、`for prop_id in question.reveals` でループ（回答処理）— 混在
- **eval スクリプト**: `_get_reveals()` ヘルパーがリスト前提。ただし `reveals[0]` のみ参照する箇所あり。コメントに「v3 では 1 質問 1 主命題が基本」
- **データ**: 全質問が `["N1a"]` のような単一要素リスト
- **アルゴリズム**: 1質問1命題が設計原則として確立

### 対応方針

- models.py: `reveals: list[str]` → `reveals: str`
- engine.py: `reveals[0]` → `reveals`、`for prop_id in question.reveals` → 単一参照に変更
- データ: `"reveals": ["N1a"]` → `"reveals": "N1a"`
- eval スクリプト: `_get_reveals()` ヘルパーを廃止し、直接 `q["reveals"]` を参照
- アルゴリズム文書: reveals の記述を単一値として統一

## 影響範囲

- `app/poc_v3/src/models.py`
- `app/poc_v3/src/engine.py`
- `app/poc_v3/eval/check_*.py` (4ファイル)
- `app/poc_v3/eval/visualize.py`
- `app/poc_v3/samples/*/data_src.json` (全サンプル)
- `theory_v3/integration/algorithms/統合アルゴリズムv3.md`
- `theory_v3/integration/rules/*.md` (複数)

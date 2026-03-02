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

## ディレクトリ構成

```
app/poc_v2/samples/{puzzle}/
└── {nn}_{YYYY-MM-DD}/
    ├── data.json
    └── history/
        ├── 01_逆算連鎖.md
        ├── 02_ピース抽出.md
        ├── ...
```

- `nn` は連番（同一パズルの反復）
- `YYYY-MM-DD` は実施日
- `data.json` はアルゴリズムの各ステップに従って段階的に構築される
- `history/` は各ステップの実施記録（追記専用）

## 手順

### 1. 状態の判定

`app/poc_v2/samples/{puzzle}/` を確認し、次の連番を決定する。ディレクトリを作成する。

### 2. アルゴリズムの段階的適用

`theory_v2/統合アルゴリズム.md` の Phase 1〜7 に従い、data.json を **段階的に** 構築する。

各ステップで:
1. アルゴリズムの該当 Phase を適用する
2. 結果を data.json に追加・更新する（形式は `app/poc_v2/src/models.py` に準拠）
3. history/ にそのステップの実施記録を書く

ステップの粒度はアルゴリズムの Phase に概ね対応する。準備段階の記録を含めてもよい。

## 参照ファイル

- `theory_v2/統合アルゴリズム.md` — Phase 定義
- `theory_v2/terms.md` — 用語定義
- `theory_v2/structure/汎用戦略.md` — 汎用戦略リスト
- `app/poc_v2/src/models.py` — データ形式の定義元

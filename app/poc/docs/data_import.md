# POC データ取り込み手順

## 概要

samples/ ディレクトリで生成された分析結果を、POC が読み込む JSON データに変換する手順。

## JSON スキーマ

```json
{
  "title": "string",
  "statement": "string",
  "init_paradigm": "string",
  "ps_values": [["Ps-1", 1], ...],
  "all_descriptor_ids": ["string", ...],
  "paradigms": [
    {
      "id": "string",
      "name": "string",
      "d_plus": ["string", ...],
      "d_minus": ["string", ...],
      "relations": [["string", "string", 0.9], ...]
    }
  ],
  "questions": [
    {
      "id": "string",
      "text": "string",
      "ans_yes": [["string", 1], ...],
      "ans_no": [["string", 0], ...],
      "ans_irrelevant": ["string", ...],
      "correct_answer": "yes" | "no" | "irrelevant",
      "is_clear": false
    }
  ]
}
```

## フィールドの対応

### title, statement

quizzes/NNN_タイトル.md の「問題」セクションから取得する。

### init_paradigm

パラダイム発見の出力における初期パラダイム ID。通常は "P1"。

### ps_values

記述素空間の Ps 一覧から生成する。全て値 1（Ps は問題文として与えられた事実であり、全て真）。

```
Ps-1 〜 Ps-N → [["Ps-1", 1], ["Ps-2", 1], ..., ["Ps-N", 1]]
```

### all_descriptor_ids

記述素空間の全記述素 ID を列挙する。サンプルテンプレートの記述素一覧セクションから直接取得できる。

対象: Ps, Fs（単一記述素規則 + 異常性検出 + 緊張関係）, Pt, Ft（単一記述素規則 + Ft 用規則）, D（合成）

### paradigms

パラダイム発見の出力から、各パラダイムについて以下を定義する。

#### id, name

パラダイム発見で付与された ID と名称をそのまま使用する。

#### d_plus（真と予測する記述素）

そのパラダイムが「このように世界を理解している」ときに真であると予測する記述素の ID 群。サンプルテンプレートの形式化セクションから取得する。

例: P1「日常的な食事体験」の d_plus は、Ps の記述素と、P1 の枠組みで整合する Fs 記述素。

#### d_minus（偽と予測する記述素）

そのパラダイムの枠組みで偽であると予測する記述素の ID 群。

例: P1 では「料理の専門家である」(Fs-24 的な仮説) は偽と予測される。

#### relations（同化辺）

パラダイム内で、ある記述素が確定したとき別の記述素の確率を更新する関係。形式: `[src, tgt, weight]`。

- src: 確定した記述素 ID
- tgt: 影響を受ける記述素 ID
- weight: 伝播の強さ（0.0〜1.0、通常 0.9）

サンプルテンプレートの形式化セクションで定義する。

### questions

質問生成の出力から、各質問について以下を定義する。

#### id, text, correct_answer

質問生成の出力テーブルからそのまま取得する。correct_answer は正答列の値を変換する。

```
はい → "yes"
いいえ → "no"
関係ない → "irrelevant"
```

#### ans_yes, ans_no, ans_irrelevant

サンプルテンプレートの ans 定義セクションから取得する。

多くの質問では既定パターンが適用される:

```
対象記述素が d のとき:
  ans_yes = [[d, 1]]
  ans_no = [[d, 0]]
  ans_irrelevant = [d]
```

対象記述素が複数（d1, d2）のとき:

```
  ans_yes = [[d1, 1], [d2, 1]]
  ans_no = [[d1, 0]]          ← 直接対応のみ
  ans_irrelevant = [d1]
```

含意対応がある質問は既定パターンの例外として個別に定義する。

#### is_clear

クリア質問（この質問に「はい」と回答するとゲームクリアとなる質問）かどうか。サンプルテンプレートで指定する。通常、T の核心に到達する質問（例: 「人肉を食べていたと悟ったか」）が該当する。

## 変換の流れ

```
quizzes/NNN_*.md
  → title, statement

samples/NNN_*/01_入力.md
  → （quizzes と同一内容、変換には不使用）

samples/NNN_*/02_記述素展開.md
  → ps_values, all_descriptor_ids

samples/NNN_*/03_パラダイム発見.md
  → init_paradigm
  → paradigms[].id, .name

samples/NNN_*/04_質問生成.md
  → questions[].id, .text, .correct_answer

samples/NNN_*/05_形式化.md
  → paradigms[].d_plus, .d_minus, .relations
  → questions[].ans_yes, .ans_no, .ans_irrelevant, .is_clear
```

## 配置

生成した JSON は `app/poc/data/` に配置する。ファイル名はスネークケースで題材名を使用する。

```
app/poc/data/turtle_soup.json
app/poc/data/another_puzzle.json
```

# 実装計画

## 目的

理論定義（H, effect, open(H), consistency 等）がプログラムとして動作するか検証する。

## ファイル構成

```
app/poc/
  src/
    models.py    # データ構造
    engine.py    # ゲームロジック
    main.py      # エントリポイント・ゲームループ（CLI）
  data/
    turtle_soup.json  # ウミガメのスープのクイズデータ
  docs/
    ...
```

## Step 1: データ構造の定義（models.py）

### Descriptor
- id: str
- label: str

### Paradigm
- id: str
- d_plus: set[str] — D⁺(P) の記述素 ID 群
- d_minus: set[str] — D⁻(P) の記述素 ID 群
- relations: list[tuple[str, str, float]] — R(P) の辺 (d₁, d₂, w)

### Question
- id: str
- text: str
- ans_yes: list[tuple[str, int]] — ans(q, はい)
- ans_no: list[tuple[str, int]] — ans(q, いいえ)
- ans_irrelevant: list[str] — ans(q, 関係ない)
- correct_answer: str — a_T(q)（"yes" / "no" / "irrelevant"）
- is_clear: bool — クリア質問かどうか

### GameState
- h: dict[str, float] — 各記述素 ID → 確率値 [0, 1]
- o: dict[str, int] — 確定記述素 ID → 値（0 or 1）
- r: set[str] — 不関与記述素 ID 群
- p_current: str — 現在のパラダイム ID
- answered: set[str] — 回答済み質問 ID 群

## Step 2: クイズデータの作成（turtle_soup.json）

既存のサンプル分析を元に作成する。

- 記述素一覧（Fs, Ft）
- パラダイム定義（D⁺, D⁻, R(P)）
- 質問定義（ans, a_T(q), クリアフラグ）
- 初期パラダイム ID
- Ps の記述素と値

## Step 3: ゲームロジックの実装（engine.py）

### effect(q) の算出
- question.correct_answer に基づいて ans の該当分岐を返す

### init_questions(paradigms, questions) → list[Question]
- P_init の D(P_init) に基づいて初期質問群を決定
- { q | ∃(d, v) ∈ effect(q) : d ∈ D(P_init) ∧ P_init(d) = v }

### update(state, question) → GameState
1. 直接更新: effect(q) を O に適用、H(d) = v
2. 同化: R(P_current) を通じて整合する情報を伝播
3. パラダイムシフト判定: consistency(O, P) の算出、閾値比較
4. open(H) 再計算: 新規オープン質問の特定

### consistency(o, paradigm) → float
- |{d ∈ D(P) ∩ O | P(d) = O(d)}| / |D(P) ∩ O|

### open_questions(state, questions) → list[Question]
- { q | ∃(d, v) ∈ effect(q) : H(d) ≈ v }
- 回答済み質問を除外

### check_clear(question) → bool
- question.is_clear かどうか

## Step 4: ゲームループの実装（main.py）

1. クイズデータを読み込む
2. GameState を初期化（H, O = Ps, P_current = P_init）
3. 初期質問群を算出・表示
4. ループ:
   a. プレイヤーが質問を選択（CLI 入力）
   b. 回答を表示
   c. update を実行
   d. クリア判定
   e. 新規オープン質問を表示
5. クリアでゲーム終了

## 実装順序

1. models.py — データ構造
2. data/turtle_soup.json — クイズデータ
3. engine.py — ロジック
4. main.py — ゲームループ

データ構造とクイズデータを先に固めることで、ロジックの検証がしやすくなる。

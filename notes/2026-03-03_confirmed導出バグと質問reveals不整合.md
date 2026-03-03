# confirmed 導出バグと質問 reveals 不整合

## 1. エンジンバグ: 仮説が confirmed に混入（修正済み）

### 問題

`engine.py` の `evaluate_derivations()` が formation_conditions による導出結果を `state.confirmed` に書き込んでいた。
`check_complete()` は `state.confirmed` で判定するため、仮説だけでクリア条件が満たされてしまう。

理論 v2 の定義（`theory_v2/terms.md`）では:
- confirmed: 質問の回答（観測）によってのみ拡張される
- derived: confirmed から formation_conditions の不動点計算で導出される従属データ
- ゲームサイクル: `f(confirmed) → derived` と `g(question, answer) → confirmed` の2関数。confirmed を更新するのは g のみ

### 修正内容

- `models.py`: `GameState` に `derived` フィールドと `known` プロパティ（confirmed ∪ derived）を追加
- `engine.py`: `evaluate_derivations()` が `state.confirmed` を変更せず `state.derived` に格納するよう修正
- `engine.py`: `_check_conditions()`（想起条件）と `answer_question()`（ピース判定）は `state.known` を使用
- `engine.py`: `check_complete()`（クリア判定）は `state.confirmed` のみ使用（変更なし・正しい）
- `main.py`: 表示ロジックを `state.derived` に対応
- `eval/find_min_questions.py`: confirmed と derived を分離するよう書き直し

### 結果

- 修正前: 最小質問数 7（仮説でクリア可能 → 不正）
- 修正後: 最小質問数 9（観測でのクリアが必要）

## 2. 質問テキストと reveals の不整合（未修正）

エンジンバグとは別に、質問の設計自体に問題がある。

### Q-15 の問題

- **質問**: 「男はあのスープの正体に気づきましたか？」→ Yes
- **reveals**: D-13「あの時のスープが仲間の人肉だったと悟った」

「気づいたか？」→「Yes」という回答からは、**何に**気づいたのかはプレイヤーに伝わらない。
にもかかわらず、reveals として「仲間の人肉だったと悟った」という核心的事実がオープンされる。
質問の回答から論理的に導けない情報が reveals に設定されている。

### 根本原因

Q-15 の質問テキスト「スープの正体に気づきましたか？」は曖昧で、Yes の回答から「何に気づいたか」が特定できない。にもかかわらず reveals が D-13「仲間の人肉だったと悟った」という具体的事実になっている。質問の回答から論理的に導けない情報が reveals されている。

なお Q-16「男は真実を知ったことで絶望し、自殺しましたか？」→ D-14 は、プレイヤーが仮説を質問として述べ Yes で確認する正常な流れであり、問題はない。

### 未解決の論点

- 質問テキストが曖昧な場合、reveals に具体的事実を設定することの妥当性
- Phase 5 の質問生成ルールに、質問テキストと reveals の論理的整合性チェックを追加すべきか

## 3. Phase 3 仮説連鎖の formation_conditions 設定誤り（未修正）

### 問題

Phase 3（仮説連鎖）が formation_conditions の設定対象を誤っている。

- **設定すべき対象**: トリガー記述素（ピースのアクセス条件）
- **実際に設定された対象**: ピースメンバー（D-10〜D-14）

### 現状

トリガー記述素の formation_conditions 設定状況:

| ID | ラベル | 所属 | formation_conditions |
|----|--------|------|---------------------|
| D-15 | 船乗りだった | P-shipwreck trigger | なし |
| D-16 | 過去に危機的な体験 | P-shipwreck trigger | なし |
| D-17 | 仲間がいた | P-shipwreck trigger | なし |
| D-21 | 過去に欺かれた | P-deception trigger | なし |
| D-22 | 過去にスープを飲んだ | P-deception trigger | [[D-3]] ✓ |

D-22 以外のトリガーには formation_conditions が設定されていない。

一方、P-realization のメンバー（D-10〜D-14）には全て formation_conditions が設定され、トリガー成立時に連鎖的に全メンバーが自動導出される構造になっている。

### 正しいアルゴリズム

ピースメンバーへの到達は Phase 4（戦術連鎖）で定義されている。戦術連鎖は P-realization の内部連鎖を正しく構成しており、各メンバーは質問を通じて発見される設計になっている。Phase 3 がメンバーに formation_conditions を設定したことで、質問による発見を経ずに自動導出される経路が生じた。

### 影響

Phase 3 と Phase 4 が同じ記述素に対して二重の到達経路を設定:
- Phase 3: formation_conditions → 自動導出（仮説）
- Phase 4: 戦術連鎖 → 質問生成 → 観測（事実）

Phase 3 の設定は不要であり、削除すべき対象。

# UXデザインガイドライン

## デザイントーン

| 項目 | 方針 |
|------|------|
| トーン | ダークモード強制。黒背景 + インディゴアクセント |
| 密度 | バランス型。余白と情報量の中間 |
| 演出 | 控えめ。軽いフィードバックとトランジション |
| ベース | iOS ネイティブコンポーネントを活かしつつ、細部の質を上げる |

## カラー定義

定数は `Presentation/Theme.swift` に集約。

- **背景**: 強制ダークモード（`.preferredColorScheme(.dark)`）
- **カード背景**: `Color(white: 0.14)` — 黒背景に対して微かに浮く
- **カードボーダー**: `Color.indigo.opacity(0.4)` — 1pt
- **アクセント**: インディゴ（`Color.indigo`）。縦線・進捗カウンター・絵文字背景・カードボーダーに統一使用
- **絵文字エリア背景**: `Color.indigo.opacity(0.2)` — カード内で区別可能な濃さ
- **テキスト**: primary（白）/ `.white.opacity(0.5)`（プレビュー文）/ `.white.opacity(0.4)`（補助ラベル）
- **回答色**: YES=グリーン、NO=レッド、関係ない=グレー
- **難易度星**: filled=イエロー、empty=`Color.gray.opacity(0.4)`
- **Solved バッジ**: グリーン
- **進捗カウンター**: 数字=インディゴ、テキスト=`.white.opacity(0.7)`、背景=`indigo.opacity(0.12)`

## タイポグラフィ

| 用途 | スタイル |
|------|---------|
| トップ アプリ名 | `.system(size: 34, weight: .bold)` |
| トップ サブタイトル | `.subheadline` + `.secondary` |
| 進捗カウンター 数字 | `.title3.bold().monospacedDigit()` |
| 進捗カウンター テキスト | `.subheadline.monospacedDigit()` |
| セクション見出し | `.headline` + `.white.opacity(0.85)` |
| パズルタイトル | `.headline` |
| プレビュー文 | `.caption` + `.white.opacity(0.5)` 2行制限 |
| 難易度ラベル | `.caption2` + `.white.opacity(0.4)` |
| 本文 | `.body` |

## 画面構成

### トップ（PuzzleListView）

List を使わず `ScrollView` + `LazyVStack` で構成。設定画面感を排除し、プロダクト感を出す。

```
[Hero]
LiteralQ                    ← .system(size: 34, weight: .bold)
Think Beyond Assumptions.   ← .subheadline + .secondary
(0 / 3 Solved)              ← Capsule pill, indigo accent

[Section Header]
│ 問題                       ← indigo縦線(4pt×24pt) + .headline

[Card]  indigo border + shadow
┌──────────────────────────────────┐
│ 🍸  バーの男    難易度: ★★☆     │
│     ある男がバーに入り…          │
│                    ✓ クリア済み  │
└──────────────────────────────────┘

[Card]
┌──────────────────────────────────┐
│ 🏜️  砂漠の男    難易度: ★★★     │
│     砂漠の真ん中で裸の男が…      │
└──────────────────────────────────┘
```

**余白リズム**: Hero上 24pt → Hero下 28pt → セクション下 16pt → カード間 14pt → カード内パディング 14pt

### パズルカード

- 背景: `Theme.cardBackground`（`Color(white: 0.14)`）
- ボーダー: `Theme.cardBorder`（indigo 0.4, 1pt）
- 角丸: 14pt
- シャドウ: `.shadow(color: .black.opacity(0.3), radius: 4, y: 2)`
- レイアウト: `HStack` — 左に絵文字（64×64, indigo背景, 角丸12pt）、中央にテキスト群
- タイトル行: タイトル（`.headline`）+ Spacer + 難易度ラベル＋星
- プレビュー: `.caption` 2行、`fixedSize(horizontal: false, vertical: true)`
- Solved バッジ: 緑チェック + テキスト（条件付き表示）

### 進捗カウンター

- Capsule 形状の pill UI
- 背景: `Theme.accent.opacity(0.12)`
- 数字: `Theme.accent`（インディゴ）で強調
- テキスト: `Theme.progressText`（白70%）

### 難易度表示

- 「難易度:」ラベル（`.caption2`, 白40%）+ 星3つ
- filled: イエロー / empty: グレー40%
- パズルごとの値は `PuzzleMetadata` に静的マップで保持

### Solved バッジ

- `checkmark.circle.fill` + 「クリア済み」テキスト
- グリーン、`.caption2.weight(.medium)`
- `SolvedPuzzleStore`（UserDefaults永続化）で状態管理

## コンポーネント設計

### 質問ボタン（GameView）

- 左端にアクセントカラーの縦線（3pt）— トップと統一
- 背景は `.fill.quaternary`
- `RoundedRectangle` + `separator` ボーダー（0.5pt）でカード感
- `.plain` ボタンスタイル

### 出題文セクション

- 背景: `.fill.quaternary`（`.ultraThinMaterial` は可読性が不安定なため不使用）
- パディングを広めに取り、読みやすさ確保

### 回答済みリスト

- デフォルト非表示。`DisclosureGroup` で「回答済み (N)」として折りたたみ
- 各アイテムは質問文 + 回答バッジを縦配置

## アニメーション・トランジション

| 箇所 | 演出 |
|------|------|
| 回答フィードバック | タップ後0.6秒の `.ultraThinMaterial` オーバーレイ（回答ラベル表示） |
| 質問退場 | `.opacity.combined(with: .move(edge: .leading))` |
| クリア遷移 | `.easeInOut(duration: 0.4)` + `.transition(.opacity)` |
| 共通アニメーション | `.easeInOut(duration: 0.3)` |

## 原則

- ダークモード強制（`.preferredColorScheme(.dark)`）
- アクセントカラーはインディゴ1色に限定し、カードボーダー・絵文字背景・進捗 pill・セクションバーで統一使用
- カードは微かなシャドウ + ボーダーで浮きを表現（過剰装飾は避ける）
- 情報が少ないページでは余白を増やし、空間を活かす
- 縦線をブランド要素としてトップ・ゲーム画面で統一使用
- パズルメタデータ（絵文字・難易度）は `PuzzleMetadata` に静的マップで管理

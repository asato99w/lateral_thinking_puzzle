# Clean Architecture ガイド

## 概要

本プロジェクトでは Robert C. Martin の Clean Architecture を採用し、
ビジネスロジックをUIやフレームワークから独立させる。

## レイヤー構成

```
┌─────────────────────────────────────┐
│  Presentation (SwiftUI Views, VM)   │  ← フレームワーク依存
├─────────────────────────────────────┤
│  Interface Adapters (Repository実装) │  ← 変換・橋渡し
├─────────────────────────────────────┤
│  Use Cases (アプリケーションロジック)  │  ← ユースケース固有
├─────────────────────────────────────┤
│  Entities (ドメインモデル・エンジン)   │  ← 最も安定・依存なし
└─────────────────────────────────────┘
```

## 依存性の方向

- 依存は常に **外側 → 内側** の一方向
- Entities は他のどのレイヤーにも依存しない
- Use Cases は Entities のみに依存する
- Presentation は Use Cases の Protocol に依存する（具象に依存しない）

## レイヤーの責務

### Entities

ビジネスルールとドメインモデル。フレームワーク非依存。

- Descriptor, Paradigm, Question, GameState
- ゲームエンジン（tension, alignment, update, assimilate）
- バリデーションルール

```
LateralThinkingPuzzle/
└── Domain/
    ├── Entities/
    └── Engine/
```

### Use Cases

アプリケーション固有のビジネスルール。

- ゲーム開始、質問選択、クリア判定
- パズルデータの読み込み指示

```
LateralThinkingPuzzle/
└── UseCases/
```

### Interface Adapters

外部とのデータ変換。

- Repository 実装（JSONからのデコード）
- ViewModel（Use Cases の結果をView向けに変換）

```
LateralThinkingPuzzle/
├── Data/
│   └── Repositories/
└── Presentation/
    └── ViewModels/
```

### Presentation

UI層。SwiftUI に依存する。

- SwiftUI Views
- ナビゲーション

```
LateralThinkingPuzzle/
└── Presentation/
    └── Views/
```

## ディレクトリ構成

```
LateralThinkingPuzzle/
├── Domain/              # Entities + Use Cases
│   ├── Entities/        # ドメインモデル
│   ├── Engine/          # ゲームエンジン
│   └── UseCases/        # ユースケース
├── Data/                # Interface Adapters (データ側)
│   └── Repositories/    # データ取得の実装
├── Presentation/        # UI層
│   ├── Views/           # SwiftUI Views
│   └── ViewModels/      # ViewModel
└── Resources/           # アセット・JSONデータ
```

## 依存性逆転の適用

Use Cases は Repository の Protocol を定義し、Data 層が実装する。

```swift
// Domain 層で Protocol を定義
protocol PuzzleRepository {
    func fetchPuzzleList() -> [PuzzleSummary]
    func fetchPuzzle(id: String) -> PuzzleData
}

// Data 層で実装
struct JSONPuzzleRepository: PuzzleRepository { ... }
```

## テストにおける利点

- Entities / Engine は UIなしで単体テスト可能
- Use Cases は Repository を Mock に差し替えてテスト可能
- Presentation は Preview + UITest でテスト可能

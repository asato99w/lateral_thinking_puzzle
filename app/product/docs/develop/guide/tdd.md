# TDD (Test-Driven Development) ガイド

## 概要

本プロジェクトでは TDD を採用し、テストを先に書いてから実装を行う。
ゲームエンジンの正確性が製品の核であるため、テスト駆動で品質を担保する。

## TDD サイクル

```
Red → Green → Refactor
```

1. **Red**: 失敗するテストを書く
2. **Green**: テストを通す最小限のコードを書く
3. **Refactor**: コードを整理する（テストは通ったまま）

## テストフレームワーク

| 用途 | フレームワーク |
|------|--------------|
| ユニットテスト | Swift Testing (`@Test`, `#expect`) |
| UIテスト | XCUITest |
| テスト実行 | Xcode Test Navigator / `xcodebuild test` |

## テスト対象と優先度

### 必須（Domain層）

ゲームエンジンのロジックはすべてテスト駆動で実装する。

| 対象 | テスト内容 |
|------|-----------|
| tension | 観測値とパラダイム予測の矛盾数が正しいか |
| alignment | H値に基づくパラダイム適合度の計算が正しいか |
| update | 直接更新 → 同化 → シフト判定 → オープン更新の各ステップ |
| initGame | 初期状態（H=0.5, Ps反映, 初期同化）が正しいか |
| initQuestions | 初期オープン質問群の選出が正しいか |
| openQuestions | H ベース / D⁺ ベースの開放条件が正しいか |
| checkClear | クリア判定が正しいか |

### 推奨（Data層）

| 対象 | テスト内容 |
|------|-----------|
| JSONデコード | パズルデータの読み込みとバリデーション |
| Repository | データ取得の正常系・異常系 |

### 任意（Presentation層）

| 対象 | テスト内容 |
|------|-----------|
| ViewModel | 状態変更が正しくViewに反映されるか |
| UIテスト | ゲームフロー全体の操作確認 |

## テストの書き方

### 命名規則

`test_[対象]_[条件]_[期待結果]`

```swift
@Test func test_tension_allMatchingObservations_returnsZero()
@Test func test_tension_oneContradiction_returnsOne()
@Test func test_alignment_allDPlusAtOne_returnsOne()
@Test func test_update_irrelevantAnswer_addsToR()
```

### テスト構造

Arrange → Act → Assert パターンを使う。

```swift
@Test func test_tension_oneContradiction_returnsOne() {
    // Arrange
    let paradigm = Paradigm(id: "P1", name: "test", dPlus: ["d1"], dMinus: ["d2"], relations: [])
    let o: [String: Int] = ["d1": 0]  // P1は d1=1 と予測、観測は 0

    // Act
    let result = tension(o: o, paradigm: paradigm)

    // Assert
    #expect(result == 1)
}
```

## テストデータ

- テスト用の最小パズルデータを fixture として用意する
- 本番の JSON データに依存しない
- エッジケース用のデータは各テストケース内で構築する

## ディレクトリ構成

```
LateralThinkingPuzzleTests/
├── Domain/
│   ├── EngineTests/        # ゲームエンジンのテスト
│   └── EntitiesTests/      # モデルのバリデーションテスト
├── Data/
│   └── RepositoryTests/    # データ読み込みテスト
├── Presentation/
│   └── ViewModelTests/     # ViewModel テスト
└── Fixtures/               # テスト用データ
```

## 実装順序

TDD に従い、以下の順序で進める。

1. Entities のバリデーションテスト → 実装
2. Engine の各関数テスト → 実装
3. Repository のデコードテスト → 実装
4. ViewModel のテスト → 実装
5. UIテスト → View実装

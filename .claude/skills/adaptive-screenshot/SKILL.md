---
name: adaptive-screenshot
description: iOSシミュレータまたはブラウザのスクリーンショットを撮影する際に使用。画像処理エラー（Could not process image等）を回避するため、低品質・小サイズから段階的に品質を上げて撮影する。スクリーンショット、画面キャプチャ、UI確認時に自動適用。
allowed-tools: Bash, Read, mcp__chrome-devtools__take_screenshot, mcp__chrome-devtools__take_snapshot
---

# Adaptive Screenshot - 段階的品質スクリーンショット

API の画像処理エラーを回避するため、小サイズ・低品質から段階的に上げてスクリーンショットを撮影する。

## 対象環境の判定

まず対象を判定する：
- **iOSシミュレータ**: `xcrun simctl list devices booted` で起動中デバイスがあれば対象
- **ブラウザ**: Chrome DevTools MCP の `list_pages` でページがあれば対象

## iOSシミュレータの場合

撮影コマンド: `xcrun simctl io booted screenshot`
リサイズ: `sips` で解像度・品質を調整

### Step 1: JPEG 50% リサイズ + 低品質 (最初に試す)
```bash
xcrun simctl io booted screenshot --type png /tmp/sim_raw.png
sips -Z 800 -s format jpeg -s formatOptions 30 /tmp/sim_raw.png --out /tmp/sim_screenshot.jpeg
```
- 縦800px にリサイズ、JPEG品質30

### Step 2: 読み取り困難な場合 → サイズ・品質を上げる
```bash
sips -Z 1200 -s format jpeg -s formatOptions 60 /tmp/sim_raw.png --out /tmp/sim_screenshot.jpeg
```

### Step 3: まだ不十分 → さらに上げる
```bash
sips -Z 1600 -s format jpeg -s formatOptions 80 /tmp/sim_raw.png --out /tmp/sim_screenshot.jpeg
```

### Step 4: JPEG限界 → PNG リサイズのみ
```bash
sips -Z 1200 /tmp/sim_raw.png --out /tmp/sim_screenshot.png
```

### Step 5: 元画像をそのまま読み込む（最終手段）
```bash
# /tmp/sim_raw.png をそのまま Read で読み込む
```

各ステップで `/tmp/sim_screenshot.*` を Read ツールで読み込み確認する。

## ブラウザの場合

Chrome DevTools MCP の `take_screenshot` を使用。

### Step 1: JPEG q30
- `format: "jpeg"`, `quality: 30`, `fullPage: false`

### Step 2: JPEG q60
### Step 3: JPEG q85
### Step 4: PNG
### Step 5: ファイル保存 → Read

## 重要ルール

- **常に Step 1 から開始する**。いきなり高品質で撮影しない
- **エラー発生時は次のステップに進む**。同じ設定でリトライしない
- **品質を上げる判断基準**: テキストが読めない、UI要素の境界が不明瞭、色の区別がつかない
- **sim_raw.png は毎回撮り直さない**。1回の撮影から sips で品質を変えて再変換する
- 最終的に読み取れた画像でUI確認を行い、改善提案に進む

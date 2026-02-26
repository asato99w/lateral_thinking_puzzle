#!/bin/bash
#
# App Store スクリーンショット撮影スクリプト
#
# 使い方:
#   ./scripts/capture_screenshots.sh          # 全デバイスサイズ
#   ./scripts/capture_screenshots.sh 6.7      # 6.7インチのみ
#   ./scripts/capture_screenshots.sh 6.5      # 6.5インチのみ
#
# 出力先: docs/apple/screenshots/{サイズ}/
#

set -euo pipefail

# ─── 設定 ──────────────────────────────────────────

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
XCODE_PROJECT="$PROJECT_DIR/LateralThinkingPuzzle.xcodeproj"
SCHEME="LateralThinkingPuzzle"
TEST_CLASS="LateralThinkingPuzzleUITests/AppStoreScreenshotTests"
SCREENSHOT_DIR="$PROJECT_DIR/../docs/apple/screenshots"
RUNTIME="com.apple.CoreSimulator.SimRuntime.iOS-18-5"
TEMP_DIR=$(mktemp -d)

# デバイス定義: サイズ → デバイスタイプ名, シミュレータ名
declare -A DEVICE_TYPE=(
    ["6.7"]="com.apple.CoreSimulator.SimDeviceType.iPhone-16-Pro-Max"
    ["6.5"]="com.apple.CoreSimulator.SimDeviceType.iPhone-11-Pro-Max"
)
declare -A DEVICE_NAME=(
    ["6.7"]="Screenshot_iPhone16ProMax"
    ["6.5"]="Screenshot_iPhone11ProMax"
)
declare -A DEVICE_DISPLAY=(
    ["6.7"]="iPhone 16 Pro Max (6.7\")"
    ["6.5"]="iPhone 11 Pro Max (6.5\")"
)

# 引数で対象サイズを絞り込み
if [[ $# -gt 0 ]]; then
    TARGET_SIZES=("$@")
else
    TARGET_SIZES=("6.7" "6.5")
fi

# ─── ユーティリティ ─────────────────────────────────

cleanup() {
    echo ""
    echo "🧹 一時ファイル削除中..."
    # スクリーンショット専用シミュレータを削除
    for size in "${TARGET_SIZES[@]}"; do
        local sim_name="${DEVICE_NAME[$size]}"
        local udid
        udid=$(xcrun simctl list devices -j | python3 -c "
import json, sys
data = json.load(sys.stdin)
for runtime, devices in data.get('devices', {}).items():
    for d in devices:
        if d['name'] == '$sim_name':
            print(d['udid'])
            sys.exit(0)
" 2>/dev/null || true)
        if [[ -n "$udid" ]]; then
            xcrun simctl shutdown "$udid" 2>/dev/null || true
            xcrun simctl delete "$udid" 2>/dev/null || true
        fi
    done
    rm -rf "$TEMP_DIR"
}
trap cleanup EXIT

log_step() {
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "  $1"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
}

# ─── シミュレータ準備 ────────────────────────────────

ensure_simulator() {
    local size="$1"
    local device_type="${DEVICE_TYPE[$size]}"
    local sim_name="${DEVICE_NAME[$size]}"

    # 既存のシミュレータを検索
    local udid
    udid=$(xcrun simctl list devices -j | python3 -c "
import json, sys
data = json.load(sys.stdin)
for runtime, devices in data.get('devices', {}).items():
    for d in devices:
        if d['name'] == '$sim_name' and d.get('isAvailable', False):
            print(d['udid'])
            sys.exit(0)
" 2>/dev/null || true)

    if [[ -n "$udid" ]]; then
        echo "  ✓ シミュレータ再利用: $sim_name ($udid)"
    else
        echo "  + シミュレータ作成: $sim_name"
        udid=$(xcrun simctl create "$sim_name" "$device_type" "$RUNTIME")
        echo "  ✓ 作成完了: $udid"
    fi

    echo "$udid"
}

# ─── テスト実行 ──────────────────────────────────────

run_tests() {
    local size="$1"
    local sim_name="${DEVICE_NAME[$size]}"
    local result_path="$TEMP_DIR/result_${size}.xcresult"

    echo "  🧪 UIテスト実行中... (数分かかります)"

    # 古い結果を削除
    rm -rf "$result_path"

    set +e
    xcodebuild test \
        -project "$XCODE_PROJECT" \
        -scheme "$SCHEME" \
        -destination "platform=iOS Simulator,name=$sim_name" \
        -only-testing:"$TEST_CLASS" \
        -resultBundlePath "$result_path" \
        -quiet 2>&1 | while IFS= read -r line; do
            # テスト結果のサマリのみ表示
            if echo "$line" | grep -qE "Test (Suite|Case)|passed|failed|Executed"; then
                echo "    $line"
            fi
        done
    local test_exit=${PIPESTATUS[0]}
    set -e

    if [[ ! -d "$result_path" ]]; then
        echo "  ❌ テスト実行失敗: xcresult が生成されませんでした"
        return 1
    fi

    # テストが失敗してもスクリーンショットは取れている可能性がある
    if [[ $test_exit -ne 0 ]]; then
        echo "  ⚠️  一部テストが失敗しましたが、スクリーンショット抽出を試みます"
    fi

    echo "$result_path"
}

# ─── スクリーンショット抽出 ────────────────────────────

extract_screenshots() {
    local result_path="$1"
    local size="$2"
    local extract_dir="$TEMP_DIR/extracted_${size}"
    local target_dir="$SCREENSHOT_DIR/$size"

    echo "  📦 スクリーンショット抽出中..."

    mkdir -p "$extract_dir"

    # xcresulttool export attachments で全添付ファイルを抽出
    xcrun xcresulttool export attachments \
        --path "$result_path" \
        --output-path "$extract_dir" 2>/dev/null

    # manifest.json から AppStore_ プレフィックスの添付ファイルを特定してリネーム
    local manifest="$extract_dir/manifest.json"
    if [[ ! -f "$manifest" ]]; then
        echo "  ❌ manifest.json が見つかりません"
        return 1
    fi

    mkdir -p "$target_dir"

    # manifest.json をパースして、名前付きスクリーンショットをコピー
    python3 <<PYEOF
import json, shutil, os

manifest_path = "$manifest"
extract_dir = "$extract_dir"
target_dir = "$target_dir"

with open(manifest_path) as f:
    manifest = json.load(f)

count = 0
for test_entry in manifest:
    for att in test_entry.get("attachments", []):
        name = att.get("suggestedHumanReadableName", "")
        exported = att.get("exportedFileName", "")
        if not name.startswith("AppStore_"):
            continue
        src = os.path.join(extract_dir, exported)
        if not os.path.exists(src):
            continue
        # 拡張子を決定
        _, ext = os.path.splitext(exported)
        if not ext:
            ext = ".png"
        dst = os.path.join(target_dir, name + ext)
        shutil.copy2(src, dst)
        count += 1
        print(f"    📸 {name}{ext}")

if count == 0:
    print("    ⚠️  AppStore_ プレフィックスのスクリーンショットが見つかりませんでした")
else:
    print(f"  ✅ {count} 枚保存完了")
PYEOF
}

# ─── メイン処理 ──────────────────────────────────────

echo ""
echo "📸 App Store スクリーンショット撮影"
echo "   対象: ${TARGET_SIZES[*]}"
echo "   出力: $SCREENSHOT_DIR"

for size in "${TARGET_SIZES[@]}"; do
    log_step "📱 ${DEVICE_DISPLAY[$size]}"

    # 1. シミュレータ準備
    udid=$(ensure_simulator "$size")

    # 2. テスト実行
    result_path=$(run_tests "$size")
    if [[ $? -ne 0 || -z "$result_path" ]]; then
        echo "  ❌ スキップ: テスト実行に失敗"
        continue
    fi

    # 3. スクリーンショット抽出
    extract_screenshots "$result_path" "$size"
done

# ─── 結果サマリ ──────────────────────────────────────

log_step "📋 結果サマリ"

total=0
for size in "${TARGET_SIZES[@]}"; do
    target_dir="$SCREENSHOT_DIR/$size"
    if [[ -d "$target_dir" ]]; then
        count=$(find "$target_dir" -name "AppStore_*" -type f 2>/dev/null | wc -l | tr -d ' ')
        total=$((total + count))
        echo ""
        echo "  📁 $size インチ ($target_dir):"
        if [[ $count -gt 0 ]]; then
            find "$target_dir" -name "AppStore_*" -type f -exec basename {} \; | sort | while read -r f; do
                echo "     $f"
            done
        else
            echo "     (なし)"
        fi
    fi
done

echo ""
if [[ $total -gt 0 ]]; then
    echo "✅ 合計 ${total} 枚のスクリーンショットを保存しました"
    echo "   $SCREENSHOT_DIR"
else
    echo "⚠️  スクリーンショットが保存されませんでした"
    echo "   テスト結果を確認してください"
fi
echo ""

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

# デバイス定義
get_device_type() {
    case "$1" in
        6.7) echo "com.apple.CoreSimulator.SimDeviceType.iPhone-16-Pro-Max" ;;
        6.5) echo "com.apple.CoreSimulator.SimDeviceType.iPhone-11-Pro-Max" ;;
    esac
}
get_sim_name() {
    case "$1" in
        6.7) echo "Screenshot_iPhone16ProMax" ;;
        6.5) echo "Screenshot_iPhone11ProMax" ;;
    esac
}
get_display_name() {
    case "$1" in
        6.7) echo "iPhone 16 Pro Max (6.7\")" ;;
        6.5) echo "iPhone 11 Pro Max (6.5\")" ;;
    esac
}

# 引数で対象サイズを絞り込み
if [[ $# -gt 0 ]]; then
    TARGET_SIZES=("$@")
else
    TARGET_SIZES=("6.7" "6.5")
fi

# ─── ユーティリティ ─────────────────────────────────

# ログは全て stderr に出力（関数の stdout は戻り値専用）
log()  { echo "$@" >&2; }

find_sim_udid() {
    local sim_name="$1"
    xcrun simctl list devices -j | python3 -c "
import json, sys
data = json.load(sys.stdin)
for runtime, devices in data.get('devices', {}).items():
    for d in devices:
        if d['name'] == '${sim_name}' and d.get('isAvailable', False):
            print(d['udid'])
            sys.exit(0)
" 2>/dev/null || true
}

cleanup() {
    log ""
    log "🧹 一時ファイル削除中..."
    for size in "${TARGET_SIZES[@]}"; do
        local sim_name
        sim_name=$(get_sim_name "$size")
        local udid
        udid=$(find_sim_udid "$sim_name")
        if [[ -n "$udid" ]]; then
            xcrun simctl shutdown "$udid" 2>/dev/null || true
            xcrun simctl delete "$udid" 2>/dev/null || true
        fi
    done
    rm -rf "$TEMP_DIR"
}
trap cleanup EXIT

# ─── シミュレータ準備 ────────────────────────────────

ensure_simulator() {
    local size="$1"
    local device_type
    device_type=$(get_device_type "$size")
    local sim_name
    sim_name=$(get_sim_name "$size")

    local udid
    udid=$(find_sim_udid "$sim_name")

    if [[ -n "$udid" ]]; then
        log "  ✓ シミュレータ再利用: $sim_name ($udid)"
    else
        log "  + シミュレータ作成: $sim_name"
        udid=$(xcrun simctl create "$sim_name" "$device_type" "$RUNTIME")
        log "  ✓ 作成完了: $udid"
    fi

    # stdout で UDID を返す
    echo "$udid"
}

# ─── テスト実行 ──────────────────────────────────────

run_tests() {
    local size="$1"
    local sim_name
    sim_name=$(get_sim_name "$size")
    local result_path="$TEMP_DIR/result_${size//./_}.xcresult"

    log "  🧪 UIテスト実行中... (数分かかります)"

    rm -rf "$result_path"

    local test_exit=0
    xcodebuild test \
        -project "$XCODE_PROJECT" \
        -scheme "$SCHEME" \
        -destination "platform=iOS Simulator,name=$sim_name" \
        -only-testing:"$TEST_CLASS" \
        -resultBundlePath "$result_path" \
        2>&1 | while IFS= read -r line; do
            if echo "$line" | grep -qE "Test (Suite|Case)|passed|failed|Executed"; then
                log "    $line"
            fi
        done || test_exit=$?

    if [[ ! -d "$result_path" ]]; then
        log "  ❌ テスト実行失敗: xcresult が生成されませんでした"
        return 1
    fi

    if [[ $test_exit -ne 0 ]]; then
        log "  ⚠️  一部テストが失敗しましたが、スクリーンショット抽出を試みます"
    fi

    # stdout で結果パスを返す
    echo "$result_path"
}

# ─── スクリーンショット抽出 ────────────────────────────

extract_screenshots() {
    local result_path="$1"
    local size="$2"
    local extract_dir="$TEMP_DIR/extracted_${size//./_}"
    local target_dir="$SCREENSHOT_DIR/$size"

    log "  📦 スクリーンショット抽出中..."

    mkdir -p "$extract_dir"

    xcrun xcresulttool export attachments \
        --path "$result_path" \
        --output-path "$extract_dir" 2>/dev/null

    local manifest="$extract_dir/manifest.json"
    if [[ ! -f "$manifest" ]]; then
        log "  ❌ manifest.json が見つかりません"
        return 1
    fi

    mkdir -p "$target_dir"

    python3 <<PYEOF
import json, shutil, os, sys, re

manifest_path = "$manifest"
extract_dir = "$extract_dir"
target_dir = "$target_dir"

with open(manifest_path) as f:
    manifest = json.load(f)

count = 0
for test_entry in manifest:
    for att in test_entry.get("attachments", []):
        suggested = att.get("suggestedHumanReadableName", "")
        exported = att.get("exportedFileName", "")
        if not suggested.startswith("AppStore_"):
            continue
        src = os.path.join(extract_dir, exported)
        if not os.path.exists(src):
            continue
        # suggestedHumanReadableName の形式:
        #   "AppStore_01_PuzzleList_0_XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX.png"
        # → 末尾の _N_UUID 部分を除去して "AppStore_01_PuzzleList.png" にする
        clean = re.sub(
            r'_\d+_[0-9A-Fa-f]{8}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{12}',
            '', suggested
        )
        # 拡張子がなければ .png を付与
        if not os.path.splitext(clean)[1]:
            clean += ".png"
        dst = os.path.join(target_dir, clean)
        shutil.copy2(src, dst)
        count += 1
        print(f"    📸 {clean}", file=sys.stderr)

if count == 0:
    print("    ⚠️  AppStore_ プレフィックスのスクリーンショットが見つかりませんでした", file=sys.stderr)
else:
    print(f"  ✅ {count} 枚保存完了", file=sys.stderr)
PYEOF
}

# ─── メイン処理 ──────────────────────────────────────

log ""
log "📸 App Store スクリーンショット撮影"
log "   対象: ${TARGET_SIZES[*]}"
log "   出力: $SCREENSHOT_DIR"

for size in "${TARGET_SIZES[@]}"; do
    log ""
    log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    log "  📱 $(get_display_name "$size")"
    log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    # 1. シミュレータ準備
    udid=$(ensure_simulator "$size")

    # 2. テスト実行
    if ! result_path=$(run_tests "$size"); then
        log "  ❌ スキップ: テスト実行に失敗"
        continue
    fi

    # 3. スクリーンショット抽出
    extract_screenshots "$result_path" "$size"
done

# ─── 結果サマリ ──────────────────────────────────────

log ""
log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
log "  📋 結果サマリ"
log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

total=0
for size in "${TARGET_SIZES[@]}"; do
    target_dir="$SCREENSHOT_DIR/$size"
    if [[ -d "$target_dir" ]]; then
        count=$(find "$target_dir" -name "AppStore_*" -type f 2>/dev/null | wc -l | tr -d ' ')
        total=$((total + count))
        log ""
        log "  📁 $size インチ ($target_dir):"
        if [[ "$count" -gt 0 ]]; then
            find "$target_dir" -name "AppStore_*" -type f -exec basename {} \; | sort | while read -r f; do
                log "     $f"
            done
        else
            log "     (なし)"
        fi
    fi
done

log ""
if [[ "$total" -gt 0 ]]; then
    log "✅ 合計 ${total} 枚のスクリーンショットを保存しました"
    log "   $SCREENSHOT_DIR"
else
    log "⚠️  スクリーンショットが保存されませんでした"
    log "   テスト結果を確認してください"
fi
log ""

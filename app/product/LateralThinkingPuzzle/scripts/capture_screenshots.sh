#!/bin/bash
#
# App Store スクリーンショット撮影スクリプト
#
# 使い方:
#   ./scripts/capture_screenshots.sh                # 全サイズ・全言語
#   ./scripts/capture_screenshots.sh 6.5            # 6.5インチ・全言語
#   ./scripts/capture_screenshots.sh 6.5 ja         # 6.5インチ・日本語のみ
#   ./scripts/capture_screenshots.sh all en          # 全サイズ・英語のみ
#
# 出力先: docs/apple/screenshots/{サイズ}/{言語}/
#

set -euo pipefail

# ─── 設定 ──────────────────────────────────────────

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
XCODE_PROJECT="$PROJECT_DIR/LateralThinkingPuzzle.xcodeproj"
SCHEME="LateralThinkingPuzzle"
TEST_CLASS="LateralThinkingPuzzleUITests/AppStoreScreenshotTests"
SCREENSHOT_DIR="$PROJECT_DIR/../docs/apple/screenshots"
RUNTIME=$(xcrun simctl list runtimes -j | python3 -c "
import json, sys
runtimes = json.load(sys.stdin).get('runtimes', [])
ios = [r for r in runtimes if r.get('isAvailable') and 'iOS' in r.get('name', '')]
if not ios:
    print('ERROR: No available iOS runtime found', file=sys.stderr)
    sys.exit(1)
ios.sort(key=lambda r: r.get('version', ''), reverse=True)
print(ios[0]['identifier'])
")
if [[ -z "$RUNTIME" || "$RUNTIME" == "ERROR"* ]]; then
    echo "❌ 利用可能な iOS ランタイムが見つかりません" >&2
    exit 1
fi
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
get_lang_display() {
    case "$1" in
        ja) echo "日本語" ;;
        en) echo "English" ;;
    esac
}

# 引数解析
ARG_SIZE="${1:-all}"
ARG_LANG="${2:-all}"

if [[ "$ARG_SIZE" == "all" ]]; then
    TARGET_SIZES=("6.7" "6.5")
else
    TARGET_SIZES=("$ARG_SIZE")
fi

if [[ "$ARG_LANG" == "all" ]]; then
    TARGET_LANGS=("ja" "en")
else
    TARGET_LANGS=("$ARG_LANG")
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
    local lang="$2"
    local sim_name
    sim_name=$(get_sim_name "$size")
    local result_path="$TEMP_DIR/result_${size//./_}_${lang}.xcresult"

    log "  🧪 UIテスト実行中... (数分かかります)"

    rm -rf "$result_path"

    local test_exit=0
    SCREENSHOT_LANG="$lang" xcodebuild test \
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
    local lang="$3"
    local extract_dir="$TEMP_DIR/extracted_${size//./_}_${lang}"
    local target_dir="$SCREENSHOT_DIR/$size/$lang"

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
log "   サイズ: ${TARGET_SIZES[*]}"
log "   言語: ${TARGET_LANGS[*]}"
log "   ランタイム: $RUNTIME"
log "   出力: $SCREENSHOT_DIR"

for size in "${TARGET_SIZES[@]}"; do
    # シミュレータはサイズごとに1つ作成し、言語間で再利用
    udid=$(ensure_simulator "$size")

    for lang in "${TARGET_LANGS[@]}"; do
        log ""
        log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        log "  📱 $(get_display_name "$size") — $(get_lang_display "$lang")"
        log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

        # テスト実行
        if ! result_path=$(run_tests "$size" "$lang"); then
            log "  ❌ スキップ: テスト実行に失敗"
            continue
        fi

        # スクリーンショット抽出
        extract_screenshots "$result_path" "$size" "$lang"
    done
done

# ─── 結果サマリ ──────────────────────────────────────

log ""
log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
log "  📋 結果サマリ"
log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

total=0
for size in "${TARGET_SIZES[@]}"; do
    for lang in "${TARGET_LANGS[@]}"; do
        target_dir="$SCREENSHOT_DIR/$size/$lang"
        if [[ -d "$target_dir" ]]; then
            count=$(find "$target_dir" -name "AppStore_*" -type f 2>/dev/null | wc -l | tr -d ' ')
            total=$((total + count))
            log ""
            log "  📁 $size インチ / $(get_lang_display "$lang") ($target_dir):"
            if [[ "$count" -gt 0 ]]; then
                find "$target_dir" -name "AppStore_*" -type f -exec basename {} \; | sort | while read -r f; do
                    log "     $f"
                done
            else
                log "     (なし)"
            fi
        fi
    done
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

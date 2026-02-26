import XCTest

/// App Store 提出用スクリーンショット撮影テスト
///
/// ## 実行方法
///
/// ### Xcode から:
/// 1. シミュレータを選択（下記参照）
/// 2. Test Navigator でこのクラスを右クリック → "Run"
///
/// ### コマンドラインから:
/// ```
/// # 6.7インチ (必須)
/// xcodebuild test \
///   -project LateralThinkingPuzzle.xcodeproj \
///   -scheme LateralThinkingPuzzle \
///   -destination 'platform=iOS Simulator,name=iPhone 16 Pro Max' \
///   -only-testing:LateralThinkingPuzzleUITests/AppStoreScreenshotTests \
///   -resultBundlePath screenshots_6_7.xcresult
///
/// # 6.5インチ (必須)
/// xcodebuild test \
///   -project LateralThinkingPuzzle.xcodeproj \
///   -scheme LateralThinkingPuzzle \
///   -destination 'platform=iOS Simulator,name=iPhone 11 Pro Max' \
///   -only-testing:LateralThinkingPuzzleUITests/AppStoreScreenshotTests \
///   -resultBundlePath screenshots_6_5.xcresult
/// ```
///
/// ## スクリーンショットの取り出し
/// Xcode → Report Navigator → テスト結果 → 各テスト展開 → Attachments を右クリック → Export
///
/// ## 必要なデバイスサイズ
/// | デバイス                | サイズ          | 解像度         |
/// |------------------------|----------------|---------------|
/// | iPhone 16 Pro Max      | 6.7インチ       | 1320 × 2868   |
/// | iPhone 15 Pro Max      | 6.7インチ       | 1290 × 2796   |
/// | iPhone 11 Pro Max      | 6.5インチ       | 1242 × 2688   |
///
/// ## 言語切り替え
/// setUp 内の launchArguments を変更して英語版スクリーンショットも撮影可能。
final class AppStoreScreenshotTests: XCTestCase {

    let app = XCUIApplication()

    override func setUpWithError() throws {
        continueAfterFailure = true

        // ── 日本語スクリーンショット ──
        app.launchArguments += ["-AppleLanguages", "(ja)", "-AppleLocale", "ja_JP"]

        // ── 英語スクリーンショットの場合は上を以下に差し替え ──
        // app.launchArguments += ["-AppleLanguages", "(en)", "-AppleLocale", "en_US"]

        app.launch()
    }

    // MARK: - Helpers

    private func takeScreenshot(_ name: String) {
        let screenshot = app.screenshot()
        let attachment = XCTAttachment(screenshot: screenshot)
        attachment.name = name
        attachment.lifetime = .keepAlways
        add(attachment)
    }

    /// 最初の利用可能な質問ボタンをタップする。
    /// 質問ボタンはラベルが数字で始まる（質問番号付き）ことで識別。
    /// - Returns: タップできた場合 true
    @discardableResult
    private func tapFirstAvailableQuestion() -> Bool {
        let predicate = NSPredicate(format: "label MATCHES %@", "[0-9]+.*")
        let questionButtons = app.buttons.matching(predicate)

        for i in 0..<questionButtons.count {
            let button = questionButtons.element(boundBy: i)
            if button.isHittable {
                button.tap()
                return true
            }
        }
        return false
    }

    /// パズルをクリアまで自動プレイする。
    private func playUntilCleared(maxTaps: Int = 60) {
        for _ in 0..<maxTaps {
            if app.staticTexts["クリア!"].exists { return }

            if !tapFirstAvailableQuestion() {
                // 質問がスクロール外にある可能性
                app.swipeUp()
                sleep(1)
                if !tapFirstAvailableQuestion() { return }
            }
            sleep(1)
        }
    }

    // MARK: - 1. パズル一覧画面

    func test_screenshot_01_puzzleList() throws {
        let puzzle = app.staticTexts["ウミガメのスープ"]
        XCTAssertTrue(puzzle.waitForExistence(timeout: 5), "パズル一覧が表示されるべき")

        takeScreenshot("AppStore_01_PuzzleList")
    }

    // MARK: - 2〜4. ゲーム画面（初期 → フィードバック → 途中経過）

    func test_screenshot_02_gameFlow() throws {
        // カテゴリタブのある「ウミガメのスープ」でゲーム画面を撮影
        let turtleSoup = app.staticTexts["ウミガメのスープ"]
        XCTAssertTrue(turtleSoup.waitForExistence(timeout: 5))
        turtleSoup.tap()
        sleep(2)

        XCTAssertTrue(
            app.staticTexts["出題"].waitForExistence(timeout: 5),
            "ゲーム画面が表示されるべき"
        )

        // ── 初期ゲーム画面（出題文 + オープン質問一覧） ──
        takeScreenshot("AppStore_02_GameScreen_Initial")

        // ── 1問目の回答フィードバック表示中 ──
        if tapFirstAvailableQuestion() {
            usleep(200_000) // 0.2秒 — フィードバックオーバーレイ表示中にキャプチャ
            takeScreenshot("AppStore_03_GameScreen_Feedback")
            sleep(1) // フィードバック終了待ち
        }

        // ── 数問回答後の途中経過 ──
        for _ in 0..<2 {
            tapFirstAvailableQuestion()
            sleep(1)
        }
        takeScreenshot("AppStore_04_GameScreen_InProgress")
    }

    // MARK: - 5. クリア画面

    func test_screenshot_03_clearScreen() throws {
        // 「バーの男」で全問回答してクリア画面を撮影
        let barMan = app.staticTexts["バーの男"]
        XCTAssertTrue(barMan.waitForExistence(timeout: 5))
        barMan.tap()
        sleep(2)

        playUntilCleared()

        let cleared = app.staticTexts["クリア!"]
        XCTAssertTrue(cleared.waitForExistence(timeout: 5), "パズルがクリアされるべき")

        takeScreenshot("AppStore_05_ClearScreen")
    }

    // MARK: - 6. コンテンツダウンロード画面

    func test_screenshot_04_contentDownload() throws {
        let puzzle = app.staticTexts["バーの男"]
        XCTAssertTrue(puzzle.waitForExistence(timeout: 5))

        app.buttons["arrow.down.circle"].tap()

        XCTAssertTrue(
            app.navigationBars["コンテンツ"].waitForExistence(timeout: 5),
            "コンテンツ画面が表示されるべき"
        )

        takeScreenshot("AppStore_06_ContentDownload")

        // スクロールして全体を撮影
        app.swipeUp()
        sleep(1)
        takeScreenshot("AppStore_07_ContentDownload_Scrolled")
    }
}

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
///
/// ## 注意
/// クリア画面のスクリーンショットは、パズルデータに `is_clear: true` の質問が
/// 設定されている必要があります。未設定の場合は test_screenshot_03 がスキップされます。
final class AppStoreScreenshotTests: XCTestCase {

    let app = XCUIApplication()

    /// 新規シミュレータの初回起動は時間がかかるため長めに設定
    private let elementTimeout: TimeInterval = 20

    override func setUpWithError() throws {
        continueAfterFailure = true

        // ── 日本語スクリーンショット ──
        // ContentLanguage は DebugSettings.languageOverride → Locale.current の順で言語を決定する。
        // シミュレータでは -AppleLanguages が Locale.current に反映されない場合があるため、
        // アプリ側の DebugSettings を直接オーバーライドする。
        app.launchArguments += ["-AppleLanguages", "(ja)", "-AppleLocale", "ja_JP"]
        app.launchArguments += ["-debug_languageOverride", "ja"]

        // ── 英語スクリーンショットの場合は上を以下に差し替え ──
        // app.launchArguments += ["-AppleLanguages", "(en)", "-AppleLocale", "en_US"]
        // app.launchArguments += ["-debug_languageOverride", "en"]

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

    /// 画面をスクロールしながら質問を探してタップする。
    /// - Returns: タップできた場合 true
    @discardableResult
    private func tapQuestionWithScroll() -> Bool {
        if tapFirstAvailableQuestion() { return true }
        // 質問がスクロール外にある可能性
        app.swipeUp()
        sleep(1)
        return tapFirstAvailableQuestion()
    }

    /// パズルを数問回答して進行する。
    private func answerQuestions(count: Int) {
        for _ in 0..<count {
            if !tapQuestionWithScroll() { break }
            sleep(1)
        }
    }

    // MARK: - 1. パズル一覧画面

    func test_screenshot_01_puzzleList() throws {
        let puzzle = app.staticTexts["ウミガメのスープ"]
        XCTAssertTrue(puzzle.waitForExistence(timeout: elementTimeout), "パズル一覧が表示されるべき")

        takeScreenshot("AppStore_01_PuzzleList")
    }

    // MARK: - 2〜4. ゲーム画面（初期 → フィードバック → 途中経過）

    func test_screenshot_02_gameFlow() throws {
        // 「バーの男」は初期状態で質問が表示されるためゲーム画面撮影に使用
        let barMan = app.staticTexts["バーの男"]
        XCTAssertTrue(barMan.waitForExistence(timeout: elementTimeout))
        barMan.tap()
        sleep(2)

        XCTAssertTrue(
            app.staticTexts["出題"].waitForExistence(timeout: elementTimeout),
            "ゲーム画面が表示されるべき"
        )

        // 質問が表示されるまで少し待つ
        sleep(1)

        // ── 初期ゲーム画面（出題文 + オープン質問一覧） ──
        // 質問一覧が見えるようスクロール
        app.swipeUp()
        sleep(1)
        takeScreenshot("AppStore_02_GameScreen_Initial")

        // ── 1問目の回答フィードバック表示中 ──
        if tapFirstAvailableQuestion() {
            usleep(200_000) // 0.2秒 — フィードバック表示中にキャプチャ
            takeScreenshot("AppStore_03_GameScreen_Feedback")
            sleep(2) // フィードバック終了待ち
        }

        // ── 数問回答後の途中経過 ──
        answerQuestions(count: 3)
        // 回答履歴が見える位置にスクロール
        app.swipeDown()
        sleep(1)
        takeScreenshot("AppStore_04_GameScreen_InProgress")
    }

    // MARK: - 5. クリア画面
    // 注意: パズルデータに is_clear: true の質問が必要。
    // 未設定の場合、このテストはスキップされます。

    func test_screenshot_03_clearScreen() throws {
        // 「バーの男」で全問回答してクリア画面を撮影
        let barMan = app.staticTexts["バーの男"]
        XCTAssertTrue(barMan.waitForExistence(timeout: elementTimeout))
        barMan.tap()
        sleep(2)

        // 全質問を回答
        for _ in 0..<30 {
            if app.staticTexts["クリア!"].exists { break }
            if !tapQuestionWithScroll() { break }
            sleep(1)
        }

        let cleared = app.staticTexts["クリア!"]
        if cleared.waitForExistence(timeout: 5) {
            takeScreenshot("AppStore_05_ClearScreen")
        } else {
            // クリア画面に到達できない場合は回答済み状態をキャプチャ
            // （is_clear 質問がパズルデータに未設定の場合）
            app.swipeDown()
            app.swipeDown()
            sleep(1)
            takeScreenshot("AppStore_05_GameScreen_AllAnswered")
        }
    }

    // MARK: - 6. コンテンツダウンロード画面

    func test_screenshot_04_contentDownload() throws {
        let puzzle = app.staticTexts["ウミガメのスープ"]
        XCTAssertTrue(puzzle.waitForExistence(timeout: elementTimeout))

        app.buttons["arrow.down.circle"].tap()

        XCTAssertTrue(
            app.navigationBars["コンテンツ"].waitForExistence(timeout: elementTimeout),
            "コンテンツ画面が表示されるべき"
        )

        takeScreenshot("AppStore_06_ContentDownload")

        // スクロールして全体を撮影
        app.swipeUp()
        sleep(1)
        takeScreenshot("AppStore_07_ContentDownload_Scrolled")
    }
}

import XCTest

/// App Store 提出用スクリーンショット撮影テスト
///
/// ## 実行方法
///
/// ### スクリプトから（推奨）:
/// ```
/// ./scripts/capture_screenshots.sh 6.5 ja   # 6.5インチ・日本語
/// ./scripts/capture_screenshots.sh 6.7 en   # 6.7インチ・英語
/// ./scripts/capture_screenshots.sh 6.5      # 6.5インチ・全言語
/// ./scripts/capture_screenshots.sh           # 全サイズ・全言語
/// ```
///
/// ### Xcode から:
/// 1. シミュレータを選択
/// 2. 環境変数 `SCREENSHOT_LANG` を設定（省略時は日本語）
/// 3. Test Navigator でこのクラスを右クリック → "Run"
///
/// ## 必要なデバイスサイズ
/// | デバイス                | サイズ          | 解像度         |
/// |------------------------|----------------|---------------|
/// | iPhone 16 Pro Max      | 6.7インチ       | 1320 × 2868   |
/// | iPhone 11 Pro Max      | 6.5インチ       | 1242 × 2688   |
/// | iPad Pro 13" (M4)      | 13インチ        | 2048 × 2732   |
///
/// ## 注意
/// クリア画面のスクリーンショットは、パズルデータに `is_clear: true` の質問が
/// 設定されている必要があります。未設定の場合は test_screenshot_03 がスキップされます。
final class AppStoreScreenshotTests: XCTestCase {

    let app = XCUIApplication()

    /// 新規シミュレータの初回起動は時間がかかるため長めに設定
    private let elementTimeout: TimeInterval = 20

    // MARK: - 言語設定

    /// 言語を取得（一時ファイル → 環境変数 → デフォルト ja の順で確認）
    private var lang: String {
        // xcodebuild は環境変数をテストプロセスに転送しないため、
        // 一時ファイル経由で言語を受け取る
        if let fileLang = try? String(contentsOfFile: "/tmp/.screenshot_lang", encoding: .utf8) {
            let trimmed = fileLang.trimmingCharacters(in: .whitespacesAndNewlines)
            if !trimmed.isEmpty { return trimmed }
        }
        return ProcessInfo.processInfo.environment["SCREENSHOT_LANG"] ?? "ja"
    }

    /// パズル一覧・コンテンツダウンロード用パズル名
    private var listPuzzleTitle: String {
        lang == "en" ? "Turtle Soup" : "ウミガメのスープ"
    }

    /// ゲームフロー・クリア画面用パズル名
    /// 日本語: bar_man（質問が初期表示されるため撮影に適している）
    /// 英語: turtle_soup（bar_man が英語版に存在しないため）
    private var gamePuzzleTitle: String {
        lang == "en" ? "Turtle Soup" : "バーの男"
    }

    /// UI文字列: 出題ラベル
    private var statementLabel: String {
        lang == "en" ? "Statement" : "出題"
    }

    /// UI文字列: クリアラベル（真相画面のヘッダー）
    private var clearedLabel: String {
        lang == "en" ? "Truth" : "真相"
    }

    /// UI文字列: コンテンツナビゲーションバータイトル
    private var contentNavTitle: String {
        lang == "en" ? "Content" : "コンテンツ"
    }

    override func setUpWithError() throws {
        continueAfterFailure = true

        if lang == "en" {
            app.launchArguments += ["-AppleLanguages", "(en)", "-AppleLocale", "en_US"]
            app.launchArguments += ["-debug_languageOverride", "en"]
        } else {
            app.launchArguments += ["-AppleLanguages", "(ja)", "-AppleLocale", "ja_JP"]
            app.launchArguments += ["-debug_languageOverride", "ja"]
        }

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
        let puzzle = app.staticTexts[listPuzzleTitle]
        XCTAssertTrue(puzzle.waitForExistence(timeout: elementTimeout), "パズル一覧が表示されるべき")

        takeScreenshot("AppStore_01_PuzzleList")
    }

    // MARK: - 2〜4. ゲーム画面（初期 → フィードバック → 途中経過）

    func test_screenshot_02_gameFlow() throws {
        let puzzle = app.staticTexts[gamePuzzleTitle]
        XCTAssertTrue(puzzle.waitForExistence(timeout: elementTimeout))
        puzzle.tap()
        sleep(2)

        XCTAssertTrue(
            app.staticTexts[statementLabel].waitForExistence(timeout: elementTimeout),
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

    // MARK: - 5. 真相画面（クリア画面）
    // 注意: パズルデータに is_clear: true の質問が必要。
    // 未設定の場合、このテストはスキップされます。

    func test_screenshot_03_clearScreen() throws {
        let puzzle = app.staticTexts[gamePuzzleTitle]
        XCTAssertTrue(puzzle.waitForExistence(timeout: elementTimeout))
        puzzle.tap()
        sleep(2)

        // 全質問を回答
        for _ in 0..<30 {
            if app.staticTexts[clearedLabel].exists { break }
            if !tapQuestionWithScroll() { break }
            sleep(1)
        }

        let cleared = app.staticTexts[clearedLabel]
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
        let puzzle = app.staticTexts[listPuzzleTitle]
        XCTAssertTrue(puzzle.waitForExistence(timeout: elementTimeout))

        app.buttons["arrow.down.circle"].tap()

        XCTAssertTrue(
            app.navigationBars[contentNavTitle].waitForExistence(timeout: elementTimeout),
            "コンテンツ画面が表示されるべき"
        )

        takeScreenshot("AppStore_06_ContentDownload")

        // スクロールして全体を撮影
        app.swipeUp()
        sleep(1)
        takeScreenshot("AppStore_07_ContentDownload_Scrolled")
    }
}

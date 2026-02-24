import XCTest

final class ContentDownloadUITests: XCTestCase {

    let app = XCUIApplication()

    override func setUpWithError() throws {
        continueAfterFailure = true
        app.launchArguments += ["-AppleLanguages", "(ja)", "-AppleLocale", "ja_JP"]
        app.launch()
    }

    func test_contentDownloadPage_showsPacksAndPuzzles() throws {
        // 1. Puzzle list should load
        let barMan = app.staticTexts["バーの男"]
        XCTAssertTrue(barMan.waitForExistence(timeout: 5), "Puzzle list should load")

        // 2. Tap download button in toolbar
        let downloadButton = app.buttons["arrow.down.circle"]
        XCTAssertTrue(downloadButton.waitForExistence(timeout: 3), "Download button should exist in toolbar")
        downloadButton.tap()

        // 3. Verify content download page loaded
        let navTitle = app.navigationBars["コンテンツ"]
        XCTAssertTrue(navTitle.waitForExistence(timeout: 5), "Content download page should appear")

        let screenshot1 = app.screenshot()
        let attach1 = XCTAttachment(screenshot: screenshot1)
        attach1.name = "01_ContentDownload_Top"
        attach1.lifetime = .keepAlways
        add(attach1)

        // 4. Verify pack section
        let packsHeader = app.staticTexts["パック"]
        XCTAssertTrue(packsHeader.exists, "Packs section header should exist")

        let classicPack = app.staticTexts["定番パック"]
        XCTAssertTrue(classicPack.exists, "Classic pack should be listed")

        let mysteryPack = app.staticTexts["ミステリーパック"]
        XCTAssertTrue(mysteryPack.exists, "Mystery pack should be listed")

        // 5. Verify puzzle section
        let puzzlesHeader = app.staticTexts["パズル"]
        XCTAssertTrue(puzzlesHeader.exists, "Puzzles section header should exist")

        // Bundled puzzles
        let turtleSoup = app.staticTexts["ウミガメのスープ"]
        XCTAssertTrue(turtleSoup.exists, "Turtle soup should be listed")

        let bundledBadge = app.staticTexts["同梱済み"]
        XCTAssertTrue(bundledBadge.exists, "Bundled badge should appear for bundled puzzles")

        // DLC puzzles
        let underground = app.staticTexts["禁じられた地下室"]
        XCTAssertTrue(underground.exists, "Underground puzzle should be listed")

        // 6. Scroll down and screenshot
        app.swipeUp()
        sleep(1)

        let screenshot2 = app.screenshot()
        let attach2 = XCTAttachment(screenshot: screenshot2)
        attach2.name = "02_ContentDownload_Scrolled"
        attach2.lifetime = .keepAlways
        add(attach2)
    }
}

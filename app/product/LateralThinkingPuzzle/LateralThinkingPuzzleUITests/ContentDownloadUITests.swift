import XCTest

final class ContentDownloadUITests: XCTestCase {

    let app = XCUIApplication()

    override func setUpWithError() throws {
        continueAfterFailure = true
        app.launchArguments += ["-AppleLanguages", "(ja)", "-AppleLocale", "ja_JP"]
    }

    // MARK: - Page Display

    func test_contentDownloadPage_showsPacksAndPuzzles() throws {
        app.launch()

        let barMan = app.staticTexts["バーの男"]
        XCTAssertTrue(barMan.waitForExistence(timeout: 5))

        app.buttons["arrow.down.circle"].tap()

        let navTitle = app.navigationBars["コンテンツ"]
        XCTAssertTrue(navTitle.waitForExistence(timeout: 5))

        let screenshot1 = app.screenshot()
        let attach1 = XCTAttachment(screenshot: screenshot1)
        attach1.name = "01_ContentDownload_Top"
        attach1.lifetime = .keepAlways
        add(attach1)

        XCTAssertTrue(app.staticTexts["パック"].exists)
        XCTAssertTrue(app.staticTexts["定番パック"].exists)
        XCTAssertTrue(app.staticTexts["ミステリーパック"].exists)
        XCTAssertTrue(app.staticTexts["パズル"].exists)
        XCTAssertTrue(app.staticTexts["ウミガメのスープ"].exists)
        XCTAssertTrue(app.staticTexts["同梱済み"].exists)
        XCTAssertTrue(app.staticTexts["禁じられた地下室"].exists)

        app.swipeUp()
        sleep(1)

        let screenshot2 = app.screenshot()
        let attach2 = XCTAttachment(screenshot: screenshot2)
        attach2.name = "02_ContentDownload_Scrolled"
        attach2.lifetime = .keepAlways
        add(attach2)
    }

    // MARK: - Puzzle List Shows All Catalog Puzzles

    func test_puzzleList_showsDLCPuzzles() throws {
        app.launch()

        // Bundled puzzles should exist
        XCTAssertTrue(app.staticTexts["ウミガメのスープ"].waitForExistence(timeout: 5))
        XCTAssertTrue(app.staticTexts["バーの男"].exists)
        XCTAssertTrue(app.staticTexts["砂漠の男"].exists)

        // Scroll to see DLC puzzles
        app.swipeUp()
        sleep(1)

        // DLC puzzles should appear with "未ダウンロード" badge
        XCTAssertTrue(app.staticTexts["禁じられた地下室"].waitForExistence(timeout: 3),
                      "DLC puzzle should appear in puzzle list")
        XCTAssertTrue(app.staticTexts["未ダウンロード"].exists,
                      "Not downloaded badge should appear for DLC puzzles")

        let screenshot = app.screenshot()
        let attach = XCTAttachment(screenshot: screenshot)
        attach.name = "06_PuzzleList_WithDLC"
        attach.lifetime = .keepAlways
        add(attach)
    }

    // MARK: - Download Reflects in Puzzle List (Mock)

    func test_downloadedPuzzle_appearsAsPlayable() throws {
        app.launchArguments += ["--mock-downloads"]
        app.launch()

        // Verify DLC puzzle shows "未ダウンロード" initially
        app.swipeUp()
        sleep(1)
        XCTAssertTrue(app.staticTexts["禁じられた地下室"].waitForExistence(timeout: 3))

        // Navigate to content download page
        app.swipeDown()
        sleep(1)
        app.buttons["arrow.down.circle"].tap()
        XCTAssertTrue(app.navigationBars["コンテンツ"].waitForExistence(timeout: 5))

        // Download the puzzle
        app.swipeUp()
        let dlButton = app.buttons["download-underground"]
        XCTAssertTrue(dlButton.waitForExistence(timeout: 3))
        dlButton.tap()

        // Wait for download to complete
        let deleteButton = app.buttons["delete-underground"]
        XCTAssertTrue(deleteButton.waitForExistence(timeout: 5))

        // Go back to puzzle list
        app.navigationBars.buttons.element(boundBy: 0).tap()
        sleep(1)

        let screenshot = app.screenshot()
        let attach = XCTAttachment(screenshot: screenshot)
        attach.name = "07_PuzzleList_AfterDownload"
        attach.lifetime = .keepAlways
        add(attach)
    }

    // MARK: - Download & Delete (Mock)

    func test_downloadAndDelete_withMock() throws {
        app.launchArguments += ["--mock-downloads"]
        app.launch()

        // Navigate to content download page
        app.buttons["arrow.down.circle"].tap()
        XCTAssertTrue(app.navigationBars["コンテンツ"].waitForExistence(timeout: 5))

        // Scroll to DLC puzzles
        app.swipeUp()

        // Find download button for a specific DLC puzzle
        let dlButton = app.buttons["download-underground"]
        XCTAssertTrue(dlButton.waitForExistence(timeout: 3), "Download button should exist for DLC puzzle")

        let screenshotBefore = app.screenshot()
        let attachBefore = XCTAttachment(screenshot: screenshotBefore)
        attachBefore.name = "03_BeforeDownload"
        attachBefore.lifetime = .keepAlways
        add(attachBefore)

        // Tap download
        dlButton.tap()

        // Wait for download to complete (~1s mock)
        let deleteButton = app.buttons["delete-underground"]
        XCTAssertTrue(deleteButton.waitForExistence(timeout: 5), "Delete button should appear after download")

        let screenshotAfter = app.screenshot()
        let attachAfter = XCTAttachment(screenshot: screenshotAfter)
        attachAfter.name = "04_AfterDownload"
        attachAfter.lifetime = .keepAlways
        add(attachAfter)

        // Delete
        deleteButton.tap()

        // Should revert to download button
        let dlButtonAgain = app.buttons["download-underground"]
        XCTAssertTrue(dlButtonAgain.waitForExistence(timeout: 3), "Download button should reappear after delete")

        let screenshotDeleted = app.screenshot()
        let attachDeleted = XCTAttachment(screenshot: screenshotDeleted)
        attachDeleted.name = "05_AfterDelete"
        attachDeleted.lifetime = .keepAlways
        add(attachDeleted)
    }
}

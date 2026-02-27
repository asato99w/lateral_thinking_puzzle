import XCTest

final class GameFlowUITests: XCTestCase {

    let app = XCUIApplication()

    override func setUpWithError() throws {
        continueAfterFailure = true
        // Force Japanese locale so manifest resolves to ja/
        app.launchArguments += ["-AppleLanguages", "(ja)", "-AppleLocale", "ja_JP"]
        app.launch()
    }

    // MARK: - Topic Category Tab Bar

    func test_turtleSoup_showsCategoryTabs() throws {
        // 1. Enter ウミガメのスープ game
        let turtleSoup = app.staticTexts["ウミガメのスープ"]
        XCTAssertTrue(turtleSoup.waitForExistence(timeout: 5), "ウミガメのスープ should appear in puzzle list")
        turtleSoup.tap()
        sleep(2)

        // 2. Verify category tab "すべて" exists
        let allTab = app.buttons.containing(NSPredicate(format: "label CONTAINS %@", "すべて")).firstMatch
        XCTAssertTrue(allTab.waitForExistence(timeout: 3), "'すべて' category tab should appear")

        // 3. Verify at least one real category tab
        let catA = app.buttons.containing(NSPredicate(format: "label CONTAINS %@", "レストラン")).firstMatch
        XCTAssertTrue(catA.exists, "Category A tab should appear")

        let screenshot1 = app.screenshot()
        let attach1 = XCTAttachment(screenshot: screenshot1)
        attach1.name = "CategoryTab_01_AllSelected"
        attach1.lifetime = .keepAlways
        add(attach1)

        // 4. Tap a category tab to filter
        catA.tap()
        sleep(1)

        let screenshot2 = app.screenshot()
        let attach2 = XCTAttachment(screenshot: screenshot2)
        attach2.name = "CategoryTab_02_FilteredByA"
        attach2.lifetime = .keepAlways
        add(attach2)

        // 5. Tap "すべて" to reset filter
        allTab.tap()
        sleep(1)

        let screenshot3 = app.screenshot()
        let attach3 = XCTAttachment(screenshot: screenshot3)
        attach3.name = "CategoryTab_03_ResetToAll"
        attach3.lifetime = .keepAlways
        add(attach3)
    }

    func test_barMan_showsCategoryTabs() throws {
        // 1. Enter バーの男 game
        let barMan = app.staticTexts["バーの男"]
        XCTAssertTrue(barMan.waitForExistence(timeout: 5), "バーの男 should appear in puzzle list")
        barMan.tap()
        sleep(2)

        // 2. Verify game loaded
        let statementHeader = app.staticTexts["出題"]
        XCTAssertTrue(statementHeader.waitForExistence(timeout: 5), "Statement header should appear")

        // 3. Verify "すべて" tab exists (bar_man now has topic_categories)
        let allTab = app.buttons.containing(NSPredicate(format: "label CONTAINS %@", "すべて")).firstMatch
        XCTAssertTrue(allTab.waitForExistence(timeout: 3), "'すべて' category tab should appear for bar_man")

        // 4. Verify a real category tab
        let catI = app.buttons.containing(NSPredicate(format: "label CONTAINS %@", "日常の理解")).firstMatch
        XCTAssertTrue(catI.exists, "Category '日常の理解' tab should appear")

        let screenshot = app.screenshot()
        let attach = XCTAttachment(screenshot: screenshot)
        attach.name = "BarMan_CategoryTabs"
        attach.lifetime = .keepAlways
        add(attach)
    }

    // MARK: - Full Game Flow

    func test_fullGameFlow_puzzleListToGameToAnswering() throws {
        // 1. Puzzle list should show "バーの男"
        let barManCell = app.staticTexts["バーの男"]
        XCTAssertTrue(barManCell.waitForExistence(timeout: 5), "バーの男 should appear in puzzle list")

        let listScreenshot = app.screenshot()
        let listAttachment = XCTAttachment(screenshot: listScreenshot)
        listAttachment.name = "01_PuzzleList"
        listAttachment.lifetime = .keepAlways
        add(listAttachment)

        // 2. Tap to enter game
        barManCell.tap()
        sleep(2)

        // 3. Take game screen screenshot
        let gameScreenshot = app.screenshot()
        let gameAttachment = XCTAttachment(screenshot: gameScreenshot)
        gameAttachment.name = "02_GameScreen"
        gameAttachment.lifetime = .keepAlways
        add(gameAttachment)

        // 4. Verify game screen loaded
        let statementHeader = app.staticTexts["出題"]
        XCTAssertTrue(statementHeader.waitForExistence(timeout: 5), "出題 header should appear")

        let questionsHeader = app.staticTexts["質問を選んでください"]
        XCTAssertTrue(questionsHeader.waitForExistence(timeout: 3), "Questions section should appear")

        // 5. Find and tap a question button
        let allButtons = app.buttons
        if allButtons.count > 0 {
            let questionButton = allButtons.element(boundBy: allButtons.count > 1 ? 1 : 0)
            if questionButton.exists {
                questionButton.tap()
                sleep(1)

                let afterAnswerScreenshot = app.screenshot()
                let afterAnswerAttachment = XCTAttachment(screenshot: afterAnswerScreenshot)
                afterAnswerAttachment.name = "03_AfterAnswer"
                afterAnswerAttachment.lifetime = .keepAlways
                add(afterAnswerAttachment)
            }

            let remainingButtons = app.buttons
            if remainingButtons.count > 1 {
                let nextButton = remainingButtons.element(boundBy: remainingButtons.count > 1 ? 1 : 0)
                if nextButton.exists {
                    nextButton.tap()
                    sleep(1)

                    let afterSecondScreenshot = app.screenshot()
                    let afterSecondAttachment = XCTAttachment(screenshot: afterSecondScreenshot)
                    afterSecondAttachment.name = "04_AfterSecondAnswer"
                    afterSecondAttachment.lifetime = .keepAlways
                    add(afterSecondAttachment)
                }
            }
        }
    }
}

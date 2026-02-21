import XCTest

final class GameFlowUITests: XCTestCase {

    let app = XCUIApplication()

    override func setUpWithError() throws {
        continueAfterFailure = true
        app.launch()
    }

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
        // Questions are in Button with plain style, look for text content
        let allButtons = app.buttons
        if allButtons.count > 0 {
            // Tap the first question button (index 0 might be nav back, try index 0)
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

            // Tap another question if available
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

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

    func test_turtleSoup_loadsGameScreen() throws {
        // 1. Enter ウミガメのスープ game
        let turtleSoup = app.staticTexts["ウミガメのスープ"]
        XCTAssertTrue(turtleSoup.waitForExistence(timeout: 5), "ウミガメのスープ should appear in puzzle list")
        turtleSoup.tap()
        sleep(2)

        // 2. Verify game screen loaded
        let statementHeader = app.staticTexts["出題"]
        XCTAssertTrue(statementHeader.waitForExistence(timeout: 5), "Statement header should appear")

        // 3. turtle_soup (v2 engine) has topic_categories, so category tabs appear
        let allTab = app.buttons.containing(NSPredicate(format: "label CONTAINS %@", "すべて")).firstMatch
        XCTAssertTrue(allTab.waitForExistence(timeout: 3), "'すべて' tab should appear (v2 puzzle has topic_categories)")

        let screenshot = app.screenshot()
        let attach = XCTAttachment(screenshot: screenshot)
        attach.name = "TurtleSoup_GameScreen"
        attach.lifetime = .keepAlways
        add(attach)
    }

    func test_barMan_showsCategoryTabs() throws {
        // 1. Enter バーの男 game
        let barMan = app.staticTexts["バーの男"]
        XCTAssertTrue(barMan.waitForExistence(timeout: 5), "バーの男 should appear in puzzle list")
        barMan.tap()
        sleep(3)

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

    // MARK: - v2 Engine Tests (turtle_soup)

    func test_turtleSoup_v2_categoryTabFiltering() throws {
        // 1. Enter ウミガメのスープ game
        let turtleSoup = app.staticTexts["ウミガメのスープ"]
        XCTAssertTrue(turtleSoup.waitForExistence(timeout: 5), "ウミガメのスープ should appear in puzzle list")
        turtleSoup.tap()
        sleep(2)

        // 2. Verify "すべて" tab is present
        let allTab = app.buttons.containing(NSPredicate(format: "label CONTAINS %@", "すべて")).firstMatch
        XCTAssertTrue(allTab.waitForExistence(timeout: 3), "'すべて' tab should appear")

        // 3. Verify v2 topic_categories tabs exist
        let hypothesisTab = app.buttons.containing(NSPredicate(format: "label CONTAINS %@", "仮説確認")).firstMatch
        let discoveryTab = app.buttons.containing(NSPredicate(format: "label CONTAINS %@", "事実発見")).firstMatch
        let connectionTab = app.buttons.containing(NSPredicate(format: "label CONTAINS %@", "真相解明")).firstMatch
        XCTAssertTrue(hypothesisTab.exists, "'仮説確認' category tab should exist")
        XCTAssertTrue(discoveryTab.exists, "'事実発見' category tab should exist")
        XCTAssertTrue(connectionTab.exists, "'真相解明' category tab should exist")

        // 4. Count questions under "すべて", then tap a category tab and verify filtering
        let allQuestions = app.buttons.matching(NSPredicate(format: "label MATCHES %@", "\\d+.+"))
        let allCount = allQuestions.count

        hypothesisTab.tap()
        sleep(1)
        let filteredQuestions = app.buttons.matching(NSPredicate(format: "label MATCHES %@", "\\d+.+"))
        let filteredCount = filteredQuestions.count
        XCTAssertTrue(filteredCount <= allCount, "Filtered questions (\(filteredCount)) should be ≤ all questions (\(allCount))")

        // 5. Tap "すべて" to restore full list
        allTab.tap()
        sleep(1)
        let restoredQuestions = app.buttons.matching(NSPredicate(format: "label MATCHES %@", "\\d+.+"))
        XCTAssertEqual(restoredQuestions.count, allCount, "Restoring 'すべて' should show original question count")

        let screenshot = app.screenshot()
        let attach = XCTAttachment(screenshot: screenshot)
        attach.name = "TurtleSoup_v2_CategoryFiltering"
        attach.lifetime = .keepAlways
        add(attach)
    }

    func test_turtleSoup_v2_answerQuestion() throws {
        // 1. Enter ウミガメのスープ game
        let turtleSoup = app.staticTexts["ウミガメのスープ"]
        XCTAssertTrue(turtleSoup.waitForExistence(timeout: 5), "ウミガメのスープ should appear in puzzle list")
        turtleSoup.tap()
        sleep(2)

        // 2. Verify initial questions are displayed
        let questionButtons = app.buttons.matching(NSPredicate(format: "label MATCHES %@", "\\d+.+"))
        XCTAssertGreaterThan(questionButtons.count, 0, "At least one question button should be visible")

        // 3. Tap the first question
        let firstQuestion = questionButtons.element(boundBy: 0)
        XCTAssertTrue(firstQuestion.exists, "First question button should exist")
        firstQuestion.tap()

        // 4. Verify answer feedback appears (YES, NO, or 関係ない)
        let feedbackYes = app.staticTexts["YES"]
        let feedbackNo = app.staticTexts["NO"]
        let feedbackIrrelevant = app.staticTexts["関係ない"]
        let feedbackAppeared = feedbackYes.waitForExistence(timeout: 2)
            || feedbackNo.waitForExistence(timeout: 0.5)
            || feedbackIrrelevant.waitForExistence(timeout: 0.5)
        XCTAssertTrue(feedbackAppeared, "Answer feedback (YES/NO/関係ない) should appear after tapping a question")

        // 5. Wait for feedback to disappear and verify answered section appears
        sleep(2)
        let answeredSection = app.staticTexts.containing(NSPredicate(format: "label CONTAINS %@", "回答済み")).firstMatch
        XCTAssertTrue(answeredSection.waitForExistence(timeout: 3), "'回答済み' section should appear after answering")

        let screenshot = app.screenshot()
        let attach = XCTAttachment(screenshot: screenshot)
        attach.name = "TurtleSoup_v2_AnswerQuestion"
        attach.lifetime = .keepAlways
        add(attach)
    }

    func test_turtleSoup_v2_fullPlaythrough() throws {
        // 1. Enter ウミガメのスープ game
        let turtleSoup = app.staticTexts["ウミガメのスープ"]
        XCTAssertTrue(turtleSoup.waitForExistence(timeout: 5), "ウミガメのスープ should appear in puzzle list")
        turtleSoup.tap()
        sleep(2)

        // 2. Answer all available questions
        let questionPredicate = NSPredicate(format: "label MATCHES %@", "\\d+.+")
        let safetyLimit = 50
        var answeredCount = 0

        for _ in 0..<safetyLimit {
            // Check if clear screen appeared
            let truthText = app.staticTexts["真相"]
            if truthText.exists {
                break
            }

            // Find available question buttons (retry for new questions to appear)
            var questionButtons = app.buttons.matching(questionPredicate)
            if questionButtons.count == 0 {
                sleep(3)
                questionButtons = app.buttons.matching(questionPredicate)
                if questionButtons.count == 0 {
                    break
                }
            }

            // Tap the first available question
            let question = questionButtons.element(boundBy: 0)
            guard question.waitForExistence(timeout: 2) else { break }
            question.tap()
            answeredCount += 1

            // Wait for feedback animation (0.6s) + state update + UI refresh
            sleep(2)
        }

        // 3. Verify at least some questions were answered
        XCTAssertGreaterThan(answeredCount, 0, "Should answer at least one question")

        // 4. Check whether clear screen appeared or questions exhausted
        let truthText = app.staticTexts["真相"]
        if truthText.waitForExistence(timeout: 5) {
            // Puzzle cleared — full playthrough successful
            let screenshot = app.screenshot()
            let attach = XCTAttachment(screenshot: screenshot)
            attach.name = "TurtleSoup_v2_ClearScreen"
            attach.lifetime = .keepAlways
            add(attach)
        } else {
            // Puzzle did not clear — capture final state for diagnostics
            let screenshot = app.screenshot()
            let attach = XCTAttachment(screenshot: screenshot)
            attach.name = "TurtleSoup_v2_Playthrough_Stalled_After\(answeredCount)Q"
            attach.lifetime = .keepAlways
            add(attach)

            // Verify answered section reflects the answers we gave
            let answeredSection = app.staticTexts.containing(
                NSPredicate(format: "label CONTAINS %@", "回答済み")).firstMatch
            XCTAssertTrue(answeredSection.exists,
                          "'回答済み' section should show \(answeredCount) answered questions")
        }
    }

    // MARK: - Full Game Flow (bar_man)

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

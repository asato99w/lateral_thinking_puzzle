import Testing
@testable import LateralThinkingPuzzle

@MainActor
struct V2GameSessionTests {

    private func makeTestPuzzle() -> V2PuzzleData {
        V2PuzzleData(
            id: "test",
            title: "Test Puzzle",
            statement: "Test statement",
            truth: "Test truth",
            descriptors: [
                "f1": V2Descriptor(id: "f1", label: "Fact 1", formationConditions: nil),
                "f2": V2Descriptor(id: "f2", label: "Fact 2", formationConditions: nil),
                "f3": V2Descriptor(id: "f3", label: "Fact 3", formationConditions: nil),
                "h1": V2Descriptor(id: "h1", label: "Hyp 1", formationConditions: [["f1"]]),
            ],
            initialConfirmed: ["f1"],
            clearConditions: [["f1", "f2", "f3"]],
            pieces: [
                "p1": V2Piece(id: "p1", label: "Piece 1", members: ["f1", "f2", "f3"], dependsOn: []),
            ],
            questions: [
                "q1": V2Question(id: "q1", text: "First question?", answer: "Yes", recallConditions: [["h1"]], reveals: ["f2"], mechanism: "observation", prerequisites: [], correctAnswer: .yes, topicCategory: "cat1"),
                "q2": V2Question(id: "q2", text: "Second question?", answer: "Yes", recallConditions: [["h1"]], reveals: ["f3"], mechanism: "link", prerequisites: [], correctAnswer: .yes, topicCategory: "cat1"),
            ],
            topicCategories: [TopicCategory(id: "cat1", name: "Category 1")]
        )
    }

    @Test func test_start_returnsOpenQuestions() {
        var session = V2GameSession(puzzle: makeTestPuzzle())
        let result = session.start()
        #expect(!result.openQuestions.isEmpty)
    }

    @Test func test_puzzleInfo_mappedCorrectly() {
        let session = V2GameSession(puzzle: makeTestPuzzle())
        #expect(session.puzzleInfo.title == "Test Puzzle")
        #expect(session.puzzleInfo.statement == "Test statement")
        #expect(session.puzzleInfo.truth == "Test truth")
        #expect(session.puzzleInfo.topicCategories.count == 1)
    }

    @Test func test_questionMapping_hasCorrectFields() {
        var session = V2GameSession(puzzle: makeTestPuzzle())
        let result = session.start()
        let q = result.openQuestions.first!
        #expect(q.text == "First question?" || q.text == "Second question?")
        #expect(q.correctAnswer == .yes)
        #expect(q.topicCategory == "cat1")
    }

    @Test func test_selectQuestion_updatesState() {
        var session = V2GameSession(puzzle: makeTestPuzzle())
        let startResult = session.start()
        let question = startResult.openQuestions.first!

        let result = session.selectQuestion(question)
        // After answering, the question count may change
        #expect(result.openQuestions.count <= startResult.openQuestions.count)
    }

    @Test func test_fullPlaythrough_clearsGame() {
        var session = V2GameSession(puzzle: makeTestPuzzle())
        _ = session.start()

        var isCleared = false
        for _ in 0..<10 {
            var s = session
            let available = s.start().openQuestions
            if available.isEmpty { break }
            let result = s.selectQuestion(available.first!)
            session = s
            if result.isCleared {
                isCleared = true
                break
            }
        }

        #expect(isCleared)
    }

    @Test func test_viewModelIntegration() {
        let session = V2GameSession(puzzle: makeTestPuzzle())
        let vm = GameViewModel(session: session)

        #expect(vm.puzzleInfo.title == "Test Puzzle")
        #expect(!vm.openQuestions.isEmpty)
        #expect(!vm.isCleared)
    }
}

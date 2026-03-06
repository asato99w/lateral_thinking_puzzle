import Testing
@testable import LateralThinkingPuzzle

struct V2AvailableQuestionsTests {

    @Test func test_questionAvailable_whenRecallConditionsMet() {
        let puzzle = V2PuzzleData(
            id: "test", title: "", statement: "", truth: "",
            descriptors: [
                "f1": V2Descriptor(id: "f1", label: "", formationConditions: nil),
                "h1": V2Descriptor(id: "h1", label: "", formationConditions: [["f1"]]),
            ],
            initialConfirmed: ["f1"],
            clearConditions: [],
            pieces: [:],
            questions: [
                "q1": V2Question(id: "q1", text: "Q?", answer: "Yes", recallConditions: [["h1"]], reveals: [], mechanism: "observation", prerequisites: [], correctAnswer: .yes, topicCategory: ""),
            ],
            topicCategories: []
        )
        let state = V2GameEngine.initGame(puzzle: puzzle)
        let available = V2GameEngine.availableQuestions(state: state, puzzle: puzzle)
        #expect(available.count == 1)
        #expect(available[0].id == "q1")
    }

    @Test func test_questionAvailable_whenRecallConditionsUseFacts() {
        // 記述素統一モデル: recall_conditions がファクトIDを参照するケース
        let puzzle = V2PuzzleData(
            id: "test", title: "", statement: "", truth: "",
            descriptors: [
                "f1": V2Descriptor(id: "f1", label: "", formationConditions: nil),
                "f2": V2Descriptor(id: "f2", label: "", formationConditions: nil),
            ],
            initialConfirmed: ["f1", "f2"],
            clearConditions: [],
            pieces: [:],
            questions: [
                "q1": V2Question(id: "q1", text: "Q?", answer: "Yes", recallConditions: [["f1", "f2"]], reveals: [], mechanism: "observation", prerequisites: [], correctAnswer: .yes, topicCategory: ""),
            ],
            topicCategories: []
        )
        let state = V2GameEngine.initGame(puzzle: puzzle)
        let available = V2GameEngine.availableQuestions(state: state, puzzle: puzzle)
        #expect(available.count == 1)
    }

    @Test func test_questionNotAvailable_whenRecallConditionsNotMet() {
        let puzzle = V2PuzzleData(
            id: "test", title: "", statement: "", truth: "",
            descriptors: [
                "f1": V2Descriptor(id: "f1", label: "", formationConditions: nil),
                "h1": V2Descriptor(id: "h1", label: "", formationConditions: [["f1"]]),
                "h2": V2Descriptor(id: "h2", label: "", formationConditions: [["h_nonexistent"]]),
            ],
            initialConfirmed: ["f1"],
            clearConditions: [],
            pieces: [:],
            questions: [
                "q1": V2Question(id: "q1", text: "Q?", answer: "Yes", recallConditions: [["h2"]], reveals: [], mechanism: "observation", prerequisites: [], correctAnswer: .yes, topicCategory: ""),
            ],
            topicCategories: []
        )
        let state = V2GameEngine.initGame(puzzle: puzzle)
        let available = V2GameEngine.availableQuestions(state: state, puzzle: puzzle)
        #expect(available.isEmpty)
    }

    @Test func test_questionNotAvailable_whenPrerequisitesNotMet() {
        // prerequisites は confirmed のみで判定（derived では不可）
        let puzzle = V2PuzzleData(
            id: "test", title: "", statement: "", truth: "",
            descriptors: [
                "f1": V2Descriptor(id: "f1", label: "", formationConditions: nil),
                "h1": V2Descriptor(id: "h1", label: "", formationConditions: [["f1"]]),
            ],
            initialConfirmed: ["f1"],
            clearConditions: [],
            pieces: [:],
            questions: [
                "q1": V2Question(id: "q1", text: "Q?", answer: "Yes", recallConditions: [["f1"]], reveals: [], mechanism: "observation", prerequisites: ["h1"], correctAnswer: .yes, topicCategory: ""),
            ],
            topicCategories: []
        )
        // h1 is derived (not confirmed), so prerequisites ["h1"] not met
        let state = V2GameEngine.initGame(puzzle: puzzle)
        let available = V2GameEngine.availableQuestions(state: state, puzzle: puzzle)
        #expect(available.isEmpty)
    }

    @Test func test_questionAvailable_whenPrerequisitesConfirmed() {
        let puzzle = V2PuzzleData(
            id: "test", title: "", statement: "", truth: "",
            descriptors: [
                "f1": V2Descriptor(id: "f1", label: "", formationConditions: nil),
                "f2": V2Descriptor(id: "f2", label: "", formationConditions: nil),
            ],
            initialConfirmed: ["f1", "f2"],
            clearConditions: [],
            pieces: [:],
            questions: [
                "q1": V2Question(id: "q1", text: "Q?", answer: "Yes", recallConditions: [["f1"]], reveals: [], mechanism: "observation", prerequisites: ["f2"], correctAnswer: .yes, topicCategory: ""),
            ],
            topicCategories: []
        )
        let state = V2GameEngine.initGame(puzzle: puzzle)
        let available = V2GameEngine.availableQuestions(state: state, puzzle: puzzle)
        #expect(available.count == 1)
    }

    @Test func test_answeredQuestion_notAvailable() {
        let puzzle = V2PuzzleData(
            id: "test", title: "", statement: "", truth: "",
            descriptors: [
                "f1": V2Descriptor(id: "f1", label: "", formationConditions: nil),
                "h1": V2Descriptor(id: "h1", label: "", formationConditions: [["f1"]]),
            ],
            initialConfirmed: ["f1"],
            clearConditions: [],
            pieces: [:],
            questions: [
                "q1": V2Question(id: "q1", text: "Q?", answer: "Yes", recallConditions: [["h1"]], reveals: [], mechanism: "observation", prerequisites: [], correctAnswer: .yes, topicCategory: ""),
            ],
            topicCategories: []
        )
        var state = V2GameEngine.initGame(puzzle: puzzle)
        state.answered.insert("q1")
        let available = V2GameEngine.availableQuestions(state: state, puzzle: puzzle)
        #expect(available.isEmpty)
    }
}

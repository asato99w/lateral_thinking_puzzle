import Testing
@testable import LateralThinkingPuzzle

struct V2AvailableQuestionsTests {

    @Test func test_questionAvailable_whenRecallConditionsMet() {
        let puzzle = V2PuzzleData(
            id: "test", title: "", statement: "", truth: "",
            facts: ["f1": V2Fact(id: "f1", label: "")],
            initialFacts: ["f1"],
            pieces: [:],
            hypotheses: [
                "h1": V2Hypothesis(id: "h1", label: "", formationConditions: [["f1"]]),
            ],
            questions: [
                "q1": V2Question(id: "q1", text: "Q?", answer: "Yes", recallConditions: [["h1"]], reveals: [], mechanism: "observation", correctAnswer: .yes, topicCategory: ""),
            ],
            topicCategories: []
        )
        let state = V2GameEngine.initGame(puzzle: puzzle)
        let available = V2GameEngine.availableQuestions(state: state, puzzle: puzzle)
        #expect(available.count == 1)
        #expect(available[0].id == "q1")
    }

    @Test func test_questionNotAvailable_whenRecallConditionsNotMet() {
        let puzzle = V2PuzzleData(
            id: "test", title: "", statement: "", truth: "",
            facts: ["f1": V2Fact(id: "f1", label: "")],
            initialFacts: ["f1"],
            pieces: [:],
            hypotheses: [
                "h1": V2Hypothesis(id: "h1", label: "", formationConditions: [["f1"]]),
                "h2": V2Hypothesis(id: "h2", label: "", formationConditions: [["h_nonexistent"]]),
            ],
            questions: [
                "q1": V2Question(id: "q1", text: "Q?", answer: "Yes", recallConditions: [["h2"]], reveals: [], mechanism: "observation", correctAnswer: .yes, topicCategory: ""),
            ],
            topicCategories: []
        )
        let state = V2GameEngine.initGame(puzzle: puzzle)
        let available = V2GameEngine.availableQuestions(state: state, puzzle: puzzle)
        #expect(available.isEmpty)
    }

    @Test func test_answeredQuestion_notAvailable() {
        let puzzle = V2PuzzleData(
            id: "test", title: "", statement: "", truth: "",
            facts: ["f1": V2Fact(id: "f1", label: "")],
            initialFacts: ["f1"],
            pieces: [:],
            hypotheses: [
                "h1": V2Hypothesis(id: "h1", label: "", formationConditions: [["f1"]]),
            ],
            questions: [
                "q1": V2Question(id: "q1", text: "Q?", answer: "Yes", recallConditions: [["h1"]], reveals: [], mechanism: "observation", correctAnswer: .yes, topicCategory: ""),
            ],
            topicCategories: []
        )
        var state = V2GameEngine.initGame(puzzle: puzzle)
        state.answered.insert("q1")
        let available = V2GameEngine.availableQuestions(state: state, puzzle: puzzle)
        #expect(available.isEmpty)
    }
}

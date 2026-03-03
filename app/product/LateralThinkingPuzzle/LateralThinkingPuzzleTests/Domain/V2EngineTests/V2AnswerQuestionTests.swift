import Testing
@testable import LateralThinkingPuzzle

struct V2AnswerQuestionTests {

    @Test func test_answerQuestion_confirmsDescriptors() {
        let puzzle = V2PuzzleData(
            id: "test", title: "", statement: "", truth: "",
            descriptors: [
                "f1": V2Descriptor(id: "f1", label: "", formationConditions: nil),
                "f2": V2Descriptor(id: "f2", label: "", formationConditions: nil),
                "h1": V2Descriptor(id: "h1", label: "", formationConditions: [["f1"]]),
            ],
            initialConfirmed: ["f1"],
            clearConditions: [],
            pieces: [:],
            questions: [
                "q1": V2Question(id: "q1", text: "Q?", answer: "Yes", recallConditions: [["h1"]], reveals: ["f2"], mechanism: "observation", correctAnswer: .yes, topicCategory: ""),
            ],
            topicCategories: []
        )
        var state = V2GameEngine.initGame(puzzle: puzzle)
        let q = puzzle.questions["q1"]!
        let result = V2GameEngine.answerQuestion(state: &state, question: q, puzzle: puzzle)
        #expect(result.newConfirmed.contains("f2"))
        #expect(state.confirmed.contains("f2"))
    }

    @Test func test_answerQuestion_marksAnswered() {
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
                "q1": V2Question(id: "q1", text: "Q?", answer: "Yes", recallConditions: [["h1"]], reveals: [], mechanism: "observation", correctAnswer: .yes, topicCategory: ""),
            ],
            topicCategories: []
        )
        var state = V2GameEngine.initGame(puzzle: puzzle)
        let q = puzzle.questions["q1"]!
        _ = V2GameEngine.answerQuestion(state: &state, question: q, puzzle: puzzle)
        #expect(state.answered.contains("q1"))
    }

    @Test func test_answerQuestion_discoversPiece_whenMembersAndDepsComplete() {
        let puzzle = V2PuzzleData(
            id: "test", title: "", statement: "", truth: "",
            descriptors: [
                "f1": V2Descriptor(id: "f1", label: "", formationConditions: nil),
                "f2": V2Descriptor(id: "f2", label: "", formationConditions: nil),
                "h1": V2Descriptor(id: "h1", label: "", formationConditions: [["f1"]]),
            ],
            initialConfirmed: ["f1"],
            clearConditions: [],
            pieces: [
                "p1": V2Piece(id: "p1", label: "Piece", members: ["f1", "f2"], dependsOn: []),
            ],
            questions: [
                "q1": V2Question(id: "q1", text: "Q?", answer: "Yes", recallConditions: [["h1"]], reveals: ["f2"], mechanism: "observation", correctAnswer: .yes, topicCategory: ""),
            ],
            topicCategories: []
        )
        var state = V2GameEngine.initGame(puzzle: puzzle)
        let q = puzzle.questions["q1"]!
        let result = V2GameEngine.answerQuestion(state: &state, question: q, puzzle: puzzle)
        #expect(result.newPieces.contains("p1"))
        #expect(state.discoveredPieces.contains("p1"))
    }

    @Test func test_answerQuestion_pieceNotDiscovered_whenDependencyMissing() {
        let puzzle = V2PuzzleData(
            id: "test", title: "", statement: "", truth: "",
            descriptors: [
                "f1": V2Descriptor(id: "f1", label: "", formationConditions: nil),
                "f2": V2Descriptor(id: "f2", label: "", formationConditions: nil),
                "h1": V2Descriptor(id: "h1", label: "", formationConditions: [["f1"]]),
            ],
            initialConfirmed: ["f1"],
            clearConditions: [],
            pieces: [
                "p_dep": V2Piece(id: "p_dep", label: "Dep", members: ["f2"], dependsOn: []),
                "p1": V2Piece(id: "p1", label: "Piece", members: ["f1"], dependsOn: ["p_dep"]),
            ],
            questions: [
                "q1": V2Question(id: "q1", text: "Q?", answer: "Yes", recallConditions: [["h1"]], reveals: [], mechanism: "observation", correctAnswer: .yes, topicCategory: ""),
            ],
            topicCategories: []
        )
        var state = V2GameEngine.initGame(puzzle: puzzle)
        let q = puzzle.questions["q1"]!
        let result = V2GameEngine.answerQuestion(state: &state, question: q, puzzle: puzzle)
        // p1 has all members (f1) but dependency p_dep is not discovered (needs f2)
        #expect(!result.newPieces.contains("p1"))
    }
}

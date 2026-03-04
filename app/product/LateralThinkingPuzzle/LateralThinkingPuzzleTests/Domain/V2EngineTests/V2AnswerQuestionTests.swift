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

    @Test func test_answerQuestion_discoversPiece_whenDerivedMemberCompletesPiece() {
        // ピースの members に derived 記述素が含まれるケース
        let puzzle = V2PuzzleData(
            id: "test", title: "", statement: "", truth: "",
            descriptors: [
                "f1": V2Descriptor(id: "f1", label: "", formationConditions: nil),
                "f2": V2Descriptor(id: "f2", label: "", formationConditions: nil),
                "h1": V2Descriptor(id: "h1", label: "", formationConditions: [["f1"]]),
                "h2": V2Descriptor(id: "h2", label: "", formationConditions: [["f1", "f2"]]),
            ],
            initialConfirmed: ["f1"],
            clearConditions: [],
            pieces: [
                // ピースの members に derived 記述素 h2 を含む
                "p1": V2Piece(id: "p1", label: "Piece", members: ["f1", "h2"], dependsOn: []),
            ],
            questions: [
                "q1": V2Question(id: "q1", text: "Q?", answer: "Yes", recallConditions: [["h1"]], reveals: ["f2"], mechanism: "observation", correctAnswer: .yes, topicCategory: ""),
            ],
            topicCategories: []
        )
        var state = V2GameEngine.initGame(puzzle: puzzle)
        let q = puzzle.questions["q1"]!
        let result = V2GameEngine.answerQuestion(state: &state, question: q, puzzle: puzzle)
        // h2 は f1+f2 から derived される → known に含まれる → ピース発見
        #expect(result.newPieces.contains("p1"))
        #expect(state.discoveredPieces.contains("p1"))
    }

    @Test func test_answerQuestion_returnsNewRejected() {
        // 質問回答で棄却が発生するケース
        let puzzle = V2PuzzleData(
            id: "test", title: "", statement: "", truth: "",
            descriptors: [
                "f1": V2Descriptor(id: "f1", label: "", formationConditions: nil),
                "f2": V2Descriptor(id: "f2", label: "", formationConditions: nil),
                "h1": V2Descriptor(id: "h1", label: "", formationConditions: [["f1"]]),
                "h_rej": V2Descriptor(id: "h_rej", label: "", formationConditions: [["f1"]], rejectionConditions: [["f2"]]),
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
        // initGame 後、h_rej は derived に入っている
        #expect(state.derived.contains("h_rej"))

        let q = puzzle.questions["q1"]!
        let result = V2GameEngine.answerQuestion(state: &state, question: q, puzzle: puzzle)
        // f2 が confirmed されたことで h_rej が棄却される
        #expect(result.newRejected.contains("h_rej"))
        #expect(!state.derived.contains("h_rej"))
    }
}

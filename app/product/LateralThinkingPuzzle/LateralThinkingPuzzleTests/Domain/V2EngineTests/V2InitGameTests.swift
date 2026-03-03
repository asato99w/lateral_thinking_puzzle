import Testing
@testable import LateralThinkingPuzzle

struct V2InitGameTests {

    private func makeMinimalPuzzle() -> V2PuzzleData {
        V2PuzzleData(
            id: "test",
            title: "Test",
            statement: "Test statement",
            truth: "Test truth",
            facts: [
                "f1": V2Fact(id: "f1", label: "Fact 1"),
                "f2": V2Fact(id: "f2", label: "Fact 2"),
                "f3": V2Fact(id: "f3", label: "Fact 3"),
            ],
            initialFacts: ["f1", "f2"],
            pieces: [
                "p1": V2Piece(id: "p1", label: "Piece 1", facts: ["f3"], dependsOn: []),
            ],
            hypotheses: [
                "h1": V2Hypothesis(id: "h1", label: "Hyp 1", formationConditions: [["f1", "f2"]]),
            ],
            questions: [
                "q1": V2Question(id: "q1", text: "Q1?", answer: "Yes", recallConditions: [["h1"]], reveals: ["f3"], mechanism: "observation", correctAnswer: .yes, topicCategory: ""),
            ],
            topicCategories: []
        )
    }

    @Test func test_initGame_setsInitialFacts() {
        let puzzle = makeMinimalPuzzle()
        let state = V2GameEngine.initGame(puzzle: puzzle)
        #expect(state.observedFacts.contains("f1"))
        #expect(state.observedFacts.contains("f2"))
        #expect(!state.observedFacts.contains("f3"))
    }

    @Test func test_initGame_evaluatesHypothesesFromInitialFacts() {
        let puzzle = makeMinimalPuzzle()
        let state = V2GameEngine.initGame(puzzle: puzzle)
        // h1 has formation_conditions [["f1", "f2"]] — both are initial facts
        #expect(state.formedHypotheses.contains("h1"))
    }

    @Test func test_initGame_emptyDiscoveredPieces() {
        let puzzle = makeMinimalPuzzle()
        let state = V2GameEngine.initGame(puzzle: puzzle)
        #expect(state.discoveredPieces.isEmpty)
    }
}

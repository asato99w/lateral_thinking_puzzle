import Testing
@testable import LateralThinkingPuzzle

struct V2InitGameTests {

    private func makeMinimalPuzzle() -> V2PuzzleData {
        V2PuzzleData(
            id: "test",
            title: "Test",
            statement: "Test statement",
            truth: "Test truth",
            descriptors: [
                "f1": V2Descriptor(id: "f1", label: "Fact 1", formationConditions: nil),
                "f2": V2Descriptor(id: "f2", label: "Fact 2", formationConditions: nil),
                "f3": V2Descriptor(id: "f3", label: "Fact 3", formationConditions: nil),
                "h1": V2Descriptor(id: "h1", label: "Hyp 1", formationConditions: [["f1", "f2"]]),
            ],
            initialConfirmed: ["f1", "f2"],
            clearConditions: [["f3"]],
            pieces: [
                "p1": V2Piece(id: "p1", label: "Piece 1", members: ["f3"], dependsOn: []),
            ],
            questions: [
                "q1": V2Question(id: "q1", text: "Q1?", answer: "Yes", recallConditions: [["h1"]], reveals: ["f3"], mechanism: "observation", prerequisites: [], correctAnswer: .yes, topicCategory: ""),
            ],
            topicCategories: []
        )
    }

    @Test func test_initGame_setsInitialConfirmed() {
        let puzzle = makeMinimalPuzzle()
        let state = V2GameEngine.initGame(puzzle: puzzle)
        #expect(state.confirmed.contains("f1"))
        #expect(state.confirmed.contains("f2"))
        #expect(!state.confirmed.contains("f3"))
    }

    @Test func test_initGame_evaluatesDerivationsFromInitialConfirmed() {
        let puzzle = makeMinimalPuzzle()
        let state = V2GameEngine.initGame(puzzle: puzzle)
        // h1 has formation_conditions [["f1", "f2"]] — both are initial confirmed
        // h1 は derived に入る（confirmed ではない）
        #expect(state.derived.contains("h1"))
        #expect(state.known.contains("h1"))
        #expect(!state.confirmed.contains("h1"))
    }

    @Test func test_initGame_emptyDiscoveredPieces() {
        let puzzle = makeMinimalPuzzle()
        let state = V2GameEngine.initGame(puzzle: puzzle)
        #expect(state.discoveredPieces.isEmpty)
    }
}

import Testing
@testable import LateralThinkingPuzzle

struct V2CheckCompleteTests {

    @Test func test_notComplete_whenPiecesMissing() {
        let puzzle = V2PuzzleData(
            id: "test", title: "", statement: "", truth: "",
            facts: ["f1": V2Fact(id: "f1", label: "")],
            initialFacts: ["f1"],
            pieces: [
                "p1": V2Piece(id: "p1", label: "", facts: ["f1"], dependsOn: []),
            ],
            hypotheses: [:],
            questions: [:],
            topicCategories: []
        )
        let state = V2GameState(observedFacts: ["f1"], formedHypotheses: [], discoveredPieces: [], answered: [])
        #expect(!V2GameEngine.checkComplete(state: state, puzzle: puzzle))
    }

    @Test func test_complete_whenAllPiecesDiscovered() {
        let puzzle = V2PuzzleData(
            id: "test", title: "", statement: "", truth: "",
            facts: ["f1": V2Fact(id: "f1", label: "")],
            initialFacts: ["f1"],
            pieces: [
                "p1": V2Piece(id: "p1", label: "", facts: ["f1"], dependsOn: []),
            ],
            hypotheses: [:],
            questions: [:],
            topicCategories: []
        )
        let state = V2GameState(observedFacts: ["f1"], formedHypotheses: [], discoveredPieces: ["p1"], answered: [])
        #expect(V2GameEngine.checkComplete(state: state, puzzle: puzzle))
    }

    @Test func test_complete_emptyPuzzle() {
        let puzzle = V2PuzzleData(
            id: "test", title: "", statement: "", truth: "",
            facts: [:],
            initialFacts: [],
            pieces: [:],
            hypotheses: [:],
            questions: [:],
            topicCategories: []
        )
        let state = V2GameState(observedFacts: [], formedHypotheses: [], discoveredPieces: [], answered: [])
        #expect(V2GameEngine.checkComplete(state: state, puzzle: puzzle))
    }
}

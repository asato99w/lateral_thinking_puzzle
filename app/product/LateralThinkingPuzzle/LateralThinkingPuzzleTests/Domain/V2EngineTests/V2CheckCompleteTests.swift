import Testing
@testable import LateralThinkingPuzzle

struct V2CheckCompleteTests {

    @Test func test_notComplete_whenClearConditionsNotMet() {
        let puzzle = V2PuzzleData(
            id: "test", title: "", statement: "", truth: "",
            descriptors: [
                "f1": V2Descriptor(id: "f1", label: "", formationConditions: nil),
                "f2": V2Descriptor(id: "f2", label: "", formationConditions: nil),
            ],
            initialConfirmed: ["f1"],
            clearConditions: [["f1", "f2"]],
            pieces: [:],
            questions: [:],
            topicCategories: []
        )
        let state = V2GameState(confirmed: ["f1"], discoveredPieces: [], answered: [])
        #expect(!V2GameEngine.checkComplete(state: state, puzzle: puzzle))
    }

    @Test func test_complete_whenClearConditionsMet() {
        let puzzle = V2PuzzleData(
            id: "test", title: "", statement: "", truth: "",
            descriptors: [
                "f1": V2Descriptor(id: "f1", label: "", formationConditions: nil),
                "f2": V2Descriptor(id: "f2", label: "", formationConditions: nil),
            ],
            initialConfirmed: ["f1"],
            clearConditions: [["f1", "f2"]],
            pieces: [:],
            questions: [:],
            topicCategories: []
        )
        let state = V2GameState(confirmed: ["f1", "f2"], discoveredPieces: [], answered: [])
        #expect(V2GameEngine.checkComplete(state: state, puzzle: puzzle))
    }

    @Test func test_complete_emptyPuzzle() {
        let puzzle = V2PuzzleData(
            id: "test", title: "", statement: "", truth: "",
            descriptors: [:],
            initialConfirmed: [],
            clearConditions: [[]],
            pieces: [:],
            questions: [:],
            topicCategories: []
        )
        let state = V2GameState(confirmed: [], discoveredPieces: [], answered: [])
        #expect(V2GameEngine.checkComplete(state: state, puzzle: puzzle))
    }
}

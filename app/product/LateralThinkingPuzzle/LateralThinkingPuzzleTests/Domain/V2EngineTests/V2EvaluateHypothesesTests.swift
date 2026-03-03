import Testing
@testable import LateralThinkingPuzzle

struct V2EvaluateDerivationsTests {

    @Test func test_simpleFormation_allConditionsMet() {
        let puzzle = V2PuzzleData(
            id: "test", title: "", statement: "", truth: "",
            descriptors: [
                "f1": V2Descriptor(id: "f1", label: "", formationConditions: nil),
                "f2": V2Descriptor(id: "f2", label: "", formationConditions: nil),
                "h1": V2Descriptor(id: "h1", label: "", formationConditions: [["f1", "f2"]]),
            ],
            initialConfirmed: ["f1", "f2"],
            clearConditions: [],
            pieces: [:],
            questions: [:],
            topicCategories: []
        )
        var state = V2GameState(confirmed: ["f1", "f2"], discoveredPieces: [], answered: [])
        let newly = V2GameEngine.evaluateDerivations(state: &state, puzzle: puzzle)
        #expect(newly.contains("h1"))
        #expect(state.confirmed.contains("h1"))
    }

    @Test func test_orOfAnd_secondGroupSuffices() {
        let puzzle = V2PuzzleData(
            id: "test", title: "", statement: "", truth: "",
            descriptors: [
                "f1": V2Descriptor(id: "f1", label: "", formationConditions: nil),
                "f2": V2Descriptor(id: "f2", label: "", formationConditions: nil),
                "f3": V2Descriptor(id: "f3", label: "", formationConditions: nil),
                "h1": V2Descriptor(id: "h1", label: "", formationConditions: [["f1"], ["f2", "f3"]]),
            ],
            initialConfirmed: ["f2", "f3"],
            clearConditions: [],
            pieces: [:],
            questions: [:],
            topicCategories: []
        )
        var state = V2GameState(confirmed: ["f2", "f3"], discoveredPieces: [], answered: [])
        let newly = V2GameEngine.evaluateDerivations(state: &state, puzzle: puzzle)
        #expect(newly.contains("h1"))
    }

    @Test func test_chainedDerivations_fixedPointIteration() {
        // h1 depends on facts, h2 depends on h1
        let puzzle = V2PuzzleData(
            id: "test", title: "", statement: "", truth: "",
            descriptors: [
                "f1": V2Descriptor(id: "f1", label: "", formationConditions: nil),
                "h1": V2Descriptor(id: "h1", label: "", formationConditions: [["f1"]]),
                "h2": V2Descriptor(id: "h2", label: "", formationConditions: [["h1"]]),
            ],
            initialConfirmed: ["f1"],
            clearConditions: [],
            pieces: [:],
            questions: [:],
            topicCategories: []
        )
        var state = V2GameState(confirmed: ["f1"], discoveredPieces: [], answered: [])
        let newly = V2GameEngine.evaluateDerivations(state: &state, puzzle: puzzle)
        #expect(newly.contains("h1"))
        #expect(newly.contains("h2"))
    }

    @Test func test_conditionsNotMet_descriptorNotDerived() {
        let puzzle = V2PuzzleData(
            id: "test", title: "", statement: "", truth: "",
            descriptors: [
                "f1": V2Descriptor(id: "f1", label: "", formationConditions: nil),
                "f2": V2Descriptor(id: "f2", label: "", formationConditions: nil),
                "h1": V2Descriptor(id: "h1", label: "", formationConditions: [["f1", "f2"]]),
            ],
            initialConfirmed: ["f1"],
            clearConditions: [],
            pieces: [:],
            questions: [:],
            topicCategories: []
        )
        var state = V2GameState(confirmed: ["f1"], discoveredPieces: [], answered: [])
        let newly = V2GameEngine.evaluateDerivations(state: &state, puzzle: puzzle)
        #expect(!newly.contains("h1"))
        #expect(!state.confirmed.contains("h1"))
    }
}

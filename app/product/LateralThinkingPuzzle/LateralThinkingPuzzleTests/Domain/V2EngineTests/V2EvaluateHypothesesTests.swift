import Testing
@testable import LateralThinkingPuzzle

struct V2EvaluateHypothesesTests {

    @Test func test_simpleFormation_allConditionsMet() {
        let puzzle = V2PuzzleData(
            id: "test", title: "", statement: "", truth: "",
            facts: ["f1": V2Fact(id: "f1", label: ""), "f2": V2Fact(id: "f2", label: "")],
            initialFacts: ["f1", "f2"],
            pieces: [:],
            hypotheses: [
                "h1": V2Hypothesis(id: "h1", label: "", formationConditions: [["f1", "f2"]]),
            ],
            questions: [:],
            topicCategories: []
        )
        var state = V2GameState(observedFacts: ["f1", "f2"], formedHypotheses: [], discoveredPieces: [], answered: [])
        let newly = V2GameEngine.evaluateHypotheses(state: &state, puzzle: puzzle)
        #expect(newly.contains("h1"))
        #expect(state.formedHypotheses.contains("h1"))
    }

    @Test func test_orOfAnd_secondGroupSuffices() {
        let puzzle = V2PuzzleData(
            id: "test", title: "", statement: "", truth: "",
            facts: ["f1": V2Fact(id: "f1", label: ""), "f2": V2Fact(id: "f2", label: ""), "f3": V2Fact(id: "f3", label: "")],
            initialFacts: ["f2", "f3"],
            pieces: [:],
            hypotheses: [
                "h1": V2Hypothesis(id: "h1", label: "", formationConditions: [["f1"], ["f2", "f3"]]),
            ],
            questions: [:],
            topicCategories: []
        )
        var state = V2GameState(observedFacts: ["f2", "f3"], formedHypotheses: [], discoveredPieces: [], answered: [])
        let newly = V2GameEngine.evaluateHypotheses(state: &state, puzzle: puzzle)
        #expect(newly.contains("h1"))
    }

    @Test func test_chainedHypotheses_fixedPointIteration() {
        // h1 depends on facts, h2 depends on h1
        let puzzle = V2PuzzleData(
            id: "test", title: "", statement: "", truth: "",
            facts: ["f1": V2Fact(id: "f1", label: "")],
            initialFacts: ["f1"],
            pieces: [:],
            hypotheses: [
                "h1": V2Hypothesis(id: "h1", label: "", formationConditions: [["f1"]]),
                "h2": V2Hypothesis(id: "h2", label: "", formationConditions: [["h1"]]),
            ],
            questions: [:],
            topicCategories: []
        )
        var state = V2GameState(observedFacts: ["f1"], formedHypotheses: [], discoveredPieces: [], answered: [])
        let newly = V2GameEngine.evaluateHypotheses(state: &state, puzzle: puzzle)
        #expect(newly.contains("h1"))
        #expect(newly.contains("h2"))
    }

    @Test func test_conditionsNotMet_hypothesisNotFormed() {
        let puzzle = V2PuzzleData(
            id: "test", title: "", statement: "", truth: "",
            facts: ["f1": V2Fact(id: "f1", label: ""), "f2": V2Fact(id: "f2", label: "")],
            initialFacts: ["f1"],
            pieces: [:],
            hypotheses: [
                "h1": V2Hypothesis(id: "h1", label: "", formationConditions: [["f1", "f2"]]),
            ],
            questions: [:],
            topicCategories: []
        )
        var state = V2GameState(observedFacts: ["f1"], formedHypotheses: [], discoveredPieces: [], answered: [])
        let newly = V2GameEngine.evaluateHypotheses(state: &state, puzzle: puzzle)
        #expect(!newly.contains("h1"))
        #expect(!state.formedHypotheses.contains("h1"))
    }
}

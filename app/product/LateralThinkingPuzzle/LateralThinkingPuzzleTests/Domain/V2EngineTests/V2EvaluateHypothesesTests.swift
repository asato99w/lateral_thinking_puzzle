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
        let result = V2GameEngine.evaluateDerivations(state: &state, puzzle: puzzle)
        #expect(result.newlyDerived.contains("h1"))
        #expect(state.derived.contains("h1"))
        #expect(state.known.contains("h1"))
        // confirmed は変更されない
        #expect(!state.confirmed.contains("h1"))
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
        let result = V2GameEngine.evaluateDerivations(state: &state, puzzle: puzzle)
        #expect(result.newlyDerived.contains("h1"))
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
        let result = V2GameEngine.evaluateDerivations(state: &state, puzzle: puzzle)
        #expect(result.newlyDerived.contains("h1"))
        #expect(result.newlyDerived.contains("h2"))
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
        let result = V2GameEngine.evaluateDerivations(state: &state, puzzle: puzzle)
        #expect(!result.newlyDerived.contains("h1"))
        #expect(!state.derived.contains("h1"))
    }

    // MARK: - 棄却メカニズムのテスト

    @Test func test_rejection_preventsDerivation() {
        // h1 は f1 から導出可能だが、f2 が confirmed されると棄却される
        let puzzle = V2PuzzleData(
            id: "test", title: "", statement: "", truth: "",
            descriptors: [
                "f1": V2Descriptor(id: "f1", label: "", formationConditions: nil),
                "f2": V2Descriptor(id: "f2", label: "", formationConditions: nil),
                "h1": V2Descriptor(id: "h1", label: "", formationConditions: [["f1"]], rejectionConditions: [["f2"]]),
            ],
            initialConfirmed: ["f1", "f2"],
            clearConditions: [],
            pieces: [:],
            questions: [:],
            topicCategories: []
        )
        var state = V2GameState(confirmed: ["f1", "f2"], discoveredPieces: [], answered: [])
        let result = V2GameEngine.evaluateDerivations(state: &state, puzzle: puzzle)
        // h1 は棄却されるため導出されない
        #expect(!result.newlyDerived.contains("h1"))
        #expect(!state.derived.contains("h1"))
    }

    @Test func test_rejection_removesExistingDerived() {
        // h1 が既に derived にある状態で、棄却条件が成立すると除去される
        let puzzle = V2PuzzleData(
            id: "test", title: "", statement: "", truth: "",
            descriptors: [
                "f1": V2Descriptor(id: "f1", label: "", formationConditions: nil),
                "f2": V2Descriptor(id: "f2", label: "", formationConditions: nil),
                "h1": V2Descriptor(id: "h1", label: "", formationConditions: [["f1"]], rejectionConditions: [["f2"]]),
            ],
            initialConfirmed: ["f1"],
            clearConditions: [],
            pieces: [:],
            questions: [:],
            topicCategories: []
        )
        // まず h1 を導出させる
        var state = V2GameState(confirmed: ["f1"], discoveredPieces: [], answered: [])
        _ = V2GameEngine.evaluateDerivations(state: &state, puzzle: puzzle)
        #expect(state.derived.contains("h1"))

        // f2 を confirmed に追加して再評価 → h1 が棄却される
        state.confirmed.insert("f2")
        let result = V2GameEngine.evaluateDerivations(state: &state, puzzle: puzzle)
        #expect(result.newlyRejected.contains("h1"))
        #expect(!state.derived.contains("h1"))
    }

    @Test func test_rejection_doesNotAffectUnrelatedDerivations() {
        // h1 は棄却されるが、h2 は影響を受けない
        let puzzle = V2PuzzleData(
            id: "test", title: "", statement: "", truth: "",
            descriptors: [
                "f1": V2Descriptor(id: "f1", label: "", formationConditions: nil),
                "f2": V2Descriptor(id: "f2", label: "", formationConditions: nil),
                "h1": V2Descriptor(id: "h1", label: "", formationConditions: [["f1"]], rejectionConditions: [["f2"]]),
                "h2": V2Descriptor(id: "h2", label: "", formationConditions: [["f1"]]),
            ],
            initialConfirmed: ["f1", "f2"],
            clearConditions: [],
            pieces: [:],
            questions: [:],
            topicCategories: []
        )
        var state = V2GameState(confirmed: ["f1", "f2"], discoveredPieces: [], answered: [])
        _ = V2GameEngine.evaluateDerivations(state: &state, puzzle: puzzle)
        #expect(!state.derived.contains("h1"))  // 棄却
        #expect(state.derived.contains("h2"))   // 影響なし
    }

    @Test func test_rejection_cascadesToDependentDerivations() {
        // h1 が棄却されると、h1 に依存する h2 も導出されない
        let puzzle = V2PuzzleData(
            id: "test", title: "", statement: "", truth: "",
            descriptors: [
                "f1": V2Descriptor(id: "f1", label: "", formationConditions: nil),
                "f2": V2Descriptor(id: "f2", label: "", formationConditions: nil),
                "h1": V2Descriptor(id: "h1", label: "", formationConditions: [["f1"]], rejectionConditions: [["f2"]]),
                "h2": V2Descriptor(id: "h2", label: "", formationConditions: [["h1"]]),
            ],
            initialConfirmed: ["f1", "f2"],
            clearConditions: [],
            pieces: [:],
            questions: [:],
            topicCategories: []
        )
        var state = V2GameState(confirmed: ["f1", "f2"], discoveredPieces: [], answered: [])
        _ = V2GameEngine.evaluateDerivations(state: &state, puzzle: puzzle)
        #expect(!state.derived.contains("h1"))  // 棄却
        #expect(!state.derived.contains("h2"))  // 依存先が棄却されたため導出不可
    }

    @Test func test_rejection_requiresAllConditionsInGroup() {
        // 棄却条件が [["f2", "f3"]] の場合、f2 だけでは棄却されない
        let puzzle = V2PuzzleData(
            id: "test", title: "", statement: "", truth: "",
            descriptors: [
                "f1": V2Descriptor(id: "f1", label: "", formationConditions: nil),
                "f2": V2Descriptor(id: "f2", label: "", formationConditions: nil),
                "f3": V2Descriptor(id: "f3", label: "", formationConditions: nil),
                "h1": V2Descriptor(id: "h1", label: "", formationConditions: [["f1"]], rejectionConditions: [["f2", "f3"]]),
            ],
            initialConfirmed: ["f1", "f2"],
            clearConditions: [],
            pieces: [:],
            questions: [:],
            topicCategories: []
        )
        var state = V2GameState(confirmed: ["f1", "f2"], discoveredPieces: [], answered: [])
        _ = V2GameEngine.evaluateDerivations(state: &state, puzzle: puzzle)
        #expect(state.derived.contains("h1"))  // f3 がないため棄却されない
    }
}

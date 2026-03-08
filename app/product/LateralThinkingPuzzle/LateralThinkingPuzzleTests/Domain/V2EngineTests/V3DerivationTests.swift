import Testing
@testable import LateralThinkingPuzzle

struct V3DerivationTests {

    // MARK: - evaluateEntailments

    @Test func test_entailment_addsToConfirmed() {
        // entailment_conditions が satisfied → confirmed に追加される
        let puzzle = V2PuzzleData(
            id: "test", title: "", statement: "", truth: "",
            descriptors: [
                "f1": V2Descriptor(id: "f1", label: "", formationConditions: nil),
                "p1": V2Descriptor(id: "p1", label: "", formationConditions: nil, entailmentConditions: [["f1"]]),
            ],
            initialConfirmed: ["f1"],
            clearConditions: [],
            pieces: [:],
            questions: [:],
            topicCategories: [],
            derivationMode: .v3
        )
        var state = V2GameState(confirmed: ["f1"], discoveredPieces: [], answered: [])
        let result = V2GameEngine.evaluateEntailments(state: &state, puzzle: puzzle)
        #expect(result.contains("p1"))
        #expect(state.confirmed.contains("p1"))
        // derived には入らない
        #expect(!state.derived.contains("p1"))
    }

    @Test func test_entailment_chainsAllowed() {
        // entailment は不動点計算なので連鎖する: f1 → p1 → p2
        let puzzle = V2PuzzleData(
            id: "test", title: "", statement: "", truth: "",
            descriptors: [
                "f1": V2Descriptor(id: "f1", label: "", formationConditions: nil),
                "p1": V2Descriptor(id: "p1", label: "", formationConditions: nil, entailmentConditions: [["f1"]]),
                "p2": V2Descriptor(id: "p2", label: "", formationConditions: nil, entailmentConditions: [["p1"]]),
            ],
            initialConfirmed: ["f1"],
            clearConditions: [],
            pieces: [:],
            questions: [:],
            topicCategories: [],
            derivationMode: .v3
        )
        var state = V2GameState(confirmed: ["f1"], discoveredPieces: [], answered: [])
        let result = V2GameEngine.evaluateEntailments(state: &state, puzzle: puzzle)
        #expect(result.contains("p1"))
        #expect(result.contains("p2"))
        #expect(state.confirmed.contains("p1"))
        #expect(state.confirmed.contains("p2"))
    }

    @Test func test_entailment_conditionsNotMet() {
        let puzzle = V2PuzzleData(
            id: "test", title: "", statement: "", truth: "",
            descriptors: [
                "f1": V2Descriptor(id: "f1", label: "", formationConditions: nil),
                "p1": V2Descriptor(id: "p1", label: "", formationConditions: nil, entailmentConditions: [["f1", "f2"]]),
            ],
            initialConfirmed: ["f1"],
            clearConditions: [],
            pieces: [:],
            questions: [:],
            topicCategories: [],
            derivationMode: .v3
        )
        var state = V2GameState(confirmed: ["f1"], discoveredPieces: [], answered: [])
        let result = V2GameEngine.evaluateEntailments(state: &state, puzzle: puzzle)
        #expect(result.isEmpty)
        #expect(!state.confirmed.contains("p1"))
    }

    // MARK: - evaluateHypotheses (v3: 1回パス)

    @Test func test_hypotheses_singlePass_noChaining() {
        // v3 の formation_conditions は1回パスのため、h1 → h2 の連鎖は起こらない
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
            topicCategories: [],
            derivationMode: .v3
        )
        var state = V2GameState(confirmed: ["f1"], discoveredPieces: [], answered: [])
        let result = V2GameEngine.evaluateHypotheses(state: &state, puzzle: puzzle)
        // h1 は confirmed から導出される
        #expect(result.newlyDerived.contains("h1"))
        #expect(state.derived.contains("h1"))
        // h2 は h1 に依存するが、h1 は derived であり confirmed ではないため導出されない
        #expect(!result.newlyDerived.contains("h2"))
        #expect(!state.derived.contains("h2"))
    }

    @Test func test_hypotheses_confirmedOnly() {
        // formation_conditions は confirmed のみ参照
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
            topicCategories: [],
            derivationMode: .v3
        )
        var state = V2GameState(confirmed: ["f1", "f2"], discoveredPieces: [], answered: [])
        let result = V2GameEngine.evaluateHypotheses(state: &state, puzzle: puzzle)
        #expect(result.newlyDerived.contains("h1"))
    }

    @Test func test_hypotheses_rejectionWorks() {
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
            topicCategories: [],
            derivationMode: .v3
        )
        var state = V2GameState(confirmed: ["f1", "f2"], discoveredPieces: [], answered: [])
        let result = V2GameEngine.evaluateHypotheses(state: &state, puzzle: puzzle)
        #expect(!result.newlyDerived.contains("h1"))
        #expect(!state.derived.contains("h1"))
    }

    // MARK: - initGame (v3 統合テスト)

    @Test func test_v3InitGame_entailmentThenHypothesis() {
        // f1 → (entailment) → p1 (confirmed), f1 → (formation) → h1 (derived)
        let puzzle = V2PuzzleData(
            id: "test", title: "", statement: "", truth: "",
            descriptors: [
                "f1": V2Descriptor(id: "f1", label: "", formationConditions: nil),
                "p1": V2Descriptor(id: "p1", label: "", formationConditions: nil, entailmentConditions: [["f1"]]),
                "h1": V2Descriptor(id: "h1", label: "", formationConditions: [["f1"]]),
                "h2": V2Descriptor(id: "h2", label: "", formationConditions: [["p1"]]),
            ],
            initialConfirmed: ["f1"],
            clearConditions: [],
            pieces: [:],
            questions: [:],
            topicCategories: [],
            derivationMode: .v3
        )
        let state = V2GameEngine.initGame(puzzle: puzzle)
        // p1 は entailment で confirmed に
        #expect(state.confirmed.contains("p1"))
        // h1 は formation で derived に
        #expect(state.derived.contains("h1"))
        // h2 は p1 (confirmed) を参照するので formation で derived に
        #expect(state.derived.contains("h2"))
    }

    @Test func test_v3InitGame_entailmentEnablesHypothesis() {
        // entailment で p1 が confirmed になり、それを前提に h1 が derived される
        let puzzle = V2PuzzleData(
            id: "test", title: "", statement: "", truth: "",
            descriptors: [
                "f1": V2Descriptor(id: "f1", label: "", formationConditions: nil),
                "p1": V2Descriptor(id: "p1", label: "", formationConditions: nil, entailmentConditions: [["f1"]]),
                "h1": V2Descriptor(id: "h1", label: "", formationConditions: [["p1"]]),
            ],
            initialConfirmed: ["f1"],
            clearConditions: [],
            pieces: [:],
            questions: [:],
            topicCategories: [],
            derivationMode: .v3
        )
        let state = V2GameEngine.initGame(puzzle: puzzle)
        #expect(state.confirmed.contains("p1"))
        #expect(state.derived.contains("h1"))
    }

    // MARK: - answerQuestion (v3)

    @Test func test_v3AnswerQuestion_entailmentAndHypothesis() {
        let puzzle = V2PuzzleData(
            id: "test", title: "", statement: "", truth: "",
            descriptors: [
                "f1": V2Descriptor(id: "f1", label: "", formationConditions: nil),
                "f2": V2Descriptor(id: "f2", label: "", formationConditions: nil),
                "p1": V2Descriptor(id: "p1", label: "", formationConditions: nil, entailmentConditions: [["f1", "f2"]]),
                "h1": V2Descriptor(id: "h1", label: "", formationConditions: [["p1"]]),
            ],
            initialConfirmed: ["f1"],
            clearConditions: [],
            pieces: [:],
            questions: [
                "q1": V2Question(id: "q1", text: "Q?", answer: "Yes", recallConditions: [["f1"]], reveals: ["f2"], mechanism: "observation", prerequisites: [], correctAnswer: .yes, topicCategory: ""),
            ],
            topicCategories: [],
            derivationMode: .v3
        )
        var state = V2GameEngine.initGame(puzzle: puzzle)
        // 初期状態: f1 のみ confirmed、p1 は条件未達
        #expect(!state.confirmed.contains("p1"))

        let q = puzzle.questions["q1"]!
        let result = V2GameEngine.answerQuestion(state: &state, question: q, puzzle: puzzle)
        // f2 が reveals で confirmed に追加
        #expect(result.newConfirmed.contains("f2"))
        // p1 が entailment で confirmed に追加
        #expect(result.newConfirmed.contains("p1"))
        #expect(state.confirmed.contains("p1"))
        // h1 が hypothesis で derived に
        #expect(result.newDerived.contains("h1"))
        #expect(state.derived.contains("h1"))
    }

    // MARK: - v2 との対比テスト

    @Test func test_v2VsV3_chainingDifference() {
        // 同じデータでも v2 と v3 で結果が異なることを確認
        // h1 → h2 の連鎖: v2 では h2 も derived、v3 では h2 は導出されない
        let descriptors: [String: V2Descriptor] = [
            "f1": V2Descriptor(id: "f1", label: "", formationConditions: nil),
            "h1": V2Descriptor(id: "h1", label: "", formationConditions: [["f1"]]),
            "h2": V2Descriptor(id: "h2", label: "", formationConditions: [["h1"]]),
        ]

        // v2: 不動点計算で連鎖
        let puzzleV2 = V2PuzzleData(
            id: "test", title: "", statement: "", truth: "",
            descriptors: descriptors, initialConfirmed: ["f1"],
            clearConditions: [], pieces: [:], questions: [:],
            topicCategories: [], derivationMode: .v2
        )
        let stateV2 = V2GameEngine.initGame(puzzle: puzzleV2)
        #expect(stateV2.derived.contains("h1"))
        #expect(stateV2.derived.contains("h2"))  // v2: 連鎖あり

        // v3: 1回パスで連鎖なし
        let puzzleV3 = V2PuzzleData(
            id: "test", title: "", statement: "", truth: "",
            descriptors: descriptors, initialConfirmed: ["f1"],
            clearConditions: [], pieces: [:], questions: [:],
            topicCategories: [], derivationMode: .v3
        )
        let stateV3 = V2GameEngine.initGame(puzzle: puzzleV3)
        #expect(stateV3.derived.contains("h1"))
        #expect(!stateV3.derived.contains("h2"))  // v3: 連鎖なし
    }
}

import Testing
@testable import LateralThinkingPuzzle

struct V2AvailableQuestionsTests {

    @Test func test_questionAvailable_whenRecallConditionsMet() {
        // reveals[0] ("target") の fc=[["h1"]], h1 は derived(known) → rc 充足 → 利用可能
        let puzzle = V2PuzzleData(
            id: "test", title: "", statement: "", truth: "",
            descriptors: [
                "f1": V2Descriptor(id: "f1", label: "", formationConditions: nil),
                "h1": V2Descriptor(id: "h1", label: "", formationConditions: [["f1"]]),
                "target": V2Descriptor(id: "target", label: "", formationConditions: [["h1"]]),
            ],
            initialConfirmed: ["f1"],
            clearConditions: [],
            pieces: [:],
            questions: [
                "q1": V2Question(id: "q1", text: "Q?", answer: "Yes", reveals: ["target"], mechanism: "observation", prerequisites: [], correctAnswer: .yes, topicCategory: ""),
            ],
            topicCategories: []
        )
        let state = V2GameEngine.initGame(puzzle: puzzle)
        let available = V2GameEngine.availableQuestions(state: state, puzzle: puzzle)
        #expect(available.count == 1)
        #expect(available[0].id == "q1")
    }

    @Test func test_questionAvailable_whenRecallConditionsUseFacts() {
        // reveals[0] ("target") の fc=[["f1", "f2"]], 両方 confirmed → rc 充足
        let puzzle = V2PuzzleData(
            id: "test", title: "", statement: "", truth: "",
            descriptors: [
                "f1": V2Descriptor(id: "f1", label: "", formationConditions: nil),
                "f2": V2Descriptor(id: "f2", label: "", formationConditions: nil),
                "target": V2Descriptor(id: "target", label: "", formationConditions: [["f1", "f2"]]),
            ],
            initialConfirmed: ["f1", "f2"],
            clearConditions: [],
            pieces: [:],
            questions: [
                "q1": V2Question(id: "q1", text: "Q?", answer: "Yes", reveals: ["target"], mechanism: "observation", prerequisites: [], correctAnswer: .yes, topicCategory: ""),
            ],
            topicCategories: []
        )
        let state = V2GameEngine.initGame(puzzle: puzzle)
        let available = V2GameEngine.availableQuestions(state: state, puzzle: puzzle)
        #expect(available.count == 1)
    }

    @Test func test_questionNotAvailable_whenRecallConditionsNotMet() {
        // reveals[0] ("target") の fc=[["h2"]], h2 は導出不可 → rc 未充足
        let puzzle = V2PuzzleData(
            id: "test", title: "", statement: "", truth: "",
            descriptors: [
                "f1": V2Descriptor(id: "f1", label: "", formationConditions: nil),
                "h1": V2Descriptor(id: "h1", label: "", formationConditions: [["f1"]]),
                "h2": V2Descriptor(id: "h2", label: "", formationConditions: [["h_nonexistent"]]),
                "target": V2Descriptor(id: "target", label: "", formationConditions: [["h2"]]),
            ],
            initialConfirmed: ["f1"],
            clearConditions: [],
            pieces: [:],
            questions: [
                "q1": V2Question(id: "q1", text: "Q?", answer: "Yes", reveals: ["target"], mechanism: "observation", prerequisites: [], correctAnswer: .yes, topicCategory: ""),
            ],
            topicCategories: []
        )
        let state = V2GameEngine.initGame(puzzle: puzzle)
        let available = V2GameEngine.availableQuestions(state: state, puzzle: puzzle)
        #expect(available.isEmpty)
    }

    @Test func test_questionNotAvailable_whenPrerequisitesNotMet() {
        // prerequisites は confirmed のみで判定（derived では不可）
        // reveals[0] ("target") の fc=[["f1"]], f1 confirmed → rc 充足
        // prerequisites=["h1"], h1 は derived → 未充足
        let puzzle = V2PuzzleData(
            id: "test", title: "", statement: "", truth: "",
            descriptors: [
                "f1": V2Descriptor(id: "f1", label: "", formationConditions: nil),
                "h1": V2Descriptor(id: "h1", label: "", formationConditions: [["f1"]]),
                "target": V2Descriptor(id: "target", label: "", formationConditions: [["f1"]]),
            ],
            initialConfirmed: ["f1"],
            clearConditions: [],
            pieces: [:],
            questions: [
                "q1": V2Question(id: "q1", text: "Q?", answer: "Yes", reveals: ["target"], mechanism: "observation", prerequisites: ["h1"], correctAnswer: .yes, topicCategory: ""),
            ],
            topicCategories: []
        )
        // h1 is derived (not confirmed), so prerequisites ["h1"] not met
        let state = V2GameEngine.initGame(puzzle: puzzle)
        let available = V2GameEngine.availableQuestions(state: state, puzzle: puzzle)
        #expect(available.isEmpty)
    }

    @Test func test_questionAvailable_whenPrerequisitesConfirmed() {
        // reveals[0] ("target") の fc=[["f1"]], f1 confirmed → rc 充足
        // prerequisites=["f2"], f2 confirmed → 充足
        let puzzle = V2PuzzleData(
            id: "test", title: "", statement: "", truth: "",
            descriptors: [
                "f1": V2Descriptor(id: "f1", label: "", formationConditions: nil),
                "f2": V2Descriptor(id: "f2", label: "", formationConditions: nil),
                "target": V2Descriptor(id: "target", label: "", formationConditions: [["f1"]]),
            ],
            initialConfirmed: ["f1", "f2"],
            clearConditions: [],
            pieces: [:],
            questions: [
                "q1": V2Question(id: "q1", text: "Q?", answer: "Yes", reveals: ["target"], mechanism: "observation", prerequisites: ["f2"], correctAnswer: .yes, topicCategory: ""),
            ],
            topicCategories: []
        )
        let state = V2GameEngine.initGame(puzzle: puzzle)
        let available = V2GameEngine.availableQuestions(state: state, puzzle: puzzle)
        #expect(available.count == 1)
    }

    @Test func test_answeredQuestion_notAvailable() {
        // reveals[0] ("target") の fc=[["h1"]], h1 derived → rc 充足
        // ただし回答済み → 利用不可
        let puzzle = V2PuzzleData(
            id: "test", title: "", statement: "", truth: "",
            descriptors: [
                "f1": V2Descriptor(id: "f1", label: "", formationConditions: nil),
                "h1": V2Descriptor(id: "h1", label: "", formationConditions: [["f1"]]),
                "target": V2Descriptor(id: "target", label: "", formationConditions: [["h1"]]),
            ],
            initialConfirmed: ["f1"],
            clearConditions: [],
            pieces: [:],
            questions: [
                "q1": V2Question(id: "q1", text: "Q?", answer: "Yes", reveals: ["target"], mechanism: "observation", prerequisites: [], correctAnswer: .yes, topicCategory: ""),
            ],
            topicCategories: []
        )
        var state = V2GameEngine.initGame(puzzle: puzzle)
        state.answered.insert("q1")
        let available = V2GameEngine.availableQuestions(state: state, puzzle: puzzle)
        #expect(available.isEmpty)
    }

    @Test func test_questionAvailable_whenNoReveals() {
        // reveals が空 → rc = nil → 常に利用可能
        let puzzle = V2PuzzleData(
            id: "test", title: "", statement: "", truth: "",
            descriptors: [
                "f1": V2Descriptor(id: "f1", label: "", formationConditions: nil),
            ],
            initialConfirmed: ["f1"],
            clearConditions: [],
            pieces: [:],
            questions: [
                "q1": V2Question(id: "q1", text: "Q?", answer: "Yes", reveals: [], mechanism: "observation", prerequisites: [], correctAnswer: .yes, topicCategory: ""),
            ],
            topicCategories: []
        )
        let state = V2GameEngine.initGame(puzzle: puzzle)
        let available = V2GameEngine.availableQuestions(state: state, puzzle: puzzle)
        #expect(available.count == 1)
    }

    @Test func test_questionAvailable_whenRevealsBasicDescriptor() {
        // reveals[0] の fc = nil（基礎記述素）→ rc = nil → 常に利用可能
        let puzzle = V2PuzzleData(
            id: "test", title: "", statement: "", truth: "",
            descriptors: [
                "f1": V2Descriptor(id: "f1", label: "", formationConditions: nil),
                "f2": V2Descriptor(id: "f2", label: "", formationConditions: nil),
            ],
            initialConfirmed: ["f1"],
            clearConditions: [],
            pieces: [:],
            questions: [
                "q1": V2Question(id: "q1", text: "Q?", answer: "Yes", reveals: ["f2"], mechanism: "observation", prerequisites: [], correctAnswer: .yes, topicCategory: ""),
            ],
            topicCategories: []
        )
        let state = V2GameEngine.initGame(puzzle: puzzle)
        let available = V2GameEngine.availableQuestions(state: state, puzzle: puzzle)
        #expect(available.count == 1)
    }
}

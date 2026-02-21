import Testing
@testable import LateralThinkingPuzzle

struct OpenQuestionsTests {

    @Test func test_openQuestions_hCloseToEffectValue_opens() {
        // Q1 effect: d1=1. H[d1]=0.9 → |0.9-1.0| = 0.1 < epsilon(0.2) → open
        let q1 = TestPuzzleData.makeQuestion(id: "q1", ansYes: [("d1", 1)], correctAnswer: .yes)
        let state = GameState(h: ["d1": 0.9], o: [:], r: [], pCurrent: "P1")

        let result = GameEngine.openQuestions(state: state, questions: [q1])
        #expect(result.map(\.id) == ["q1"])
    }

    @Test func test_openQuestions_hFarFromEffectValue_doesNotOpen() {
        // Q1 effect: d1=1. H[d1]=0.5 → |0.5-1.0| = 0.5 > epsilon(0.2) → not open
        let q1 = TestPuzzleData.makeQuestion(id: "q1", ansYes: [("d1", 1)], correctAnswer: .yes)
        let state = GameState(h: ["d1": 0.5], o: [:], r: [], pCurrent: "P1")

        let result = GameEngine.openQuestions(state: state, questions: [q1])
        #expect(result.isEmpty)
    }

    @Test func test_openQuestions_answeredQuestionsExcluded() {
        let q1 = TestPuzzleData.makeQuestion(id: "q1", ansYes: [("d1", 1)], correctAnswer: .yes)
        let state = GameState(h: ["d1": 1.0], o: [:], r: [], pCurrent: "P1", answered: ["q1"])

        let result = GameEngine.openQuestions(state: state, questions: [q1])
        #expect(result.isEmpty)
    }

    @Test func test_openQuestions_irrelevantQuestionsNotOpened() {
        let q1 = TestPuzzleData.makeQuestion(id: "q1", correctAnswer: .irrelevant)
        let state = GameState(h: ["d1": 1.0], o: [:], r: [], pCurrent: "P1")

        let result = GameEngine.openQuestions(state: state, questions: [q1])
        #expect(result.isEmpty) // irrelevant has no observation pairs
    }

    @Test func test_openQuestions_missingHDefaultsToHalf() {
        // Q1 effect: d1=0. H[d1] missing → default 0.5. |0.5-0.0| = 0.5 > epsilon → not open
        let q1 = TestPuzzleData.makeQuestion(id: "q1", ansNo: [("d1", 0)], correctAnswer: .no)
        let state = GameState(h: [:], o: [:], r: [], pCurrent: "P1")

        let result = GameEngine.openQuestions(state: state, questions: [q1])
        #expect(result.isEmpty)
    }

    @Test func test_openQuestions_effectValueZero_hCloseToZero_opens() {
        // Q1 effect: d1=0. H[d1]=0.1 → |0.1-0.0| = 0.1 < epsilon → open
        let q1 = TestPuzzleData.makeQuestion(id: "q1", ansNo: [("d1", 0)], correctAnswer: .no)
        let state = GameState(h: ["d1": 0.1], o: [:], r: [], pCurrent: "P1")

        let result = GameEngine.openQuestions(state: state, questions: [q1])
        #expect(result.map(\.id) == ["q1"])
    }
}

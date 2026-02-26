import Testing
@testable import LateralThinkingPuzzle

struct OpenQuestionsTests {

    @Test func test_openQuestions_consistentReach_opens() {
        // P1: d1=1, d2=1, relation d1->d2
        // O has d1=1 (consistent), so d2 is reachable via consistent reach
        // Q effect d2=1 matches prediction -> opens
        let p1 = TestPuzzleData.makeParadigm(
            pPred: ["d1": 1, "d2": 1],
            relations: [Relation(src: "d1", tgt: "d2", weight: 0.8)]
        )
        let q1 = TestPuzzleData.makeQuestion(id: "q1", ansYes: [("d2", 1)], ansNo: [("d2", 0)], ansIrrelevant: ["d2"], correctAnswer: .yes, paradigms: ["P1"])
        let state = GameState(h: ["d1": 1.0, "d2": 0.5], o: ["d1": 1], r: [], pCurrent: "P1")

        let result = GameEngine.openQuestions(state: state, questions: [q1], paradigms: ["P1": p1])
        #expect(result.map(\.id) == ["q1"])
    }

    @Test func test_openQuestions_anomalyReach_opens() {
        // P1: d1=1, d3=0, relation d1->d3
        // O has d1=0 (anomaly), so d3 is reachable via anomaly reach
        // Q effect d3=1 -> opens via anomaly reach (regardless of prediction match)
        let p1 = TestPuzzleData.makeParadigm(
            pPred: ["d1": 1, "d3": 0],
            relations: [Relation(src: "d1", tgt: "d3", weight: 0.8)]
        )
        let q1 = TestPuzzleData.makeQuestion(id: "q1", ansYes: [("d3", 1)], ansNo: [("d3", 0)], ansIrrelevant: ["d3"], correctAnswer: .yes, paradigms: ["P1"])
        let state = GameState(h: ["d1": 0.0, "d3": 0.5], o: ["d1": 0], r: [], pCurrent: "P1")

        let result = GameEngine.openQuestions(state: state, questions: [q1], paradigms: ["P1": p1])
        #expect(result.map(\.id) == ["q1"])
    }

    @Test func test_openQuestions_paradigmMismatch_excluded() {
        // Q belongs to P2 only, current paradigm is P1 -> excluded
        let p1 = TestPuzzleData.makeParadigm(
            pPred: ["d1": 1, "d2": 1],
            relations: [Relation(src: "d1", tgt: "d2", weight: 0.8)]
        )
        let q1 = TestPuzzleData.makeQuestion(id: "q1", ansYes: [("d2", 1)], ansNo: [("d2", 0)], ansIrrelevant: ["d2"], correctAnswer: .yes, paradigms: ["P2"])
        let state = GameState(h: ["d1": 1.0, "d2": 0.5], o: ["d1": 1], r: [], pCurrent: "P1")

        let result = GameEngine.openQuestions(state: state, questions: [q1], paradigms: ["P1": p1])
        #expect(result.isEmpty)
    }

    @Test func test_openQuestions_emptyParadigms_noFilter() {
        // Q has empty paradigms array -> no paradigm filter applied
        let p1 = TestPuzzleData.makeParadigm(
            pPred: ["d1": 1, "d2": 1],
            relations: [Relation(src: "d1", tgt: "d2", weight: 0.8)]
        )
        let q1 = TestPuzzleData.makeQuestion(id: "q1", ansYes: [("d2", 1)], ansNo: [("d2", 0)], ansIrrelevant: ["d2"], correctAnswer: .yes, paradigms: [])
        let state = GameState(h: ["d1": 1.0, "d2": 0.5], o: ["d1": 1], r: [], pCurrent: "P1")

        let result = GameEngine.openQuestions(state: state, questions: [q1], paradigms: ["P1": p1])
        #expect(result.map(\.id) == ["q1"])
    }

    @Test func test_openQuestions_answeredExcluded() {
        let p1 = TestPuzzleData.makeParadigm(
            pPred: ["d1": 1, "d2": 1],
            relations: [Relation(src: "d1", tgt: "d2", weight: 0.8)]
        )
        let q1 = TestPuzzleData.makeQuestion(id: "q1", ansYes: [("d2", 1)], ansNo: [("d2", 0)], ansIrrelevant: ["d2"], correctAnswer: .yes, paradigms: ["P1"])
        let state = GameState(h: ["d1": 1.0, "d2": 0.5], o: ["d1": 1], r: [], pCurrent: "P1", answered: ["q1"])

        let result = GameEngine.openQuestions(state: state, questions: [q1], paradigms: ["P1": p1])
        #expect(result.isEmpty)
    }

    @Test func test_openQuestions_prerequisitesNotMet_excluded() {
        let p1 = TestPuzzleData.makeParadigm(
            pPred: ["d1": 1, "d2": 1],
            relations: [Relation(src: "d1", tgt: "d2", weight: 0.8)]
        )
        let q1 = TestPuzzleData.makeQuestion(id: "q1", ansYes: [("d2", 1)], ansNo: [("d2", 0)], ansIrrelevant: ["d2"], correctAnswer: .yes, prerequisites: ["d3"], paradigms: ["P1"])
        let state = GameState(h: ["d1": 1.0, "d2": 0.5], o: ["d1": 1], r: [], pCurrent: "P1")

        let result = GameEngine.openQuestions(state: state, questions: [q1], paradigms: ["P1": p1])
        #expect(result.isEmpty)
    }

    @Test func test_openQuestions_noReach_excluded() {
        // No relation from d1, so d2 is not reachable
        let p1 = TestPuzzleData.makeParadigm(
            pPred: ["d1": 1, "d2": 1],
            relations: []
        )
        let q1 = TestPuzzleData.makeQuestion(id: "q1", ansYes: [("d2", 1)], ansNo: [("d2", 0)], ansIrrelevant: ["d2"], correctAnswer: .yes, paradigms: ["P1"])
        let state = GameState(h: ["d1": 1.0, "d2": 0.5], o: ["d1": 1], r: [], pCurrent: "P1")

        let result = GameEngine.openQuestions(state: state, questions: [q1], paradigms: ["P1": p1])
        #expect(result.isEmpty)
    }
}

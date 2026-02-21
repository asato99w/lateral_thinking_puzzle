import Testing
@testable import LateralThinkingPuzzle

struct InitQuestionsTests {

    @Test func test_initQuestions_selectsQuestionsWithDPlusEffect() {
        // P1 has dPlus: d1, d2. Questions with effect containing d1=1 or d2=1 should be selected.
        let paradigm = TestPuzzleData.makeParadigm(dPlus: ["d1", "d2"], dMinus: ["d3"])
        let q1 = TestPuzzleData.makeQuestion(id: "q1", ansYes: [("d1", 1)], correctAnswer: .yes) // d1=1, pred=1 → match
        let q2 = TestPuzzleData.makeQuestion(id: "q2", ansYes: [("d3", 1)], correctAnswer: .yes) // d3=1, pred=0 → no match
        let q3 = TestPuzzleData.makeQuestion(id: "q3", ansYes: [("d5", 1)], correctAnswer: .yes) // d5 not in paradigm → no match

        let result = GameEngine.initQuestions(paradigm: paradigm, questions: [q1, q2, q3])
        #expect(result.map(\.id) == ["q1"])
    }

    @Test func test_initQuestions_irrelevantQuestionsExcluded() {
        let paradigm = TestPuzzleData.makeParadigm(dPlus: ["d1"], dMinus: ["d3"])
        let q1 = TestPuzzleData.makeQuestion(id: "q1", correctAnswer: .irrelevant) // irrelevant → no observation pairs

        let result = GameEngine.initQuestions(paradigm: paradigm, questions: [q1])
        #expect(result.isEmpty)
    }

    @Test func test_initQuestions_noMatchingQuestions_returnsEmpty() {
        let paradigm = TestPuzzleData.makeParadigm(dPlus: ["d1"], dMinus: ["d3"])
        let q1 = TestPuzzleData.makeQuestion(id: "q1", ansNo: [("d1", 0)], correctAnswer: .no) // d1=0, pred=1 → no match

        let result = GameEngine.initQuestions(paradigm: paradigm, questions: [q1])
        #expect(result.isEmpty)
    }

    @Test func test_initQuestions_dMinusMatchAlsoSelected() {
        // Q with effect d3=0, paradigm predicts d3=0 (dMinus) → match
        let paradigm = TestPuzzleData.makeParadigm(dPlus: ["d1"], dMinus: ["d3"])
        let q1 = TestPuzzleData.makeQuestion(id: "q1", ansNo: [("d3", 0)], correctAnswer: .no) // d3=0, pred=0 → match

        let result = GameEngine.initQuestions(paradigm: paradigm, questions: [q1])
        #expect(result.map(\.id) == ["q1"])
    }
}

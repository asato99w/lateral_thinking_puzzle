import Testing
@testable import LateralThinkingPuzzle

struct InitQuestionsTests {

    @Test func test_initQuestions_selectsQuestionsWithMatchingEffect() {
        // P1 pred: d1=1, d2=1, d3=0. Questions with effect matching prediction should be selected.
        let paradigm = TestPuzzleData.makeParadigm(pPred: ["d1": 1, "d2": 1, "d3": 0], conceivable: ["d1", "d2", "d3"])
        let q1 = TestPuzzleData.makeQuestion(id: "q1", ansYes: [("d1", 1)], ansNo: [("d1", 0)], ansIrrelevant: ["d1"], correctAnswer: .yes) // d1=1, pred=1 -> match
        let q2 = TestPuzzleData.makeQuestion(id: "q2", ansYes: [("d3", 1)], ansNo: [("d3", 0)], ansIrrelevant: ["d3"], correctAnswer: .yes) // d3=1, pred=0 -> conflict
        let q3 = TestPuzzleData.makeQuestion(id: "q3", ansYes: [("d5", 1)], ansNo: [("d5", 0)], ansIrrelevant: ["d5"], correctAnswer: .yes) // d5 not in conceivable -> blocked

        let result = GameEngine.initQuestions(paradigm: paradigm, questions: [q1, q2, q3])
        #expect(result.map(\.id) == ["q1"])
    }

    @Test func test_initQuestions_irrelevantQuestionsExcluded() {
        let paradigm = TestPuzzleData.makeParadigm(pPred: ["d1": 1, "d3": 0], conceivable: ["d1", "d3"])
        let q1 = TestPuzzleData.makeQuestion(id: "q1", ansIrrelevant: ["d1"], correctAnswer: .irrelevant) // irrelevant -> no observation pairs

        let result = GameEngine.initQuestions(paradigm: paradigm, questions: [q1])
        #expect(result.isEmpty)
    }

    @Test func test_initQuestions_noMatchingQuestions_returnsEmpty() {
        let paradigm = TestPuzzleData.makeParadigm(pPred: ["d1": 1, "d3": 0], conceivable: ["d1", "d3"])
        let q1 = TestPuzzleData.makeQuestion(id: "q1", ansYes: [("d1", 1)], ansNo: [("d1", 0)], ansIrrelevant: ["d1"], correctAnswer: .no) // d1=0, pred=1 -> conflict

        let result = GameEngine.initQuestions(paradigm: paradigm, questions: [q1])
        #expect(result.isEmpty)
    }

    @Test func test_initQuestions_predZeroMatchAlsoSelected() {
        // Q with effect d3=0, paradigm predicts d3=0 -> match
        let paradigm = TestPuzzleData.makeParadigm(pPred: ["d1": 1, "d3": 0], conceivable: ["d1", "d3"])
        let q1 = TestPuzzleData.makeQuestion(id: "q1", ansYes: [("d3", 1)], ansNo: [("d3", 0)], ansIrrelevant: ["d3"], correctAnswer: .no) // d3=0, pred=0 -> match

        let result = GameEngine.initQuestions(paradigm: paradigm, questions: [q1])
        #expect(result.map(\.id) == ["q1"])
    }

    @Test func test_initQuestions_excludesQuestionWithMatchAndConflict() {
        // Q with effect containing both match (d1=1, pred=1) and conflict (d3=1, pred=0)
        let paradigm = TestPuzzleData.makeParadigm(pPred: ["d1": 1, "d3": 0], conceivable: ["d1", "d3"])
        let q1 = TestPuzzleData.makeQuestion(id: "q1", ansYes: [("d1", 1), ("d3", 1)], ansNo: [("d1", 0), ("d3", 0)], ansIrrelevant: ["d1", "d3"], correctAnswer: .yes)

        let result = GameEngine.initQuestions(paradigm: paradigm, questions: [q1])
        #expect(result.isEmpty)
    }
}

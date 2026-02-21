import Testing
@testable import LateralThinkingPuzzle

struct QuestionTests {

    @Test func test_effect_correctAnswerYes_returnsAnsYes() {
        let q = TestPuzzleData.makeQuestion(
            ansYes: [("d1", 1)],
            ansNo: [("d1", 0)],
            correctAnswer: .yes
        )
        let eff = q.effect
        #expect(eff == .observation([("d1", 1)]))
    }

    @Test func test_effect_correctAnswerNo_returnsAnsNo() {
        let q = TestPuzzleData.makeQuestion(
            ansYes: [("d1", 1)],
            ansNo: [("d1", 0)],
            correctAnswer: .no
        )
        let eff = q.effect
        #expect(eff == .observation([("d1", 0)]))
    }

    @Test func test_effect_correctAnswerIrrelevant_returnsAnsIrrelevant() {
        let q = TestPuzzleData.makeQuestion(
            ansIrrelevant: ["d1"],
            correctAnswer: .irrelevant
        )
        let eff = q.effect
        #expect(eff == .irrelevant(["d1"]))
    }
}

import Testing
@testable import LateralThinkingPuzzle

struct InitQuestionsTests {

    @Test func test_initQuestions_returnsMatchingIDs() {
        let q1 = TestPuzzleData.makeQuestion(id: "q1")
        let q2 = TestPuzzleData.makeQuestion(id: "q2")
        let q3 = TestPuzzleData.makeQuestion(id: "q3")

        let result = GameEngine.initQuestions(questions: [q1, q2, q3], initQuestionIDs: ["q1", "q3"])
        #expect(result.map(\.id) == ["q1", "q3"])
    }

    @Test func test_initQuestions_nonexistentIDsIgnored() {
        let q1 = TestPuzzleData.makeQuestion(id: "q1")

        let result = GameEngine.initQuestions(questions: [q1], initQuestionIDs: ["q1", "q99"])
        #expect(result.map(\.id) == ["q1"])
    }

    @Test func test_initQuestions_emptyIDs_returnsEmpty() {
        let q1 = TestPuzzleData.makeQuestion(id: "q1")

        let result = GameEngine.initQuestions(questions: [q1], initQuestionIDs: [])
        #expect(result.isEmpty)
    }

    @Test func test_initQuestions_emptyQuestions_returnsEmpty() {
        let result = GameEngine.initQuestions(questions: [], initQuestionIDs: ["q1"])
        #expect(result.isEmpty)
    }
}

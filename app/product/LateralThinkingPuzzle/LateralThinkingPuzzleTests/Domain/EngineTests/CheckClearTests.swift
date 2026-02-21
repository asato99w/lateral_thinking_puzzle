import Testing
@testable import LateralThinkingPuzzle

struct CheckClearTests {

    @Test func test_checkClear_clearQuestion_returnsTrue() {
        let q = TestPuzzleData.makeQuestion(id: "q1", isClear: true)
        #expect(GameEngine.checkClear(question: q) == true)
    }

    @Test func test_checkClear_normalQuestion_returnsFalse() {
        let q = TestPuzzleData.makeQuestion(id: "q1", isClear: false)
        #expect(GameEngine.checkClear(question: q) == false)
    }
}

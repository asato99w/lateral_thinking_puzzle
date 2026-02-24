import Testing
@testable import LateralThinkingPuzzle

struct TensionTests {

    @Test func test_tension_allMatchingObservations_returnsZero() {
        let paradigm = TestPuzzleData.makeParadigm(pPred: ["d1": 1, "d2": 0], conceivable: ["d1", "d2"])
        let o: [String: Int] = ["d1": 1, "d2": 0]
        #expect(GameEngine.tension(o: o, paradigm: paradigm) == 0)
    }

    @Test func test_tension_oneContradiction_returnsOne() {
        let paradigm = TestPuzzleData.makeParadigm(pPred: ["d1": 1, "d2": 0], conceivable: ["d1", "d2"])
        let o: [String: Int] = ["d1": 0] // P predicts d1=1, observed d1=0
        #expect(GameEngine.tension(o: o, paradigm: paradigm) == 1)
    }

    @Test func test_tension_noOverlap_returnsZero() {
        let paradigm = TestPuzzleData.makeParadigm(pPred: ["d1": 1, "d2": 0], conceivable: ["d1", "d2"])
        let o: [String: Int] = ["d5": 1]
        #expect(GameEngine.tension(o: o, paradigm: paradigm) == 0)
    }

    @Test func test_tension_multipleContradictions_returnsCount() {
        let paradigm = TestPuzzleData.makeParadigm(pPred: ["d1": 1, "d2": 1, "d3": 0, "d4": 0], conceivable: ["d1", "d2", "d3", "d4"])
        let o: [String: Int] = ["d1": 0, "d2": 0, "d3": 1, "d4": 1] // all contradict
        #expect(GameEngine.tension(o: o, paradigm: paradigm) == 4)
    }

    @Test func test_tension_emptyObservations_returnsZero() {
        let paradigm = TestPuzzleData.makeParadigm()
        let o: [String: Int] = [:]
        #expect(GameEngine.tension(o: o, paradigm: paradigm) == 0)
    }
}

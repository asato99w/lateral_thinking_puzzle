import Testing
@testable import LateralThinkingPuzzle

struct AlignmentTests {

    @Test func test_alignment_allPredOneAtOne_returnsOne() {
        let paradigm = TestPuzzleData.makeParadigm(pPred: ["d1": 1, "d2": 1], conceivable: ["d1", "d2"])
        let h: [String: Double] = ["d1": 1.0, "d2": 1.0]
        let result = GameEngine.alignment(h: h, paradigm: paradigm)
        #expect(result == 1.0)
    }

    @Test func test_alignment_allPredZeroAtZero_returnsOne() {
        let paradigm = TestPuzzleData.makeParadigm(pPred: ["d3": 0, "d4": 0], conceivable: ["d3", "d4"])
        let h: [String: Double] = ["d3": 0.0, "d4": 0.0]
        let result = GameEngine.alignment(h: h, paradigm: paradigm)
        #expect(result == 1.0)
    }

    @Test func test_alignment_allAtHalf_returnsHalf() {
        let paradigm = TestPuzzleData.makeParadigm(pPred: ["d1": 1, "d3": 0], conceivable: ["d1", "d3"])
        let h: [String: Double] = ["d1": 0.5, "d3": 0.5]
        let result = GameEngine.alignment(h: h, paradigm: paradigm)
        #expect(result == 0.5)
    }

    @Test func test_alignment_missingDescriptorDefaults_toHalf() {
        let paradigm = TestPuzzleData.makeParadigm(pPred: ["d1": 1, "d3": 0], conceivable: ["d1", "d3"])
        let h: [String: Double] = [:] // all missing -> default 0.5
        let result = GameEngine.alignment(h: h, paradigm: paradigm)
        #expect(result == 0.5)
    }

    @Test func test_alignment_emptyParadigm_returnsZero() {
        let paradigm = TestPuzzleData.makeParadigm(pPred: [:], conceivable: [])
        let h: [String: Double] = ["d1": 1.0]
        let result = GameEngine.alignment(h: h, paradigm: paradigm)
        #expect(result == 0.0)
    }

    @Test func test_alignment_mixedValues_calculatesCorrectly() {
        // pred=1: d1(h=1.0) contributes 1.0, d2(h=0.0) contributes 0.0
        // pred=0: d3(h=0.0) contributes 1.0-0.0=1.0
        // total = (1.0 + 0.0 + 1.0) / 3 = 2/3
        let paradigm = TestPuzzleData.makeParadigm(pPred: ["d1": 1, "d2": 1, "d3": 0], conceivable: ["d1", "d2", "d3"])
        let h: [String: Double] = ["d1": 1.0, "d2": 0.0, "d3": 0.0]
        let result = GameEngine.alignment(h: h, paradigm: paradigm)
        #expect(abs(result - 2.0 / 3.0) < 0.0001)
    }
}

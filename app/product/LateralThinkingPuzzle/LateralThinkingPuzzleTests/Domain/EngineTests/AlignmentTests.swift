import Testing
@testable import LateralThinkingPuzzle

struct AlignmentTests {

    @Test func test_alignment_allDPlusAtOne_returnsOne() {
        let paradigm = TestPuzzleData.makeParadigm(dPlus: ["d1", "d2"], dMinus: [])
        let h: [String: Double] = ["d1": 1.0, "d2": 1.0]
        let result = GameEngine.alignment(h: h, paradigm: paradigm)
        #expect(result == 1.0)
    }

    @Test func test_alignment_allDMinusAtZero_returnsOne() {
        let paradigm = TestPuzzleData.makeParadigm(dPlus: [], dMinus: ["d3", "d4"])
        let h: [String: Double] = ["d3": 0.0, "d4": 0.0]
        let result = GameEngine.alignment(h: h, paradigm: paradigm)
        #expect(result == 1.0)
    }

    @Test func test_alignment_allAtHalf_returnsHalf() {
        let paradigm = TestPuzzleData.makeParadigm(dPlus: ["d1"], dMinus: ["d3"])
        let h: [String: Double] = ["d1": 0.5, "d3": 0.5]
        let result = GameEngine.alignment(h: h, paradigm: paradigm)
        #expect(result == 0.5)
    }

    @Test func test_alignment_missingDescriptorDefaults_toHalf() {
        let paradigm = TestPuzzleData.makeParadigm(dPlus: ["d1"], dMinus: ["d3"])
        let h: [String: Double] = [:] // all missing → default 0.5
        let result = GameEngine.alignment(h: h, paradigm: paradigm)
        #expect(result == 0.5)
    }

    @Test func test_alignment_emptyParadigm_returnsZero() {
        let paradigm = TestPuzzleData.makeParadigm(dPlus: [], dMinus: [])
        let h: [String: Double] = ["d1": 1.0]
        let result = GameEngine.alignment(h: h, paradigm: paradigm)
        #expect(result == 0.0)
    }

    @Test func test_alignment_mixedValues_calculatesCorrectly() {
        // dPlus: d1(h=1.0) contributes 1.0, d2(h=0.0) contributes 0.0
        // dMinus: d3(h=0.0) contributes 1.0-0.0=1.0
        // total = (1.0 + 0.0 + 1.0) / 3 = 2/3
        let paradigm = TestPuzzleData.makeParadigm(dPlus: ["d1", "d2"], dMinus: ["d3"])
        let h: [String: Double] = ["d1": 1.0, "d2": 0.0, "d3": 0.0]
        let result = GameEngine.alignment(h: h, paradigm: paradigm)
        #expect(abs(result - 2.0 / 3.0) < 0.0001)
    }
}

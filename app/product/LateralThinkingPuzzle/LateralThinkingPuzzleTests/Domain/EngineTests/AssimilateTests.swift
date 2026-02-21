import Testing
@testable import LateralThinkingPuzzle

struct AssimilateTests {

    @Test func test_assimilateDescriptor_propagatesToTarget() {
        // d1 → d2 (weight 0.8), d2 is dPlus (pred=1)
        // h[d2] = 0.5 + 0.8 * (1.0 - 0.5) = 0.5 + 0.4 = 0.9
        let paradigm = TestPuzzleData.makeParadigm(
            dPlus: ["d1", "d2"],
            dMinus: [],
            relations: [Relation(src: "d1", tgt: "d2", weight: 0.8)]
        )
        var h: [String: Double] = ["d1": 1.0, "d2": 0.5]
        GameEngine.assimilateDescriptor(h: &h, dID: "d1", paradigm: paradigm)
        #expect(abs(h["d2"]! - 0.9) < 0.0001)
    }

    @Test func test_assimilateDescriptor_noRelation_noChange() {
        let paradigm = TestPuzzleData.makeParadigm(
            dPlus: ["d1", "d2"],
            dMinus: [],
            relations: []
        )
        var h: [String: Double] = ["d1": 1.0, "d2": 0.5]
        GameEngine.assimilateDescriptor(h: &h, dID: "d1", paradigm: paradigm)
        #expect(h["d2"]! == 0.5) // no change
    }

    @Test func test_assimilateDescriptor_dMinusTarget_propagatesTowardZero() {
        // d1 → d3 (weight 0.8), d3 is dMinus (pred=0)
        // h[d3] = 0.5 + 0.8 * (0.0 - 0.5) = 0.5 - 0.4 = 0.1
        let paradigm = TestPuzzleData.makeParadigm(
            dPlus: ["d1"],
            dMinus: ["d3"],
            relations: [Relation(src: "d1", tgt: "d3", weight: 0.8)]
        )
        var h: [String: Double] = ["d1": 1.0, "d3": 0.5]
        GameEngine.assimilateDescriptor(h: &h, dID: "d1", paradigm: paradigm)
        #expect(abs(h["d3"]! - 0.1) < 0.0001)
    }

    @Test func test_assimilateFromParadigm_appliesMatchingObservations() {
        let paradigm = TestPuzzleData.makeParadigm(
            dPlus: ["d1", "d2"],
            dMinus: ["d3"],
            relations: [Relation(src: "d1", tgt: "d2", weight: 0.8)]
        )
        var h: [String: Double] = ["d1": 0.5, "d2": 0.5, "d3": 0.5]
        let o: [String: Int] = ["d1": 1] // matches dPlus prediction

        GameEngine.assimilateFromParadigm(h: &h, o: o, paradigm: paradigm)

        // d2 should be propagated: 0.5 + 0.8 * (1.0 - 0.5) = 0.9
        // but then o restores d1 to 1.0
        #expect(h["d1"]! == 1.0) // restored from o
        #expect(abs(h["d2"]! - 0.9) < 0.0001) // propagated
    }

    @Test func test_assimilateFromParadigm_nonMatchingObservation_noAssimilation() {
        let paradigm = TestPuzzleData.makeParadigm(
            dPlus: ["d1", "d2"],
            dMinus: ["d3"],
            relations: [Relation(src: "d1", tgt: "d2", weight: 0.8)]
        )
        var h: [String: Double] = ["d1": 0.5, "d2": 0.5]
        let o: [String: Int] = ["d1": 0] // contradicts dPlus prediction (pred=1, obs=0)

        GameEngine.assimilateFromParadigm(h: &h, o: o, paradigm: paradigm)

        // d2 should NOT be propagated because d1 observation doesn't match prediction
        // but o restores d1 to 0.0
        #expect(h["d1"]! == 0.0) // restored from o
        #expect(h["d2"]! == 0.5) // unchanged
    }
}

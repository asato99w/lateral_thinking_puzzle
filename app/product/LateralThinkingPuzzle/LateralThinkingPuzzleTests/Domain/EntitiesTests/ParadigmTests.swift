import Testing
@testable import LateralThinkingPuzzle

struct ParadigmTests {

    // MARK: - Construction

    @Test func test_paradigm_validData_creates() {
        let p = Paradigm(
            id: "P1", name: "test",
            pPred: ["d1": 1, "d2": 1, "d3": 0],
            relations: [Relation(src: "d1", tgt: "d2", weight: 0.8)]
        )
        #expect(p.pPred.count == 3)
    }

    // MARK: - Prediction

    @Test func test_paradigm_predictionOne_returnsOne() {
        let p = Paradigm(id: "P1", name: "test", pPred: ["d1": 1, "d2": 0], relations: [])
        #expect(p.prediction("d1") == 1)
    }

    @Test func test_paradigm_predictionZero_returnsZero() {
        let p = Paradigm(id: "P1", name: "test", pPred: ["d1": 1, "d2": 0], relations: [])
        #expect(p.prediction("d2") == 0)
    }

    @Test func test_paradigm_predictionUnknown_returnsNil() {
        let p = Paradigm(id: "P1", name: "test", pPred: ["d1": 1, "d2": 0], relations: [])
        #expect(p.prediction("d3") == nil)
    }

    // MARK: - Neighbors & Threshold

    @Test func test_paradigm_neighborsDefaultEmpty() {
        let p = Paradigm(id: "P1", name: "test", pPred: ["d1": 1], relations: [])
        #expect(p.neighbors.isEmpty)
    }

    @Test func test_paradigm_shiftThresholdDefaultNil() {
        let p = Paradigm(id: "P1", name: "test", pPred: ["d1": 1], relations: [])
        #expect(p.shiftThreshold == nil)
    }
}

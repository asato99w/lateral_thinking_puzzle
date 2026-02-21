import Testing
@testable import LateralThinkingPuzzle

struct ParadigmTests {

    // MARK: - Validation

    @Test func test_paradigm_dPlusDMinusOverlap_throwsError() {
        #expect(throws: Paradigm.ValidationError.self) {
            _ = try Paradigm(
                id: "P1", name: "test",
                dPlus: ["d1", "d2"],
                dMinus: ["d2", "d3"],
                relations: []
            )
        }
    }

    @Test func test_paradigm_relationSrcNotInD_throwsError() {
        #expect(throws: Paradigm.ValidationError.self) {
            _ = try Paradigm(
                id: "P1", name: "test",
                dPlus: ["d1"],
                dMinus: ["d2"],
                relations: [Relation(src: "unknown", tgt: "d1", weight: 0.5)]
            )
        }
    }

    @Test func test_paradigm_relationTgtNotInD_throwsError() {
        #expect(throws: Paradigm.ValidationError.self) {
            _ = try Paradigm(
                id: "P1", name: "test",
                dPlus: ["d1"],
                dMinus: ["d2"],
                relations: [Relation(src: "d1", tgt: "unknown", weight: 0.5)]
            )
        }
    }

    @Test func test_paradigm_validData_doesNotThrow() throws {
        let p = try Paradigm(
            id: "P1", name: "test",
            dPlus: ["d1", "d2"],
            dMinus: ["d3"],
            relations: [Relation(src: "d1", tgt: "d2", weight: 0.8)]
        )
        #expect(p.dAll == Set(["d1", "d2", "d3"]))
    }

    // MARK: - Prediction

    @Test func test_paradigm_predictionDPlus_returnsOne() throws {
        let p = try Paradigm(id: "P1", name: "test", dPlus: ["d1"], dMinus: ["d2"], relations: [])
        #expect(p.prediction("d1") == 1)
    }

    @Test func test_paradigm_predictionDMinus_returnsZero() throws {
        let p = try Paradigm(id: "P1", name: "test", dPlus: ["d1"], dMinus: ["d2"], relations: [])
        #expect(p.prediction("d2") == 0)
    }

    @Test func test_paradigm_predictionUnknown_returnsNil() throws {
        let p = try Paradigm(id: "P1", name: "test", dPlus: ["d1"], dMinus: ["d2"], relations: [])
        #expect(p.prediction("d3") == nil)
    }
}

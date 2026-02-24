import Testing
@testable import LateralThinkingPuzzle

struct ParadigmTests {

    // MARK: - Validation

    @Test func test_paradigm_conceivableNotSubsetOfPPred_throwsError() {
        #expect(throws: Paradigm.ValidationError.self) {
            _ = try Paradigm(
                id: "P1", name: "test",
                pPred: ["d1": 1],
                conceivable: ["d1", "d2"], // d2 not in pPred
                relations: []
            )
        }
    }

    @Test func test_paradigm_relationSrcNotInConceivable_throwsError() {
        #expect(throws: Paradigm.ValidationError.self) {
            _ = try Paradigm(
                id: "P1", name: "test",
                pPred: ["d1": 1, "d2": 0],
                conceivable: ["d1", "d2"],
                relations: [Relation(src: "unknown", tgt: "d1", weight: 0.5)]
            )
        }
    }

    @Test func test_paradigm_relationTgtNotInConceivable_throwsError() {
        #expect(throws: Paradigm.ValidationError.self) {
            _ = try Paradigm(
                id: "P1", name: "test",
                pPred: ["d1": 1, "d2": 0],
                conceivable: ["d1", "d2"],
                relations: [Relation(src: "d1", tgt: "unknown", weight: 0.5)]
            )
        }
    }

    @Test func test_paradigm_validData_doesNotThrow() throws {
        let p = try Paradigm(
            id: "P1", name: "test",
            pPred: ["d1": 1, "d2": 1, "d3": 0],
            conceivable: ["d1", "d2", "d3"],
            relations: [Relation(src: "d1", tgt: "d2", weight: 0.8)]
        )
        #expect(p.conceivable == Set(["d1", "d2", "d3"]))
    }

    // MARK: - Prediction

    @Test func test_paradigm_predictionOne_returnsOne() throws {
        let p = try Paradigm(id: "P1", name: "test", pPred: ["d1": 1, "d2": 0], conceivable: ["d1", "d2"], relations: [])
        #expect(p.prediction("d1") == 1)
    }

    @Test func test_paradigm_predictionZero_returnsZero() throws {
        let p = try Paradigm(id: "P1", name: "test", pPred: ["d1": 1, "d2": 0], conceivable: ["d1", "d2"], relations: [])
        #expect(p.prediction("d2") == 0)
    }

    @Test func test_paradigm_predictionUnknown_returnsNil() throws {
        let p = try Paradigm(id: "P1", name: "test", pPred: ["d1": 1, "d2": 0], conceivable: ["d1", "d2"], relations: [])
        #expect(p.prediction("d3") == nil)
    }
}

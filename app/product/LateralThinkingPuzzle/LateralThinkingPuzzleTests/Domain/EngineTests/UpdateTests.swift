import Testing
@testable import LateralThinkingPuzzle

struct UpdateTests {

    // MARK: - Direct Update

    @Test func test_update_yesAnswer_updatesHAndO() {
        let p1 = TestPuzzleData.makeParadigm(pPred: ["d1": 1, "d2": 1, "d3": 0], conceivable: ["d1", "d2", "d3"])
        let q = TestPuzzleData.makeQuestion(id: "q1", ansYes: [("d1", 1)], ansNo: [("d1", 0)], ansIrrelevant: ["d1"], correctAnswer: .yes)
        var state = GameState(h: ["d1": 0.5, "d2": 0.5, "d3": 0.5], o: [:], r: [], pCurrent: "P1")

        _ = GameEngine.update(
            state: &state, question: q,
            paradigms: ["P1": p1], allQuestions: [q],
            currentOpen: [q]
        )

        #expect(state.h["d1"] == 1.0)
        #expect(state.o["d1"] == 1)
    }

    @Test func test_update_irrelevantAnswer_addsToR() {
        let p1 = TestPuzzleData.makeParadigm(pPred: ["d1": 1, "d3": 0], conceivable: ["d1", "d3"])
        let q = TestPuzzleData.makeQuestion(
            id: "q1", ansYes: [("d5", 1)], ansNo: [("d5", 0)], ansIrrelevant: ["d5"], correctAnswer: .irrelevant
        )
        var state = GameState(h: ["d1": 0.5, "d3": 0.5, "d5": 0.5], o: [:], r: [], pCurrent: "P1")

        _ = GameEngine.update(
            state: &state, question: q,
            paradigms: ["P1": p1], allQuestions: [q],
            currentOpen: [q]
        )

        #expect(state.r.contains("d5"))
    }

    @Test func test_update_marksQuestionAsAnswered() {
        let p1 = TestPuzzleData.makeParadigm(pPred: ["d1": 1, "d3": 0], conceivable: ["d1", "d3"])
        let q = TestPuzzleData.makeQuestion(id: "q1", ansYes: [("d1", 1)], ansNo: [("d1", 0)], ansIrrelevant: ["d1"], correctAnswer: .yes)
        var state = GameState(h: ["d1": 0.5, "d3": 0.5], o: [:], r: [], pCurrent: "P1")

        _ = GameEngine.update(
            state: &state, question: q,
            paradigms: ["P1": p1], allQuestions: [q],
            currentOpen: [q]
        )

        #expect(state.answered.contains("q1"))
    }

    // MARK: - Assimilation in Update

    @Test func test_update_matchingObservation_triggersAssimilation() {
        // P1: d1,d2 pred=1, relation d1->d2 (0.8)
        // Answer q1 with d1=1 (matches prediction) -> should assimilate d2
        let p1 = TestPuzzleData.makeParadigm(
            pPred: ["d1": 1, "d2": 1, "d3": 0],
            conceivable: ["d1", "d2", "d3"],
            relations: [Relation(src: "d1", tgt: "d2", weight: 0.8)]
        )
        let q = TestPuzzleData.makeQuestion(id: "q1", ansYes: [("d1", 1)], ansNo: [("d1", 0)], ansIrrelevant: ["d1"], correctAnswer: .yes)
        var state = GameState(h: ["d1": 0.5, "d2": 0.5, "d3": 0.5], o: [:], r: [], pCurrent: "P1")

        _ = GameEngine.update(
            state: &state, question: q,
            paradigms: ["P1": p1], allQuestions: [q],
            currentOpen: [q]
        )

        // d2 should be assimilated: 0.5 + 0.8*(1.0-0.5) = 0.9
        #expect(abs(state.h["d2"]! - 0.9) < 0.0001)
    }

    // MARK: - Paradigm Shift in Update

    @Test func test_update_tensionExceedsThreshold_triggersShift() {
        // P1: d1 pred=1, d3 pred=0, threshold=0
        // P2: d3 pred=1, d1 pred=0
        // Observe d1=0 (contradicts P1, matches P2) -> tension=1 > threshold=0
        var p1 = TestPuzzleData.makeParadigm(id: "P1", pPred: ["d1": 1, "d3": 0], conceivable: ["d1", "d3"])
        p1.threshold = 0
        let p2 = TestPuzzleData.makeParadigm(id: "P2", pPred: ["d3": 1, "d1": 0], conceivable: ["d1", "d3"])
        let q = TestPuzzleData.makeQuestion(id: "q1", ansYes: [("d1", 1)], ansNo: [("d1", 0)], ansIrrelevant: ["d1"], correctAnswer: .no)
        var state = GameState(h: ["d1": 0.5, "d3": 0.5], o: [:], r: [], pCurrent: "P1")

        _ = GameEngine.update(
            state: &state, question: q,
            paradigms: ["P1": p1, "P2": p2], allQuestions: [q],
            currentOpen: [q]
        )

        #expect(state.pCurrent == "P2")
    }

    @Test func test_update_noThreshold_noShift() {
        // threshold == nil -> no shift even with high tension
        let p1 = TestPuzzleData.makeParadigm(id: "P1", pPred: ["d1": 1, "d3": 0], conceivable: ["d1", "d3"])
        let p2 = TestPuzzleData.makeParadigm(id: "P2", pPred: ["d3": 1, "d1": 0], conceivable: ["d1", "d3"])
        let q = TestPuzzleData.makeQuestion(id: "q1", ansYes: [("d1", 1)], ansNo: [("d1", 0)], ansIrrelevant: ["d1"], correctAnswer: .no)
        var state = GameState(h: ["d1": 0.5, "d3": 0.5], o: [:], r: [], pCurrent: "P1")

        _ = GameEngine.update(
            state: &state, question: q,
            paradigms: ["P1": p1, "P2": p2], allQuestions: [q],
            currentOpen: [q]
        )

        #expect(state.pCurrent == "P1") // no shift (threshold is nil)
    }

    @Test func test_update_tensionBelowThreshold_noShift() {
        // threshold=10, tension=1 -> no shift
        var p1 = TestPuzzleData.makeParadigm(id: "P1", pPred: ["d1": 1, "d3": 0], conceivable: ["d1", "d3"])
        p1.threshold = 10
        let p2 = TestPuzzleData.makeParadigm(id: "P2", pPred: ["d3": 1, "d1": 0], conceivable: ["d1", "d3"])
        let q = TestPuzzleData.makeQuestion(id: "q1", ansYes: [("d1", 1)], ansNo: [("d1", 0)], ansIrrelevant: ["d1"], correctAnswer: .no)
        var state = GameState(h: ["d1": 0.5, "d3": 0.5], o: [:], r: [], pCurrent: "P1")

        _ = GameEngine.update(
            state: &state, question: q,
            paradigms: ["P1": p1, "P2": p2], allQuestions: [q],
            currentOpen: [q]
        )

        #expect(state.pCurrent == "P1") // no shift
    }

    // MARK: - Open Questions Update

    @Test func test_update_removesAnsweredQuestionFromOpen() {
        let p1 = TestPuzzleData.makeParadigm(pPred: ["d1": 1, "d3": 0], conceivable: ["d1", "d3"])
        let q1 = TestPuzzleData.makeQuestion(id: "q1", ansYes: [("d1", 1)], ansNo: [("d1", 0)], ansIrrelevant: ["d1"], correctAnswer: .yes)
        let q2 = TestPuzzleData.makeQuestion(id: "q2", ansYes: [("d3", 1)], ansNo: [("d3", 0)], ansIrrelevant: ["d3"], correctAnswer: .yes)
        var state = GameState(h: ["d1": 0.5, "d3": 0.5], o: [:], r: [], pCurrent: "P1")

        let newOpen = GameEngine.update(
            state: &state, question: q1,
            paradigms: ["P1": p1], allQuestions: [q1, q2],
            currentOpen: [q1, q2]
        )

        #expect(!newOpen.contains(where: { $0.id == "q1" }))
    }

    // MARK: - ExplainedO-Based Candidate Filtering

    @Test func test_update_nonExplainingParadigm_notShiftCandidate() {
        // P1 shares descriptors with P2 but NOT with P3
        // P3 can't explain any observations -> not a candidate
        var p1 = TestPuzzleData.makeParadigm(id: "P1", pPred: ["d1": 1, "d3": 0], conceivable: ["d1", "d3"])
        p1.threshold = 0
        let p2 = TestPuzzleData.makeParadigm(id: "P2", pPred: ["d3": 1, "d1": 0], conceivable: ["d1", "d3"])
        let p3 = TestPuzzleData.makeParadigm(id: "P3", pPred: ["d5": 1, "d6": 0], conceivable: ["d5", "d6"])
        let q = TestPuzzleData.makeQuestion(id: "q1", ansYes: [("d1", 1)], ansNo: [("d1", 0)], ansIrrelevant: ["d1"], correctAnswer: .no)
        var state = GameState(h: ["d1": 0.5, "d3": 0.5, "d5": 0.5, "d6": 0.5], o: [:], r: [], pCurrent: "P1")

        _ = GameEngine.update(
            state: &state, question: q,
            paradigms: ["P1": p1, "P2": p2, "P3": p3], allQuestions: [q],
            currentOpen: [q]
        )

        // Shifts to P2 (explains more O), not P3 (explains nothing in O)
        #expect(state.pCurrent == "P2")
    }
}

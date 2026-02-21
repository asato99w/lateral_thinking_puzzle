import Testing
@testable import LateralThinkingPuzzle

struct UpdateTests {

    // MARK: - Direct Update

    @Test func test_update_yesAnswer_updatesHAndO() {
        let p1 = TestPuzzleData.makeParadigm(dPlus: ["d1", "d2"], dMinus: ["d3"])
        let q = TestPuzzleData.makeQuestion(id: "q1", ansYes: [("d1", 1)], correctAnswer: .yes)
        var state = GameState(h: ["d1": 0.5, "d2": 0.5, "d3": 0.5], o: [:], r: [], pCurrent: "P1")

        _ = GameEngine.update(
            state: &state, question: q,
            paradigms: ["P1": p1], allQuestions: [q],
            currentOpen: [q], tensionThreshold: 10
        )

        #expect(state.h["d1"] == 1.0)
        #expect(state.o["d1"] == 1)
    }

    @Test func test_update_irrelevantAnswer_addsToR() {
        let p1 = TestPuzzleData.makeParadigm(dPlus: ["d1"], dMinus: ["d3"])
        let q = TestPuzzleData.makeQuestion(
            id: "q1", ansIrrelevant: ["d5"], correctAnswer: .irrelevant
        )
        var state = GameState(h: ["d1": 0.5, "d3": 0.5, "d5": 0.5], o: [:], r: [], pCurrent: "P1")

        _ = GameEngine.update(
            state: &state, question: q,
            paradigms: ["P1": p1], allQuestions: [q],
            currentOpen: [q], tensionThreshold: 10
        )

        #expect(state.r.contains("d5"))
    }

    @Test func test_update_marksQuestionAsAnswered() {
        let p1 = TestPuzzleData.makeParadigm(dPlus: ["d1"], dMinus: ["d3"])
        let q = TestPuzzleData.makeQuestion(id: "q1", ansYes: [("d1", 1)], correctAnswer: .yes)
        var state = GameState(h: ["d1": 0.5, "d3": 0.5], o: [:], r: [], pCurrent: "P1")

        _ = GameEngine.update(
            state: &state, question: q,
            paradigms: ["P1": p1], allQuestions: [q],
            currentOpen: [q], tensionThreshold: 10
        )

        #expect(state.answered.contains("q1"))
    }

    // MARK: - Assimilation in Update

    @Test func test_update_matchingObservation_triggersAssimilation() {
        // P1: dPlus=[d1,d2], relation d1→d2 (0.8)
        // Answer q1 with d1=1 (matches prediction) → should assimilate d2
        let p1 = TestPuzzleData.makeParadigm(
            dPlus: ["d1", "d2"], dMinus: ["d3"],
            relations: [Relation(src: "d1", tgt: "d2", weight: 0.8)]
        )
        let q = TestPuzzleData.makeQuestion(id: "q1", ansYes: [("d1", 1)], correctAnswer: .yes)
        var state = GameState(h: ["d1": 0.5, "d2": 0.5, "d3": 0.5], o: [:], r: [], pCurrent: "P1")

        _ = GameEngine.update(
            state: &state, question: q,
            paradigms: ["P1": p1], allQuestions: [q],
            currentOpen: [q], tensionThreshold: 10
        )

        // d2 should be assimilated: 0.5 + 0.8*(1.0-0.5) = 0.9
        #expect(abs(state.h["d2"]! - 0.9) < 0.0001)
    }

    // MARK: - Paradigm Shift in Update

    @Test func test_update_tensionExceedsThreshold_triggersShift() {
        // P1: dPlus=[d1], dMinus=[d3]
        // P2: dPlus=[d3], dMinus=[d1]
        // Observe d1=0 (contradicts P1, matches P2) → tension=1 > threshold=0
        let p1 = TestPuzzleData.makeParadigm(id: "P1", dPlus: ["d1"], dMinus: ["d3"])
        let p2 = TestPuzzleData.makeParadigm(id: "P2", dPlus: ["d3"], dMinus: ["d1"])
        let q = TestPuzzleData.makeQuestion(id: "q1", ansNo: [("d1", 0)], correctAnswer: .no)
        var state = GameState(h: ["d1": 0.5, "d3": 0.5], o: [:], r: [], pCurrent: "P1")

        _ = GameEngine.update(
            state: &state, question: q,
            paradigms: ["P1": p1, "P2": p2], allQuestions: [q],
            currentOpen: [q], tensionThreshold: 0
        )

        #expect(state.pCurrent == "P2")
    }

    @Test func test_update_tensionBelowThreshold_noShift() {
        let p1 = TestPuzzleData.makeParadigm(id: "P1", dPlus: ["d1"], dMinus: ["d3"])
        let p2 = TestPuzzleData.makeParadigm(id: "P2", dPlus: ["d3"], dMinus: ["d1"])
        let q = TestPuzzleData.makeQuestion(id: "q1", ansNo: [("d1", 0)], correctAnswer: .no)
        var state = GameState(h: ["d1": 0.5, "d3": 0.5], o: [:], r: [], pCurrent: "P1")

        _ = GameEngine.update(
            state: &state, question: q,
            paradigms: ["P1": p1, "P2": p2], allQuestions: [q],
            currentOpen: [q], tensionThreshold: 10 // high threshold
        )

        #expect(state.pCurrent == "P1") // no shift
    }

    // MARK: - Open Questions Update

    @Test func test_update_removesAnsweredQuestionFromOpen() {
        let p1 = TestPuzzleData.makeParadigm(dPlus: ["d1"], dMinus: ["d3"])
        let q1 = TestPuzzleData.makeQuestion(id: "q1", ansYes: [("d1", 1)], correctAnswer: .yes)
        let q2 = TestPuzzleData.makeQuestion(id: "q2", ansYes: [("d3", 1)], correctAnswer: .yes)
        var state = GameState(h: ["d1": 0.5, "d3": 0.5], o: [:], r: [], pCurrent: "P1")

        let newOpen = GameEngine.update(
            state: &state, question: q1,
            paradigms: ["P1": p1], allQuestions: [q1, q2],
            currentOpen: [q1, q2], tensionThreshold: 10
        )

        #expect(!newOpen.contains(where: { $0.id == "q1" }))
    }

    // MARK: - Shift Candidates

    @Test func test_update_shiftCandidates_limitsShiftTargets() {
        let p1 = TestPuzzleData.makeParadigm(id: "P1", dPlus: ["d1"], dMinus: ["d3"])
        let p2 = TestPuzzleData.makeParadigm(id: "P2", dPlus: ["d3"], dMinus: ["d1"])
        let p3 = TestPuzzleData.makeParadigm(id: "P3", dPlus: ["d3"], dMinus: ["d1"])
        let q = TestPuzzleData.makeQuestion(id: "q1", ansNo: [("d1", 0)], correctAnswer: .no)
        var state = GameState(h: ["d1": 0.5, "d3": 0.5], o: [:], r: [], pCurrent: "P1")

        // Only P3 is a candidate, not P2
        _ = GameEngine.update(
            state: &state, question: q,
            paradigms: ["P1": p1, "P2": p2, "P3": p3], allQuestions: [q],
            currentOpen: [q], tensionThreshold: 0,
            shiftCandidates: ["P1": ["P3"]]
        )

        #expect(state.pCurrent == "P3")
    }
}

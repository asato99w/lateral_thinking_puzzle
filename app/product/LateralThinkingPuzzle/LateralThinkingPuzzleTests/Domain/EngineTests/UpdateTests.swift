import Testing
@testable import LateralThinkingPuzzle

struct UpdateTests {

    // MARK: - Direct Update

    @Test func test_update_yesAnswer_updatesHAndO() {
        let p1 = TestPuzzleData.makeParadigm(pPred: ["d1": 1, "d2": 1, "d3": 0])
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
        let p1 = TestPuzzleData.makeParadigm(pPred: ["d1": 1, "d3": 0])
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
        let p1 = TestPuzzleData.makeParadigm(pPred: ["d1": 1, "d3": 0])
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
        let p1 = TestPuzzleData.makeParadigm(
            pPred: ["d1": 1, "d2": 1, "d3": 0],
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

    // MARK: - Paradigm Shift in Update (neighbors + resolve model)

    @Test func test_update_neighborsAndResolve_triggersShift() {
        // P1: d1=1, d3=0. P2: d3=1, d1=0.
        // P1 has P2 as neighbor, P2 shiftThreshold=1
        // Observe d1=0 -> P1 anomaly={d1}, P2 resolves d1 (pred=0=observed) -> resolve=1 >= threshold=1
        // tension(P2) < tension(P1) -> shift
        let p1 = TestPuzzleData.makeParadigm(id: "P1", pPred: ["d1": 1, "d3": 0], neighbors: ["P2"])
        let p2 = TestPuzzleData.makeParadigm(id: "P2", pPred: ["d3": 1, "d1": 0], shiftThreshold: 1)
        let q = TestPuzzleData.makeQuestion(id: "q1", ansYes: [("d1", 1)], ansNo: [("d1", 0)], ansIrrelevant: ["d1"], correctAnswer: .no)
        var state = GameState(h: ["d1": 0.5, "d3": 0.5], o: [:], r: [], pCurrent: "P1")

        _ = GameEngine.update(
            state: &state, question: q,
            paradigms: ["P1": p1, "P2": p2], allQuestions: [q],
            currentOpen: [q]
        )

        #expect(state.pCurrent == "P2")
    }

    @Test func test_update_notInNeighbors_noShift() {
        // P1 has no neighbors -> no shift possible
        let p1 = TestPuzzleData.makeParadigm(id: "P1", pPred: ["d1": 1, "d3": 0], neighbors: [])
        let p2 = TestPuzzleData.makeParadigm(id: "P2", pPred: ["d3": 1, "d1": 0], shiftThreshold: 1)
        let q = TestPuzzleData.makeQuestion(id: "q1", ansYes: [("d1", 1)], ansNo: [("d1", 0)], ansIrrelevant: ["d1"], correctAnswer: .no)
        var state = GameState(h: ["d1": 0.5, "d3": 0.5], o: [:], r: [], pCurrent: "P1")

        _ = GameEngine.update(
            state: &state, question: q,
            paradigms: ["P1": p1, "P2": p2], allQuestions: [q],
            currentOpen: [q]
        )

        #expect(state.pCurrent == "P1")
    }

    @Test func test_update_resolveBelowThreshold_noShift() {
        // P2 shiftThreshold=10, resolve=1 < 10 -> no shift
        let p1 = TestPuzzleData.makeParadigm(id: "P1", pPred: ["d1": 1, "d3": 0], neighbors: ["P2"])
        let p2 = TestPuzzleData.makeParadigm(id: "P2", pPred: ["d3": 1, "d1": 0], shiftThreshold: 10)
        let q = TestPuzzleData.makeQuestion(id: "q1", ansYes: [("d1", 1)], ansNo: [("d1", 0)], ansIrrelevant: ["d1"], correctAnswer: .no)
        var state = GameState(h: ["d1": 0.5, "d3": 0.5], o: [:], r: [], pCurrent: "P1")

        _ = GameEngine.update(
            state: &state, question: q,
            paradigms: ["P1": p1, "P2": p2], allQuestions: [q],
            currentOpen: [q]
        )

        #expect(state.pCurrent == "P1")
    }

    // MARK: - Open Questions Update

    @Test func test_update_removesAnsweredQuestionFromOpen() {
        let p1 = TestPuzzleData.makeParadigm(pPred: ["d1": 1, "d3": 0])
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
}

import Testing
@testable import LateralThinkingPuzzle

struct StartGameUseCaseTests {

    @Test func test_execute_withInitQuestionIDs_returnsSpecifiedQuestions() {
        let p1 = TestPuzzleData.makeParadigm(
            id: "P1",
            pPred: ["d1": 1, "d2": 1, "d3": 0],
            relations: [Relation(src: "d1", tgt: "d2", weight: 0.8)]
        )
        let q1 = TestPuzzleData.makeQuestion(id: "q1", ansYes: [("d1", 1)], ansNo: [("d1", 0)], ansIrrelevant: ["d1"], correctAnswer: .yes)
        let q2 = TestPuzzleData.makeQuestion(id: "q2", ansYes: [("d3", 1)], ansNo: [("d3", 0)], ansIrrelevant: ["d3"], correctAnswer: .yes)

        let puzzle = PuzzleData(
            title: "Test",
            statement: "Test statement",
            initParadigm: "P1",
            psValues: [("d1", 1)],
            allDescriptorIDs: ["d1", "d2", "d3"],
            paradigms: ["P1": p1],
            questions: [q1, q2],
            tier: .free,
            topicCategories: [],
            initQuestionIDs: ["q1"]
        )

        let useCase = StartGameUseCase()
        let result = useCase.execute(puzzle: puzzle)

        #expect(result.state.pCurrent == "P1")
        #expect(result.state.o["d1"] == 1)
        #expect(result.openQuestions.contains(where: { $0.id == "q1" }))
        #expect(!result.openQuestions.contains(where: { $0.id == "q2" }))
    }

    @Test func test_execute_withoutInitQuestionIDs_fallsBackToOpenQuestions() {
        let p1 = TestPuzzleData.makeParadigm(
            id: "P1",
            pPred: ["d1": 1, "d2": 1, "d3": 0],
            relations: [Relation(src: "d1", tgt: "d2", weight: 0.8)]
        )
        let q1 = TestPuzzleData.makeQuestion(id: "q1", ansYes: [("d2", 1)], ansNo: [("d2", 0)], ansIrrelevant: ["d2"], correctAnswer: .yes, paradigms: ["P1"])

        let puzzle = PuzzleData(
            title: "Test",
            statement: "Test statement",
            initParadigm: "P1",
            psValues: [("d1", 1)],
            allDescriptorIDs: ["d1", "d2", "d3"],
            paradigms: ["P1": p1],
            questions: [q1],
            tier: .free,
            topicCategories: [],
            initQuestionIDs: nil
        )

        let useCase = StartGameUseCase()
        let result = useCase.execute(puzzle: puzzle)

        #expect(result.state.pCurrent == "P1")
        // d1=1 consistent with P1 pred, d1->d2 relation -> d2 reachable -> q1 opens
        #expect(result.openQuestions.contains(where: { $0.id == "q1" }))
    }
}

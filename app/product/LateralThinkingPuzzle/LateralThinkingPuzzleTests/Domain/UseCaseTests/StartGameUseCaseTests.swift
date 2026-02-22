import Testing
@testable import LateralThinkingPuzzle

struct StartGameUseCaseTests {

    @Test func test_execute_returnsInitialStateAndOpenQuestions() {
        let p1 = TestPuzzleData.makeParadigm(
            id: "P1", dPlus: ["d1", "d2"], dMinus: ["d3"],
            relations: [Relation(src: "d1", tgt: "d2", weight: 0.8)]
        )
        let q1 = TestPuzzleData.makeQuestion(id: "q1", ansYes: [("d1", 1)], correctAnswer: .yes)
        let q2 = TestPuzzleData.makeQuestion(id: "q2", ansYes: [("d3", 1)], correctAnswer: .yes) // d3=1, pred=0 → no match

        let puzzle = PuzzleData(
            title: "Test",
            statement: "Test statement",
            initParadigm: "P1",
            psValues: [("d1", 1)],
            allDescriptorIDs: ["d1", "d2", "d3"],
            paradigms: ["P1": p1],
            questions: [q1, q2],
            tier: .free
        )

        let useCase = StartGameUseCase()
        let result = useCase.execute(puzzle: puzzle)

        #expect(result.state.pCurrent == "P1")
        #expect(result.state.o["d1"] == 1)
        #expect(result.openQuestions.contains(where: { $0.id == "q1" }))
        #expect(!result.openQuestions.contains(where: { $0.id == "q2" }))
    }
}

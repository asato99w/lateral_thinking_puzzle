import Testing
@testable import LateralThinkingPuzzle

@MainActor
struct GameViewModelTests {

    @Test func test_init_setsUpInitialState() {
        let p1 = TestPuzzleData.makeParadigm(
            id: "P1",
            pPred: ["d1": 1, "d2": 1, "d3": 0],
            conceivable: ["d1", "d2", "d3"],
            relations: [Relation(src: "d1", tgt: "d2", weight: 0.8)]
        )
        let q1 = TestPuzzleData.makeQuestion(id: "q1", ansYes: [("d1", 1)], ansNo: [("d1", 0)], ansIrrelevant: ["d1"], correctAnswer: .yes)

        let puzzle = PuzzleData(
            title: "Test", statement: "Test",
            initParadigm: "P1", psValues: [("d1", 1)],
            allDescriptorIDs: ["d1", "d2", "d3"],
            paradigms: ["P1": p1], questions: [q1], tier: .free
        )

        let vm = GameViewModel(puzzle: puzzle)

        #expect(!vm.isCleared)
        #expect(vm.answeredQuestions.isEmpty)
        #expect(!vm.openQuestions.isEmpty)
    }

    @Test func test_selectQuestion_movesQuestionToAnswered() {
        let p1 = TestPuzzleData.makeParadigm(
            id: "P1",
            pPred: ["d1": 1, "d2": 1, "d3": 0],
            conceivable: ["d1", "d2", "d3"],
            relations: []
        )
        let q1 = TestPuzzleData.makeQuestion(id: "q1", ansYes: [("d1", 1)], ansNo: [("d1", 0)], ansIrrelevant: ["d1"], correctAnswer: .yes)

        let puzzle = PuzzleData(
            title: "Test", statement: "Test",
            initParadigm: "P1", psValues: [],
            allDescriptorIDs: ["d1", "d2", "d3"],
            paradigms: ["P1": p1], questions: [q1], tier: .free
        )

        let vm = GameViewModel(puzzle: puzzle)
        let questionToAnswer = vm.openQuestions.first!

        vm.selectQuestion(questionToAnswer)

        #expect(vm.answeredQuestions.count == 1)
        #expect(vm.answeredQuestions[0].question.id == questionToAnswer.id)
    }

    @Test func test_selectClearQuestion_setsIsCleared() {
        let p1 = TestPuzzleData.makeParadigm(
            id: "P1",
            pPred: ["d1": 1, "d3": 0],
            conceivable: ["d1", "d3"],
            relations: []
        )
        let q1 = TestPuzzleData.makeQuestion(id: "q1", ansYes: [("d1", 1)], ansNo: [("d1", 0)], ansIrrelevant: ["d1"], correctAnswer: .yes, isClear: true)

        let puzzle = PuzzleData(
            title: "Test", statement: "Test",
            initParadigm: "P1", psValues: [],
            allDescriptorIDs: ["d1", "d3"],
            paradigms: ["P1": p1], questions: [q1], tier: .free
        )

        let vm = GameViewModel(puzzle: puzzle)
        guard let question = vm.openQuestions.first else {
            Issue.record("No open questions")
            return
        }

        vm.selectQuestion(question)

        #expect(vm.isCleared)
    }
}

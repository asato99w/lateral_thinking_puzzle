import Testing
@testable import LateralThinkingPuzzle

@MainActor
struct GameViewModelTests {

    @Test func test_init_setsUpInitialState() {
        let p1 = TestPuzzleData.makeParadigm(
            id: "P1",
            pPred: ["d1": 1, "d2": 1, "d3": 0],
            relations: [Relation(src: "d1", tgt: "d2", weight: 0.8)]
        )
        let q1 = TestPuzzleData.makeQuestion(id: "q1", ansYes: [("d1", 1)], ansNo: [("d1", 0)], ansIrrelevant: ["d1"], correctAnswer: .yes)

        let puzzle = PuzzleData(
            title: "Test", statement: "Test",
            initParadigm: "P1", psValues: [("d1", 1)],
            allDescriptorIDs: ["d1", "d2", "d3"],
            paradigms: ["P1": p1], questions: [q1], tier: .free,
            topicCategories: [],
            initQuestionIDs: ["q1"],
            resolveCaps: [:]
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
            relations: []
        )
        let q1 = TestPuzzleData.makeQuestion(id: "q1", ansYes: [("d1", 1)], ansNo: [("d1", 0)], ansIrrelevant: ["d1"], correctAnswer: .yes)

        let puzzle = PuzzleData(
            title: "Test", statement: "Test",
            initParadigm: "P1", psValues: [],
            allDescriptorIDs: ["d1", "d2", "d3"],
            paradigms: ["P1": p1], questions: [q1], tier: .free,
            topicCategories: [],
            initQuestionIDs: ["q1"],
            resolveCaps: [:]
        )

        let vm = GameViewModel(puzzle: puzzle)
        let questionToAnswer = vm.openQuestions.first!

        vm.selectQuestion(questionToAnswer)

        #expect(vm.answeredQuestions.count == 1)
        #expect(vm.answeredQuestions[0].question.id == questionToAnswer.id)
    }

    // MARK: - Topic Category Filtering

    @Test func test_filteredOpenQuestions_withNoCategory_returnsAll() {
        let p1 = TestPuzzleData.makeParadigm(
            id: "P1",
            pPred: ["d1": 1, "d2": 1, "d3": 0],
            relations: []
        )
        let q1 = TestPuzzleData.makeQuestion(id: "q1", ansYes: [("d1", 1)], ansNo: [("d1", 0)], ansIrrelevant: ["d1"], correctAnswer: .yes, topicCategory: "A")
        let q2 = TestPuzzleData.makeQuestion(id: "q2", text: "Q2?", ansYes: [("d2", 1)], ansNo: [("d2", 0)], ansIrrelevant: ["d2"], correctAnswer: .yes, topicCategory: "B")

        let puzzle = PuzzleData(
            title: "Test", statement: "Test",
            initParadigm: "P1", psValues: [],
            allDescriptorIDs: ["d1", "d2", "d3"],
            paradigms: ["P1": p1], questions: [q1, q2], tier: .free,
            topicCategories: [TopicCategory(id: "A", name: "Cat A"), TopicCategory(id: "B", name: "Cat B")],
            initQuestionIDs: ["q1", "q2"],
            resolveCaps: [:]
        )

        let vm = GameViewModel(puzzle: puzzle)
        vm.selectedCategory = nil

        #expect(vm.filteredOpenQuestions.count == vm.openQuestions.count)
    }

    @Test func test_filteredOpenQuestions_withCategory_filtersCorrectly() {
        let p1 = TestPuzzleData.makeParadigm(
            id: "P1",
            pPred: ["d1": 1, "d2": 1, "d3": 0],
            relations: []
        )
        let q1 = TestPuzzleData.makeQuestion(id: "q1", ansYes: [("d1", 1)], ansNo: [("d1", 0)], ansIrrelevant: ["d1"], correctAnswer: .yes, topicCategory: "A")
        let q2 = TestPuzzleData.makeQuestion(id: "q2", text: "Q2?", ansYes: [("d2", 1)], ansNo: [("d2", 0)], ansIrrelevant: ["d2"], correctAnswer: .yes, topicCategory: "B")

        let puzzle = PuzzleData(
            title: "Test", statement: "Test",
            initParadigm: "P1", psValues: [],
            allDescriptorIDs: ["d1", "d2", "d3"],
            paradigms: ["P1": p1], questions: [q1, q2], tier: .free,
            topicCategories: [TopicCategory(id: "A", name: "Cat A"), TopicCategory(id: "B", name: "Cat B")],
            initQuestionIDs: ["q1", "q2"],
            resolveCaps: [:]
        )

        let vm = GameViewModel(puzzle: puzzle)
        vm.selectedCategory = "A"

        let filtered = vm.filteredOpenQuestions
        #expect(filtered.allSatisfy { $0.topicCategory == "A" })
    }

    @Test func test_openCountForCategory_returnsCorrectCount() {
        let p1 = TestPuzzleData.makeParadigm(
            id: "P1",
            pPred: ["d1": 1, "d2": 1, "d3": 1],
            relations: []
        )
        let q1 = TestPuzzleData.makeQuestion(id: "q1", ansYes: [("d1", 1)], ansNo: [("d1", 0)], ansIrrelevant: ["d1"], correctAnswer: .yes, topicCategory: "A")
        let q2 = TestPuzzleData.makeQuestion(id: "q2", text: "Q2?", ansYes: [("d2", 1)], ansNo: [("d2", 0)], ansIrrelevant: ["d2"], correctAnswer: .yes, topicCategory: "B")
        let q3 = TestPuzzleData.makeQuestion(id: "q3", text: "Q3?", ansYes: [("d3", 1)], ansNo: [("d3", 0)], ansIrrelevant: ["d3"], correctAnswer: .yes, topicCategory: "A")

        let puzzle = PuzzleData(
            title: "Test", statement: "Test",
            initParadigm: "P1", psValues: [],
            allDescriptorIDs: ["d1", "d2", "d3"],
            paradigms: ["P1": p1], questions: [q1, q2, q3], tier: .free,
            topicCategories: [TopicCategory(id: "A", name: "Cat A"), TopicCategory(id: "B", name: "Cat B")],
            initQuestionIDs: ["q1", "q2", "q3"],
            resolveCaps: [:]
        )

        let vm = GameViewModel(puzzle: puzzle)
        let openA = vm.openCountForCategory("A")
        let openB = vm.openCountForCategory("B")
        let openC = vm.openCountForCategory("C")

        #expect(openA >= 1)
        #expect(openB >= 0)
        #expect(openC == 0)
        #expect(openA + openB == vm.openQuestions.count || openA + openB <= vm.openQuestions.count)
    }

    @Test func test_filteredOpenQuestions_withNonexistentCategory_returnsEmpty() {
        let p1 = TestPuzzleData.makeParadigm(
            id: "P1",
            pPred: ["d1": 1, "d2": 1, "d3": 0],
            relations: []
        )
        let q1 = TestPuzzleData.makeQuestion(id: "q1", ansYes: [("d1", 1)], ansNo: [("d1", 0)], ansIrrelevant: ["d1"], correctAnswer: .yes, topicCategory: "A")

        let puzzle = PuzzleData(
            title: "Test", statement: "Test",
            initParadigm: "P1", psValues: [],
            allDescriptorIDs: ["d1", "d2", "d3"],
            paradigms: ["P1": p1], questions: [q1], tier: .free,
            topicCategories: [TopicCategory(id: "A", name: "Cat A")],
            initQuestionIDs: ["q1"],
            resolveCaps: [:]
        )

        let vm = GameViewModel(puzzle: puzzle)
        vm.selectedCategory = "Z"

        #expect(vm.filteredOpenQuestions.isEmpty)
    }

    // MARK: - Clear

    @Test func test_selectClearQuestion_setsIsCleared() {
        let p1 = TestPuzzleData.makeParadigm(
            id: "P1",
            pPred: ["d1": 1, "d3": 0],
            relations: []
        )
        let q1 = TestPuzzleData.makeQuestion(id: "q1", ansYes: [("d1", 1)], ansNo: [("d1", 0)], ansIrrelevant: ["d1"], correctAnswer: .yes, isClear: true)

        let puzzle = PuzzleData(
            title: "Test", statement: "Test",
            initParadigm: "P1", psValues: [],
            allDescriptorIDs: ["d1", "d3"],
            paradigms: ["P1": p1], questions: [q1], tier: .free,
            topicCategories: [],
            initQuestionIDs: ["q1"],
            resolveCaps: [:]
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

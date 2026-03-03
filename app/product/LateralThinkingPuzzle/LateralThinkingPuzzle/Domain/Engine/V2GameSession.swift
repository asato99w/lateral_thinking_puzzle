struct V2GameSession: GameSession {
    let puzzle: V2PuzzleData
    private(set) var state: V2GameState
    private var questionMap: [String: V2Question]

    var puzzleInfo: PuzzleInfo {
        PuzzleInfo(
            title: puzzle.title,
            statement: puzzle.statement,
            truth: puzzle.truth,
            topicCategories: puzzle.topicCategories
        )
    }

    init(puzzle: V2PuzzleData) {
        self.puzzle = puzzle
        self.state = V2GameEngine.initGame(puzzle: puzzle)
        self.questionMap = puzzle.questions
    }

    mutating func start() -> GameSessionStartResult {
        let available = V2GameEngine.availableQuestions(state: state, puzzle: puzzle)
        let questions = available.map { mapToQuestion($0) }
        return GameSessionStartResult(openQuestions: questions)
    }

    mutating func selectQuestion(_ question: Question) -> GameSessionUpdateResult {
        guard let v2q = questionMap[question.id] else {
            return GameSessionUpdateResult(openQuestions: [], isCleared: true, newQuestionIDs: [])
        }

        let previousAnswered = state.answered
        _ = V2GameEngine.answerQuestion(state: &state, question: v2q, puzzle: puzzle)

        let available = V2GameEngine.availableQuestions(state: state, puzzle: puzzle)
        let openQuestions = available.map { mapToQuestion($0) }

        let newIDs = Set(openQuestions.map(\.id)).subtracting(
            Set(openQuestions.map(\.id)).intersection(previousAnswered)
        )

        let isCleared = V2GameEngine.checkComplete(state: state, puzzle: puzzle)

        return GameSessionUpdateResult(
            openQuestions: openQuestions,
            isCleared: isCleared,
            newQuestionIDs: newIDs
        )
    }

    // MARK: - Private

    private func mapToQuestion(_ v2q: V2Question) -> Question {
        Question(
            id: v2q.id,
            text: v2q.text,
            ansYes: [],
            ansNo: [],
            ansIrrelevant: [],
            correctAnswer: v2q.correctAnswer,
            isClear: false,
            prerequisites: [],
            relatedDescriptors: [],
            topicCategory: v2q.topicCategory,
            paradigms: []
        )
    }
}

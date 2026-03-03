struct V1GameSession: GameSession {
    let puzzle: PuzzleData
    private(set) var state: GameState
    private(set) var currentOpen: [Question]

    var puzzleInfo: PuzzleInfo { puzzle.puzzleInfo }

    init(puzzle: PuzzleData) {
        self.puzzle = puzzle
        let result = StartGameUseCase().execute(puzzle: puzzle)
        self.state = result.state
        self.currentOpen = result.openQuestions
    }

    mutating func start() -> GameSessionStartResult {
        GameSessionStartResult(openQuestions: currentOpen)
    }

    mutating func selectQuestion(_ question: Question) -> GameSessionUpdateResult {
        let result = AnswerQuestionUseCase().execute(
            state: &state,
            question: question,
            puzzle: puzzle,
            currentOpen: currentOpen
        )

        state = result.state
        currentOpen = result.openQuestions

        var newIDs = Set<String>()
        for event in result.events {
            if case .questionsOpened(let ids) = event {
                newIDs = Set(ids)
            }
        }

        let isCleared = result.events.contains(.puzzleCleared)

        return GameSessionUpdateResult(
            openQuestions: currentOpen,
            isCleared: isCleared,
            newQuestionIDs: newIDs
        )
    }
}

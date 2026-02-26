struct StartGameResult: Sendable {
    let state: GameState
    let openQuestions: [Question]
}

struct StartGameUseCase: Sendable {
    func execute(puzzle: PuzzleData) -> StartGameResult {
        let state = GameEngine.initGame(
            psValues: puzzle.psValues,
            paradigms: puzzle.paradigms,
            initParadigmID: puzzle.initParadigm,
            allDescriptorIDs: puzzle.allDescriptorIDs
        )
        let open: [Question]
        if let ids = puzzle.initQuestionIDs {
            open = GameEngine.initQuestions(questions: puzzle.questions, initQuestionIDs: ids)
        } else {
            // フォールバック: openQuestions で初期リストを生成
            open = GameEngine.openQuestions(state: state, questions: puzzle.questions, paradigms: puzzle.paradigms)
        }
        return StartGameResult(state: state, openQuestions: open)
    }
}

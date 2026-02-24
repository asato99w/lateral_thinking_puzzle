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
        let initialParadigm = puzzle.paradigms[puzzle.initParadigm]!
        let open = GameEngine.initQuestions(paradigm: initialParadigm, questions: puzzle.questions, o: state.o)
        return StartGameResult(state: state, openQuestions: open)
    }
}

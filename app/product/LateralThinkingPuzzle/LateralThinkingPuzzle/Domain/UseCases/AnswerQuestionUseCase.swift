enum GameEvent: Equatable, Sendable {
    case questionAnswered(questionID: String, answer: Answer)
    case paradigmShifted(from: String, to: String)
    case questionsOpened(ids: [String])
    case puzzleCleared

    static func == (lhs: GameEvent, rhs: GameEvent) -> Bool {
        switch (lhs, rhs) {
        case let (.questionAnswered(id1, a1), .questionAnswered(id2, a2)):
            return id1 == id2 && a1 == a2
        case let (.paradigmShifted(f1, t1), .paradigmShifted(f2, t2)):
            return f1 == f2 && t1 == t2
        case let (.questionsOpened(ids1), .questionsOpened(ids2)):
            return ids1 == ids2
        case (.puzzleCleared, .puzzleCleared):
            return true
        default:
            return false
        }
    }
}

struct AnswerQuestionResult: Sendable {
    let state: GameState
    let openQuestions: [Question]
    let events: [GameEvent]
}

struct AnswerQuestionUseCase: Sendable {
    func execute(
        state: inout GameState,
        question: Question,
        puzzle: PuzzleData,
        currentOpen: [Question]
    ) -> AnswerQuestionResult {
        var events = [GameEvent]()
        let previousParadigm = state.pCurrent

        events.append(.questionAnswered(questionID: question.id, answer: question.correctAnswer))

        let newOpen = GameEngine.update(
            state: &state,
            question: question,
            paradigms: puzzle.paradigms,
            allQuestions: puzzle.questions,
            currentOpen: currentOpen
        )

        if state.pCurrent != previousParadigm {
            events.append(.paradigmShifted(from: previousParadigm, to: state.pCurrent))
        }

        let newIDs = Set(newOpen.map(\.id)).subtracting(Set(currentOpen.map(\.id)).subtracting([question.id]))
        if !newIDs.isEmpty {
            events.append(.questionsOpened(ids: newIDs.sorted()))
        }

        if GameEngine.checkClear(question: question) {
            events.append(.puzzleCleared)
        }

        return AnswerQuestionResult(state: state, openQuestions: newOpen, events: events)
    }
}

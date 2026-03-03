struct GameSessionStartResult: Sendable {
    let openQuestions: [Question]
}

struct GameSessionUpdateResult: Sendable {
    let openQuestions: [Question]
    let isCleared: Bool
    let newQuestionIDs: Set<String>
}

protocol GameSession: Sendable {
    var puzzleInfo: PuzzleInfo { get }
    mutating func start() -> GameSessionStartResult
    mutating func selectQuestion(_ question: Question) -> GameSessionUpdateResult
}

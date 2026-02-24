import Foundation
import Observation

@MainActor @Observable
final class GameViewModel {
    let puzzle: PuzzleData
    private(set) var state: GameState
    private(set) var openQuestions: [Question]
    private(set) var answeredQuestions: [(question: Question, answer: Answer)] = []
    private(set) var isCleared = false

    /// Whether the answered-questions section is expanded
    var showAnswered = false

    private let startGame = StartGameUseCase()
    private let answerQuestion = AnswerQuestionUseCase()

    init(puzzle: PuzzleData) {
        self.puzzle = puzzle
        let result = startGame.execute(puzzle: puzzle)
        self.state = result.state
        self.openQuestions = result.openQuestions
    }

    func selectQuestion(_ question: Question) {
        answeredQuestions.append((question: question, answer: question.correctAnswer))

        let result = answerQuestion.execute(
            state: &state,
            question: question,
            puzzle: puzzle,
            currentOpen: openQuestions
        )

        state = result.state
        openQuestions = result.openQuestions

        if result.events.contains(.puzzleCleared) {
            isCleared = true
        }
    }
}

import Foundation
import Observation

@MainActor @Observable
final class GameViewModel {
    let puzzleID: String
    let puzzle: PuzzleData
    private(set) var state: GameState
    private(set) var openQuestions: [Question]
    private(set) var answeredQuestions: [(question: Question, answer: Answer)] = []
    private(set) var isCleared = false

    /// Whether the answered-questions section is expanded
    var showAnswered = false

    /// Selected topic category filter (nil = show all)
    var selectedCategory: String?

    var filteredOpenQuestions: [Question] {
        guard let cat = selectedCategory else { return openQuestions }
        return openQuestions.filter { $0.topicCategory == cat }
    }

    func openCountForCategory(_ categoryID: String) -> Int {
        openQuestions.filter { $0.topicCategory == categoryID }.count
    }

    private let startGame = StartGameUseCase()
    private let answerQuestion = AnswerQuestionUseCase()

    init(puzzleID: String = "", puzzle: PuzzleData) {
        self.puzzleID = puzzleID
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
            SolvedPuzzleStore.shared.markSolved(puzzleID)
        }
    }
}

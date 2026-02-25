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

    /// IDs of questions newly opened by the last answer
    private(set) var newQuestionIDs: Set<String> = []

    /// Whether the answered-questions section is expanded
    var showAnswered = false

    /// Selected topic category filter (nil = show all)
    var selectedCategory: String?

    var filteredOpenQuestions: [Question] {
        let base: [Question]
        if let cat = selectedCategory {
            base = openQuestions.filter { $0.topicCategory == cat }
        } else {
            base = openQuestions
        }
        // New questions first so the slide-in animation is visible
        guard !newQuestionIDs.isEmpty else { return base }
        let new = base.filter { newQuestionIDs.contains($0.id) }
        let existing = base.filter { !newQuestionIDs.contains($0.id) }
        return new + existing
    }

    func openCountForCategory(_ categoryID: String) -> Int {
        openQuestions.filter { $0.topicCategory == categoryID }.count
    }

    func isNewQuestion(_ id: String) -> Bool {
        newQuestionIDs.contains(id)
    }

    func hasNewQuestions(inCategory categoryID: String) -> Bool {
        openQuestions.contains { $0.topicCategory == categoryID && newQuestionIDs.contains($0.id) }
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

        newQuestionIDs = []
        for event in result.events {
            if case .questionsOpened(let ids) = event {
                newQuestionIDs = Set(ids)
            }
        }

        if !newQuestionIDs.isEmpty {
            selectedCategory = nil
        }

        if result.events.contains(.puzzleCleared) {
            isCleared = true
            SolvedPuzzleStore.shared.markSolved(puzzleID)
        }
    }
}

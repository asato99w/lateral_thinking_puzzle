import Foundation
import Observation

@MainActor @Observable
final class GameViewModel {
    let puzzleID: String
    let puzzleInfo: PuzzleInfo
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

    private var session: any GameSession

    init(puzzleID: String = "", session: any GameSession) {
        self.puzzleID = puzzleID
        self.puzzleInfo = session.puzzleInfo
        var s = session
        let result = s.start()
        self.openQuestions = result.openQuestions
        self.session = s
    }

    func selectQuestion(_ question: Question) {
        answeredQuestions.append((question: question, answer: question.correctAnswer))

        var s = session
        let result = s.selectQuestion(question)
        session = s

        openQuestions = result.openQuestions
        newQuestionIDs = result.newQuestionIDs

        if !newQuestionIDs.isEmpty {
            selectedCategory = nil
        }

        if result.isCleared {
            isCleared = true
            SolvedPuzzleStore.shared.markSolved(puzzleID)
            saveHistory()
        }
    }

    private func saveHistory() {
        let entries = answeredQuestions.map {
            GameHistoryEntry(questionText: $0.question.text, answer: $0.answer.rawValue)
        }
        let history = GameHistory(puzzleID: puzzleID, puzzleTitle: puzzleInfo.title, entries: entries)
        GameHistoryStore.shared.save(history)
    }
}

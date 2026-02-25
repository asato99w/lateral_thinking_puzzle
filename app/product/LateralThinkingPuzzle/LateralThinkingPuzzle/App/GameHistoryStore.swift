import Foundation
import Observation

struct GameHistoryEntry: Codable, Sendable {
    let questionText: String
    let answer: String // "yes" | "no" | "irrelevant"
}

struct GameHistory: Codable, Sendable {
    let puzzleID: String
    let puzzleTitle: String
    let entries: [GameHistoryEntry]
}

@MainActor @Observable
final class GameHistoryStore {
    static let shared = GameHistoryStore()

    private static let key = "gameHistories"

    private(set) var histories: [String: GameHistory] // puzzleID -> history

    private init() {
        guard let data = UserDefaults.standard.data(forKey: Self.key),
              let decoded = try? JSONDecoder().decode([String: GameHistory].self, from: data) else {
            histories = [:]
            return
        }
        histories = decoded
    }

    func save(_ history: GameHistory) {
        histories[history.puzzleID] = history
        persist()
    }

    func history(for puzzleID: String) -> GameHistory? {
        histories[puzzleID]
    }

    private func persist() {
        guard let data = try? JSONEncoder().encode(histories) else { return }
        UserDefaults.standard.set(data, forKey: Self.key)
    }
}

import Foundation
import Observation

@MainActor @Observable
final class SolvedPuzzleStore {
    static let shared = SolvedPuzzleStore()

    private static let key = "solvedPuzzleIDs"

    private(set) var solvedIDs: Set<String>

    private init() {
        let array = UserDefaults.standard.stringArray(forKey: Self.key) ?? []
        solvedIDs = Set(array)
    }

    func markSolved(_ id: String) {
        guard !id.isEmpty else { return }
        solvedIDs.insert(id)
        UserDefaults.standard.set(Array(solvedIDs), forKey: Self.key)
    }

    func isSolved(_ id: String) -> Bool {
        solvedIDs.contains(id)
    }

    func reset() {
        solvedIDs.removeAll()
        UserDefaults.standard.removeObject(forKey: Self.key)
    }
}

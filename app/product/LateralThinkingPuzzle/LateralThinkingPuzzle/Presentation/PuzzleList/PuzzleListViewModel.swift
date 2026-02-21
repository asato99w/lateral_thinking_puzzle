import Foundation
import Observation

@MainActor @Observable
final class PuzzleListViewModel {
    private(set) var puzzles: [PuzzleSummary] = []
    private(set) var isLoading = false
    private(set) var error: String?

    private let fetchPuzzleList: FetchPuzzleListUseCase

    init(repository: PuzzleRepository) {
        self.fetchPuzzleList = FetchPuzzleListUseCase(repository: repository)
    }

    func loadPuzzles() async {
        isLoading = true
        error = nil
        do {
            puzzles = try await fetchPuzzleList.execute()
        } catch {
            self.error = error.localizedDescription
        }
        isLoading = false
    }
}

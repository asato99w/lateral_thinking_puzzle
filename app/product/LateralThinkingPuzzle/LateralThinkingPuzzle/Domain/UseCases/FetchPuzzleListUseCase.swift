struct FetchPuzzleListUseCase: Sendable {
    let repository: PuzzleRepository

    func execute() async throws -> [PuzzleSummary] {
        try await repository.fetchPuzzleList()
    }
}

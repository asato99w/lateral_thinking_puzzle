protocol PuzzleRepository: Sendable {
    func fetchPuzzle(id: String) async throws -> PuzzleData
}

struct PuzzleSummary: Equatable, Sendable {
    let id: String
    let title: String
    let statementPreview: String
    let icon: String
    let difficulty: Int
    let tier: PuzzleTier
    let isDownloaded: Bool
}

protocol PuzzleRepository: Sendable {
    func fetchPuzzleList() async throws -> [PuzzleSummary]
    func fetchPuzzle(id: String) async throws -> PuzzleData
}

struct PuzzleSummary: Equatable, Sendable {
    let id: String
    let title: String
    let statementPreview: String
    let tier: PuzzleTier
    let isDownloaded: Bool
}

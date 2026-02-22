import Foundation

struct JSONPuzzleRepository: PuzzleRepository {

    private static let puzzleIDs = ["bar_man", "turtle_soup"]

    func fetchPuzzleList() async throws -> [PuzzleSummary] {
        var summaries = [PuzzleSummary]()

        for id in Self.puzzleIDs {
            guard let url = Bundle.main.url(forResource: id, withExtension: "json") else {
                continue
            }
            let data = try Data(contentsOf: url)
            let dto = try JSONDecoder().decode(PuzzleDataDTO.self, from: data)
            let preview = String(dto.statement.prefix(50))
            summaries.append(PuzzleSummary(
                id: id,
                title: dto.title,
                statementPreview: preview,
                tier: .free,
                isDownloaded: true
            ))
        }

        return summaries
    }

    func fetchPuzzle(id: String) async throws -> PuzzleData {
        guard let url = Bundle.main.url(forResource: id, withExtension: "json") else {
            throw PuzzleRepositoryError.puzzleNotFound(id: id)
        }
        let data = try Data(contentsOf: url)
        let dto = try JSONDecoder().decode(PuzzleDataDTO.self, from: data)
        return try dto.toDomain()
    }
}

enum PuzzleRepositoryError: Error {
    case puzzleNotFound(id: String)
}

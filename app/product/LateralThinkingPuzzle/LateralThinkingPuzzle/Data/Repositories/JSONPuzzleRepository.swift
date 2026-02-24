import Foundation

struct JSONPuzzleRepository: PuzzleRepository {

    @MainActor
    private func puzzleSubdirectory() -> String {
        "Puzzles/\(ContentLanguage.current)"
    }

    @MainActor
    private func loadManifest() throws -> [String] {
        let subdir = puzzleSubdirectory()
        guard let url = Bundle.main.url(forResource: "manifest", withExtension: "json", subdirectory: subdir) else {
            throw PuzzleRepositoryError.manifestNotFound(language: ContentLanguage.current)
        }
        let data = try Data(contentsOf: url)
        let manifest = try JSONDecoder().decode(Manifest.self, from: data)
        return manifest.puzzles
    }

    @MainActor
    func fetchPuzzleList() async throws -> [PuzzleSummary] {
        let ids = try loadManifest()
        let subdir = puzzleSubdirectory()
        var summaries = [PuzzleSummary]()

        for id in ids {
            guard let url = Bundle.main.url(forResource: id, withExtension: "json", subdirectory: subdir) else {
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

    @MainActor
    func fetchPuzzle(id: String) async throws -> PuzzleData {
        let subdir = puzzleSubdirectory()
        guard let url = Bundle.main.url(forResource: id, withExtension: "json", subdirectory: subdir) else {
            throw PuzzleRepositoryError.puzzleNotFound(id: id)
        }
        let data = try Data(contentsOf: url)
        let dto = try JSONDecoder().decode(PuzzleDataDTO.self, from: data)
        return try dto.toDomain()
    }
}

private struct Manifest: Decodable {
    let puzzles: [String]
}

enum PuzzleRepositoryError: Error {
    case puzzleNotFound(id: String)
    case manifestNotFound(language: String)
}

import Foundation

struct JSONPuzzleRepository: PuzzleRepository {

    @MainActor
    func fetchPuzzle(id: String) async throws -> PuzzleData {
        let data = try loadPuzzleData(id: id)
        let dto = try JSONDecoder().decode(PuzzleDataDTO.self, from: data)
        return try dto.toDomain()
    }

    @MainActor
    func fetchSession(id: String, engineVersion: String) async throws -> any GameSession {
        let data = try loadPuzzleData(id: id)
        switch engineVersion {
        case "v2":
            let dto = try JSONDecoder().decode(V2PuzzleDataDTO.self, from: data)
            return V2GameSession(puzzle: dto.toDomain(derivationMode: .v2))
        case "v3":
            let dto = try JSONDecoder().decode(V2PuzzleDataDTO.self, from: data)
            return V2GameSession(puzzle: dto.toDomain(derivationMode: .v3))
        default:
            let dto = try JSONDecoder().decode(PuzzleDataDTO.self, from: data)
            return V1GameSession(puzzle: try dto.toDomain())
        }
    }

    @MainActor
    private func loadPuzzleData(id: String) throws -> Data {
        let lang = ContentLanguage.current

        // 1. Bundled puzzles: Puzzles/{lang}/{id}.json
        if let url = Bundle.main.url(forResource: id, withExtension: "json", subdirectory: "Puzzles/\(lang)")
            ?? Bundle.main.url(forResource: id, withExtension: "json", subdirectory: "Puzzles/ja") {
            return try Data(contentsOf: url)
        }

        // 2. ODR puzzles: {id}_{lang}.json (flat, accessible after beginAccessingResources)
        if let url = Bundle.main.url(forResource: "\(id)_\(lang)", withExtension: "json")
            ?? Bundle.main.url(forResource: "\(id)_ja", withExtension: "json") {
            return try Data(contentsOf: url)
        }

        throw PuzzleRepositoryError.puzzleNotFound(id: id)
    }
}

enum PuzzleRepositoryError: Error {
    case puzzleNotFound(id: String)
}

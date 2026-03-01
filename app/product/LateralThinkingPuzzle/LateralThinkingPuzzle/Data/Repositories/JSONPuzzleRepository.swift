import Foundation

struct JSONPuzzleRepository: PuzzleRepository {

    @MainActor
    func fetchPuzzle(id: String) async throws -> PuzzleData {
        let lang = ContentLanguage.current
        let url = Bundle.main.url(forResource: id, withExtension: "json", subdirectory: "Puzzles/\(lang)")
            ?? Bundle.main.url(forResource: id, withExtension: "json", subdirectory: "Puzzles/ja")
        guard let url else {
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

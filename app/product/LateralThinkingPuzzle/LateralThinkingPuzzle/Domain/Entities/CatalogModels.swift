import Foundation

struct PuzzleCatalogEntry: Codable, Identifiable, Sendable {
    let id: String
    let odrTag: String
    let titleJa: String
    let titleEn: String
    let statementPreviewJa: String
    let statementPreviewEn: String
    let icon: String
    let difficulty: Int
    let tier: String
    let bundled: Bool
}

struct PackCatalogEntry: Codable, Identifiable, Sendable {
    let id: String
    let titleJa: String
    let titleEn: String
    let descriptionJa: String
    let descriptionEn: String
    let icon: String
    let puzzleIds: [String]
    let tier: String
}

struct PuzzleCatalog: Codable, Sendable {
    let puzzles: [PuzzleCatalogEntry]
    let packs: [PackCatalogEntry]
}

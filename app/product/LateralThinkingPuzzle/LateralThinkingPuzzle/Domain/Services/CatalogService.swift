import Foundation

enum CatalogError: Error {
    case notFound
}

@MainActor
enum CatalogService {
    private static var cached: PuzzleCatalog?

    static func load() throws -> PuzzleCatalog {
        if let cached { return cached }

        guard let url = Bundle.main.url(forResource: "catalog", withExtension: "json") else {
            throw CatalogError.notFound
        }

        let data = try Data(contentsOf: url)
        let decoder = JSONDecoder()
        decoder.keyDecodingStrategy = .convertFromSnakeCase
        let catalog = try decoder.decode(PuzzleCatalog.self, from: data)
        cached = catalog
        return catalog
    }

    static func localizedTitle(_ entry: PuzzleCatalogEntry) -> String {
        ContentLanguage.current == "ja" ? entry.titleJa : entry.titleEn
    }

    static func localizedPreview(_ entry: PuzzleCatalogEntry) -> String {
        ContentLanguage.current == "ja" ? entry.statementPreviewJa : entry.statementPreviewEn
    }

    static func localizedTitle(_ entry: PackCatalogEntry) -> String {
        ContentLanguage.current == "ja" ? entry.titleJa : entry.titleEn
    }

    static func localizedDescription(_ entry: PackCatalogEntry) -> String {
        ContentLanguage.current == "ja" ? entry.descriptionJa : entry.descriptionEn
    }
}

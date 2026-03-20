import Foundation

enum CatalogError: Error {
    case notFound
}

@MainActor
enum CatalogService {
    private static var cached: PuzzleCatalog?

    private static var catalogResourceName: String {
        #if DEBUG
        return "catalog_debug"
        #else
        return "catalog"
        #endif
    }

    static func load() throws -> PuzzleCatalog {
        if let cached { return cached }

        guard let url = Bundle.main.url(forResource: catalogResourceName, withExtension: "json")
                ?? Bundle.main.url(forResource: "catalog", withExtension: "json") else {
            throw CatalogError.notFound
        }

        let data = try Data(contentsOf: url)
        let decoder = JSONDecoder()
        decoder.keyDecodingStrategy = .convertFromSnakeCase
        let catalog = try decoder.decode(PuzzleCatalog.self, from: data)
        cached = catalog
        return catalog
    }

    static func loadForCurrentLocale() throws -> PuzzleCatalog {
        try filtered(try load(), locale: ContentLanguage.current)
    }

    nonisolated static func filtered(_ catalog: PuzzleCatalog, locale: String) -> PuzzleCatalog {
        let filteredPuzzles = catalog.puzzles.filter { entry in
            guard let locales = entry.locales else { return true }
            return locales.contains(locale)
        }
        let filteredPuzzleIds = Set(filteredPuzzles.map(\.id))
        let filteredPacks = catalog.packs.compactMap { pack -> PackCatalogEntry? in
            let ids = pack.puzzleIds.filter { filteredPuzzleIds.contains($0) }
            guard !ids.isEmpty else { return nil }
            return PackCatalogEntry(
                id: pack.id,
                titleJa: pack.titleJa, titleEn: pack.titleEn,
                descriptionJa: pack.descriptionJa, descriptionEn: pack.descriptionEn,
                icon: pack.icon, puzzleIds: ids, tier: pack.tier
            )
        }
        return PuzzleCatalog(puzzles: filteredPuzzles, packs: filteredPacks)
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

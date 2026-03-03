import Testing
@testable import LateralThinkingPuzzle

struct CatalogFilterTests {

    private func makeCatalog() -> PuzzleCatalog {
        let puzzles: [PuzzleCatalogEntry] = [
            .init(id: "turtle_soup", engineVersion: nil, odrTag: "", titleJa: "ウミガメ", titleEn: "Turtle Soup",
                  statementPreviewJa: "", statementPreviewEn: "", icon: "", difficulty: 1,
                  tier: "free", bundled: true, locales: ["ja", "en"]),
            .init(id: "bar_man", engineVersion: nil, odrTag: "", titleJa: "バーの男", titleEn: "The Bar Man",
                  statementPreviewJa: "", statementPreviewEn: "", icon: "", difficulty: 2,
                  tier: "free", bundled: true, locales: ["ja"]),
            .init(id: "desert_man", engineVersion: nil, odrTag: "", titleJa: "砂漠の男", titleEn: "The Desert Man",
                  statementPreviewJa: "", statementPreviewEn: "", icon: "", difficulty: 3,
                  tier: "free", bundled: true, locales: ["ja", "en"]),
            .init(id: "poisonous_mushroom", engineVersion: nil, odrTag: "", titleJa: "毒キノコ", titleEn: "Mushroom",
                  statementPreviewJa: "", statementPreviewEn: "", icon: "", difficulty: 2,
                  tier: "free", bundled: false, locales: ["ja", "en"]),
            .init(id: "underground", engineVersion: nil, odrTag: "", titleJa: "地下室", titleEn: "Underground",
                  statementPreviewJa: "", statementPreviewEn: "", icon: "", difficulty: 2,
                  tier: "free", bundled: false, locales: ["ja"]),
        ]
        let packs: [PackCatalogEntry] = [
            .init(id: "classic", titleJa: "定番", titleEn: "Classic",
                  descriptionJa: "", descriptionEn: "", icon: "",
                  puzzleIds: ["turtle_soup", "bar_man", "desert_man"], tier: "free"),
        ]
        return PuzzleCatalog(puzzles: puzzles, packs: packs)
    }

    @Test func test_ja_showsAllPuzzles() {
        let catalog = makeCatalog()
        let filtered = CatalogService.filtered(catalog, locale: "ja")
        let ids = filtered.puzzles.map(\.id)
        #expect(ids == ["turtle_soup", "bar_man", "desert_man", "poisonous_mushroom", "underground"])
    }

    @Test func test_ja_bundledPuzzles() {
        let catalog = makeCatalog()
        let filtered = CatalogService.filtered(catalog, locale: "ja")
        let bundled = filtered.puzzles.filter(\.bundled).map(\.id)
        #expect(bundled == ["turtle_soup", "bar_man", "desert_man"])
    }

    @Test func test_ja_dlcPuzzles() {
        let catalog = makeCatalog()
        let filtered = CatalogService.filtered(catalog, locale: "ja")
        let dlc = filtered.puzzles.filter { !$0.bundled }.map(\.id)
        #expect(dlc == ["poisonous_mushroom", "underground"])
    }

    @Test func test_en_showsOnlyEnPuzzles() {
        let catalog = makeCatalog()
        let filtered = CatalogService.filtered(catalog, locale: "en")
        let ids = filtered.puzzles.map(\.id)
        #expect(ids == ["turtle_soup", "desert_man", "poisonous_mushroom"])
    }

    @Test func test_en_barManExcluded() {
        let catalog = makeCatalog()
        let filtered = CatalogService.filtered(catalog, locale: "en")
        let ids = Set(filtered.puzzles.map(\.id))
        #expect(!ids.contains("bar_man"))
        #expect(!ids.contains("underground"))
    }

    @Test func test_en_bundledPuzzles() {
        let catalog = makeCatalog()
        let filtered = CatalogService.filtered(catalog, locale: "en")
        let bundled = filtered.puzzles.filter(\.bundled).map(\.id)
        #expect(bundled == ["turtle_soup", "desert_man"])
    }

    @Test func test_en_dlcPuzzles() {
        let catalog = makeCatalog()
        let filtered = CatalogService.filtered(catalog, locale: "en")
        let dlc = filtered.puzzles.filter { !$0.bundled }.map(\.id)
        #expect(dlc == ["poisonous_mushroom"])
    }

    @Test func test_en_packFilteredByLocale() {
        let catalog = makeCatalog()
        let filtered = CatalogService.filtered(catalog, locale: "en")
        let classicPack = filtered.packs.first { $0.id == "classic" }
        #expect(classicPack != nil)
        #expect(classicPack?.puzzleIds == ["turtle_soup", "desert_man"])
    }

    @Test func test_ja_packIncludesAll() {
        let catalog = makeCatalog()
        let filtered = CatalogService.filtered(catalog, locale: "ja")
        let classicPack = filtered.packs.first { $0.id == "classic" }
        #expect(classicPack?.puzzleIds == ["turtle_soup", "bar_man", "desert_man"])
    }
}

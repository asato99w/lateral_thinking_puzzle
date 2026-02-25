import Foundation
import Observation

@MainActor @Observable
final class PuzzleListViewModel {
    private(set) var puzzles: [PuzzleSummary] = []
    private(set) var isLoading = false
    private(set) var error: String?

    private let resourceProvider: ResourceProvider

    init(resourceProvider: ResourceProvider = ODRResourceProvider()) {
        self.resourceProvider = resourceProvider
    }

    func loadPuzzles() async {
        isLoading = true
        error = nil
        do {
            let catalog = try CatalogService.load()
            var summaries: [PuzzleSummary] = []
            for entry in catalog.puzzles {
                let isDownloaded: Bool
                if entry.bundled {
                    isDownloaded = true
                } else {
                    isDownloaded = await resourceProvider.isAvailable(tag: entry.odrTag)
                }
                let tier: PuzzleTier = entry.tier == "paid" ? .premium : .free
                summaries.append(PuzzleSummary(
                    id: entry.id,
                    title: CatalogService.localizedTitle(entry),
                    statementPreview: CatalogService.localizedPreview(entry),
                    icon: entry.icon,
                    difficulty: entry.difficulty,
                    tier: tier,
                    isDownloaded: isDownloaded
                ))
            }
            puzzles = summaries
        } catch {
            self.error = error.localizedDescription
        }
        isLoading = false
    }
}

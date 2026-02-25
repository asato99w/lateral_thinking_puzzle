import Foundation
import Observation

// MARK: - Download States

enum PuzzleDownloadState: Equatable {
    case bundled
    case notDownloaded
    case downloading(progress: Double)
    case downloaded
}

enum PackDownloadState: Equatable {
    case notDownloaded
    case partial(downloaded: Int, total: Int)
    case downloading
    case downloaded
}

// MARK: - ViewModel

@MainActor @Observable
final class ContentDownloadViewModel {
    private(set) var catalog: PuzzleCatalog?
    private(set) var error: String?
    var puzzleStates: [String: PuzzleDownloadState] = [:]

    private let resourceProvider: ResourceProvider

    init(resourceProvider: ResourceProvider = ODRResourceProvider()) {
        self.resourceProvider = resourceProvider
    }

    func load() async {
        do {
            let catalog = try CatalogService.load()
            self.catalog = catalog

            for puzzle in catalog.puzzles {
                if puzzle.bundled {
                    puzzleStates[puzzle.id] = .bundled
                } else {
                    let available = await resourceProvider.isAvailable(tag: puzzle.odrTag)
                    puzzleStates[puzzle.id] = available ? .downloaded : .notDownloaded
                }
            }
        } catch {
            self.error = error.localizedDescription
        }
    }

    func downloadPuzzle(_ puzzle: PuzzleCatalogEntry) async {
        guard puzzleStates[puzzle.id] == .notDownloaded else { return }
        puzzleStates[puzzle.id] = .downloading(progress: 0)

        do {
            try await resourceProvider.download(tag: puzzle.odrTag) { [weak self] progress in
                Task { @MainActor in
                    self?.puzzleStates[puzzle.id] = .downloading(progress: progress)
                }
            }
            puzzleStates[puzzle.id] = .downloaded

            let priority = puzzle.tier == "paid" ? 1.0 : 0.5
            resourceProvider.setPreservationPriority(priority, for: puzzle.odrTag)
        } catch {
            puzzleStates[puzzle.id] = .notDownloaded
        }
    }

    func removePuzzle(_ puzzle: PuzzleCatalogEntry) {
        guard puzzleStates[puzzle.id] == .downloaded else { return }
        resourceProvider.remove(tag: puzzle.odrTag)
        puzzleStates[puzzle.id] = .notDownloaded
    }

    func downloadPack(_ pack: PackCatalogEntry) async {
        guard let catalog else { return }
        let puzzlesToDownload = pack.puzzleIds.compactMap { id in
            catalog.puzzles.first { $0.id == id }
        }.filter { puzzleStates[$0.id] == .notDownloaded }

        await withTaskGroup(of: Void.self) { group in
            for puzzle in puzzlesToDownload {
                group.addTask {
                    await self.downloadPuzzle(puzzle)
                }
            }
        }
    }

    func removePack(_ pack: PackCatalogEntry) {
        guard let catalog else { return }
        for id in pack.puzzleIds {
            if let puzzle = catalog.puzzles.first(where: { $0.id == id }) {
                removePuzzle(puzzle)
            }
        }
    }

    func packState(for pack: PackCatalogEntry) -> PackDownloadState {
        let states = pack.puzzleIds.compactMap { puzzleStates[$0] }
        let total = states.count
        guard total > 0 else { return .downloaded }

        let downloadedCount = states.filter { $0 == .downloaded || $0 == .bundled }.count
        let isDownloading = states.contains {
            if case .downloading = $0 { return true }
            return false
        }

        if downloadedCount == total { return .downloaded }
        if isDownloading { return .downloading }
        if downloadedCount == 0 { return .notDownloaded }
        return .partial(downloaded: downloadedCount, total: total)
    }
}

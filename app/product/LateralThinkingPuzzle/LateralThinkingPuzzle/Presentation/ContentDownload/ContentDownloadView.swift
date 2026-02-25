import SwiftUI

struct ContentDownloadView: View {
    @State private var viewModel = ContentDownloadView.makeViewModel()

    private static func makeViewModel() -> ContentDownloadViewModel {
        #if DEBUG
        if DebugSettings.isMockDownloadsEnabled {
            return ContentDownloadViewModel(resourceProvider: MockResourceProvider.shared)
        }
        #endif
        return ContentDownloadViewModel()
    }

    var body: some View {
        Group {
            if let catalog = viewModel.catalog {
                contentList(catalog)
            } else if let error = viewModel.error {
                VStack(spacing: 16) {
                    Text(Strings.error)
                        .font(.headline)
                    Text(error)
                        .foregroundStyle(.secondary)
                }
            } else {
                ProgressView(Strings.loading)
            }
        }
        .navigationTitle(Strings.contentDownload)
        .navigationBarTitleDisplayMode(.large)
        .task {
            await viewModel.load()
        }
    }

    // MARK: - Content List

    private func contentList(_ catalog: PuzzleCatalog) -> some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 0) {
                if !catalog.packs.isEmpty {
                    packSection(catalog.packs)
                }
                puzzleSection(catalog.puzzles)
            }
        }
    }

    // MARK: - Pack Section

    private func packSection(_ packs: [PackCatalogEntry]) -> some View {
        VStack(alignment: .leading, spacing: 12) {
            sectionHeader(Strings.packs)

            ForEach(packs) { pack in
                NavigationLink {
                    PackDetailView(pack: pack, viewModel: viewModel)
                } label: {
                    packCard(pack)
                }
                .buttonStyle(.plain)
            }
        }
        .padding(.horizontal)
        .padding(.top, 16)
        .padding(.bottom, 28)
    }

    private func packCard(_ pack: PackCatalogEntry) -> some View {
        let state = viewModel.packState(for: pack)

        return HStack(spacing: 12) {
            Text(pack.icon)
                .font(.system(size: 28))
                .frame(width: 44, height: 44)
                .background(Theme.accent.opacity(0.2))
                .clipShape(RoundedRectangle(cornerRadius: 8))

            Text(CatalogService.localizedTitle(pack))
                .font(.headline)

            Spacer()

            packStateBadge(state)

            Image(systemName: "chevron.right")
                .font(.caption)
                .foregroundStyle(.secondary)
        }
        .padding(12)
        .background(Theme.cardBackground)
        .clipShape(RoundedRectangle(cornerRadius: Theme.cardCornerRadius))
        .overlay(
            RoundedRectangle(cornerRadius: Theme.cardCornerRadius)
                .stroke(Theme.cardBorder, lineWidth: 1)
        )
    }

    @ViewBuilder
    private func packStateBadge(_ state: PackDownloadState) -> some View {
        switch state {
        case .downloaded:
            Image(systemName: "checkmark.circle.fill")
                .foregroundStyle(Theme.solvedBadge)
        case .downloading:
            ProgressView()
                .controlSize(.mini)
        case .partial(let downloaded, let total):
            Text("\(downloaded)/\(total)")
                .font(.caption.monospacedDigit())
                .foregroundStyle(.secondary)
        case .notDownloaded:
            Text(Strings.free)
                .font(.caption.weight(.medium))
                .foregroundStyle(.secondary)
        }
    }

    // MARK: - Puzzle Section

    private func puzzleSection(_ puzzles: [PuzzleCatalogEntry]) -> some View {
        VStack(alignment: .leading, spacing: 12) {
            sectionHeader(Strings.puzzles)

            ForEach(puzzles) { puzzle in
                puzzleCard(puzzle)
            }
        }
        .padding(.horizontal)
        .padding(.bottom, 24)
    }

    private func puzzleCard(_ puzzle: PuzzleCatalogEntry) -> some View {
        let state = viewModel.puzzleStates[puzzle.id] ?? .notDownloaded

        return HStack(spacing: 14) {
            // Emoji thumbnail
            Text(puzzle.icon)
                .font(.system(size: 40))
                .frame(width: 64, height: 64)
                .background(Theme.accent.opacity(0.2))
                .clipShape(RoundedRectangle(cornerRadius: 12))

            // Info
            VStack(alignment: .leading, spacing: 6) {
                HStack {
                    Text(CatalogService.localizedTitle(puzzle))
                        .font(.headline)
                    Spacer()
                    difficultyStars(puzzle.difficulty)
                }

                Text(CatalogService.localizedPreview(puzzle))
                    .font(.caption)
                    .foregroundStyle(.white.opacity(0.5))
                    .lineLimit(2)

                downloadStateBadge(state)
                    .padding(.top, 2)
            }

            // Download button
            puzzleDownloadButton(puzzle, state: state)
        }
        .padding(14)
        .background(Theme.cardBackground)
        .clipShape(RoundedRectangle(cornerRadius: Theme.cardCornerRadius))
        .overlay(
            RoundedRectangle(cornerRadius: Theme.cardCornerRadius)
                .stroke(Theme.cardBorder, lineWidth: 1)
        )
    }

    @ViewBuilder
    private func puzzleDownloadButton(_ puzzle: PuzzleCatalogEntry, state: PuzzleDownloadState) -> some View {
        switch state {
        case .bundled:
            Image(systemName: "checkmark.circle.fill")
                .foregroundStyle(Theme.solvedBadge)
                .font(.title2)
        case .downloaded:
            Button {
                viewModel.removePuzzle(puzzle)
            } label: {
                Image(systemName: "trash.circle")
                    .foregroundStyle(.secondary)
                    .font(.title2)
            }
            .accessibilityIdentifier("delete-\(puzzle.id)")
        case .downloading(let progress):
            CircularProgressView(progress: progress)
                .frame(width: 28, height: 28)
        case .notDownloaded:
            Button {
                Task { await viewModel.downloadPuzzle(puzzle) }
            } label: {
                Image(systemName: "arrow.down.circle.fill")
                    .foregroundStyle(Theme.accent)
                    .font(.title2)
            }
            .accessibilityIdentifier("download-\(puzzle.id)")
        }
    }

    @ViewBuilder
    private func downloadStateBadge(_ state: PuzzleDownloadState) -> some View {
        switch state {
        case .bundled:
            HStack(spacing: 3) {
                Image(systemName: "internaldrive.fill")
                    .font(.caption2)
                Text(Strings.bundled)
                    .font(.caption2.weight(.medium))
            }
            .foregroundStyle(.secondary)
        case .downloaded:
            HStack(spacing: 3) {
                Image(systemName: "checkmark.circle.fill")
                    .font(.caption2)
                Text(Strings.downloadComplete)
                    .font(.caption2.weight(.medium))
            }
            .foregroundStyle(Theme.solvedBadge)
        case .downloading:
            HStack(spacing: 3) {
                Image(systemName: "arrow.down.circle")
                    .font(.caption2)
                Text(Strings.downloading)
                    .font(.caption2.weight(.medium))
            }
            .foregroundStyle(Theme.accent)
        case .notDownloaded:
            HStack(spacing: 3) {
                Image(systemName: "yensign.circle")
                    .font(.caption2)
                Text(Strings.free)
                    .font(.caption2.weight(.medium))
            }
            .foregroundStyle(.secondary)
        }
    }

    // MARK: - Helpers

    private func sectionHeader(_ title: String) -> some View {
        HStack(spacing: 10) {
            RoundedRectangle(cornerRadius: 2)
                .fill(Theme.accent)
                .frame(width: 4, height: 24)
            Text(title)
                .font(.headline)
                .foregroundStyle(.white.opacity(0.85))
        }
        .padding(.bottom, 4)
    }

    private func difficultyStars(_ level: Int) -> some View {
        HStack(spacing: 4) {
            ForEach(1...3, id: \.self) { star in
                Image(systemName: star <= level ? "star.fill" : "star")
                    .font(.caption2)
                    .foregroundStyle(star <= level ? Theme.starFilled : Theme.starEmpty)
            }
        }
    }
}

// MARK: - Circular Progress

struct CircularProgressView: View {
    let progress: Double

    var body: some View {
        ZStack {
            Circle()
                .stroke(Color.gray.opacity(0.3), lineWidth: 3)
            Circle()
                .trim(from: 0, to: progress)
                .stroke(Theme.accent, style: StrokeStyle(lineWidth: 3, lineCap: .round))
                .rotationEffect(.degrees(-90))
        }
    }
}

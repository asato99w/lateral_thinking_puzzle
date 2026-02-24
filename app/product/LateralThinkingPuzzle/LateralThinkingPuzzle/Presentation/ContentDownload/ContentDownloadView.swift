import SwiftUI

struct ContentDownloadView: View {
    @State private var viewModel = ContentDownloadViewModel()

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
                packCard(pack)
            }
        }
        .padding(.horizontal)
        .padding(.top, 16)
        .padding(.bottom, 28)
    }

    private func packCard(_ pack: PackCatalogEntry) -> some View {
        let state = viewModel.packState(for: pack)
        let puzzles = pack.puzzleIds.compactMap { id in
            viewModel.catalog?.puzzles.first { $0.id == id }
        }

        return VStack(alignment: .leading, spacing: 12) {
            // Header: icon + title + description + download button
            HStack(spacing: 12) {
                Text(pack.icon)
                    .font(.system(size: 32))
                    .frame(width: 52, height: 52)
                    .background(Theme.accent.opacity(0.2))
                    .clipShape(RoundedRectangle(cornerRadius: 10))

                VStack(alignment: .leading, spacing: 4) {
                    Text(CatalogService.localizedTitle(pack))
                        .font(.headline)
                    Text(CatalogService.localizedDescription(pack))
                        .font(.caption)
                        .foregroundStyle(.secondary)
                }

                Spacer()

                packDownloadButton(pack, state: state)
            }

            // Puzzle emoji preview
            HStack(spacing: 6) {
                ForEach(puzzles) { puzzle in
                    Text(puzzle.icon)
                        .font(.title3)
                }
            }

            // Progress indicator for partial downloads
            if case .partial(let downloaded, let total) = state {
                HStack(spacing: 8) {
                    ProgressView(value: Double(downloaded), total: Double(total))
                        .tint(Theme.accent)
                    Text("\(downloaded)/\(total)")
                        .font(.caption2.monospacedDigit())
                        .foregroundStyle(.secondary)
                }
            }
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
    private func packDownloadButton(_ pack: PackCatalogEntry, state: PackDownloadState) -> some View {
        switch state {
        case .downloaded:
            Image(systemName: "checkmark.circle.fill")
                .foregroundStyle(Theme.solvedBadge)
                .font(.title2)
        case .downloading:
            ProgressView()
                .controlSize(.small)
        case .notDownloaded, .partial:
            Button {
                Task { await viewModel.downloadPack(pack) }
            } label: {
                Image(systemName: "arrow.down.circle.fill")
                    .foregroundStyle(Theme.accent)
                    .font(.title2)
            }
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
        case .bundled, .downloaded:
            Image(systemName: "checkmark.circle.fill")
                .foregroundStyle(Theme.solvedBadge)
                .font(.title2)
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
            EmptyView()
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

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
                NavigationLink {
                    PuzzleDetailView(puzzle: puzzle, viewModel: viewModel)
                } label: {
                    puzzleCard(puzzle)
                }
                .buttonStyle(.plain)
            }
        }
        .padding(.horizontal)
        .padding(.bottom, 24)
    }

    private func puzzleCard(_ puzzle: PuzzleCatalogEntry) -> some View {
        let state = viewModel.puzzleStates[puzzle.id] ?? .notDownloaded

        return HStack(spacing: 12) {
            Text(puzzle.icon)
                .font(.system(size: 28))
                .frame(width: 44, height: 44)
                .background(Theme.accent.opacity(0.2))
                .clipShape(RoundedRectangle(cornerRadius: 8))

            Text(CatalogService.localizedTitle(puzzle))
                .font(.headline)

            Spacer()

            puzzleStateBadge(state)

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
    private func puzzleStateBadge(_ state: PuzzleDownloadState) -> some View {
        switch state {
        case .bundled:
            Image(systemName: "checkmark.circle.fill")
                .foregroundStyle(Theme.solvedBadge)
        case .downloaded:
            Image(systemName: "checkmark.circle.fill")
                .foregroundStyle(Theme.solvedBadge)
        case .downloading:
            ProgressView()
                .controlSize(.mini)
        case .notDownloaded:
            Text(Strings.free)
                .font(.caption.weight(.medium))
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

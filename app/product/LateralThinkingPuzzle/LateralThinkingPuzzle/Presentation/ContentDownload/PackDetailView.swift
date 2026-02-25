import SwiftUI

struct PackDetailView: View {
    let pack: PackCatalogEntry
    @Bindable var viewModel: ContentDownloadViewModel

    private var puzzles: [PuzzleCatalogEntry] {
        pack.puzzleIds.compactMap { id in
            viewModel.catalog?.puzzles.first { $0.id == id }
        }
    }

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 0) {
                packHeader
                puzzleList
            }
        }
        .navigationTitle(CatalogService.localizedTitle(pack))
        .navigationBarTitleDisplayMode(.large)
    }

    // MARK: - Pack Header

    private var packHeader: some View {
        let state = viewModel.packState(for: pack)

        return VStack(alignment: .leading, spacing: 12) {
            HStack(spacing: 14) {
                Text(pack.icon)
                    .font(.system(size: 44))
                    .frame(width: 72, height: 72)
                    .background(Theme.accent.opacity(0.2))
                    .clipShape(RoundedRectangle(cornerRadius: 14))

                VStack(alignment: .leading, spacing: 4) {
                    Text(CatalogService.localizedTitle(pack))
                        .font(.title2.bold())
                    Text(CatalogService.localizedDescription(pack))
                        .font(.subheadline)
                        .foregroundStyle(.secondary)
                }
            }

            packActionButton(state)

            if case .downloading = state {
                ProgressView()
                    .tint(Theme.accent)
                    .frame(maxWidth: .infinity, alignment: .leading)
            }
        }
        .padding()
        .padding(.bottom, 8)
    }

    @ViewBuilder
    private func packActionButton(_ state: PackDownloadState) -> some View {
        switch state {
        case .downloaded:
            Label(Strings.downloadComplete, systemImage: "checkmark.circle.fill")
                .font(.subheadline.weight(.medium))
                .foregroundStyle(Theme.solvedBadge)
        case .downloading:
            HStack(spacing: 8) {
                ProgressView()
                    .controlSize(.small)
                Text(Strings.downloading)
                    .font(.subheadline)
                    .foregroundStyle(.secondary)
            }
        case .notDownloaded, .partial:
            Button {
                Task { await viewModel.downloadPack(pack) }
            } label: {
                Label(Strings.download, systemImage: "arrow.down.circle.fill")
                    .font(.subheadline.weight(.medium))
            }
            .buttonStyle(.borderedProminent)
            .tint(Theme.accent)
        }
    }

    // MARK: - Puzzle List

    private var puzzleList: some View {
        VStack(alignment: .leading, spacing: 12) {
            ForEach(puzzles) { puzzle in
                NavigationLink {
                    PuzzleDetailView(puzzle: puzzle, viewModel: viewModel)
                } label: {
                    puzzleRow(puzzle)
                }
                .buttonStyle(.plain)
            }
        }
        .padding(.horizontal)
        .padding(.bottom, 24)
    }

    private func puzzleRow(_ puzzle: PuzzleCatalogEntry) -> some View {
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

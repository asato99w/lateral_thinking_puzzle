import SwiftUI

struct PuzzleDetailView: View {
    let puzzle: PuzzleCatalogEntry
    @Bindable var viewModel: ContentDownloadViewModel

    private var state: PuzzleDownloadState {
        viewModel.puzzleStates[puzzle.id] ?? .notDownloaded
    }

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 0) {
                puzzleHeader
            }
        }
        .navigationTitle(CatalogService.localizedTitle(puzzle))
        .navigationBarTitleDisplayMode(.large)
    }

    // MARK: - Header

    private var puzzleHeader: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack(spacing: 14) {
                Text(puzzle.icon)
                    .font(.system(size: 44))
                    .frame(width: 72, height: 72)
                    .background(Theme.accent.opacity(0.2))
                    .clipShape(RoundedRectangle(cornerRadius: 14))

                VStack(alignment: .leading, spacing: 4) {
                    Text(CatalogService.localizedTitle(puzzle))
                        .font(.title2.bold())
                    difficultyStars(puzzle.difficulty)
                }
            }

            Text(CatalogService.localizedPreview(puzzle))
                .font(.subheadline)
                .foregroundStyle(.secondary)

            actionButton
        }
        .padding()
    }

    // MARK: - Action Button

    @ViewBuilder
    private var actionButton: some View {
        switch state {
        case .bundled:
            Label(Strings.bundled, systemImage: "internaldrive.fill")
                .font(.subheadline.weight(.medium))
                .foregroundStyle(.secondary)
        case .downloaded:
            HStack(spacing: 12) {
                Label(Strings.downloadComplete, systemImage: "checkmark.circle.fill")
                    .font(.subheadline.weight(.medium))
                    .foregroundStyle(Theme.solvedBadge)

                Button {
                    viewModel.removePuzzle(puzzle)
                } label: {
                    Label(Strings.deleteContent, systemImage: "trash")
                        .font(.subheadline.weight(.medium))
                }
                .buttonStyle(.bordered)
                .tint(.secondary)
            }
        case .downloading(let progress):
            HStack(spacing: 8) {
                CircularProgressView(progress: progress)
                    .frame(width: 20, height: 20)
                Text(Strings.downloading)
                    .font(.subheadline)
                    .foregroundStyle(.secondary)
            }
        case .notDownloaded:
            Button {
                Task { await viewModel.downloadPuzzle(puzzle) }
            } label: {
                Label(Strings.download, systemImage: "arrow.down.circle.fill")
                    .font(.subheadline.weight(.medium))
            }
            .buttonStyle(.borderedProminent)
            .tint(Theme.accent)
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

import SwiftUI

struct PuzzleListView: View {
    @State private var viewModel = PuzzleListView.makeViewModel()
    @State private var solvedStore = SolvedPuzzleStore.shared
    @State private var historyStore = GameHistoryStore.shared
    #if DEBUG
    @State private var showDebugSettings = false
    #endif

    private static func makeViewModel() -> PuzzleListViewModel {
        #if DEBUG
        if DebugSettings.isMockDownloadsEnabled {
            return PuzzleListViewModel(resourceProvider: MockResourceProvider.shared)
        }
        #endif
        return PuzzleListViewModel()
    }

    private var solvedCount: Int { solvedStore.solvedIDs.count }
    private var totalCount: Int { viewModel.puzzles.count }

    var body: some View {
        NavigationStack {
            Group {
                if viewModel.isLoading {
                    ProgressView(Strings.loading)
                } else if let error = viewModel.error {
                    VStack(spacing: 16) {
                        Text(Strings.error)
                            .font(.headline)
                        Text(error)
                            .foregroundStyle(.secondary)
                        Button(Strings.retry) {
                            Task { await viewModel.loadPuzzles() }
                        }
                    }
                } else {
                    puzzleList
                }
            }
            .navigationDestination(for: String.self) { puzzleID in
                GameContainerView(puzzleID: puzzleID)
            }
            .onAppear {
                Task { await viewModel.loadPuzzles() }
            }
            .toolbar {
                ToolbarItem(placement: .navigationBarLeading) {
                    NavigationLink {
                        ContentDownloadView()
                    } label: {
                        Image(systemName: "arrow.down.circle")
                    }
                }
                #if DEBUG
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button {
                        showDebugSettings = true
                    } label: {
                        Image(systemName: "gearshape")
                    }
                }
                #endif
            }
            #if DEBUG
            .sheet(isPresented: $showDebugSettings, onDismiss: {
                viewModel = PuzzleListView.makeViewModel()
                Task { await viewModel.loadPuzzles() }
            }) {
                DebugView()
            }
            #endif
        }
    }

    // MARK: - Puzzle List

    private var puzzleList: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 0) {
                heroSection
                sectionHeader
                cardList
            }
        }
    }

    // MARK: - Hero

    private var heroSection: some View {
        VStack(alignment: .leading, spacing: 12) {
            (Text("Lateral")
                .foregroundStyle(.white)
            + Text("Q")
                .foregroundStyle(Theme.accent))
                .font(.system(size: 34, weight: .bold, design: .serif))

            Text(Strings.appSubtitle)
                .font(.subheadline)
                .foregroundStyle(.secondary)

            // Progress pill
            HStack(spacing: 6) {
                Text("\(solvedCount)")
                    .font(.title3.bold().monospacedDigit())
                    .foregroundStyle(Theme.accent)
                Text("/ \(totalCount) Solved")
                    .font(.subheadline.monospacedDigit())
                    .foregroundStyle(Theme.progressText)
            }
            .padding(.horizontal, 14)
            .padding(.vertical, 8)
            .background(Theme.accent.opacity(0.12))
            .clipShape(Capsule())
            .padding(.top, 4)
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .padding(.horizontal)
        .padding(.top, 24)
        .padding(.bottom, 28)
    }

    // MARK: - Section Header

    private var sectionHeader: some View {
        HStack(spacing: 10) {
            RoundedRectangle(cornerRadius: 2)
                .fill(Theme.accent)
                .frame(width: 4, height: 24)

            Text(Strings.problemsSection)
                .font(.headline)
                .foregroundStyle(.white.opacity(0.85))
        }
        .padding(.horizontal)
        .padding(.bottom, 16)
    }

    // MARK: - Card List

    private var cardList: some View {
        LazyVStack(spacing: 14) {
            ForEach(viewModel.puzzles, id: \.id) { puzzle in
                if puzzle.isDownloaded {
                    NavigationLink(value: puzzle.id) {
                        puzzleCard(puzzle)
                    }
                    .buttonStyle(.plain)
                } else {
                    NavigationLink {
                        ContentDownloadView()
                    } label: {
                        puzzleCard(puzzle)
                    }
                    .buttonStyle(.plain)
                }
            }
        }
        .padding(.horizontal)
        .padding(.bottom, 24)
    }

    // MARK: - Puzzle Card

    private func puzzleCard(_ puzzle: PuzzleSummary) -> some View {
        let solved = solvedStore.isSolved(puzzle.id)

        return HStack(spacing: 14) {
            // Emoji thumbnail
            Text(puzzle.icon)
                .font(.system(size: 40))
                .frame(width: 64, height: 64)
                .background(Color.indigo.opacity(0.2))
                .clipShape(RoundedRectangle(cornerRadius: 12))

            // Title + preview + difficulty
            VStack(alignment: .leading, spacing: 6) {
                HStack {
                    Text(puzzle.title)
                        .font(.headline)
                    Spacer()
                    difficultyStars(puzzle.difficulty)
                }

                Text(puzzle.statementPreview)
                    .font(.caption)
                    .foregroundStyle(.white.opacity(0.5))
                    .lineLimit(2)
                    .fixedSize(horizontal: false, vertical: true)

                if solved {
                    HStack(spacing: 8) {
                        solvedBadge
                        if historyStore.history(for: puzzle.id) != nil {
                            NavigationLink {
                                GameHistoryView(history: historyStore.history(for: puzzle.id)!)
                            } label: {
                                historyBadge
                            }
                        }
                    }
                    .padding(.top, 2)
                } else if !puzzle.isDownloaded {
                    downloadBadge
                        .padding(.top, 2)
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
        .shadow(color: .black.opacity(0.3), radius: 4, y: 2)
        .opacity(puzzle.isDownloaded ? 1.0 : 0.6)
    }

    // MARK: - Difficulty Stars

    private func difficultyStars(_ level: Int) -> some View {
        HStack(spacing: 4) {
            Text(Strings.difficulty)
                .font(.caption2)
                .foregroundStyle(.white.opacity(0.4))
            ForEach(1...3, id: \.self) { star in
                Image(systemName: star <= level ? "star.fill" : "star")
                    .font(.caption2)
                    .foregroundStyle(star <= level ? Theme.starFilled : Theme.starEmpty)
            }
        }
    }

    // MARK: - Solved Badge

    private var solvedBadge: some View {
        HStack(spacing: 3) {
            Image(systemName: "checkmark.circle.fill")
                .font(.caption2)
            Text(Strings.solved)
                .font(.caption2.weight(.medium))
        }
        .foregroundStyle(Theme.solvedBadge)
    }

    // MARK: - History Badge

    private var historyBadge: some View {
        HStack(spacing: 3) {
            Image(systemName: "clock.arrow.circlepath")
                .font(.caption2)
            Text(Strings.history)
                .font(.caption2.weight(.medium))
        }
        .foregroundStyle(Theme.accent)
    }

    // MARK: - Download Badge

    private var downloadBadge: some View {
        HStack(spacing: 3) {
            Image(systemName: "arrow.down.circle")
                .font(.caption2)
            Text(Strings.notDownloaded)
                .font(.caption2.weight(.medium))
        }
        .foregroundStyle(Theme.accent)
    }
}

// MARK: - Game Container

struct GameContainerView: View {
    let puzzleID: String
    @State private var puzzle: PuzzleData?
    @State private var error: String?

    var body: some View {
        Group {
            if let puzzle {
                GameView(viewModel: GameViewModel(puzzleID: puzzleID, puzzle: puzzle))
            } else if let error {
                Text(Strings.errorDetail(error))
            } else {
                ProgressView()
            }
        }
        .task {
            do {
                puzzle = try await JSONPuzzleRepository().fetchPuzzle(id: puzzleID)
            } catch {
                self.error = error.localizedDescription
            }
        }
    }
}

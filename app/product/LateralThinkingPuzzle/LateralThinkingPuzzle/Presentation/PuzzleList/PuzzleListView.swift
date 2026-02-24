import SwiftUI

struct PuzzleListView: View {
    @State private var viewModel = PuzzleListViewModel(repository: JSONPuzzleRepository())
    @State private var selectedPuzzleID: String?
    #if DEBUG
    @State private var showDebugSettings = false
    #endif

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
                    List(viewModel.puzzles, id: \.id) { puzzle in
                        NavigationLink(value: puzzle.id) {
                            VStack(alignment: .leading, spacing: 4) {
                                Text(puzzle.title)
                                    .font(.headline)
                                Text(puzzle.statementPreview)
                                    .font(.caption)
                                    .foregroundStyle(.secondary)
                                    .lineLimit(1)
                            }
                            .padding(.vertical, 4)
                        }
                    }
                }
            }
            .navigationTitle(Strings.appTitle)
            .navigationDestination(for: String.self) { puzzleID in
                GameContainerView(puzzleID: puzzleID)
            }
            .task {
                await viewModel.loadPuzzles()
            }
            #if DEBUG
            .toolbar {
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button {
                        showDebugSettings = true
                    } label: {
                        Image(systemName: "gearshape")
                    }
                }
            }
            .sheet(isPresented: $showDebugSettings, onDismiss: {
                Task { await viewModel.loadPuzzles() }
            }) {
                DebugView()
            }
            #endif
        }
    }
}

struct GameContainerView: View {
    let puzzleID: String
    @State private var puzzle: PuzzleData?
    @State private var error: String?

    var body: some View {
        Group {
            if let puzzle {
                GameView(viewModel: GameViewModel(puzzle: puzzle))
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

import SwiftUI

struct PuzzleListView: View {
    @State private var viewModel = PuzzleListViewModel(repository: JSONPuzzleRepository())
    @State private var selectedPuzzleID: String?

    var body: some View {
        NavigationStack {
            Group {
                if viewModel.isLoading {
                    ProgressView("読み込み中...")
                } else if let error = viewModel.error {
                    VStack(spacing: 16) {
                        Text("エラー")
                            .font(.headline)
                        Text(error)
                            .foregroundStyle(.secondary)
                        Button("再試行") {
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
                                    .lineLimit(2)
                            }
                            .padding(.vertical, 4)
                        }
                    }
                }
            }
            .navigationTitle("水平思考パズル")
            .navigationDestination(for: String.self) { puzzleID in
                GameContainerView(puzzleID: puzzleID)
            }
            .task {
                await viewModel.loadPuzzles()
            }
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
                Text("エラー: \(error)")
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

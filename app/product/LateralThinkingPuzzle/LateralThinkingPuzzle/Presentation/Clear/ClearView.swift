import SwiftUI

struct ClearView: View {
    let puzzle: PuzzleData
    @Environment(\.dismiss) private var dismiss

    var body: some View {
        VStack(spacing: 32) {
            Spacer()

            Image(systemName: "checkmark.circle.fill")
                .font(.system(size: 80))
                .foregroundStyle(.green)

            Text("クリア!")
                .font(.largeTitle)
                .fontWeight(.bold)

            Text(puzzle.title)
                .font(.title2)
                .foregroundStyle(.secondary)

            Spacer()

            Button("パズル一覧に戻る") {
                dismiss()
            }
            .buttonStyle(.borderedProminent)
            .controlSize(.large)
        }
        .padding()
        .navigationBarBackButtonHidden(true)
    }
}

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

            Text(Strings.cleared)
                .font(.largeTitle)
                .fontWeight(.bold)

            Text(puzzle.title)
                .font(.title2)
                .foregroundStyle(.secondary)

            Spacer()

            Button(Strings.backToList) {
                dismiss()
            }
            .buttonStyle(.borderedProminent)
            .controlSize(.large)
        }
        .padding()
        .navigationBarBackButtonHidden(true)
    }
}

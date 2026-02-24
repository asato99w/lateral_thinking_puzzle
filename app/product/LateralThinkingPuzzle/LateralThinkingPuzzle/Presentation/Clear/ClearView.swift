import SwiftUI

struct ClearView: View {
    let puzzle: PuzzleData
    @Environment(\.dismiss) private var dismiss

    var body: some View {
        VStack(spacing: 32) {
            Spacer()

            Image(systemName: "checkmark.circle.fill")
                .font(.system(size: 80))
                .foregroundStyle(Theme.solvedBadge)

            Text(Strings.cleared)
                .font(.largeTitle)
                .fontWeight(.bold)

            Text(puzzle.title)
                .font(.title2)
                .foregroundStyle(.secondary)

            Spacer()

            Button {
                dismiss()
            } label: {
                Text(Strings.backToList)
                    .font(.headline)
                    .frame(maxWidth: .infinity)
                    .padding(.vertical, 14)
                    .background(Theme.accent)
                    .foregroundStyle(.white)
                    .clipShape(RoundedRectangle(cornerRadius: Theme.cardCornerRadius))
            }
        }
        .padding()
        .navigationBarBackButtonHidden(true)
    }
}

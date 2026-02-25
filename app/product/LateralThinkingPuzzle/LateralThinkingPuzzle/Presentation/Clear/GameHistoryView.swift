import SwiftUI

struct GameHistoryView: View {
    let history: GameHistory

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 8) {
                ForEach(Array(history.entries.enumerated()), id: \.offset) { index, entry in
                    let answer = Answer(rawValue: entry.answer) ?? .yes

                    HStack(spacing: 0) {
                        Text("\(index + 1)")
                            .font(.caption.bold().monospacedDigit())
                            .foregroundStyle(answerColor(answer))
                            .frame(width: 40)
                            .frame(maxHeight: .infinity)
                            .background(answerColor(answer).opacity(0.12))

                        VStack(alignment: .leading, spacing: 4) {
                            Text(entry.questionText)
                                .font(.subheadline)
                            Text(answerLabel(answer))
                                .font(.caption.weight(.bold))
                                .foregroundStyle(answerColor(answer))
                        }
                        .padding(.horizontal, 12)
                        .padding(.vertical, 10)

                        Spacer(minLength: 0)
                    }
                    .background(Theme.cardBackground)
                    .clipShape(RoundedRectangle(cornerRadius: Theme.cardCornerRadius))
                    .overlay(
                        RoundedRectangle(cornerRadius: Theme.cardCornerRadius)
                            .stroke(answerColor(answer).opacity(0.2), lineWidth: 1)
                    )
                }
            }
            .padding()
        }
        .navigationTitle(history.puzzleTitle)
        .navigationBarTitleDisplayMode(.large)
    }

    // MARK: - Helpers

    private func answerLabel(_ answer: Answer) -> String {
        switch answer {
        case .yes: Strings.answerYes
        case .no: Strings.answerNo
        case .irrelevant: Strings.answerIrrelevant
        }
    }

    private func answerColor(_ answer: Answer) -> Color {
        switch answer {
        case .yes: Theme.answerYes
        case .no: Theme.answerNo
        case .irrelevant: Theme.answerIrrelevant
        }
    }
}

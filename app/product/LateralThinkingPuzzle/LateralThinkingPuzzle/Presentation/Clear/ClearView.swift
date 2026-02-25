import SwiftUI

struct ClearView: View {
    let puzzle: PuzzleData
    let answeredQuestions: [(question: Question, answer: Answer)]
    @Environment(\.dismiss) private var dismiss

    var body: some View {
        ScrollView {
            VStack(spacing: 24) {
                // Header
                VStack(spacing: 12) {
                    Image(systemName: "checkmark.circle.fill")
                        .font(.system(size: 80))
                        .foregroundStyle(Theme.solvedBadge)

                    Text(Strings.cleared)
                        .font(.largeTitle)
                        .fontWeight(.bold)

                    Text(puzzle.title)
                        .font(.title2)
                        .foregroundStyle(.secondary)
                }
                .padding(.top, 40)

                // History
                if !answeredQuestions.isEmpty {
                    historySection
                }

                // Back button
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
                .padding(.top, 8)
            }
            .padding()
        }
        .navigationBarBackButtonHidden(true)
    }

    // MARK: - History

    private var historySection: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text("\(Strings.answered) (\(answeredQuestions.count))")
                .font(.subheadline.weight(.semibold))
                .foregroundStyle(.secondary)

            ForEach(Array(answeredQuestions.enumerated()), id: \.offset) { index, item in
                HStack(spacing: 0) {
                    Text("\(index + 1)")
                        .font(.caption.bold().monospacedDigit())
                        .foregroundStyle(answerColor(item.answer))
                        .frame(width: 40)
                        .frame(maxHeight: .infinity)
                        .background(answerColor(item.answer).opacity(0.12))

                    VStack(alignment: .leading, spacing: 4) {
                        Text(item.question.text)
                            .font(.subheadline)
                        Text(answerLabel(item.answer))
                            .font(.caption.weight(.bold))
                            .foregroundStyle(answerColor(item.answer))
                    }
                    .padding(.horizontal, 12)
                    .padding(.vertical, 10)

                    Spacer(minLength: 0)
                }
                .background(Theme.cardBackground)
                .clipShape(RoundedRectangle(cornerRadius: Theme.cardCornerRadius))
                .overlay(
                    RoundedRectangle(cornerRadius: Theme.cardCornerRadius)
                        .stroke(answerColor(item.answer).opacity(0.2), lineWidth: 1)
                )
            }
        }
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

import SwiftUI

struct ClearView: View {
    let puzzleInfo: PuzzleInfo
    let answeredQuestions: [(question: Question, answer: Answer)]
    @Environment(\.dismiss) private var dismiss
    @State private var showHistory = false

    var body: some View {
        ScrollView {
            VStack(spacing: 28) {
                // Header
                VStack(spacing: 8) {
                    Image(systemName: "eye.fill")
                        .font(.system(size: 40))
                        .foregroundStyle(Theme.accent)

                    Text(Strings.truth)
                        .font(.title2.weight(.bold))

                    Text(puzzleInfo.title)
                        .font(.subheadline)
                        .foregroundStyle(.secondary)
                }
                .padding(.top, 40)

                // Truth card
                if let truth = puzzleInfo.truth {
                    Text(truth)
                        .font(.body)
                        .lineSpacing(6)
                        .frame(maxWidth: .infinity, alignment: .leading)
                        .padding()
                        .background(Theme.accent.opacity(0.15))
                        .clipShape(RoundedRectangle(cornerRadius: Theme.cardCornerRadius))
                        .overlay(
                            RoundedRectangle(cornerRadius: Theme.cardCornerRadius)
                                .stroke(Theme.accent.opacity(0.5), lineWidth: 1)
                        )
                }

                // Question count
                VStack(spacing: 4) {
                    Text("\(answeredQuestions.count)")
                        .font(.system(size: 56, weight: .bold, design: .rounded))
                        .foregroundStyle(Theme.accent)

                    Text(Strings.questionsAsked)
                        .font(.subheadline)
                        .foregroundStyle(.secondary)
                }

                // View history button
                if !answeredQuestions.isEmpty {
                    Button {
                        showHistory = true
                    } label: {
                        HStack(spacing: 6) {
                            Image(systemName: "list.bullet")
                                .font(.subheadline)
                            Text(Strings.viewHistory)
                                .font(.subheadline.weight(.medium))
                        }
                        .foregroundStyle(Theme.accent)
                    }
                    .buttonStyle(.plain)
                }

                // Back to list button
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
        .sheet(isPresented: $showHistory) {
            NavigationStack {
                historySheet
                    .navigationTitle(Strings.history)
                    .navigationBarTitleDisplayMode(.inline)
                    .toolbar {
                        ToolbarItem(placement: .topBarTrailing) {
                            Button {
                                showHistory = false
                            } label: {
                                Image(systemName: "xmark.circle.fill")
                                    .foregroundStyle(.secondary)
                            }
                        }
                    }
            }
        }
    }

    // MARK: - History Sheet

    private var historySheet: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 8) {
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
            .padding()
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

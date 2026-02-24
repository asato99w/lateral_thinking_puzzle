import SwiftUI

struct GameView: View {
    @State var viewModel: GameViewModel

    /// Tracks feedback overlay: question ID -> answer being shown
    @State private var feedbackForQuestion: [String: Answer] = [:]

    var body: some View {
        if viewModel.isCleared {
            ClearView(puzzle: viewModel.puzzle)
                .transition(.opacity)
        } else {
            ScrollView {
                VStack(alignment: .leading, spacing: 24) {
                    // Statement
                    statementSection

                    // Open Questions
                    if !viewModel.openQuestions.isEmpty {
                        openQuestionsSection
                    }

                    // Answered Questions
                    if !viewModel.answeredQuestions.isEmpty {
                        answeredSection
                    }
                }
                .padding()
            }
            .navigationTitle(viewModel.puzzle.title)
            .navigationBarTitleDisplayMode(.inline)
            .animation(.easeInOut(duration: Theme.transitionDuration), value: viewModel.isCleared)
        }
    }

    // MARK: - Statement

    private var statementSection: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text(Strings.statement)
                .font(.subheadline.weight(.semibold))
                .foregroundStyle(.secondary)
            Text(viewModel.puzzle.statement)
                .font(.body)
        }
        .padding()
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(.fill.quaternary)
        .clipShape(RoundedRectangle(cornerRadius: 12))
    }

    // MARK: - Open Questions

    private var openQuestionsSection: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text(Strings.chooseQuestion)
                .font(.subheadline.weight(.semibold))
                .foregroundStyle(.secondary)
            ForEach(viewModel.openQuestions) { question in
                questionButton(question)
                    .transition(.opacity.combined(with: .move(edge: .leading)))
            }
        }
    }

    private func questionButton(_ question: Question) -> some View {
        Button {
            handleQuestionTap(question)
        } label: {
            HStack(spacing: 0) {
                // Accent bar
                RoundedRectangle(cornerRadius: Theme.accentBarWidth / 2)
                    .fill(Theme.accent)
                    .frame(width: Theme.accentBarWidth)

                Text(question.text)
                    .frame(maxWidth: .infinity, alignment: .leading)
                    .padding(.horizontal, 12)
                    .padding(.vertical, 12)
            }
            .background(.fill.quaternary)
            .clipShape(RoundedRectangle(cornerRadius: Theme.cardCornerRadius))
            .overlay(
                RoundedRectangle(cornerRadius: Theme.cardCornerRadius)
                    .strokeBorder(Color(.separator), lineWidth: 0.5)
            )
            .overlay {
                // Feedback overlay
                if let answer = feedbackForQuestion[question.id] {
                    Text(answerLabel(answer))
                        .font(.headline)
                        .foregroundStyle(answerColor(answer))
                        .frame(maxWidth: .infinity, maxHeight: .infinity)
                        .background(.ultraThinMaterial)
                        .clipShape(RoundedRectangle(cornerRadius: Theme.cardCornerRadius))
                        .transition(.opacity)
                }
            }
            .animation(.easeInOut(duration: Theme.animationDuration), value: feedbackForQuestion[question.id] != nil)
        }
        .buttonStyle(.plain)
        .disabled(feedbackForQuestion[question.id] != nil)
    }

    private func handleQuestionTap(_ question: Question) {
        let answer = question.correctAnswer

        // Show feedback overlay
        withAnimation(.easeInOut(duration: Theme.animationDuration)) {
            feedbackForQuestion[question.id] = answer
        }

        // After delay, commit the answer
        DispatchQueue.main.asyncAfter(deadline: .now() + Theme.feedbackDuration) {
            feedbackForQuestion.removeValue(forKey: question.id)

            withAnimation(.easeInOut(duration: Theme.animationDuration)) {
                viewModel.selectQuestion(question)
            }
        }
    }

    // MARK: - Answered Questions

    private var answeredSection: some View {
        DisclosureGroup(isExpanded: $viewModel.showAnswered) {
            VStack(alignment: .leading, spacing: 8) {
                ForEach(viewModel.answeredQuestions, id: \.question.id) { item in
                    VStack(alignment: .leading, spacing: 4) {
                        Text(item.question.text)
                            .font(.subheadline)
                        Text(answerLabel(item.answer))
                            .font(.caption.weight(.bold))
                            .foregroundStyle(answerColor(item.answer))
                    }
                    .padding(.vertical, 4)
                }
            }
        } label: {
            Text("\(Strings.answered) (\(viewModel.answeredQuestions.count))")
                .font(.subheadline.weight(.semibold))
                .foregroundStyle(.secondary)
        }
        .tint(.secondary)
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

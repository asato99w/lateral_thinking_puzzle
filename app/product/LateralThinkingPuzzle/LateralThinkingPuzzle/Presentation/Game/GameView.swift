import SwiftUI

struct GameView: View {
    @State var viewModel: GameViewModel

    /// Tracks feedback overlay: question ID -> answer being shown
    @State private var feedbackForQuestion: [String: Answer] = [:]
    @State private var statementExpanded = true

    private var totalQuestionCount: Int {
        viewModel.openQuestions.count + viewModel.answeredQuestions.count
    }

    var body: some View {
        if viewModel.isCleared {
            ClearView(puzzle: viewModel.puzzle)
                .transition(.opacity)
        } else {
            VStack(spacing: 0) {
                // Fixed top area
                VStack(alignment: .leading, spacing: 12) {
                    statementSection

                    if !viewModel.answeredQuestions.isEmpty {
                        answeredSection
                    }

                    progressPill

                    if !viewModel.openQuestions.isEmpty {
                        sectionLabel(Strings.chooseQuestion)
                    }
                }
                .padding(.horizontal)
                .padding(.top, 8)
                .padding(.bottom, 12)

                Divider().opacity(0.3)

                // Category filter tabs
                if !viewModel.puzzle.topicCategories.isEmpty {
                    categoryTabBar
                }

                // Scrollable: question buttons only
                ScrollView {
                    VStack(alignment: .leading, spacing: 8) {
                        if !viewModel.filteredOpenQuestions.isEmpty {
                            questionList
                        }
                    }
                    .padding()
                }
            }
            .navigationBarTitleDisplayMode(.inline)
            .animation(.easeInOut(duration: Theme.transitionDuration), value: viewModel.isCleared)
        }
    }

    // MARK: - Statement

    private var statementSection: some View {
        VStack(alignment: .leading, spacing: 12) {
            // Header row (always visible, tappable)
            Button {
                withAnimation(.easeInOut(duration: Theme.animationDuration)) {
                    statementExpanded.toggle()
                }
            } label: {
                HStack(spacing: 12) {
                    Text(PuzzleMetadata.icon(for: viewModel.puzzleID))
                        .font(.system(size: 36))
                        .frame(width: 56, height: 56)
                        .background(Theme.accent.opacity(0.2))
                        .clipShape(RoundedRectangle(cornerRadius: 12))

                    VStack(alignment: .leading, spacing: 4) {
                        Text(viewModel.puzzle.title)
                            .font(.headline)
                        difficultyStars(PuzzleMetadata.difficulty(for: viewModel.puzzleID))
                    }

                    Spacer()

                    Image(systemName: statementExpanded ? "chevron.up" : "chevron.down")
                        .font(.caption)
                        .foregroundStyle(.secondary)
                }
            }
            .buttonStyle(.plain)

            // Collapsible statement text
            if statementExpanded {
                sectionLabel(Strings.statement)

                Text(viewModel.puzzle.statement)
                    .font(.body)
                    .lineSpacing(4)
            }
        }
        .padding()
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(Theme.cardBackground)
        .clipShape(RoundedRectangle(cornerRadius: Theme.cardCornerRadius))
        .overlay(
            RoundedRectangle(cornerRadius: Theme.cardCornerRadius)
                .stroke(Theme.cardBorder, lineWidth: 1)
        )
    }

    // MARK: - Progress Pill

    private var progressPill: some View {
        HStack(spacing: 6) {
            Text("\(viewModel.answeredQuestions.count)")
                .font(.title3.bold().monospacedDigit())
                .foregroundStyle(Theme.accent)
            Text("/ \(totalQuestionCount)")
                .font(.subheadline.monospacedDigit())
                .foregroundStyle(Theme.progressText)
        }
        .padding(.horizontal, 14)
        .padding(.vertical, 8)
        .background(Theme.accent.opacity(0.12))
        .clipShape(Capsule())
    }

    // MARK: - Open Questions

    private var openQuestionsSection: some View {
        VStack(alignment: .leading, spacing: 8) {
            sectionLabel(Strings.chooseQuestion)
            questionList
        }
    }

    private var questionList: some View {
        ForEach(Array(viewModel.filteredOpenQuestions.enumerated()), id: \.element.id) { index, question in
            questionButton(question, number: index + 1)
                .transition(.opacity.combined(with: .move(edge: .leading)))
        }
    }

    private func questionButton(_ question: Question, number: Int) -> some View {
        Button {
            handleQuestionTap(question)
        } label: {
            HStack(spacing: 0) {
                // Number badge
                Text("\(number)")
                    .font(.caption.bold().monospacedDigit())
                    .foregroundStyle(Theme.accent)
                    .frame(width: 40)
                    .frame(maxHeight: .infinity)
                    .background(Theme.accent.opacity(0.15))

                Text(question.text)
                    .font(.subheadline)
                    .frame(maxWidth: .infinity, alignment: .leading)
                    .padding(.horizontal, 12)
                    .padding(.vertical, 14)
            }
            .background(Theme.cardBackground)
            .clipShape(RoundedRectangle(cornerRadius: Theme.cardCornerRadius))
            .overlay(
                RoundedRectangle(cornerRadius: Theme.cardCornerRadius)
                    .stroke(Theme.cardBorder, lineWidth: 1)
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
                ForEach(Array(viewModel.answeredQuestions.enumerated()), id: \.element.question.id) { index, item in
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
            .padding(.top, 8)
        } label: {
            Text("\(Strings.answered) (\(viewModel.answeredQuestions.count))")
                .font(.subheadline.weight(.semibold))
                .foregroundStyle(.secondary)
        }
        .tint(.secondary)
    }

    // MARK: - Category Tab Bar

    private var categoryTabBar: some View {
        ScrollView(.horizontal, showsIndicators: false) {
            HStack(spacing: 8) {
                categoryTab(
                    label: Strings.allCategories,
                    count: viewModel.openQuestions.count,
                    isActive: viewModel.selectedCategory == nil
                ) {
                    viewModel.selectedCategory = nil
                }

                ForEach(viewModel.puzzle.topicCategories) { cat in
                    categoryTab(
                        label: cat.name,
                        count: viewModel.openCountForCategory(cat.id),
                        isActive: viewModel.selectedCategory == cat.id
                    ) {
                        viewModel.selectedCategory = cat.id
                    }
                }
            }
            .padding(.horizontal)
            .padding(.vertical, 8)
        }
    }

    private func categoryTab(label: String, count: Int, isActive: Bool, action: @escaping () -> Void) -> some View {
        Button(action: action) {
            HStack(spacing: 4) {
                Text(label)
                    .font(.caption.weight(.semibold))
                    .lineLimit(1)
                Text("\(count)")
                    .font(.caption2.bold().monospacedDigit())
                    .padding(.horizontal, 5)
                    .padding(.vertical, 1)
                    .background(.white.opacity(isActive ? 0.2 : 0.1))
                    .clipShape(Capsule())
            }
            .padding(.horizontal, 12)
            .padding(.vertical, 7)
            .background(isActive ? Theme.categoryActive : Theme.categoryInactive)
            .foregroundStyle(.white)
            .clipShape(Capsule())
        }
        .buttonStyle(.plain)
        .animation(.easeInOut(duration: Theme.animationDuration), value: isActive)
    }

    // MARK: - Helpers

    private func sectionLabel(_ text: String) -> some View {
        HStack(spacing: 8) {
            RoundedRectangle(cornerRadius: 2)
                .fill(Theme.accent)
                .frame(width: 4, height: 18)
            Text(text)
                .font(.subheadline.weight(.semibold))
                .foregroundStyle(.white.opacity(0.85))
        }
    }

    private func difficultyStars(_ level: Int) -> some View {
        HStack(spacing: 4) {
            ForEach(1...3, id: \.self) { star in
                Image(systemName: star <= level ? "star.fill" : "star")
                    .font(.caption2)
                    .foregroundStyle(star <= level ? Theme.starFilled : Theme.starEmpty)
            }
        }
    }

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

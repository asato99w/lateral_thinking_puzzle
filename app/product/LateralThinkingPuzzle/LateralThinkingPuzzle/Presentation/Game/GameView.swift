import SwiftUI

struct GameView: View {
    @State var viewModel: GameViewModel

    var body: some View {
        if viewModel.isCleared {
            ClearView(puzzle: viewModel.puzzle)
        } else {
            ScrollView {
                VStack(alignment: .leading, spacing: 24) {
                    // Statement
                    VStack(alignment: .leading, spacing: 8) {
                        Text(Strings.statement)
                            .font(.headline)
                        Text(viewModel.puzzle.statement)
                            .font(.body)
                    }
                    .padding()
                    .frame(maxWidth: .infinity, alignment: .leading)
                    .background(.ultraThinMaterial)
                    .clipShape(RoundedRectangle(cornerRadius: 12))

                    // Open Questions
                    if !viewModel.openQuestions.isEmpty {
                        VStack(alignment: .leading, spacing: 8) {
                            Text(Strings.chooseQuestion)
                                .font(.headline)
                            ForEach(viewModel.openQuestions) { question in
                                Button {
                                    viewModel.selectQuestion(question)
                                } label: {
                                    Text(question.text)
                                        .frame(maxWidth: .infinity, alignment: .leading)
                                        .padding()
                                        .background(Color(.systemGray6))
                                        .clipShape(RoundedRectangle(cornerRadius: 8))
                                }
                                .buttonStyle(.plain)
                            }
                        }
                    }

                    // Answered Questions
                    if !viewModel.answeredQuestions.isEmpty {
                        VStack(alignment: .leading, spacing: 8) {
                            Text(Strings.answered)
                                .font(.headline)
                                .foregroundStyle(.secondary)
                            ForEach(viewModel.answeredQuestions, id: \.question.id) { item in
                                HStack {
                                    Text(item.question.text)
                                        .font(.subheadline)
                                    Spacer()
                                    Text(answerLabel(item.answer))
                                        .font(.caption)
                                        .fontWeight(.bold)
                                        .foregroundStyle(answerColor(item.answer))
                                }
                                .padding(.vertical, 4)
                            }
                        }
                    }
                }
                .padding()
            }
            .navigationTitle(viewModel.puzzle.title)
            .navigationBarTitleDisplayMode(.inline)
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
        case .yes: .green
        case .no: .red
        case .irrelevant: .gray
        }
    }
}

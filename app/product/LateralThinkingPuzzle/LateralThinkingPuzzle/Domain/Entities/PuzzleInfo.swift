struct PuzzleInfo: Equatable, Sendable {
    let title: String
    let statement: String
    let truth: String?
    let topicCategories: [TopicCategory]
}

extension PuzzleData {
    var puzzleInfo: PuzzleInfo {
        PuzzleInfo(
            title: title,
            statement: statement,
            truth: truth,
            topicCategories: topicCategories
        )
    }
}

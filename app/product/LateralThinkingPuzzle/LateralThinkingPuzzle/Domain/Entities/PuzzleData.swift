struct TopicCategory: Equatable, Sendable, Identifiable {
    let id: String
    let name: String
}

struct PuzzleData: Equatable, Sendable {
    let title: String
    let statement: String
    let initParadigm: String
    let psValues: [(String, Int)]
    let allDescriptorIDs: [String]
    let paradigms: [String: Paradigm]
    let questions: [Question]
    let tier: PuzzleTier
    let topicCategories: [TopicCategory]

    static func == (lhs: PuzzleData, rhs: PuzzleData) -> Bool {
        lhs.title == rhs.title
    }
}

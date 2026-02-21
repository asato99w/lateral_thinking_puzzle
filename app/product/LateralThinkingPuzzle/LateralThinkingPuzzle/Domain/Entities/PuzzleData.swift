struct PuzzleData: Equatable, Sendable {
    let title: String
    let statement: String
    let initParadigm: String
    let tensionThreshold: Int
    let shiftCandidates: [String: [String]]
    let psValues: [(String, Int)]
    let allDescriptorIDs: [String]
    let paradigms: [String: Paradigm]
    let questions: [Question]
    let tier: PuzzleTier

    static func == (lhs: PuzzleData, rhs: PuzzleData) -> Bool {
        lhs.title == rhs.title
    }
}

struct Question: Equatable, Identifiable, Sendable {
    let id: String
    let text: String
    let ansYes: [(String, Int)]
    let ansNo: [(String, Int)]
    let ansIrrelevant: [String]
    let correctAnswer: Answer
    let isClear: Bool
    let prerequisites: [String]
    let relatedDescriptors: [String]
    let topicCategory: String

    var effect: QuestionEffect {
        switch correctAnswer {
        case .yes:
            return .observation(ansYes)
        case .no:
            return .observation(ansNo)
        case .irrelevant:
            return .irrelevant(ansIrrelevant)
        }
    }

    /// All descriptors referenced by this question (effect + related).
    var allDescriptors: Set<String> {
        var ds = Set<String>()
        for (d, _) in ansYes { ds.insert(d) }
        for (d, _) in ansNo { ds.insert(d) }
        for d in ansIrrelevant { ds.insert(d) }
        for d in relatedDescriptors { ds.insert(d) }
        return ds
    }

    static func == (lhs: Question, rhs: Question) -> Bool {
        lhs.id == rhs.id
    }
}

enum QuestionEffect: Equatable, Sendable {
    case observation([(String, Int)])
    case irrelevant([String])

    static func == (lhs: QuestionEffect, rhs: QuestionEffect) -> Bool {
        switch (lhs, rhs) {
        case let (.observation(a), .observation(b)):
            return a.count == b.count && zip(a, b).allSatisfy { $0.0 == $1.0 && $0.1 == $1.1 }
        case let (.irrelevant(a), .irrelevant(b)):
            return a == b
        default:
            return false
        }
    }
}

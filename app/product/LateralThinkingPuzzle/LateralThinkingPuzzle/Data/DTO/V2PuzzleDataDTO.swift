import Foundation

struct V2FactDTO: Codable {
    let id: String
    let label: String
}

struct V2PieceDTO: Codable {
    let id: String
    let label: String
    let facts: [String]
    let dependsOn: [String]

    enum CodingKeys: String, CodingKey {
        case id, label, facts
        case dependsOn = "depends_on"
    }
}

struct V2HypothesisDTO: Codable {
    let id: String
    let label: String
    let formationConditions: [[String]]

    enum CodingKeys: String, CodingKey {
        case id, label
        case formationConditions = "formation_conditions"
    }
}

struct V2QuestionDTO: Codable {
    let id: String
    let text: String
    let answer: String
    let recallConditions: [[String]]
    let reveals: [String]
    let mechanism: String
    let correctAnswer: String?
    let topicCategory: String?

    enum CodingKeys: String, CodingKey {
        case id, text, answer
        case recallConditions = "recall_conditions"
        case reveals, mechanism
        case correctAnswer = "correct_answer"
        case topicCategory = "topic_category"
    }
}

struct V2PuzzleDataDTO: Codable {
    let id: String
    let title: String
    let statement: String
    let truth: String
    let facts: [V2FactDTO]
    let initialFacts: [String]
    let pieces: [V2PieceDTO]
    let hypotheses: [V2HypothesisDTO]
    let questions: [V2QuestionDTO]
    let topicCategories: [TopicCategoryDTO]?

    enum CodingKeys: String, CodingKey {
        case id, title, statement, truth, facts
        case initialFacts = "initial_facts"
        case pieces, hypotheses, questions
        case topicCategories = "topic_categories"
    }

    func toDomain() -> V2PuzzleData {
        let factsMap = Dictionary(uniqueKeysWithValues: facts.map {
            ($0.id, V2Fact(id: $0.id, label: $0.label))
        })

        let piecesMap = Dictionary(uniqueKeysWithValues: pieces.map {
            ($0.id, V2Piece(id: $0.id, label: $0.label, facts: $0.facts, dependsOn: $0.dependsOn))
        })

        let hypothesesMap = Dictionary(uniqueKeysWithValues: hypotheses.map {
            ($0.id, V2Hypothesis(id: $0.id, label: $0.label, formationConditions: $0.formationConditions))
        })

        let questionsMap = Dictionary(uniqueKeysWithValues: questions.map { q in
            let answer: Answer
            switch q.correctAnswer {
            case "yes": answer = .yes
            case "no": answer = .no
            case "irrelevant": answer = .irrelevant
            default:
                // Derive from answer text if not explicitly set
                answer = q.answer.hasPrefix("はい") || q.answer.lowercased().hasPrefix("yes") ? .yes : .no
            }

            return (q.id, V2Question(
                id: q.id,
                text: q.text,
                answer: q.answer,
                recallConditions: q.recallConditions,
                reveals: q.reveals,
                mechanism: q.mechanism,
                correctAnswer: answer,
                topicCategory: q.topicCategory ?? ""
            ))
        })

        return V2PuzzleData(
            id: id,
            title: title,
            statement: statement,
            truth: truth,
            facts: factsMap,
            initialFacts: initialFacts,
            pieces: piecesMap,
            hypotheses: hypothesesMap,
            questions: questionsMap,
            topicCategories: (topicCategories ?? []).map { $0.toDomain() }
        )
    }
}

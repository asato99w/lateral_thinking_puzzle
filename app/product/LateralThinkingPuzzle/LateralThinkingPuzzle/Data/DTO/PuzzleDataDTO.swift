import Foundation

struct TopicCategoryDTO: Codable {
    let id: String
    let name: String

    func toDomain() -> TopicCategory {
        TopicCategory(id: id, name: name)
    }
}

struct PuzzleDataDTO: Codable {
    let title: String
    let statement: String
    let initParadigm: String
    let tensionThreshold: Int?
    let shiftCandidates: [String: [String]]?
    let psValues: [[PsValueElement]]
    let allDescriptorIds: [String]
    let paradigms: [ParadigmDTO]
    let questions: [QuestionDTO]
    let topicCategories: [TopicCategoryDTO]?

    enum CodingKeys: String, CodingKey {
        case title, statement
        case initParadigm = "init_paradigm"
        case tensionThreshold = "tension_threshold"
        case shiftCandidates = "shift_candidates"
        case psValues = "ps_values"
        case allDescriptorIds = "all_descriptor_ids"
        case paradigms, questions
        case topicCategories = "topic_categories"
    }

    func toDomain() throws -> PuzzleData {
        var paradigmMap = [String: Paradigm]()
        for dto in paradigms {
            let p = try dto.toDomain()
            paradigmMap[p.id] = p
        }

        let domainQuestions = questions.map { $0.toDomain() }

        let ps = psValues.map { pair -> (String, Int) in
            let id = pair[0].stringValue!
            let val = pair[1].intValue!
            return (id, val)
        }

        let oStar = GameEngine.buildOStar(questions: domainQuestions, psValues: ps)
        GameEngine.computeThresholds(paradigms: &paradigmMap, oStar: oStar)
        GameEngine.computeDepths(paradigms: &paradigmMap, oStar: oStar)

        return PuzzleData(
            title: title,
            statement: statement,
            initParadigm: initParadigm,
            psValues: ps,
            allDescriptorIDs: allDescriptorIds,
            paradigms: paradigmMap,
            questions: domainQuestions,
            tier: .free,
            topicCategories: (topicCategories ?? []).map { $0.toDomain() }
        )
    }
}

// MARK: - Heterogeneous Array Support

enum PsValueElement: Codable {
    case string(String)
    case int(Int)

    var stringValue: String? {
        if case let .string(v) = self { return v }
        return nil
    }

    var intValue: Int? {
        if case let .int(v) = self { return v }
        return nil
    }

    init(from decoder: Decoder) throws {
        let container = try decoder.singleValueContainer()
        if let v = try? container.decode(String.self) {
            self = .string(v)
        } else if let v = try? container.decode(Int.self) {
            self = .int(v)
        } else {
            throw DecodingError.typeMismatch(
                PsValueElement.self,
                DecodingError.Context(codingPath: decoder.codingPath, debugDescription: "Expected String or Int")
            )
        }
    }

    func encode(to encoder: Encoder) throws {
        var container = encoder.singleValueContainer()
        switch self {
        case let .string(v): try container.encode(v)
        case let .int(v): try container.encode(v)
        }
    }
}

// MARK: - ParadigmDTO

struct ParadigmDTO: Codable {
    let id: String
    let name: String
    let pPred: [[PPredElement]]
    let conceivable: [String]
    let relations: [[RelationElement]]

    enum CodingKeys: String, CodingKey {
        case id, name
        case pPred = "p_pred"
        case conceivable
        case relations
    }

    func toDomain() throws -> Paradigm {
        let predDict = Dictionary(uniqueKeysWithValues: pPred.map { pair -> (String, Int) in
            (pair[0].stringValue!, pair[1].intValue!)
        })
        let rels = relations.map { arr -> Relation in
            let src = arr[0].stringValue!
            let tgt = arr[1].stringValue!
            let weight = arr[2].doubleValue!
            return Relation(src: src, tgt: tgt, weight: weight)
        }
        return try Paradigm(
            id: id,
            name: name,
            pPred: predDict,
            conceivable: Set(conceivable),
            relations: rels
        )
    }
}

enum PPredElement: Codable {
    case string(String)
    case int(Int)

    var stringValue: String? {
        if case let .string(v) = self { return v }
        return nil
    }

    var intValue: Int? {
        if case let .int(v) = self { return v }
        return nil
    }

    init(from decoder: Decoder) throws {
        let container = try decoder.singleValueContainer()
        if let v = try? container.decode(String.self) {
            self = .string(v)
        } else if let v = try? container.decode(Int.self) {
            self = .int(v)
        } else {
            throw DecodingError.typeMismatch(
                PPredElement.self,
                DecodingError.Context(codingPath: decoder.codingPath, debugDescription: "Expected String or Int")
            )
        }
    }

    func encode(to encoder: Encoder) throws {
        var container = encoder.singleValueContainer()
        switch self {
        case let .string(v): try container.encode(v)
        case let .int(v): try container.encode(v)
        }
    }
}

enum RelationElement: Codable {
    case string(String)
    case double(Double)

    var stringValue: String? {
        if case let .string(v) = self { return v }
        return nil
    }

    var doubleValue: Double? {
        if case let .double(v) = self { return v }
        return nil
    }

    init(from decoder: Decoder) throws {
        let container = try decoder.singleValueContainer()
        if let v = try? container.decode(String.self) {
            self = .string(v)
        } else if let v = try? container.decode(Double.self) {
            self = .double(v)
        } else {
            throw DecodingError.typeMismatch(
                RelationElement.self,
                DecodingError.Context(codingPath: decoder.codingPath, debugDescription: "Expected String or Double")
            )
        }
    }

    func encode(to encoder: Encoder) throws {
        var container = encoder.singleValueContainer()
        switch self {
        case let .string(v): try container.encode(v)
        case let .double(v): try container.encode(v)
        }
    }
}

// MARK: - QuestionDTO

struct QuestionDTO: Codable {
    let id: String
    let text: String
    let ansYes: [[EffectElement]]
    let ansNo: [[EffectElement]]
    let ansIrrelevant: [String]
    let correctAnswer: String
    let isClear: Bool?
    let prerequisites: [String]?
    let relatedDescriptors: [String]?
    let topicCategory: String?

    enum CodingKeys: String, CodingKey {
        case id, text
        case ansYes = "ans_yes"
        case ansNo = "ans_no"
        case ansIrrelevant = "ans_irrelevant"
        case correctAnswer = "correct_answer"
        case isClear = "is_clear"
        case prerequisites
        case relatedDescriptors = "related_descriptors"
        case topicCategory = "topic_category"
    }

    func toDomain() -> Question {
        let yes = ansYes.map { pair -> (String, Int) in
            (pair[0].stringValue!, pair[1].intValue!)
        }
        let no = ansNo.map { pair -> (String, Int) in
            (pair[0].stringValue!, pair[1].intValue!)
        }
        let answer: Answer
        switch correctAnswer {
        case "yes": answer = .yes
        case "no": answer = .no
        default: answer = .irrelevant
        }
        return Question(
            id: id,
            text: text,
            ansYes: yes,
            ansNo: no,
            ansIrrelevant: ansIrrelevant,
            correctAnswer: answer,
            isClear: isClear ?? false,
            prerequisites: prerequisites ?? [],
            relatedDescriptors: relatedDescriptors ?? [],
            topicCategory: topicCategory ?? ""
        )
    }
}

enum EffectElement: Codable {
    case string(String)
    case int(Int)

    var stringValue: String? {
        if case let .string(v) = self { return v }
        return nil
    }

    var intValue: Int? {
        if case let .int(v) = self { return v }
        return nil
    }

    init(from decoder: Decoder) throws {
        let container = try decoder.singleValueContainer()
        if let v = try? container.decode(String.self) {
            self = .string(v)
        } else if let v = try? container.decode(Int.self) {
            self = .int(v)
        } else {
            throw DecodingError.typeMismatch(
                EffectElement.self,
                DecodingError.Context(codingPath: decoder.codingPath, debugDescription: "Expected String or Int")
            )
        }
    }

    func encode(to encoder: Encoder) throws {
        var container = encoder.singleValueContainer()
        switch self {
        case let .string(v): try container.encode(v)
        case let .int(v): try container.encode(v)
        }
    }
}

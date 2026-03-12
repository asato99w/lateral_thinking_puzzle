// MARK: - V2 Domain Models

enum DerivationMode: Sendable {
    case v2  // formation_conditions で不動点計算 → derived
    case v3  // entailment_conditions → confirmed (不動点) + formation_conditions → derived (1回パス)
}

struct V2Descriptor: Equatable, Sendable {
    let id: String
    let label: String
    let formationConditions: [[String]]?  // nil = 基礎記述素
    let entailmentConditions: [[String]]?  // v3: 論理的導出（confirmed → confirmed）
    let rejectionConditions: [[String]]?  // confirmed により棄却される条件

    init(id: String, label: String, formationConditions: [[String]]?, entailmentConditions: [[String]]? = nil, rejectionConditions: [[String]]? = nil) {
        self.id = id
        self.label = label
        self.formationConditions = formationConditions
        self.entailmentConditions = entailmentConditions
        self.rejectionConditions = rejectionConditions
    }
}

struct V2Piece: Equatable, Sendable {
    let id: String
    let label: String
    let members: [String]
    let dependsOn: [String]
}

struct V2Question: Equatable, Sendable {
    let id: String
    let text: String
    let answer: String
    let reveals: [String]
    let mechanism: String
    let prerequisites: [String]
    let correctAnswer: Answer
    let topicCategory: String
}

struct V2PuzzleData: Sendable {
    let id: String
    let title: String
    let statement: String
    let truth: String
    let descriptors: [String: V2Descriptor]
    let initialConfirmed: [String]
    let clearConditions: [[String]]
    let pieces: [String: V2Piece]
    let questions: [String: V2Question]
    let topicCategories: [TopicCategory]
    let derivationMode: DerivationMode

    init(id: String, title: String, statement: String, truth: String,
         descriptors: [String: V2Descriptor], initialConfirmed: [String],
         clearConditions: [[String]], pieces: [String: V2Piece],
         questions: [String: V2Question], topicCategories: [TopicCategory],
         derivationMode: DerivationMode = .v2) {
        self.id = id
        self.title = title
        self.statement = statement
        self.truth = truth
        self.descriptors = descriptors
        self.initialConfirmed = initialConfirmed
        self.clearConditions = clearConditions
        self.pieces = pieces
        self.questions = questions
        self.topicCategories = topicCategories
        self.derivationMode = derivationMode
    }
}

struct V2GameState: Equatable, Sendable {
    var confirmed: Set<String>
    var derived: Set<String>
    var discoveredPieces: Set<String>
    var answered: Set<String>

    var known: Set<String> {
        confirmed.union(derived)
    }

    init(confirmed: Set<String>, derived: Set<String> = [], discoveredPieces: Set<String>, answered: Set<String>) {
        self.confirmed = confirmed
        self.derived = derived
        self.discoveredPieces = discoveredPieces
        self.answered = answered
    }
}

// MARK: - V2 Engine

struct V2AnswerResult: Sendable {
    let newConfirmed: [String]
    let newDerived: [String]
    let newRejected: [String]
    let newPieces: [String]
    let mechanism: String
}

enum V2GameEngine {

    static func initGame(puzzle: V2PuzzleData) -> V2GameState {
        var state = V2GameState(
            confirmed: Set(puzzle.initialConfirmed),
            derived: [],
            discoveredPieces: [],
            answered: []
        )
        switch puzzle.derivationMode {
        case .v2:
            _ = evaluateDerivations(state: &state, puzzle: puzzle)
        case .v3:
            _ = evaluateEntailments(state: &state, puzzle: puzzle)
            _ = evaluateHypotheses(state: &state, puzzle: puzzle)
        }
        return state
    }

    /// confirmed 集合から導出可能な記述素を不動点計算で求め、state.derived を更新する。
    /// state.confirmed は変更しない。導出結果は state.derived に格納される。
    /// 戻り値: (newlyDerived, newlyRejected)
    @discardableResult
    static func evaluateDerivations(state: inout V2GameState, puzzle: V2PuzzleData) -> (newlyDerived: [String], newlyRejected: [String]) {
        // Step 1: 棄却集合の計算（confirmed のみ参照）
        var rejected = Set<String>()
        for d in puzzle.descriptors.values {
            guard let rejConds = d.rejectionConditions else { continue }
            if rejConds.contains(where: { group in group.allSatisfy { state.confirmed.contains($0) } }) {
                rejected.insert(d.id)
            }
        }

        // Step 2: 不動点計算（rejected をスキップ）
        var knownSet = Set(state.confirmed)
        var changed = true
        while changed {
            changed = false
            for d in puzzle.descriptors.values {
                guard let conditions = d.formationConditions else { continue }
                if knownSet.contains(d.id) || rejected.contains(d.id) { continue }
                for conditionSet in conditions {
                    if conditionSet.allSatisfy({ knownSet.contains($0) }) {
                        knownSet.insert(d.id)
                        changed = true
                        break
                    }
                }
            }
        }

        // Step 3: derived = known - confirmed
        let newDerivedSet = knownSet.subtracting(state.confirmed)
        let newlyDerived = newDerivedSet.subtracting(state.derived).sorted()
        let newlyRejected = state.derived.subtracting(newDerivedSet).subtracting(state.confirmed).sorted()
        state.derived = newDerivedSet
        return (newlyDerived: newlyDerived, newlyRejected: newlyRejected)
    }

    static func availableQuestions(state: V2GameState, puzzle: V2PuzzleData) -> [V2Question] {
        puzzle.questions.values.filter { q in
            guard !state.answered.contains(q.id) else { return false }
            // prerequisites: confirmed のみで判定
            if !q.prerequisites.isEmpty && !q.prerequisites.allSatisfy({ state.confirmed.contains($0) }) {
                return false
            }
            // 想起条件: reveals[0] の formationConditions を known (confirmed ∪ derived) で判定
            guard let rc = deriveRecallConditions(question: q, puzzle: puzzle) else { return true }
            return checkConditions(rc, state: state)
        }
    }

    static func answerQuestion(state: inout V2GameState, question: V2Question, puzzle: V2PuzzleData) -> V2AnswerResult {
        var newConfirmed: [String] = []
        var newPieces: [String] = []

        // reveals の記述素を confirmed に追加
        for descriptorID in question.reveals {
            if !state.confirmed.contains(descriptorID) {
                state.confirmed.insert(descriptorID)
                newConfirmed.append(descriptorID)
            }
        }

        // 導出の再評価（derivationMode で分岐）
        let newDerived: [String]
        let newRejected: [String]
        switch puzzle.derivationMode {
        case .v2:
            let result = evaluateDerivations(state: &state, puzzle: puzzle)
            newDerived = result.newlyDerived
            newRejected = result.newlyRejected
        case .v3:
            let entailed = evaluateEntailments(state: &state, puzzle: puzzle)
            newConfirmed.append(contentsOf: entailed)
            let result = evaluateHypotheses(state: &state, puzzle: puzzle)
            newDerived = result.newlyDerived
            newRejected = result.newlyRejected
        }

        // ピースの構成記述素がすべて揃ったかチェック（confirmed ∪ derived で判定）
        let knownSet = state.known
        for piece in puzzle.pieces.values {
            if state.discoveredPieces.contains(piece.id) { continue }
            guard piece.members.allSatisfy({ knownSet.contains($0) }) else { continue }
            guard piece.dependsOn.allSatisfy({ state.discoveredPieces.contains($0) }) else { continue }
            state.discoveredPieces.insert(piece.id)
            newPieces.append(piece.id)
        }

        state.answered.insert(question.id)

        return V2AnswerResult(
            newConfirmed: newConfirmed,
            newDerived: newDerived,
            newRejected: newRejected,
            newPieces: newPieces,
            mechanism: question.mechanism
        )
    }

    static func checkComplete(state: V2GameState, puzzle: V2PuzzleData) -> Bool {
        puzzle.clearConditions.contains { conditionSet in
            conditionSet.allSatisfy { state.confirmed.contains($0) }
        }
    }

    // MARK: - v3 Derivation

    /// v3 論理的導出: entailment_conditions → confirmed の不動点計算。
    /// 論理的帰結であり連鎖を許容する。confirmed に直接追加される。
    /// 戻り値: 新たに confirmed に追加された命題のリスト
    @discardableResult
    static func evaluateEntailments(state: inout V2GameState, puzzle: V2PuzzleData) -> [String] {
        var newlyConfirmed: [String] = []
        var changed = true
        while changed {
            changed = false
            for d in puzzle.descriptors.values {
                guard let conditions = d.entailmentConditions else { continue }
                if state.confirmed.contains(d.id) { continue }
                for conditionSet in conditions {
                    if conditionSet.allSatisfy({ state.confirmed.contains($0) }) {
                        state.confirmed.insert(d.id)
                        newlyConfirmed.append(d.id)
                        changed = true
                        break
                    }
                }
            }
        }
        return newlyConfirmed
    }

    /// v3 仮説導出: formation_conditions → derived の1回パス（連鎖なし）。
    /// confirmed のみ参照し、derived 同士の連鎖は行わない。
    /// 戻り値: (newlyDerived, newlyRejected)
    @discardableResult
    static func evaluateHypotheses(state: inout V2GameState, puzzle: V2PuzzleData) -> (newlyDerived: [String], newlyRejected: [String]) {
        // Step 1: 棄却集合の計算（confirmed のみ参照）
        var rejected = Set<String>()
        for d in puzzle.descriptors.values {
            guard let rejConds = d.rejectionConditions else { continue }
            if rejConds.contains(where: { group in group.allSatisfy { state.confirmed.contains($0) } }) {
                rejected.insert(d.id)
            }
        }

        // Step 2: 1回パス（confirmed のみ参照、連鎖なし）
        var newDerivedSet = Set<String>()
        for d in puzzle.descriptors.values {
            guard let conditions = d.formationConditions else { continue }
            if state.confirmed.contains(d.id) || rejected.contains(d.id) { continue }
            for conditionSet in conditions {
                if conditionSet.allSatisfy({ state.confirmed.contains($0) }) {
                    newDerivedSet.insert(d.id)
                    break
                }
            }
        }

        let newlyDerived = newDerivedSet.subtracting(state.derived).sorted()
        let newlyRejected = state.derived.subtracting(newDerivedSet).subtracting(state.confirmed).sorted()
        state.derived = newDerivedSet
        return (newlyDerived: newlyDerived, newlyRejected: newlyRejected)
    }

    // MARK: - Private

    /// reveals[0] の formationConditions を想起条件として返す。
    /// reveals が空または対象記述素が見つからない場合は nil（常に利用可能）。
    private static func deriveRecallConditions(question: V2Question, puzzle: V2PuzzleData) -> [[String]]? {
        guard let firstReveal = question.reveals.first,
              let descriptor = puzzle.descriptors[firstReveal] else { return nil }
        return descriptor.formationConditions
    }

    private static func checkConditions(_ conditions: [[String]], state: V2GameState) -> Bool {
        let knownSet = state.known
        return conditions.contains { conditionSet in
            conditionSet.allSatisfy { knownSet.contains($0) }
        }
    }
}

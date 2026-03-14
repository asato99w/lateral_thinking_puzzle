// MARK: - V3 Game Engine
//
// v3 専用エンジン。V2GameEngine の分岐ロジックから独立。
//
// v2 との主要な違い:
// - 論理的導出（entailment_conditions）: confirmed → confirmed の不動点計算
// - 仮説導出（formation_conditions）: confirmed → derived の 1 回パス（連鎖なし）
// - 質問の利用可能判定: fc を confirmed のみで判定（derived は使わない）
// - 「いいえ」質問: negation_of 先の命題の fc で利用可能性を判定

enum V3GameEngine {

    static func initGame(puzzle: V2PuzzleData) -> V2GameState {
        var state = V2GameState(
            confirmed: Set(puzzle.initialConfirmed),
            derived: [],
            discoveredPieces: [],
            answered: []
        )
        evaluateEntailments(state: &state, puzzle: puzzle)
        evaluateHypotheses(state: &state, puzzle: puzzle)
        return state
    }

    // MARK: - 論理的導出（confirmed → confirmed の不動点計算）

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

    // MARK: - 仮説導出（confirmed → derived の 1 回パス）

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

        // Step 2: 1 回パス（confirmed のみ参照、連鎖なし）
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

    // MARK: - 質問の利用可能判定

    static func availableQuestions(state: V2GameState, puzzle: V2PuzzleData) -> [V2Question] {
        puzzle.questions.values.filter { q in
            guard !state.answered.contains(q.id) else { return false }
            // prerequisites: confirmed のみで判定
            if !q.prerequisites.isEmpty && !q.prerequisites.allSatisfy({ state.confirmed.contains($0) }) {
                return false
            }
            // 想起条件: confirmed のみで判定（v3 は derived を使わない）
            guard let rc = recallConditions(question: q, puzzle: puzzle) else { return true }
            return rc.contains { conditionSet in
                conditionSet.allSatisfy { state.confirmed.contains($0) }
            }
        }
    }

    // MARK: - 質問回答

    static func answerQuestion(state: inout V2GameState, question: V2Question, puzzle: V2PuzzleData) -> V2AnswerResult {
        var newConfirmed: [String] = []
        var newPieces: [String] = []

        // 1. reveals の命題を confirmed に追加
        for descriptorID in question.reveals {
            if !state.confirmed.contains(descriptorID) {
                state.confirmed.insert(descriptorID)
                newConfirmed.append(descriptorID)
            }
        }

        // 2. 論理的導出（confirmed → confirmed の不動点計算）
        let entailed = evaluateEntailments(state: &state, puzzle: puzzle)
        newConfirmed.append(contentsOf: entailed)

        // 3. 仮説導出（confirmed → derived の 1 回パス）
        let (newDerived, newRejected) = evaluateHypotheses(state: &state, puzzle: puzzle)

        // 4. ピースの構成命題チェック（confirmed ∪ derived で判定）
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

    // MARK: - クリア判定

    static func checkComplete(state: V2GameState, puzzle: V2PuzzleData) -> Bool {
        puzzle.clearConditions.contains { conditionSet in
            conditionSet.allSatisfy { state.confirmed.contains($0) }
        }
    }

    // MARK: - Private

    /// 質問の想起条件（利用可能条件）を返す。
    ///
    /// - 「はい」質問: reveals 先命題の formation_conditions
    /// - 「いいえ」質問: reveals 先命題の negation_of が指す命題の formation_conditions
    /// - reveals が空または対象命題が見つからない場合は nil（常に利用可能）
    private static func recallConditions(question: V2Question, puzzle: V2PuzzleData) -> [[String]]? {
        guard let firstReveal = question.reveals.first,
              let descriptor = puzzle.descriptors[firstReveal] else { return nil }

        // 「いいえ」質問: negation_of 先の命題の fc を使う
        if question.correctAnswer == .no,
           let negationOf = descriptor.negationOf,
           let target = puzzle.descriptors[negationOf] {
            return target.formationConditions
        }

        return descriptor.formationConditions
    }
}

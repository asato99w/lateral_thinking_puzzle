// MARK: - V2 Domain Models

struct V2Descriptor: Equatable, Sendable {
    let id: String
    let label: String
    let formationConditions: [[String]]?  // nil = 基礎記述素
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
    let recallConditions: [[String]]
    let reveals: [String]
    let mechanism: String
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
}

struct V2GameState: Equatable, Sendable {
    var confirmed: Set<String>
    var discoveredPieces: Set<String>
    var answered: Set<String>
}

// MARK: - V2 Engine

struct V2AnswerResult: Sendable {
    let newConfirmed: [String]
    let newDerived: [String]
    let newPieces: [String]
    let mechanism: String
}

enum V2GameEngine {

    static func initGame(puzzle: V2PuzzleData) -> V2GameState {
        var state = V2GameState(
            confirmed: Set(puzzle.initialConfirmed),
            discoveredPieces: [],
            answered: []
        )
        _ = evaluateDerivations(state: &state, puzzle: puzzle)
        return state
    }

    @discardableResult
    static func evaluateDerivations(state: inout V2GameState, puzzle: V2PuzzleData) -> [String] {
        var newlyConfirmed: [String] = []
        var derived = Set(state.confirmed)
        var changed = true
        while changed {
            changed = false
            for d in puzzle.descriptors.values {
                guard let conditions = d.formationConditions else {
                    continue  // 基礎記述素はスキップ
                }
                if derived.contains(d.id) {
                    if !state.confirmed.contains(d.id) {
                        state.confirmed.insert(d.id)
                        newlyConfirmed.append(d.id)
                    }
                    continue
                }
                if state.confirmed.contains(d.id) {
                    derived.insert(d.id)
                    changed = true
                    continue
                }
                for conditionSet in conditions {
                    if conditionSet.allSatisfy({ derived.contains($0) }) {
                        derived.insert(d.id)
                        if !state.confirmed.contains(d.id) {
                            state.confirmed.insert(d.id)
                            newlyConfirmed.append(d.id)
                        }
                        changed = true
                        break
                    }
                }
            }
        }
        return newlyConfirmed
    }

    static func availableQuestions(state: V2GameState, puzzle: V2PuzzleData) -> [V2Question] {
        puzzle.questions.values.filter { q in
            !state.answered.contains(q.id) && checkConditions(q.recallConditions, state: state)
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

        // 導出の再評価
        let newDerived = evaluateDerivations(state: &state, puzzle: puzzle)

        // ピースの構成記述素がすべて揃ったかチェック
        for piece in puzzle.pieces.values {
            if state.discoveredPieces.contains(piece.id) { continue }
            guard piece.members.allSatisfy({ state.confirmed.contains($0) }) else { continue }
            guard piece.dependsOn.allSatisfy({ state.discoveredPieces.contains($0) }) else { continue }
            state.discoveredPieces.insert(piece.id)
            newPieces.append(piece.id)
        }

        state.answered.insert(question.id)

        return V2AnswerResult(
            newConfirmed: newConfirmed,
            newDerived: newDerived,
            newPieces: newPieces,
            mechanism: question.mechanism
        )
    }

    static func checkComplete(state: V2GameState, puzzle: V2PuzzleData) -> Bool {
        puzzle.clearConditions.contains { conditionSet in
            conditionSet.allSatisfy { state.confirmed.contains($0) }
        }
    }

    // MARK: - Private

    private static func checkConditions(_ conditions: [[String]], state: V2GameState) -> Bool {
        conditions.contains { conditionSet in
            conditionSet.allSatisfy { state.confirmed.contains($0) }
        }
    }
}

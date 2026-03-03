// MARK: - V2 Domain Models

struct V2Fact: Equatable, Sendable {
    let id: String
    let label: String
}

struct V2Piece: Equatable, Sendable {
    let id: String
    let label: String
    let facts: [String]
    let dependsOn: [String]
}

struct V2Hypothesis: Equatable, Sendable {
    let id: String
    let label: String
    let formationConditions: [[String]]
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
    let facts: [String: V2Fact]
    let initialFacts: [String]
    let pieces: [String: V2Piece]
    let hypotheses: [String: V2Hypothesis]
    let questions: [String: V2Question]
    let topicCategories: [TopicCategory]
}

struct V2GameState: Equatable, Sendable {
    var observedFacts: Set<String>
    var formedHypotheses: Set<String>
    var discoveredPieces: Set<String>
    var answered: Set<String>
}

// MARK: - V2 Engine

struct V2AnswerResult: Sendable {
    let newFacts: [String]
    let newHypotheses: [String]
    let newPieces: [String]
    let mechanism: String
}

enum V2GameEngine {

    static func initGame(puzzle: V2PuzzleData) -> V2GameState {
        var state = V2GameState(
            observedFacts: Set(puzzle.initialFacts),
            formedHypotheses: [],
            discoveredPieces: [],
            answered: []
        )
        _ = evaluateHypotheses(state: &state, puzzle: puzzle)
        return state
    }

    @discardableResult
    static func evaluateHypotheses(state: inout V2GameState, puzzle: V2PuzzleData) -> [String] {
        var newlyFormed: [String] = []
        var derived = state.observedFacts

        var changed = true
        while changed {
            changed = false
            for h in puzzle.hypotheses.values {
                if derived.contains(h.id) { continue }

                // Hypothesis matches an observed fact
                if state.observedFacts.contains(h.id) {
                    derived.insert(h.id)
                    if !state.formedHypotheses.contains(h.id) {
                        state.formedHypotheses.insert(h.id)
                        newlyFormed.append(h.id)
                    }
                    changed = true
                    continue
                }

                // Formation conditions (OR of AND) met
                for conditionSet in h.formationConditions {
                    if conditionSet.allSatisfy({ derived.contains($0) }) {
                        derived.insert(h.id)
                        if !state.formedHypotheses.contains(h.id) {
                            state.formedHypotheses.insert(h.id)
                            newlyFormed.append(h.id)
                        }
                        changed = true
                        break
                    }
                }
            }
        }
        return newlyFormed
    }

    static func availableQuestions(state: V2GameState, puzzle: V2PuzzleData) -> [V2Question] {
        puzzle.questions.values.filter { q in
            !state.answered.contains(q.id) && checkConditions(q.recallConditions, state: state)
        }
    }

    static func answerQuestion(state: inout V2GameState, question: V2Question, puzzle: V2PuzzleData) -> V2AnswerResult {
        var newFacts: [String] = []
        var newPieces: [String] = []

        // Add revealed facts
        for factID in question.reveals {
            if !state.observedFacts.contains(factID) {
                state.observedFacts.insert(factID)
                newFacts.append(factID)
            }
        }

        // Re-evaluate hypotheses
        let newHypotheses = evaluateHypotheses(state: &state, puzzle: puzzle)

        // Check piece completion
        for piece in puzzle.pieces.values {
            if state.discoveredPieces.contains(piece.id) { continue }
            guard piece.facts.allSatisfy({ state.observedFacts.contains($0) }) else { continue }
            guard piece.dependsOn.allSatisfy({ state.discoveredPieces.contains($0) }) else { continue }
            state.discoveredPieces.insert(piece.id)
            newPieces.append(piece.id)
        }

        state.answered.insert(question.id)

        return V2AnswerResult(
            newFacts: newFacts,
            newHypotheses: newHypotheses,
            newPieces: newPieces,
            mechanism: question.mechanism
        )
    }

    static func checkComplete(state: V2GameState, puzzle: V2PuzzleData) -> Bool {
        puzzle.pieces.keys.allSatisfy { state.discoveredPieces.contains($0) }
    }

    // MARK: - Private

    private static func checkConditions(_ conditions: [[String]], state: V2GameState) -> Bool {
        conditions.contains { conditionSet in
            conditionSet.allSatisfy { state.formedHypotheses.contains($0) }
        }
    }
}

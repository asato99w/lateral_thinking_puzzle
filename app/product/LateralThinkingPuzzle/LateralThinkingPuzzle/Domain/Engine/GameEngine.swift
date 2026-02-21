import Foundation

enum GameEngine {

    static let epsilon: Double = 0.2
    static let defaultTensionThreshold: Int = 2

    // MARK: - Tension

    static func tension(o: [String: Int], paradigm: Paradigm) -> Int {
        let overlap = paradigm.dAll.intersection(Set(o.keys))
        return overlap.reduce(0) { count, d in
            count + (paradigm.prediction(d) != o[d] ? 1 : 0)
        }
    }

    // MARK: - Alignment

    static func alignment(h: [String: Double], paradigm: Paradigm) -> Double {
        let dAll = paradigm.dAll
        guard !dAll.isEmpty else { return 0.0 }
        var score = 0.0
        for d in dAll {
            let hVal = h[d] ?? 0.5
            if paradigm.dPlus.contains(d) {
                score += hVal
            } else {
                score += 1.0 - hVal
            }
        }
        return score / Double(dAll.count)
    }

    // MARK: - Assimilate

    static func assimilateDescriptor(h: inout [String: Double], dID: String, paradigm: Paradigm) {
        for rel in paradigm.relations {
            if rel.src == dID {
                if let pred = paradigm.prediction(rel.tgt) {
                    let hTgt = h[rel.tgt] ?? 0.5
                    h[rel.tgt] = hTgt + rel.weight * (Double(pred) - hTgt)
                }
            }
        }
    }

    static func assimilateFromParadigm(h: inout [String: Double], o: [String: Int], paradigm: Paradigm) {
        for dID in Set(o.keys).intersection(paradigm.dAll) {
            if let pred = paradigm.prediction(dID), pred == o[dID] {
                assimilateDescriptor(h: &h, dID: dID, paradigm: paradigm)
            }
        }
        for (d, v) in o {
            h[d] = Double(v)
        }
    }

    // MARK: - Init Game

    static func initGame(
        psValues: [(String, Int)],
        paradigms: [String: Paradigm],
        initParadigmID: String,
        allDescriptorIDs: [String]
    ) -> GameState {
        var h = [String: Double]()
        for d in allDescriptorIDs {
            h[d] = 0.5
        }
        var o = [String: Int]()

        for (dID, val) in psValues {
            h[dID] = Double(val)
            o[dID] = val
        }

        let pInit = paradigms[initParadigmID]!
        assimilateFromParadigm(h: &h, o: o, paradigm: pInit)

        return GameState(h: h, o: o, r: [], pCurrent: initParadigmID)
    }

    // MARK: - Init Questions

    static func initQuestions(paradigm: Paradigm, questions: [Question]) -> [Question] {
        var result = [Question]()
        for q in questions {
            let eff = q.effect
            if case let .observation(pairs) = eff {
                for (dID, v) in pairs {
                    if let pred = paradigm.prediction(dID), pred == v {
                        result.append(q)
                        break
                    }
                }
            }
        }
        return result
    }

    // MARK: - Open Questions

    static func openQuestions(state: GameState, questions: [Question]) -> [Question] {
        var result = [Question]()
        for q in questions {
            if state.answered.contains(q.id) { continue }
            let eff = q.effect
            if case let .observation(pairs) = eff {
                for (dID, v) in pairs {
                    let hVal = state.h[dID] ?? 0.5
                    if abs(hVal - Double(v)) < epsilon {
                        result.append(q)
                        break
                    }
                }
            }
        }
        return result
    }

    // MARK: - Check Clear

    static func checkClear(question: Question) -> Bool {
        question.isClear
    }

    // MARK: - Update

    static func update(
        state: inout GameState,
        question: Question,
        paradigms: [String: Paradigm],
        allQuestions: [Question],
        currentOpen: [Question],
        tensionThreshold: Int = defaultTensionThreshold,
        shiftCandidates: [String: [String]]? = nil
    ) -> [Question] {
        // Step 1: Direct update
        let eff = question.effect
        switch eff {
        case let .irrelevant(ids):
            for dID in ids {
                state.r.insert(dID)
            }
        case let .observation(pairs):
            for (dID, v) in pairs {
                state.h[dID] = Double(v)
                state.o[dID] = v
            }
        }

        state.answered.insert(question.id)

        let pCurrent = paradigms[state.pCurrent]!

        // Step 2: Assimilate
        if case let .observation(pairs) = eff {
            for (dID, v) in pairs {
                if let pred = pCurrent.prediction(dID), pred == v {
                    assimilateDescriptor(h: &state.h, dID: dID, paradigm: pCurrent)
                }
            }
            for (d, v) in state.o {
                state.h[d] = Double(v)
            }
        }

        // Step 3: Paradigm shift
        let currentTension = tension(o: state.o, paradigm: pCurrent)
        if currentTension > tensionThreshold {
            let candidates: [String]
            if let sc = shiftCandidates, let c = sc[state.pCurrent] {
                candidates = c
            } else {
                candidates = paradigms.keys.filter { $0 != state.pCurrent }
            }

            let currentAlignment = alignment(h: state.h, paradigm: pCurrent)
            var bestID = state.pCurrent
            var bestScore = currentAlignment
            for pID in candidates {
                guard let p = paradigms[pID] else { continue }
                let score = alignment(h: state.h, paradigm: p)
                if score > bestScore {
                    bestScore = score
                    bestID = pID
                }
            }
            if bestID != state.pCurrent {
                state.pCurrent = bestID
                let pNew = paradigms[bestID]!
                assimilateFromParadigm(h: &state.h, o: state.o, paradigm: pNew)
            }
        }

        // Step 4: Open questions update (add only, exclude answered)
        var remaining = currentOpen.filter { $0.id != question.id }
        let remainingIDs = Set(remaining.map(\.id))
        let newlyOpened = openQuestions(state: state, questions: allQuestions)
            .filter { !remainingIDs.contains($0.id) && !state.answered.contains($0.id) }

        remaining.append(contentsOf: newlyOpened)
        return remaining
    }
}

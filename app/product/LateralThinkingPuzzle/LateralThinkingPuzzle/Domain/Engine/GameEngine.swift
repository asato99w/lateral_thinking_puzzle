import Foundation

enum GameEngine {

    static let epsilon: Double = 0.2

    // MARK: - Conceivable Block

    /// Returns true if any descriptor referenced by the question is outside conceivable.
    static func conceivableBlocked(_ question: Question, conceivable: Set<String>) -> Bool {
        for d in question.allDescriptors {
            if !conceivable.contains(d) {
                return true
            }
        }
        return false
    }

    // MARK: - Tension

    /// Anomaly count: Conceivable(P) ∩ O where P's prediction conflicts with O.
    static func tension(o: [String: Int], paradigm: Paradigm) -> Int {
        var count = 0
        for d in paradigm.conceivable {
            if let oVal = o[d] {
                if let pred = paradigm.prediction(d), pred != oVal {
                    count += 1
                }
            }
        }
        return count
    }

    // MARK: - Alignment

    /// H-based alignment using pPred.
    static func alignment(h: [String: Double], paradigm: Paradigm) -> Double {
        let predItems = paradigm.pPred
        guard !predItems.isEmpty else { return 0.0 }
        var score = 0.0
        var count = 0
        for (d, predVal) in predItems {
            let hVal = h[d] ?? 0.5
            if predVal == 1 {
                score += hVal
            } else {
                score += 1.0 - hVal
            }
            count += 1
        }
        return count > 0 ? score / Double(count) : 0.0
    }

    // MARK: - Explained O

    /// Count of O entries that match P's prediction.
    static func explainedO(o: [String: Int], paradigm: Paradigm) -> Int {
        var count = 0
        for (dID, v) in o {
            if let pred = paradigm.prediction(dID), pred == v {
                count += 1
            }
        }
        return count
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
        for dID in Set(o.keys).intersection(paradigm.conceivable) {
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

    static func initQuestions(
        paradigm: Paradigm,
        questions: [Question],
        o: [String: Int]? = nil
    ) -> [Question] {
        var result = [Question]()
        for q in questions {
            if conceivableBlocked(q, conceivable: paradigm.conceivable) {
                continue
            }
            if let o = o, !q.prerequisites.allSatisfy({ o.keys.contains($0) }) {
                continue
            }
            let eff = q.effect
            if case let .observation(pairs) = eff {
                var hasMatch = false
                var hasConflict = false
                for (dID, v) in pairs {
                    if let pred = paradigm.prediction(dID) {
                        if pred == v {
                            hasMatch = true
                        } else {
                            hasConflict = true
                        }
                    }
                }
                if hasMatch && !hasConflict {
                    result.append(q)
                }
            }
        }
        return result
    }

    // MARK: - Open Questions

    static func openQuestions(
        state: GameState,
        questions: [Question],
        paradigms: [String: Paradigm]? = nil
    ) -> [Question] {
        var conceivable = Set<String>()
        if let paradigms = paradigms, let p = paradigms[state.pCurrent] {
            conceivable = p.conceivable
        }
        var result = [Question]()
        for q in questions {
            if state.answered.contains(q.id) { continue }
            if !conceivable.isEmpty && conceivableBlocked(q, conceivable: conceivable) {
                continue
            }
            if !q.prerequisites.allSatisfy({ state.o.keys.contains($0) }) {
                continue
            }
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

    // MARK: - Build O*

    static func buildOStar(
        questions: [Question],
        psValues: [(String, Int)]
    ) -> [String: Int] {
        var oStar = [String: Int]()
        for (dID, val) in psValues {
            oStar[dID] = val
        }
        for q in questions {
            if q.correctAnswer == .irrelevant { continue }
            let eff = q.effect
            if case let .observation(pairs) = eff {
                for (dID, v) in pairs {
                    oStar[dID] = v
                }
            }
        }
        return oStar
    }

    // MARK: - Compute Thresholds

    static func computeThresholds(
        paradigms: inout [String: Paradigm],
        oStar: [String: Int]
    ) {
        for (pid, p) in paradigms {
            let exclusive = exclusiveConceivableAnomalies(paradigm: p, allParadigms: paradigms, oStar: oStar)

            var minShared: Int?
            for (pid2, p2) in paradigms where pid2 != pid {
                let shared = sharedConceivableAnomalies(paradigm: p, other: p2, oStar: oStar)
                if minShared == nil || shared < minShared! {
                    minShared = shared
                }
            }

            if let minShared = minShared {
                paradigms[pid]!.threshold = exclusive + minShared
            } else {
                paradigms[pid]!.threshold = nil
            }
        }
    }

    /// Exclusive conceivable anomalies: descriptors unique to this paradigm's conceivable that conflict with O*.
    private static func exclusiveConceivableAnomalies(
        paradigm: Paradigm,
        allParadigms: [String: Paradigm],
        oStar: [String: Int]
    ) -> Int {
        var otherConceivable = Set<String>()
        for (pid, p) in allParadigms where pid != paradigm.id {
            otherConceivable.formUnion(p.conceivable)
        }
        let exclusive = paradigm.conceivable.subtracting(otherConceivable)
        var count = 0
        for d in exclusive {
            if let pred = paradigm.prediction(d), let oVal = oStar[d], pred != oVal {
                count += 1
            }
        }
        return count
    }

    /// Shared conceivable anomalies between two paradigms.
    private static func sharedConceivableAnomalies(
        paradigm: Paradigm,
        other: Paradigm,
        oStar: [String: Int]
    ) -> Int {
        let shared = paradigm.conceivable.intersection(other.conceivable)
        var count = 0
        for d in shared {
            if let pred = paradigm.prediction(d), let oVal = oStar[d], pred != oVal {
                count += 1
            }
        }
        return count
    }

    // MARK: - Compute Depths

    static func computeDepths(
        paradigms: inout [String: Paradigm],
        oStar: [String: Int]
    ) {
        // Compute Explained(P) for each paradigm
        var explained = [String: Set<String>]()
        for (pid, p) in paradigms {
            var exp = Set<String>()
            for (d, predVal) in p.pPred {
                if let oVal = oStar[d], predVal == oVal {
                    exp.insert(d)
                }
            }
            explained[pid] = exp
        }

        let pids = Array(paradigms.keys)

        // Build containment DAG: a → b means Explained(a) ⊂ Explained(b)
        var strictlyContained = [String: Set<String>]()
        for pid in pids { strictlyContained[pid] = [] }

        for a in pids {
            for b in pids where a != b {
                if explained[a]!.isStrictSubset(of: explained[b]!) {
                    strictlyContained[a]!.insert(b)
                }
            }
        }

        // Topological sort for depth assignment
        var depthMap = [String: Int]()

        func computeDepth(_ pid: String, _ visited: inout Set<String>) -> Int {
            if let cached = depthMap[pid] { return cached }
            if visited.contains(pid) { return 0 }
            visited.insert(pid)

            let parents = pids.filter { strictlyContained[$0]!.contains(pid) }
            if parents.isEmpty {
                depthMap[pid] = 0
            } else {
                let maxParentDepth = parents.map { computeDepth($0, &visited) }.max()!
                depthMap[pid] = maxParentDepth + 1
            }
            return depthMap[pid]!
        }

        for pid in pids {
            var visited = Set<String>()
            _ = computeDepth(pid, &visited)
        }

        for (pid, _) in paradigms {
            paradigms[pid]!.depth = depthMap[pid] ?? 0
        }
    }

    // MARK: - Update

    static func update(
        state: inout GameState,
        question: Question,
        paradigms: [String: Paradigm],
        allQuestions: [Question],
        currentOpen: [Question]
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
        if let threshold = pCurrent.threshold, currentTension > threshold {
            let currentExplained = explainedO(o: state.o, paradigm: pCurrent)
            let candidates = paradigms.keys.filter { pID in
                pID != state.pCurrent
                    && explainedO(o: state.o, paradigm: paradigms[pID]!) > currentExplained
            }

            if !candidates.isEmpty {
                var bestID = candidates[0]
                var bestScore = alignment(h: state.h, paradigm: paradigms[candidates[0]]!)
                for pID in candidates.dropFirst() {
                    let score = alignment(h: state.h, paradigm: paradigms[pID]!)
                    if score > bestScore {
                        bestScore = score
                        bestID = pID
                    }
                }
                state.pCurrent = bestID
                let pNew = paradigms[bestID]!
                assimilateFromParadigm(h: &state.h, o: state.o, paradigm: pNew)
            }
        }

        // Step 4: Open questions update
        var remaining = currentOpen.filter { $0.id != question.id }
        let remainingIDs = Set(remaining.map(\.id))
        let newlyOpened = openQuestions(state: state, questions: allQuestions, paradigms: paradigms)
            .filter { !remainingIDs.contains($0.id) && !state.answered.contains($0.id) }

        remaining.append(contentsOf: newlyOpened)
        return remaining
    }
}

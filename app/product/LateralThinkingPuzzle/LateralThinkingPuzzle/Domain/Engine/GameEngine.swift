import Foundation

enum GameEngine {

    // MARK: - Tension

    /// Anomaly count: pPred(P) ∩ O where P's prediction conflicts with O.
    static func tension(o: [String: Int], paradigm: Paradigm) -> Int {
        var count = 0
        for (d, pred) in paradigm.pPred {
            if let oVal = o[d], pred != oVal {
                count += 1
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
        for dID in Set(o.keys).intersection(Set(paradigm.pPred.keys)) {
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

    // MARK: - Init Questions (data-driven)

    static func initQuestions(
        questions: [Question],
        initQuestionIDs: [String]
    ) -> [Question] {
        let idSet = Set(initQuestionIDs)
        return questions.filter { idSet.contains($0.id) }
    }

    // MARK: - Reachable (BFS via R(P))

    /// R(P) で origins から到達可能な記述素を返す（多ホップ BFS）。
    static func reachable(origins: Set<String>, paradigm: Paradigm) -> Set<String> {
        var result = Set<String>()
        var frontier = Array(origins)
        var visited = Set<String>()
        while !frontier.isEmpty {
            let current = frontier.removeFirst()
            if visited.contains(current) { continue }
            visited.insert(current)
            for rel in paradigm.relations {
                if rel.src == current && !visited.contains(rel.tgt) {
                    result.insert(rel.tgt)
                    frontier.append(rel.tgt)
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
        guard let paradigms = paradigms, let p = paradigms[state.pCurrent] else {
            return []
        }

        // Consistent(O, P) と Anomaly(O, P)
        var consistent = Set<String>()
        var anomaly = Set<String>()
        for (d, v) in state.o {
            if let pred = p.prediction(d) {
                if pred == v { consistent.insert(d) }
                else { anomaly.insert(d) }
            }
        }

        let consistentReach = reachable(origins: consistent, paradigm: p)
        let anomalyReach = reachable(origins: anomaly, paradigm: p)

        var result = [Question]()
        for q in questions {
            if state.answered.contains(q.id) { continue }
            if !q.paradigms.isEmpty && !q.paradigms.contains(state.pCurrent) { continue }
            if !q.prerequisites.allSatisfy({ state.o.keys.contains($0) }) { continue }
            let eff = q.effect
            if case let .observation(pairs) = eff {
                for (dID, v) in pairs {
                    // 3a: 一致からの探索
                    if consistentReach.contains(dID) && p.prediction(dID) == v {
                        result.append(q)
                        break
                    }
                    // 3b: 違和感からの探索
                    if anomalyReach.contains(dID) {
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

    // MARK: - Compute Neighborhoods

    /// O* ベースの射影で各パラダイムの近傍集合を計算する。
    static func computeNeighborhoods(
        paradigms: inout [String: Paradigm],
        oStar: [String: Int]
    ) {
        let pids = Array(paradigms.keys)

        var anomalySets = [String: Set<String>]()
        var tensions = [String: Int]()
        for pid in pids {
            let p = paradigms[pid]!
            var anom = Set<String>()
            for (d, pred) in p.pPred {
                if let oVal = oStar[d], pred != oVal {
                    anom.insert(d)
                }
            }
            anomalySets[pid] = anom
            tensions[pid] = anom.count
        }

        for pidCur in pids {
            let anomCur = anomalySets[pidCur]!
            guard !anomCur.isEmpty else {
                paradigms[pidCur]!.neighbors = []
                continue
            }

            // 候補: tension strict < かつ Remaining が真部分集合
            var remainingMap = [String: Set<String>]()
            for pidCand in pids where pidCand != pidCur {
                guard tensions[pidCand]! < tensions[pidCur]! else { continue }
                let remaining = anomCur.intersection(anomalySets[pidCand]!)
                if remaining.isStrictSubset(of: anomCur) {
                    remainingMap[pidCand] = remaining
                }
            }

            // Hasse 図: 極大 Remaining のみ（中間がないもの）
            var neighbors = Set<String>()
            let candPids = Array(remainingMap.keys)
            for (i, pidA) in candPids.enumerated() {
                let remA = remainingMap[pidA]!
                var isCovered = false
                for (j, pidB) in candPids.enumerated() where i != j {
                    let remB = remainingMap[pidB]!
                    if remA.isStrictSubset(of: remB) {
                        isCovered = true
                        break
                    }
                }
                if !isCovered {
                    neighbors.insert(pidA)
                }
            }
            paradigms[pidCur]!.neighbors = neighbors
        }
    }

    // MARK: - Compute Shift Thresholds

    /// 各パラダイムの shiftThreshold N(P_target) を計算する。
    static func computeShiftThresholds(
        paradigms: inout [String: Paradigm],
        oStar: [String: Int]
    ) {
        for (pidTarget, _) in paradigms {
            var minResolve: Int?
            for (pidSource, pSource) in paradigms where pidSource != pidTarget {
                guard pSource.neighbors.contains(pidTarget) else { continue }
                let res = resolve(oStar: oStar, pSource: pSource, pTarget: paradigms[pidTarget]!)
                if minResolve == nil || res < minResolve! {
                    minResolve = res
                }
            }
            paradigms[pidTarget]!.shiftThreshold = minResolve
        }
    }

    /// P_source のアノマリーのうち P_target が正しく予測する数。
    private static func resolve(
        oStar: [String: Int],
        pSource: Paradigm,
        pTarget: Paradigm
    ) -> Int {
        var count = 0
        for (d, predSrc) in pSource.pPred {
            guard let oVal = oStar[d], predSrc != oVal else { continue }
            if let predTgt = pTarget.prediction(d), predTgt == oVal {
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

        var strictlyContained = [String: Set<String>]()
        for pid in pids { strictlyContained[pid] = [] }

        for a in pids {
            for b in pids where a != b {
                if explained[a]!.isStrictSubset(of: explained[b]!) {
                    strictlyContained[a]!.insert(b)
                }
            }
        }

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

    // MARK: - Select Shift Target

    /// 近傍 + resolve 閾値に基づくシフト先選択。
    ///
    /// 3条件全てを満たす候補のみ:
    ///   1. 近傍: pid ∈ pCurrent.neighbors
    ///   2. tension strict <: tension(O, P') < tension(O, P_current)
    ///   3. resolve >= N: P' の shiftThreshold 以上の resolve
    ///
    /// 選択: resolve DESC → attention DESC → pid ASC
    static func selectShiftTarget(
        o: [String: Int],
        pCurrent: Paradigm,
        paradigms: [String: Paradigm]
    ) -> String? {
        let anomalies = Set(
            pCurrent.pPred.filter { d, pred in
                if let oVal = o[d] { return pred != oVal }
                return false
            }.keys
        )
        let curTension = tension(o: o, paradigm: pCurrent)

        struct Candidate {
            let pid: String
            let tension: Int
            let attention: Int
            let resolve: Int
        }
        var candidates = [Candidate]()

        for (pid, p) in paradigms {
            if pid == pCurrent.id { continue }
            guard pCurrent.neighbors.contains(pid) else { continue }
            let t = tension(o: o, paradigm: p)
            guard t < curTension else { continue }
            let res = anomalies.filter { d in
                if let pred = p.prediction(d), let oVal = o[d] { return pred == oVal }
                return false
            }.count
            if let threshold = p.shiftThreshold, res < threshold { continue }
            let att = anomalies.filter { p.pPred[$0] != nil }.count
            candidates.append(Candidate(pid: pid, tension: t, attention: att, resolve: res))
        }

        guard !candidates.isEmpty else { return nil }
        candidates.sort { a, b in
            if a.resolve != b.resolve { return a.resolve > b.resolve }
            if a.attention != b.attention { return a.attention > b.attention }
            return a.pid < b.pid
        }
        return candidates[0].pid
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

        // Step 3: Paradigm shift (neighbors + resolve threshold)
        if let bestID = selectShiftTarget(o: state.o, pCurrent: pCurrent, paradigms: paradigms) {
            state.pCurrent = bestID
            let pNew = paradigms[bestID]!
            assimilateFromParadigm(h: &state.h, o: state.o, paradigm: pNew)
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

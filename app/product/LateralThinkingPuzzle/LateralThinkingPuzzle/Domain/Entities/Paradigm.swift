struct Paradigm: Equatable, Sendable {

    let id: String
    let name: String
    let pPred: [String: Int]       // {d_id: 0|1}, unknown = key absent
    let relations: [Relation]
    var neighbors: Set<String> = []         // 近傍パラダイム集合（静的計算）
    var shiftThreshold: Int?                // resolve 閾値 N(P)（自動計算）
    var depth: Int?

    init(
        id: String,
        name: String,
        pPred: [String: Int],
        relations: [Relation]
    ) {
        self.id = id
        self.name = name
        self.pPred = pPred
        self.relations = relations
    }

    func prediction(_ dID: String) -> Int? {
        pPred[dID]
    }
}

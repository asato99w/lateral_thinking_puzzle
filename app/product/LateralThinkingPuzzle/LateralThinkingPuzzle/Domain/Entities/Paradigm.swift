struct Paradigm: Equatable, Sendable {

    enum ValidationError: Error, Equatable {
        case conceivableNotSubsetOfPPred(ids: [String])
        case relationRefNotInConceivable(paradigmID: String, ref: String)
    }

    let id: String
    let name: String
    let pPred: [String: Int]       // {d_id: 0|1}, unknown = key absent
    let conceivable: Set<String>   // conceivable set
    let relations: [Relation]
    var threshold: Int?
    var depth: Int?

    init(
        id: String,
        name: String,
        pPred: [String: Int],
        conceivable: Set<String>,
        relations: [Relation]
    ) throws {
        self.id = id
        self.name = name
        self.pPred = pPred
        self.conceivable = conceivable
        self.relations = relations
        try validate()
    }

    func prediction(_ dID: String) -> Int? {
        pPred[dID]
    }

    // MARK: - Validation

    private func validate() throws {
        let predKeys = Set(pPred.keys)
        if !conceivable.isSubset(of: predKeys) {
            let invalid = conceivable.subtracting(predKeys).sorted()
            throw ValidationError.conceivableNotSubsetOfPPred(ids: invalid)
        }
        for rel in relations {
            if !conceivable.contains(rel.src) {
                throw ValidationError.relationRefNotInConceivable(paradigmID: id, ref: rel.src)
            }
            if !conceivable.contains(rel.tgt) {
                throw ValidationError.relationRefNotInConceivable(paradigmID: id, ref: rel.tgt)
            }
        }
    }
}

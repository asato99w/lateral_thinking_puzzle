struct Paradigm: Equatable, Sendable {

    enum ValidationError: Error, Equatable {
        case dPlusDMinusOverlap(ids: [String])
        case relationRefNotInD(paradigmID: String, ref: String)
    }

    let id: String
    let name: String
    let dPlus: Set<String>
    let dMinus: Set<String>
    let relations: [Relation]

    var dAll: Set<String> { dPlus.union(dMinus) }

    init(id: String, name: String, dPlus: Set<String>, dMinus: Set<String>, relations: [Relation]) throws {
        self.id = id
        self.name = name
        self.dPlus = dPlus
        self.dMinus = dMinus
        self.relations = relations
        try validate()
    }

    func prediction(_ dID: String) -> Int? {
        if dPlus.contains(dID) { return 1 }
        if dMinus.contains(dID) { return 0 }
        return nil
    }

    // MARK: - Validation

    private func validate() throws {
        let overlap = dPlus.intersection(dMinus)
        if !overlap.isEmpty {
            throw ValidationError.dPlusDMinusOverlap(ids: overlap.sorted())
        }
        let dAll = self.dAll
        for rel in relations {
            if !dAll.contains(rel.src) {
                throw ValidationError.relationRefNotInD(paradigmID: id, ref: rel.src)
            }
            if !dAll.contains(rel.tgt) {
                throw ValidationError.relationRefNotInD(paradigmID: id, ref: rel.tgt)
            }
        }
    }
}

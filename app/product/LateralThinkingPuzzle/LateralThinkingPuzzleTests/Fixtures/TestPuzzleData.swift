@testable import LateralThinkingPuzzle

enum TestPuzzleData {

    // MARK: - Minimal Paradigms

    static func makeParadigm(
        id: String = "P1",
        name: String = "Test Paradigm",
        pPred: [String: Int] = ["d1": 1, "d2": 1, "d3": 0, "d4": 0],
        conceivable: Set<String> = ["d1", "d2", "d3", "d4"],
        relations: [Relation] = []
    ) -> Paradigm {
        try! Paradigm(id: id, name: name, pPred: pPred, conceivable: conceivable, relations: relations)
    }

    static func makeQuestion(
        id: String = "q1",
        text: String = "Test question?",
        ansYes: [(String, Int)] = [("d1", 1)],
        ansNo: [(String, Int)] = [("d1", 0)],
        ansIrrelevant: [String] = ["d1"],
        correctAnswer: Answer = .yes,
        isClear: Bool = false,
        prerequisites: [String] = [],
        relatedDescriptors: [String] = []
    ) -> Question {
        Question(
            id: id,
            text: text,
            ansYes: ansYes,
            ansNo: ansNo,
            ansIrrelevant: ansIrrelevant,
            correctAnswer: correctAnswer,
            isClear: isClear,
            prerequisites: prerequisites,
            relatedDescriptors: relatedDescriptors
        )
    }

    // MARK: - Minimal Puzzle for Engine Tests

    static func makeMinimalPuzzle() -> (
        paradigms: [String: Paradigm],
        questions: [Question],
        allDescriptorIDs: [String],
        psValues: [(String, Int)]
    ) {
        let p1 = makeParadigm(
            id: "P1", name: "Initial",
            pPred: ["d1": 1, "d2": 1, "d3": 0],
            conceivable: ["d1", "d2", "d3"],
            relations: [Relation(src: "d1", tgt: "d2", weight: 0.8)]
        )
        let p2 = makeParadigm(
            id: "P2", name: "Alternative",
            pPred: ["d1": 0, "d2": 0, "d3": 1],
            conceivable: ["d1", "d2", "d3"],
            relations: []
        )

        let questions = [
            makeQuestion(id: "q1", ansYes: [("d1", 1)], ansNo: [("d1", 0)], ansIrrelevant: ["d1"], correctAnswer: .yes),
            makeQuestion(id: "q2", ansYes: [("d3", 1)], ansNo: [("d3", 0)], ansIrrelevant: ["d3"], correctAnswer: .yes),
            makeQuestion(id: "q3", ansYes: [("d2", 1)], ansNo: [("d2", 0)], ansIrrelevant: ["d2"], correctAnswer: .no, isClear: true),
        ]

        return (
            paradigms: ["P1": p1, "P2": p2],
            questions: questions,
            allDescriptorIDs: ["d1", "d2", "d3", "ps1"],
            psValues: [("ps1", 1)]
        )
    }
}

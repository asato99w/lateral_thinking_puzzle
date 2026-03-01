import Testing
import Foundation
@testable import LateralThinkingPuzzle

struct PuzzleDataDTOTests {

    private func loadPuzzleJSON(name: String) throws -> Data {
        // Try app bundle with subdirectory (folder reference preserves ja/ structure)
        if let url = Bundle.main.url(forResource: name, withExtension: "json", subdirectory: "Puzzles/ja") {
            return try Data(contentsOf: url)
        }
        // Fallback: test bundle
        if let url = Bundle(for: BundleMarker.self).url(forResource: name, withExtension: "json", subdirectory: "Puzzles/ja") {
            return try Data(contentsOf: url)
        }
        Issue.record("JSON file \(name).json not found in bundle")
        throw PuzzleRepositoryError.puzzleNotFound(id: name)
    }

    @Test func test_decodeBarManJSON_succeeds() throws {
        let data = try loadPuzzleJSON(name: "bar_man")
        let dto = try JSONDecoder().decode(PuzzleDataDTO.self, from: data)

        #expect(dto.title == "バーの男")
        #expect(dto.initParadigm == "P1")
        #expect(dto.paradigms.count == 5)
        #expect(dto.questions.count == 21)
    }

    @Test func test_decodeDesertManJSON_succeeds() throws {
        let data = try loadPuzzleJSON(name: "desert_man")
        let dto = try JSONDecoder().decode(PuzzleDataDTO.self, from: data)

        #expect(dto.title == "砂漠の男")
        #expect(dto.initParadigm == "P1")
        #expect(dto.paradigms.count == 6)
        #expect(dto.questions.count == 26)
    }

    @Test func test_barManToDomain_succeeds() throws {
        let data = try loadPuzzleJSON(name: "bar_man")
        let dto = try JSONDecoder().decode(PuzzleDataDTO.self, from: data)
        let puzzle = try dto.toDomain()

        #expect(puzzle.title == "バーの男")
        #expect(puzzle.paradigms.count == 5)
        #expect(puzzle.questions.count == 21)
    }

    @Test func test_desertManToDomain_succeeds() throws {
        let data = try loadPuzzleJSON(name: "desert_man")
        let dto = try JSONDecoder().decode(PuzzleDataDTO.self, from: data)
        let puzzle = try dto.toDomain()

        #expect(puzzle.title == "砂漠の男")
        #expect(puzzle.paradigms.count == 6)
        #expect(puzzle.questions.count == 26)
    }

    @Test func test_allBundledPuzzles_toDomain_succeeds() throws {
        let names = ["bar_man", "desert_man", "turtle_soup", "poisonous_mushroom", "underground"]
        for name in names {
            let data = try loadPuzzleJSON(name: name)
            let dto = try JSONDecoder().decode(PuzzleDataDTO.self, from: data)
            let puzzle = try dto.toDomain()
            #expect(!puzzle.title.isEmpty, "Puzzle \(name) has empty title")
            #expect(!puzzle.paradigms.isEmpty, "Puzzle \(name) has no paradigms")
            #expect(!puzzle.questions.isEmpty, "Puzzle \(name) has no questions")
        }
    }

    @Test func test_allBundledPuzzles_fullGameFlow() throws {
        let names = ["bar_man", "desert_man", "turtle_soup", "poisonous_mushroom", "underground"]
        for name in names {
            let data = try loadPuzzleJSON(name: name)
            let dto = try JSONDecoder().decode(PuzzleDataDTO.self, from: data)
            let puzzle = try dto.toDomain()

            // Simulate StartGameUseCase
            let startGame = StartGameUseCase()
            let result = startGame.execute(puzzle: puzzle)

            #expect(!result.state.pCurrent.isEmpty, "Puzzle \(name): pCurrent should be set")

            // Simulate answering each open question
            let answerUseCase = AnswerQuestionUseCase()
            var state = result.state
            var openQs = result.openQuestions

            // Answer up to 5 questions to verify no crash
            var answeredCount = 0
            while answeredCount < 5 && !openQs.isEmpty {
                let q = openQs[0]
                let ansResult = answerUseCase.execute(
                    state: &state,
                    question: q,
                    puzzle: puzzle,
                    currentOpen: openQs
                )
                state = ansResult.state
                openQs = ansResult.openQuestions
                answeredCount += 1
            }
        }
    }

    @Test func test_dtoToDomain_succeeds() throws {
        let json = """
        {
          "title": "テスト",
          "statement": "テスト問題",
          "init_paradigm": "P1",
          "ps_values": [["ps1", 1]],
          "all_descriptor_ids": ["d1", "d2", "ps1"],
          "paradigms": [{
            "id": "P1", "name": "テスト",
            "p_pred": [["d1", 1], ["d2", 0]],
            "conceivable": ["d1", "d2"],
            "relations": [["d1", "d2", 0.8]]
          }],
          "questions": [{
            "id": "q1", "text": "テスト？",
            "ans_yes": [["d1", 1]], "ans_no": [["d1", 0]],
            "ans_irrelevant": ["d1"],
            "correct_answer": "yes"
          }]
        }
        """.data(using: .utf8)!

        let dto = try JSONDecoder().decode(PuzzleDataDTO.self, from: json)
        let puzzle = try dto.toDomain()

        #expect(puzzle.title == "テスト")
        #expect(puzzle.paradigms["P1"] != nil)
        #expect(puzzle.paradigms["P1"]!.pPred["d1"] == 1)
        #expect(puzzle.paradigms["P1"]!.pPred["d2"] == 0)
        #expect(puzzle.questions.count == 1)
        #expect(puzzle.questions[0].correctAnswer == .yes)
        // conceivable is now optional in DTO - should decode without error
    }
}

// Marker class for bundle lookup in test target
private class BundleMarker {}

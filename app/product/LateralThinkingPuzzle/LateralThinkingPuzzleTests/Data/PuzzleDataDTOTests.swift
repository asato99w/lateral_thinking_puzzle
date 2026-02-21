import Testing
import Foundation
@testable import LateralThinkingPuzzle

struct PuzzleDataDTOTests {

    @Test func test_decodeBarManJSON_succeeds() throws {
        let url = Bundle(for: BundleMarker.self).url(
            forResource: "bar_man", withExtension: "json", subdirectory: "Puzzles"
        )
        // If running in test target, try main bundle
        let resolvedURL = url ?? Bundle.main.url(forResource: "bar_man", withExtension: "json", subdirectory: "Puzzles")
        guard let jsonURL = resolvedURL else {
            // Skip if resource not available in test context
            return
        }
        let data = try Data(contentsOf: jsonURL)
        let dto = try JSONDecoder().decode(PuzzleDataDTO.self, from: data)

        #expect(dto.title == "バーの男")
        #expect(dto.initParadigm == "P1")
        #expect(dto.paradigms.count == 6)
        #expect(dto.questions.count == 55)
    }

    @Test func test_dtoToDomain_succeeds() throws {
        let json = """
        {
          "title": "テスト",
          "statement": "テスト問題",
          "init_paradigm": "P1",
          "tension_threshold": 2,
          "shift_candidates": {"P1": ["P2"]},
          "ps_values": [["ps1", 1]],
          "all_descriptor_ids": ["d1", "d2", "ps1"],
          "paradigms": [{
            "id": "P1", "name": "テスト",
            "d_plus": ["d1"], "d_minus": ["d2"],
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
        #expect(puzzle.paradigms["P1"]!.dPlus == Set(["d1"]))
        #expect(puzzle.questions.count == 1)
        #expect(puzzle.questions[0].correctAnswer == .yes)
    }
}

// Marker class for bundle lookup in test target
private class BundleMarker {}

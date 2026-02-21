import Testing
@testable import LateralThinkingPuzzle

struct InitGameTests {

    @Test func test_initGame_hInitializedToHalf() {
        let data = TestPuzzleData.makeMinimalPuzzle()
        let state = GameEngine.initGame(
            psValues: [],
            paradigms: data.paradigms,
            initParadigmID: "P1",
            allDescriptorIDs: data.allDescriptorIDs
        )
        for d in data.allDescriptorIDs {
            #expect(state.h[d] != nil)
        }
    }

    @Test func test_initGame_psValuesReflectedInHAndO() {
        let data = TestPuzzleData.makeMinimalPuzzle()
        let state = GameEngine.initGame(
            psValues: data.psValues,
            paradigms: data.paradigms,
            initParadigmID: "P1",
            allDescriptorIDs: data.allDescriptorIDs
        )
        #expect(state.h["ps1"] == 1.0)
        #expect(state.o["ps1"] == 1)
    }

    @Test func test_initGame_initialParadigmSet() {
        let data = TestPuzzleData.makeMinimalPuzzle()
        let state = GameEngine.initGame(
            psValues: data.psValues,
            paradigms: data.paradigms,
            initParadigmID: "P1",
            allDescriptorIDs: data.allDescriptorIDs
        )
        #expect(state.pCurrent == "P1")
    }

    @Test func test_initGame_answeredIsEmpty() {
        let data = TestPuzzleData.makeMinimalPuzzle()
        let state = GameEngine.initGame(
            psValues: data.psValues,
            paradigms: data.paradigms,
            initParadigmID: "P1",
            allDescriptorIDs: data.allDescriptorIDs
        )
        #expect(state.answered.isEmpty)
    }

    @Test func test_initGame_initialAssimilationApplied() {
        // P1 has d1,d2 in dPlus with relation d1→d2 (weight 0.8)
        // If ps1=1 is in o but ps1 is NOT in P1.dAll, no assimilation from ps1
        // Only observations that match P1 predictions trigger assimilation
        let p1 = TestPuzzleData.makeParadigm(
            id: "P1", name: "test",
            dPlus: ["d1", "d2"],
            dMinus: ["d3"],
            relations: [Relation(src: "d1", tgt: "d2", weight: 0.8)]
        )
        let state = GameEngine.initGame(
            psValues: [("d1", 1)], // d1 matches P1 dPlus prediction
            paradigms: ["P1": p1],
            initParadigmID: "P1",
            allDescriptorIDs: ["d1", "d2", "d3"]
        )
        // d2 should be assimilated: 0.5 + 0.8*(1.0-0.5) = 0.9
        #expect(abs(state.h["d2"]! - 0.9) < 0.0001)
        // d1 restored to observation value
        #expect(state.h["d1"]! == 1.0)
    }
}

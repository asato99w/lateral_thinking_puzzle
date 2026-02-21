struct GameState: Equatable, Sendable {
    var h: [String: Double]
    var o: [String: Int]
    var r: Set<String>
    var pCurrent: String
    var answered: Set<String>

    init(h: [String: Double], o: [String: Int], r: Set<String>, pCurrent: String, answered: Set<String> = []) {
        self.h = h
        self.o = o
        self.r = r
        self.pCurrent = pCurrent
        self.answered = answered
    }
}

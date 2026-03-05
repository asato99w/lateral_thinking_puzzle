import Foundation

enum PuzzleMetadata {
    static func icon(for id: String) -> String {
        icons[id] ?? "❓"
    }

    static func difficulty(for id: String) -> Int {
        difficulties[id] ?? 1
    }

    private static let icons: [String: String] = [
        "bar_man": "\u{1F378}",      // 🍸
        "desert_man": "\u{1F3DC}",   // 🏜️
        "turtle_soup": "\u{1F422}", // 🐢
        "forbidden_basement": "\u{1F6AA}", // 🚪
    ]

    private static let difficulties: [String: Int] = [
        "bar_man": 2,
        "desert_man": 3,
        "turtle_soup": 1,
        "forbidden_basement": 2,
    ]
}

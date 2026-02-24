import SwiftUI

@main
struct LateralThinkingPuzzleApp: App {
    var body: some Scene {
        WindowGroup {
            PuzzleListView()
                .preferredColorScheme(.dark)
        }
    }
}

import Foundation
import Observation

@MainActor @Observable
final class DebugSettings {
    static let shared = DebugSettings()

    var languageOverride: String? {
        didSet { UserDefaults.standard.set(languageOverride, forKey: "debug_languageOverride") }
    }

    private init() {
        languageOverride = UserDefaults.standard.string(forKey: "debug_languageOverride")
    }
}

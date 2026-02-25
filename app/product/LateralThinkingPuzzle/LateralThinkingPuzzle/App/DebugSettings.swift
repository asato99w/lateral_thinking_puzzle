import Foundation
import Observation

@MainActor @Observable
final class DebugSettings {
    static let shared = DebugSettings()

    var languageOverride: String? {
        didSet { UserDefaults.standard.set(languageOverride, forKey: "debug_languageOverride") }
    }

    var useMockDownloads: Bool {
        didSet { UserDefaults.standard.set(useMockDownloads, forKey: "debug_useMockDownloads") }
    }

    static var isMockDownloadsEnabled: Bool {
        ProcessInfo.processInfo.arguments.contains("--mock-downloads")
            || shared.useMockDownloads
    }

    private init() {
        languageOverride = UserDefaults.standard.string(forKey: "debug_languageOverride")
        useMockDownloads = UserDefaults.standard.bool(forKey: "debug_useMockDownloads")
    }
}

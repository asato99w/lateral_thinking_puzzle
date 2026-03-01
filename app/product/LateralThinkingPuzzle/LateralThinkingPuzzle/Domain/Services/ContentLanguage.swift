import Foundation

@MainActor
enum ContentLanguage {
    static let supportedLanguages = ["ja", "en"]
    static let fallback = "en"

    static var current: String {
        if let override = DebugSettings.shared.languageOverride {
            return override
        }
        // Use preferredLanguages (respects -AppleLanguages launch arg)
        for preferred in Locale.preferredLanguages {
            let lang = Locale(identifier: preferred).language.languageCode?.identifier ?? ""
            if supportedLanguages.contains(lang) {
                return lang
            }
        }
        return fallback
    }
}

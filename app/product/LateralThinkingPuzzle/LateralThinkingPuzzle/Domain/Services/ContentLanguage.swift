import Foundation

@MainActor
enum ContentLanguage {
    static let supportedLanguages = ["ja", "en"]
    static let fallback = "en"

    static var current: String {
        if let override = DebugSettings.shared.languageOverride {
            return override
        }
        let systemLang = Locale.current.language.languageCode?.identifier ?? fallback
        return supportedLanguages.contains(systemLang) ? systemLang : fallback
    }
}

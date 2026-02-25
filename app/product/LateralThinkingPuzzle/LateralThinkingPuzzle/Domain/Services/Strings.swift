import Foundation

@MainActor
enum Strings {
    static var appTitle: String { "LiteralQ" }
    static var appSubtitle: String { "Think Beyond Assumptions." }
    static var problemsSection: String { s("問題", "Problems") }
    static var loading: String { s("読み込み中...", "Loading...") }
    static var error: String { s("エラー", "Error") }
    static var retry: String { s("再試行", "Retry") }
    static var statement: String { s("出題", "Statement") }
    static var chooseQuestion: String { s("質問を選んでください", "Choose a question") }
    static var answered: String { s("回答済み", "Answered") }
    static var cleared: String { s("クリア!", "Cleared!") }
    static var backToList: String { s("パズル一覧に戻る", "Back to puzzles") }
    static var answerYes: String { "YES" }
    static var answerNo: String { "NO" }
    static var answerIrrelevant: String { s("関係ない", "Irrelevant") }
    static var allCategories: String { s("すべて", "All") }
    static var solved: String { s("クリア済み", "Solved") }
    static var difficulty: String { s("難易度:", "Difficulty:") }
    static var contentDownload: String { s("コンテンツ", "Content") }
    static var packs: String { s("パック", "Packs") }
    static var puzzles: String { s("パズル", "Puzzles") }
    static var bundled: String { s("同梱済み", "Bundled") }
    static var downloadComplete: String { s("ダウンロード済み", "Downloaded") }
    static var downloading: String { s("ダウンロード中…", "Downloading…") }
    static var deleteContent: String { s("削除", "Delete") }
    static var notDownloaded: String { s("未ダウンロード", "Not Downloaded") }
    static var free: String { s("無料", "Free") }
    static var download: String { s("ダウンロード", "Download") }

    static func showOthers(_ count: Int) -> String {
        s("他 \(count) 件を表示", "Show \(count) more")
    }
    static var hideOthers: String { s("閉じる", "Hide") }
    static var history: String { s("履歴", "History") }

    static func solvedProgress(_ solved: Int, _ total: Int) -> String {
        "\(solved)/\(total) Solved"
    }

    static func errorDetail(_ message: String) -> String {
        s("エラー: \(message)", "Error: \(message)")
    }

    private static func s(_ ja: String, _ en: String) -> String {
        ContentLanguage.current == "ja" ? ja : en
    }
}

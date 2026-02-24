import Foundation

@MainActor
enum Strings {
    static var appTitle: String { s("水平思考パズル", "Lateral Thinking Puzzle") }
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

    static func errorDetail(_ message: String) -> String {
        s("エラー: \(message)", "Error: \(message)")
    }

    private static func s(_ ja: String, _ en: String) -> String {
        ContentLanguage.current == "ja" ? ja : en
    }
}

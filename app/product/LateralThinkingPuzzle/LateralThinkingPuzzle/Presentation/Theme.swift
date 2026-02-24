import SwiftUI

enum Theme {
    // MARK: - Accent

    static let accent = Color.indigo

    // MARK: - Answer Colors

    static let answerYes = Color.green
    static let answerNo = Color.red
    static let answerIrrelevant = Color.gray

    // MARK: - Card (Dark)

    static let cardBackground = Color(white: 0.14)
    static let cardBorder = Color.indigo.opacity(0.4)
    static let starFilled = Color.yellow
    static let starEmpty = Color.gray.opacity(0.4)
    static let solvedBadge = Color.green
    static let progressText = Color.white.opacity(0.7)

    // MARK: - Dimensions

    static let accentBarWidth: CGFloat = 3
    static let cardCornerRadius: CGFloat = 14
    static let sectionBarHeight: CGFloat = 20
    static let feedbackDuration: TimeInterval = 0.6
    static let transitionDuration: TimeInterval = 0.4
    static let animationDuration: TimeInterval = 0.3
}

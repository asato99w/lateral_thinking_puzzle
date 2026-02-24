import SwiftUI

enum Theme {
    // MARK: - Accent

    static let accent = Color.indigo

    // MARK: - Answer Colors

    static let answerYes = Color.green
    static let answerNo = Color.red
    static let answerIrrelevant = Color.gray

    // MARK: - Dimensions

    static let accentBarWidth: CGFloat = 3
    static let cardCornerRadius: CGFloat = 10
    static let feedbackDuration: TimeInterval = 0.6
    static let transitionDuration: TimeInterval = 0.4
    static let animationDuration: TimeInterval = 0.3
}

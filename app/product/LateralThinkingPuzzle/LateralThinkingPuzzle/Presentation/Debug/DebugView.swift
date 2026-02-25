#if DEBUG
import SwiftUI

struct DebugView: View {
    @Bindable private var settings = DebugSettings.shared
    @Environment(\.dismiss) private var dismiss

    private var languageBinding: Binding<String> {
        Binding(
            get: { settings.languageOverride ?? "auto" },
            set: { settings.languageOverride = $0 == "auto" ? nil : $0 }
        )
    }

    var body: some View {
        NavigationStack {
            List {
                Section("Content Language") {
                    Picker("Language", selection: languageBinding) {
                        Text("Auto (System)").tag("auto")
                        Text("Japanese (ja)").tag("ja")
                        Text("English (en)").tag("en")
                    }
                    .pickerStyle(.inline)

                    Text("Current: \(ContentLanguage.current)")
                        .font(.caption)
                        .foregroundStyle(.secondary)
                }

                Section("Downloads") {
                    Toggle("Mock Downloads", isOn: $settings.useMockDownloads)
                    Text("Simulates download/delete without ODR.")
                        .font(.caption)
                        .foregroundStyle(.secondary)
                }

                Section("Solved Puzzles") {
                    Button("Reset Solved Puzzles", role: .destructive) {
                        SolvedPuzzleStore.shared.reset()
                    }
                }
            }
            .navigationTitle("Debug Settings")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .confirmationAction) {
                    Button("Done") { dismiss() }
                }
            }
        }
    }
}
#endif

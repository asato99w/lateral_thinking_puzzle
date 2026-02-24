import Foundation

// MARK: - Resource Provider Protocol (ODR / future AHBA abstraction)

protocol ResourceProvider: Sendable {
    func isAvailable(tag: String) async -> Bool
    func download(tag: String, progress: @Sendable @escaping (Double) -> Void) async throws
    func setPreservationPriority(_ priority: Double, for tag: String)
}

// MARK: - ODR Implementation

final class ODRResourceProvider: ResourceProvider, @unchecked Sendable {

    func isAvailable(tag: String) async -> Bool {
        await withCheckedContinuation { continuation in
            let request = NSBundleResourceRequest(tags: [tag])
            request.conditionallyBeginAccessingResources { available in
                if available {
                    request.endAccessingResources()
                }
                continuation.resume(returning: available)
            }
        }
    }

    func download(tag: String, progress: @Sendable @escaping (Double) -> Void) async throws {
        let request = NSBundleResourceRequest(tags: [tag])

        let observation = request.progress.observe(\.fractionCompleted) { prog, _ in
            progress(prog.fractionCompleted)
        }

        defer { observation.invalidate() }

        try await request.beginAccessingResources()
        progress(1.0)
    }

    func setPreservationPriority(_ priority: Double, for tag: String) {
        Bundle.main.setPreservationPriority(priority, forTags: [tag])
    }
}

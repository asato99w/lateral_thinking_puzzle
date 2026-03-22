import Foundation

// MARK: - Resource Provider Protocol (ODR / future AHBA abstraction)

protocol ResourceProvider: Sendable {
    func isAvailable(tag: String) async -> Bool
    func download(tag: String, progress: @Sendable @escaping (Double) -> Void) async throws
    func remove(tag: String)
    func setPreservationPriority(_ priority: Double, for tag: String)
}

// MARK: - ODR Implementation

final class ODRResourceProvider: ResourceProvider, @unchecked Sendable {

    /// Retained resource requests that keep ODR content accessible via Bundle.main
    private var activeRequests: [String: NSBundleResourceRequest] = [:]
    private let lock = NSLock()

    func isAvailable(tag: String) async -> Bool {
        await withCheckedContinuation { continuation in
            let request = NSBundleResourceRequest(tags: [tag])
            request.conditionallyBeginAccessingResources { [weak self] available in
                if available {
                    self?.lock.lock()
                    self?.activeRequests[tag] = request
                    self?.lock.unlock()
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

        lock.lock()
        activeRequests[tag] = request
        lock.unlock()
    }

    func remove(tag: String) {
        lock.lock()
        let request = activeRequests.removeValue(forKey: tag)
        lock.unlock()

        request?.endAccessingResources()
        Bundle.main.setPreservationPriority(0.0, forTags: [tag])
    }

    func setPreservationPriority(_ priority: Double, for tag: String) {
        Bundle.main.setPreservationPriority(priority, forTags: [tag])
    }
}

// MARK: - Mock Implementation (DEBUG)

#if DEBUG
final class MockResourceProvider: ResourceProvider, @unchecked Sendable {
    static let shared = MockResourceProvider()

    private var downloaded: Set<String> = []
    private let lock = NSLock()

    func isAvailable(tag: String) async -> Bool {
        lock.lock()
        defer { lock.unlock() }
        return downloaded.contains(tag)
    }

    func download(tag: String, progress: @Sendable @escaping (Double) -> Void) async throws {
        // Simulate download with progress over ~1 second
        for i in 1...10 {
            try await Task.sleep(for: .milliseconds(100))
            progress(Double(i) / 10.0)
        }
        lock.lock()
        downloaded.insert(tag)
        lock.unlock()
    }

    func remove(tag: String) {
        lock.lock()
        downloaded.remove(tag)
        lock.unlock()
    }

    func setPreservationPriority(_ priority: Double, for tag: String) {
        // no-op
    }
}
#endif

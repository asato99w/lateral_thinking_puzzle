import Foundation

protocol ODRResourceManaging: Sendable {
    func requestResource(tag: String) async throws -> Double
}

final class ODRResourceManager: ODRResourceManaging, @unchecked Sendable {
    func requestResource(tag: String) async throws -> Double {
        let request = NSBundleResourceRequest(tags: [tag])
        try await request.beginAccessingResources()
        return request.progress.fractionCompleted
    }
}

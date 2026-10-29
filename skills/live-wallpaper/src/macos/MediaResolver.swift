import Cocoa
import Foundation

// MARK: - Media & Source Resolution

func detectMediaType(for pathOrUrl: String) -> MediaType {
    let ext: String
    if let url = URL(string: pathOrUrl), url.scheme != nil {
        ext = url.pathExtension.lowercased()
    } else {
        ext = (pathOrUrl as NSString).pathExtension.lowercased()
    }
    if imageExtensions.contains(ext) {
        return .image
    }
    return .video
}

func expandSources(_ sources: [String]) -> [QueueItem] {
    var items: [QueueItem] = []
    let fm = FileManager.default

    for src in sources {
        if src.lowercased() == "naruto" {
            let p = NSString(string: "~/Desktop/naruto-kurama.mp4").expandingTildeInPath
            if fm.fileExists(atPath: p) { items.append(QueueItem(pathOrUrl: p, type: .video)); continue }
        } else if src.lowercased() == "aot" || src.lowercased() == "eren" {
            let p = NSString(string: "~/Desktop/aot-eren-yeager.mp4").expandingTildeInPath
            if fm.fileExists(atPath: p) { items.append(QueueItem(pathOrUrl: p, type: .video)); continue }
        }

        if src.hasPrefix("http://") || src.hasPrefix("https://") {
            items.append(QueueItem(pathOrUrl: src, type: detectMediaType(for: src)))
            continue
        }

        let localPath = NSString(string: src).expandingTildeInPath
        var isDir: ObjCBool = false
        if fm.fileExists(atPath: localPath, isDirectory: &isDir) {
            if isDir.boolValue {
                if let files = try? fm.contentsOfDirectory(atPath: localPath) {
                    let sortedFiles = files.sorted()
                    for f in sortedFiles {
                        if f.hasPrefix(".") { continue }
                        let ext = (f as NSString).pathExtension.lowercased()
                        let fullPath = (localPath as NSString).appendingPathComponent(f)
                        if imageExtensions.contains(ext) {
                            items.append(QueueItem(pathOrUrl: fullPath, type: .image))
                        } else if videoExtensions.contains(ext) {
                            items.append(QueueItem(pathOrUrl: fullPath, type: .video))
                        }
                    }
                }
            } else {
                items.append(QueueItem(pathOrUrl: localPath, type: detectMediaType(for: localPath)))
            }
        }
    }
    return items
}

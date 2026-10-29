import Cocoa
import AVFoundation

// MARK: - Enums & Models

enum MediaType: String, Codable {
    case video
    case image
}

struct QueueItem: Codable {
    let pathOrUrl: String
    let type: MediaType

    var url: URL? {
        if pathOrUrl.hasPrefix("http://") || pathOrUrl.hasPrefix("https://") {
            return URL(string: pathOrUrl)
        }
        let expanded = NSString(string: pathOrUrl).expandingTildeInPath
        if FileManager.default.fileExists(atPath: expanded) {
            return URL(fileURLWithPath: expanded)
        }
        return nil
    }

    var displayName: String {
        return url?.lastPathComponent ?? pathOrUrl
    }
}

struct EngineState: Codable {
    let pid: Int32
    let currentIndex: Int
    let interval: Double
    let perSpace: Bool
    let isMuted: Bool
    let volume: Float
    let currentItem: String
    let items: [QueueItem]
    let screensaverIdle: Double?
}

// MARK: - Constants & Paths

let pidFile = NSString(string: "~/.live-wallpaper.pid").expandingTildeInPath
let stateFile = NSString(string: "~/.live-wallpaper.state").expandingTildeInPath
let cmdFile = NSString(string: "~/.live-wallpaper.cmd").expandingTildeInPath
let logFile = NSString(string: "~/.live-wallpaper.log").expandingTildeInPath
let plistFile = NSString(string: "~/Library/LaunchAgents/com.antigravity.live-wallpaper.plist").expandingTildeInPath

let imageExtensions: Set<String> = ["png", "jpg", "jpeg", "heic", "webp", "gif", "bmp", "tiff", "tif"]
let videoExtensions: Set<String> = ["mp4", "mov", "m4v", "mkv", "avi", "webm", "m3u8"]

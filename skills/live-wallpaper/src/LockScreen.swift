import Cocoa
import AVFoundation
import CryptoKit

// MARK: - Native macOS Lock Screen Trigger

typealias SACLockScreenImmediateFunc = @convention(c) () -> Void

func lockSystemScreen() {
    if let lib = dlopen("/System/Library/PrivateFrameworks/login.framework/Versions/Current/login", RTLD_LAZY),
       let sym = dlsym(lib, "SACLockScreenImmediate") {
        let lockFunc = unsafeBitCast(sym, to: SACLockScreenImmediateFunc.self)
        lockFunc()
        return
    }
    // Fallback via system display sleep / login suspension
    let task = Process()
    task.executableURL = URL(fileURLWithPath: "/usr/bin/pmset")
    task.arguments = ["displaysleepnow"]
    try? task.run()
}

// MARK: - Lock Screen Wallpaper Synchronization

class LockScreenManager {
    static let shared = LockScreenManager()

    private let cacheDir: String
    private let primaryLockScreenFile: URL

    private init() {
        self.cacheDir = lockCacheDir
        let fm = FileManager.default
        if !fm.fileExists(atPath: cacheDir) {
            try? fm.createDirectory(atPath: cacheDir, withIntermediateDirectories: true)
        }
        self.primaryLockScreenFile = URL(fileURLWithPath: lockScreenFile)
    }

    /// Computes a persistent cache filename for a given media path/URL
    private func cacheFilePath(for pathOrUrl: String) -> URL {
        let hash = Insecure.MD5.hash(data: Data(pathOrUrl.utf8))
            .map { String(format: "%02hhx", $0) }
            .joined()
        let filename = "frame_\(hash).jpg"
        let fullPath = (cacheDir as NSString).appendingPathComponent(filename)
        return URL(fileURLWithPath: fullPath)
    }

    /// Synchronizes current active wallpaper (image or video poster frame) to the macOS native Lock Screen
    func syncLockScreen(for item: QueueItem, completion: ((Bool) -> Void)? = nil) {
        guard let url = item.url else {
            completion?(false)
            return
        }

        if item.type == .image {
            // Native image: set directly as desktop / lock screen wallpaper
            self.applyDesktopImage(url: url)
            completion?(true)
            return
        }

        // Video: Check cache first for 0ms frame retrieval
        let cachedURL = self.cacheFilePath(for: item.pathOrUrl)
        if FileManager.default.fileExists(atPath: cachedURL.path) {
            self.applyDesktopImage(url: cachedURL)
            // Mirror to canonical lockscreen path
            try? FileManager.default.removeItem(at: self.primaryLockScreenFile)
            try? FileManager.default.copyItem(at: cachedURL, to: self.primaryLockScreenFile)
            completion?(true)
            return
        }

        // Extract high-resolution video frame asynchronously
        DispatchQueue.global(qos: .userInitiated).async { [weak self] in
            guard let self = self else {
                completion?(false)
                return
            }
            self.extractPosterFrame(videoURL: url, saveTo: cachedURL) { [weak self] success in
                guard let self = self, success else {
                    DispatchQueue.main.async { completion?(false) }
                    return
                }
                // Mirror to canonical path
                try? FileManager.default.removeItem(at: self.primaryLockScreenFile)
                try? FileManager.default.copyItem(at: cachedURL, to: self.primaryLockScreenFile)
                self.applyDesktopImage(url: cachedURL)
                DispatchQueue.main.async { completion?(true) }
            }
        }
    }

    /// Extracts a crisp 4K frame from the video at 1.0s (or 0.0s fallback)
    private func extractPosterFrame(videoURL: URL, saveTo targetURL: URL, completion: @escaping (Bool) -> Void) {
        let asset = AVURLAsset(url: videoURL)
        let generator = AVAssetImageGenerator(asset: asset)
        generator.appliesPreferredTrackTransform = true
        generator.maximumSize = CGSize(width: 3840, height: 2160)

        let targetTimes = [
            CMTime(seconds: 1.0, preferredTimescale: 600),
            CMTime(seconds: 0.0, preferredTimescale: 600)
        ]

        if #available(macOS 13.0, *) {
            Task {
                for time in targetTimes {
                    do {
                        let (cgImage, _) = try await generator.image(at: time)
                        let bitmap = NSBitmapImageRep(cgImage: cgImage)
                        if let data = bitmap.representation(using: .jpeg, properties: [.compressionFactor: 0.92]) {
                            try data.write(to: targetURL, options: .atomic)
                            completion(true)
                            return
                        }
                    } catch {
                        continue
                    }
                }
                completion(false)
            }
        } else {
            for time in targetTimes {
                do {
                    let cgImage = try generator.copyCGImage(at: time, actualTime: nil)
                    let bitmap = NSBitmapImageRep(cgImage: cgImage)
                    if let data = bitmap.representation(using: .jpeg, properties: [.compressionFactor: 0.92]) {
                        try data.write(to: targetURL, options: .atomic)
                        completion(true)
                        return
                    }
                } catch {
                    continue
                }
            }
            completion(false)
        }
    }

    /// Sets the desktop picture across all screens so the macOS Lock Screen displays this image
    private func applyDesktopImage(url: URL) {
        DispatchQueue.main.async {
            for screen in NSScreen.screens {
                try? NSWorkspace.shared.setDesktopImageURL(url, for: screen, options: [:])
            }
        }
    }

    /// Clear cached video poster frames
    func clearCache() {
        try? FileManager.default.removeItem(atPath: cacheDir)
        try? FileManager.default.createDirectory(atPath: cacheDir, withIntermediateDirectories: true)
    }
}

// MARK: - Distributed Lock & Unlock Notification Monitor

class ScreenLockMonitor {
    static let shared = ScreenLockMonitor()

    private(set) var isScreenLocked: Bool = false
    var onLock: (() -> Void)?
    var onUnlock: (() -> Void)?

    private var isMonitoring = false

    func startMonitoring() {
        guard !isMonitoring else { return }
        isMonitoring = true

        let dnc = DistributedNotificationCenter.default()

        dnc.addObserver(
            forName: NSNotification.Name("com.apple.screenIsLocked"),
            object: nil,
            queue: .main
        ) { [weak self] _ in
            guard let self = self else { return }
            self.isScreenLocked = true
            self.onLock?()
        }

        dnc.addObserver(
            forName: NSNotification.Name("com.apple.screenIsUnlocked"),
            object: nil,
            queue: .main
        ) { [weak self] _ in
            guard let self = self else { return }
            self.isScreenLocked = false
            self.onUnlock?()
        }
    }
}

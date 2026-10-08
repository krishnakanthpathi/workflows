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

// MARK: - Lock Screen Video & Wallpaper Synchronization

class LockScreenManager {
    static let shared = LockScreenManager()

    private let cacheDir: String
    private let primaryLockScreenFile: URL

    // Aerial video directories across macOS versions
    private let userAerialsVideosDir: String
    private let userAerialsThumbnailsDir: String
    private let userIndexPlistPath: String
    private let systemAerialsVideosDir: String

    private init() {
        self.cacheDir = lockCacheDir
        let fm = FileManager.default
        if !fm.fileExists(atPath: cacheDir) {
            try? fm.createDirectory(atPath: cacheDir, withIntermediateDirectories: true)
        }
        self.primaryLockScreenFile = URL(fileURLWithPath: lockScreenFile)

        self.userAerialsVideosDir = NSString(string: "~/Library/Application Support/com.apple.wallpaper/aerials/videos").expandingTildeInPath
        self.userAerialsThumbnailsDir = NSString(string: "~/Library/Application Support/com.apple.wallpaper/aerials/thumbnails").expandingTildeInPath
        self.userIndexPlistPath = NSString(string: "~/Library/Application Support/com.apple.wallpaper/Store/Index.plist").expandingTildeInPath
        self.systemAerialsVideosDir = "/Library/Application Support/com.apple.idleassetsd/Customer/4KSDR240FPS"
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

    /// Synchronizes current active wallpaper (both static poster and dynamic lock screen video)
    func syncLockScreen(for item: QueueItem, completion: ((Bool) -> Void)? = nil) {
        guard let url = item.url else {
            completion?(false)
            return
        }

        if item.type == .image {
            self.applyDesktopImage(url: url)
            completion?(true)
            return
        }

        // For Video:
        // 1. Extract static frame for desktop background continuity
        self.syncStaticPosterFrame(videoURL: url, pathOrUrl: item.pathOrUrl)

        // 2. Deploy dynamic video into macOS native Aerial lock screen engine
        self.syncDynamicLockScreenVideo(videoURL: url) { success in
            completion?(success)
        }
    }

    private func syncStaticPosterFrame(videoURL: URL, pathOrUrl: String) {
        let cachedURL = self.cacheFilePath(for: pathOrUrl)
        if FileManager.default.fileExists(atPath: cachedURL.path) {
            self.applyDesktopImage(url: cachedURL)
            try? FileManager.default.removeItem(at: self.primaryLockScreenFile)
            try? FileManager.default.copyItem(at: cachedURL, to: self.primaryLockScreenFile)
            return
        }

        self.extractPosterFrame(videoURL: videoURL, saveTo: cachedURL) { [weak self] success in
            guard let self = self, success else { return }
            try? FileManager.default.removeItem(at: self.primaryLockScreenFile)
            try? FileManager.default.copyItem(at: cachedURL, to: self.primaryLockScreenFile)
            self.applyDesktopImage(url: cachedURL)
        }
    }

    /// Injects video into macOS Aerial Lock Screen directories
    func syncDynamicLockScreenVideo(videoURL: URL, completion: @escaping (Bool) -> Void) {
        let fm = FileManager.default
        var targetDirs: [String] = []

        if fm.fileExists(atPath: userAerialsVideosDir) {
            targetDirs.append(userAerialsVideosDir)
        }
        if fm.isWritableFile(atPath: systemAerialsVideosDir) {
            targetDirs.append(systemAerialsVideosDir)
        }

        guard !targetDirs.isEmpty else {
            completion(false)
            return
        }

        DispatchQueue.global(qos: .userInitiated).async { [weak self] in
            guard let self = self else { completion(false); return }

            let tempMOV = URL(fileURLWithPath: NSTemporaryDirectory()).appendingPathComponent("live_lockscreen_export.mov")
            try? fm.removeItem(at: tempMOV)

            self.convertToMOV(inputURL: videoURL, outputURL: tempMOV) { success in
                guard success else {
                    completion(false)
                    return
                }

                var didUpdateAny = false

                for dir in targetDirs {
                    guard let contents = try? fm.contentsOfDirectory(atPath: dir) else { continue }
                    let movFiles = contents.filter { $0.hasSuffix(".mov") && !$0.contains(".backup") }

                    for movFile in movFiles {
                        let fullMovPath = (dir as NSString).appendingPathComponent(movFile)
                        let backupPath = fullMovPath + ".backup"

                        // Safety backup original using APFS clone / copy
                        if !fm.fileExists(atPath: backupPath) {
                            try? fm.copyItem(atPath: fullMovPath, toPath: backupPath)
                        }

                        // Overwrite target with converted custom video
                        try? fm.removeItem(atPath: fullMovPath)
                        do {
                            try fm.copyItem(at: tempMOV, to: URL(fileURLWithPath: fullMovPath))
                            didUpdateAny = true

                            // Also update thumbnail if in user directory
                            let uuidPrefix = (movFile as NSString).deletingPathExtension
                            let thumbPath = (self.userAerialsThumbnailsDir as NSString).appendingPathComponent(uuidPrefix + ".png")
                            if fm.fileExists(atPath: self.userAerialsThumbnailsDir) {
                                self.updateThumbnail(for: videoURL, targetPath: thumbPath)
                            }
                        } catch {
                            print("[LOCK_SCREEN] Failed to copy to \(fullMovPath): \(error)")
                        }
                    }
                }

                try? fm.removeItem(at: tempMOV)

                if didUpdateAny {
                    // Update Index.plist so system wallpaper uses choice.aerials
                    self.configureIndexPlistForAerials()
                    // Set screensaver extension
                    self.configureScreensaverExtension()
                    // Signal WallpaperAgent to reload
                    self.restartWallpaperAgent()
                    print("[LOCK_SCREEN] Deployed dynamic video to macOS native Lock Screen Aerial engine.")
                    fflush(stdout)
                }

                DispatchQueue.main.async {
                    completion(didUpdateAny)
                }
            }
        }
    }

    /// Converts or passthrough-remuxes input video to QuickTime MOV format
    private func convertToMOV(inputURL: URL, outputURL: URL, completion: @escaping (Bool) -> Void) {
        if inputURL.pathExtension.lowercased() == "mov" {
            try? FileManager.default.copyItem(at: inputURL, to: outputURL)
            completion(true)
            return
        }

        let asset = AVURLAsset(url: inputURL)
        guard let exportSession = AVAssetExportSession(asset: asset, presetName: AVAssetExportPresetPassthrough) else {
            completion(false)
            return
        }

        if #available(macOS 15.0, *) {
            Task {
                do {
                    try await exportSession.export(to: outputURL, as: .mov)
                    completion(true)
                } catch {
                    completion(false)
                }
            }
        } else {
            exportSession.outputURL = outputURL
            exportSession.outputFileType = .mov
            exportSession.exportAsynchronously {
                completion(exportSession.status == .completed)
            }
        }
    }

    /// Extracts a crisp frame from the video
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

    /// Generates thumbnail PNG for lockscreen transition
    private func updateThumbnail(for videoURL: URL, targetPath: String) {
        let asset = AVURLAsset(url: videoURL)
        let generator = AVAssetImageGenerator(asset: asset)
        generator.appliesPreferredTrackTransform = true
        generator.maximumSize = CGSize(width: 1280, height: 720)
        let time = CMTime(seconds: 1.0, preferredTimescale: 600)

        if #available(macOS 13.0, *) {
            Task {
                if let (cgImage, _) = try? await generator.image(at: time) {
                    let rep = NSBitmapImageRep(cgImage: cgImage)
                    if let pngData = rep.representation(using: .png, properties: [:]) {
                        try? pngData.write(to: URL(fileURLWithPath: targetPath), options: .atomic)
                    }
                }
            }
        }
    }

    /// Configures Index.plist so macOS uses choice.aerials on Desktop & Idle
    private func configureIndexPlistForAerials() {
        let fm = FileManager.default
        guard fm.fileExists(atPath: userIndexPlistPath) else { return }

        // Backup Index.plist if not already backed up
        let backupPath = userIndexPlistPath + ".backup"
        if !fm.fileExists(atPath: backupPath) {
            try? fm.copyItem(atPath: userIndexPlistPath, toPath: backupPath)
        }

        let script = """
        import plistlib, os
        path = os.path.expanduser('~/Library/Application Support/com.apple.wallpaper/Store/Index.plist')
        try:
            with open(path, 'rb') as f:
                idx = plistlib.load(f)
            updated = False
            for disp_id, disp in idx.get('Displays', {}).items():
                if 'Idle' in disp and 'Desktop' in disp:
                    idle_choices = disp['Idle'].get('Content', {}).get('Choices', [])
                    for choice in idle_choices:
                        if choice.get('Provider') == 'com.apple.wallpaper.choice.aerials':
                            disp['Desktop']['Content']['Choices'] = idle_choices
                            updated = True
                            break
            if updated:
                with open(path, 'wb') as f:
                    plistlib.dump(idx, f)
        except Exception:
            pass
        """
        let p = Process()
        p.executableURL = URL(fileURLWithPath: "/usr/bin/python3")
        p.arguments = ["-c", script]
        try? p.run()
        p.waitUntilExit()
    }

    /// Configures screensaver module to use WallpaperAerialsExtension
    private func configureScreensaverExtension() {
        let p = Process()
        p.executableURL = URL(fileURLWithPath: "/usr/bin/defaults")
        p.arguments = [
            "-currentHost", "write", "com.apple.screensaver", "moduleDict", "-dict",
            "moduleName", "WallpaperAerialsExtension",
            "path", "/System/Library/ExtensionKit/Extensions/WallpaperAerialsExtension.appex",
            "type", "0"
        ]
        try? p.run()
        p.waitUntilExit()
    }

    /// Restarts WallpaperAgent and WallpaperAerialsExtension
    private func restartWallpaperAgent() {
        let p = Process()
        p.executableURL = URL(fileURLWithPath: "/usr/bin/killall")
        p.arguments = ["WallpaperAgent", "WallpaperAerialsExtension"]
        try? p.run()
    }

    /// Sets the desktop picture across all screens
    private func applyDesktopImage(url: URL) {
        DispatchQueue.main.async {
            for screen in NSScreen.screens {
                try? NSWorkspace.shared.setDesktopImageURL(url, for: screen, options: [:])
            }
        }
    }

    /// Restores any backed up original macOS aerial videos and Index.plist
    func restoreOriginalLockScreen() -> Bool {
        let fm = FileManager.default
        var restored = false
        let targetDirs = [userAerialsVideosDir, systemAerialsVideosDir]

        for dir in targetDirs {
            guard let contents = try? fm.contentsOfDirectory(atPath: dir) else { continue }
            let backupFiles = contents.filter { $0.hasSuffix(".mov.backup") }

            for bFile in backupFiles {
                let backupPath = (dir as NSString).appendingPathComponent(bFile)
                let originalPath = (backupPath as NSString).deletingPathExtension

                try? fm.removeItem(atPath: originalPath)
                if (try? fm.copyItem(atPath: backupPath, toPath: originalPath)) != nil {
                    restored = true
                }
            }
        }

        let indexBackup = userIndexPlistPath + ".backup"
        if fm.fileExists(atPath: indexBackup) {
            try? fm.removeItem(atPath: userIndexPlistPath)
            try? fm.copyItem(atPath: indexBackup, toPath: userIndexPlistPath)
            restored = true
        }

        if restored {
            restartWallpaperAgent()
        }
        return restored
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

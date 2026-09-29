import Cocoa
import AVFoundation
import AVKit
import CoreFoundation

// MARK: - Models

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
}

// MARK: - Constants & Paths

let pidFile = NSString(string: "~/.live-wallpaper.pid").expandingTildeInPath
let stateFile = NSString(string: "~/.live-wallpaper.state").expandingTildeInPath
let cmdFile = NSString(string: "~/.live-wallpaper.cmd").expandingTildeInPath
let logFile = NSString(string: "~/.live-wallpaper.log").expandingTildeInPath
let plistFile = NSString(string: "~/Library/LaunchAgents/com.antigravity.live-wallpaper.plist").expandingTildeInPath

let imageExtensions: Set<String> = ["png", "jpg", "jpeg", "heic", "webp", "gif", "bmp", "tiff", "tif"]
let videoExtensions: Set<String> = ["mp4", "mov", "m4v", "mkv", "avi", "webm", "m3u8"]

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

// MARK: - SkyLight Private CGS Spaces API

typealias CGSConnectionIDFunc = @convention(c) () -> Int32
typealias CGSCopySpacesFunc = @convention(c) (Int32) -> Unmanaged<CFArray>?
typealias CGSAddWindowsToSpacesFunc = @convention(c) (Int32, CFArray, CFArray) -> Void
typealias CGSRemoveWindowsFromSpacesFunc = @convention(c) (Int32, CFArray, CFArray) -> Void

var cgsConnection: CGSConnectionIDFunc?
var copyManagedSpaces: CGSCopySpacesFunc?
var addWindowsToSpaces: CGSAddWindowsToSpacesFunc?
var removeWindowsFromSpaces: CGSRemoveWindowsFromSpacesFunc?

func initSkyLight() {
    guard let handle = dlopen("/System/Library/PrivateFrameworks/SkyLight.framework/SkyLight", RTLD_LAZY) else {
        return
    }
    if let symConn = dlsym(handle, "CGSMainConnectionID") {
        cgsConnection = unsafeBitCast(symConn, to: CGSConnectionIDFunc.self)
    }
    if let symSpaces = dlsym(handle, "CGSCopyManagedDisplaySpaces") {
        copyManagedSpaces = unsafeBitCast(symSpaces, to: CGSCopySpacesFunc.self)
    }
    if let symAdd = dlsym(handle, "CGSAddWindowsToSpaces") {
        addWindowsToSpaces = unsafeBitCast(symAdd, to: CGSAddWindowsToSpacesFunc.self)
    }
    if let symRemove = dlsym(handle, "CGSRemoveWindowsFromSpaces") {
        removeWindowsFromSpaces = unsafeBitCast(symRemove, to: CGSRemoveWindowsFromSpacesFunc.self)
    }
}

func getAllSpaceIDs() -> [Int64] {
    if cgsConnection == nil { initSkyLight() }
    guard let getCID = cgsConnection, let getSpaces = copyManagedSpaces else { return [] }
    let cid = getCID()
    guard let unmanaged = getSpaces(cid) else { return [] }
    let array = unmanaged.takeRetainedValue() as [AnyObject]
    guard let monitor = array.first as? [String: Any],
          let spaces = monitor["Spaces"] as? [[String: Any]] else {
        return []
    }
    return spaces.compactMap { $0["id64"] as? Int64 }
}

func getCurrentSpaceIndex() -> Int {
    if cgsConnection == nil { initSkyLight() }
    guard let getCID = cgsConnection, let getSpaces = copyManagedSpaces else { return 0 }
    let cid = getCID()
    guard let unmanaged = getSpaces(cid) else { return 0 }
    let array = unmanaged.takeRetainedValue() as [AnyObject]
    guard let monitor = array.first as? [String: Any],
          let cur = monitor["Current Space"] as? [String: Any],
          let curId = cur["ManagedSpaceID"] as? Int,
          let spaces = monitor["Spaces"] as? [[String: Any]] else {
        return 0
    }
    let ids = spaces.compactMap { $0["ManagedSpaceID"] as? Int }
    if let idx = ids.firstIndex(of: curId) {
        return idx
    }
    return 0
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

// MARK: - Space-Dedicated Window (Native Zero-Delay Sliding)

class SpaceWallpaperWindow {
    let window: NSWindow
    let spaceID: Int64
    let item: QueueItem
    var player: AVQueuePlayer?
    var looper: AVPlayerLooper?

    init(screen: NSScreen, spaceID: Int64, item: QueueItem, isMuted: Bool, volume: Float) {
        self.spaceID = spaceID
        self.item = item

        window = NSWindow(
            contentRect: screen.frame,
            styleMask: [.borderless],
            backing: .buffered,
            defer: false,
            screen: screen
        )

        let iconLevel = Int(CGWindowLevelForKey(.desktopIconWindow))
        window.level = NSWindow.Level(rawValue: iconLevel - 1)
        window.collectionBehavior = [.stationary, .ignoresCycle] // Pinned strictly to this space!
        window.ignoresMouseEvents = true
        window.isOpaque = true
        window.backgroundColor = .black
        window.hasShadow = false

        if item.type == .image {
            let container = NSView(frame: NSRect(origin: .zero, size: screen.frame.size))
            container.wantsLayer = true
            let imageLayer = CALayer()
            imageLayer.frame = NSRect(origin: .zero, size: screen.frame.size)
            imageLayer.contentsGravity = .resizeAspectFill
            imageLayer.autoresizingMask = [.layerWidthSizable, .layerHeightSizable]
            if let url = item.url, let img = NSImage(contentsOf: url) {
                imageLayer.contents = img
            }
            container.layer?.addSublayer(imageLayer)
            window.contentView = container
        } else {
            let container = NSView(frame: NSRect(origin: .zero, size: screen.frame.size))
            let playerView = AVPlayerView(frame: NSRect(origin: .zero, size: screen.frame.size))
            playerView.controlsStyle = .none
            playerView.videoGravity = .resizeAspectFill
            playerView.autoresizingMask = [.width, .height]

            if let url = item.url {
                let playerItem = AVPlayerItem(url: url)
                let qPlayer = AVQueuePlayer(playerItem: playerItem)
                qPlayer.isMuted = isMuted
                qPlayer.volume = volume
                qPlayer.actionAtItemEnd = .none
                let qLooper = AVPlayerLooper(player: qPlayer, templateItem: playerItem)
                self.looper = qLooper
                self.player = qPlayer
                playerView.player = qPlayer
            }
            container.addSubview(playerView)
            window.contentView = container
        }

        window.orderFrontRegardless()
    }

    func activate(isMuted: Bool, volume: Float) {
        setAudioActive(!isMuted, volume: volume)
        player?.play()
    }

    func deactivate() {
        player?.pause()
        player?.isMuted = true
    }

    func setAudioActive(_ active: Bool, volume: Float) {
        guard let p = player else { return }
        if active {
            p.volume = volume
            p.isMuted = false
        } else {
            p.isMuted = true
        }
    }

    func teardown() {
        player?.pause()
        player?.removeAllItems()
        looper = nil
        player = nil
        window.orderOut(nil)
    }
}

// MARK: - Regular Mode Screen Renderer

class ScreenRenderer {
    let window: NSWindow
    let containerView: NSView
    let playerView: AVPlayerView
    let imageLayer: CALayer
    var player: AVQueuePlayer?
    var looper: AVPlayerLooper?
    var endObserver: Any?
    var currentURL: URL?

    init(screen: NSScreen) {
        window = NSWindow(
            contentRect: screen.frame,
            styleMask: [.borderless],
            backing: .buffered,
            defer: false,
            screen: screen
        )

        let iconLevel = Int(CGWindowLevelForKey(.desktopIconWindow))
        window.level = NSWindow.Level(rawValue: iconLevel - 1)
        window.collectionBehavior = [.canJoinAllSpaces, .stationary, .ignoresCycle]
        window.ignoresMouseEvents = true
        window.isOpaque = true
        window.backgroundColor = .black
        window.hasShadow = false

        containerView = NSView(frame: NSRect(origin: .zero, size: screen.frame.size))
        containerView.wantsLayer = true

        imageLayer = CALayer()
        imageLayer.frame = NSRect(origin: .zero, size: screen.frame.size)
        imageLayer.contentsGravity = .resizeAspectFill
        imageLayer.autoresizingMask = [.layerWidthSizable, .layerHeightSizable]
        imageLayer.opacity = 0.0

        playerView = AVPlayerView(frame: NSRect(origin: .zero, size: screen.frame.size))
        playerView.controlsStyle = .none
        playerView.videoGravity = .resizeAspectFill
        playerView.autoresizingMask = [.width, .height]
        playerView.wantsLayer = true
        playerView.layer?.opacity = 0.0

        containerView.layer?.addSublayer(imageLayer)
        containerView.addSubview(playerView)
        window.contentView = containerView
        window.orderFrontRegardless()
    }

    func displayImage(url: URL) {
        if currentURL == url && imageLayer.opacity > 0.9 { return }
        currentURL = url
        guard let nsImage = NSImage(contentsOf: url) else { return }
        cleanupVideo()

        CATransaction.begin()
        CATransaction.setAnimationDuration(0.3)
        imageLayer.contents = nsImage
        imageLayer.opacity = 1.0
        playerView.layer?.opacity = 0.0
        CATransaction.commit()
    }

    func displayVideo(url: URL, isMuted: Bool, volume: Float, onEnd: (() -> Void)?) {
        if currentURL == url && player != nil { return }
        currentURL = url
        cleanupVideo()

        let playerItem = AVPlayerItem(url: url)
        let qPlayer = AVQueuePlayer(playerItem: playerItem)
        qPlayer.isMuted = isMuted
        qPlayer.volume = volume
        qPlayer.actionAtItemEnd = .none

        let qLooper = AVPlayerLooper(player: qPlayer, templateItem: playerItem)
        self.looper = qLooper
        self.player = qPlayer

        if let onEnd = onEnd {
            endObserver = NotificationCenter.default.addObserver(
                forName: AVPlayerItem.didPlayToEndTimeNotification,
                object: playerItem,
                queue: .main
            ) { _ in
                onEnd()
            }
        }

        playerView.player = qPlayer
        CATransaction.begin()
        CATransaction.setAnimationDuration(0.3)
        playerView.layer?.opacity = 1.0
        imageLayer.opacity = 0.0
        CATransaction.commit()

        qPlayer.play()
    }

    func cleanupVideo() {
        if let obs = endObserver {
            NotificationCenter.default.removeObserver(obs)
            endObserver = nil
        }
        player?.pause()
        player?.removeAllItems()
        looper = nil
        player = nil
        playerView.player = nil
    }

    func teardown() {
        cleanupVideo()
        window.orderOut(nil)
    }
}

// MARK: - App Delegate & Queue Engine

class WallpaperApp: NSObject, NSApplicationDelegate {
    static var shared: WallpaperApp?

    var renderers: [ScreenRenderer] = []
    var spaceWindows: [SpaceWallpaperWindow] = []
    var items: [QueueItem] = []
    var currentIndex: Int = 0
    let interval: Double
    let perSpace: Bool
    let isMuted: Bool
    let volume: Float
    let shuffleQueue: Bool

    var rotationTimer: Timer?
    var sigusr1Source: DispatchSourceSignal?
    var lastSpaceIndex: Int = -1

    init(items: [QueueItem], interval: Double, perSpace: Bool, isMuted: Bool, volume: Float, shuffle: Bool) {
        self.items = items
        self.interval = interval
        self.perSpace = perSpace
        self.isMuted = isMuted
        self.volume = volume
        self.shuffleQueue = shuffle
        if shuffle {
            self.items.shuffle()
        }
        super.init()
        WallpaperApp.shared = self
    }

    func applicationDidFinishLaunching(_ notification: Notification) {
        initSkyLight()
        setupWindows()
        setupSignals()

        NotificationCenter.default.addObserver(
            self,
            selector: #selector(screenParametersChanged),
            name: NSApplication.didChangeScreenParametersNotification,
            object: nil
        )

        if perSpace {
            // Watch for space changes to sync audio and state
            let timer = Timer(timeInterval: 0.15, repeats: true) { [weak self] _ in
                self?.syncActiveSpace()
            }
            RunLoop.main.add(timer, forMode: .common)
            syncActiveSpace()
        } else {
            playCurrent()
            startTimerIfNeeded()
        }
    }

    @objc func screenParametersChanged() {
        teardownWindows()
        setupWindows()
        if !perSpace {
            playCurrent()
        }
    }

    func setupWindows() {
        if perSpace {
            setupPerSpaceWindows()
        } else {
            for screen in NSScreen.screens {
                renderers.append(ScreenRenderer(screen: screen))
            }
        }
    }

    func setupPerSpaceWindows() {
        let spaceIDs = getAllSpaceIDs()
        guard !spaceIDs.isEmpty, let screen = NSScreen.main else {
            // Fallback to regular screen renderer if spaces query failed
            for s in NSScreen.screens {
                renderers.append(ScreenRenderer(screen: s))
            }
            return
        }

        guard let getCID = cgsConnection,
              let add = addWindowsToSpaces,
              let remove = removeWindowsFromSpaces else {
            return
        }

        let cid = getCID()

        for (idx, spaceID) in spaceIDs.enumerated() {
            let item = items[idx % items.count]
            let spaceWin = SpaceWallpaperWindow(
                screen: screen,
                spaceID: spaceID,
                item: item,
                isMuted: isMuted,
                volume: volume
            )

            let wid = spaceWin.window.windowNumber
            // Isolate window strictly to its designated virtual desktop space!
            remove(cid, [wid] as CFArray, spaceIDs as CFArray)
            add(cid, [wid] as CFArray, [spaceID] as CFArray)

            spaceWindows.append(spaceWin)
        }

        // Extreme Low-Power: only activate current space, pause all others
        let currentIdx = getCurrentSpaceIndex()
        for (idx, spaceWin) in spaceWindows.enumerated() {
            if idx == currentIdx {
                spaceWin.activate(isMuted: isMuted, volume: volume)
            } else {
                spaceWin.deactivate()
            }
        }

        saveState()
        print("Initialized \(spaceWindows.count) zero-delay desktop space windows (Extreme Low-Power Mode).")
        fflush(stdout)
    }

    func teardownWindows() {
        for w in spaceWindows {
            w.teardown()
        }
        spaceWindows.removeAll()

        for r in renderers {
            r.teardown()
        }
        renderers.removeAll()
    }

    func syncActiveSpace() {
        let currentIdx = getCurrentSpaceIndex()
        if currentIdx != lastSpaceIndex {
            let oldIndex = lastSpaceIndex
            lastSpaceIndex = currentIdx
            currentIndex = currentIdx % items.count
            saveState()

            // Extreme Low-Power: pause previous space, resume active space
            if spaceWindows.indices.contains(oldIndex) {
                spaceWindows[oldIndex].deactivate()
            }
            if spaceWindows.indices.contains(currentIdx) {
                spaceWindows[currentIdx].activate(isMuted: isMuted, volume: volume)
            }

            let activeItem = items[currentIndex]
            print("ACTIVE_DESKTOP_SPACE [Desktop \(currentIdx + 1)]: \(activeItem.displayName)")
            fflush(stdout)
        }
    }

    func playCurrent() {
        guard !perSpace, !items.isEmpty else { return }
        if currentIndex >= items.count { currentIndex = 0 }
        if currentIndex < 0 { currentIndex = items.count - 1 }

        for (screenIdx, r) in renderers.enumerated() {
            let itemIdx = (currentIndex + screenIdx) % items.count
            let item = items[itemIdx]
            guard let url = item.url else { continue }

            if item.type == .image {
                r.displayImage(url: url)
            } else {
                let onEnd: (() -> Void)? = (interval == 0 && items.count > 1) ? { [weak self] in
                    self?.nextWallpaper()
                } : nil
                r.displayVideo(url: url, isMuted: isMuted, volume: volume, onEnd: onEnd)
            }
        }

        saveState()
        let activeItem = items[currentIndex]
        print("LIVE_WALLPAPER_ACTIVE [\(currentIndex + 1)/\(items.count)]: \(activeItem.displayName)")
        fflush(stdout)
    }

    func startTimerIfNeeded() {
        rotationTimer?.invalidate()
        if !perSpace && interval > 0 && items.count > 1 {
            rotationTimer = Timer.scheduledTimer(withTimeInterval: interval, repeats: true) { [weak self] _ in
                self?.nextWallpaper()
            }
        }
    }

    func nextWallpaper() {
        guard !items.isEmpty else { return }
        currentIndex = (currentIndex + 1) % items.count
        playCurrent()
        startTimerIfNeeded()
    }

    func prevWallpaper() {
        guard !items.isEmpty else { return }
        currentIndex = (currentIndex - 1 + items.count) % items.count
        playCurrent()
        startTimerIfNeeded()
    }

    func gotoWallpaper(index: Int) {
        guard !items.isEmpty else { return }
        let clamped = max(0, min(items.count - 1, index))
        currentIndex = clamped
        playCurrent()
        startTimerIfNeeded()
    }

    func addItem(pathOrUrl: String) {
        let expanded = expandSources([pathOrUrl])
        if !expanded.isEmpty {
            items.append(contentsOf: expanded)
            saveState()
            if perSpace {
                teardownWindows()
                setupPerSpaceWindows()
            } else {
                startTimerIfNeeded()
            }
            print("Added \(expanded.count) item(s) to queue. Total: \(items.count)")
        }
    }

    func saveState() {
        let currentName = items.indices.contains(currentIndex) ? items[currentIndex].displayName : "none"
        let state = EngineState(
            pid: getpid(),
            currentIndex: currentIndex,
            interval: interval,
            perSpace: perSpace,
            isMuted: isMuted,
            volume: volume,
            currentItem: currentName,
            items: items
        )
        if let data = try? JSONEncoder().encode(state) {
            try? data.write(to: URL(fileURLWithPath: stateFile))
        }
    }

    func setupSignals() {
        signal(SIGUSR1, SIG_IGN)
        let source = DispatchSource.makeSignalSource(signal: SIGUSR1, queue: .main)
        source.setEventHandler { [weak self] in
            self?.handleIPCCommand()
        }
        source.resume()
        self.sigusr1Source = source
    }

    func handleIPCCommand() {
        guard let raw = try? String(contentsOfFile: cmdFile, encoding: .utf8) else {
            nextWallpaper()
            return
        }
        let content = raw.trimmingCharacters(in: .whitespacesAndNewlines)
        if content.isEmpty {
            nextWallpaper()
            return
        }
        try? FileManager.default.removeItem(atPath: cmdFile)

        let parts = content.split(separator: " ", maxSplits: 1).map(String.init)
        let action = parts[0].uppercased()

        switch action {
        case "NEXT":
            nextWallpaper()
        case "PREV":
            prevWallpaper()
        case "GOTO":
            if parts.count > 1, let idx = Int(parts[1]) {
                gotoWallpaper(index: idx)
            }
        case "ADD":
            if parts.count > 1 {
                addItem(pathOrUrl: parts[1])
            }
        default:
            nextWallpaper()
        }
    }
}

// MARK: - Process & IPC Control Functions

func getRunningPID() -> Int32? {
    guard let content = try? String(contentsOfFile: pidFile, encoding: .utf8),
          let pid = Int32(content.trimmingCharacters(in: .whitespacesAndNewlines)) else {
        return nil
    }
    if kill(pid, 0) == 0 {
        return pid
    }
    return nil
}

func sendCommand(_ cmd: String) -> Bool {
    guard let pid = getRunningPID() else {
        print("Live wallpaper is not running.")
        return false
    }
    try? cmd.write(toFile: cmdFile, atomically: true, encoding: .utf8)
    kill(pid, SIGUSR1)
    return true
}

func stopRunning() {
    if let pid = getRunningPID() {
        kill(pid, SIGTERM)
        try? FileManager.default.removeItem(atPath: pidFile)
        try? FileManager.default.removeItem(atPath: stateFile)
        try? FileManager.default.removeItem(atPath: cmdFile)
        print("Stopped live wallpaper (PID \(pid)).")
    } else {
        print("No live wallpaper currently running.")
    }
}

func printStatus() {
    guard let pid = getRunningPID() else {
        print("Live wallpaper is not running.")
        return
    }

    if let data = try? Data(contentsOf: URL(fileURLWithPath: stateFile)),
       let state = try? JSONDecoder().decode(EngineState.self, from: data) {
        print("Live wallpaper is running (PID \(pid))")
        print("Active item [\(state.currentIndex + 1)/\(state.items.count)]: \(state.currentItem)")
        if state.perSpace {
            let spaceIdx = getCurrentSpaceIndex()
            print("Mode: Native Per-Desktop Space Pinning (Currently on Desktop \(spaceIdx + 1)) [0ms Delay]")
        } else {
            print("Interval: \(state.interval > 0 ? "\(Int(state.interval))s" : "Loop-based (0s)")")
        }
        print("Audio: \(state.isMuted ? "Muted" : "\(Int(state.volume * 100))%")")
        print("Queue count: \(state.items.count)")
    } else {
        print("Live wallpaper is running (PID \(pid))")
    }
}

func printQueue() {
    guard let data = try? Data(contentsOf: URL(fileURLWithPath: stateFile)),
          let state = try? JSONDecoder().decode(EngineState.self, from: data) else {
        print("No active live wallpaper queue found.")
        return
    }

    let modeDesc = state.perSpace ? "Native Per-Desktop Space Pinning (0ms Real-Time)" : (state.interval > 0 ? "Interval: \(Int(state.interval))s" : "Loop-based")
    print("Live Wallpaper Queue (\(state.items.count) items):")
    print("\(modeDesc) | Audio: \(state.isMuted ? "Muted" : "\(Int(state.volume * 100))%")\n")

    for (i, item) in state.items.enumerated() {
        let marker = (i == state.currentIndex) ? "-> [ACTIVE]" : "           "
        let spaceTag = state.perSpace ? " (Desktop \(i + 1))" : ""
        print(String(format: "%@ %2d. [%@] %@%@", marker, i + 1, item.type.rawValue.uppercased(), item.displayName, spaceTag))
    }
}

func installService(sources: [String], interval: Double, perSpace: Bool, isMuted: Bool, volume: Float, shuffle: Bool) {
    let binPath = "/Users/krishnakanth/.local/bin/live-wallpaper"
    var args: [String] = [binPath]
    if !isMuted {
        args.append(contentsOf: ["--audio", "--volume", "\(Int(volume * 100))"])
    }
    if perSpace {
        args.append("--per-space")
    } else if interval > 0 {
        args.append(contentsOf: ["--interval", "\(Int(interval))"])
    }
    if shuffle {
        args.append("--shuffle")
    }
    args.append(contentsOf: sources)

    let argsXml = args.map { "        <string>\($0)</string>" }.joined(separator: "\n")
    let plistContent = """
    <?xml version="1.0" encoding="UTF-8"?>
    <!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
    <plist version="1.0">
    <dict>
        <key>Label</key>
        <string>com.antigravity.live-wallpaper</string>
        <key>ProgramArguments</key>
        <array>
    \(argsXml)
        </array>
        <key>RunAtLoad</key>
        <true/>
        <key>KeepAlive</key>
        <true/>
        <key>StandardOutPath</key>
        <string>\(logFile)</string>
        <key>StandardErrorPath</key>
        <string>\(logFile)</string>
    </dict>
    </plist>
    """

    let agentDir = NSString(string: "~/Library/LaunchAgents").expandingTildeInPath
    try? FileManager.default.createDirectory(atPath: agentDir, withIntermediateDirectories: true)
    try? plistContent.write(toFile: plistFile, atomically: true, encoding: .utf8)
    _ = Process.launchedProcess(launchPath: "/bin/launchctl", arguments: ["load", "-w", plistFile])
    print("Installed and started live wallpaper service (LaunchAgent).")
}

func uninstallService() {
    _ = Process.launchedProcess(launchPath: "/bin/launchctl", arguments: ["unload", "-w", plistFile])
    try? FileManager.default.removeItem(atPath: plistFile)
    stopRunning()
    print("Uninstalled live wallpaper system service.")
}

// MARK: - CLI Parsing

var isDaemon = false
var isMuted = true
var volume: Float = 1.0
var interval: Double = -1
var perSpace = false
var shuffle = false
var rawSources: [String] = []
var isServiceCommand = false
var serviceAction = ""

let rawArgs = Array(CommandLine.arguments.dropFirst())
var index = 0

while index < rawArgs.count {
    let arg = rawArgs[index]
    switch arg {
    case "-d", "--daemon", "daemon":
        isDaemon = true
    case "-a", "--audio", "--unmute":
        isMuted = false
    case "-m", "--mute":
        isMuted = true
    case "-v", "--volume":
        if index + 1 < rawArgs.count, let v = Float(rawArgs[index + 1]) {
            volume = max(0.0, min(1.0, v > 1.0 ? v / 100.0 : v))
            isMuted = false
            index += 1
        }
    case "-i", "--interval":
        if index + 1 < rawArgs.count, let sec = Double(rawArgs[index + 1]) {
            interval = sec
            index += 1
        }
    case "-p", "--per-space", "--spaces", "spaces":
        perSpace = true
    case "-s", "--shuffle":
        shuffle = true
    case "stop", "--stop":
        stopRunning()
        exit(0)
    case "status", "--status":
        printStatus()
        exit(0)
    case "next", "--next":
        if sendCommand("NEXT") {
            usleep(100_000)
            printStatus()
        }
        exit(0)
    case "prev", "--prev":
        if sendCommand("PREV") {
            usleep(100_000)
            printStatus()
        }
        exit(0)
    case "queue", "list", "--queue", "--list":
        printQueue()
        exit(0)
    case "add", "--add":
        if index + 1 < rawArgs.count {
            let itemToAdd = rawArgs[index + 1]
            if sendCommand("ADD \(itemToAdd)") {
                print("Sent request to add: \(itemToAdd)")
            }
            exit(0)
        } else {
            fputs("Usage: live-wallpaper add <file|directory|url>\n", stderr)
            exit(1)
        }
    case "goto":
        if index + 1 < rawArgs.count, let targetIdx = Int(rawArgs[index + 1]) {
            if sendCommand("GOTO \(targetIdx - 1)") {
                usleep(100_000)
                printStatus()
            }
            exit(0)
        } else {
            fputs("Usage: live-wallpaper goto <1-based index>\n", stderr)
            exit(1)
        }
    case "service":
        isServiceCommand = true
        if index + 1 < rawArgs.count {
            serviceAction = rawArgs[index + 1].lowercased()
            index += 1
        }
    default:
        if !arg.hasPrefix("-") {
            rawSources.append(arg)
        }
    }
    index += 1
}

// Fallback source if none provided
if rawSources.isEmpty {
    rawSources.append("~/Pictures/Wallpapers")
}

// Service Commands
if isServiceCommand {
    if serviceAction == "uninstall" || serviceAction == "remove" {
        uninstallService()
        exit(0)
    } else if serviceAction == "install" || serviceAction == "start" {
        installService(sources: rawSources, interval: interval > 0 ? interval : 60, perSpace: perSpace, isMuted: isMuted, volume: volume, shuffle: shuffle)
        exit(0)
    } else if serviceAction == "status" {
        let isInstalled = FileManager.default.fileExists(atPath: plistFile)
        print("Service installed: \(isInstalled ? "Yes" : "No")")
        printStatus()
        exit(0)
    } else {
        print("Usage: live-wallpaper service [install|uninstall|status]")
        exit(1)
    }
}

// Resolve items
let queueItems = expandSources(rawSources)
if queueItems.isEmpty {
    fputs("Error: No valid video or image sources found in \(rawSources.joined(separator: ", "))\n", stderr)
    exit(1)
}

let effectiveInterval: Double
if interval >= 0 {
    effectiveInterval = interval
} else {
    effectiveInterval = perSpace ? 0.0 : (queueItems.count > 1 ? 60.0 : 0.0)
}

// Daemonize if requested
if isDaemon && ProcessInfo.processInfo.environment["LIVE_WALLPAPER_DAEMON"] != "1" {
    guard let execURL = Bundle.main.executableURL else {
        fputs("Failed to locate executable URL\n", stderr)
        exit(1)
    }
    let daemonArgs = CommandLine.arguments.filter { $0 != "-d" && $0 != "--daemon" && $0 != "daemon" }
    let process = Process()
    process.executableURL = execURL
    process.arguments = Array(daemonArgs.dropFirst())

    var env = ProcessInfo.processInfo.environment
    env["LIVE_WALLPAPER_DAEMON"] = "1"
    process.environment = env

    FileManager.default.createFile(atPath: logFile, contents: nil)
    if let logHandle = FileHandle(forWritingAtPath: logFile) {
        logHandle.seekToEndOfFile()
        process.standardOutput = logHandle
        process.standardError = logHandle
    }

    do {
        try process.run()
        print("Live wallpaper spawned in background (PID \(process.processIdentifier)).")
        print("Queue loaded with \(queueItems.count) item(s).")
        if perSpace {
            print("Mode: Native Per-Desktop Space Pinning (0ms real-time sliding)")
        } else {
            print("Interval: \(effectiveInterval > 0 ? "\(Int(effectiveInterval))s" : "Loop-based")")
        }
        print("Audio: \(isMuted ? "Muted" : "\(Int(volume * 100))%")")
        exit(0)
    } catch {
        fputs("Failed to daemonize process: \(error.localizedDescription)\n", stderr)
        exit(1)
    }
}

// Terminate old instance
if let oldPid = getRunningPID(), oldPid != getpid() {
    kill(oldPid, SIGTERM)
    usleep(150_000)
}

// Write PID
let myPid = String(getpid())
try? myPid.write(toFile: pidFile, atomically: true, encoding: .utf8)

// Signal traps
signal(SIGTERM) { _ in
    let pidFile = NSString(string: "~/.live-wallpaper.pid").expandingTildeInPath
    let stateFile = NSString(string: "~/.live-wallpaper.state").expandingTildeInPath
    let cmdFile = NSString(string: "~/.live-wallpaper.cmd").expandingTildeInPath
    try? FileManager.default.removeItem(atPath: pidFile)
    try? FileManager.default.removeItem(atPath: stateFile)
    try? FileManager.default.removeItem(atPath: cmdFile)
    exit(0)
}
signal(SIGINT) { _ in
    let pidFile = NSString(string: "~/.live-wallpaper.pid").expandingTildeInPath
    let stateFile = NSString(string: "~/.live-wallpaper.state").expandingTildeInPath
    let cmdFile = NSString(string: "~/.live-wallpaper.cmd").expandingTildeInPath
    try? FileManager.default.removeItem(atPath: pidFile)
    try? FileManager.default.removeItem(atPath: stateFile)
    try? FileManager.default.removeItem(atPath: cmdFile)
    exit(0)
}

let app = NSApplication.shared
app.setActivationPolicy(.accessory)
let delegate = WallpaperApp(
    items: queueItems,
    interval: effectiveInterval,
    perSpace: perSpace,
    isMuted: isMuted,
    volume: volume,
    shuffle: shuffle
)
app.delegate = delegate
app.run()

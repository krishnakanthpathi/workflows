import Cocoa
import AVFoundation

// MARK: - App Delegate & Queue Engine

class WallpaperApp: NSObject, NSApplicationDelegate {
    static var shared: WallpaperApp?

    var renderers: [ScreenRenderer] = []
    var spaceWindows: [SpaceWallpaperWindow] = []
    var items: [QueueItem] = []
    var screensaverItems: [QueueItem] = []
    var currentIndex: Int = 0
    let interval: Double
    let perSpace: Bool
    let isMuted: Bool
    let volume: Float
    let shuffleQueue: Bool
    let screensaverIdle: Double?

    var rotationTimer: Timer?
    var sigusr1Source: DispatchSourceSignal?
    var lastSpaceIndex: Int = -1

    init(
        items: [QueueItem],
        screensaverItems: [QueueItem] = [],
        interval: Double,
        perSpace: Bool,
        isMuted: Bool,
        volume: Float,
        shuffle: Bool,
        screensaverIdle: Double? = nil
    ) {
        self.items = items
        self.screensaverItems = screensaverItems
        self.interval = interval
        self.perSpace = perSpace
        self.isMuted = isMuted
        self.volume = volume
        self.shuffleQueue = shuffle
        self.screensaverIdle = screensaverIdle
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

        // Configure screensaver if idle threshold set
        if let idle = screensaverIdle, idle > 0 {
            let ssItems = screensaverItems.isEmpty ? items : screensaverItems
            ScreensaverManager.shared.configure(items: ssItems, isMuted: isMuted, volume: volume, idleThreshold: idle)
            ScreensaverManager.shared.startIdleMonitoring()
        }

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
            pinWindowToSpace(windowNumber: wid, spaceID: spaceID, allSpaceIDs: spaceIDs)

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
            items: items,
            screensaverIdle: screensaverIdle
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
        case "SCREENSAVER":
            ScreensaverManager.shared.activate()
        default:
            nextWallpaper()
        }
    }
}

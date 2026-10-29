import Cocoa
import AVFoundation
import AVKit
import IOKit

// MARK: - System Idle Detection

func getSystemIdleTime() -> Double {
    let entry = IOServiceGetMatchingService(kIOMainPortDefault, IOServiceMatching("IOHIDSystem"))
    guard entry != 0 else { return 0 }
    defer { IOObjectRelease(entry) }
    var unmanagedDict: Unmanaged<CFMutableDictionary>?
    if IORegistryEntryCreateCFProperties(entry, &unmanagedDict, kCFAllocatorDefault, 0) == KERN_SUCCESS,
       let dict = unmanagedDict?.takeRetainedValue() as? [String: Any],
       let nanoseconds = dict["HIDIdleTime"] as? Int64 {
        return Double(nanoseconds) / 1_000_000_000.0
    }
    return 0
}

// MARK: - Screensaver Window

class ScreensaverWindow {
    let window: NSWindow
    let containerView: NSView
    let playerView: AVPlayerView
    let imageLayer: CALayer
    let timeLabel: NSTextField
    let dateLabel: NSTextField
    let shadowHost: NSView
    var player: AVQueuePlayer?
    var looper: AVPlayerLooper?
    var clockTimer: Timer?

    init(screen: NSScreen) {
        window = NSWindow(
            contentRect: screen.frame,
            styleMask: [.borderless],
            backing: .buffered,
            defer: false,
            screen: screen
        )

        window.level = .screenSaver
        window.collectionBehavior = [.canJoinAllSpaces, .stationary, .fullScreenAuxiliary]
        window.ignoresMouseEvents = false
        window.isOpaque = true
        window.backgroundColor = .black
        window.hasShadow = false
        window.alphaValue = 0.0

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

        // Frosted Glass HUD Capsule
        let cardWidth: CGFloat = 380
        let cardHeight: CGFloat = 145
        let cardX = (screen.frame.width - cardWidth) / 2
        let cardY = screen.frame.height * 0.65 - (cardHeight / 2)
        let cardFrame = NSRect(x: cardX, y: cardY, width: cardWidth, height: cardHeight)

        shadowHost = NSView(frame: cardFrame)
        shadowHost.wantsLayer = true
        shadowHost.autoresizingMask = [.minXMargin, .maxXMargin, .minYMargin, .maxYMargin]
        shadowHost.shadow = {
            let s = NSShadow()
            s.shadowBlurRadius = 32
            s.shadowColor = NSColor.black.withAlphaComponent(0.45)
            s.shadowOffset = NSSize(width: 0, height: -8)
            return s
        }()

        let glassView = NSVisualEffectView(frame: NSRect(origin: .zero, size: cardFrame.size))
        glassView.material = .hudWindow
        glassView.blendingMode = .withinWindow
        glassView.state = .active
        glassView.wantsLayer = true
        glassView.layer?.cornerRadius = 28
        glassView.layer?.masksToBounds = true
        glassView.layer?.borderColor = NSColor(white: 1.0, alpha: 0.22).cgColor
        glassView.layer?.borderWidth = 1.0

        // Specular gradient reflection
        let gradient = CAGradientLayer()
        gradient.frame = NSRect(origin: .zero, size: cardFrame.size)
        gradient.colors = [
            NSColor(white: 1.0, alpha: 0.15).cgColor,
            NSColor(white: 1.0, alpha: 0.02).cgColor
        ]
        gradient.startPoint = CGPoint(x: 0.5, y: 0.0)
        gradient.endPoint = CGPoint(x: 0.5, y: 1.0)
        glassView.layer?.addSublayer(gradient)

        timeLabel = NSTextField(labelWithString: "")
        timeLabel.font = NSFont.monospacedDigitSystemFont(ofSize: 64, weight: .light)
        timeLabel.textColor = NSColor(white: 1.0, alpha: 0.95)
        timeLabel.alignment = .center
        timeLabel.isBordered = false
        timeLabel.drawsBackground = false
        timeLabel.isBezeled = false
        timeLabel.isEditable = false
        timeLabel.frame = NSRect(x: 0, y: 48, width: cardWidth, height: 75)
        timeLabel.wantsLayer = true
        timeLabel.shadow = {
            let s = NSShadow()
            s.shadowBlurRadius = 12
            s.shadowColor = NSColor.black.withAlphaComponent(0.4)
            s.shadowOffset = NSSize(width: 0, height: -2)
            return s
        }()

        dateLabel = NSTextField(labelWithString: "")
        dateLabel.font = NSFont.systemFont(ofSize: 15, weight: .medium)
        dateLabel.textColor = NSColor(white: 1.0, alpha: 0.78)
        dateLabel.alignment = .center
        dateLabel.isBordered = false
        dateLabel.drawsBackground = false
        dateLabel.isBezeled = false
        dateLabel.isEditable = false
        dateLabel.frame = NSRect(x: 0, y: 22, width: cardWidth, height: 24)
        dateLabel.wantsLayer = true
        dateLabel.shadow = {
            let s = NSShadow()
            s.shadowBlurRadius = 8
            s.shadowColor = NSColor.black.withAlphaComponent(0.4)
            s.shadowOffset = NSSize(width: 0, height: -1)
            return s
        }()

        glassView.addSubview(timeLabel)
        glassView.addSubview(dateLabel)
        shadowHost.addSubview(glassView)

        containerView.layer?.addSublayer(imageLayer)
        containerView.addSubview(playerView)
        containerView.addSubview(shadowHost)
        window.contentView = containerView
    }

    func show(item: QueueItem, isMuted: Bool, volume: Float) {
        updateClock()
        clockTimer = Timer.scheduledTimer(withTimeInterval: 1.0, repeats: true) { [weak self] _ in
            self?.updateClock()
        }

        if item.type == .image {
            if let url = item.url, let img = NSImage(contentsOf: url) {
                cleanupVideo()
                imageLayer.contents = img
                imageLayer.opacity = 1.0
                playerView.layer?.opacity = 0.0
            }
        } else if let url = item.url {
            cleanupVideo()
            let playerItem = AVPlayerItem(url: url)
            let qPlayer = AVQueuePlayer(playerItem: playerItem)
            qPlayer.isMuted = isMuted
            qPlayer.volume = volume
            qPlayer.actionAtItemEnd = .none

            self.looper = AVPlayerLooper(player: qPlayer, templateItem: playerItem)
            self.player = qPlayer
            playerView.player = qPlayer

            playerView.layer?.opacity = 1.0
            imageLayer.opacity = 0.0
            qPlayer.play()
        }

        window.makeKeyAndOrderFront(nil)
        NSAnimationContext.runAnimationGroup { context in
            context.duration = 0.5
            window.animator().alphaValue = 1.0
        }
    }

    func updateClock() {
        let now = Date()
        let timeFormatter = DateFormatter()
        timeFormatter.timeStyle = .short
        timeLabel.stringValue = timeFormatter.string(from: now)

        let dateFormatter = DateFormatter()
        dateFormatter.dateFormat = "EEEE, MMMM d"
        dateLabel.stringValue = dateFormatter.string(from: now)
    }

    func hide(completion: @escaping () -> Void) {
        clockTimer?.invalidate()
        clockTimer = nil

        NSAnimationContext.runAnimationGroup({ context in
            context.duration = 0.3
            window.animator().alphaValue = 0.0
        }, completionHandler: {
            self.cleanupVideo()
            self.window.orderOut(nil)
            completion()
        })
    }

    func cleanupVideo() {
        player?.pause()
        player?.removeAllItems()
        looper = nil
        player = nil
        playerView.player = nil
    }

    func teardown() {
        clockTimer?.invalidate()
        clockTimer = nil
        cleanupVideo()
        window.orderOut(nil)
    }
}

// MARK: - Screensaver Manager

class ScreensaverManager {
    static let shared = ScreensaverManager()

    var isRunning = false
    var windows: [ScreensaverWindow] = []
    var items: [QueueItem] = []
    var isMuted: Bool = true
    var volume: Float = 1.0
    var idleThreshold: Double?
    var idleCheckTimer: Timer?
    var eventMonitors: [Any] = []
    var initialMousePos: NSPoint?
    var isStandalone = false

    func configure(items: [QueueItem], isMuted: Bool, volume: Float, idleThreshold: Double?) {
        self.items = items
        self.isMuted = isMuted
        self.volume = volume
        self.idleThreshold = idleThreshold
    }

    func startIdleMonitoring() {
        guard let threshold = idleThreshold, threshold > 0 else { return }
        idleCheckTimer?.invalidate()
        idleCheckTimer = Timer.scheduledTimer(withTimeInterval: 2.0, repeats: true) { [weak self] _ in
            self?.checkIdleTime()
        }
    }

    func checkIdleTime() {
        guard let threshold = idleThreshold, threshold > 0 else { return }
        let idleSec = getSystemIdleTime()
        if idleSec >= threshold && !isRunning {
            activate()
        }
    }

    func activate() {
        guard !isRunning, !items.isEmpty else { return }
        isRunning = true
        initialMousePos = NSEvent.mouseLocation

        // Build screensaver windows for each monitor
        windows = NSScreen.screens.map { ScreensaverWindow(screen: $0) }
        for (idx, win) in windows.enumerated() {
            let item = items[idx % items.count]
            win.show(item: item, isMuted: isMuted, volume: volume)
        }

        setupWakeMonitors()
        print("SCREENSAVER_ACTIVATED: Showing on \(windows.count) display(s)")
        fflush(stdout)
    }

    func dismiss() {
        guard isRunning else { return }
        removeWakeMonitors()

        let group = DispatchGroup()
        for win in windows {
            group.enter()
            win.hide {
                group.leave()
            }
        }

        group.notify(queue: .main) { [weak self] in
            guard let self = self else { return }
            self.windows.removeAll()
            self.isRunning = false
            print("SCREENSAVER_DISMISSED: Resumed desktop workspace")
            fflush(stdout)

            if self.isStandalone {
                exit(0)
            }
        }
    }

    func setupWakeMonitors() {
        removeWakeMonitors()

        // Global events: mouse clicks, keystrokes
        let global = NSEvent.addGlobalMonitorForEvents(matching: [.keyDown, .leftMouseDown, .rightMouseDown, .otherMouseDown, .scrollWheel, .mouseMoved]) { [weak self] event in
            if event.type == .mouseMoved {
                if let initial = self?.initialMousePos {
                    let cur = NSEvent.mouseLocation
                    let dx = abs(cur.x - initial.x)
                    let dy = abs(cur.y - initial.y)
                    if dx > 15 || dy > 15 {
                        self?.dismiss()
                    }
                }
            } else {
                self?.dismiss()
            }
        }
        if let g = global { eventMonitors.append(g) }

        // Local events
        let local = NSEvent.addLocalMonitorForEvents(matching: [.keyDown, .leftMouseDown, .rightMouseDown, .otherMouseDown, .scrollWheel, .mouseMoved]) { [weak self] event in
            if event.type == .mouseMoved {
                if let initial = self?.initialMousePos {
                    let cur = NSEvent.mouseLocation
                    let dx = abs(cur.x - initial.x)
                    let dy = abs(cur.y - initial.y)
                    if dx > 15 || dy > 15 {
                        self?.dismiss()
                    }
                }
            } else {
                self?.dismiss()
            }
            return nil
        }
        if let l = local { eventMonitors.append(l) }
    }

    func removeWakeMonitors() {
        for m in eventMonitors {
            NSEvent.removeMonitor(m)
        }
        eventMonitors.removeAll()
    }

    func runStandalone(items: [QueueItem], isMuted: Bool, volume: Float) {
        self.isStandalone = true
        self.items = items
        self.isMuted = isMuted
        self.volume = volume

        let app = NSApplication.shared
        app.setActivationPolicy(.accessory)
        activate()
        app.run()
    }
}

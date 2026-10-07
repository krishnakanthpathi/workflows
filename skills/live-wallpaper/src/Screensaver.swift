import Cocoa
import AVFoundation
import AVKit
import IOKit
import IOKit.pwr_mgt
import CoreText
import QuartzCore

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

// MARK: - macOS Dock-Style Frosted Glass Clock

class DockGlassClockView: NSView {
    let glassEffect: NSVisualEffectView
    let specGradient: CAGradientLayer
    let timeLabel: NSTextField
    let dateLabel: NSTextField
    let lockBadge: NSTextField?
    let isLockArmed: Bool

    init(frame: NSRect, isLockArmed: Bool = false) {
        self.isLockArmed = isLockArmed
        glassEffect = NSVisualEffectView(frame: NSRect(origin: .zero, size: frame.size))
        glassEffect.material = .hudWindow
        glassEffect.blendingMode = .withinWindow
        glassEffect.state = .active
        glassEffect.alphaValue = 0.38 // Highly transparent, airy frosted glass
        glassEffect.wantsLayer = true
        glassEffect.layer?.cornerRadius = 34
        glassEffect.layer?.masksToBounds = true
        glassEffect.layer?.borderColor = NSColor(white: 1.0, alpha: 0.16).cgColor
        glassEffect.layer?.borderWidth = 1.0

        // Dock-like subtle top specular light reflection
        specGradient = CAGradientLayer()
        specGradient.frame = NSRect(origin: .zero, size: frame.size)
        specGradient.colors = [
            NSColor(white: 1.0, alpha: 0.10).cgColor,
            NSColor(white: 1.0, alpha: 0.01).cgColor
        ]
        specGradient.startPoint = CGPoint(x: 0.5, y: 0.0)
        specGradient.endPoint = CGPoint(x: 0.5, y: 1.0)
        glassEffect.layer?.addSublayer(specGradient)

        let timeY: CGFloat = isLockArmed ? 58 : 52
        let dateY: CGFloat = isLockArmed ? 28 : 22

        timeLabel = NSTextField(labelWithString: "")
        timeLabel.frame = NSRect(x: 0, y: timeY, width: frame.width, height: 86)
        timeLabel.font = NSFont.monospacedDigitSystemFont(ofSize: 74, weight: .light)
        timeLabel.textColor = NSColor(white: 1.0, alpha: 0.98)
        timeLabel.alignment = .center
        timeLabel.isBordered = false
        timeLabel.drawsBackground = false
        timeLabel.isBezeled = false
        timeLabel.isEditable = false
        timeLabel.wantsLayer = true
        timeLabel.shadow = {
            let s = NSShadow()
            s.shadowBlurRadius = 10
            s.shadowColor = NSColor.black.withAlphaComponent(0.5)
            s.shadowOffset = NSSize(width: 0, height: -2)
            return s
        }()

        dateLabel = NSTextField(labelWithString: "")
        dateLabel.frame = NSRect(x: 0, y: dateY, width: frame.width, height: 26)
        dateLabel.font = NSFont.systemFont(ofSize: 16, weight: .medium)
        dateLabel.textColor = NSColor(white: 1.0, alpha: 0.85)
        dateLabel.alignment = .center
        dateLabel.isBordered = false
        dateLabel.drawsBackground = false
        dateLabel.isBezeled = false
        dateLabel.isEditable = false
        dateLabel.wantsLayer = true
        dateLabel.shadow = {
            let s = NSShadow()
            s.shadowBlurRadius = 8
            s.shadowColor = NSColor.black.withAlphaComponent(0.5)
            s.shadowOffset = NSSize(width: 0, height: -1)
            return s
        }()

        if isLockArmed {
            let badge = NSTextField(labelWithString: "🔒 Lock on Wake Armed")
            badge.frame = NSRect(x: 0, y: 10, width: frame.width, height: 16)
            badge.font = NSFont.systemFont(ofSize: 11, weight: .semibold)
            badge.textColor = NSColor(white: 1.0, alpha: 0.65)
            badge.alignment = .center
            badge.isBordered = false
            badge.drawsBackground = false
            badge.isBezeled = false
            badge.isEditable = false
            self.lockBadge = badge
        } else {
            self.lockBadge = nil
        }

        super.init(frame: frame)
        self.wantsLayer = true
        self.shadow = {
            let s = NSShadow()
            s.shadowBlurRadius = 32
            s.shadowColor = NSColor.black.withAlphaComponent(0.40)
            s.shadowOffset = NSSize(width: 0, height: -8)
            return s
        }()

        self.addSubview(glassEffect)
        self.addSubview(timeLabel)
        self.addSubview(dateLabel)
        if let b = lockBadge {
            self.addSubview(b)
        }
    }

    required init?(coder: NSCoder) { fatalError() }

    func update(time: String, date: String) {
        timeLabel.stringValue = time
        dateLabel.stringValue = date
    }
}

// MARK: - Screensaver Window

class ScreensaverWindow {
    let window: NSWindow
    let containerView: NSView
    let playerView: AVPlayerView
    let imageLayer: CALayer
    let dockGlassClockView: DockGlassClockView
    var player: AVQueuePlayer?
    var looper: AVPlayerLooper?
    var clockTimer: Timer?

    init(screen: NSScreen, isLockArmed: Bool = false) {
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

        // macOS Dock-Style Frosted Glass Clock Capsule (Top Left)
        let cardWidth: CGFloat = 460
        let cardHeight: CGFloat = 160
        let margin: CGFloat = 60
        let cardX = margin
        let cardY = screen.frame.height - cardHeight - margin
        let cardFrame = NSRect(x: cardX, y: cardY, width: cardWidth, height: cardHeight)

        dockGlassClockView = DockGlassClockView(frame: cardFrame, isLockArmed: isLockArmed)
        dockGlassClockView.autoresizingMask = [.maxXMargin, .minYMargin]

        containerView.layer?.addSublayer(imageLayer)
        containerView.addSubview(playerView)
        containerView.addSubview(dockGlassClockView)
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
        let timeString = timeFormatter.string(from: now)

        let dateFormatter = DateFormatter()
        dateFormatter.dateFormat = "EEEE, MMMM d"
        let dateString = dateFormatter.string(from: now)

        dockGlassClockView.update(time: timeString, date: dateString)
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
    var displaySleepAssertionID: IOPMAssertionID = 0
    var activationTime: CFTimeInterval = 0
    var isStandalone = false
    var lockOnWake: Bool = false

    func configure(items: [QueueItem], isMuted: Bool, volume: Float, idleThreshold: Double?, lockOnWake: Bool = false) {
        self.items = items
        self.isMuted = isMuted
        self.volume = volume
        self.idleThreshold = idleThreshold
        self.lockOnWake = lockOnWake
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
        activationTime = CACurrentMediaTime()
        initialMousePos = NSEvent.mouseLocation

        // Prevent macOS from putting display to sleep while custom screensaver is playing
        _ = IOPMAssertionCreateWithName(
            kIOPMAssertionTypePreventUserIdleDisplaySleep as CFString,
            IOPMAssertionLevel(kIOPMAssertionLevelOn),
            "LiveWallpaperScreensaver" as CFString,
            &displaySleepAssertionID
        )

        // Build screensaver windows for each monitor
        windows = NSScreen.screens.map { ScreensaverWindow(screen: $0, isLockArmed: lockOnWake) }
        for (idx, win) in windows.enumerated() {
            let item = items[idx % items.count]
            win.show(item: item, isMuted: isMuted, volume: volume)
        }

        setupWakeMonitors()
        print("SCREENSAVER_ACTIVATED: Showing on \(windows.count) display(s)\(lockOnWake ? " [Lock on Wake Armed]" : "")")
        fflush(stdout)
    }

    func dismiss() {
        guard isRunning else { return }
        removeWakeMonitors()

        if displaySleepAssertionID != 0 {
            IOPMAssertionRelease(displaySleepAssertionID)
            displaySleepAssertionID = 0
        }

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

            if self.lockOnWake {
                lockSystemScreen()
            }

            if self.isStandalone {
                exit(0)
            }
        }
    }

    func setupWakeMonitors() {
        removeWakeMonitors()

        // Global events: mouse clicks, keystrokes
        let global = NSEvent.addGlobalMonitorForEvents(matching: [.keyDown, .leftMouseDown, .rightMouseDown, .otherMouseDown, .scrollWheel, .mouseMoved]) { [weak self] event in
            guard let self = self else { return }
            if CACurrentMediaTime() - self.activationTime < 0.8 { return }

            if event.type == .mouseMoved {
                if let initial = self.initialMousePos {
                    let cur = NSEvent.mouseLocation
                    let dx = abs(cur.x - initial.x)
                    let dy = abs(cur.y - initial.y)
                    if dx > 30 || dy > 30 {
                        self.dismiss()
                    }
                }
            } else {
                self.dismiss()
            }
        }
        if let g = global { eventMonitors.append(g) }

        // Local events
        let local = NSEvent.addLocalMonitorForEvents(matching: [.keyDown, .leftMouseDown, .rightMouseDown, .otherMouseDown, .scrollWheel, .mouseMoved]) { [weak self] event in
            guard let self = self else { return nil }
            if CACurrentMediaTime() - self.activationTime < 0.8 { return nil }

            if event.type == .mouseMoved {
                if let initial = self.initialMousePos {
                    let cur = NSEvent.mouseLocation
                    let dx = abs(cur.x - initial.x)
                    let dy = abs(cur.y - initial.y)
                    if dx > 30 || dy > 30 {
                        self.dismiss()
                    }
                }
            } else {
                self.dismiss()
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

    func runStandalone(items: [QueueItem], isMuted: Bool, volume: Float, lockOnWake: Bool = false) {
        self.isStandalone = true
        self.items = items
        self.isMuted = isMuted
        self.volume = volume
        self.lockOnWake = lockOnWake

        let app = NSApplication.shared
        app.setActivationPolicy(.accessory)
        activate()
        app.run()
    }
}

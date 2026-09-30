import Cocoa
import AVFoundation
import AVKit

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

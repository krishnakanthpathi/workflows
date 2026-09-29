import Cocoa
import AVFoundation
import AVKit

class WallpaperApp: NSObject, NSApplicationDelegate {
    var windows: [NSWindow] = []
    var players: [AVQueuePlayer] = []
    var loopers: [AVPlayerLooper] = []
    let videoURL: URL
    let isMuted: Bool
    let volume: Float

    init(videoURL: URL, isMuted: Bool, volume: Float) {
        self.videoURL = videoURL
        self.isMuted = isMuted
        self.volume = volume
        super.init()
    }

    func applicationDidFinishLaunching(_ notification: Notification) {
        setupScreens()
        NotificationCenter.default.addObserver(
            self,
            selector: #selector(screenParametersChanged),
            name: NSApplication.didChangeScreenParametersNotification,
            object: nil
        )
        print("LIVE_WALLPAPER_ACTIVE:\(videoURL.absoluteString)")
        fflush(stdout)
    }

    @objc func screenParametersChanged() {
        teardownScreens()
        setupScreens()
    }

    func teardownScreens() {
        for player in players {
            player.pause()
            player.removeAllItems()
        }
        for window in windows {
            window.orderOut(nil)
        }
        windows.removeAll()
        players.removeAll()
        loopers.removeAll()
    }

    func setupScreens() {
        for screen in NSScreen.screens {
            setupWindow(for: screen)
        }
    }

    func setupWindow(for screen: NSScreen) {
        let window = NSWindow(
            contentRect: screen.frame,
            styleMask: [.borderless],
            backing: .buffered,
            defer: false,
            screen: screen
        )

        // Desktop icons sit at layer -2147483603.
        // - 1 places the window at layer -2147483604, behind desktop icons.
        let iconLevel = Int(CGWindowLevelForKey(.desktopIconWindow))
        window.level = NSWindow.Level(rawValue: iconLevel - 1)

        window.collectionBehavior = [.canJoinAllSpaces, .stationary, .ignoresCycle]
        window.ignoresMouseEvents = true
        window.isOpaque = true
        window.backgroundColor = .black
        window.hasShadow = false

        let playerItem = AVPlayerItem(url: videoURL)
        let player = AVQueuePlayer(playerItem: playerItem)
        player.isMuted = isMuted
        player.volume = volume
        player.actionAtItemEnd = .none

        // Handle looping via AVPlayerLooper with fallback notification
        let looper = AVPlayerLooper(player: player, templateItem: playerItem)
        loopers.append(looper)

        NotificationCenter.default.addObserver(
            forName: AVPlayerItem.didPlayToEndTimeNotification,
            object: playerItem,
            queue: .main
        ) { [weak player] _ in
            player?.seek(to: .zero)
            player?.play()
        }

        let playerView = AVPlayerView(frame: NSRect(origin: .zero, size: screen.frame.size))
        playerView.player = player
        playerView.controlsStyle = .none
        playerView.videoGravity = .resizeAspectFill
        playerView.autoresizingMask = [.width, .height]

        window.contentView = playerView
        window.orderFrontRegardless()

        player.play()

        windows.append(window)
        players.append(player)
    }
}

let pidFile = NSString(string: "~/.live-wallpaper.pid").expandingTildeInPath
let stateFile = NSString(string: "~/.live-wallpaper.state").expandingTildeInPath
let logFile = NSString(string: "~/.live-wallpaper.log").expandingTildeInPath
let plistFile = NSString(string: "~/Library/LaunchAgents/com.antigravity.live-wallpaper.plist").expandingTildeInPath

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

func stopRunning() {
    if let pid = getRunningPID() {
        kill(pid, SIGTERM)
        try? FileManager.default.removeItem(atPath: pidFile)
        try? FileManager.default.removeItem(atPath: stateFile)
        print("Stopped live wallpaper (PID \(pid)).")
    } else {
        print("No live wallpaper currently running.")
    }
}

func printStatus() {
    if let pid = getRunningPID() {
        let currentVideo = (try? String(contentsOfFile: stateFile, encoding: .utf8))?.trimmingCharacters(in: .whitespacesAndNewlines) ?? "unknown"
        print("Live wallpaper is running (PID \(pid))")
        print("Active source: \(currentVideo)")
    } else {
        print("Live wallpaper is not running.")
    }
}

func installService(videoSource: String, isMuted: Bool, volume: Float) {
    let binPath = "/Users/krishnakanth/.local/bin/live-wallpaper"
    let argsXml: String
    if isMuted {
        argsXml = """
                <string>\(binPath)</string>
                <string>\(videoSource)</string>
        """
    } else {
        argsXml = """
                <string>\(binPath)</string>
                <string>--audio</string>
                <string>--volume</string>
                <string>\(Int(volume * 100))</string>
                <string>\(videoSource)</string>
        """
    }

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
    print("It will now start automatically whenever your Mac boots/logs in.")
}

func uninstallService() {
    _ = Process.launchedProcess(launchPath: "/bin/launchctl", arguments: ["unload", "-w", plistFile])
    try? FileManager.default.removeItem(atPath: plistFile)
    stopRunning()
    print("Uninstalled live wallpaper system service.")
}

// CLI Argument Parsing
var isDaemon = false
var isMuted = true
var volume: Float = 1.0
var rawSource = ""
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
    case "stop", "--stop":
        stopRunning()
        exit(0)
    case "status", "--status":
        printStatus()
        exit(0)
    case "service":
        isServiceCommand = true
        if index + 1 < rawArgs.count {
            serviceAction = rawArgs[index + 1].lowercased()
            index += 1
        }
    default:
        if !arg.hasPrefix("-") && rawSource.isEmpty {
            rawSource = arg
        }
    }
    index += 1
}

// Resolve video source (presets, streaming URLs, local files)
var targetSource = NSString(string: "~/Desktop/naruto-kurama.mp4").expandingTildeInPath
if !rawSource.isEmpty {
    if rawSource == "naruto" {
        targetSource = NSString(string: "~/Desktop/naruto-kurama.mp4").expandingTildeInPath
    } else if rawSource == "aot" || rawSource == "eren" {
        targetSource = NSString(string: "~/Desktop/aot-eren-yeager.mp4").expandingTildeInPath
    } else {
        targetSource = rawSource
    }
}

// Handle Service actions
if isServiceCommand {
    if serviceAction == "uninstall" || serviceAction == "remove" {
        uninstallService()
        exit(0)
    } else if serviceAction == "install" || serviceAction == "start" {
        installService(videoSource: targetSource, isMuted: isMuted, volume: volume)
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

// Parse Video URL (Local or Streaming)
let videoURL: URL
if targetSource.hasPrefix("http://") || targetSource.hasPrefix("https://") {
    guard let url = URL(string: targetSource) else {
        fputs("Error: Invalid streaming URL: \(targetSource)\n", stderr)
        exit(1)
    }
    videoURL = url
} else {
    let localPath = NSString(string: targetSource).expandingTildeInPath
    guard FileManager.default.fileExists(atPath: localPath) else {
        fputs("Error: Video file not found at \(localPath)\n", stderr)
        exit(1)
    }
    videoURL = URL(fileURLWithPath: localPath)
}

// Handle Daemon Backgrounding
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
        print("Active source: \(videoURL.absoluteString)")
        print("Audio: \(isMuted ? "Muted" : "Active (\(Int(volume * 100))%)")")
        exit(0)
    } catch {
        fputs("Failed to daemonize process: \(error.localizedDescription)\n", stderr)
        exit(1)
    }
}

// Terminate existing running instance if starting new
if let oldPid = getRunningPID(), oldPid != getpid() {
    kill(oldPid, SIGTERM)
    usleep(100_000)
}

// Write PID and State
let myPid = String(getpid())
try? myPid.write(toFile: pidFile, atomically: true, encoding: .utf8)
let stateInfo = "\(videoURL.absoluteString) | Audio: \(isMuted ? "Muted" : "\(Int(volume * 100))%")"
try? stateInfo.write(toFile: stateFile, atomically: true, encoding: .utf8)

// Signal traps for clean exit
signal(SIGTERM) { _ in
    let pidFile = NSString(string: "~/.live-wallpaper.pid").expandingTildeInPath
    let stateFile = NSString(string: "~/.live-wallpaper.state").expandingTildeInPath
    try? FileManager.default.removeItem(atPath: pidFile)
    try? FileManager.default.removeItem(atPath: stateFile)
    exit(0)
}
signal(SIGINT) { _ in
    let pidFile = NSString(string: "~/.live-wallpaper.pid").expandingTildeInPath
    let stateFile = NSString(string: "~/.live-wallpaper.state").expandingTildeInPath
    try? FileManager.default.removeItem(atPath: pidFile)
    try? FileManager.default.removeItem(atPath: stateFile)
    exit(0)
}

let app = NSApplication.shared
app.setActivationPolicy(.accessory)
let delegate = WallpaperApp(videoURL: videoURL, isMuted: isMuted, volume: volume)
app.delegate = delegate
app.run()

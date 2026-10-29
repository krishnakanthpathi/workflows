import Cocoa
import Foundation

// MARK: - CLI Parsing & Execution Entry Point

var isDaemon = false
var isMuted = true
var volume: Float = 1.0
var interval: Double = -1
var perSpace = false
var shuffle = false
var screensaverIdle: Double? = nil
var rawSources: [String] = []
var screensaverSources: [String] = []
var isServiceCommand = false
var serviceAction = ""
var isScreensaverCommand = false

let rawArgs = Array(CommandLine.arguments.dropFirst())
var index = 0

func printHelp() {
    let help = """
    macOS Live Wallpaper & Screensaver Engine

    USAGE:
      live-wallpaper [OPTIONS] [SOURCES...]
      live-wallpaper <COMMAND>

    COMMANDS:
      screensaver [SOURCES...]    Launch fullscreen screensaver overlay immediately
      status                     Print running instance status and playback mode
      queue, list                Display current queue with space bindings
      next                       Advance to next wallpaper
      prev                       Return to previous wallpaper
      goto <index>               Jump directly to 1-based queue index
      add <file|dir|url>         Append new media to running queue
      stop                       Terminate running background engine
      service <install|uninstall|status>  Manage LaunchAgent auto-start service

    OPTIONS:
      -d, --daemon               Run wallpaper engine in the background
      -p, --per-space            Pin distinct wallpapers to virtual spaces (0ms delay)
      -a, --audio, --unmute      Enable audio playback (default: muted)
      -v, --volume <0-100>       Set audio volume percentage (e.g. 35)
      -i, --interval <seconds>   Queue rotation interval in seconds (default: 60)
      -s, --shuffle              Randomize wallpaper playback order
      --screensaver [seconds]    Enable auto-screensaver on idle (default: 180s)
      --screensaver-source <src> Dedicated media path or directory for screensaver
      -h, --help                 Display this help menu
    """
    print(help)
}

while index < rawArgs.count {
    let arg = rawArgs[index]
    switch arg {
    case "-h", "--help", "help":
        printHelp()
        exit(0)
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
    case "--screensaver", "--screensaver-idle":
        if index + 1 < rawArgs.count, let sec = Double(rawArgs[index + 1]) {
            screensaverIdle = sec
            index += 1
        } else {
            screensaverIdle = 180.0 // Default 3 mins
        }
    case "--screensaver-source":
        if index + 1 < rawArgs.count {
            screensaverSources.append(rawArgs[index + 1])
            index += 1
        }
    case "screensaver", "--screensaver-test":
        isScreensaverCommand = true
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
        installService(
            sources: rawSources,
            interval: interval > 0 ? interval : 60,
            perSpace: perSpace,
            isMuted: isMuted,
            volume: volume,
            shuffle: shuffle,
            screensaverIdle: screensaverIdle
        )
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

// Screensaver Standalone / Trigger Command
if isScreensaverCommand {
    if getRunningPID() != nil && rawSources == ["~/Pictures/Wallpapers"] {
        // Trigger screensaver on running daemon
        if sendCommand("SCREENSAVER") {
            print("Triggered screensaver on active live wallpaper daemon.")
            exit(0)
        }
    }
    // Launch standalone screensaver
    let ssSources = screensaverSources.isEmpty ? rawSources : screensaverSources
    let items = expandSources(ssSources)
    if items.isEmpty {
        fputs("Error: No valid screensaver items found in \(ssSources.joined(separator: ", "))\n", stderr)
        exit(1)
    }
    ScreensaverManager.shared.runStandalone(items: items, isMuted: isMuted, volume: volume)
    exit(0)
}

// Resolve items
let queueItems = expandSources(rawSources)
if queueItems.isEmpty {
    fputs("Error: No valid video or image sources found in \(rawSources.joined(separator: ", "))\n", stderr)
    exit(1)
}

let ssItems = screensaverSources.isEmpty ? [] : expandSources(screensaverSources)

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
        if let ss = screensaverIdle, ss > 0 {
            print("Screensaver auto-trigger: \(Int(ss))s idle")
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
    screensaverItems: ssItems,
    interval: effectiveInterval,
    perSpace: perSpace,
    isMuted: isMuted,
    volume: volume,
    shuffle: shuffle,
    screensaverIdle: screensaverIdle
)
app.delegate = delegate
app.run()

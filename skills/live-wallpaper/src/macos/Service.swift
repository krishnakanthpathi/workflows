import Foundation

// MARK: - LaunchAgent Service Management

func installService(sources: [String], interval: Double, perSpace: Bool, isMuted: Bool, volume: Float, shuffle: Bool, screensaverIdle: Double?) {
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
    if let ss = screensaverIdle, ss > 0 {
        args.append(contentsOf: ["--screensaver", "\(Int(ss))"])
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

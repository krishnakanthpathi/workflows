import Foundation

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
        if let ss = state.screensaverIdle, ss > 0 {
            print("Screensaver auto-trigger: \(Int(ss))s idle")
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
    let ssDesc = (state.screensaverIdle ?? 0) > 0 ? " | Screensaver: \(Int(state.screensaverIdle!))s idle" : ""
    print("Live Wallpaper Queue (\(state.items.count) items):")
    print("\(modeDesc)\(ssDesc) | Audio: \(state.isMuted ? "Muted" : "\(Int(state.volume * 100))%")\n")

    for (i, item) in state.items.enumerated() {
        let marker = (i == state.currentIndex) ? "-> [ACTIVE]" : "           "
        let spaceTag = state.perSpace ? " (Desktop \(i + 1))" : ""
        print(String(format: "%@ %2d. [%@] %@%@", marker, i + 1, item.type.rawValue.uppercased(), item.displayName, spaceTag))
    }
}

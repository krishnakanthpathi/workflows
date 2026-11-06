---
name: native-assistant
description: "Cross-platform workstation automation MCP server for macOS and Windows. Exposes 49 native OS capabilities including volume, window management, active application focus, keyboard/scroll input simulation, filesystem operations, system state, notification/dialogs, Wi-Fi control, and Finder/Explorer reveals."
version: 1.2.0
author: Krishna Kanth
license: MIT
platforms: [macos, windows]
metadata:
  icon: "🖥️"
hermes:
  tags: [macos, windows, automation, mcp, fastmcp, system, finder, window-manager, input]
---

# 🖥️ Native Assistant MCP (`native-assistant-mcp`)

Cross-platform workstation and system automation engine providing 49 native OS capabilities for macOS and Windows via FastMCP stdio transport.

* **Repository**: [native-assistant-mcp](https://github.com/krishnakanthpathi/native-assistant-mcp)
* **Local Root**: [`/Users/krishnakanth/Projects/native-assistant-mcp`](file:///Users/krishnakanth/Projects/native-assistant-mcp)
* **MCP Identifier**: `native-assistant-mcp`

---

## ⚡ Tool Categories & Capabilities

### 1. Volume & Audio Control
* `volume_set(level: float)`: Set system volume (0–100%). Clamps gracefully.
* `get_volume()`: Retrieve current system volume percentage and mute state.

### 2. Active Window & Application Focus
* `get_active_window()`: Retrieve the frontmost application name and window title.
* `list_applications()`: Enumerate installed GUI applications from standard app bundles.
* `open_application(app: str)`: Launch or bring a GUI application to the front.
* `close_application(app: str)`: Gracefully terminate a running application.

### 3. Window & Mission Control Management
* `list_apps()`: List non-background running processes.
* `list_windows()`: Enumerate all on-screen visible windows with titles and geometries.
* `focus_app(bundle_id: str)`: Bring application to front by bundle ID or process name.
* `focus_window(id: int)`: Focus a specific window ID.
* `move_window(id: int, x: int, y: int)`: Reposition window on desktop.
* `resize_window(id: int, w: int, h: int)`: Resize window dimensions.
* `set_space(index: int)`: Switch Mission Control space / desktop.
* `list_spaces()`: Enumerate all Mission Control spaces, displays, active space, and associated window IDs.

### 4. Finder & Explorer Integration
* `reveal_in_finder(path: str)`: Reveal file or folder in macOS Finder (`open -R`).
* `spotlight_search(query: str, limit: int = 20)`: Query local Spotlight index via `mdfind`.
* `get_finder_selection()`: Retrieve paths currently selected in the frontmost Finder window.
* `reveal_in_explorer(path: str)`: Reveal file or directory in Windows File Explorer (Windows).

### 5. System State & Hardware
* `set_dark_mode(enable: bool)`: Toggle system dark mode on/off.
* `get_system_stats()`: Retrieve battery status, CPU load, and disk utilization.
* `get_date_time()`: Return local time, timezone, epoch milliseconds, and ISO timestamp.
* `lock_screen()`: Lock display immediately (`pmset displaysleepnow`).
* `system_power(action: str)`: Trigger system power states (`sleep`, `restart`, `shutdown`).
* `empty_trash()`: Empty macOS Trash / Windows Recycle Bin.
* `say_speech(text: str)`: Text-to-speech engine.
* `notify(title: str, body: str)`: Display native desktop notification banner.
* `prompt_user(message: str)`: Display interactive modal dialog.
* `wifi_control(action: str)`: Inspect or toggle Wi-Fi status (`status`, `on`, `off`).
* `clipboard_read(type: str = "text")`: Read clipboard content (`text`, `image`, `file_urls`, `rtf`).
* `clipboard_write(content_type: str, value: str)`: Write typed content to system clipboard.
* `take_screenshot(target: str = "screen")`: Capture full screen, window, or region.

### 6. Input Automation (Keyboard & Scroll)
* `mouse_scroll(dx: int, dy: int)`: Scroll mouse horizontally or vertically.
* `key_press(key: str, modifiers: list = [])`: Trigger key press with modifier keys.
* `type_text(text: str)`: Simulate typing text stream.
* `keystroke_action(action: str, text: str)`: Execute keystroke shortcuts.
* `media_control(action: str, player: str = "Music")`: Control media playback (`play`, `pause`, `next`, `prev`).

### 7. Filesystem Operations
* `fs_read(path: str, encoding: str = "utf8")`: Read file contents.
* `fs_read_many(paths: list[str])`: Read multiple files in a single call.
* `fs_write(path: str, content: str, encoding: str = "utf8", mode: str = "create")`: Write file (text/base64).
* `fs_edit(path: str, find: str, replace: str)`: Targeted find-and-replace text editing.
* `fs_write_pdf(path: str, text: str)`: Generate formatted PDF document.
* `fs_list(path: str, recursive: bool = false)`: List directory entries.
* `fs_stat(path: str)`: Retrieve file size, timestamps, and permissions.
* `fs_copy(src: str, dst: str)`: Copy file or directory recursively.
* `fs_move(src: str, dst: str)`: Move or rename file or directory.
* `fs_make_dir(path: str)`: Create directory hierarchy (`mkdir -p`).
* `fs_delete(path: str)`: Delete file or directory.

### 8. Scripting & Integration
* `wait_ms(ms: int)`: Non-blocking sleep for milliseconds (capped at 60000 ms).
* `run_applescript(script: str)`: Execute arbitrary AppleScript string (macOS).
* `run_powershell(script: str)`: Execute arbitrary PowerShell command (Windows).
* `terminal(action: str, ...)`: Terminal/iTerm session inspection and interaction.

---

## 🛠️ Usage Patterns

### Calling via Antigravity MCP Bridge
```markdown
call_mcp_tool native-assistant-mcp reveal_in_finder {"path": "/Users/krishnakanth/Desktop/Report.pdf"}
call_mcp_tool native-assistant-mcp get_system_stats {}
call_mcp_tool native-assistant-mcp spotlight_search {"query": "kind:image modified:today", "limit": 10}
```

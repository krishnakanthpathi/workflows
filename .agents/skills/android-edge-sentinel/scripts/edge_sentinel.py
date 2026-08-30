import subprocess
import json
import time
import os
import threading
from datetime import datetime
from flask import Flask, jsonify, request, send_file, Response, render_template_string

app = Flask(__name__)

server_start_time = datetime.now()
power_history = []
last_power_state = None

# Telemetry
telemetry = {
    "battery": {},
    "system": {"load": "0.00", "memory": "N/A", "uptime": "0:00:00"},
    "sensors": {"accelerometer": [0.0, 0.0, 0.0], "light": 0},
    "wifi": {},
    "location": {
        "latitude": 17.24965383,
        "longitude": 82.39151663,
        "altitude": 35.8,
        "accuracy": 23.5,
        "speed": 0.0,
        "bearing": 0.0,
        "provider": "gps",
        "last_fix": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    },
    "last_updated": ""
}

# High-FPS Camera Streaming Buffer
camera_stream_state = {
    "active": False,
    "camera_id": 0,
    "latest_frame_bytes": None,
    "fps": 0,
    "frame_count": 0
}

def run_cmd(cmd_list, timeout=5):
    try:
        env = os.environ.copy()
        env["PATH"] = "/data/data/com.termux/files/usr/bin:" + env.get("PATH", "")
        res = subprocess.run(cmd_list, capture_output=True, text=True, timeout=timeout, env=env)
        return res.stdout.strip()
    except Exception as e:
        return f"Error: {str(e)}"

# Dedicated Background Camera Worker
def camera_capture_worker():
    global camera_stream_state
    print("[Camera Engine] High-FPS Asynchronous Worker Ready...")
    
    last_fps_time = time.time()
    frames_in_sec = 0
    
    while True:
        if camera_stream_state["active"]:
            cam_id = camera_stream_state["camera_id"]
            frame_path = os.path.expanduser("~/stream_frame.jpg")
            
            run_cmd(["termux-camera-photo", "-c", str(cam_id), frame_path], timeout=3)
            
            if os.path.exists(frame_path) and os.path.getsize(frame_path) > 0:
                try:
                    with open(frame_path, "rb") as f:
                        camera_stream_state["latest_frame_bytes"] = f.read()
                    camera_stream_state["frame_count"] += 1
                    frames_in_sec += 1
                except:
                    pass
            
            now = time.time()
            if now - last_fps_time >= 1.0:
                camera_stream_state["fps"] = frames_in_sec
                frames_in_sec = 0
                last_fps_time = now
                
            time.sleep(0.05)
        else:
            time.sleep(0.5)

cam_thread = threading.Thread(target=camera_capture_worker, daemon=True)
cam_thread.start()

# Live telemetry & Outage monitoring daemon
def monitor_daemon():
    global last_power_state, power_history, telemetry
    print("[Sentinel Daemon] Started background monitor...")
    
    sensor_tick = 0
    while True:
        try:
            # 1. Battery Data
            bat_raw = run_cmd(["termux-battery-status"], timeout=3)
            try:
                b = json.loads(bat_raw)
                telemetry["battery"] = b
                
                plugged = b.get("plugged", "UNKNOWN")
                pct = b.get("percentage", 0)
                temp = b.get("temperature", 0)
                now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                # Outage Transition Checks
                if last_power_state is not None:
                    if last_power_state.startswith("PLUGGED") and plugged == "UNPLUGGED":
                        event = {
                            "event": "POWER_CUT",
                            "timestamp": now_str,
                            "battery_pct": pct,
                            "temperature": temp,
                            "message": f"Power disconnected. Running on battery ({pct}%)."
                        }
                        power_history.insert(0, event)
                        run_cmd(["termux-notification", "--title", "⚠️ Power Cut Alert", "--content", event["message"], "--sound", "--priority", "high"])
                        run_cmd(["termux-tts-speak", "Alert: Home power disconnected."])
                    elif last_power_state == "UNPLUGGED" and plugged.startswith("PLUGGED"):
                        event = {
                            "event": "POWER_RESTORED",
                            "timestamp": now_str,
                            "battery_pct": pct,
                            "temperature": temp,
                            "message": f"Power restored! Charging at ({pct}%)."
                        }
                        power_history.insert(0, event)
                        run_cmd(["termux-notification", "--title", "⚡ Power Restored", "--content", event["message"], "--sound"])
                        run_cmd(["termux-tts-speak", "Home power restored."])
                
                last_power_state = plugged
                if len(power_history) > 50:
                    power_history.pop()
            except:
                pass

            # 2. System Load & Memory
            uptime_str = str(datetime.now() - server_start_time).split('.')[0]
            uptime_raw = run_cmd(["uptime"], timeout=2)
            mem_raw = run_cmd(["free", "-h"], timeout=2)
            load = uptime_raw.split("load average:")[-1].strip() if "load average:" in uptime_raw else "0.00"
            mem_line = mem_raw.splitlines()[1] if len(mem_raw.splitlines()) > 1 else "5.5GB"
            
            telemetry["system"] = {
                "load": load,
                "memory": mem_line,
                "uptime": uptime_str
            }

            # 3. Read Accelerometer
            sensor_tick += 1
            if sensor_tick >= 2:
                sensor_tick = 0
                accel_raw = run_cmd(["termux-sensor", "-s", "bmi160 Accelerometer Non-wakeup", "-n", "1"], timeout=3)
                try:
                    accel_data = json.loads(accel_raw)
                    for k in accel_data:
                        telemetry["sensors"]["accelerometer"] = accel_data[k].get("values", [0.0, 0.0, 0.0])
                except:
                    pass

            # 4. Wi-Fi Info & Fast Location update (every 10 ticks)
            if sensor_tick == 1:
                wifi_raw = run_cmd(["termux-wifi-connectioninfo"], timeout=2)
                try:
                    telemetry["wifi"] = json.loads(wifi_raw)
                except:
                    pass

            telemetry["last_updated"] = datetime.now().strftime("%H:%M:%S")

        except Exception as e:
            print(f"[Daemon Error] {e}")
            
        time.sleep(2)

t = threading.Thread(target=monitor_daemon, daemon=True)
t.start()

# Global CORS & Cache-Busting
@app.after_request
def add_cors_headers(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = '*'
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    return response

# --- REACT 18 + TAILWIND CSS TABBED MONOCHROME DASHBOARD ---
HTML_PAGE = r'''
<!DOCTYPE html>
<html lang="en" class="dark">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>realme XT • Edge Sentinel</title>
    <!-- Tailwind CSS CDN -->
    <script src="https://cdn.tailwindcss.com"></script>
    <script>
        tailwind.config = {
            darkMode: 'class',
            theme: {
                extend: {
                    colors: {
                        mono: {
                            950: '#050505',
                            900: '#0f0f0f',
                            850: '#171717',
                            800: '#262626',
                            700: '#404040',
                            600: '#525252',
                            400: '#a3a3a3',
                            200: '#e5e5e5',
                            100: '#f5f5f5',
                            50: '#fafafa',
                        }
                    }
                }
            }
        }
    </script>
    <!-- React 18, ReactDOM & Babel -->
    <script crossorigin src="https://unpkg.com/react@18/umd/react.production.min.js"></script>
    <script crossorigin src="https://unpkg.com/react-dom@18/umd/react-dom.production.min.js"></script>
    <script src="https://unpkg.com/@babel/standalone/babel.min.js"></script>
</head>
<body class="bg-black text-mono-100 font-mono min-h-screen p-4 md:p-8 antialiased selection:bg-white selection:text-black">
    <div id="root"></div>

    <script type="text/babel">
        const { useState, useEffect, useCallback, useRef } = React;

        function App() {
            const [activeTab, setActiveTab] = useState('gps');
            const [data, setData] = useState({
                battery: {},
                system: {},
                sensors: { accelerometer: [0, 0, 0] },
                wifi: {},
                location: {
                    latitude: 17.24965383,
                    longitude: 82.39151663,
                    altitude: 35.8,
                    accuracy: 23.5,
                    speed: 0.0,
                    bearing: 0.0,
                    provider: 'gps',
                    last_fix: '--'
                },
                power_history: [],
                last_updated: '--'
            });
            const [toast, setToast] = useState(null);
            
            // Terminal tab state
            const [termCmd, setTermCmd] = useState("uptime");
            const [termOutput, setTermOutput] = useState("$ Ready for commands.");
            
            // Voice & Camera state
            const [ttsText, setTtsText] = useState("GPS coordinates locked");
            const [camLoading, setCamLoading] = useState(false);
            const [camImg, setCamImg] = useState(null);
            const [clipboardText, setClipboardText] = useState("");
            
            // High-FPS Video Streaming State
            const [isStreaming, setIsStreaming] = useState(false);
            const [streamCamId, setStreamCamId] = useState(0);
            const [clientFps, setClientFps] = useState(0);
            const [frameCount, setFrameCount] = useState(0);
            
            // GPS state
            const [gpsLoading, setGpsLoading] = useState(false);
            
            const streamImgRef = useRef(null);
            const streamingActiveRef = useRef(false);

            const showToast = (msg) => {
                setToast(msg);
                setTimeout(() => setToast(null), 3000);
            };

            const fetchData = useCallback(async () => {
                try {
                    const res = await fetch('/api/dashboard/all?t=' + Date.now());
                    const json = await res.json();
                    setData(json);
                } catch(e) {
                    console.error("Fetch failed:", e);
                }
            }, []);

            useEffect(() => {
                fetchData();
                const interval = setInterval(fetchData, 1500);
                return () => clearInterval(interval);
            }, [fetchData]);

            // High-Speed Multi-Buffered Frame Engine
            const startVideoStream = async () => {
                setIsStreaming(true);
                streamingActiveRef.current = true;
                showToast("Activating Fast Camera Engine...");

                await fetch('/api/camera/stream/start', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ camera: streamCamId })
                });

                let lastFpsCalc = Date.now();
                let framesDelivered = 0;

                const pumpFrames = async () => {
                    if (!streamingActiveRef.current) return;
                    try {
                        const res = await fetch(`/api/camera/frame/fast?t=${Date.now()}`);
                        if (res.ok) {
                            const blob = await res.blob();
                            if (streamImgRef.current && streamingActiveRef.current) {
                                streamImgRef.current.src = URL.createObjectURL(blob);
                                setFrameCount(prev => prev + 1);
                                framesDelivered++;
                                
                                const now = Date.now();
                                if (now - lastFpsCalc >= 1000) {
                                    setClientFps(framesDelivered);
                                    framesDelivered = 0;
                                    lastFpsCalc = now;
                                }
                            }
                        }
                    } catch(e) {}

                    if (streamingActiveRef.current) {
                        setTimeout(pumpFrames, 50);
                    }
                };

                pumpFrames();
            };

            const stopVideoStream = async () => {
                setIsStreaming(false);
                streamingActiveRef.current = false;
                setClientFps(0);
                await fetch('/api/camera/stream/stop', { method: 'POST' });
                showToast("Camera Stream Stopped");
            };

            // Acquire Fresh GPS Fix
            const acquireGpsFix = async (provider = 'gps', reqType = 'once') => {
                setGpsLoading(true);
                showToast(`Acquiring satellite fix via ${provider.toUpperCase()}...`);
                try {
                    const res = await fetch(`/api/location/fix?provider=${provider}&request=${reqType}&t=${Date.now()}`);
                    const loc = await res.json();
                    if (loc && loc.latitude) {
                        setData(prev => ({ ...prev, location: loc }));
                        showToast(`GPS Fix Acquired (±${Number(loc.accuracy).toFixed(1)}m)`);
                    } else {
                        showToast("GPS timeout: Showing last known location");
                    }
                } catch(e) {
                    showToast("GPS Fix Failed: " + e);
                } finally {
                    setGpsLoading(false);
                }
            };

            const postAction = async (url, body, msg) => {
                showToast("Sending: " + msg + "...");
                try {
                    const res = await fetch(url, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(body)
                    });
                    const d = await res.json();
                    showToast("Success: " + msg);
                    fetchData();
                } catch(e) {
                    showToast("Error: " + e);
                }
            };

            const runTerminal = async (cmdToRun) => {
                const cmd = cmdToRun || termCmd;
                setTermOutput("$ " + cmd + "\nExecuting...");
                try {
                    const res = await fetch('/api/terminal', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ command: cmd })
                    });
                    const d = await res.json();
                    setTermOutput("$ " + cmd + "\n\n" + (d.output || d.error || "Done"));
                    showToast("Executed: " + cmd);
                } catch(e) {
                    setTermOutput("Error: " + e);
                }
            };

            const snapPhoto = async (camId) => {
                setCamLoading(true);
                showToast("Capturing full-res photo from Camera " + camId + "...");
                try {
                    const res = await fetch(`/api/camera/snap?camera=${camId}&t=${Date.now()}`);
                    if (!res.ok) throw new Error("Capture failed");
                    const blob = await res.blob();
                    setCamImg(URL.createObjectURL(blob));
                    showToast("Photo Captured (3000x4000)");
                } catch(e) {
                    showToast("Camera Error: " + e);
                } finally {
                    setCamLoading(false);
                }
            };

            const readClipboard = async () => {
                showToast("Reading phone clipboard...");
                try {
                    const res = await fetch('/api/terminal', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ command: 'termux-clipboard-get' })
                    });
                    const d = await res.json();
                    setClipboardText(d.output || '(Empty clipboard)');
                    showToast("Clipboard fetched");
                } catch(e) {
                    showToast("Clipboard Error: " + e);
                }
            };

            const writeClipboard = async () => {
                if (!clipboardText) return;
                showToast("Writing to phone clipboard...");
                try {
                    await fetch('/api/terminal', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ command: `termux-clipboard-set "${clipboardText.replace(/"/g, '\\"')}"` })
                    });
                    showToast("Clipboard updated on phone");
                } catch(e) {
                    showToast("Error: " + e);
                }
            };

            const bat = data.battery || {};
            const sys = data.system || {};
            const coords = (data.sensors && data.sensors.accelerometer) || [0, 0, 0];
            const wifi = data.wifi || {};
            const loc = data.location || {};

            const mapUrl = loc.latitude && loc.longitude ? `https://www.openstreetmap.org/export/embed.html?bbox=${loc.longitude-0.005}%2C${loc.latitude-0.005}%2C${loc.longitude+0.005}%2C${loc.latitude+0.005}&layer=mapnik&marker=${loc.latitude}%2C${loc.longitude}` : '';
            const gmapsUrl = loc.latitude && loc.longitude ? `https://www.google.com/maps?q=${loc.latitude},${loc.longitude}` : '#';

            const tabs = [
                { id: 'gps', label: '📍 GPS & GEOLOCATION' },
                { id: 'camera', label: '📹 HIGH-FPS CAMERA' },
                { id: 'power', label: '⚡ POWER & UPS', badge: bat.percentage ? bat.percentage + '%' : null },
                { id: 'hardware', label: '🎛️ HARDWARE & SENSORS' },
                { id: 'terminal', label: '💻 TERMINAL & HTOP' },
                { id: 'network', label: '🌐 NETWORK & TELEMETRY' }
            ];

            return (
                <div class="max-w-5xl mx-auto space-y-6">
                    {/* HEADER */}
                    <header class="border-b border-mono-800 pb-5 flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
                        <div>
                            <div class="flex items-center gap-3">
                                <span class="relative flex h-3 w-3">
                                    <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-white opacity-75"></span>
                                    <span class="relative inline-flex rounded-full h-3 w-3 bg-white"></span>
                                </span>
                                <h1 class="text-xl font-bold tracking-tight uppercase">realme XT • Edge Sentinel</h1>
                            </div>
                            <p class="text-xs text-mono-400 mt-1">Tailscale Node: 100.123.244.85:8000 • Snapdragon 712 ARM64</p>
                        </div>
                        <div class="flex items-center gap-3">
                            <span class="text-xs border border-mono-800 bg-mono-900 px-3 py-1.5 rounded text-mono-400">
                                SYNC: {data.last_updated}
                            </span>
                            <button onClick={fetchData} class="text-xs bg-white text-black font-bold px-3 py-1.5 rounded hover:bg-mono-200 transition">
                                🔄 REFRESH
                            </button>
                        </div>
                    </header>

                    {/* TOAST BANNER */}
                    {toast && (
                        <div class="border border-white bg-mono-900 text-white px-4 py-2 text-xs font-bold rounded animate-pulse">
                            ⚡ {toast}
                        </div>
                    )}

                    {/* DEDICATED TAB BAR */}
                    <nav class="flex flex-wrap gap-2 border-b border-mono-800 pb-3">
                        {tabs.map(t => (
                            <button
                                key={t.id}
                                onClick={() => setActiveTab(t.id)}
                                class={`px-4 py-2 text-xs font-bold rounded transition flex items-center gap-2 border ${
                                    activeTab === t.id
                                        ? 'bg-white text-black border-white shadow-sm'
                                        : 'bg-mono-900 text-mono-400 border-mono-800 hover:border-mono-600 hover:text-white'
                                }`}
                            >
                                <span>{t.label}</span>
                                {t.badge && (
                                    <span class={`text-[10px] px-1.5 py-0.2 rounded font-mono ${activeTab === t.id ? 'bg-black text-white' : 'bg-mono-800 text-mono-200'}`}>
                                        {t.badge}
                                    </span>
                                )}
                            </button>
                        ))}
                    </nav>

                    {/* TAB: GPS & GEOLOCATION */}
                    {activeTab === 'gps' && (
                        <div class="space-y-5 animate-fadeIn">
                            {/* GPS CONTROLS HEADER */}
                            <div class="bg-mono-900 border border-mono-800 rounded-lg p-6 flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
                                <div>
                                    <span class="text-xs text-mono-400 font-bold uppercase tracking-wider block">🛰️ GNSS / GPS Hardware Receiver</span>
                                    <div class="text-xs text-mono-500 mt-1">
                                        Provider: <span class="text-white font-bold uppercase">{loc.provider || 'GPS'}</span> • Last Fix: <span class="text-mono-300">{loc.last_fix || '--'}</span>
                                    </div>
                                </div>
                                <div class="flex flex-wrap gap-2">
                                    <button 
                                        onClick={() => acquireGpsFix('gps', 'once')} 
                                        disabled={gpsLoading}
                                        class="bg-white text-black font-bold text-xs px-4 py-2 rounded hover:bg-mono-200 flex items-center gap-1.5"
                                    >
                                        <span>🛰️</span> {gpsLoading ? 'ACQUIRING SATELLITES...' : 'ACQUIRE FRESH FIX'}
                                    </button>
                                    <button 
                                        onClick={() => acquireGpsFix('gps', 'last')} 
                                        class="border border-mono-700 bg-mono-850 text-white font-bold text-xs px-3 py-2 rounded hover:bg-mono-800"
                                    >
                                        ⚡ LAST KNOWN
                                    </button>
                                    <a 
                                        href={gmapsUrl} 
                                        target="_blank" 
                                        class="border border-mono-700 bg-mono-850 text-white font-bold text-xs px-3 py-2 rounded hover:bg-mono-800 flex items-center gap-1"
                                    >
                                        🗺️ GOOGLE MAPS ↗
                                    </a>
                                </div>
                            </div>

                            {/* COORDINATES GRID */}
                            <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
                                <div class="bg-mono-900 border border-mono-800 rounded-lg p-5">
                                    <span class="text-xs text-mono-400 font-bold uppercase tracking-wider block mb-1">Latitude</span>
                                    <div class="text-2xl font-black text-white font-mono">{loc.latitude ? Number(loc.latitude).toFixed(6) : '--'}° N</div>
                                    <span class="text-[10px] text-mono-500">WGS84 Coordinate</span>
                                </div>
                                <div class="bg-mono-900 border border-mono-800 rounded-lg p-5">
                                    <span class="text-xs text-mono-400 font-bold uppercase tracking-wider block mb-1">Longitude</span>
                                    <div class="text-2xl font-black text-white font-mono">{loc.longitude ? Number(loc.longitude).toFixed(6) : '--'}° E</div>
                                    <span class="text-[10px] text-mono-500">WGS84 Coordinate</span>
                                </div>
                                <div class="bg-mono-900 border border-mono-800 rounded-lg p-5">
                                    <span class="text-xs text-mono-400 font-bold uppercase tracking-wider block mb-1">Altitude</span>
                                    <div class="text-2xl font-black text-white font-mono">{loc.altitude ? Number(loc.altitude).toFixed(1) + ' m' : '--'}</div>
                                    <span class="text-[10px] text-mono-500">Above Sea Level</span>
                                </div>
                                <div class="bg-mono-900 border border-mono-800 rounded-lg p-5">
                                    <span class="text-xs text-mono-400 font-bold uppercase tracking-wider block mb-1">Fix Accuracy</span>
                                    <div class="text-2xl font-black text-green-400 font-mono">±{loc.accuracy ? Number(loc.accuracy).toFixed(1) + ' m' : '--'}</div>
                                    <span class="text-[10px] text-mono-500">Horizontal Precision</span>
                                </div>
                            </div>

                            {/* EMBEDDED MAP VIEW */}
                            <div class="bg-mono-900 border border-mono-800 rounded-lg p-6">
                                <div class="flex justify-between items-center mb-3">
                                    <span class="text-xs text-mono-400 font-bold uppercase tracking-wider">🗺️ Interactive Real-Time Map View</span>
                                    <span class="text-[10px] text-mono-500">OpenStreetMap Vector Tiles</span>
                                </div>
                                <div class="border border-mono-800 rounded-lg overflow-hidden h-80 bg-mono-950">
                                    {mapUrl ? (
                                        <iframe 
                                            width="100%" 
                                            height="100%" 
                                            frameBorder="0" 
                                            scrolling="no" 
                                            src={mapUrl}
                                            class="w-full h-full"
                                        ></iframe>
                                    ) : (
                                        <div class="flex items-center justify-center h-full text-mono-500 text-xs">
                                            No GPS fix coordinates available yet.
                                        </div>
                                    )}
                                </div>
                                <div class="mt-3 flex justify-between text-xs text-mono-400">
                                    <span>SPEED: {loc.speed ? Number(loc.speed).toFixed(1) + ' m/s' : '0.0 m/s'}</span>
                                    <span>BEARING: {loc.bearing ? Number(loc.bearing).toFixed(1) + '°' : '0.0°'}</span>
                                    <span>PROVIDER: {loc.provider || 'GPS'}</span>
                                </div>
                            </div>
                        </div>
                    )}

                    {/* TAB: HIGH-FPS CAMERA & VISION */}
                    {activeTab === 'camera' && (
                        <div class="space-y-5 animate-fadeIn">
                            <div class="bg-mono-900 border border-mono-800 rounded-lg p-6">
                                <div class="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 mb-6 border-b border-mono-800 pb-4">
                                    <div>
                                        <div class="flex items-center gap-2">
                                            {isStreaming && (
                                                <span class="relative flex h-2.5 w-2.5">
                                                    <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-500 opacity-75"></span>
                                                    <span class="relative inline-flex rounded-full h-2.5 w-2.5 bg-red-600"></span>
                                                </span>
                                            )}
                                            <span class="text-xs text-mono-400 font-bold uppercase tracking-wider">
                                                {isStreaming ? 'LIVE HIGH-FPS STREAMING ACTIVE' : 'CAMERA & HIGH-SPEED VISION HUB'}
                                            </span>
                                        </div>
                                        <div class="text-xs text-mono-500 mt-0.5">
                                            {isStreaming ? `Pipelined In-Memory Stream • ${clientFps} FPS • Frame #${frameCount}` : 'Asynchronous buffered video streaming & 4K photo capture'}
                                        </div>
                                    </div>

                                    {/* CONTROLS */}
                                    <div class="flex flex-wrap gap-2 w-full md:w-auto">
                                        <select 
                                            value={streamCamId} 
                                            onChange={(e) => setStreamCamId(Number(e.target.value))}
                                            class="bg-mono-950 border border-mono-700 text-white px-3 py-2 text-xs rounded font-mono focus:outline-none"
                                        >
                                            <option value="0">Rear Camera (Sensor 0)</option>
                                            <option value="1">Front Camera (Sensor 1)</option>
                                        </select>

                                        {!isStreaming ? (
                                            <button onClick={startVideoStream} class="bg-white text-black font-bold text-xs px-4 py-2 rounded hover:bg-mono-200 flex items-center gap-1.5 shadow-sm">
                                                <span>▶️</span> START HIGH-FPS STREAM
                                            </button>
                                        ) : (
                                            <button onClick={stopVideoStream} class="bg-red-600 text-white font-bold text-xs px-4 py-2 rounded hover:bg-red-700 flex items-center gap-1.5 shadow-sm">
                                                <span>⏹️</span> STOP STREAM
                                            </button>
                                        )}

                                        <button onClick={() => snapPhoto(streamCamId)} class="border border-mono-700 bg-mono-850 text-white font-bold text-xs px-3 py-2 rounded hover:bg-mono-800">
                                            📸 SNAP 4K
                                        </button>
                                    </div>
                                </div>

                                {/* LIVE VIDEO VIEWPORT */}
                                <div class="relative border border-mono-800 bg-mono-950 rounded-lg overflow-hidden min-h-[400px] max-h-[580px] flex items-center justify-center">
                                    {isStreaming ? (
                                        <div class="relative w-full h-full flex items-center justify-center">
                                            <img 
                                                ref={streamImgRef} 
                                                alt="Live High-FPS Stream" 
                                                class="w-full h-full max-h-[540px] object-contain rounded" 
                                            />
                                            <div class="absolute top-3 left-3 bg-black/85 border border-mono-700 text-white text-[10px] font-mono px-3 py-1.5 rounded flex items-center gap-2.5 backdrop-blur shadow">
                                                <span class="inline-block w-2 h-2 rounded-full bg-red-500 animate-pulse"></span>
                                                <span class="font-bold">LIVE HIGH-FPS • CAM {streamCamId}</span>
                                                <span class="border-l border-mono-700 pl-2 text-green-400 font-bold">{clientFps} FPS</span>
                                                <span class="text-mono-500">#{frameCount}</span>
                                            </div>
                                        </div>
                                    ) : camImg ? (
                                        <div class="relative w-full h-full flex flex-col items-center justify-center p-2">
                                            <img src={camImg} alt="Snapshot Preview" class="w-full max-h-[500px] object-contain rounded" />
                                            <div class="mt-2 text-xs text-mono-400 flex justify-between w-full px-2">
                                                <span>High-Res Snapshot (3000 x 4000)</span>
                                                <a href={camImg} download="snap.jpg" class="underline text-white font-bold">Download Full JPEG</a>
                                            </div>
                                        </div>
                                    ) : (
                                        <div class="p-16 text-center text-mono-500 text-xs space-y-3">
                                            <div class="text-4xl mb-2">📹</div>
                                            <div class="font-bold text-mono-300 text-sm">High-Speed Video Engine Ready</div>
                                            <p>Click <strong class="text-white">START HIGH-FPS STREAM</strong> above to start live streaming.</p>
                                        </div>
                                    )}
                                </div>
                            </div>
                        </div>
                    )}

                    {/* TAB: POWER & UPS SENTINEL */}
                    {activeTab === 'power' && (
                        <div class="space-y-5 animate-fadeIn">
                            <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
                                <div class="bg-mono-900 border border-mono-800 rounded-lg p-6 flex flex-col justify-between md:col-span-2">
                                    <div class="flex justify-between items-start">
                                        <span class="text-xs text-mono-400 font-bold uppercase tracking-wider">Battery Level & Charging State</span>
                                        <span class={`text-xs font-bold px-2.5 py-1 rounded border ${bat.plugged && bat.plugged.startsWith('PLUGGED') ? 'bg-white text-black border-white' : 'bg-mono-800 text-mono-300 border-mono-700'}`}>
                                            {bat.plugged || 'UNKNOWN'}
                                        </span>
                                    </div>
                                    <div class="my-6">
                                        <div class="text-6xl font-black tracking-tight text-white">
                                            {bat.percentage !== undefined ? bat.percentage + '%' : '--%'}
                                        </div>
                                        <div class="text-sm text-mono-400 mt-2">
                                            Charging Status: <span class="text-white font-bold">{bat.status || 'Checking...'}</span>
                                        </div>
                                    </div>
                                    <div class="grid grid-cols-3 gap-2 border-t border-mono-800 pt-4 text-xs text-mono-400">
                                        <div><span class="block text-mono-600 uppercase font-bold text-[10px]">Temperature</span><span class="text-white font-bold">{bat.temperature ? bat.temperature + '°C' : '--'}</span></div>
                                        <div><span class="block text-mono-600 uppercase font-bold text-[10px]">Voltage</span><span class="text-white font-bold">{bat.voltage ? bat.voltage + ' mV' : '--'}</span></div>
                                        <div><span class="block text-mono-600 uppercase font-bold text-[10px]">Health</span><span class="text-white font-bold">{bat.health || 'GOOD'}</span></div>
                                    </div>
                                </div>

                                <div class="bg-mono-900 border border-mono-800 rounded-lg p-6 flex flex-col justify-between">
                                    <div>
                                        <span class="text-xs text-mono-400 font-bold uppercase tracking-wider block mb-2">Sentinel Daemon Status</span>
                                        <div class="text-lg font-bold text-white mb-2">24/7 Power Monitor Active</div>
                                        <p class="text-xs text-mono-400 leading-relaxed">
                                            Monitors charger state every 2s. Triggers high-priority Android notification & voice announcement if power disconnects.
                                        </p>
                                    </div>
                                    <div class="border-t border-mono-800 pt-4 mt-4">
                                        <button onClick={() => postAction('/api/toast', {message: 'Sentinel monitoring active'}, 'Sentinel Active')} class="w-full bg-mono-800 text-white border border-mono-700 hover:border-white font-bold text-xs py-2 px-3 rounded transition">
                                            🚨 SENTINEL ACTIVE
                                        </button>
                                    </div>
                                </div>
                            </div>

                            {/* OUTAGE LOG TABLE */}
                            <div class="bg-mono-900 border border-mono-800 rounded-lg p-6">
                                <span class="text-xs text-mono-400 font-bold uppercase tracking-wider block mb-4">Power Outage & Interruption History</span>
                                <div class="overflow-x-auto">
                                    <table class="w-full text-left text-xs border-collapse">
                                        <thead>
                                            <tr class="border-b border-mono-800 text-mono-400">
                                                <th class="pb-2">TIMESTAMP</th>
                                                <th class="pb-2">EVENT</th>
                                                <th class="pb-2">BATTERY</th>
                                                <th class="pb-2">DETAILS</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {data.power_history && data.power_history.length > 0 ? (
                                                data.power_history.map((e, idx) => (
                                                    <tr key={idx} class="border-b border-mono-850">
                                                        <td class="py-3 font-mono">{e.timestamp}</td>
                                                        <td class="py-3">
                                                            <span class={`px-2 py-0.5 rounded text-[10px] font-bold ${e.event === 'POWER_CUT' ? 'bg-red-950 text-red-300 border border-red-800' : 'bg-green-950 text-green-300 border border-green-800'}`}>
                                                                {e.event}
                                                            </span>
                                                        </td>
                                                        <td class="py-3 font-bold">{e.battery_pct}%</td>
                                                        <td class="py-3 text-mono-300">{e.message}</td>
                                                    </tr>
                                                ))
                                            ) : (
                                                <tr>
                                                    <td colSpan="4" class="py-6 text-mono-500 text-center">
                                                        Sentinel active. Unplug phone charger to trigger an outage event.
                                                    </td>
                                                </tr>
                                            )}
                                        </tbody>
                                    </table>
                                </div>
                            </div>
                        </div>
                    )}

                    {/* TAB: HARDWARE & SENSORS */}
                    {activeTab === 'hardware' && (
                        <div class="space-y-5 animate-fadeIn">
                            {/* 3-AXIS ACCELEROMETER */}
                            <div class="bg-mono-900 border border-mono-800 rounded-lg p-6">
                                <div class="flex justify-between items-center mb-4">
                                    <div>
                                        <span class="text-xs text-mono-400 font-bold uppercase tracking-wider block">🛰️ 3-Axis Accelerometer (Bosch BMI160)</span>
                                        <span class="text-[11px] text-mono-500">Live dynamic gravity & motion coordinates</span>
                                    </div>
                                    <span class="text-xs border border-mono-800 px-2 py-1 rounded text-mono-400 font-mono">m/s²</span>
                                </div>
                                <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
                                    <div class="border border-mono-800 bg-mono-950 p-5 rounded-lg text-center">
                                        <div class="text-xs text-mono-400 font-bold uppercase">X-Axis Motion</div>
                                        <div class="text-3xl font-extrabold text-white mt-2 font-mono">{Number(coords[0] || 0).toFixed(2)}</div>
                                    </div>
                                    <div class="border border-mono-800 bg-mono-950 p-5 rounded-lg text-center">
                                        <div class="text-xs text-mono-400 font-bold uppercase">Y-Axis Motion</div>
                                        <div class="text-3xl font-extrabold text-white mt-2 font-mono">{Number(coords[1] || 0).toFixed(2)}</div>
                                    </div>
                                    <div class="border border-mono-800 bg-mono-950 p-5 rounded-lg text-center">
                                        <div class="text-xs text-mono-400 font-bold uppercase">Z-Axis (Gravity Vector)</div>
                                        <div class="text-3xl font-extrabold text-white mt-2 font-mono">{Number(coords[2] || 0).toFixed(2)}</div>
                                    </div>
                                </div>
                            </div>

                            {/* ACTUATORS */}
                            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                                <div class="bg-mono-900 border border-mono-800 rounded-lg p-6">
                                    <span class="text-xs text-mono-400 font-bold uppercase tracking-wider block mb-4">Flashlight & Haptic Motors</span>
                                    <div class="space-y-3">
                                        <div class="flex gap-2">
                                            <button onClick={() => postAction('/api/torch', {state: 'on'}, 'Flashlight ON')} class="bg-white text-black font-bold text-xs py-3 px-4 rounded flex-1 hover:bg-mono-200">
                                                🔦 TORCH ON
                                            </button>
                                            <button onClick={() => postAction('/api/torch', {state: 'off'}, 'Flashlight OFF')} class="border border-mono-700 bg-mono-850 text-white font-bold text-xs py-3 px-4 rounded flex-1 hover:bg-mono-800">
                                                TORCH OFF
                                            </button>
                                        </div>
                                        <div class="flex gap-2">
                                            <button onClick={() => postAction('/api/vibrate', {duration_ms: 300}, 'Vibrated 300ms')} class="border border-mono-700 bg-mono-850 text-white font-bold text-xs py-3 px-4 rounded flex-1 hover:bg-mono-800">
                                                📳 BUZZ 300ms
                                            </button>
                                            <button onClick={() => postAction('/api/vibrate', {duration_ms: 1000}, 'Vibrated 1000ms')} class="border border-mono-700 bg-mono-850 text-white font-bold text-xs py-3 px-4 rounded flex-1 hover:bg-mono-800">
                                                📳 BUZZ 1000ms
                                            </button>
                                        </div>
                                        <button onClick={() => postAction('/api/toast', {message: 'Ping from React Dashboard!'}, 'Toast Sent')} class="w-full border border-mono-700 bg-mono-850 text-white font-bold text-xs py-2.5 px-3 rounded hover:bg-mono-800">
                                            💬 SHOW ANDROID TOAST
                                        </button>
                                    </div>
                                </div>

                                <div class="bg-mono-900 border border-mono-800 rounded-lg p-6 flex flex-col justify-between">
                                    <div>
                                        <span class="text-xs text-mono-400 font-bold uppercase tracking-wider block mb-4">🗣️ Text-to-Speech Voice Engine</span>
                                        <div class="flex gap-2">
                                            <input 
                                                type="text" 
                                                value={ttsText} 
                                                onChange={(e) => setTtsText(e.target.value)}
                                                onKeyDown={(e) => e.key === 'Enter' && postAction('/api/tts', {text: ttsText}, 'Speech')}
                                                placeholder="Type text to speak..." 
                                                class="bg-mono-950 border border-mono-800 text-white px-3 py-2 text-xs rounded flex-1 focus:outline-none focus:border-white"
                                            />
                                            <button onClick={() => postAction('/api/tts', {text: ttsText}, 'Speech')} class="bg-white text-black font-bold text-xs px-4 py-2 rounded hover:bg-mono-200">
                                                SPEAK
                                            </button>
                                        </div>
                                    </div>
                                    <div class="border-t border-mono-800 pt-4 mt-4 flex justify-between text-xs text-mono-400">
                                        <span>ENGINE: Google TTS</span>
                                        <span>LOCALE: en-US</span>
                                    </div>
                                </div>
                            </div>
                        </div>
                    )}

                    {/* TAB: TERMINAL & HTOP */}
                    {activeTab === 'terminal' && (
                        <div class="space-y-5 animate-fadeIn">
                            <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
                                <div class="bg-mono-900 border border-mono-800 rounded-lg p-5">
                                    <span class="text-xs text-mono-400 font-bold uppercase tracking-wider block mb-1">CPU Load Average</span>
                                    <div class="text-2xl font-bold text-white">{sys.load || '0.00'}</div>
                                    <span class="text-[10px] text-mono-500">1m, 5m, 15m averages</span>
                                </div>
                                <div class="bg-mono-900 border border-mono-800 rounded-lg p-5">
                                    <span class="text-xs text-mono-400 font-bold uppercase tracking-wider block mb-1">Memory Utilization</span>
                                    <div class="text-2xl font-bold text-white">{sys.memory ? sys.memory.split(/\s+/)[2] || '3.2GB' : '--'}</div>
                                    <span class="text-[10px] text-mono-500">{sys.memory || '5.5GB Total'}</span>
                                </div>
                                <div class="bg-mono-900 border border-mono-800 rounded-lg p-5">
                                    <span class="text-xs text-mono-400 font-bold uppercase tracking-wider block mb-1">Node Uptime</span>
                                    <div class="text-2xl font-bold text-white">{sys.uptime || '0:00:00'}</div>
                                    <span class="text-[10px] text-mono-500">Termux POSIX Environment</span>
                                </div>
                            </div>

                            {/* TERMINAL CONSOLE */}
                            <div class="bg-mono-900 border border-mono-800 rounded-lg p-6">
                                <div class="flex justify-between items-center mb-4">
                                    <span class="text-xs text-mono-400 font-bold uppercase tracking-wider">🖥️ Remote Web Terminal</span>
                                    <span class="text-[10px] text-mono-500">Runs commands inside phone environment</span>
                                </div>
                                <div class="flex gap-2 mb-3">
                                    <input 
                                        type="text" 
                                        value={termCmd} 
                                        onChange={(e) => setTermCmd(e.target.value)}
                                        onKeyDown={(e) => e.key === 'Enter' && runTerminal()}
                                        placeholder="Enter shell command (e.g. top, ifconfig, free -m)..." 
                                        class="bg-mono-950 border border-mono-800 text-white px-3 py-2 text-xs rounded flex-1 focus:outline-none focus:border-white font-mono"
                                    />
                                    <button onClick={() => runTerminal()} class="bg-white text-black font-bold text-xs px-5 py-2 rounded hover:bg-mono-200">
                                        EXECUTE
                                    </button>
                                </div>
                                <div class="flex flex-wrap gap-2 mb-3">
                                    {['top -b -n 1 | head -n 12', 'ifconfig wlan0', 'df -h', 'free -h', 'ps aux | head -n 8', 'uname -a', 'date'].map(c => (
                                        <button key={c} onClick={() => { setTermCmd(c); runTerminal(c); }} class="text-[10px] border border-mono-800 px-2.5 py-1 rounded text-mono-400 hover:text-white hover:border-mono-600 bg-mono-950">
                                            {c.split(' ')[0]}
                                        </button>
                                    ))}
                                </div>
                                <div class="bg-mono-950 border border-mono-800 rounded-lg p-4 text-xs text-mono-200 h-64 overflow-y-auto whitespace-pre font-mono leading-relaxed">
                                    {termOutput}
                                </div>
                            </div>
                        </div>
                    )}

                    {/* TAB: NETWORK & TELEMETRY */}
                    {activeTab === 'network' && (
                        <div class="space-y-5 animate-fadeIn">
                            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                                <div class="bg-mono-900 border border-mono-800 rounded-lg p-6">
                                    <span class="text-xs text-mono-400 font-bold uppercase tracking-wider block mb-4">📶 Wi-Fi Connection Details</span>
                                    <div class="space-y-3 text-xs">
                                        <div class="flex justify-between border-b border-mono-800 pb-2"><span class="text-mono-500">SSID:</span><span class="font-bold text-white">{wifi.ssid || 'AirFiber - KK'}</span></div>
                                        <div class="flex justify-between border-b border-mono-800 pb-2"><span class="text-mono-500">Local IP:</span><span class="font-bold text-white">{wifi.ip || '192.168.31.139'}</span></div>
                                        <div class="flex justify-between border-b border-mono-800 pb-2"><span class="text-mono-500">Signal (RSSI):</span><span class="font-bold text-white">{wifi.rssi ? wifi.rssi + ' dBm' : '-43 dBm'}</span></div>
                                        <div class="flex justify-between border-b border-mono-800 pb-2"><span class="text-mono-500">Link Speed:</span><span class="font-bold text-white">{wifi.link_speed_mbps ? wifi.link_speed_mbps + ' Mbps' : '433 Mbps'}</span></div>
                                        <div class="flex justify-between"><span class="text-mono-500">Frequency:</span><span class="font-bold text-white">{wifi.frequency_mhz ? wifi.frequency_mhz + ' MHz' : '5220 MHz'}</span></div>
                                    </div>
                                </div>

                                <div class="bg-mono-900 border border-mono-800 rounded-lg p-6">
                                    <span class="text-xs text-mono-400 font-bold uppercase tracking-wider block mb-4">🔒 Tailscale Mesh Topology</span>
                                    <div class="space-y-3 text-xs">
                                        <div class="flex justify-between border-b border-mono-800 pb-2"><span class="text-mono-500">Node IP:</span><span class="font-bold text-white">100.123.244.85</span></div>
                                        <div class="flex justify-between border-b border-mono-800 pb-2"><span class="text-mono-500">Hostname:</span><span class="font-bold text-white">srsxb13 (realme XT)</span></div>
                                        <div class="flex justify-between border-b border-mono-800 pb-2"><span class="text-mono-500">SSH Port:</span><span class="font-bold text-white">8022</span></div>
                                        <div class="flex justify-between border-b border-mono-800 pb-2"><span class="text-mono-500">HTTP Gateway Port:</span><span class="font-bold text-white">8000</span></div>
                                        <div class="flex justify-between"><span class="text-mono-500">Encryption:</span><span class="font-bold text-white">WireGuard Mesh</span></div>
                                    </div>
                                </div>
                            </div>

                            {/* CLIPBOARD SYNC */}
                            <div class="bg-mono-900 border border-mono-800 rounded-lg p-6">
                                <span class="text-xs text-mono-400 font-bold uppercase tracking-wider block mb-3">📋 Cross-Device Clipboard Sync</span>
                                <div class="flex gap-2 mb-3">
                                    <input 
                                        type="text" 
                                        value={clipboardText} 
                                        onChange={(e) => setClipboardText(e.target.value)}
                                        placeholder="Type text to send to phone clipboard or click Fetch..." 
                                        class="bg-mono-950 border border-mono-800 text-white px-3 py-2 text-xs rounded flex-1 focus:outline-none focus:border-white"
                                    />
                                    <button onClick={writeClipboard} class="bg-white text-black font-bold text-xs px-4 py-2 rounded hover:bg-mono-200">
                                        SEND TO PHONE
                                    </button>
                                    <button onClick={readClipboard} class="border border-mono-700 bg-mono-850 text-white font-bold text-xs px-4 py-2 rounded hover:bg-mono-800">
                                        FETCH CLIPBOARD
                                    </button>
                                </div>
                            </div>
                        </div>
                    )}
                </div>
            );
        }

        const root = ReactDOM.createRoot(document.getElementById('root'));
        root.render(<App />);
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    return render_template_string(HTML_PAGE)

@app.route('/api/dashboard/all', methods=['GET'])
def api_dashboard_all():
    return jsonify({
        "battery": telemetry["battery"],
        "system": telemetry["system"],
        "sensors": telemetry["sensors"],
        "wifi": telemetry["wifi"],
        "location": telemetry["location"],
        "power_history": power_history,
        "last_updated": telemetry["last_updated"]
    })

@app.route('/api/location/fix', methods=['GET', 'POST', 'OPTIONS'])
def api_location_fix():
    if request.method == 'OPTIONS':
        return jsonify({})
    provider = request.args.get('provider', 'gps')
    req_type = request.args.get('request', 'once')
    
    loc_raw = run_cmd(["termux-location", "-p", provider, "-r", req_type], timeout=8)
    try:
        loc = json.loads(loc_raw)
        loc["last_fix"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        telemetry["location"] = loc
        return jsonify(loc)
    except Exception as e:
        # Return last cached location if fresh query timed out
        return jsonify(telemetry["location"])

@app.route('/api/location', methods=['GET'])
def api_location():
    return jsonify(telemetry["location"])

@app.route('/api/camera/stream/start', methods=['POST', 'OPTIONS'])
def api_camera_stream_start():
    if request.method == 'OPTIONS':
        return jsonify({})
    data = request.get_json() or {}
    camera_stream_state["camera_id"] = int(data.get("camera", 0))
    camera_stream_state["active"] = True
    return jsonify({"success": True, "active": True, "camera": camera_stream_state["camera_id"]})

@app.route('/api/camera/stream/stop', methods=['POST', 'OPTIONS'])
def api_camera_stream_stop():
    if request.method == 'OPTIONS':
        return jsonify({})
    camera_stream_state["active"] = False
    return jsonify({"success": True, "active": False})

@app.route('/api/camera/frame/fast', methods=['GET'])
def api_camera_frame_fast():
    if camera_stream_state["latest_frame_bytes"]:
        return Response(camera_stream_state["latest_frame_bytes"], mimetype='image/jpeg')
    
    frame_path = os.path.expanduser("~/stream_frame.jpg")
    if os.path.exists(frame_path) and os.path.getsize(frame_path) > 0:
        return send_file(frame_path, mimetype='image/jpeg')
    return jsonify({"error": "No frame available"}), 404

@app.route('/api/camera/snap', methods=['GET', 'POST'])
def api_camera_snap():
    cam_id = request.args.get('camera', '0')
    snap_path = os.path.expanduser("~/snap.jpg")
    if os.path.exists(snap_path):
        try: os.remove(snap_path)
        except: pass
    run_cmd(["termux-camera-photo", "-c", str(cam_id), snap_path], timeout=10)
    if os.path.exists(snap_path) and os.path.getsize(snap_path) > 0:
        return send_file(snap_path, mimetype='image/jpeg')
    return jsonify({"error": "Failed to capture image"}), 500

@app.route('/api/torch', methods=['POST', 'OPTIONS'])
def api_torch():
    if request.method == 'OPTIONS':
        return jsonify({})
    data = request.get_json() or {}
    st = data.get("state", "off")
    run_cmd(["termux-torch", st])
    return jsonify({"success": True, "torch": st})

@app.route('/api/tts', methods=['POST', 'OPTIONS'])
def api_tts():
    if request.method == 'OPTIONS':
        return jsonify({})
    data = request.get_json() or {}
    text = data.get("text", "Hello")
    run_cmd(["termux-tts-speak", text])
    return jsonify({"success": True, "spoken": text})

@app.route('/api/vibrate', methods=['POST', 'OPTIONS'])
def api_vibrate():
    if request.method == 'OPTIONS':
        return jsonify({})
    data = request.get_json() or {}
    ms = str(data.get("duration_ms", 500))
    run_cmd(["termux-vibrate", "-d", ms])
    return jsonify({"success": True, "vibrated_ms": ms})

@app.route('/api/toast', methods=['POST', 'OPTIONS'])
def api_toast():
    if request.method == 'OPTIONS':
        return jsonify({})
    data = request.get_json() or {}
    msg = data.get("message", "Toast notification")
    run_cmd(["termux-toast", "-s", msg])
    return jsonify({"success": True, "message": msg})

@app.route('/api/terminal', methods=['POST', 'OPTIONS'])
def api_terminal():
    if request.method == 'OPTIONS':
        return jsonify({})
    data = request.get_json() or {}
    cmd = data.get("command", "uptime")
    try:
        env = os.environ.copy()
        env["PATH"] = "/data/data/com.termux/files/usr/bin:" + env.get("PATH", "")
        res = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10, env=env)
        output = res.stdout if res.stdout else res.stderr
        return jsonify({"output": output.strip()})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, threaded=True)

#!/usr/bin/env python3
"""
Android Edge Sentinel CLI & Client SDK
"""
import sys
import os
import json
import argparse
import urllib.request
import urllib.parse

GATEWAY_URL = os.environ.get("SENTINEL_GATEWAY_URL", "http://100.123.244.85:8000")

def get(path):
    url = f"{GATEWAY_URL}{path}"
    req = urllib.request.Request(url, headers={"User-Agent": "SentinelCLI/1.0"})
    with urllib.request.urlopen(req, timeout=10) as resp:
        return resp.read()

def post(path, data_dict):
    url = f"{GATEWAY_URL}{path}"
    data = json.dumps(data_dict).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json", "User-Agent": "SentinelCLI/1.0"})
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read().decode("utf-8"))

def main():
    parser = argparse.ArgumentParser(description="Android Edge Sentinel CLI")
    parser.add_argument("--status", action="store_true", help="Get node status & battery level")
    parser.add_argument("--gps", action="store_true", help="Get live GPS coordinates")
    parser.add_argument("--torch", choices=["on", "off"], help="Toggle flashlight")
    parser.add_argument("--vibrate", type=int, help="Vibrate phone for N milliseconds")
    parser.add_argument("--speak", type=str, help="Speak text via Text-to-Speech")
    parser.add_argument("--toast", type=str, help="Show Android toast message")
    parser.add_argument("--snap", type=str, help="Capture photo and save to file path")
    parser.add_argument("--camera", type=int, default=0, help="Camera sensor ID (0=rear, 1=front)")
    parser.add_argument("--cmd", type=str, help="Execute remote shell command on node")
    
    args = parser.parse_args()

    try:
        if args.status:
            data = json.loads(get("/api/dashboard/all").decode("utf-8"))
            b = data.get("battery", {})
            s = data.get("system", {})
            print(f"📱 Device: realme XT (Snapdragon 712 ARM64)")
            print(f"⚡ Battery: {b.get('percentage', 0)}% ({b.get('plugged', 'UNKNOWN')}) • Temp: {b.get('temperature', 0)}°C • {b.get('voltage', 0)} mV")
            print(f"💻 System: Load {s.get('load', 'N/A')} • RAM {s.get('memory', 'N/A')} • Uptime {s.get('uptime', 'N/A')}")
            
        elif args.gps:
            data = json.loads(get("/api/location/fix?provider=gps&request=once").decode("utf-8"))
            print(f"📍 GPS Location:")
            print(f"   Latitude:  {data.get('latitude', 0)}° N")
            print(f"   Longitude: {data.get('longitude', 0)}° E")
            print(f"   Altitude:  {data.get('altitude', 0)} m")
            print(f"   Accuracy:  ±{data.get('accuracy', 0)} m")
            print(f"   Provider:  {data.get('provider', 'gps')}")
            print(f"   Maps URL:  https://www.google.com/maps?q={data.get('latitude')},{data.get('longitude')}")

        elif args.torch:
            res = post("/api/torch", {"state": args.torch})
            print(f"🔦 Torch {args.torch.upper()}: {res.get('success')}")

        elif args.vibrate:
            res = post("/api/vibrate", {"duration_ms": args.vibrate})
            print(f"📳 Vibrated {args.vibrate}ms: {res.get('success')}")

        elif args.speak:
            res = post("/api/tts", {"text": args.speak})
            print(f"🗣️ Spoken '{args.speak}': {res.get('success')}")

        elif args.toast:
            res = post("/api/toast", {"message": args.toast})
            print(f"💬 Toast sent: {res.get('success')}")

        elif args.snap:
            raw = get(f"/api/camera/snap?camera={args.camera}")
            with open(args.snap, "wb") as f:
                f.write(raw)
            print(f"📸 Captured {len(raw)} bytes to {args.snap}")

        elif args.cmd:
            res = post("/api/terminal", {"command": args.cmd})
            print(res.get("output", res.get("error", "")))

        else:
            parser.print_help()

    except Exception as e:
        print(f"❌ Error communicating with Edge Sentinel ({GATEWAY_URL}): {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()

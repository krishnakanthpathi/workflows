#!/usr/bin/env bash
# Android Edge Sentinel REST API Curl Recipes

NODE_URL="http://100.123.244.85:8000"

echo "=== 1. Health Status & Uptime ==="
curl -s "${NODE_URL}/api/status" | jq .

echo -e "\n=== 2. Full Telemetry (Battery, CPU, Sensors) ==="
curl -s "${NODE_URL}/api/dashboard/all" | jq .

echo -e "\n=== 3. GPS GNSS Real-Time Location ==="
curl -s "${NODE_URL}/api/location/fix?provider=gps&request=once" | jq .

echo -e "\n=== 4. Speak Announcement ==="
curl -s -X POST "${NODE_URL}/api/tts" \
  -H "Content-Type: application/json" \
  -d '{"text": "Homelab edge node online"}' | jq .

echo -e "\n=== 5. Toggle Flashlight Torch ON then OFF ==="
curl -s -X POST "${NODE_URL}/api/torch" -H "Content-Type: application/json" -d '{"state": "on"}' | jq .
sleep 1
curl -s -X POST "${NODE_URL}/api/torch" -H "Content-Type: application/json" -d '{"state": "off"}' | jq .

echo -e "\n=== 6. Haptic Vibration 500ms ==="
curl -s -X POST "${NODE_URL}/api/vibrate" -H "Content-Type: application/json" -d '{"duration_ms": 500}' | jq .
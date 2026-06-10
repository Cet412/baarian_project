#!/bin/sh
# Generate ESP32cam/secrets.h from environment variables.
# Usage:
#   export WIFI_SSID="your-ssid"
#   export WIFI_PASSWORD="your-password"
#   ./secrets.sh
# Or edit this file and run it to refresh secrets.h.

WIFI_SSID="${WIFI_SSID:-YOUR_SSID}"
WIFI_PASSWORD="${WIFI_PASSWORD:-YOUR_PASSWORD}"

cat > secrets.h <<EOF
#pragma once
const char* WIFI_SSID = "${WIFI_SSID}";
const char* WIFI_PASSWORD = "${WIFI_PASSWORD}";
EOF

echo "Generated secrets.h with current WiFi values."

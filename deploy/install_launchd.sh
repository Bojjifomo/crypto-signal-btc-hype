#!/usr/bin/env bash
# Pasang monitor sebagai launchd agent di macOS: jalan tiap hari 07:15 waktu lokal Mac.
# Pakai:   ./deploy/install_launchd.sh            pasang + langsung jalan sekali
#          ./deploy/install_launchd.sh --remove   copot
# Kalau Mac lagi sleep pas jam itu, launchd jalanin begitu Mac bangun.
set -euo pipefail

LABEL="local.cryptomonitor"
HOUR="${HOUR:-7}"
MINUTE="${MINUTE:-15}"
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PLIST="$HOME/Library/LaunchAgents/$LABEL.plist"
DOMAIN="gui/$(id -u)"

if [[ "${1:-}" == "--remove" ]]; then
  launchctl bootout "$DOMAIN/$LABEL" 2>/dev/null || true
  rm -f "$PLIST"
  echo "dicopot: $LABEL"
  exit 0
fi

# Cari python 3.11+ (tomllib). Bisa dipaksa lewat PYTHON=/path/ke/python3.
PY="${PYTHON:-}"
if [[ -z "$PY" ]]; then
  for cand in /opt/homebrew/bin/python3 /usr/local/bin/python3 "$(command -v python3 || true)"; do
    [[ -n "$cand" && -x "$cand" ]] || continue
    if "$cand" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)' 2>/dev/null; then
      PY="$cand"; break
    fi
  done
fi
if [[ -z "$PY" ]]; then
  echo "Nggak nemu Python 3.11+. Install dulu: brew install python@3.13" >&2
  exit 1
fi

LOGS="$REPO/logs"
mkdir -p "$LOGS" "$(dirname "$PLIST")"

cat > "$PLIST" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key><string>$LABEL</string>
  <key>ProgramArguments</key>
  <array>
    <string>$PY</string>
    <string>-m</string>
    <string>cryptomonitor</string>
    <string>all</string>
  </array>
  <key>WorkingDirectory</key><string>$REPO</string>
  <key>StartCalendarInterval</key>
  <dict>
    <key>Hour</key><integer>$HOUR</integer>
    <key>Minute</key><integer>$MINUTE</integer>
  </dict>
  <key>StandardOutPath</key><string>$LOGS/launchd.log</string>
  <key>StandardErrorPath</key><string>$LOGS/launchd.log</string>
  <key>ProcessType</key><string>Background</string>
</dict>
</plist>
PLIST

if [[ "${DRY_RUN:-}" == "1" ]]; then
  echo "DRY_RUN: plist ditulis ke $PLIST, launchctl dilewati"
  exit 0
fi

plutil -lint "$PLIST" >/dev/null
launchctl bootout "$DOMAIN/$LABEL" 2>/dev/null || true
launchctl bootstrap "$DOMAIN" "$PLIST"
launchctl enable "$DOMAIN/$LABEL"
launchctl kickstart -k "$DOMAIN/$LABEL"   # langsung jalan sekali sekarang

cat <<MSG
Terpasang: $LABEL
  python : $PY
  repo   : $REPO
  jadwal : tiap hari $(printf '%02d:%02d' "$HOUR" "$MINUTE") waktu lokal Mac
  log    : $LOGS/launchd.log
  hasil  : $REPO/report.md dan $REPO/dashboard.html (dihitung ulang tiap jalan)
Cek status: launchctl print $DOMAIN/$LABEL | head -20
MSG

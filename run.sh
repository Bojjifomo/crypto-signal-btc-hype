#!/usr/bin/env bash
# Jalanin fetch + backtest + skor hari ini.
set -euo pipefail
cd "$(dirname "$0")"
exec python3 -m cryptomonitor all "$@"

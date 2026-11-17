"""CLI: python -m cryptomonitor fetch|backtest|score|all"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from cryptomonitor.engine import publish
from cryptomonitor.fetch import run_fetch
from cryptomonitor.lib import load_config, repo_root


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="cryptomonitor",
        description="Monitor sinyal beli BTC & HYPE, plus backtest skor DCA.",
    )
    parser.add_argument("--db", type=Path, default=Path("data/monitor.db"))
    parser.add_argument("--config", type=Path, default=None)
    parser.add_argument("--report", type=Path, default=Path("report.md"))
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("fetch", help="Tarik data publik ke SQLite")
    sub.add_parser("backtest", help="Hitung skor v1/v2 dan tulis report.md")
    sub.add_parser("score", help="Cetak skor hari ini (sekaligus segarkan laporan)")
    sub.add_parser("all", help="fetch, lalu backtest + skor")
    args = parser.parse_args(argv)
    cfg = load_config(args.config)
    db = args.db if args.db.is_absolute() else repo_root() / args.db
    report = args.report if args.report.is_absolute() else repo_root() / args.report
    # Jalankan dari folder lain tetap nemu config, DB, dan laporan di repo.
    if args.cmd in ("fetch", "all"):
        code = run_fetch(db, cfg)
        if args.cmd == "fetch" or code != 0:
            return code
    return publish(db, cfg, report)


if __name__ == "__main__":
    sys.exit(main())

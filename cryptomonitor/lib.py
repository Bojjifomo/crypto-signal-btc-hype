"""HTTP, SQLite, tanggal, dan format angka Indonesia (titik ribuan, koma desimal, jt/M)."""

from __future__ import annotations

import json
import sqlite3
import time
import tomllib
import urllib.error
import urllib.request
from datetime import date, datetime, timezone
from pathlib import Path

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
)

SCHEMA = """
CREATE TABLE IF NOT EXISTS prices (
    asset TEXT NOT NULL,
    date TEXT NOT NULL,
    close REAL NOT NULL,
    source TEXT NOT NULL,
    PRIMARY KEY (asset, date)
);
CREATE TABLE IF NOT EXISTS funding (
    asset TEXT NOT NULL,
    ts INTEGER NOT NULL,
    rate REAL NOT NULL,
    source TEXT NOT NULL,
    PRIMARY KEY (asset, ts)
);
CREATE TABLE IF NOT EXISTS open_interest (
    asset TEXT NOT NULL,
    date TEXT NOT NULL,
    oi_usd REAL,
    oi_coin REAL,
    source TEXT NOT NULL,
    PRIMARY KEY (asset, date)
);
CREATE TABLE IF NOT EXISTS fear_greed (
    date TEXT PRIMARY KEY,
    value INTEGER NOT NULL,
    classification TEXT
);
CREATE TABLE IF NOT EXISTS etf_flows (
    date TEXT PRIMARY KEY,
    flow_usd REAL NOT NULL,
    source TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS stablecoin_supply (
    date TEXT PRIMARY KEY,
    supply_usd REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS dominance (
    date TEXT PRIMARY KEY,
    btc_pct REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS fx_usd_idr (
    date TEXT PRIMARY KEY,
    rate REAL NOT NULL,
    source TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS metrics (
    asset TEXT NOT NULL,
    date TEXT NOT NULL,
    name TEXT NOT NULL,
    value REAL NOT NULL,
    source TEXT NOT NULL,
    PRIMARY KEY (asset, date, name)
);
CREATE TABLE IF NOT EXISTS fetch_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts TEXT NOT NULL,
    source TEXT NOT NULL,
    ok INTEGER NOT NULL,
    detail TEXT
);
CREATE TABLE IF NOT EXISTS meta (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
"""


def repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def load_config(path: Path | None = None) -> dict:
    path = path or (repo_root() / "config.toml")
    with path.open("rb") as handle:
        return tomllib.load(handle)


def today_utc() -> date:
    return datetime.now(timezone.utc).date()


def utc_date_from_ms(ms: int) -> date:
    return datetime.fromtimestamp(ms / 1000, timezone.utc).date()


def utc_date_from_s(sec: int | float) -> date:
    return datetime.fromtimestamp(float(sec), timezone.utc).date()


def parse_iso(value: str) -> date:
    return date.fromisoformat(value)


def http_bytes(
    url: str,
    *,
    method: str = "GET",
    body: bytes | None = None,
    headers: dict | None = None,
    timeout: int = 45,
    retries: int = 3,
) -> bytes:
    hdrs = {"User-Agent": USER_AGENT, "Accept": "*/*"}
    if headers:
        hdrs.update(headers)
    last: Exception | None = None
    for attempt in range(retries):
        req = urllib.request.Request(url, data=body, headers=hdrs, method=method)
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return resp.read()
        except urllib.error.HTTPError as exc:
            last = exc
            if exc.code in (400, 401, 403, 404, 409, 451):
                raise
            time.sleep(0.5 * (attempt + 1))
        except urllib.error.URLError as exc:
            last = exc
            time.sleep(0.5 * (attempt + 1))
    assert last is not None
    raise last


def http_json(url: str, **kwargs):
    raw = http_bytes(url, **kwargs)
    return json.loads(raw.decode("utf-8"))


def http_post_json(url: str, payload: dict, **kwargs):
    body = json.dumps(payload).encode()
    headers = dict(kwargs.pop("headers", {}) or {})
    headers["Content-Type"] = "application/json"
    return http_json(url, method="POST", body=body, headers=headers, **kwargs)


def connect(path: Path) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    return conn


def log_fetch(conn: sqlite3.Connection, source: str, ok: bool, detail: str) -> None:
    conn.execute(
        "INSERT INTO fetch_log (ts, source, ok, detail) VALUES (?, ?, ?, ?)",
        (datetime.now(timezone.utc).isoformat(timespec="seconds"), source, 1 if ok else 0, detail[:500]),
    )


def set_meta(conn: sqlite3.Connection, key: str, value: str) -> None:
    conn.execute(
        "INSERT INTO meta(key, value) VALUES(?, ?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
        (key, value),
    )


def get_meta(conn: sqlite3.Connection, key: str) -> str | None:
    row = conn.execute("SELECT value FROM meta WHERE key=?", (key,)).fetchone()
    return None if row is None else row["value"]


def upsert_prices(conn: sqlite3.Connection, rows: list[tuple]) -> None:
    conn.executemany(
        """
        INSERT INTO prices(asset, date, close, source) VALUES (?,?,?,?)
        ON CONFLICT(asset, date) DO UPDATE SET close=excluded.close, source=excluded.source
        """,
        rows,
    )


def upsert_funding(conn: sqlite3.Connection, rows: list[tuple]) -> None:
    # rows: asset, ts, rate, source. Binance menang kalau tabrakan dengan OKX.
    conn.executemany(
        """
        INSERT INTO funding(asset, ts, rate, source) VALUES (?,?,?,?)
        ON CONFLICT(asset, ts) DO UPDATE SET
            rate=excluded.rate,
            source=excluded.source
        WHERE funding.source != 'binance' OR excluded.source = 'binance'
        """,
        rows,
    )


def load_prices(conn: sqlite3.Connection, asset: str) -> list[tuple[date, float]]:
    rows = conn.execute(
        "SELECT date, close FROM prices WHERE asset=? ORDER BY date",
        (asset,),
    ).fetchall()
    return [(date.fromisoformat(r["date"]), float(r["close"])) for r in rows]


def load_funding_daily(conn: sqlite3.Connection, asset: str) -> dict[date, float]:
    rows = conn.execute(
        "SELECT ts, rate, source FROM funding WHERE asset=? ORDER BY ts",
        (asset,),
    ).fetchall()
    buckets: dict[date, dict[str, list[float]]] = {}
    for row in rows:
        day = utc_date_from_ms(int(row["ts"]))
        buckets.setdefault(day, {}).setdefault(row["source"], []).append(float(row["rate"]))
    out: dict[date, float] = {}
    for day, by_src in buckets.items():
        rates = by_src.get("binance") or by_src.get("okx") or by_src.get("hyperliquid")
        if not rates:
            rates = next(iter(by_src.values()))
        out[day] = sum(rates) / len(rates)
    return out


def upsert_metrics(conn: sqlite3.Connection, rows: list[tuple]) -> None:
    # rows: asset, date, name, value, source
    conn.executemany(
        """
        INSERT INTO metrics(asset, date, name, value, source) VALUES (?,?,?,?,?)
        ON CONFLICT(asset, date, name) DO UPDATE SET value=excluded.value, source=excluded.source
        """,
        rows,
    )


def load_metric(conn: sqlite3.Connection, asset: str, name: str) -> dict[date, float]:
    rows = conn.execute(
        "SELECT date, value FROM metrics WHERE asset=? AND name=?",
        (asset, name),
    ).fetchall()
    return {date.fromisoformat(r["date"]): float(r["value"]) for r in rows}


def load_funding_apr(conn: sqlite3.Connection, asset: str) -> dict[date, float]:
    """Funding per hari, disetahunkan: jumlah print sehari x 365.

    Binance/OKX 3 print sehari, Hyperliquid 24. Dijumlah per hari biar dua-duanya
    bisa dibandingin pakai satuan yang sama.
    """
    rows = conn.execute(
        "SELECT ts, rate, source FROM funding WHERE asset=? ORDER BY ts",
        (asset,),
    ).fetchall()
    buckets: dict[date, dict[str, float]] = {}
    for row in rows:
        day = utc_date_from_ms(int(row["ts"]))
        by_src = buckets.setdefault(day, {})
        by_src[row["source"]] = by_src.get(row["source"], 0.0) + float(row["rate"])
    out: dict[date, float] = {}
    for day, by_src in buckets.items():
        for src in ("binance", "okx", "hyperliquid"):
            if src in by_src:
                out[day] = by_src[src] * 365.0
                break
        else:
            out[day] = next(iter(by_src.values())) * 365.0
    return out


def load_fear_greed(conn: sqlite3.Connection) -> dict[date, int]:
    rows = conn.execute("SELECT date, value FROM fear_greed").fetchall()
    return {date.fromisoformat(r["date"]): int(r["value"]) for r in rows}


def load_etf(conn: sqlite3.Connection) -> dict[date, float]:
    rows = conn.execute("SELECT date, flow_usd FROM etf_flows").fetchall()
    return {date.fromisoformat(r["date"]): float(r["flow_usd"]) for r in rows}


def load_fx(conn: sqlite3.Connection) -> dict[date, float]:
    rows = conn.execute("SELECT date, rate FROM fx_usd_idr").fetchall()
    return {date.fromisoformat(r["date"]): float(r["rate"]) for r in rows}


def latest_fetch_notes(conn: sqlite3.Connection) -> list[str]:
    raw = get_meta(conn, "fetch_notes")
    if not raw:
        return []
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return [raw]
    return [str(item) for item in data]


def fmt_number(n: float, digits: int = 0) -> str:
    """1234.5, 1 digit → '1.234,5'."""
    sign = "-" if n < 0 else ""
    text = f"{abs(float(n)):.{max(digits, 0)}f}"
    whole, _, frac = text.partition(".")
    groups: list[str] = []
    while whole:
        groups.append(whole[-3:])
        whole = whole[:-3]
    whole_fmt = ".".join(reversed(groups)) if groups else "0"
    if digits <= 0:
        return sign + whole_fmt
    return f"{sign}{whole_fmt},{frac}"


def _strip_frac(text: str) -> str:
    if "," not in text:
        return text
    whole, frac = text.split(",", 1)
    frac = frac.rstrip("0")
    if not frac:
        return whole
    return f"{whole},{frac}"


def fmt_compact(n: float, digits: int = 1) -> str:
    """30_000_000 → '30jt'. 7_500_000 → '7,5jt'. 1_200_000_000 → '1,2M'."""
    sign = "-" if n < 0 else ""
    magnitude = abs(float(n))
    if magnitude >= 1e12:
        num, unit = magnitude / 1e12, "T"
    elif magnitude >= 1e9:
        num, unit = magnitude / 1e9, "M"
    elif magnitude >= 1e6:
        num, unit = magnitude / 1e6, "jt"
    else:
        return sign + fmt_number(magnitude, 0)
    return sign + _strip_frac(fmt_number(num, digits)) + unit


def fmt_idr(n: float | None, digits: int = 1) -> str:
    if n is None:
        return "—"
    return "Rp " + fmt_compact(n, digits)


def fmt_usd(n: float | None, digits: int = 1) -> str:
    if n is None:
        return "—"
    if n < 0:
        return "-$" + fmt_compact(abs(n), digits)
    return "$" + fmt_compact(n, digits)


def fmt_px(n: float | None) -> str:
    if n is None:
        return "—"
    if abs(n) >= 1000:
        return "$" + fmt_number(n, 0)
    return "$" + fmt_number(n, 2)


def fmt_pct(x: float | None, digits: int = 1) -> str:
    if x is None:
        return "—"
    body = fmt_number(abs(x) * 100, digits)
    if body.replace(".", "").replace(",", "").strip("0") == "":
        return body + "%"
    sign = "+" if x > 0 else "-"
    return sign + body + "%"


def fmt_win(x: float | None, digits: int = 1) -> str:
    if x is None:
        return "—"
    return fmt_number(x * 100, digits) + "%"

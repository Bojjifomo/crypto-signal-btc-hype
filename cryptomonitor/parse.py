"""Parser murni. Nggak nyentuh jaringan, biar gampang dites."""

from __future__ import annotations

import csv
import io
import zipfile
from datetime import date, datetime, timezone
from html.parser import HTMLParser

_MONTHS = {
    "jan": 1,
    "feb": 2,
    "mar": 3,
    "apr": 4,
    "may": 5,
    "jun": 6,
    "jul": 7,
    "aug": 8,
    "sep": 9,
    "oct": 10,
    "nov": 11,
    "dec": 12,
}


class _TableParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.tables: list[list[list[str]]] = []
        self._table: list[list[str]] | None = None
        self._row: list[str] | None = None
        self._cell: list[str] | None = None

    def handle_starttag(self, tag: str, attrs) -> None:
        if tag == "table":
            self._table = []
        elif tag == "tr" and self._table is not None:
            self._row = []
        elif tag in ("td", "th") and self._row is not None:
            self._cell = []

    def handle_endtag(self, tag: str) -> None:
        if tag in ("td", "th") and self._cell is not None and self._row is not None:
            self._row.append("".join(self._cell).strip())
            self._cell = None
        elif tag == "tr" and self._row is not None and self._table is not None:
            if any(cell.strip() for cell in self._row):
                self._table.append(self._row)
            self._row = None
        elif tag == "table" and self._table is not None:
            self.tables.append(self._table)
            self._table = None

    def handle_data(self, data: str) -> None:
        if self._cell is not None:
            self._cell.append(data)


def parse_flow_cell(raw: str) -> float | None:
    text = raw.strip().replace("\xa0", "").replace(" ", "")
    if text in {"", "-", "—", "–", "n/a", "N/A"}:
        return None
    negative = text.startswith("(") and text.endswith(")")
    text = text.strip("()")
    text = text.replace(",", "")
    try:
        value = float(text)
    except ValueError:
        return None
    return -value if negative else value


def parse_farside_date(raw: str) -> date | None:
    text = " ".join(raw.split())
    iso = _try_iso(text)
    if iso:
        return iso
    parts = text.replace(",", "").split(" ")
    if len(parts) != 3:
        return None
    if parts[0].isdigit():
        day_s, mon_s, year_s = parts
    elif parts[1].isdigit():
        mon_s, day_s, year_s = parts
    else:
        return None
    month = _MONTHS.get(mon_s[:3].lower())
    if month is None or not year_s.isdigit():
        return None
    try:
        return date(int(year_s), month, int(day_s))
    except ValueError:
        return None


def _try_iso(text: str) -> date | None:
    if len(text) >= 10 and text[4] == "-" and text[7] == "-":
        try:
            return date.fromisoformat(text[:10])
        except ValueError:
            return None
    return None


def parse_farside_html(html: str) -> list[tuple[date, float]]:
    """Tabel Farside: kolom Total dalam juta USD. Baris ringkasan dibuang."""
    parser = _TableParser()
    parser.feed(html)
    best: list[tuple[date, float]] = []
    for table in parser.tables:
        parsed = _rows_from_table(table)
        if len(parsed) > len(best):
            best = parsed
    return best


def _rows_from_table(table: list[list[str]]) -> list[tuple[date, float]]:
    total_idx = None
    for row in table[:8]:
        # Baris ringkasan "Total / Average / ..." bukan header kolom.
        if row and row[0].strip().lower() in {"total", "average", "maximum", "minimum", "avg"}:
            continue
        for idx, cell in enumerate(row):
            if cell.strip().lower() == "total":
                total_idx = idx
                break
        if total_idx is not None:
            break
    if total_idx is None:
        total_idx = -1
    skip = {"fee", "total", "average", "maximum", "minimum", "avg"}
    out: list[tuple[date, float]] = []
    for row in table:
        if not row:
            continue
        label = row[0].strip().lower()
        if label in skip:
            continue
        day = parse_farside_date(row[0])
        if day is None:
            continue
        cell = row[total_idx] if total_idx >= 0 else row[-1]
        if total_idx >= len(row):
            cell = row[-1]
        value = parse_flow_cell(cell)
        if value is None:
            continue
        out.append((day, value * 1_000_000))
    return out


def parse_etf_csv(text: str) -> list[tuple[date, float]]:
    """CSV cadangan: kolom day, etfFlow dalam USD (bukan juta)."""
    handle = io.StringIO(text)
    reader = csv.DictReader(handle)
    out: list[tuple[date, float]] = []
    if reader.fieldnames is None:
        return out
    fields = {name.strip().lower(): name for name in reader.fieldnames}
    day_key = fields.get("day") or fields.get("date")
    flow_key = fields.get("etfflow") or fields.get("flow") or fields.get("flow_usd")
    if day_key is None or flow_key is None:
        raise ValueError(f"kolom CSV ETF nggak dikenal: {reader.fieldnames}")
    for row in reader:
        raw_day = (row.get(day_key) or "").strip()
        raw_flow = (row.get(flow_key) or "").strip()
        if not raw_day or not raw_flow:
            continue
        day = parse_farside_date(raw_day)
        value = parse_flow_cell(raw_flow)
        if day is None or value is None:
            continue
        out.append((day, value))
    return out


def parse_binance_funding_csv(text: str) -> list[tuple[int, float]]:
    out: list[tuple[int, float]] = []
    for line in text.splitlines():
        parts = [part.strip() for part in line.split(",")]
        if len(parts) < 3:
            continue
        try:
            ts = int(float(parts[0]))
            rate = float(parts[2])
        except ValueError:
            continue
        out.append((ts, rate))
    return out


def parse_binance_funding_zip(blob: bytes) -> list[tuple[int, float]]:
    with zipfile.ZipFile(io.BytesIO(blob)) as archive:
        names = [name for name in archive.namelist() if name.endswith(".csv")]
        if not names:
            return []
        text = archive.read(names[0]).decode("utf-8")
    return parse_binance_funding_csv(text)


def parse_binance_klines(payload: list) -> list[tuple[date, float]]:
    out: list[tuple[date, float]] = []
    for candle in payload:
        open_ms = int(candle[0])
        close = float(candle[4])
        day = datetime.fromtimestamp(open_ms / 1000, timezone.utc).date()
        out.append((day, close))
    return out

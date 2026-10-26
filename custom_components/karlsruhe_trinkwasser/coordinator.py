"""DataUpdateCoordinator for Karlsruhe Trinkwasser."""
from __future__ import annotations

import logging
import re
import zlib
import struct
from datetime import timedelta

import aiohttp

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    DIGIT_TEMPLATES,
    DOMAIN,
    IMAGE_BASE_URL,
    PAGE_URL,
    SENSOR_KEYS,
)

_LOGGER = logging.getLogger(__name__)

_IMG_RE = re.compile(
    r"/wMedia/img/produkte/trinkwasser/messwerte/weblication/wThumbnails/"
    r"([a-z]+)-[0-9a-f]+-[0-9a-f]+@100w\.png"
)
_TS_RE = re.compile(r"Letzte Abfrage am:\s*(.+?)(?:</h|$)", re.IGNORECASE)


# ---------------------------------------------------------------------------
# Low-level PNG OCR (pure Python – no external dependencies)
# ---------------------------------------------------------------------------

def _decode_png_rows(data: bytes) -> list[list[int]] | None:
    """Decode a 100×150 4-bit indexed PNG into a list of pixel rows."""
    try:
        chunks: dict[str, list[bytes]] = {}
        i = 8
        while i < len(data) - 12:
            length = struct.unpack(">I", data[i : i + 4])[0]
            ctype = data[i + 4 : i + 8].decode("ascii", errors="replace")
            chunks.setdefault(ctype, []).append(data[i + 8 : i + 8 + length])
            i += 12 + length

        raw = zlib.decompress(b"".join(chunks["IDAT"]))
        width = struct.unpack(">I", chunks["IHDR"][0][:4])[0]
        stride = width // 2 + 1
        rows: list[list[int]] = []
        for r in range(150):
            row_data = raw[r * stride + 1 : r * stride + 1 + width // 2]
            px: list[int] = []
            for byte in row_data:
                px.append((byte >> 4) & 0xF)
                px.append(byte & 0xF)
            rows.append(px[:width])
        return rows
    except Exception as err:  # noqa: BLE001
        _LOGGER.debug("PNG decode failed: %s", err)
        return None


def _is_dark(p: int) -> bool:
    return p in (0, 1, 3)


def _col_projection(rows: list[list[int]], r_start: int, r_end: int) -> list[int]:
    counts = [0] * 100
    for r in range(r_start, r_end + 1):
        for c in range(100):
            if _is_dark(rows[r][c]):
                counts[c] += 1
    return counts


def _segment(counts: list[int]) -> list[tuple[int, int]]:
    """Find character segments, bridging single-pixel gaps and splitting wide spans."""
    active = [counts[c] > 0 for c in range(100)]
    # Bridge single-pixel gaps (anti-aliasing artefacts inside a digit)
    for c in range(1, 99):
        if not active[c] and active[c - 1] and active[c + 1]:
            active[c] = True

    in_seg: bool
    in_seg, start, basic = False, 0, []
    for c in range(100):
        if active[c] and not in_seg:
            in_seg, start = True, c
        elif not active[c] and in_seg:
            in_seg = False
            basic.append((start, c - 1))
    if in_seg:
        basic.append((start, 99))

    result: list[tuple[int, int]] = []
    for s, e in basic:
        w = e - s + 1
        if w <= 9:
            result.append((s, e))
            continue
        # Wide span: split into ~7 px chunks at local minima
        n_parts = round(w / 7)
        current: list[tuple[int, int]] = [(s, e)]
        for _ in range(n_parts - 1):
            widest = max(current, key=lambda x: x[1] - x[0])
            ws, we = widest
            center = (ws + we) // 2
            best_pos, best_dist = None, 999
            for i in range(ws + 1, we):
                if counts[i] <= counts[i - 1] and counts[i] <= counts[i + 1]:
                    d = abs(i - center)
                    if d < best_dist:
                        best_dist, best_pos = d, i
            if best_pos is None:
                break
            current.remove(widest)
            current.extend([(ws, best_pos - 1), (best_pos, we)])
        result.extend(sorted(current))
    return result


def _char_bitmap(
    rows: list[list[int]], s: int, e: int, r_start: int, r_end: int
) -> tuple:
    return tuple(
        1 if _is_dark(rows[r][c]) else 0
        for r in range(r_start, r_end + 1)
        for c in range(s, e + 1)
    )


def _ocr_image(data: bytes) -> float | None:
    """Extract a numeric value from a Weblication gauge PNG."""
    rows = _decode_png_rows(data)
    if rows is None:
        return None

    # Locate the text rows (rows with significant dark pixels, excluding borders)
    r_start = r_end = None
    for r in range(1, 149):
        if sum(1 for p in rows[r][2:98] if _is_dark(p)) > 3:
            if r_start is None:
                r_start = r
            r_end = r
    if r_start is None:
        return None

    counts = _col_projection(rows, r_start, r_end)
    segs = _segment(counts)
    # Discard border segments (column 0–1 and 98–99)
    char_segs = [(s, e) for s, e in segs if 1 < s < 98 and 1 < e < 98]
    if not char_segs:
        return None

    digits: list[str] = []
    for s, e in char_segs:
        bm = _char_bitmap(rows, s, e, r_start, r_end)
        ch = DIGIT_TEMPLATES.get((e - s + 1, bm))
        if ch is None:
            _LOGGER.debug("Unknown character at cols %d-%d (width=%d)", s, e, e - s + 1)
            return None
        digits.append(ch)

    value_str = "".join(digits)
    try:
        return float(value_str)
    except ValueError:
        _LOGGER.debug("OCR produced non-numeric string: %s", value_str)
        return None


# ---------------------------------------------------------------------------
# Coordinator
# ---------------------------------------------------------------------------

class TrinkwasserCoordinator(DataUpdateCoordinator):
    """Fetches all Trinkwasser measurements from Stadtwerke Karlsruhe."""

    def __init__(self, hass: HomeAssistant, scan_interval: int) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=scan_interval),
        )

    async def _async_update_data(self) -> dict:
        try:
            async with aiohttp.ClientSession() as session:
                # Fetch the main page to get image URLs + timestamp
                async with session.get(
                    PAGE_URL, timeout=aiohttp.ClientTimeout(total=30)
                ) as resp:
                    resp.raise_for_status()
                    html = await resp.text(errors="replace")

                # Parse image URLs (key = sensor key like "temperatur")
                img_urls: dict[str, str] = {}
                for m in _IMG_RE.finditer(html):
                    key = m.group(1)
                    if key in SENSOR_KEYS and key not in img_urls:
                        img_urls[key] = IMAGE_BASE_URL + m.group(0)

                # Parse "Letzte Abfrage" timestamp from heading text
                timestamp: str | None = None
                ts_m = _TS_RE.search(html)
                if ts_m:
                    timestamp = ts_m.group(1).strip()

                # Fetch + OCR each gauge image
                result: dict = {"timestamp": timestamp}
                for key, url in img_urls.items():
                    async with session.get(
                        url, timeout=aiohttp.ClientTimeout(total=15)
                    ) as img_resp:
                        img_resp.raise_for_status()
                        png_data = await img_resp.read()
                    value = await self.hass.async_add_executor_job(_ocr_image, png_data)
                    result[key] = value
                    if value is None:
                        _LOGGER.warning("OCR failed for %s (%s)", key, url)

                missing = [k for k in SENSOR_KEYS if k not in result]
                if missing:
                    _LOGGER.warning("Missing sensors: %s", missing)

                return result

        except aiohttp.ClientError as err:
            raise UpdateFailed(f"Verbindungsfehler: {err}") from err
        except Exception as err:
            raise UpdateFailed(f"Unerwarteter Fehler: {err}") from err

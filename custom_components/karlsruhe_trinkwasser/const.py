"""Constants for Karlsruhe Trinkwasser integration."""

DOMAIN = "karlsruhe_trinkwasser"

PAGE_URL = (
    "https://www.stadtwerke-karlsruhe.de/de/gk/wohnungswirtschaft"
    "/trinkwasser/wasserqualitaet.php"
)
IMAGE_BASE_URL = "https://www.stadtwerke-karlsruhe.de"

CONF_SCAN_INTERVAL = "scan_interval"
DEFAULT_SCAN_INTERVAL = 3600  # 1 hour

SCAN_INTERVAL_OPTIONS = [
    ("600", "10 Minuten"),
    ("3600", "1 Stunde"),
    ("86400", "1 Tag"),
]

SENSOR_KEYS = [
    "temperatur",
    "phwert",
    "leitfaehigkeit",
    "truebung",
    "sauerstoff",
    "nitrat",
]

SENSOR_META = {
    "temperatur":    {"name": "Temperatur",    "unit": "°C",     "icon": "mdi:thermometer-water"},
    "phwert":        {"name": "pH-Wert",        "unit": None,     "icon": "mdi:ph"},
    "leitfaehigkeit":{"name": "Leitfähigkeit", "unit": "µS/cm",  "icon": "mdi:lightning-bolt-circle"},
    "truebung":      {"name": "Trübung",        "unit": "NTU",    "icon": "mdi:water-opacity"},
    "sauerstoff":    {"name": "Sauerstoff",     "unit": "mg/l",   "icon": "mdi:molecule"},
    "nitrat":        {"name": "Nitrat",         "unit": "mg/l",   "icon": "mdi:test-tube"},
}

# ---------------------------------------------------------------------------
# Digit OCR – templates built from the Weblication CMS gauge images (100×150 px,
# 4-bit palette, text region rows 68–79).  Each key is (width, bitmap_tuple).
# ---------------------------------------------------------------------------

def _h(hex_str: str, n: int) -> tuple:
    """Decode hex-encoded bitmap back to a tuple of 0/1 ints."""
    bits = bin(int(hex_str, 16))[2:].zfill(len(hex_str) * 4)
    return tuple(int(b) for b in bits[:n])


DIGIT_TEMPLATES: dict[tuple, str] = {
    # "." width=1
    (1, _h("0010", 12)): ".",
    # "0" width=7
    (7, _h("388a14183060c1830911c0", 84)): "0",
    # "1" width=4
    (4, _h("137911111111", 48)): "1",
    # "2" width=7
    (7, _h("388a0810208208208207f0", 84)): "2",
    # "3" width=7
    (7, _h("308a1020c30181030d11c0", 84)): "3",
    # "4" width=8
    (8, _h("04040c1414240444ff040404", 96)): "4",
    # "5" width=7
    (7, _h("7e81020f988081030711c0", 84)): "5",
    # "6" width=7 (variant a)
    (7, _h("18880c0998a0c1830511c0", 84)): "6",
    # "6" width=7 (variant b)
    (7, _h("388a0c0b98a0c1830511c0", 84)): "6",
    # "7" width=7
    (7, _h("fe0c304082041820408300", 84)): "7",
    # "8" width=7 (variant a)
    (7, _h("388a1424473141830511c0", 84)): "8",
    # "8" width=7 (variant b)
    (7, _h("30881404471141830511c0", 84)): "8",
    # "9" width=7 (variant a)
    (7, _h("308a041830519903011180", 84)): "9",
    # "9" width=7 (variant b)
    (7, _h("388a0c18305199030911c0", 84)): "9",
}

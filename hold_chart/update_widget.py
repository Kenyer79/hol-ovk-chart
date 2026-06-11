"""
update_widget.py
Beolvassa az ovk_data.json-t és frissíti a hold_ovk_widget.html
adattömbjeit, hogy az iframe mindig friss adatot mutasson.

Futtatás: python update_widget.py
"""

import json
import re
from pathlib import Path
from datetime import datetime

# ── Fájlútvonalak ─────────────────────────────────────────────────────────────
BASE        = Path(__file__).parent
DATA_FILE   = BASE / "ovk_data.json"
WIDGET_FILE = BASE / "hold_ovk_widget.html"

# ── Havi ritkítás ────────────────────────────────────────────────────────────
def monthly_thin(series):
    """Napi sorozatból minden hónap UTOLSÓ kereskedési napját tartja meg.
    Az induló és a legutóbbi adatpont mindig benne marad."""
    if not series:
        return []
    by_month = {}
    for d, v in series:
        key = d[:7]  # "YYYY-MM"
        by_month[key] = [d, v]  # felülírás -> hónap utolsó napja marad
    result = list(by_month.values())
    result.sort(key=lambda x: x[0])
    return result
# ── Sorozat -> JS tömb string ─────────────────────────────────────────────────
def series_to_js(series):
    """[[date, val], ...] -> JS literál string a HTML-be"""
    lines = [f'  ["{d}",{v}]' for d, v in series]
    return "[\n" + ",\n".join(lines) + "\n]"

# ── Frissítő ─────────────────────────────────────────────────────────────────
def update():
    # JSON betöltés
    if not DATA_FILE.exists():
        raise FileNotFoundError(f"Nem található: {DATA_FILE}\nFuttasd először: python bamosz_scraper.py")

    data    = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    updated = data.get("updated", "–")
    series  = data.get("series", {})

    din  = monthly_thin(series.get("dinamikus", []))

    # Ha a fő sorozat üres, ne írjuk felül a HTML-t
    if len(din) < 10:
        print(f"  FIGYELEM: Dinamikus sorozat üres vagy hiányos ({len(din)} pont) – HTML nem módosul.")
        return

    # HTML betöltés
    if not WIDGET_FILE.exists():
        raise FileNotFoundError(f"Nem található: {WIDGET_FILE}")

    html = WIDGET_FILE.read_text(encoding="utf-8")

    # ── Adattömbök cseréje regex-szel ────────────────────────────────────────
    # A HTML-ben ezek a blokkok vannak jelölve:
    #   const DIN_RAW = [ ... ];
    #   const KIE_RAW = ...
    #   stb.

    # Csak DIN_RAW-t cseréljük – KIE/MEG/PMAP a JS-ben számított (map)
    replacements = {
        "DIN_RAW": series_to_js(din),
    }

    for varname, js_array in replacements.items():
        pattern     = rf"(const {varname}\s*=\s*)\[[\s\S]*?\](\s*;)"
        replacement = rf"\g<1>{js_array}\2"
        new_html, count = re.subn(pattern, replacement, html, count=1)
        if count == 0:
            print(f"  FIGYELEM: {varname} nem található a HTML-ben!")
        else:
            html = new_html
            print(f"  {varname}: {len(replacements[varname].splitlines())-2} adatpont frissítve")

    # Frissítési dátum a header-ben – magyar hónapnevek
    HU_MONTHS = ["január","február","március","április","május","június",
                 "július","augusztus","szeptember","október","november","december"]
    last_date = din[-1][0] if din else updated
    try:
        d   = datetime.strptime(last_date, "%Y-%m-%d")
        fmt = f"{d.year}. {HU_MONTHS[d.month-1]} {d.day}."
    except Exception:
        fmt = last_date

    # A <span id="lastUpdate"> tartalmát cseréljük, nem a JS sorát
    html = re.sub(
        r'(<span id="lastUpdate">)([^<]*)(</span>)',
        rf'\g<1>Frissítve: {fmt}\3',
        html
    )

    WIDGET_FILE.write_text(html, encoding="utf-8")
    print(f"\nWidget frissítve: {WIDGET_FILE}")
    print(f"Adat dátuma: {updated}")

if __name__ == "__main__":
    print(f"[{datetime.now():%Y-%m-%d %H:%M}] Widget frissítő indul...\n")
    update()

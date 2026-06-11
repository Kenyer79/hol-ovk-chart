"""
bamosz_scraper.py
Napi frissítő: lekéri a BAMOSZ alapoldalról az utolsó árfolyamot,
és hozzáfűzi a meglévő ovk_data.json sorozathoz.

A teljes history a JSON-ban marad – naponta csak 1 új pont adódik hozzá.
Ha az adat már szerepel (dátum egyezés), nem írja felül.

Futtatás: python bamosz_scraper.py
"""

import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime
from pathlib import Path

# ── Konfiguráció ──────────────────────────────────────────────────────────────
ISINS = {
    "dinamikus":  "HU0000727771",   # HOLD VK 300 A sor. HUF
    "kiegyen":    "HU0000727763",   # HOLD VK 200 A sor. HUF
    "megfontolt": "HU0000727748",   # HOLD VK 100 A sor. HUF
}

OUTPUT_FILE = Path(__file__).parent / "ovk_data.json"
BAMOSZ_URL  = "https://www.bamosz.hu/alapoldal"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "hu-HU,hu;q=0.9,en;q=0.8",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Referer": "https://www.bamosz.hu/",
}

# ── Meglévő JSON betöltése ────────────────────────────────────────────────────
def load_existing():
    """Betölti a meglévő ovk_data.json-t, vagy üres struktúrát ad vissza."""
    if OUTPUT_FILE.exists():
        try:
            return json.loads(OUTPUT_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"updated": "", "series": {"dinamikus": [], "kiegyen": [], "megfontolt": []}}

# ── BAMOSZ alapoldal scraping ─────────────────────────────────────────────────
def fetch_latest(isin):
    """
    Lekéri a BAMOSZ alapoldalát és kinyeri:
    - az utolsó árfolyamot
    - az utolsó árfolyam dátumát
    Visszatér: (dátum_str, árfolyam_float) vagy None hiba esetén.
    """
    r = requests.get(BAMOSZ_URL, params={"isin": isin}, headers=HEADERS, timeout=20)
    r.raise_for_status()

    soup = BeautifulSoup(r.text, "html.parser")

    # Az alapoldal táblázatából: "Árfolyam" és "Dátum" sorok a főbb infók táblájában
    # Keressük a kulcs-érték párokat tartalmazó táblát
    date_val  = None
    price_val = None

    for table in soup.find_all("table"):
        rows = table.find_all("tr")
        for row in rows:
            cells = row.find_all(["td", "th"])
            if len(cells) < 2:
                continue
            label = cells[0].get_text(strip=True)
            value = cells[1].get_text(strip=True)

            if "Árfolyam" in label and not price_val:
                try:
                    price_val = float(value.replace(",", ".").replace(" ", ""))
                except ValueError:
                    pass

            if "Dátum" in label and not date_val:
                s = value.strip().rstrip(".")
                for fmt in ("%Y.%m.%d", "%Y-%m-%d"):
                    try:
                        date_val = datetime.strptime(s, fmt).strftime("%Y-%m-%d")
                        break
                    except ValueError:
                        continue

        if date_val and price_val:
            break

    if date_val and price_val:
        return date_val, price_val
    return None

# ── Normalizált érték kiszámítása ─────────────────────────────────────────────
def append_point(series, new_date, new_raw_price):
    """
    Hozzáfűzi az új pontot a normalizált sorozathoz.
    A normalizálás alapja az első pont nyers ára – ezt a JSON-ban tároljuk.
    Ha a dátum már szerepel, kihagyjuk.
    Visszatér: (módosult-e, frissített sorozat)
    """
    if not series:
        # Üres sorozat – ez nem fordulhat elő normál esetben
        return False, series

    # Ellenőrzés: már szerepel-e ez a dátum
    existing_dates = {p[0] for p in series}
    if new_date in existing_dates:
        return False, series

    # Az első pont értéke = normalizálási alap
    # A meglévő sorozatban az értékek már normalizáltak (első = 1.0)
    # Az új nyers árfolyamot úgy kell normalizálni, hogy konzisztens legyen.
    # A trükk: megkeressük az előző nap nyers árát a sorozatból visszaszámolva.
    # Helyette egyszerűbb: az utolsó normalizált értékből és az árfolyam arányából számítjuk.
    # Ehhez szükségünk van az "alap nyers árra" – ezt az első feltöltéskor tároljuk.
    last_norm  = series[-1][1]          # utolsó normalizált érték
    last_date  = series[-1][0]
    return True, series  # placeholder – ld. lent a teljes logikában

# ── Fő logika ─────────────────────────────────────────────────────────────────
def main():
    data = load_existing()
    series_map = data.get("series", {})
    changed = False

    for key, isin in ISINS.items():
        print(f"  {key} ({isin})... ", end="", flush=True)
        try:
            result = fetch_latest(isin)
            if not result:
                print("Nem sikerült kinyerni az árfolyamot – oldal struktúra változhatott")
                continue

            new_date, new_raw = result
            existing = series_map.get(key, [])

            # Ha a dátum már szerepel, kihagyjuk
            if existing and existing[-1][0] >= new_date:
                print(f"Már aktuális ({new_date}), nincs teendő")
                continue

            # Normalizálás: az új pont értéke = (új nyers ár / első nyers ár)
            # Az első nyers árat tároljuk a JSON-ban "base_prices" kulcs alatt
            base_prices = data.get("base_prices", {})

            if not existing:
                # Első adat – ez az alap
                base_prices[key] = new_raw
                new_norm = 1.0
            elif key not in base_prices:
                # Meglévő sorozat, de nincs mentve az alap – visszaszámoljuk
                # Az első pont normalizált értéke 1.0, tehát:
                # base = first_raw = new_raw / first_norm * 1.0
                # De az első normalizált értéket tudjuk (1.0), és az első dátumot is.
                # Legegyszerűbb: az utolsó ismert normalizált értékből arányosítjuk.
                # Nincs meg az alap nyers ár -> nem tudunk biztonságosan normalizálni.
                print(f"Alap ár hiányzik – új pont kihagyva. Futtasd a teljes reset-et.")
                continue
            else:
                base_raw  = base_prices[key]
                new_norm  = round(new_raw / base_raw, 6)

            existing.append([new_date, new_norm])
            series_map[key] = existing
            data["base_prices"] = base_prices
            changed = True
            print(f"OK – új pont: {new_date} = {new_norm}")

        except Exception as e:
            print(f"HIBA: {e}")

    if changed:
        data["updated"] = datetime.now().strftime("%Y-%m-%d %H:%M")
        data["series"]  = series_map
        OUTPUT_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"\nAdatok mentve ({OUTPUT_FILE})")
    else:
        print("\nNincs változás – JSON nem módosult")

if __name__ == "__main__":
    print(f"[{datetime.now():%Y-%m-%d %H:%M}] BAMOSZ scraper (napi mód) indul...\n")
    main()

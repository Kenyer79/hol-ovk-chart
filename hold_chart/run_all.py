"""
run_all.py
Napi futtatásra szánt script – Task Schedulerből hívandó.
Sorban futtatja: scraper -> widget frissítés -> FTP feltöltés.

Task Scheduler beállítás:
  Program:   python.exe  (vagy teljes útvonal)
  Argumentum: E:\\hold_chart\\run_all.py
  Kezdési idő: pl. 08:00 (BAMOSZ ~7:30-ra frissül)
  Log: E:\\hold_chart\\run_all.log
"""

import sys
import traceback
from pathlib import Path
from datetime import datetime

# Saját könyvtár hozzáadása az importhoz
sys.path.insert(0, str(Path(__file__).parent))

LOG_FILE = Path(__file__).parent / "run_all.log"

def log(msg):
    line = f"[{datetime.now():%Y-%m-%d %H:%M:%S}] {msg}"
    print(line)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")

def run():
    log("=" * 55)
    log("HOLD OVK widget frissítés indul")
    log("=" * 55)

    # ── 1. BAMOSZ scraper ──────────────────────────────────────
    log("1/3  BAMOSZ adatletöltés...")
    try:
        import bamosz_scraper
        bamosz_scraper.main()
        log("     OK")
    except Exception as e:
        log(f"     HIBA: {e}")
        log(traceback.format_exc())
        log("Scraper hiba – leállás.")
        return False

    # ── 2. Widget frissítés ────────────────────────────────────
    log("2/3  Widget HTML frissítés...")
    try:
        import update_widget
        update_widget.update()
        log("     OK")
    except Exception as e:
        log(f"     HIBA: {e}")
        log(traceback.format_exc())
        log("Widget frissítés hiba – leállás.")
        return False

    # ── 3. FTP feltöltés ───────────────────────────────────────
    log("3/3  FTP feltöltés...")
    try:
        import ftp_upload
        ftp_upload.upload()
        log("     OK")
    except Exception as e:
        log(f"     HIBA: {e}")
        log(traceback.format_exc())
        # FTP hiba nem állítja le – legalább a helyi fájl friss
        log("FTP hiba (helyi fájl frissítve, feltöltés sikertelen).")
        return False

    log("Minden lépés sikeres.")
    return True

if __name__ == "__main__":
    ok = run()
    sys.exit(0 if ok else 1)

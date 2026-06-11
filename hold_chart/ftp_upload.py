"""
ftp_upload.py
Feltölti a hold_ovk_widget.html-t a Viacom tárhelyre FTP-n keresztül.
Hitelesítési adatok: E:\\secrets.json -> "hold_chart_ftp" kulcs alatt.

Futtatás: python ftp_upload.py
"""

import os
import ftplib
import json
from pathlib import Path
from datetime import datetime

# ── Konfiguráció ──────────────────────────────────────────────────────────────
BASE        = Path(__file__).parent
WIDGET_FILE = BASE / "hold_ovk_widget.html"
SECRETS     = Path(r"E:\secrets.json")

# ── Secrets betöltése ─────────────────────────────────────────────────────────
def load_ftp_config():
    """
    E:\\secrets.json-ban várt struktúra, vagy környezeti változók:
    FTP_HOST, FTP_USER, FTP_PASSWORD, FTP_DIR
    """
    # 1. Környezeti változók ellenőrzése (GitHub Actions felhő mód)
    if os.environ.get("FTP_HOST") and os.environ.get("FTP_USER") and os.environ.get("FTP_PASSWORD"):
        return {
            "host": os.environ.get("FTP_HOST"),
            "user": os.environ.get("FTP_USER"),
            "password": os.environ.get("FTP_PASSWORD"),
            "remote_dir": os.environ.get("FTP_DIR", "/public_html/hold-chart/")
        }

    # 2. Helyi secrets.json ellenőrzése
    if not SECRETS.exists():
        raise FileNotFoundError(
            f"Nem találhatók a szükséges környezeti változók (FTP_HOST, FTP_USER, FTP_PASSWORD) "
            f"és a helyi secrets fájl sem létezik: {SECRETS}"
        )

    data = json.loads(SECRETS.read_text(encoding="utf-8"))

    if "hold_chart_ftp" not in data:
        raise KeyError(
            '"hold_chart_ftp" kulcs hiányzik a secrets.json-ból.\n'
            'Add hozzá az alábbi struktúrával:\n'
            '{\n'
            '  "hold_chart_ftp": {\n'
            '    "host":       "ftp.viacomkft.hu",\n'
            '    "user":       "ftp_felhasznalo",\n'
            '    "password":   "ftp_jelszo",\n'
            '    "remote_dir": "/public_html/hold-chart/"\n'
            '  }\n'
            '}'
        )

    return data["hold_chart_ftp"]

# ── FTP feltöltés ─────────────────────────────────────────────────────────────
def upload():
    cfg = load_ftp_config()

    host       = cfg["host"]
    user       = cfg["user"]
    password   = cfg["password"]
    remote_dir = cfg.get("remote_dir", "/public_html/hold-chart/")

    if not WIDGET_FILE.exists():
        raise FileNotFoundError(f"Widget fájl nem található: {WIDGET_FILE}")

    print(f"  FTP csatlakozás: {host} ({user})")

    with ftplib.FTP(host, timeout=30) as ftp:
        ftp.login(user, password)
        ftp.set_pasv(True)

        # Célmappa létrehozása ha nem létezik
        dirs = [d for d in remote_dir.strip("/").split("/") if d]
        current = "/"
        for d in dirs:
            current = f"{current}{d}/"
            try:
                ftp.cwd(current)
            except ftplib.error_perm:
                ftp.mkd(current)
                ftp.cwd(current)
                print(f"  Mappa létrehozva: {current}")

        # index.html feltöltése
        remote_path = remote_dir.rstrip("/") + "/index.html"
        with open(WIDGET_FILE, "rb") as f:
            ftp.storbinary(f"STOR {remote_path}", f)
        print(f"  Feltöltve: {remote_path} ({WIDGET_FILE.stat().st_size:,} byte)")

        # .htaccess feltöltése (iframe + DirectoryIndex engedély)
        htaccess_file = BASE / ".htaccess"
        if htaccess_file.exists():
            remote_htaccess = remote_dir.rstrip("/") + "/.htaccess"
            with open(htaccess_file, "rb") as f:
                ftp.storbinary(f"STOR {remote_htaccess}", f)
            print(f"  Feltöltve: {remote_htaccess}")

    print(f"\nFTP feltöltés kész.")

if __name__ == "__main__":
    print(f"[{datetime.now():%Y-%m-%d %H:%M}] FTP feltöltő indul...\n")
    upload()

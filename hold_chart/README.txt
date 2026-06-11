HOLD OVK Widget – automatikus frissítő
=======================================

MAPPA: E:\hold_chart\

Fájlok:
  hold_ovk_widget.html   – a widget maga (ez kerül FTP-re)
  bamosz_scraper.py      – BAMOSZ adatletöltés -> ovk_data.json
  update_widget.py       – JSON adatok -> HTML injektálás
  ftp_upload.py          – FTP feltöltés Viacom tárhelyre
  run_all.py             – összefoglaló runner (Task Schedulerbe ez megy)
  hold_chart_update.bat  – BAT wrapper (opcionális)
  ovk_data.json          – generált adatfájl (nem kell szerkeszteni)
  run_all.log            – futási napló

ELSŐ FUTTATÁS:
  1. Másold a teljes mappát E:\hold_chart\ alá
  2. Nyisd meg E:\secrets.json és add hozzá:
       "hold_chart_ftp": {
         "host":       "ftp.viacomkft.hu",
         "user":       "...",
         "password":   "...",
         "remote_dir": "/public_html/hold-chart/"
       }
  3. Hozd létre a hold-chart mappát a tárhelyen (FlashFXP)
  4. Futtasd: python run_all.py

TASK SCHEDULER:
  Trigger: Naponta 08:00 (BAMOSZ ~07:30-ra frissül)
  Program: python.exe
  Argumentum: E:\hold_chart\run_all.py
  Munkamappa: E:\hold_chart\

IFRAME KÓD (kollégáknak):
  <iframe src="https://okosdontes.hu/hold-chart/"
          width="100%" height="520"
          frameborder="0"
          style="border-radius:12px; border:1px solid #eee;">
  </iframe>

BAMOSZ ISIN kódok:
  Dinamikus     (VK 300): HU0000727771  ← valós, ellenőrzött
  Kiegyensúlyozott (VK 200): HU0000727763  ← ellenőrizd BAMOSZ-on
  Megfontolt    (VK 100): HU0000727748  ← ellenőrizd BAMOSZ-on
  Ha a VK 200/100 ISIN hibás, a scraper fallback arányos adatot használ.

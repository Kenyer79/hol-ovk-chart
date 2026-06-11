@echo off
REM hold_chart_update.bat
REM Ezt add hozzá a Task Schedulerhez, vagy duplaklikkel is futtatható.

cd /d E:\okosdontes-befektetes\hold_chart
python run_all.py >> run_all.log 2>&1

REM Ha kézzel futtatod és látni akarod az eredményt:
REM python run_all.py
REM pause

@echo off
echo Membuat auto_input.exe ...
pip install pyinstaller
pyinstaller --onefile --noconsole auto_input.py
echo Selesai. File ada di folder "dist\auto_input.exe"
pause

@echo off
cd /d "%~dp0"
echo Optional packages are being installed. This can take a few minutes.
".venv\Scripts\python.exe" -m pip install openai pypdf python-docx pytesseract
pause

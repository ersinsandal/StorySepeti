@echo off
chcp 65001 > nul
echo ========================================================
echo  StoryVault - Windows EXE Derleme Scripti (PyInstaller)
echo ========================================================
echo.

echo [1/3] Gerekli kutuphaneler kontrol ediliyor...
python -m pip install -r requirements.txt -q
taskkill /F /IM StoryVault.exe >nul 2>&1

echo.
echo [2/3] PyInstaller ile StoryVault paketi derleniyor...
pyinstaller ^
  --noconfirm ^
  --onedir ^
  --windowed ^
  --icon=assets\icon.ico ^
  --add-data "storyvault\i18n;storyvault\i18n" ^
  --add-data "assets;assets" ^
  --collect-all "customtkinter" ^
  --collect-all "yt_dlp" ^
  --collect-all "gallery_dl" ^
  --collect-all "selenium" ^
  --collect-all "curl_cffi" ^
  --name "StoryVault" ^
  --version-file=version_info.txt ^
  --manifest "storyvault.manifest" ^
  --noupx ^
  --hidden-import "customtkinter" ^
  --hidden-import "cryptography" ^
  --hidden-import "pywin32" ^
  --hidden-import "win32crypt" ^
  --hidden-import "pystray" ^
  --hidden-import "browser_cookie3" ^
  --hidden-import "win10toast" ^
  --hidden-import "curl_cffi" ^
  --hidden-import "selenium" ^
  --clean ^
  StoryVaultPro.py

echo.
echo [3/3] Derleme basariyla tamamlandi!
echo Cikti konumu: dist\StoryVault\StoryVault.exe
echo.
pause

@echo off
:: ============================================================
::  TEFAS Günlük Fiyat Çekici - Windows Görev Zamanlayıcı Kurulum
::  Bu dosyayı SAĞ TIK → "Yönetici olarak çalıştır" ile aç
:: ============================================================

echo.
echo  TEFAS Otomatik Guncelleme - Gorev Planlayici Kurulumu
echo  ======================================================
echo.

:: Python yolunu bul
for /f "delims=" %%i in ('where python 2^>nul') do set PYTHON_PATH=%%i
if "%PYTHON_PATH%"=="" (
    echo  [HATA] Python bulunamadi! Lutfen Python yukleyin.
    pause
    exit /b 1
)
echo  Python bulundu: %PYTHON_PATH%

:: Script yolunu al (bu bat dosyasinin oldugu klasor)
set SCRIPT_DIR=%~dp0
set SCRIPT_PATH=%SCRIPT_DIR%tefas_gunluk.py

if not exist "%SCRIPT_PATH%" (
    echo  [HATA] tefas_gunluk.py bulunamadi!
    echo  Lutfen tefas_gunluk.py dosyasini bu klasore koyun: %SCRIPT_DIR%
    pause
    exit /b 1
)
echo  Script bulundu: %SCRIPT_PATH%

:: Gorevi olustur (her gun saat 20:00'de calisir - TEFAS kapandiktan sonra)
schtasks /create ^
    /tn "TEFAS_Gunluk_Fiyat" ^
    /tr "\"%PYTHON_PATH%\" \"%SCRIPT_PATH%\"" ^
    /sc daily ^
    /st 20:00 ^
    /f ^
    /rl highest

if %errorlevel% == 0 (
    echo.
    echo  ============================================
    echo   KURULUM BASARILI!
    echo  ============================================
    echo   Her gun saat 20:00'de otomatik calisacak.
    echo   Gorev adi: TEFAS_Gunluk_Fiyat
    echo  ============================================
) else (
    echo  [HATA] Gorev olusturulamadi. Yonetici olarak calistirdiginizdan emin olun.
)

echo.
echo  Gorevi simdi test etmek ister misiniz? (E/H)
set /p TEST_CHOICE=
if /i "%TEST_CHOICE%"=="E" (
    echo  Calistiriliyor...
    "%PYTHON_PATH%" "%SCRIPT_PATH%"
)

pause

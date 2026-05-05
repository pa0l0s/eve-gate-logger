@echo off
echo Building eve-gate-logger.exe...
pyinstaller build.spec --clean --noconfirm
echo.
echo Copying default settings.ini next to exe...
copy /Y settings.ini dist\settings.ini
echo.
echo Done. Run: dist\eve-gate-logger.exe
pause

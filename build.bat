@echo off
echo ========================================
echo  PumpFun Sniper - Build Executable
echo ========================================
echo.

REM Verificar se Python esta instalado
python --version >nul 2>&1
if errorlevel 1 (
    echo ERRO: Python nao encontrado!
    echo Instale Python 3.10+ de https://python.org
    pause
    exit /b 1
)

REM Instalar dependencias
echo [1/3] Instalando dependencias...
pip install -r requirements.txt --quiet

REM Verificar pyinstaller
pyinstaller --version >nul 2>&1
if errorlevel 1 (
    echo Instalando PyInstaller...
    pip install pyinstaller
)

REM Build
echo.
echo [2/3] Gerando executavel...
echo Isso pode demorar alguns minutos...
echo.

pyinstaller build.spec --noconfirm

REM Verificar resultado
if exist "dist\PumpFunSniper.exe" (
    echo.
    echo ========================================
    echo  BUILD COMPLETO!
    echo ========================================
    echo.
    echo Executavel gerado em: dist\PumpFunSniper.exe
    echo.
    echo Tamanho do arquivo:
    dir "dist\PumpFunSniper.exe" | findstr "PumpFunSniper"
    echo.
) else (
    echo.
    echo ERRO: Build falhou!
    echo Verifique os erros acima.
)

pause

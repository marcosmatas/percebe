@echo off
echo ========================================
echo P.E.R.C.E.B.E. - Script de Compilacion
echo ========================================
echo.

REM Verificar si Python esta instalado
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python no esta instalado o no esta en PATH
    echo Por favor instala Python desde https://www.python.org/
    pause
    exit /b 1
)

echo Python detectado correctamente
echo.

REM Verificar si PyQt5 esta instalado
echo Verificando PyQt5...
python -c "import PyQt5" >nul 2>&1
if errorlevel 1 (
    echo PyQt5 no esta instalado. Instalando...
    pip install PyQt5
    if errorlevel 1 (
        echo ERROR: No se pudo instalar PyQt5
        pause
        exit /b 1
    )
) else (
    echo PyQt5 ya esta instalado
)
echo.

REM Verificar si PyInstaller esta instalado
echo Verificando PyInstaller...
python -c "import PyInstaller" >nul 2>&1
if errorlevel 1 (
    echo PyInstaller no esta instalado. Instalando...
    pip install pyinstaller
    if errorlevel 1 (
        echo ERROR: No se pudo instalar PyInstaller
        pause
        exit /b 1
    )
) else (
    echo PyInstaller ya esta instalado
)
echo.

REM Limpiar compilaciones anteriores
echo Limpiando archivos anteriores...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist *.spec del /q *.spec
echo.

REM Compilar
echo Compilando P.E.R.C.E.B.E....
echo Esto puede tardar unos minutos...
echo.

pyinstaller --onefile --windowed --name "PERCEBE" percebe_client.py --icon=C:\Users\marcosms\python\percebe.ico

if errorlevel 1 (
    echo.
    echo ERROR: La compilacion fallo
    pause
    exit /b 1
)

echo.
echo ========================================
echo Compilacion completada con exito!
echo ========================================
echo.
echo El ejecutable esta en: dist\PERCEBE.exe
echo.
echo Puedes copiar ese archivo a cualquier ubicacion
echo y crear un acceso directo en la carpeta de Inicio
echo para que se ejecute automaticamente.
echo.
echo Para crear el acceso directo en Inicio:
echo 1. Presiona Win+R y escribe: shell:startup
echo 2. Crea un acceso directo de PERCEBE.exe ahi
echo.
pause

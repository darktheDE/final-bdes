@echo off
setlocal enabledelayedexpansion

echo ===================================================
echo Setting up Food ^& Restaurant Sentiment Analysis
echo ===================================================

:: 1. Install Python dependencies
echo [1/3] Installing Python dependencies from requirements.txt...
pip install -r "%~dp0..\requirements.txt"
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Failed to install Python dependencies. Please check requirements.txt
    exit /b 1
)

:: 2. Create tools/hadoop/bin directory
set "TOOLS_DIR=%~dp0..\tools"
set "HADOOP_BIN=%TOOLS_DIR%\hadoop\bin"
if not exist "%HADOOP_BIN%" (
    echo [2/3] Creating Hadoop bin directory at tools\hadoop\bin...
    mkdir "%HADOOP_BIN%"
) else (
    echo [2/3] Hadoop bin directory already exists.
)

:: 3. Download winutils.exe and hadoop.dll
echo [3/3] Downloading winutils.exe and hadoop.dll (Hadoop 3.3.6 compatible)...
set "WINUTILS_URL=https://raw.githubusercontent.com/cdarlint/winutils/master/hadoop-3.3.6/bin/winutils.exe"
set "HADOOP_DLL_URL=https://raw.githubusercontent.com/cdarlint/winutils/master/hadoop-3.3.6/bin/hadoop.dll"

if not exist "%HADOOP_BIN%\winutils.exe" (
    echo Downloading winutils.exe...
    powershell -Command "[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; (New-Object Net.WebClient).DownloadFile('%WINUTILS_URL%', '%HADOOP_BIN%\winutils.exe')"
) else (
    echo winutils.exe already exists.
)

if not exist "%HADOOP_BIN%\hadoop.dll" (
    echo Downloading hadoop.dll...
    powershell -Command "[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; (New-Object Net.WebClient).DownloadFile('%HADOOP_DLL_URL%', '%HADOOP_BIN%\hadoop.dll')"
) else (
    echo hadoop.dll already exists.
)

echo ===================================================
echo Setup Complete!
echo You can now run bin\run.bat to start the pipeline.
echo ===================================================
endlocal
pause

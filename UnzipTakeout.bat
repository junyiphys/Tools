@echo off
setlocal enabledelayedexpansion

:: =============================================================================
::
::  Takeout Unzip and Organize Script
::
::  This script automates the process of handling multiple zip archives,
::  for example, from Google Takeout. It performs the following actions:
::  1. Unzips all `takeout-*.zip` files from a source directory.
::  2. Moves the contents of the 'Drive' subfolder from each unzipped
::     Takeout folder to a final, consolidated destination.
::  3. Safely cleans up the empty Takeout folders after the files have been
::     moved.
::
:: =============================================================================


:: -----------------------------------------------------------------------------
:: Configuration
::
:: Please set the following directory paths to match your system's setup.
:: -----------------------------------------------------------------------------

:: 1. The source folder containing all your `takeout-*.zip` archives.
set "ZIP_SOURCE_DIR=C:\Downloads\Zip"

:: 2. A temporary working directory for unzipping and processing files.
::    This directory will be created if it does not exist.
set "WORKING_DIR=C:\Downloads\Out"

:: 3. The final destination folder where all your files will be consolidated.
::    This directory will be created if it does not exist.
set "FINAL_DEST_DIR=C:\Downloads\Out\Organize"

:: 4. The specific subfolder within each Takeout archive that contains the
::    data you want to move. This typically does not need to be changed.
set "DATA_SUBFOLDER=Takeout\Google Drive"


:: --- Script Execution Begins ---
echo.
echo [*] Automation Script: Unzip, Move, and Cleanup
echo --------------------------------------------------------------------------
echo [i] Zip Source : %ZIP_SOURCE_DIR%
echo [i] Working Dir: %WORKING_DIR%
echo [i] Final Dest : %FINAL_DEST_DIR%
echo --------------------------------------------------------------------------
echo.
echo This script will perform all actions in 5 seconds. Press Ctrl+C to cancel.
:: Use ping for a cross-version delay without external tools.
ping -n 6 127.0.0.1 > nul


:: --- Environment Sanity Checks ---
if not exist "%ZIP_SOURCE_DIR%" (
    echo [!] ERROR: Zip source directory not found. Halting script.
    pause
    exit /b
)
if not exist "%WORKING_DIR%" (
    echo [i] Working directory not found. Creating it...
    mkdir "%WORKING_DIR%"
)
if not exist "%FINAL_DEST_DIR%" (
    echo [i] Final destination directory not found. Creating it...
    mkdir "%FINAL_DEST_DIR%"
)


:: =============================================================================
::  PHASE 0: UNZIP ALL ARCHIVES
:: =============================================================================
echo.
echo === PHASE 0: UNZIPPING FILES ===
:: Iterate through all files matching the Takeout pattern in the source dir.
for %%f in ("%ZIP_SOURCE_DIR%\takeout-*.zip") do (
    echo [+] Unzipping "%%~nxf" to "%WORKING_DIR%"...
    :: Use PowerShell's built-in Expand-Archive cmdlet for robust unzipping.
    powershell -command "Expand-Archive -Path '%%f' -DestinationPath '%WORKING_DIR%' -Force"
)
echo.


:: Change the current directory to the working directory for easier pathing.
cd /d "%WORKING_DIR%"

:: =============================================================================
::  PHASE 1 & 2: MOVE DATA AND CLEAN UP
:: =============================================================================
echo === PHASE 1 & 2: MOVING AND CLEANING UP ===
:: Process each unzipped Takeout directory one by one.
for /d %%d in (takeout-*) do (
    echo.
    echo --------------------------------------------------------------------------
    echo --- Processing folder: "%%d"

    set "FULL_SOURCE_PATH=%%d\%DATA_SUBFOLDER%"

    :: --- Phase 1: Move Files ---
    :: Check if the target data subfolder exists before attempting to move.
    if exist "!FULL_SOURCE_PATH!" (
        echo [+] Moving contents from "!FULL_SOURCE_PATH!"...
        :: Use Robocopy to reliably move all files and subdirectories.
        :: /e     - Copies subdirectories, including empty ones.
        :: /move  - Moves files and directories (deletes from source).
        :: /nfl   - No file list.
        :: /njh   - No job header.
        :: /ndl   - No directory list.
        robocopy "!FULL_SOURCE_PATH!" "%FINAL_DEST_DIR%" /e /move /nfl /njh /ndl
    ) else (
        echo [i] Data subfolder "!FULL_SOURCE_PATH!" not found, skipping move.
    )

    :: --- Phase 2: Securely Delete Folder ---
    echo [?] Checking "%%d" for any remaining files...
    :: Check if the original Takeout directory contains any files.
    :: The `dir` command will set ERRORLEVEL to 1 if no files are found.
    dir /s /b /a-d "%%d" > nul 2>&1

    :: If ERRORLEVEL is 1, no files were found, and it's safe to delete.
    if !ERRORLEVEL! == 1 (
        echo [^] Verdict: SAFE. No files remain. Deleting...
        rmdir /s /q "%%d"
    ) else (
        echo [-] Verdict: SKIPPED. Folder still contains other files (e.g., from
        echo     other services) and will not be deleted.
    )
)

echo.
echo --------------------------------------------------------------------------
echo [*] All tasks finished.
echo --------------------------------------------------------------------------
pause

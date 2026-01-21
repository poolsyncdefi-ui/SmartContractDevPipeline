@echo off
chcp 65001
title Final Share - Batch Only
color 0A

:menu
cls
echo.
echo ========================================
echo   FINAL SHARE - BATCH ONLY
echo ========================================
echo.
echo 1. CREATE FULL SHARE (all files with line numbers)
echo 2. CREATE DIFF SHARE (changed files only)
echo 3. GIT COMMIT + PUSH
echo 4. EXIT
echo.

set /p choice=Enter choice (1-4): 

if "%choice%"=="1" goto fullshare
if "%choice%"=="2" goto diffshare
if "%choice%"=="3" goto gitpush
if "%choice%"=="4" exit /b 0
goto menu

:fullshare
cls
echo Creating project share with line numbers and full paths...

rem Create header
echo ============================================================================== > PROJECT_SHARE.txt
echo STRUCTURED LENDING PROTOCOL - FULL PROJECT SHARE >> PROJECT_SHARE.txt
echo ============================================================================== >> PROJECT_SHARE.txt
echo GitHub: poolsyncdefi-ui/SmartContractPipeline >> PROJECT_SHARE.txt
echo Repo URL: https://github.com/poolsyncdefi-ui/SmartContractPipeline >> PROJECT_SHARE.txt
echo Date: %date% Time: %time% >> PROJECT_SHARE.txt
echo. >> PROJECT_SHARE.txt

rem Get git info
echo [GIT INFORMATION] >> PROJECT_SHARE.txt
echo ------------------------------------------------------------------------------ >> PROJECT_SHARE.txt
for /f "delims=" %%i in ('git branch --show-current 2^>nul') do echo Branch: %%i >> PROJECT_SHARE.txt
for /f "delims=" %%i in ('git rev-parse --short HEAD 2^>nul') do echo Commit: %%i >> PROJECT_SHARE.txt
for /f "delims=" %%i in ('git log --oneline -1 --pretty=format:"%%s" 2^>nul') do echo Last commit: %%i >> PROJECT_SHARE.txt
echo. >> PROJECT_SHARE.txt

rem === CONTRACTS DIRECTORY ===
echo [CONTRACTS DIRECTORY - *.sol files] >> PROJECT_SHARE.txt
echo ============================================================================== >> PROJECT_SHARE.txt
set contract_count=0
for /r contracts %%f in (*.sol) do (
    set /a contract_count+=1
    
    set "filepath=%%f"
    set "filename=%%~nxf"
    set "filesize=%%~z"
    set "filemodified=%%~tf"
    
    echo. >> PROJECT_SHARE.txt
    echo FILE %contract_count% ^| !filepath! >> PROJECT_SHARE.txt
    echo Size: !filesize! bytes ^| Modified: !filemodified! >> PROJECT_SHARE.txt
    echo ------------------------------------------------------------------------------ >> PROJECT_SHARE.txt
    
    if exist "%%f" (
        setlocal enabledelayedexpansion
        set line_num=1
        for /f "tokens=* delims=" %%a in ('type "%%f"') do (
            echo !line_num!: %%a >> PROJECT_SHARE.txt
            set /a line_num+=1
        )
        endlocal
    ) else (
        echo [FILE NOT FOUND] >> PROJECT_SHARE.txt
    )
    echo ------------------------------------------------------------------------------ >> PROJECT_SHARE.txt
)

rem === SCRIPTS DIRECTORY ===
echo. >> PROJECT_SHARE.txt
echo [SCRIPTS DIRECTORY - *.js, *.bat, *.sh, *.txt files] >> PROJECT_SHARE.txt
echo ============================================================================== >> PROJECT_SHARE.txt
set script_count=0
for /r scripts %%f in (*.js *.bat *.sh *.txt) do (
    if exist "%%f" (
        set /a script_count+=1
        
        set "filepath=%%f"
        set "filename=%%~nxf"
        set "filesize=%%~z"
        set "filemodified=%%~tf"
        set "fileext=%%~xf"
        
        echo. >> PROJECT_SHARE.txt
        echo SCRIPT !script_count! ^| !filepath! >> PROJECT_SHARE.txt
        echo Size: !filesize! bytes ^| Type: !fileext! ^| Modified: !filemodified! >> PROJECT_SHARE.txt
        echo ------------------------------------------------------------------------------ >> PROJECT_SHARE.txt
        
        setlocal enabledelayedexpansion
        set line_num=1
        for /f "tokens=* delims=" %%a in ('type "%%f"') do (
            echo !line_num!: %%a >> PROJECT_SHARE.txt
            set /a line_num+=1
        )
        endlocal
        echo ------------------------------------------------------------------------------ >> PROJECT_SHARE.txt
    )
)

rem === TESTS DIRECTORY ===
echo. >> PROJECT_SHARE.txt
echo [TESTS DIRECTORY - *.js, *.txt files] >> PROJECT_SHARE.txt
echo ============================================================================== >> PROJECT_SHARE.txt
set test_count=0
for /r test %%f in (*.js *.txt) do (
    if exist "%%f" (
        set /a test_count+=1
        
        set "filepath=%%f"
        set "filename=%%~nxf"
        set "filesize=%%~z"
        set "filemodified=%%~tf"
        set "fileext=%%~xf"
        
        echo. >> PROJECT_SHARE.txt
        echo TEST !test_count! ^| !filepath! >> PROJECT_SHARE.txt
        echo Size: !filesize! bytes ^| Type: !fileext! ^| Modified: !filemodified! >> PROJECT_SHARE.txt
        echo ------------------------------------------------------------------------------ >> PROJECT_SHARE.txt
        
        setlocal enabledelayedexpansion
        set line_num=1
        for /f "tokens=* delims=" %%a in ('type "%%f"') do (
            echo !line_num!: %%a >> PROJECT_SHARE.txt
            set /a line_num+=1
        )
        endlocal
        echo ------------------------------------------------------------------------------ >> PROJECT_SHARE.txt
    )
)

rem === PROJECT STRUCTURE ===
echo. >> PROJECT_SHARE.txt
echo [PROJECT FILE STRUCTURE] >> PROJECT_SHARE.txt
echo ============================================================================== >> PROJECT_SHARE.txt
echo Listing all project files... >> PROJECT_SHARE.txt
echo. >> PROJECT_SHARE.txt

echo CONTRACTS: >> PROJECT_SHARE.txt
dir contracts /b /s >> PROJECT_SHARE.txt
echo. >> PROJECT_SHARE.txt

echo SCRIPTS: >> PROJECT_SHARE.txt
dir scripts /b /s >> PROJECT_SHARE.txt
echo. >> PROJECT_SHARE.txt

echo TESTS: >> PROJECT_SHARE.txt
dir test /b /s >> PROJECT_SHARE.txt
echo. >> PROJECT_SHARE.txt

echo CONFIG FILES: >> PROJECT_SHARE.txt
dir *.json *.toml *.yml *.yaml *.config *.cfg /b >> PROJECT_SHARE.txt
echo. >> PROJECT_SHARE.txt

rem === SUMMARY ===
echo. >> PROJECT_SHARE.txt
echo [SUMMARY] >> PROJECT_SHARE.txt
echo ============================================================================== >> PROJECT_SHARE.txt
echo Total contract files: %contract_count% >> PROJECT_SHARE.txt
echo Total script files: %script_count% >> PROJECT_SHARE.txt
echo Total test files: %test_count% >> PROJECT_SHARE.txt
set /a total_files=contract_count+script_count+test_count
echo Total code files: %total_files% >> PROJECT_SHARE.txt
echo. >> PROJECT_SHARE.txt
echo Generated: %date% %time% >> PROJECT_SHARE.txt
echo ============================================================================== >> PROJECT_SHARE.txt

cls
echo File created: PROJECT_SHARE.txt
echo Files: %total_files% total (%contract_count% contracts, %script_count% scripts, %test_count% tests)
echo.
echo Copy content to pastebin.com and share the URL
echo.
pause
goto menu

:diffshare
cls
echo Creating diff report...

rem Create diff report
echo ============================================================================== > DIFF_REPORT.txt
echo STRUCTURED LENDING PROTOCOL - DIFF REPORT >> DIFF_REPORT.txt
echo ============================================================================== >> DIFF_REPORT.txt
echo Date: %date% Time: %time% >> DIFF_REPORT.txt
echo. >> DIFF_REPORT.txt

rem Get git information
echo [GIT STATUS] >> DIFF_REPORT.txt
echo ------------------------------------------------------------------------------ >> DIFF_REPORT.txt
git status >> DIFF_REPORT.txt 2>nul
echo. >> DIFF_REPORT.txt

rem Get changed files with details
echo [CHANGED FILES DETAIL] >> DIFF_REPORT.txt
echo ============================================================================== >> DIFF_REPORT.txt
set changed_count=0
for /f "tokens=1,*" %%a in ('git status --porcelain 2^>nul') do (
    set status=%%a
    set "file=%%b"
    
    if exist "!file!" (
        set /a changed_count+=1
        
        set "filepath=!file!"
        set "filesize=%%~z"
        set "filemodified=%%~tf"
        
        echo. >> DIFF_REPORT.txt
        echo FILE !changed_count! ^| !filepath! >> DIFF_REPORT.txt
        echo Status: !status! ^| Size: !filesize! bytes ^| Modified: !filemodified! >> DIFF_REPORT.txt
        echo ------------------------------------------------------------------------------ >> DIFF_REPORT.txt
        
        if "!status!"=="??" (
            echo [NEW FILE - FULL CONTENT WITH LINE NUMBERS] >> DIFF_REPORT.txt
            echo ------------------------------------------------------------------------------ >> DIFF_REPORT.txt
            setlocal enabledelayedexpansion
            set line_num=1
            for /f "tokens=* delims=" %%l in ('type "!file!"') do (
                echo !line_num!: %%l >> DIFF_REPORT.txt
                set /a line_num+=1
            )
            endlocal
        ) else (
            echo [MODIFICATIONS - GIT DIFF OUTPUT] >> DIFF_REPORT.txt
            echo ------------------------------------------------------------------------------ >> DIFF_REPORT.txt
            git diff "!file!" >> DIFF_REPORT.txt 2>nul
            if errorlevel 1 (
                git diff --cached "!file!" >> DIFF_REPORT.txt 2>nul
            )
            echo. >> DIFF_REPORT.txt
            echo [CURRENT FILE CONTENT WITH LINE NUMBERS] >> DIFF_REPORT.txt
            echo ------------------------------------------------------------------------------ >> DIFF_REPORT.txt
            setlocal enabledelayedexpansion
            set line_num=1
            for /f "tokens=* delims=" %%l in ('type "!file!"') do (
                echo !line_num!: %%l >> DIFF_REPORT.txt
                set /a line_num+=1
            )
            endlocal
        )
        echo ------------------------------------------------------------------------------ >> DIFF_REPORT.txt
    )
)

if %changed_count%==0 (
    echo No changes detected in the working directory. >> DIFF_REPORT.txt
    echo. >> DIFF_REPORT.txt
)

if %changed_count% gtr 0 (
    echo. >> DIFF_REPORT.txt
    echo [LINE-BY-LINE CHANGES SUMMARY] >> DIFF_REPORT.txt
    echo ============================================================================== >> DIFF_REPORT.txt
    for /f "tokens=2" %%f in ('git status --porcelain 2^>nul ^| findstr /r "^M ^A ^??"') do (
        if exist "%%f" (
            echo. >> DIFF_REPORT.txt
            echo FILE: %%f >> DIFF_REPORT.txt
            echo ------------------------------------------------------------------------------ >> DIFF_REPORT.txt
            git diff --unified=0 "%%f" 2>nul | findstr "+" "-" >> DIFF_REPORT.txt
            echo ------------------------------------------------------------------------------ >> DIFF_REPORT.txt
        )
    )
)

echo. >> DIFF_REPORT.txt
echo [GIT DIFF SUMMARY] >> DIFF_REPORT.txt
echo ============================================================================== >> DIFF_REPORT.txt
git diff --stat >> DIFF_REPORT.txt 2>nul
if errorlevel 1 (
    echo No staged changes. Use 'git diff --cached' for staged changes. >> DIFF_REPORT.txt
)

rem Summary
echo. >> DIFF_REPORT.txt
echo [REPORT SUMMARY] >> DIFF_REPORT.txt
echo ============================================================================== >> DIFF_REPORT.txt
echo Total changed files: %changed_count% >> DIFF_REPORT.txt
echo Report generated: %date% %time% >> DIFF_REPORT.txt
echo. >> DIFF_REPORT.txt
echo INSTRUCTIONS FOR CODE REVIEW: >> DIFF_REPORT.txt
echo 1. Files are listed with full paths for precise location >> DIFF_REPORT.txt
echo 2. Line numbers are included for specific references >> DIFF_REPORT.txt
echo 3. Changes marked with + (additions) and - (deletions) >> DIFF_REPORT.txt
echo 4. New files show complete content >> DIFF_REPORT.txt
echo ============================================================================== >> DIFF_REPORT.txt

cls
echo File created: DIFF_REPORT.txt
echo Changed files: %changed_count%
echo.
echo Copy content to pastebin.com and share the URL
echo.
pause
goto menu

:gitpush
cls
echo GitHub: https://github.com/poolsyncdefi-ui/SmartContractPipeline
echo.
set /p msg=Commit message: 
if "%msg%"=="" set msg="Project update"
echo.
git add .
git commit -m "%msg%"
git push
echo.
echo Verify commit: https://github.com/poolsyncdefi-ui/SmartContractPipeline/commits/main
echo.
pause
goto menu
@echo off
chcp 65001
title Final Share - Batch Only
color 0A

rem Configuration GitHub
set GITHUB_USERNAME=poolsyncdefi-ui
set GITHUB_REPO=structured-lending-protocol-clean
set GITHUB_TOKEN=

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
echo 4. PUBLISH TO GITHUB REPOSITORY
echo 5. SHARE TO GITHUB GISTS
echo 6. EXIT
echo.

set /p choice=Enter choice (1-6): 

if "%choice%"=="1" goto fullshare
if "%choice%"=="2" goto diffshare
if "%choice%"=="3" goto gitpush
if "%choice%"=="4" goto githubrepo
if "%choice%"=="5" goto githubgists
if "%choice%"=="6" exit /b 0
goto menu

:fullshare
cls
echo Creating project share with line numbers and full paths...

rem Create header
echo ============================================================================== > PROJECT_SHARE.txt
echo STRUCTURED LENDING PROTOCOL - FULL PROJECT SHARE >> PROJECT_SHARE.txt
echo ============================================================================== >> PROJECT_SHARE.txt
echo GitHub: %GITHUB_USERNAME%/%GITHUB_REPO% >> PROJECT_SHARE.txt
echo Repo URL: https://github.com/%GITHUB_USERNAME%/%GITHUB_REPO% >> PROJECT_SHARE.txt
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
echo GitHub: https://github.com/%GITHUB_USERNAME%/%GITHUB_REPO%
echo.
set /p msg=Commit message: 
if "%msg%"=="" set msg="Project update"
echo.
git add .
git commit -m "%msg%"
git push
echo.
echo Verify commit: https://github.com/%GITHUB_USERNAME%/%GITHUB_REPO%/commits/main
echo.
pause
goto menu

:githubrepo
cls
echo ========================================
echo   PUBLISH TO GITHUB REPOSITORY
echo ========================================
echo.
echo Repository: %GITHUB_USERNAME%/%GITHUB_REPO%
echo URL: https://github.com/%GITHUB_USERNAME%/%GITHUB_REPO%
echo.

rem Check if Git is installed
git --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Git is not installed or not in PATH
    echo Please install Git from: https://git-scm.com/downloads
    echo.
    pause
    goto menu
)

rem Check if GitHub token is set
if "%GITHUB_TOKEN%"=="" (
    echo GITHUB_TOKEN is not configured.
    echo.
    echo To create a GitHub token:
    echo 1. Go to https://github.com/settings/tokens
    echo 2. Click "Generate new token (classic)"
    echo 3. Give it a name
    echo 4. Select "repo" (FULL scope)
    echo 5. Click "Generate token"
    echo 6. Copy the token (starts with 'ghp_')
    echo.
    set /p GITHUB_TOKEN=Enter your GitHub token: 
    if "%GITHUB_TOKEN%"=="" (
        echo No token entered. Operation cancelled.
        echo.
        pause
        goto menu
    )
)

rem Configure remote URL with token
echo Configuring Git remote with token...
git remote remove origin 2>nul
git remote add origin https://x-access-token:%GITHUB_TOKEN%@github.com/%GITHUB_USERNAME%/%GITHUB_REPO%.git

if errorlevel 1 (
    echo ERROR: Failed to configure Git remote
    echo.
    pause
    goto menu
)

rem Configure Git user
echo Configuring Git user...
git config user.name "%GITHUB_USERNAME%"
git config user.email "%GITHUB_USERNAME%@users.noreply.github.com"

rem Add all files
echo Adding files to Git...
git add .

rem Commit
set /p commit_msg=Enter commit message (press Enter for default): 
if "%commit_msg%"=="" set commit_msg="🚀 Automated publication: Structured Lending Protocol - %date% %time%"
echo Committing with message: %commit_msg%
git commit -m "%commit_msg%"

rem Push to GitHub
echo Pushing to GitHub repository...
git branch -M main
git push -u origin main --force

if errorlevel 1 (
    echo ERROR: Failed to push to GitHub
    echo Check your token permissions and repository access
    echo.
    
    rem Try alternative method
    echo Trying alternative authentication method...
    git remote remove origin
    git remote add origin https://%GITHUB_USERNAME%:%GITHUB_TOKEN%@github.com/%GITHUB_USERNAME%/%GITHUB_REPO%.git
    git push -u origin main --force
    
    if errorlevel 1 (
        echo ERROR: All authentication methods failed
        echo Please verify:
        echo 1. Token has "repo" permissions
        echo 2. Repository exists: %GITHUB_REPO%
        echo 3. Token is not expired
        echo.
    ) else (
        echo SUCCESS: Repository published successfully!
        echo URL: https://github.com/%GITHUB_USERNAME%/%GITHUB_REPO%
    )
) else (
    echo SUCCESS: Repository published successfully!
    echo URL: https://github.com/%GITHUB_USERNAME%/%GITHUB_REPO%
    echo.
    echo Check your repository at:
    echo https://github.com/%GITHUB_USERNAME%/%GITHUB_REPO%
)

rem Clear token from memory for security
set GITHUB_TOKEN=
echo.
pause
goto menu

:githubgists
cls
echo ========================================
echo   SHARE TO GITHUB GISTS
echo ========================================
echo.
echo Gists are like pastebin but integrated with GitHub
echo Each file can be up to 1MB
echo.

rem Check if curl is installed
where curl >nul 2>&1
if errorlevel 1 (
    echo ERROR: curl is not installed or not in PATH
    echo Please install curl or use Windows PowerShell alternative
    echo.
    pause
    goto menu
)

rem Check if GitHub token is set
if "%GITHUB_TOKEN%"=="" (
    echo GITHUB_TOKEN is not configured.
    echo.
    echo To create a GitHub token:
    echo 1. Go to https://github.com/settings/tokens
    echo 2. Click "Generate new token (classic)"
    echo 3. Give it a name
    echo 4. Select "gist" permission
    echo 5. Click "Generate token"
    echo 6. Copy the token (starts with 'ghp_')
    echo.
    set /p GITHUB_TOKEN=Enter your GitHub token (with gist permission): 
    if "%GITHUB_TOKEN%"=="" (
        echo No token entered. Operation cancelled.
        echo.
        pause
        goto menu
    )
)

echo Checking GitHub token...
curl -s -H "Authorization: token %GITHUB_TOKEN%" https://api.github.com/user > temp_user.json
findstr "login" temp_user.json >nul
if errorlevel 1 (
    echo ERROR: Invalid GitHub token or no permission
    echo Please verify:
    echo 1. Token has "gist" permission
    echo 2. Token is not expired
    echo 3. Token starts with "ghp_"
    echo.
    del temp_user.json 2>nul
    pause
    goto menu
)

for /f "tokens=2 delims=:," %%a in ('findstr "login" temp_user.json') do set github_login=%%a
set github_login=%github_login:"=%
set github_login=%github_login: =%
del temp_user.json 2>nul

echo Token valid for user: %github_login%
echo.

rem Check if share files exist
if not exist "PROJECT_SHARE.txt" (
    echo PROJECT_SHARE.txt not found.
    echo Would you like to create it first? (Y/N)
    set /p create_choice=
    if /i "%create_choice%"=="Y" goto fullshare
    echo Operation cancelled.
    echo.
    pause
    goto menu
)

rem Read the file and check size
for %%F in ("PROJECT_SHARE.txt") do set filesize=%%~zF
set /a filesize_kb=%filesize%/1024
set /a filesize_mb=%filesize_kb%/1024

echo File: PROJECT_SHARE.txt
echo Size: %filesize% bytes (%filesize_kb% KB, %filesize_mb% MB)
echo.

if %filesize% gtr 1000000 (
    echo WARNING: File is larger than 1MB (%filesize_mb%.%filesize_kb% MB)
    echo Gists have a 1MB limit per file.
    echo.
    echo Options:
    echo 1. Split file into multiple parts (recommended)
    echo 2. Try to upload anyway (may fail)
    echo 3. Cancel
    echo.
    set /p split_choice=Choose option (1-3): 
    
    if "%split_choice%"=="1" goto splitfile
    if "%split_choice%"=="3" goto menu
)

rem Prepare file content for JSON
echo Preparing file content for upload...
powershell -Command "(Get-Content -Path 'PROJECT_SHARE.txt' -Raw) -replace '\"', '\"' -replace '\\', '\\' -replace '`t', '\t' -replace '`r`n', '\n' | Set-Content -Path 'temp_content.txt' -Force"

rem Create JSON payload
echo Creating Gist...
(
echo {
echo   "description": "Structured Lending Protocol - Full Project Share ^(%date% ^)",
echo   "public": false,
echo   "files": {
echo     "PROJECT_SHARE.txt": {
echo       "content": 
) > temp_payload.json

type temp_content.txt >> temp_payload.json

(
echo
echo     }
echo   }
echo }
) >> temp_payload.json

rem Upload to GitHub Gists
echo Uploading to GitHub Gists...
curl -s -X POST ^
  -H "Authorization: token %GITHUB_TOKEN%" ^
  -H "Accept: application/vnd.github.v3+json" ^
  https://api.github.com/gists ^
  -d @temp_payload.json > temp_response.json

rem Check response
findstr "html_url" temp_response.json >nul
if errorlevel 1 (
    echo ERROR: Failed to create Gist
    echo Response:
    type temp_response.json
    echo.
    
    rem Try to parse error
    for /f "tokens=2 delims=:," %%a in ('findstr "message" temp_response.json') do (
        set error_msg=%%a
        set error_msg=!error_msg:"=!
        echo Error: !error_msg!
    )
) else (
    for /f "tokens=2 delims=:," %%a in ('findstr "html_url" temp_response.json') do (
        set gist_url=%%a
        set gist_url=!gist_url:"=!
        set gist_url=!gist_url: =!
    )
    
    echo SUCCESS: Gist created successfully!
    echo.
    echo Gist URL: !gist_url!
    echo.
    echo You can share this URL for code review.
    
    rem Save Gist info to file
    echo Gist URL: !gist_url! > GIST_INFO.txt
    echo Created: %date% %time% >> GIST_INFO.txt
    echo Description: Structured Lending Protocol - Full Project Share >> GIST_INFO.txt
    echo File: PROJECT_SHARE.txt >> GIST_INFO.txt
    echo.
    echo Gist information saved to: GIST_INFO.txt
)

rem Cleanup
del temp_content.txt 2>nul
del temp_payload.json 2>nul
del temp_response.json 2>nul
set GITHUB_TOKEN=

echo.
pause
goto menu

:splitfile
cls
echo ========================================
echo   SPLIT FILE FOR GITHUB GISTS
echo ========================================
echo.
echo Splitting PROJECT_SHARE.txt for GitHub Gists...
echo Gist limit: 1MB per file
echo.

rem Calculate number of parts needed
set /a parts_needed=(%filesize% / 1000000) + 1
echo File size: %filesize% bytes
echo Parts needed: %parts_needed%
echo.

set /p gist_desc=Enter description for Gists: 
if "%gist_desc%"=="" set gist_desc="Structured Lending Protocol - Part"

echo Creating %parts_needed% parts...
set part_num=1
set current_line=1
set total_lines=0

rem Count total lines first
for /f %%i in ('type "PROJECT_SHARE.txt" ^| find /c /v ""') do set total_lines=%%i
set /a lines_per_part=%total_lines% / %parts_needed%

echo Total lines: %total_lines%
echo Lines per part: %lines_per_part%
echo.

:splitloop
if %part_num% gtr %parts_needed% goto splitdone

set start_line=%current_line%
set /a end_line=%current_line% + %lines_per_part% - 1
if %end_line% gtr %total_lines% set end_line=%total_lines%

echo Creating part %part_num%: lines %start_line%-%end_line%

rem Extract part using PowerShell
powershell -Command "Get-Content -Path 'PROJECT_SHARE.txt' -TotalCount %end_line% | Select-Object -Last %lines_per_part% | Set-Content -Path 'PROJECT_SHARE_PART%part_num%.txt' -Force"

rem Upload this part to Gist
echo Uploading part %part_num% to Gist...
powershell -Command "(Get-Content -Path 'PROJECT_SHARE_PART%part_num%.txt' -Raw) -replace '\"', '\"' -replace '\\', '\\' -replace '`t', '\t' -replace '`r`n', '\n' | Set-Content -Path 'temp_content_part.txt' -Force"

(
echo {
echo   "description": "%gist_desc% %part_num%/%parts_needed%",
echo   "public": false,
echo   "files": {
echo     "PROJECT_SHARE_PART%part_num%.txt": {
echo       "content": 
) > temp_payload_part.json

type temp_content_part.txt >> temp_payload_part.json

(
echo
echo     }
echo   }
echo }
) >> temp_payload_part.json

curl -s -X POST ^
  -H "Authorization: token %GITHUB_TOKEN%" ^
  -H "Accept: application/vnd.github.v3+json" ^
  https://api.github.com/gists ^
  -d @temp_payload_part.json > temp_response_part.json

findstr "html_url" temp_response_part.json >nul
if errorlevel 1 (
    echo ERROR: Failed to create Gist for part %part_num%
) else (
    for /f "tokens=2 delims=:," %%a in ('findstr "html_url" temp_response_part.json') do (
        set gist_url_part=%%a
        set gist_url_part=!gist_url_part:"=!
        set gist_url_part=!gist_url_part: =!
    )
    echo SUCCESS: Part %part_num% created: !gist_url_part!
    
    rem Save Gist URL
    echo Part %part_num%: !gist_url_part! >> GISTS_INDEX.txt
)

rem Cleanup for this part
del temp_content_part.txt 2>nul
del temp_payload_part.json 2>nul
del temp_response_part.json 2>nul

set /a current_line=%end_line% + 1
set /a part_num+=1
goto splitloop

:splitdone
echo.
echo All parts created successfully!
if exist "GISTS_INDEX.txt" (
    echo.
    echo Gist URLs saved to: GISTS_INDEX.txt
    echo.
    type GISTS_INDEX.txt
)

rem Create master index
echo Creating master index file...
(
echo ========================================
echo   GITHUB GISTS INDEX
echo ========================================
echo Project: Structured Lending Protocol
echo Split into: %parts_needed% parts
echo Date: %date% Time: %time%
echo.
echo GIST URLs:
echo.
) > GISTS_MASTER_INDEX.txt

if exist "GISTS_INDEX.txt" type GISTS_INDEX.txt >> GISTS_MASTER_INDEX.txt

echo.
echo Master index saved to: GISTS_MASTER_INDEX.txt
echo.

rem Cleanup part files
for /l %%i in (1,1,%parts_needed%) do (
    del PROJECT_SHARE_PART%%i.txt 2>nul
)

set GITHUB_TOKEN=
pause
goto menu
# SmartContractPipeline.ps1
# Pipeline for Smart Contract analysis and GitHub publication

# Load configuration from JSON file
function Load-Configuration {
    $configPath = "project_config.json"
    
    if (-not (Test-Path $configPath)) {
        Write-Host "ERROR: Configuration file not found: $configPath" -ForegroundColor Red
        Write-Host "Please create project_config.json file" -ForegroundColor Yellow
        exit 1
    }
    
    try {
        $configContent = Get-Content $configPath -Raw
        $config = $configContent | ConvertFrom-Json
        
        # Validate required fields
        if (-not $config.PROJECT_NAME -or 
            -not $config.PROJECT_PATH -or 
            -not $config.GITHUB_USERNAME -or 
            -not $config.GITHUB_TOKEN -or 
            -not $config.GITHUB_REPO_NAME) {
            Write-Host "ERROR: Missing required fields in configuration" -ForegroundColor Red
            exit 1
        }
        
        # Check if token is still placeholder
        if ($config.GITHUB_TOKEN -eq "ghp_**************") {
            Write-Host "ERROR: GitHub token not configured" -ForegroundColor Red
            Write-Host "Please update your token in project_config.json" -ForegroundColor Yellow
            Write-Host "Current token value: $($config.GITHUB_TOKEN)" -ForegroundColor DarkGray
            exit 1
        }
        
        Write-Host "Configuration loaded: $($config.PROJECT_NAME)" -ForegroundColor Green
        return $config
    }
    catch {
        Write-Host "ERROR loading configuration: $_" -ForegroundColor Red
        exit 1
    }
}

# Create complete project file with all content (excluding config file)
function Create-ProjectShareFile {
    Write-Host "Creating PROJECT_SHARE_COMPLETE.txt file..." -ForegroundColor Yellow
    
    $outputFile = Join-Path $global:config.PROJECT_PATH "PROJECT_SHARE_COMPLETE.txt"
    
    try {
        # Header
        $header = @"
===============================================================
PROJECT_SHARE_COMPLETE - $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')
Project: $($global:config.PROJECT_NAME)
Note: project_config.json excluded for security reasons
===============================================================

"@
        $header | Out-File $outputFile -Encoding UTF8
        
        # Get all files (exclude config file, git, node_modules, and the output file itself)
        $files = Get-ChildItem -Path $global:config.PROJECT_PATH -Recurse -File -ErrorAction SilentlyContinue | 
                 Where-Object {
                     $_.FullName -notmatch '\\.git\\' -and
                     $_.Name -notmatch 'project_config\.json$' -and
                     $_.Name -notmatch 'PROJECT_SHARE_COMPLETE\.txt$' -and
                     $_.FullName -notmatch '\\node_modules\\' -and
                     $_.FullName -ne $outputFile
                 }
        
        Write-Host "Files to process: $($files.Count)" -ForegroundColor Gray
        Write-Host "Note: project_config.json excluded for security" -ForegroundColor Yellow
        
        $fileCounter = 0
        $totalLines = 0
        
        foreach ($file in $files) {
            $fileCounter++
            $relativePath = $file.FullName.Substring($global:config.PROJECT_PATH.Length + 1)
            
            Write-Host "  [$fileCounter/$($files.Count)] Processing: $relativePath" -ForegroundColor Gray
            
            # File separator
            $separator = @"

===============================================================
FILE: $relativePath
===============================================================
Full path: $($file.FullName)
Size: $([math]::Round($file.Length/1KB,2)) KB
Last modified: $($file.LastWriteTime.ToString('yyyy-MM-dd HH:mm:ss'))

"@
            $separator | Out-File $outputFile -Encoding UTF8 -Append
            
            # Read file content
            try {
                $content = Get-Content $file.FullName -Encoding UTF8 -ErrorAction Stop
                
                # Add content with line numbers
                for ($i = 0; $i -lt $content.Count; $i++) {
                    $lineNumber = $i + 1
                    $lineOutput = [string]::Format("{0,4}: {1}", $lineNumber, $content[$i])
                    $lineOutput | Out-File $outputFile -Encoding UTF8 -Append
                    $totalLines++
                }
                
                # Handle empty files
                if ($content.Count -eq 0) {
                    "     (empty file)" | Out-File $outputFile -Encoding UTF8 -Append
                }
                
                Write-Host "    Added $($content.Count) lines" -ForegroundColor DarkGray
            }
            catch {
                "ERROR READING FILE: $($_.Exception.Message)" | Out-File $outputFile -Encoding UTF8 -Append
                Write-Host "    Error reading file" -ForegroundColor Red
            }
            
            # Add blank line between files
            "`n" | Out-File $outputFile -Encoding UTF8 -Append
        }
        
        # Add note about excluded config file
        $configNote = @"

===============================================================
NOTE: CONFIGURATION FILE EXCLUDED
===============================================================
For security reasons, project_config.json is not included in this report.
This file contains sensitive information like GitHub tokens.

To view the project configuration, check the original project_config.json file.
"@
        $configNote | Out-File $outputFile -Encoding UTF8 -Append
        
        # Footer
        $footer = @"

===============================================================
SUMMARY
===============================================================
Files processed: $fileCounter
Total lines: $totalLines
Generation date: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')
Project: $($global:config.PROJECT_NAME)
Path: $($global:config.PROJECT_PATH)

===============================================================
END OF REPORT
===============================================================
"@
        $footer | Out-File $outputFile -Encoding UTF8 -Append
        
        Write-Host "===============================================================" -ForegroundColor Green
        Write-Host "FILE CREATED SUCCESSFULLY" -ForegroundColor Green
        Write-Host "===============================================================" -ForegroundColor Green
        Write-Host "File: $outputFile" -ForegroundColor Cyan
        Write-Host "Files included: $fileCounter" -ForegroundColor Cyan
        Write-Host "Total lines: $totalLines" -ForegroundColor Cyan
        
        return $true, $outputFile
    }
    catch {
        Write-Host "ERROR creating file: $_" -ForegroundColor Red
        return $false, $null
    }
}

# Publish to GitHub
function Publish-ToGitHub {
    Write-Host "===============================================================" -ForegroundColor Cyan
    Write-Host "PUBLISHING TO GITHUB" -ForegroundColor Yellow
    Write-Host "===============================================================" -ForegroundColor Cyan
    
    # Check if GitHub token is configured
    if ($global:config.GITHUB_TOKEN -eq "ghp_**************") {
        Write-Host "ERROR: GitHub token not configured" -ForegroundColor Red
        Write-Host "Please update your token in project_config.json" -ForegroundColor Yellow
        return $false
    }
    
    # Check if git is installed
    try {
        $gitVersion = git --version 2>$null
        if (-not $gitVersion) {
            throw "Git not found"
        }
        Write-Host "Git detected" -ForegroundColor Green
    }
    catch {
        Write-Host "ERROR: Git is not installed or not in PATH" -ForegroundColor Red
        return $false
    }
    
    # Save current directory
    $originalLocation = Get-Location
    
    try {
        # Navigate to project directory
        if (Test-Path $global:config.PROJECT_PATH) {
            Set-Location $global:config.PROJECT_PATH
            Write-Host "Directory: $(Get-Location)" -ForegroundColor Gray
        }
        else {
            Write-Host "ERROR: Project path not found: $($global:config.PROJECT_PATH)" -ForegroundColor Red
            return $false
        }
        
        # Check if git repository exists
        $isGitRepo = Test-Path ".git"
        
        if (-not $isGitRepo) {
            Write-Host "Initializing git repository..." -ForegroundColor Yellow
            git init
            git config user.email "pipeline@poolsyncdefi.com"
            git config user.name "PoolSync DeFi Pipeline"
            Write-Host "Git repository initialized" -ForegroundColor Green
        }
        
        # Check current branch
        $currentBranch = git branch --show-current 2>$null
        if ([string]::IsNullOrWhiteSpace($currentBranch)) {
            Write-Host "No branch exists, creating 'master' branch..." -ForegroundColor Yellow
            # Create an initial empty commit to establish branch
            git commit --allow-empty -m "Initial empty commit"
            git branch -M master 2>$null
            $currentBranch = "master"
        }
        
        Write-Host "Current branch: $currentBranch" -ForegroundColor Green
        
        # Create .gitignore file if it doesn't exist
        if (-not (Test-Path ".gitignore")) {
            Write-Host "Creating .gitignore file..." -ForegroundColor Yellow
            $gitignoreContent = @"
# Exclude sensitive configuration files
project_config.json
*.env
*.secret
*credentials*

# Exclude temporary files
*.tmp
*.temp
*.log

# Exclude system files
Thumbs.db
.DS_Store

# Exclude large files
*.zip
*.rar
*.7z

# Exclude build directories
dist/
build/
node_modules/
"@
            $gitignoreContent | Out-File ".gitignore" -Encoding UTF8 -Force
            Write-Host ".gitignore file created" -ForegroundColor Green
        }
        else {
            Write-Host ".gitignore file already exists" -ForegroundColor Gray
        }
        
        # Check if there are any changes
        Write-Host "Checking for changes..." -ForegroundColor Yellow
        git add .
        $status = git status --porcelain
        
        if ([string]::IsNullOrWhiteSpace($status)) {
            Write-Host "No changes to commit" -ForegroundColor Gray
            Write-Host "Creating a timestamp file to have something to commit..." -ForegroundColor Yellow
            
            # Create a timestamp file
            $timestampFile = "LAST_UPDATE_$(Get-Date -Format 'yyyyMMdd_HHmmss').txt"
            "Last pipeline update: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" | Out-File $timestampFile -Encoding UTF8
            git add $timestampFile
            Write-Host "Created timestamp file: $timestampFile" -ForegroundColor Gray
        }
        
        # Commit changes
        $commitMessage = "Pipeline update - $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
        Write-Host "Committing changes: $commitMessage" -ForegroundColor Yellow
        git commit -m $commitMessage
        Write-Host "Changes committed locally" -ForegroundColor Green
        
        # Set remote URL
        $remoteUrl = "https://$($global:config.GITHUB_TOKEN)@github.com/$($global:config.GITHUB_USERNAME)/$($global:config.GITHUB_REPO_NAME).git"
        
        # Check if remote exists
        $remotes = git remote -v 2>$null
        if ($remotes -match "origin") {
            Write-Host "Remote origin exists, updating URL..." -ForegroundColor Gray
            git remote set-url origin $remoteUrl
        }
        else {
            Write-Host "Adding remote origin..." -ForegroundColor Yellow
            git remote add origin $remoteUrl
            Write-Host "Remote origin added" -ForegroundColor Green
        }
        
        # First, pull any changes from remote
        Write-Host "Pulling latest changes from GitHub..." -ForegroundColor Yellow
        try {
            # Try to fetch first
            git fetch origin
            
            # Try to pull with rebase to integrate remote changes
            git pull --rebase origin $currentBranch 2>&1 | Out-Null
            Write-Host "Successfully pulled latest changes" -ForegroundColor Green
        }
        catch {
            Write-Host "No existing remote branch or pull failed, continuing..." -ForegroundColor Yellow
        }
        
        # Now push changes (without --force)
        Write-Host "Pushing changes to GitHub..." -ForegroundColor Yellow
        $pushResult = git push origin $currentBranch 2>&1
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "SUCCESS: Changes pushed to GitHub" -ForegroundColor Green
            
            Write-Host "===============================================================" -ForegroundColor Green
            Write-Host "GITHUB PUBLICATION COMPLETED SUCCESSFULLY" -ForegroundColor Green
            Write-Host "===============================================================" -ForegroundColor Green
            Write-Host "Repository: https://github.com/$($global:config.GITHUB_USERNAME)/$($global:config.GITHUB_REPO_NAME)" -ForegroundColor Cyan
            Write-Host "Project: $($global:config.PROJECT_NAME)" -ForegroundColor Cyan
            Write-Host "Branch: $currentBranch" -ForegroundColor Cyan
            Write-Host "Commit: $commitMessage" -ForegroundColor Cyan
            Write-Host "Time: $(Get-Date -Format 'HH:mm:ss')" -ForegroundColor Cyan
            Write-Host ""
            Write-Host "This commit has been ADDED to the existing history." -ForegroundColor Yellow
            
            return $true
        }
        else {
            $errorMsg = $pushResult | Out-String
            Write-Host "ERROR: Failed to push to GitHub" -ForegroundColor Red
            Write-Host "Error: $errorMsg" -ForegroundColor DarkRed
            
            # If push fails due to non-fast-forward, suggest merge
            if ($errorMsg -match "non-fast-forward" -or $errorMsg -match "failed to push some refs") {
                Write-Host ""
                Write-Host "SOLUTION: Remote has changes you don't have locally" -ForegroundColor Yellow
                Write-Host "Try: git pull --rebase origin $currentBranch" -ForegroundColor White
                Write-Host "Then run this script again" -ForegroundColor White
            }
            
            return $false
        }
    }
    catch {
        Write-Host "ERROR during publication: $_" -ForegroundColor Red
        return $false
    }
    finally {
        # Return to original directory
        Set-Location $originalLocation
    }
}

# Main function
function Main {
    # Display header
    Write-Host "===============================================================" -ForegroundColor Cyan
    Write-Host "SMART CONTRACT PIPELINE" -ForegroundColor Yellow
    Write-Host "===============================================================" -ForegroundColor Cyan
    Write-Host ""
    
    # Load configuration
    $global:config = Load-Configuration
    
    # Display options
    Write-Host "Select an option:" -ForegroundColor White
    Write-Host "1. Analyze project and create complete file" -ForegroundColor Gray
    Write-Host "2. Publish to GitHub (ADD commit to history)" -ForegroundColor Gray
    Write-Host "3. Analyze and publish to GitHub" -ForegroundColor Gray
    Write-Host "4. Exit" -ForegroundColor Gray
    Write-Host ""
    
    $choice = Read-Host "Enter choice (1-4)"
    
    switch ($choice) {
        "1" {
            # Analyze project
            Write-Host "Starting project analysis..." -ForegroundColor Yellow
            $fileCreated, $outputFile = Create-ProjectShareFile
            
            if ($fileCreated) {
                Write-Host "Analysis completed successfully" -ForegroundColor Green
            }
            
            Write-Host ""
            Write-Host "Press any key to continue..." -ForegroundColor Gray
            $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
            Main
        }
        "2" {
            # Publish to GitHub
            Write-Host ""
            Write-Host "NOTE: This will ADD a new commit to the existing history" -ForegroundColor Yellow
            Write-Host "Continue? (Y/N)" -ForegroundColor White
            $confirm = Read-Host
            
            if ($confirm -eq "Y" -or $confirm -eq "y") {
                $success = Publish-ToGitHub
            }
            else {
                Write-Host "Operation cancelled" -ForegroundColor Gray
            }
            
            Write-Host ""
            Write-Host "Press any key to continue..." -ForegroundColor Gray
            $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
            Main
        }
        "3" {
            # Analyze and publish
            Write-Host "Starting project analysis..." -ForegroundColor Yellow
            $fileCreated, $outputFile = Create-ProjectShareFile
            
            if ($fileCreated) {
                Write-Host ""
                Write-Host "NOTE: This will ADD a new commit to the existing history" -ForegroundColor Yellow
                Write-Host "Continue with publication? (Y/N)" -ForegroundColor White
                $confirm = Read-Host
                
                if ($confirm -eq "Y" -or $confirm -eq "y") {
                    Write-Host "Publishing to GitHub..." -ForegroundColor Yellow
                    Publish-ToGitHub
                }
                else {
                    Write-Host "Publication cancelled" -ForegroundColor Gray
                }
            }
            
            Write-Host ""
            Write-Host "Press any key to continue..." -ForegroundColor Gray
            $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
            Main
        }
        "4" {
            Write-Host "Goodbye!" -ForegroundColor Green
            exit 0
        }
        default {
            Write-Host "Invalid choice" -ForegroundColor Red
            Write-Host ""
            Write-Host "Press any key to continue..." -ForegroundColor Gray
            $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
            Main
        }
    }
}

# Start the script
try {
    Main
}
catch {
    Write-Host "UNEXPECTED ERROR: $_" -ForegroundColor Red
    Write-Host ""
    Write-Host "Press any key to exit..." -ForegroundColor Gray
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
    exit 1
}
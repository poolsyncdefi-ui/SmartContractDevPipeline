# ShareSplit1M_Working.ps1
# ============================================================================
# CONFIGURATION
# ============================================================================
# Lecture de la configuration
$configPath = ".\..\project_config.json"
if (Test-Path $configPath) {
    $config = Get-Content $configPath -Raw | ConvertFrom-Json
    $PROJECT_NAME = $config.PROJECT_NAME
    $PROJECT_PATH = $config.PROJECT_PATH
    $GITHUB_TOKEN = $config.GITHUB_TOKEN
    $GITHUB_USERNAME = $config.GITHUB_USERNAME
    $GITHUB_REPO_NAME = $config.GITHUB_REPO_NAME
    $GITHUB_REPO_PRIVATE = $config.GITHUB_REPO_PRIVATE
    $GITHUB_REPO_DESCRIPTION = $config.GITHUB_REPO_DESCRIPTION
} else {
    Write-Host "Fichier de configuration non trouve. Utilisation des valeurs par defaut." -ForegroundColor Yellow
    $PROJECT_NAME = "MonProjet"
    $PROJECT_PATH = "."
    $GITHUB_TOKEN = ""
    $GITHUB_USERNAME = ""
    $GITHUB_REPO_NAME = ""
    $GITHUB_REPO_PRIVATE = $false
    $GITHUB_REPO_DESCRIPTION = "Projet partage automatiquement"
}

# ============================================================================
# FONCTION POUR PUBLIER SUR GITHUB REPOSITORY - VERSION FONCTIONNELLE
# ============================================================================
function Publish-ToGitHubRepo-Working {
    param(
        [string]$Token,
        [string]$Username,
        [string]$RepoName,
        [string]$Description,
        [bool]$IsPrivate
    )
    
    Write-Host "`n=== PUBLICATION SUR GITHUB REPOSITORY ===" -ForegroundColor Cyan
    
    # CRITIQUE: Verifier que nous sommes dans le bon repertoire
    Write-Host "Verification du repertoire..." -NoNewline
    $currentDir = Get-Location
    $projectDir = Resolve-Path $PROJECT_PATH -ErrorAction SilentlyContinue
    
    if ($currentDir.Path -ne $projectDir.Path) {
        Write-Host " ✗" -ForegroundColor Red
        Write-Host "ERREUR: Vous devez etre dans le dossier du projet!" -ForegroundColor Red
        Write-Host "Actuel: $currentDir" -ForegroundColor Yellow
        Write-Host "Projet: $projectDir" -ForegroundColor Yellow
        Write-Host "Executez: cd '$PROJECT_PATH'" -ForegroundColor Cyan
        return @{ success = $false; error = "Mauvais repertoire" }
    }
    Write-Host " ✓" -ForegroundColor Green
    
    # CRITIQUE: Verifier le token
    if ([string]::IsNullOrWhiteSpace($Token) -or $Token -notmatch "^ghp_[a-zA-Z0-9]{36,}$") {
        Write-Host "❌ Token invalide ou manquant" -ForegroundColor Red
        return @{ success = $false; error = "Token GitHub invalide" }
    }
    
    # CRITIQUE: Verifier que Git est installe
    try {
        git --version | Out-Null
    } catch {
        Write-Host "❌ Git non installe" -ForegroundColor Red
        return @{ success = $false; error = "Git non installe" }
    }
    
    # CRITIQUE: Nettoyer la configuration Git
    Write-Host "Nettoyage Git..." -NoNewline
    git config --global --unset credential.helper 2>$null
    git config --global credential.helper "" 2>$null
    Write-Host " ✓" -ForegroundColor Green
    
    try {
        # CRITIQUE: Initialiser Git si necessaire
        if (-not (Test-Path ".git")) {
            Write-Host "Initialisation Git..." -NoNewline
            git init
            Write-Host " ✓" -ForegroundColor Green
        } else {
            Write-Host "✓ Git deja initialise" -ForegroundColor Gray
        }
        
        # CRITIQUE: Configurer Git
        Write-Host "Configuration Git..." -NoNewline
        git config user.name "$Username"
        git config user.email "$Username@users.noreply.github.com"
        Write-Host " ✓" -ForegroundColor Green
        
        # CRITIQUE: Creer le .gitignore pour exclure les fichiers sensibles
        $gitignoreContent = @"
# Fichiers sensibles
project_config.json
*.backup
*.bak

# Fichiers generes
PROJECT_SHARE_*
GISTS_INDEX*
GITHUB_PUBLISH_*

# Dossiers systeme
node_modules/
.vscode/
.idea/
__pycache__/
.env
"@
        $gitignoreContent | Out-File ".gitignore" -Encoding UTF8
        
        # CRITIQUE: Preparer l URL avec le token
        $remoteUrl = "https://x-access-token:${Token}@github.com/${Username}/${RepoName}.git"
        Write-Host "Remote: https://github.com/${Username}/${RepoName}" -ForegroundColor Gray
        
        # CRITIQUE: Gerer le remote
        git remote remove origin 2>$null
        git remote add origin $remoteUrl
        
        # Ajouter tous les fichiers
        Write-Host "Ajout fichiers..." -NoNewline
        git add .
        Write-Host " ✓" -ForegroundColor Green
        
        # Commit
        Write-Host "Commit..." -NoNewline
        $commitMsg = "🚀 Publication: $PROJECT_NAME - $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
        git commit -m $commitMsg --quiet
        Write-Host " ✓" -ForegroundColor Green
        
        # CRITIQUE: Creer la branche main
        Write-Host "Branche..." -NoNewline
        git branch -M main
        Write-Host " ✓" -ForegroundColor Green
        
        # CORRECTION: Push avec l approche en deux etapes
        Write-Host "Push vers GitHub..." -NoNewline
        # Desactiver les prompts
        $env:GIT_TERMINAL_PROMPT = "0"
        
        # Premiere tentative : push normal
        $pushOutput = git push -u origin main 2>&1
        
        # Si echec avec erreur d histoires non liees, essayer avec --force
        if ($LASTEXITCODE -ne 0) {
            if ($pushOutput -match "failed to push some refs" -or $pushOutput -match "unrelated histories" -or $pushOutput -match "non-fast-forward") {
                Write-Host " (tentative avec --force)..." -NoNewline -ForegroundColor Yellow
                $pushOutput = git push -u origin main --force 2>&1
            }
        }
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host " ✓" -ForegroundColor Green
            Write-Host "✅ PUBLICATION REUSSIE !" -ForegroundColor Green
            Write-Host "🔗 https://github.com/$Username/$RepoName" -ForegroundColor Cyan
            return @{
                success = $true
                repo_url = "https://github.com/$Username/$RepoName"
                message = "Publication reussie"
            }
        } else {
            Write-Host " ✗" -ForegroundColor Red
            # Analyser l erreur
            $errorMsg = "Erreur Git"
            if ($pushOutput -match "Authentication failed") {
                $errorMsg = "Token invalide - Regenez-le sur GitHub"
            } elseif ($pushOutput -match "Repository not found") {
                $errorMsg = "Repository non trouve - Creez-le d abord sur GitHub"
            } elseif ($pushOutput -match "GH013" -or $pushOutput -match "secret") {
                $errorMsg = "GitHub a bloque le push (secret detecte) - Autorisez-le sur GitHub"
            } else {
                $errorMsg = "Erreur: $($pushOutput | Select-Object -First 2)"
            }
            Write-Host "❌ $errorMsg" -ForegroundColor Red
            return @{
                success = $false
                error = $errorMsg
                git_output = $pushOutput
            }
        }
    } catch {
        Write-Host " ✗" -ForegroundColor Red
        Write-Host "❌ Erreur inattendue: $_" -ForegroundColor Red
        return @{
            success = $false
            error = $_.Exception.Message
        }
    }
}

# ============================================================================
# FONCTION POUR PARTAGER SUR GITHUB GISTS
# ============================================================================
function Publish-ToGitHubGists {
    param(
        [string]$Token,
        [string]$Username,
        [string]$ProjectName,
        [int]$MaxFileSizeKB = 250
    )
    
    Write-Host "`n=== PARTAGE SUR GITHUB GISTS ===" -ForegroundColor Cyan
    
    # Verifier le token
    if ([string]::IsNullOrWhiteSpace($Token) -or $Token -notmatch "^ghp_[a-zA-Z0-9]{36,}$") {
        Write-Host "❌ Token invalide ou manquant" -ForegroundColor Red
        return @{ success = $false; error = "Token GitHub invalide" }
    }
    
    # Verifier le chemin du projet
    Write-Host "Verification du repertoire..." -NoNewline
    $currentDir = Get-Location
    $projectDir = Resolve-Path $PROJECT_PATH -ErrorAction SilentlyContinue
    
    if ($currentDir.Path -ne $projectDir.Path) {
        Write-Host " ✗" -ForegroundColor Red
        Write-Host "ERREUR: Vous devez etre dans le dossier du projet!" -ForegroundColor Red
        Write-Host "Actuel: $currentDir" -ForegroundColor Yellow
        Write-Host "Projet: $projectDir" -ForegroundColor Yellow
        Write-Host "Executez: cd '$PROJECT_PATH'" -ForegroundColor Cyan
        return @{ success = $false; error = "Mauvais repertoire" }
    }
    Write-Host " ✓" -ForegroundColor Green
    
    # Lister les fichiers a partager
    Write-Host "Analyse des fichiers du projet..." -NoNewline
    $projectFiles = Get-ChildItem -Path . -File -Recurse | 
        Where-Object { 
            $_.FullName -notmatch "\\.git" -and 
            $_.FullName -notmatch "project_config.json" -and
            $_.FullName -notmatch "PROJECT_SHARE_" -and
            $_.FullName -notmatch "GISTS_INDEX" -and
            $_.FullName -notmatch "GITHUB_PUBLISH_"
        }
    
    if (-not $projectFiles) {
        Write-Host " ✗" -ForegroundColor Red
        Write-Host "❌ Aucun fichier trouve a partager" -ForegroundColor Red
        return @{ success = $false; error = "Aucun fichier a partager" }
    }
    Write-Host " ✓ ($($projectFiles.Count) fichiers)" -ForegroundColor Green
    
    # Preparer les donnees pour les Gists
    $gistsData = @()
    $currentGistFiles = @{}
    $currentSize = 0
    $gistCounter = 1
    $fileCounter = 0
    
    Write-Host "Preparation des Gists..." -ForegroundColor Yellow
    
    foreach ($file in $projectFiles) {
        $fileSizeKB = [math]::Round($file.Length / 1KB, 2)
        $relativePath = $file.FullName.Substring($projectDir.Path.Length + 1)
        
        # Si le fichier est trop gros pour un Gist
        if ($fileSizeKB > $MaxFileSizeKB) {
            Write-Host "  ⚠ Fichier trop gros: $relativePath ($fileSizeKB KB)" -ForegroundColor Yellow
            continue
        }
        
        # Verifier si on depasse la limite de taille pour le Gist actuel
        $shouldCreateNewGist = ($currentSize + $fileSizeKB > $MaxFileSizeKB) -and ($currentGistFiles.Count -gt 0)
        if ($shouldCreateNewGist) {
            # Creer un Gist avec les fichiers actuels
            $gistName = "${ProjectName}_Part${gistCounter}"
            $gistsData += @{
                Name = $gistName
                Files = $currentGistFiles.Clone()
                TotalSizeKB = $currentSize
                FileCount = $currentGistFiles.Count
            }
            
            # Reinitialiser pour le prochain Gist
            $currentGistFiles = @{}
            $currentSize = 0
            $gistCounter++
        }
        
        # Lire le contenu du fichier
        try {
            $content = Get-Content -Path $file.FullName -Raw -Encoding UTF8
            $currentGistFiles[$relativePath] = @{
                content = $content
                sizeKB = $fileSizeKB
            }
            $currentSize += $fileSizeKB
            $fileCounter++
            Write-Host "  ✓ $relativePath ($fileSizeKB KB)" -ForegroundColor Gray
        } catch {
            Write-Host "  ✗ Erreur lecture: $relativePath" -ForegroundColor Red
        }
    }
    
    # Ajouter le dernier Gist s il reste des fichiers
    if ($currentGistFiles.Count -gt 0) {
        $gistName = "${ProjectName}_Part${gistCounter}"
        $gistsData += @{
            Name = $gistName
            Files = $currentGistFiles.Clone()
            TotalSizeKB = $currentSize
            FileCount = $currentGistFiles.Count
        }
    }
    
    if ($gistsData.Count -eq 0) {
        Write-Host "❌ Aucun Gist a creer" -ForegroundColor Red
        return @{ success = $false; error = "Aucun Gist a creer" }
    }
    
    Write-Host "`nResume:" -ForegroundColor Cyan
    Write-Host "• Fichiers traites: $fileCounter" -ForegroundColor Gray
    Write-Host "• Gists a creer: $($gistsData.Count)" -ForegroundColor Gray
    Write-Host "• Taille max par Gist: ${MaxFileSizeKB} KB" -ForegroundColor Gray
    
    # Demander confirmation
    Write-Host "`nConfirmez la creation des Gists ? (O/N)" -ForegroundColor Yellow
    $confirm = Read-Host
    if ($confirm -notmatch "^[OoYy]") {
        Write-Host "Operation annulee" -ForegroundColor Yellow
        return @{ success = $false; error = "Operation annulee par l utilisateur" }
    }
    
    # Creer les Gists via API GitHub
    $createdGists = @()
    $failedGists = @()
    $indexContent = "# GISTS INDEX - $ProjectName`n`n"
    $indexContent += "Date: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')`n"
    $indexContent += "Nombre de Gists: $($gistsData.Count)`n"
    $indexContent += "Fichiers totaux: $fileCounter`n`n"
    $indexContent += "## LISTE DES GISTS`n`n"
    
    $baseHeaders = @{
        "Authorization" = "token $Token"
        "Accept" = "application/vnd.github.v3+json"
        "Content-Type" = "application/json"
    }
    
    foreach ($gist in $gistsData) {
        Write-Host "`nCreation du Gist: $($gist.Name)..." -NoNewline
        
        # Preparer les fichiers pour l API
        $gistFiles = @{}
        foreach ($fileEntry in $gist.Files.GetEnumerator()) {
            $fileName = $fileEntry.Key
            $fileData = $fileEntry.Value
            $gistFiles[$fileName] = @{ content = $fileData.content }
        }
        
        # Corps de la requete
        $body = @{
            description = "$ProjectName - $($gist.Name)"
            public = $true
            files = $gistFiles
        } | ConvertTo-Json -Depth 10
        
        try {
            # Appel API GitHub
            $response = Invoke-RestMethod -Uri "https://api.github.com/gists" `
                -Method Post `
                -Headers $baseHeaders `
                -Body $body `
                -TimeoutSec 30 `
                -ErrorAction Stop
            
            $gistUrl = $response.html_url
            $createdGists += @{
                Name = $gist.Name
                URL = $gistUrl
                FileCount = $gist.FileCount
                SizeKB = $gist.TotalSizeKB
            }
            
            Write-Host " ✓" -ForegroundColor Green
            Write-Host "  URL: $gistUrl" -ForegroundColor Gray
            
            # Ajouter a l index
            $indexContent += "### $($gist.Name)`n"
            $indexContent += "- URL: $gistUrl`n"
            $indexContent += "- Fichiers: $($gist.FileCount)`n"
            $indexContent += "- Taille: $($gist.TotalSizeKB) KB`n"
            $indexContent += "- Fichiers inclus:`n"
            
            foreach ($fileName in $gist.Files.Keys | Sort-Object) {
                $fileSize = $gist.Files[$fileName].sizeKB
                $indexContent += "  * $fileName ($fileSize KB)`n"
            }
            $indexContent += "`n"
            
        } catch {
            Write-Host " ✗" -ForegroundColor Red
            $errorMsg = $_.Exception.Message
            Write-Host "  Erreur: $errorMsg" -ForegroundColor Red
            $failedGists += @{
                Name = $gist.Name
                Error = $errorMsg
            }
        }
        
        # Pause pour eviter les limites de rate limit
        if ($gistsData.IndexOf($gist) -lt $gistsData.Count - 1) {
            Start-Sleep -Seconds 1
        }
    }
    
    # Sauvegarder l index localement
    $indexFileName = "GISTS_INDEX_$(Get-Date -Format 'yyyyMMdd_HHmmss').txt"
    $indexContent | Out-File -FilePath $indexFileName -Encoding UTF8
    
    Write-Host "`n=== RESUME ===" -ForegroundColor Cyan
    Write-Host "Gists crees avec succes: $($createdGists.Count)" -ForegroundColor Green
    
    if ($createdGists.Count -gt 0) {
        Write-Host "`nListe des Gists:" -ForegroundColor Yellow
        foreach ($gist in $createdGists) {
            Write-Host "• $($gist.Name): $($gist.URL)" -ForegroundColor Gray
        }
    }
    
    if ($failedGists.Count -gt 0) {
        Write-Host "`nGists en echec: $($failedGists.Count)" -ForegroundColor Red
        foreach ($failed in $failedGists) {
            Write-Host "• $($failed.Name): $($failed.Error)" -ForegroundColor Red
        }
    }
    
    Write-Host "`nIndex local sauvegarde: $indexFileName" -ForegroundColor Green
    
    return @{
        success = ($failedGists.Count -eq 0)
        created_gists = $createdGists
        failed_gists = $failedGists
        index_file = $indexFileName
        total_created = $createdGists.Count
        total_failed = $failedGists.Count
    }
}

# ============================================================================
# FONCTION POUR GENERER LES FICHIERS LOCAUX
# ============================================================================
function Generate-LocalFiles {
    param(
        [string]$ProjectName,
        [int]$MaxFileSizeKB = 1000
    )
    
    Write-Host "`n=== GENERATION DES FICHIERS LOCAUX ===" -ForegroundColor Cyan
    
    # Verifier le chemin du projet
    Write-Host "Verification du repertoire..." -NoNewline
    $currentDir = Get-Location
    $projectDir = Resolve-Path $PROJECT_PATH -ErrorAction SilentlyContinue
    
    if ($currentDir.Path -ne $projectDir.Path) {
        Write-Host " ✗" -ForegroundColor Red
        Write-Host "ERREUR: Vous devez etre dans le dossier du projet!" -ForegroundColor Red
        Write-Host "Actuel: $currentDir" -ForegroundColor Yellow
        Write-Host "Projet: $projectDir" -ForegroundColor Yellow
        Write-Host "Executez: cd '$PROJECT_PATH'" -ForegroundColor Cyan
        return @{ success = $false; error = "Mauvais repertoire" }
    }
    Write-Host " ✓" -ForegroundColor Green
    
    # Lister les fichiers du projet
    Write-Host "Analyse des fichiers..." -NoNewline
    $projectFiles = Get-ChildItem -Path . -File -Recurse | 
        Where-Object { 
            $_.FullName -notmatch "\\.git" -and 
            $_.FullName -notmatch "project_config.json" -and
            $_.FullName -notmatch "PROJECT_SHARE_" -and
            $_.FullName -notmatch "GISTS_INDEX" -and
            $_.FullName -notmatch "GITHUB_PUBLISH_"
        }
    
    if (-not $projectFiles) {
        Write-Host " ✗" -ForegroundColor Red
        Write-Host "❌ Aucun fichier trouve" -ForegroundColor Red
        return @{ success = $false; error = "Aucun fichier trouve" }
    }
    Write-Host " ✓ ($($projectFiles.Count) fichiers)" -ForegroundColor Green
    
    # Preparer les donnees pour les fichiers partages
    $shareParts = @()
    $currentPartFiles = @()
    $currentPartSize = 0
    $partCounter = 1
    $totalFilesProcessed = 0
    
    Write-Host "Preparation des fichiers partages..." -ForegroundColor Yellow
    
    foreach ($file in $projectFiles) {
        $fileSizeKB = [math]::Round($file.Length / 1KB, 2)
        $relativePath = $file.FullName.Substring($projectDir.Path.Length + 1)
        
        # Verifier si on depasse la limite de taille
        $shouldCreateNewPart = ($currentPartSize + $fileSizeKB > $MaxFileSizeKB) -and ($currentPartFiles.Count -gt 0)
        if ($shouldCreateNewPart) {
            # Creer une partie
            $shareParts += @{
                PartNumber = $partCounter
                Files = $currentPartFiles.Clone()
                TotalSizeKB = $currentPartSize
            }
            
            # Reinitialiser pour la partie suivante
            $currentPartFiles = @()
            $currentPartSize = 0
            $partCounter++
        }
        
        # Lire le contenu du fichier
        try {
            $content = Get-Content -Path $file.FullName -Raw -Encoding UTF8
            $currentPartFiles += @{
                Path = $relativePath
                Content = $content
                SizeKB = $fileSizeKB
            }
            $currentPartSize += $fileSizeKB
            $totalFilesProcessed++
            Write-Host "  ✓ $relativePath ($fileSizeKB KB)" -ForegroundColor Gray
        } catch {
            Write-Host "  ✗ Erreur lecture: $relativePath" -ForegroundColor Red
        }
    }
    
    # Ajouter la derniere partie s il reste des fichiers
    if ($currentPartFiles.Count -gt 0) {
        $shareParts += @{
            PartNumber = $partCounter
            Files = $currentPartFiles
            TotalSizeKB = $currentPartSize
        }
    }
    
    if ($shareParts.Count -eq 0) {
        Write-Host "❌ Aucune partie a creer" -ForegroundColor Red
        return @{ success = $false; error = "Aucune partie a creer" }
    }
    
    # Generer les fichiers partages
    $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $shareFilesCreated = @()
    
    Write-Host "`nGeneration des fichiers..." -ForegroundColor Cyan
    
    foreach ($part in $shareParts) {
        $fileName = "PROJECT_SHARE_PART$($part.PartNumber)_$timestamp.txt"
        $fileContent = "# PROJECT SHARE - Part $($part.PartNumber)`n"
        $fileContent += "# Project: $ProjectName`n"
        $fileContent += "# Generated: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')`n"
        $fileContent += "# Total size: $($part.TotalSizeKB) KB`n"
        $fileContent += "# Files: $($part.Files.Count)`n"
        $fileContent += "`n"
        
        foreach ($file in $part.Files) {
            $fileContent += "=" * 60 + "`n"
            $fileContent += "FILE: $($file.Path)`n"
            $fileContent += "SIZE: $($file.SizeKB) KB`n"
            $fileContent += "=" * 60 + "`n"
            $fileContent += $file.Content
            $fileContent += "`n`n"
        }
        
        $fileContent | Out-File -FilePath $fileName -Encoding UTF8
        $shareFilesCreated += $fileName
        Write-Host "  ✓ $fileName ($($part.Files.Count) fichiers, $($part.TotalSizeKB) KB)" -ForegroundColor Green
    }
    
    # Generer le fichier index
    $indexFileName = "PROJECT_SHARE_INDEX_$timestamp.txt"
    $indexContent = "# PROJECT SHARE INDEX`n"
    $indexContent += "# Project: $ProjectName`n"
    $indexContent += "# Generated: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')`n"
    $indexContent += "# Total parts: $($shareParts.Count)`n"
    $indexContent += "# Total files: $totalFilesProcessed`n"
    $indexContent += "`n"
    $indexContent += "## PARTS LIST`n`n"
    
    foreach ($part in $shareParts) {
        $fileName = "PROJECT_SHARE_PART$($part.PartNumber)_$timestamp.txt"
        $indexContent += "### Part $($part.PartNumber) - $fileName`n"
        $indexContent += "- Size: $($part.TotalSizeKB) KB`n"
        $indexContent += "- Files: $($part.Files.Count)`n"
        $indexContent += "- Files included:`n"
        
        foreach ($file in $part.Files) {
            $indexContent += "  * $($file.Path) ($($file.SizeKB) KB)`n"
        }
        $indexContent += "`n"
    }
    
    $indexContent | Out-File -FilePath $indexFileName -Encoding UTF8
    $shareFilesCreated += $indexFileName
    
    Write-Host "`n=== RESUME ===" -ForegroundColor Cyan
    Write-Host "Fichiers generes: $($shareFilesCreated.Count)" -ForegroundColor Green
    Write-Host "• Index: $indexFileName" -ForegroundColor Gray
    foreach ($fileName in $shareFilesCreated) {
        if ($fileName -ne $indexFileName) {
            Write-Host "• Part: $fileName" -ForegroundColor Gray
        }
    }
    
    return @{
        success = $true
        files_created = $shareFilesCreated
        total_parts = $shareParts.Count
        total_files = $totalFilesProcessed
        index_file = $indexFileName
    }
}

# ============================================================================
# MENU PRINCIPAL FONCTIONNEL
# ============================================================================
function Show-MainMenu {
    Clear-Host
    Write-Host ""
    Write-Host "=" * 60 -ForegroundColor Cyan
    Write-Host "SHARE SPLIT 1M - $PROJECT_NAME" -ForegroundColor Cyan
    Write-Host "=" * 60 -ForegroundColor Cyan
    Write-Host ""
    Write-Host "=== MENU PRINCIPAL ===" -ForegroundColor Yellow
    Write-Host "1. Publier sur GitHub Repository" -ForegroundColor Green
    Write-Host "2. Partager sur GitHub Gists" -ForegroundColor Yellow
    Write-Host "3. Generer seulement les fichiers locaux" -ForegroundColor Yellow
    Write-Host "4. Quitter" -ForegroundColor Red
    Write-Host ""
    $choice = Read-Host "Votre choix [1-4]"
    
    switch ($choice) {
        '1' {
            Write-Host "`n=== PUBLICATION GITHUB REPOSITORY ===" -ForegroundColor Cyan
            
            # Verifier le token
            if (-not $GITHUB_TOKEN -or $GITHUB_TOKEN -eq "*** REMOVED FOR SECURITY ***") {
                Write-Host "🔑 TOKEN GITHUB REQUIS" -ForegroundColor Yellow
                Write-Host "Collez votre token GitHub (commence par 'ghp_'):"
                $GITHUB_TOKEN = Read-Host
            }
            
            # Verifier les autres informations
            if (-not $GITHUB_USERNAME) {
                $GITHUB_USERNAME = Read-Host "Nom d utilisateur GitHub"
            }
            if (-not $GITHUB_REPO_NAME) {
                $GITHUB_REPO_NAME = Read-Host "Nom du repository"
            }
            
            # CRITIQUE: S assurer d etre dans le bon repertoire
            Write-Host "`nVerification du repertoire..." -ForegroundColor Yellow
            if ((Get-Location).Path -ne (Resolve-Path $PROJECT_PATH).Path) {
                Write-Host "ATTENTION: Vous devez etre dans: $PROJECT_PATH" -ForegroundColor Red
                Write-Host "Executez d abord: cd '$PROJECT_PATH'" -ForegroundColor Cyan
                Read-Host "Appuyez sur Entree pour continuer..."
                return
            }
            
            # Executer la publication
            $result = Publish-ToGitHubRepo-Working -Token $GITHUB_TOKEN `
                -Username $GITHUB_USERNAME `
                -RepoName $GITHUB_REPO_NAME `
                -Description $GITHUB_REPO_DESCRIPTION `
                -IsPrivate $GITHUB_REPO_PRIVATE
            
            if ($result.success) {
                Write-Host ""
                Write-Host "✅ Publication reussie sur GitHub!" -ForegroundColor Green
                Write-Host "Repository: $($result.repo_url)" -ForegroundColor Cyan
            } else {
                Write-Host ""
                Write-Host "❌ Echec de la publication" -ForegroundColor Red
                Write-Host "Erreur: $($result.error)" -ForegroundColor Red
                
                # Conseils de depannage
                if ($result.error -match "Token") {
                    Write-Host "`n=== CONSEILS ===" -ForegroundColor Yellow
                    Write-Host "1. https://github.com/settings/tokens" -ForegroundColor Gray
                    Write-Host "2. 'Generate new token (classic)'" -ForegroundColor Gray
                    Write-Host "3. Permission: 'repo' (TOUTE la section)" -ForegroundColor Green
                    Write-Host "4. Copiez le token (ghp_...)" -ForegroundColor Gray
                }
            }
            Write-Host ""
            Write-Host "Appuyez sur Entree pour continuer..."
            Read-Host
        }
        '2' {
            Write-Host "`n=== GITHUB GISTS ===" -ForegroundColor Cyan
            
            # Verifier le token
            if (-not $GITHUB_TOKEN -or $GITHUB_TOKEN -eq "*** REMOVED FOR SECURITY ***") {
                Write-Host "🔑 TOKEN GITHUB REQUIS" -ForegroundColor Yellow
                Write-Host "Collez votre token GitHub (commence par 'ghp_'):"
                $GITHUB_TOKEN = Read-Host
            }
            
            # Verifier le nom d utilisateur
            if (-not $GITHUB_USERNAME) {
                $GITHUB_USERNAME = Read-Host "Nom d utilisateur GitHub"
            }
            
            # Verifier le repertoire
            Write-Host "`nVerification du repertoire..." -ForegroundColor Yellow
            if ((Get-Location).Path -ne (Resolve-Path $PROJECT_PATH).Path) {
                Write-Host "ATTENTION: Vous devez etre dans: $PROJECT_PATH" -ForegroundColor Red
                Write-Host "Executez d abord: cd '$PROJECT_PATH'" -ForegroundColor Cyan
                Read-Host "Appuyez sur Entree pour continuer..."
                return
            }
            
            # Demander la taille max des Gists
            Write-Host "`nTaille maximale par Gist (en KB) [defaut: 250]:"
            $maxSizeInput = Read-Host
            if (-not [int]::TryParse($maxSizeInput, [ref]$null) -or [int]$maxSizeInput -le 0) {
                $maxSizeKB = 250
            } else {
                $maxSizeKB = [int]$maxSizeInput
            }
            
            # Executer la publication sur Gists
            $result = Publish-ToGitHubGists -Token $GITHUB_TOKEN `
                -Username $GITHUB_USERNAME `
                -ProjectName $PROJECT_NAME `
                -MaxFileSizeKB $maxSizeKB
            
            if ($result.success -or $result.total_created -gt 0) {
                Write-Host ""
                Write-Host "✅ $($result.total_created) Gists crees avec succes!" -ForegroundColor Green
                if ($result.total_failed -gt 0) {
                    Write-Host "⚠ $($result.total_failed) Gists en echec" -ForegroundColor Yellow
                }
                Write-Host "Index local: $($result.index_file)" -ForegroundColor Cyan
            } else {
                Write-Host ""
                Write-Host "❌ Echec de la creation des Gists" -ForegroundColor Red
                Write-Host "Erreur: $($result.error)" -ForegroundColor Red
            }
            
            Write-Host ""
            Write-Host "Appuyez sur Entree pour continuer..."
            Read-Host
        }
        '3' {
            Write-Host "`n=== FICHIERS LOCAUX ===" -ForegroundColor Cyan
            
            # Verifier le repertoire
            Write-Host "Verification du repertoire..." -ForegroundColor Yellow
            if ((Get-Location).Path -ne (Resolve-Path $PROJECT_PATH).Path) {
                Write-Host "ATTENTION: Vous devez etre dans: $PROJECT_PATH" -ForegroundColor Red
                Write-Host "Executez d abord: cd '$PROJECT_PATH'" -ForegroundColor Cyan
                Read-Host "Appuyez sur Entree pour continuer..."
                return
            }
            
            # Demander la taille max des fichiers
            Write-Host "`nTaille maximale par fichier (en KB) [defaut: 1000]:"
            $maxSizeInput = Read-Host
            if (-not [int]::TryParse($maxSizeInput, [ref]$null) -or [int]$maxSizeInput -le 0) {
                $maxSizeKB = 1000
            } else {
                $maxSizeKB = [int]$maxSizeInput
            }
            
            # Generer les fichiers
            $result = Generate-LocalFiles -ProjectName $PROJECT_NAME -MaxFileSizeKB $maxSizeKB
            
            if ($result.success) {
                Write-Host ""
                Write-Host "✅ $($result.total_parts) fichiers generes avec succes!" -ForegroundColor Green
                Write-Host "Total fichiers inclus: $($result.total_files)" -ForegroundColor Gray
                Write-Host "Fichier index: $($result.index_file)" -ForegroundColor Cyan
            } else {
                Write-Host ""
                Write-Host "❌ Echec de la generation des fichiers" -ForegroundColor Red
                Write-Host "Erreur: $($result.error)" -ForegroundColor Red
            }
            
            Write-Host ""
            Write-Host "Appuyez sur Entree pour continuer..."
            Read-Host
        }
        '4' {
            Write-Host "Au revoir!" -ForegroundColor Green
            exit 0
        }
        default {
            Write-Host "Choix invalide!" -ForegroundColor Red
            Start-Sleep -Seconds 1
        }
    }
}

# ============================================================================
# POINT D ENTREE
# ============================================================================
# Boucle principale
do {
    try {
        Show-MainMenu
    } catch {
        Write-Host "❌ Erreur: $_" -ForegroundColor Red
        Write-Host "Redemarrage dans 3 secondes..." -ForegroundColor Yellow
        Start-Sleep -Seconds 3
    }
} while ($true)
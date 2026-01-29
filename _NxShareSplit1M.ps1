# ShareSplit1M_Complete.ps1
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
    Write-Host "Fichier de configuration non trouvé. Utilisation des valeurs par défaut." -ForegroundColor Yellow
    $PROJECT_NAME = "MonProjet"
    $PROJECT_PATH = "."
    $GITHUB_TOKEN = ""
    $GITHUB_USERNAME = ""
    $GITHUB_REPO_NAME = ""
    $GITHUB_REPO_PRIVATE = $false
    $GITHUB_REPO_DESCRIPTION = "Projet partagé automatiquement"
}

# ============================================================================
# FONCTION POUR PUBLIER SUR GITHUB REPOSITORY
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
    
    # CRITIQUE: Vérifier que nous sommes dans le bon répertoire
    Write-Host "Vérification du répertoire..." -NoNewline
    $currentDir = Get-Location
    $projectDir = Resolve-Path $PROJECT_PATH -ErrorAction SilentlyContinue
    
    if ($currentDir.Path -ne $projectDir.Path) {
        Write-Host " ✗" -ForegroundColor Red
        Write-Host "ERREUR: Vous devez être dans le dossier du projet!" -ForegroundColor Red
        Write-Host "Actuel: $currentDir" -ForegroundColor Yellow
        Write-Host "Projet: $projectDir" -ForegroundColor Yellow
        Write-Host "Exécutez: cd '$PROJECT_PATH'" -ForegroundColor Cyan
        return @{ success = $false; error = "Mauvais répertoire" }
    }
    Write-Host " ✓" -ForegroundColor Green
    
    # CRITIQUE: Vérifier le token
    if ([string]::IsNullOrWhiteSpace($Token) -or $Token -notmatch "^ghp_[a-zA-Z0-9]{36,}$") {
        Write-Host "❌ Token invalide ou manquant" -ForegroundColor Red
        return @{ success = $false; error = "Token GitHub invalide" }
    }
    
    # CRITIQUE: Vérifier que Git est installé
    try {
        git --version | Out-Null
    } catch {
        Write-Host "❌ Git non installé" -ForegroundColor Red
        return @{ success = $false; error = "Git non installé" }
    }
    
    # CRITIQUE: Nettoyer la configuration Git
    Write-Host "Nettoyage Git..." -NoNewline
    git config --global --unset credential.helper 2>$null
    git config --global credential.helper "" 2>$null
    Write-Host " ✓" -ForegroundColor Green
    
    try {
        # CRITIQUE: Initialiser Git si nécessaire
        if (-not (Test-Path ".git")) {
            Write-Host "Initialisation Git..." -NoNewline
            git init
            Write-Host " ✓" -ForegroundColor Green
        } else {
            Write-Host "✓ Git déjà initialisé" -ForegroundColor Gray
        }
        
        # CRITIQUE: Configurer Git
        Write-Host "Configuration Git..." -NoNewline
        git config user.name "$Username"
        git config user.email "$Username@users.noreply.github.com"
        Write-Host " ✓" -ForegroundColor Green
        
        # CRITIQUE: Créer le .gitignore pour exclure les fichiers sensibles
        $gitignoreContent = @"
# Fichiers sensibles
project_config.json
*.backup
*.bak

# Fichiers générés
PROJECT_SHARE_*
GISTS_INDEX*
GITHUB_PUBLISH_*

# Dossiers système
node_modules/
.vscode/
.idea/
__pycache__/
.env
"@
        $gitignoreContent | Out-File ".gitignore" -Encoding UTF8
        
        # CRITIQUE: Préparer l'URL avec le token
        $remoteUrl = "https://x-access-token:${Token}@github.com/${Username}/${RepoName}.git"
        Write-Host "Remote: https://github.com/${Username}/${RepoName}" -ForegroundColor Gray
        
        # CRITIQUE: Gérer le remote
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
        
        # CRITIQUE: Créer la branche main
        Write-Host "Branche..." -NoNewline
        git branch -M main
        Write-Host " ✓" -ForegroundColor Green
        
        # CORRECTION: Push avec l'approche en deux étapes
        Write-Host "Push vers GitHub..." -NoNewline
        # Désactiver les prompts
        $env:GIT_TERMINAL_PROMPT = "0"
        
        # Première tentative : push normal
        $pushOutput = git push -u origin main 2>&1
        
        # Si échec avec erreur d'histoires non liées, essayer avec --force
        if ($LASTEXITCODE -ne 0) {
            if ($pushOutput -match "failed to push some refs" -or $pushOutput -match "unrelated histories" -or $pushOutput -match "non-fast-forward") {
                Write-Host " (tentative avec --force)..." -NoNewline -ForegroundColor Yellow
                $pushOutput = git push -u origin main --force 2>&1
            }
        }
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host " ✓" -ForegroundColor Green
            Write-Host "✅ PUBLICATION RÉUSSIE !" -ForegroundColor Green
            Write-Host "🔗 https://github.com/$Username/$RepoName" -ForegroundColor Cyan
            return @{
                success = $true
                repo_url = "https://github.com/$Username/$RepoName"
                message = "Publication réussie"
            }
        } else {
            Write-Host " ✗" -ForegroundColor Red
            # Analyser l'erreur
            $errorMsg = "Erreur Git"
            if ($pushOutput -match "Authentication failed") {
                $errorMsg = "Token invalide - Regénérez-le sur GitHub"
            } elseif ($pushOutput -match "Repository not found") {
                $errorMsg = "Repository non trouvé - Créez-le d'abord sur GitHub"
            } elseif ($pushOutput -match "GH013" -or $pushOutput -match "secret") {
                $errorMsg = "GitHub a bloqué le push (secret détecté) - Autorisez-le sur GitHub"
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
# FONCTION POUR PUBLIER SUR GITHUB GISTS
# ============================================================================
function Publish-ToGitHubGists {
    param(
        [string]$Token,
        [string]$Username,
        [string]$Description
    )
    
    Write-Host "`n=== PUBLICATION SUR GITHUB GISTS ===" -ForegroundColor Cyan
    
    # Vérifier le token
    if ([string]::IsNullOrWhiteSpace($Token) -or $Token -notmatch "^ghp_[a-zA-Z0-9]{36,}$") {
        Write-Host "❌ Token invalide ou manquant" -ForegroundColor Red
        Write-Host "Générez un token sur: https://github.com/settings/tokens" -ForegroundColor Yellow
        return @{ success = $false; error = "Token GitHub invalide" }
    }
    
    # S'assurer d'être dans le bon répertoire
    $currentDir = Get-Location
    $projectDir = Resolve-Path $PROJECT_PATH -ErrorAction SilentlyContinue
    
    if ($currentDir.Path -ne $projectDir.Path) {
        Write-Host "ERREUR: Vous devez être dans le dossier du projet!" -ForegroundColor Red
        Write-Host "Exécutez: cd '$PROJECT_PATH'" -ForegroundColor Cyan
        return @{ success = $false; error = "Mauvais répertoire" }
    }
    
    # Scanner les fichiers du projet
    Write-Host "Scan des fichiers du projet..." -NoNewline
    $files = Get-ChildItem -Path . -File -Recurse | Where-Object {
        # Exclure certains fichiers/dossiers
        $excludePatterns = @(
            '\.git', 'node_modules', '\.vscode', '\.idea', '__pycache__',
            'project_config\.json', '\.env', '\.backup', '\.bak',
            'PROJECT_SHARE_', 'GISTS_INDEX_', 'GITHUB_PUBLISH_'
        )
        $exclude = $false
        foreach ($pattern in $excludePatterns) {
            if ($_.FullName -match $pattern) {
                $exclude = $true
                break
            }
        }
        return -not $exclude
    }
    
    $totalFiles = $files.Count
    Write-Host " ✓ ($totalFiles fichiers trouvés)" -ForegroundColor Green
    
    # Limiter la taille des fichiers (Gists a une limite de 10 fichiers)
    $maxFiles = 10
    $maxFileSize = 1MB
    
    $filteredFiles = @()
    $skippedFiles = @()
    
    foreach ($file in $files) {
        if ($filteredFiles.Count -ge $maxFiles) {
            $skippedFiles += $file.Name
            continue
        }
        
        if ($file.Length -gt $maxFileSize) {
            $skippedFiles += "$($file.Name) (trop grand: $([math]::Round($file.Length / 1MB, 2)) MB)"
            continue
        }
        
        $filteredFiles += $file
    }
    
    if ($filteredFiles.Count -eq 0) {
        Write-Host "❌ Aucun fichier à publier (tous filtrés)" -ForegroundColor Red
        return @{ success = $false; error = "Aucun fichier à publier" }
    }
    
    Write-Host "Fichiers sélectionnés pour Gists ($($filteredFiles.Count)/$totalFiles) :" -ForegroundColor Yellow
    $filteredFiles | ForEach-Object { Write-Host "  - $($_.Name)" -ForegroundColor Gray }
    
    if ($skippedFiles.Count -gt 0) {
        Write-Host "Fichiers ignorés :" -ForegroundColor Yellow
        $skippedFiles | ForEach-Object { Write-Host "  - $_" -ForegroundColor Gray }
    }
    
    # Préparer les fichiers pour l'API GitHub
    $filesObject = @{}
    
    foreach ($file in $filteredFiles) {
        try {
            $content = Get-Content -Path $file.FullName -Raw -Encoding UTF8 -ErrorAction Stop
            $filesObject[$file.Name] = @{ content = $content }
        } catch {
            Write-Host "⚠️  Impossible de lire $($file.Name): $_" -ForegroundColor Yellow
        }
    }
    
    # Préparer le corps de la requête
    $body = @{
        description = "$Description - $PROJECT_NAME"
        public = $false
        files = $filesObject
    } | ConvertTo-Json -Depth 10
    
    # Publier sur GitHub Gists
    Write-Host "Publication sur GitHub Gists..." -NoNewline
    
    try {
        $headers = @{
            "Authorization" = "token $Token"
            "Accept" = "application/vnd.github.v3+json"
            "Content-Type" = "application/json"
        }
        
        $response = Invoke-RestMethod -Uri "https://api.github.com/gists" `
            -Method Post `
            -Headers $headers `
            -Body $body `
            -TimeoutSec 30
        
        Write-Host " ✓" -ForegroundColor Green
        Write-Host "✅ GIST CRÉÉ AVEC SUCCÈS !" -ForegroundColor Green
        Write-Host "🔗 $($response.html_url)" -ForegroundColor Cyan
        Write-Host "ID: $($response.id)" -ForegroundColor Gray
        
        # Créer un fichier index local
        $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
        $indexFile = "GISTS_INDEX_$timestamp.txt"
        
        $indexContent = @"
==========================================
GITHUB GISTS PUBLICATION INDEX
==========================================
Date: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')
Projet: $PROJECT_NAME
Gist URL: $($response.html_url)
Gist ID: $($response.id)
Description: $Description

FICHIERS PUBLIÉS:
$($filteredFiles | ForEach-Object { "  - $($_.Name)" } | Out-String)

FICHIERS IGNORÉS:
$(if ($skippedFiles.Count -gt 0) { $skippedFiles | ForEach-Object { "  - $_" } | Out-String } else { "  (aucun)" })

==========================================
"@
        
        $indexContent | Out-File $indexFile -Encoding UTF8
        Write-Host "📄 Index créé: $indexFile" -ForegroundColor Green
        
        return @{
            success = $true
            gist_url = $response.html_url
            gist_id = $response.id
            files_published = $filteredFiles.Count
            index_file = $indexFile
        }
        
    } catch {
        Write-Host " ✗" -ForegroundColor Red
        $errorMsg = "Erreur API GitHub"
        if ($_.Exception.Response) {
            $stream = $_.Exception.Response.GetResponseStream()
            $reader = New-Object System.IO.StreamReader($stream)
            $responseBody = $reader.ReadToEnd()
            $reader.Close()
            
            try {
                $errorDetails = $responseBody | ConvertFrom-Json
                $errorMsg = "GitHub: $($errorDetails.message)"
            } catch {
                $errorMsg = "Erreur HTTP: $($_.Exception.Message)"
            }
        }
        
        Write-Host "❌ $errorMsg" -ForegroundColor Red
        return @{
            success = $false
            error = $errorMsg
        }
    }
}

# ============================================================================
# FONCTION POUR GÉNÉRER DES FICHIERS LOCAUX
# ============================================================================
function Generate-LocalFiles {
    param(
        [string]$OutputFormat = "ALL"
    )
    
    Write-Host "`n=== GÉNÉRATION DE FICHIERS LOCAUX ===" -ForegroundColor Cyan
    
    # S'assurer d'être dans le bon répertoire
    $currentDir = Get-Location
    $projectDir = Resolve-Path $PROJECT_PATH -ErrorAction SilentlyContinue
    
    if ($currentDir.Path -ne $projectDir.Path) {
        Write-Host "ERREUR: Vous devez être dans le dossier du projet!" -ForegroundColor Red
        Write-Host "Exécutez: cd '$PROJECT_PATH'" -ForegroundColor Cyan
        return @{ success = $false; error = "Mauvais répertoire" }
    }
    
    # Scanner les fichiers du projet
    Write-Host "Scan des fichiers du projet..." -NoNewline
    $files = Get-ChildItem -Path . -File -Recurse | Where-Object {
        # Exclure certains fichiers/dossiers
        $excludePatterns = @(
            '\.git', 'node_modules', '\.vscode', '\.idea', '__pycache__',
            'project_config\.json', '\.env', '\.backup', '\.bak',
            'PROJECT_SHARE_', 'GISTS_INDEX_', 'GITHUB_PUBLISH_'
        )
        $exclude = $false
        foreach ($pattern in $excludePatterns) {
            if ($_.FullName -match $pattern) {
                $exclude = $true
                break
            }
        }
        return -not $exclude
    }
    
    $totalFiles = $files.Count
    Write-Host " ✓ ($totalFiles fichiers trouvés)" -ForegroundColor Green
    
    # Créer un dossier de sortie
    $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $outputDir = "PROJECT_SHARE_$timestamp"
    New-Item -ItemType Directory -Path $outputDir -Force | Out-Null
    
    Write-Host "Dossier de sortie: $outputDir" -ForegroundColor Green
    
    # Générer différents formats selon le choix
    $generatedFiles = @()
    
    # 1. Archive ZIP complète
    if ($OutputFormat -eq "ALL" -or $OutputFormat -eq "ZIP") {
        Write-Host "Création de l'archive ZIP..." -NoNewline
        $zipFile = "$outputDir/$PROJECT_NAME.zip"
        try {
            Compress-Archive -Path $files.FullName -DestinationPath $zipFile -CompressionLevel Optimal
            $generatedFiles += "Archive ZIP: $zipFile"
            Write-Host " ✓" -ForegroundColor Green
        } catch {
            Write-Host " ✗ ($_)" -ForegroundColor Red
        }
    }
    
    # 2. Fichier d'index avec métadonnées
    if ($OutputFormat -eq "ALL" -or $OutputFormat -eq "INDEX") {
        Write-Host "Création du fichier d'index..." -NoNewline
        $indexFile = "$outputDir/PROJECT_INDEX.txt"
        
        $indexContent = @"
==========================================
PROJECT SHARE - INDEX
==========================================
Date: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')
Projet: $PROJECT_NAME
Chemin: $PROJECT_PATH
Fichiers total: $totalFiles

LISTE DES FICHIERS:
$($files | ForEach-Object { 
    $size = if ($_.Length -lt 1024) { "$($_.Length) B" }
            elseif ($_.Length -lt 1048576) { "$([math]::Round($_.Length/1KB, 2)) KB" }
            else { "$([math]::Round($_.Length/1MB, 2)) MB" }
    "  - $($_.Name) [$size]"
} | Out-String)

STATISTIQUES:
$($files | Group-Object Extension | Sort-Object Count -Descending | ForEach-Object {
    "  - $($_.Name): $($_.Count) fichiers"
} | Out-String)

TAILLE TOTALE: $([math]::Round(($files | Measure-Object Length -Sum).Sum / 1MB, 2)) MB
==========================================
"@
        
        $indexContent | Out-File $indexFile -Encoding UTF8
        $generatedFiles += "Fichier index: $indexFile"
        Write-Host " ✓" -ForegroundColor Green
    }
    
    # 3. Fichier README pour le partage
    if ($OutputFormat -eq "ALL" -or $OutputFormat -eq "README") {
        Write-Host "Création du fichier README..." -NoNewline
        $readmeFile = "$outputDir/README_SHARE.md"
        
        $readmeContent = @"
# $PROJECT_NAME - Partage de Projet

## 📋 Informations
- **Projet:** $PROJECT_NAME
- **Date de génération:** $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')
- **Nombre de fichiers:** $totalFiles
- **Format:** Généré automatiquement avec ShareSplit1M

## 📁 Structure du Projet

\`\`\`
$(Get-Location)
$(Get-ChildItem -Recurse -Depth 2 | Where-Object { $_.PSIsContainer } | ForEach-Object {
    $depth = ($_.FullName -split '[\\/]').Count - 1
    "|$("--" * $depth) $($_.Name)/"
})
\`\`\`

## 🔧 Fichiers Principaux

$(($files | Sort-Object Length -Descending | Select-Object -First 10) | ForEach-Object {
    $size = if ($_.Length -lt 1024) { "$($_.Length) B" }
            elseif ($_.Length -lt 1048576) { "$([math]::Round($_.Length/1KB, 2)) KB" }
            else { "$([math]::Round($_.Length/1MB, 2)) MB" }
    "- \`$($_.Name)\` - $size"
} | Out-String)

## 📊 Statistiques
\`\`\`text
$($files | Group-Object Extension | Sort-Object Count -Descending | ForEach-Object {
    "$($_.Name.PadRight(10)): $($_.Count.ToString().PadLeft(4)) fichiers"
} | Out-String)
\`\`\`

## ⚠️ Notes
- Ce dossier a été généré automatiquement
- Ne contient pas de fichiers sensibles (config, env, etc.)
- Pour restaurer, extraire l'archive ZIP

---
*Généré avec ❤️ par ShareSplit1M*
"@
        
        $readmeContent | Out-File $readmeFile -Encoding UTF8
        $generatedFiles += "Fichier README: $readmeFile"
        Write-Host " ✓" -ForegroundColor Green
    }
    
    # 4. Fichiers individuels copiés
    if ($OutputFormat -eq "ALL" -or $OutputFormat -eq "FILES") {
        Write-Host "Copie des fichiers..." -NoNewline
        $filesDir = "$outputDir/files"
        New-Item -ItemType Directory -Path $filesDir -Force | Out-Null
        
        $copied = 0
        foreach ($file in $files) {
            try {
                $relativePath = $file.FullName.Substring($currentDir.Path.Length + 1)
                $destPath = Join-Path $filesDir $relativePath
                $destDir = Split-Path $destPath -Parent
                
                if (-not (Test-Path $destDir)) {
                    New-Item -ItemType Directory -Path $destDir -Force | Out-Null
                }
                
                Copy-Item -Path $file.FullName -Destination $destPath -Force
                $copied++
            } catch {
                Write-Host "  ⚠️  Erreur copie $($file.Name): $_" -ForegroundColor Yellow
            }
        }
        
        $generatedFiles += "Fichiers copiés: $copied/$totalFiles dans $filesDir/"
        Write-Host " ✓ ($copied/$totalFiles fichiers)" -ForegroundColor Green
    }
    
    Write-Host "`n✅ GÉNÉRATION TERMINÉE !" -ForegroundColor Green
    Write-Host "Fichiers générés dans: $outputDir" -ForegroundColor Cyan
    $generatedFiles | ForEach-Object { Write-Host "  - $_" -ForegroundColor Gray }
    
    return @{
        success = $true
        output_dir = $outputDir
        generated_files = $generatedFiles
        total_files = $totalFiles
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
    Write-Host "3. Générer seulement les fichiers locaux" -ForegroundColor Yellow
    Write-Host "4. Quitter" -ForegroundColor Red
    Write-Host ""
    $choice = Read-Host "Votre choix [1-4]"
    
    switch ($choice) {
        '1' {
            Write-Host "`n=== PUBLICATION GITHUB REPOSITORY ===" -ForegroundColor Cyan
            
            # Vérifier le token
            if (-not $GITHUB_TOKEN -or $GITHUB_TOKEN -eq "*** REMOVED FOR SECURITY ***") {
                Write-Host "🔑 TOKEN GITHUB REQUIS" -ForegroundColor Yellow
                Write-Host "Collez votre token GitHub (commence par 'ghp_'):"
                $GITHUB_TOKEN = Read-Host
            }
            
            # Vérifier les autres informations
            if (-not $GITHUB_USERNAME) {
                $GITHUB_USERNAME = Read-Host "Nom d'utilisateur GitHub"
            }
            if (-not $GITHUB_REPO_NAME) {
                $GITHUB_REPO_NAME = Read-Host "Nom du repository"
            }
            
            # CRITIQUE: S'assurer d'être dans le bon répertoire
            Write-Host "`nVérification du répertoire..." -ForegroundColor Yellow
            if ((Get-Location).Path -ne (Resolve-Path $PROJECT_PATH).Path) {
                Write-Host "ATTENTION: Vous devez être dans: $PROJECT_PATH" -ForegroundColor Red
                Write-Host "Exécutez d'abord: cd '$PROJECT_PATH'" -ForegroundColor Cyan
                Read-Host "Appuyez sur Entrée pour continuer..."
                return
            }
            
            # Exécuter la publication
            $result = Publish-ToGitHubRepo-Working -Token $GITHUB_TOKEN `
                -Username $GITHUB_USERNAME `
                -RepoName $GITHUB_REPO_NAME `
                -Description $GITHUB_REPO_DESCRIPTION `
                -IsPrivate $GITHUB_REPO_PRIVATE
            
            if ($result.success) {
                Write-Host ""
                Write-Host "✅ Publication réussie sur GitHub!" -ForegroundColor Green
                Write-Host "Repository: $($result.repo_url)" -ForegroundColor Cyan
            } else {
                Write-Host ""
                Write-Host "❌ Échec de la publication" -ForegroundColor Red
                Write-Host "Erreur: $($result.error)" -ForegroundColor Red
                
                # Conseils de dépannage
                if ($result.error -match "Token") {
                    Write-Host "`n=== CONSEILS ===" -ForegroundColor Yellow
                    Write-Host "1. https://github.com/settings/tokens" -ForegroundColor Gray
                    Write-Host "2. 'Generate new token (classic)'" -ForegroundColor Gray
                    Write-Host "3. Permission: 'repo' (TOUTE la section)" -ForegroundColor Green
                    Write-Host "4. Copiez le token (ghp_...)" -ForegroundColor Gray
                }
            }
            Write-Host ""
            Read-Host "Appuyez sur Entrée pour continuer..."
        }
        '2' {
            Write-Host "`n=== GITHUB GISTS ===" -ForegroundColor Cyan
            
            # Vérifier le token
            if (-not $GITHUB_TOKEN -or $GITHUB_TOKEN -eq "*** REMOVED FOR SECURITY ***") {
                Write-Host "🔑 TOKEN GITHUB REQUIS" -ForegroundColor Yellow
                Write-Host "Collez votre token GitHub (commence par 'ghp_'):"
                $GITHUB_TOKEN = Read-Host
            }
            
            if (-not $GITHUB_USERNAME) {
                $GITHUB_USERNAME = Read-Host "Nom d'utilisateur GitHub"
            }
            
            # Vérifier le répertoire
            Write-Host "`nVérification du répertoire..." -ForegroundColor Yellow
            if ((Get-Location).Path -ne (Resolve-Path $PROJECT_PATH).Path) {
                Write-Host "ATTENTION: Vous devez être dans: $PROJECT_PATH" -ForegroundColor Red
                Write-Host "Exécutez d'abord: cd '$PROJECT_PATH'" -ForegroundColor Cyan
                Read-Host "Appuyez sur Entrée pour continuer..."
                return
            }
            
            $description = Read-Host "Description du Gist (optionnel) [$GITHUB_REPO_DESCRIPTION]"
            if (-not $description) { $description = $GITHUB_REPO_DESCRIPTION }
            
            $result = Publish-ToGitHubGists -Token $GITHUB_TOKEN `
                -Username $GITHUB_USERNAME `
                -Description $description
            
            if ($result.success) {
                Write-Host ""
                Write-Host "✅ Gist créé avec succès!" -ForegroundColor Green
                Write-Host "URL: $($result.gist_url)" -ForegroundColor Cyan
                Write-Host "Fichiers publiés: $($result.files_published)" -ForegroundColor Gray
                Write-Host "Index créé: $($result.index_file)" -ForegroundColor Gray
            } else {
                Write-Host ""
                Write-Host "❌ Échec de la publication sur Gists" -ForegroundColor Red
                Write-Host "Erreur: $($result.error)" -ForegroundColor Red
            }
            Write-Host ""
            Read-Host "Appuyez sur Entrée pour continuer..."
        }
        '3' {
            Write-Host "`n=== FICHIERS LOCAUX ===" -ForegroundColor Cyan
            
            # Sous-menu pour les formats
            Write-Host "`nSélectionnez le format de sortie:" -ForegroundColor Yellow
            Write-Host "1. Tous les formats (ZIP + Index + README + Fichiers)" -ForegroundColor Green
            Write-Host "2. Archive ZIP seulement" -ForegroundColor Yellow
            Write-Host "3. Fichier d'index seulement" -ForegroundColor Yellow
            Write-Host "4. Retour au menu principal" -ForegroundColor Gray
            Write-Host ""
            $formatChoice = Read-Host "Choix [1-4]"
            
            $formatMap = @{
                '1' = 'ALL'
                '2' = 'ZIP'
                '3' = 'INDEX'
            }
            
            if ($formatMap.ContainsKey($formatChoice)) {
                $result = Generate-LocalFiles -OutputFormat $formatMap[$formatChoice]
                
                if ($result.success) {
                    Write-Host ""
                    Write-Host "✅ Génération terminée avec succès!" -ForegroundColor Green
                    Write-Host "Dossier: $($result.output_dir)" -ForegroundColor Cyan
                    Write-Host "Fichiers générés:" -ForegroundColor Gray
                    $result.generated_files | ForEach-Object { Write-Host "  - $_" -ForegroundColor Gray }
                } else {
                    Write-Host "❌ Échec de la génération: $($result.error)" -ForegroundColor Red
                }
            }
            
            Write-Host ""
            Read-Host "Appuyez sur Entrée pour continuer..."
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
# POINT D'ENTRÉE
# ============================================================================
# Boucle principale
do {
    try {
        Show-MainMenu
    } catch {
        Write-Host "❌ Erreur: $_" -ForegroundColor Red
        Write-Host "Redémarrage dans 3 secondes..." -ForegroundColor Yellow
        Start-Sleep -Seconds 3
    }
} while ($true)
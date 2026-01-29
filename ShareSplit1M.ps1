# ============================================================================
# CONFIGURATION
# ============================================================================

# Lecture de la configuration
$configPath = "..\project_config.json"
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
    $PROJECT_NAME = "SmartContractDevPipeline"
    $PROJECT_PATH = "."
    $GITHUB_TOKEN = ""
    $GITHUB_USERNAME = ""
    $GITHUB_REPO_NAME = ""
    $GITHUB_REPO_PRIVATE = $false
    $GITHUB_REPO_DESCRIPTION = "Pipeline de développement de Smart Contracts"
}

# ============================================================================
# PARAMÈTRES CONFIGURABLES
# ============================================================================
$MAX_FILE_SIZE = 1024KB  # 1 Mo
$TARGET_FILE_SIZE = 650KB  # Pour ~95% de remplissage
$EXCLUDE_PATTERNS = @("node_modules", ".git", ".vscode", ".idea", "dist", "build", "coverage", "*.log", "*.tmp", "*.cache", "package-lock.json", "yarn.lock", "PROJECT_SHARE_*", "GISTS_INDEX*", "GITHUB_PUBLISH_*")
$SHARE_FILENAME_PREFIX = "PROJECT_SHARE"
$INDEX_FILENAME = "${SHARE_FILENAME_PREFIX}_INDEX.txt"
$SHOW_LINE_NUMBERS = $true

# ============================================================================
# FONCTIONS UTILITAIRES
# ============================================================================

# Fonction pour créer un Gist GitHub
function New-GitHubGist {
    param(
        [string]$Token,
        [string]$FileName,
        [string]$Content,
        [string]$Description
    )
    
    try {
        $Token = $Token.Trim()
        
        if ($Token -eq "ghp_********" -or $Token -eq "ghp_*" -or [string]::IsNullOrWhiteSpace($Token) -or $Token -match "^\*+$") {
            return @{
                success = $false
                error = "Token invalide ou non configuré"
            }
        }
        
        $body = @{
            description = $Description
            public = $false
            files = @{
                $FileName = @{content = $Content}
            }
        }
        
        $jsonBody = $body | ConvertTo-Json -Depth 10
        
        $headers = @{
            Authorization = "token $Token"
            Accept = "application/vnd.github.v3+json"
            "User-Agent" = "PowerShell-Gist-Uploader"
        }
        
        $response = Invoke-RestMethod -Uri "https://api.github.com/gists" `
                                     -Method POST `
                                     -Headers $headers `
                                     -Body $jsonBody `
                                     -ContentType "application/json" `
                                     -ErrorAction Stop
        
        return @{
            success = $true
            url = $response.html_url
            id = $response.id
        }
    } catch {
        $errorMsg = $_.Exception.Message
        
        if ($errorMsg -like "*401*") {
            $errorMsg = "Token GitHub invalide ou expiré (401). Regénérez un token avec permission 'gist'."
        } elseif ($errorMsg -like "*403*") {
            $errorMsg = "Accès refusé (403). Vérifiez les permissions du token."
        }
        
        return @{
            success = $false
            error = $errorMsg
        }
    }
}

# Fonction pour tester le token GitHub
function Test-GitHubToken {
    param([string]$Token)
    
    try {
        $headers = @{
            Authorization = "token $Token"
            Accept = "application/vnd.github.v3+json"
            "User-Agent" = "PowerShell-Test"
        }
        
        $response = Invoke-WebRequest -Uri "https://api.github.com/user" -Headers $headers -ErrorAction Stop
        $user = $response.Content | ConvertFrom-Json
        
        return @{
            valid = $true
            username = $user.login
        }
    } catch {
        $errorMsg = $_.Exception.Message
        if ($errorMsg -like "*401*") {
            $errorMsg = "Token invalide ou expiré (401 Unauthorized)"
        }
        
        return @{
            valid = $false
            error = $errorMsg
        }
    }
}

# Fonction pour publier sur GitHub Repository - SANS INTERACTION
# Fonction ULTIME CORRIGÉE pour publier sur GitHub Repository
function Publish-ToGitHubRepo {
    param(
        [string]$Token,
        [string]$Username,
        [string]$RepoName,
        [string]$Description,
        [bool]$IsPrivate
    )
    
    Write-Host "`n=== PUBLICATION SUR GITHUB REPOSITORY ===" -ForegroundColor Cyan
    
    # Vérifier et nettoyer le token
    $Token = $Token.Trim()
    
    # Log pour débogage
    Write-Host "Token (premiers 10 chars): $($Token.Substring(0, [math]::Min(10, $Token.Length)))..." -ForegroundColor Gray
    Write-Host "Longueur token: $($Token.Length)" -ForegroundColor Gray
    
    if ($Token -match "^\*+$" -or $Token -eq "ghp_********" -or [string]::IsNullOrWhiteSpace($Token)) {
        Write-Host "❌ Token vide ou masqué" -ForegroundColor Red
        return @{ success = $false; error = "Token GitHub vide ou masqué" }
    }
    
    if (-not $Token.StartsWith("ghp_")) {
        Write-Host "❌ Format de token invalide (doit commencer par 'ghp_')" -ForegroundColor Red
        return @{ success = $false; error = "Format de token invalide" }
    }
    
    # Sauvegarder le répertoire original
    $originalLocation = Get-Location
    
    try {
        # Vérifier si Git est installé
        try {
            git --version | Out-Null
            Write-Host "✓ Git installé" -ForegroundColor Gray
        } catch {
            Write-Host "✗ Git non trouvé sur le système" -ForegroundColor Red
            Write-Host "Installation requise: https://git-scm.com/downloads" -ForegroundColor Yellow
            return @{ success = $false; error = "Git non installé" }
        }
        
        # Vérifier si le dossier existe
        if (-not (Test-Path $PROJECT_PATH)) {
            Write-Host "Création du dossier: $PROJECT_PATH" -ForegroundColor Yellow
            New-Item -ItemType Directory -Path $PROJECT_PATH -Force | Out-Null
        }
        
        # Se déplacer dans le dossier du projet
        Write-Host "Changement vers: $PROJECT_PATH" -ForegroundColor Yellow
        Set-Location -Path $PROJECT_PATH -ErrorAction Stop
        Write-Host "Répertoire actuel: $(Get-Location)" -ForegroundColor Gray
        
        # Nettoyer la configuration Git
        Write-Host "Configuration Git..." -NoNewline
        
        # 1. Essayer avec x-access-token (recommandé par GitHub)
        $remoteUrl1 = "https://x-access-token:${Token}@github.com/${Username}/${RepoName}.git"
        
        # 2. Essayer avec username:token (méthode classique)
        $encodedToken = [System.Web.HttpUtility]::UrlEncode($Token)
        $remoteUrl2 = "https://${Username}:${encodedToken}@github.com/${Username}/${RepoName}.git"
        
        Write-Host " URL: https://github.com/${Username}/${RepoName}.git" -ForegroundColor Gray
        Write-Host " ✓" -ForegroundColor Green
        
        # Tester d'abord si on peut se connecter au repository
        Write-Host "Test de connexion au repository..." -NoNewline
        
        # Essayer la première méthode
        $testOutput = git ls-remote $remoteUrl1 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Host " ✓ (x-access-token)" -ForegroundColor Green
            $remoteUrl = $remoteUrl1
        } else {
            # Essayer la deuxième méthode
            $testOutput = git ls-remote $remoteUrl2 2>&1
            if ($LASTEXITCODE -eq 0) {
                Write-Host " ✓ (username:token)" -ForegroundColor Green
                $remoteUrl = $remoteUrl2
            } else {
                Write-Host " ✗" -ForegroundColor Red
                Write-Host "Impossible de se connecter au repository" -ForegroundColor Red
                Write-Host "Message: $testOutput" -ForegroundColor Red
                
                Set-Location -Path $originalLocation
                return @{
                    success = $false
                    error = "Connexion impossible au repository. Vérifiez:"
                    details = @(
                        "1. Le token est-il valide?",
                        "2. Le repository '$RepoName' existe-t-il?",
                        "3. Le token a-t-il la permission 'repo'?",
                        "4. Le token est-il expiré?",
                        "Erreur Git: $testOutput"
                    )
                }
            }
        }
        
        # Initialiser Git si nécessaire
        if (-not (Test-Path ".git")) {
            Write-Host "Initialisation Git..." -NoNewline
            git init | Out-Null
            Write-Host " ✓" -ForegroundColor Green
        } else {
            Write-Host "✓ Repository Git déjà initialisé" -ForegroundColor Gray
        }
        
        # Configurer Git
        git config user.name "$Username"
        git config user.email "$Username@users.noreply.github.com"
        
        # Ajouter/supprimer remote
        git remote remove origin 2>$null
        git remote add origin $remoteUrl
        
        # Ajouter les fichiers
        Write-Host "Ajout des fichiers..." -NoNewline
        git add . 2>&1 | Out-Null
        Write-Host " ✓" -ForegroundColor Green
        
        # Commit
        Write-Host "Commit..." -NoNewline
        $commitMsg = "🚀 Publication: $PROJECT_NAME - $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
        git commit -m $commitMsg --quiet 2>&1 | Out-Null
        Write-Host " ✓" -ForegroundColor Green
        
        # Créer la branche main
        Write-Host "Configuration branche..." -NoNewline
        git branch -M main 2>&1 | Out-Null
        Write-Host " ✓" -ForegroundColor Green
        
        # Push avec gestion d'erreur améliorée
        Write-Host "Push vers GitHub..." -NoNewline
        
        # Désactiver les prompts
        $env:GIT_TERMINAL_PROMPT = "0"
        
        # Exécuter le push
        $pushOutput = git push -u origin main --force 2>&1
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host " ✓" -ForegroundColor Green
            Write-Host "✅ PUBLICATION RÉUSSIE !" -ForegroundColor Green
            Write-Host "Repository: https://github.com/$Username/$RepoName" -ForegroundColor Cyan
            
            # Afficher le dernier commit
            $lastCommit = git log --oneline -1 2>$null
            if ($lastCommit) {
                Write-Host "Commit: $lastCommit" -ForegroundColor Gray
            }
            
            Set-Location -Path $originalLocation
            return @{
                success = $true
                repo_url = "https://github.com/$Username/$RepoName"
                commit = $lastCommit
                message = "Publication réussie"
            }
        } else {
            Write-Host " ✗" -ForegroundColor Red
            
            # Analyser l'erreur
            $errorDetails = $pushOutput -join " "
            
            # CORRECTION: Ne pas appeler .Trim() sur un tableau ou ErrorRecord
            if ($pushOutput -is [array]) {
                $errorMessage = $pushOutput -join " "
            } elseif ($pushOutput -is [string]) {
                $errorMessage = $pushOutput.Trim()
            } else {
                $errorMessage = $pushOutput.ToString()
            }
            
            Write-Host "❌ Erreur lors du push" -ForegroundColor Red
            Write-Host "Détails: $errorMessage" -ForegroundColor Red
            
            Set-Location -Path $originalLocation
            return @{
                success = $false
                error = "Échec du push Git"
                details = $errorMessage
                git_output = $pushOutput
            }
        }
        
    } catch {
        Write-Host " ✗" -ForegroundColor Red
        
        # CORRECTION: Gérer l'erreur proprement sans .Trim()
        $errorMsg = $_.Exception.Message
        Write-Host "❌ Erreur inattendue: $errorMsg" -ForegroundColor Red
        
        # Essayer de revenir au répertoire original
        try {
            Set-Location -Path $originalLocation -ErrorAction SilentlyContinue
        } catch {
            # Ignorer
        }
        
        return @{
            success = $false
            error = $errorMsg
            exception_type = $_.Exception.GetType().Name
        }
    }
}

# Fonction pour générer des fichiers locaux
function Generate-LocalFiles {
    Write-Host "`n=== GÉNÉRATION DE FICHIERS LOCAUX ===" -ForegroundColor Cyan
    
    # Analyser tous les fichiers du projet
    Write-Host "Analyse des fichiers dans: $PROJECT_PATH" -ForegroundColor Yellow
    
    $allFiles = Get-ChildItem -Path $PROJECT_PATH -Recurse -File | Where-Object {
        $relativePath = $_.FullName.Replace($PROJECT_PATH, "").TrimStart('\')
        -not (Should-ExcludePath -Path $relativePath)
    }
    
    Write-Host "Nombre de fichiers trouvés: $($allFiles.Count)" -ForegroundColor Green
    
    if ($allFiles.Count -eq 0) {
        Write-Host "Aucun fichier à traiter." -ForegroundColor Yellow
        return @{ success = $false; error = "Aucun fichier trouvé" }
    }
    
    # Créer un fichier d'index
    $indexContent = @"
INDEX DES FICHIERS DU PROJET: $PROJECT_NAME
Date de génération: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')
Chemin du projet: $PROJECT_PATH

LISTE DES FICHIERS:
"@
    
    $fileIndex = 1
    $processedFiles = @()
    
    foreach ($file in $allFiles) {
        $relativePath = $file.FullName.Replace($PROJECT_PATH, "").TrimStart('\')
        $fileSizeKB = [math]::Round($file.Length / 1KB, 2)
        
        $indexContent += "`n$fileIndex. $relativePath (${fileSizeKB} KB)"
        $fileIndex++
        
        $processedFiles += @{
            FullPath = $file.FullName
            RelativePath = $relativePath
            Size = $file.Length
            ProcessedSize = $file.Length
        }
    }
    
    # Écrire le fichier d'index
    $indexContent | Out-File -FilePath $INDEX_FILENAME -Encoding UTF8
    Write-Host "✅ Fichier d'index créé: $INDEX_FILENAME" -ForegroundColor Green
    
    # Générer des fichiers partagés si nécessaire
    $totalSize = ($processedFiles | Measure-Object -Property Size -Sum).Sum
    $totalSizeMB = [math]::Round($totalSize / 1MB, 2)
    
    Write-Host "Taille totale des fichiers: ${totalSizeMB} MB" -ForegroundColor Yellow
    
    if ($totalSize -gt $MAX_FILE_SIZE) {
        Write-Host "Le projet est trop volumineux, génération de fichiers partagés..." -ForegroundColor Cyan
        
        $groups = Optimize-FileGrouping -Files $processedFiles -MaxSize $MAX_FILE_SIZE -TargetSize $TARGET_FILE_SIZE
        
        $shareFiles = @()
        $groupIndex = 1
        
        foreach ($group in $groups) {
            $shareFileName = "${SHARE_FILENAME_PREFIX}_PART${groupIndex}.txt"
            $shareContent = @"
FICHIER PARTAGÉ: $shareFileName
Projet: $PROJECT_NAME
Partie: $groupIndex/$($groups.Count)
Date: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')
Taille totale: $([math]::Round($group.TotalSize/1KB, 2)) KB

"@
            
            foreach ($file in $group.Files) {
                $fileContent = Get-Content -Path $file.FullPath -Raw -ErrorAction SilentlyContinue
                if ($fileContent) {
                    $shareContent += "=" * 60 + "`n"
                    $shareContent += "FICHIER: $($file.RelativePath)`n"
                    $shareContent += "TAILLE: $([math]::Round($file.Size/1KB, 2)) KB`n"
                    $shareContent += "=" * 60 + "`n`n"
                    $shareContent += Add-LineNumbers -Content $fileContent
                    $shareContent += "`n`n"
                }
            }
            
            $shareContent | Out-File -FilePath $shareFileName -Encoding UTF8
            $shareFiles += $shareFileName
            Write-Host "  Fichier créé: $shareFileName ($([math]::Round($group.TotalSize/1KB, 2)) KB)" -ForegroundColor Gray
            $groupIndex++
        }
        
        Write-Host "✅ $($groups.Count) fichier(s) partagé(s) créé(s)" -ForegroundColor Green
        
        return @{
            success = $true
            index_file = $INDEX_FILENAME
            share_files = $shareFiles
            total_size = $totalSize
            file_count = $allFiles.Count
        }
    } else {
        Write-Host "Le projet tient dans un seul fichier." -ForegroundColor Green
        return @{
            success = $true
            index_file = $INDEX_FILENAME
            total_size = $totalSize
            file_count = $allFiles.Count
        }
    }
}

# Fonction pour partager sur GitHub Gists
function Share-ToGitHubGists {
    Write-Host "`n=== PARTAGE SUR GITHUB GISTS ===" -ForegroundColor Cyan
    
    # Vérifier le token
    if (-not $GITHUB_TOKEN -or $GITHUB_TOKEN -match "^\*+$" -or $GITHUB_TOKEN -eq "ghp_********") {
        Write-Host "❌ Token GitHub non configuré" -ForegroundColor Red
        return @{ success = $false; error = "Token GitHub manquant" }
    }
    
    # Générer d'abord les fichiers locaux
    $localResult = Generate-LocalFiles
    if (-not $localResult.success) {
        return $localResult
    }
    
    $gists = @()
    
    # Partager le fichier d'index
    if (Test-Path $INDEX_FILENAME) {
        $indexContent = Get-Content -Path $INDEX_FILENAME -Raw
        $indexGist = New-GitHubGist -Token $GITHUB_TOKEN `
                                   -FileName "$($PROJECT_NAME)_INDEX.txt" `
                                   -Content $indexContent `
                                   -Description "Index du projet $PROJECT_NAME"
        
        if ($indexGist.success) {
            Write-Host "✅ Index partagé: $($indexGist.url)" -ForegroundColor Green
            $gists += @{
                type = "index"
                url = $indexGist.url
            }
        } else {
            Write-Host "❌ Erreur partage index: $($indexGist.error)" -ForegroundColor Red
        }
    }
    
    # Partager les fichiers de partage
    if ($localResult.share_files) {
        $fileIndexCounter = 1
        foreach ($shareFile in $localResult.share_files) {
            if (Test-Path $shareFile) {
                $fileContent = Get-Content -Path $shareFile -Raw
                $gistResult = New-GitHubGist -Token $GITHUB_TOKEN `
                                            -FileName "$($PROJECT_NAME)_PART${fileIndexCounter}.txt" `
                                            -Content $fileContent `
                                            -Description "Partie $fileIndexCounter du projet $PROJECT_NAME"
                
                if ($gistResult.success) {
                    Write-Host "✅ Partie $fileIndexCounter partagée: $($gistResult.url)" -ForegroundColor Green
                    $gists += @{
                        type = "part"
                        part = $fileIndexCounter
                        url = $gistResult.url
                    }
                } else {
                    Write-Host "❌ Erreur partie $fileIndexCounter : $($gistResult.error)" -ForegroundColor Red
                }
                $fileIndexCounter++
            }
        }
    }
    
    # Créer un index des Gists
    if ($gists.Count -gt 0) {
        $gistsIndex = @"
INDEX DES GISTS GITHUB - $PROJECT_NAME
Date: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')

"@
        
        foreach ($gist in $gists) {
            if ($gist.type -eq "index") {
                $gistsIndex += "📄 INDEX: $($gist.url)`n"
            } else {
                $gistsIndex += "📦 PARTIE $($gist.part): $($gist.url)`n"
            }
        }
        
        $timestamp = Get-Date -Format 'yyyyMMdd_HHmmss'
        $gistsIndexFile = "GISTS_INDEX_${timestamp}.txt"
        $gistsIndex | Out-File -FilePath $gistsIndexFile -Encoding UTF8
        Write-Host "✅ Index des Gists créé localement: $gistsIndexFile" -ForegroundColor Green
        
        return @{
            success = $true
            gists = $gists
            gists_count = $gists.Count
            index_file = $gistsIndexFile
        }
    } else {
        return @{
            success = $false
            error = "Aucun Gist n'a pu être créé"
        }
    }
}

# Fonction pour l'optimisation
function Optimize-FileGrouping {
    param(
        [array]$Files,
        [int]$MaxSize,
        [int]$TargetSize
    )
    
    $sortedFiles = $Files | Sort-Object @{Expression = {$_.ProcessedSize}; Descending = $true}
    
    $groups = @()
    $currentGroup = @()
    $currentSize = 0
    
    foreach ($file in $sortedFiles) {
        $fileSize = $file.ProcessedSize
        
        if ($fileSize -gt $MaxSize) {
            Write-Host "  AVERTISSEMENT: $($file.RelativePath) est trop gros ($([math]::Round($fileSize/1KB, 2)) Ko) - sera dans son propre fichier" -ForegroundColor Yellow
            if ($currentGroup.Count -gt 0) {
                $groups += @{
                    Files = $currentGroup
                    TotalSize = $currentSize
                }
                $currentGroup = @()
                $currentSize = 0
            }
            $groups += @{
                Files = @($file)
                TotalSize = $fileSize
            }
            continue
        }
        
        if (($currentSize + $fileSize) -gt $TargetSize -and $currentGroup.Count -gt 0) {
            $groups += @{
                Files = $currentGroup
                TotalSize = $currentSize
            }
            $currentGroup = @()
            $currentSize = 0
        }
        
        $currentGroup += $file
        $currentSize += $fileSize
    }
    
    if ($currentGroup.Count -gt 0) {
        $groups += @{
            Files = $currentGroup
            TotalSize = $currentSize
        }
    }
    
    return $groups
}

# Fonction pour ajouter des numéros de ligne
function Add-LineNumbers {
    param([string]$Content)
    
    if (-not $SHOW_LINE_NUMBERS) { return $Content }
    
    $lines = $Content -split "`n"
    $result = @()
    $i = 1
    
    foreach ($line in $lines) {
        $result += "{0:D5}: {1}" -f $i, $line
        $i++
    }
    
    return $result -join "`n"
}

# Fonction pour vérifier les exclusions
function Should-ExcludePath {
    param([string]$Path)
    
    if ($Path -like "*${SHARE_FILENAME_PREFIX}_*" -or $Path -like "*GISTS_INDEX*" -or $Path -like "*GITHUB_PUBLISH_*") {
        return $true
    }
    
    foreach ($pattern in $EXCLUDE_PATTERNS) {
        if ($pattern -match "^\*\.") {
            $ext = $pattern.Substring(1)
            if ($Path -like "*$ext") { return $true }
        }
        elseif ($Path -like "*$pattern*") {
            return $true
        }
    }
    return $false
}

# ============================================================================
# SCRIPT PRINCIPAL
# ============================================================================

Clear-Host
Write-Host ""
Write-Host ("=" * 60) -ForegroundColor Cyan
Write-Host "SHARE SPLIT 1M - $PROJECT_NAME" -ForegroundColor Cyan
Write-Host ("=" * 60) -ForegroundColor Cyan
Write-Host ""

# Vérifier le dossier
if (-not (Test-Path $PROJECT_PATH)) {
    Write-Host "ERREUR: Chemin introuvable: $PROJECT_PATH" -ForegroundColor Red
    exit 1
}

Write-Host "Chemin: $PROJECT_PATH" -ForegroundColor Green
Write-Host ""

# ============================================================================
# CONNEXION AUTOMATIQUE À GITHUB (NON INTERACTIVE)
# ============================================================================

$autoConnectSuccess = $false
$showMenu = $true

# Correction du pattern regex pour éviter l'erreur
$validTokenPattern = "ghp_[a-zA-Z0-9]{36,}"

# Vérifier si la configuration GitHub est complète
if ($GITHUB_TOKEN -and $GITHUB_TOKEN -match $validTokenPattern -and 
    $GITHUB_USERNAME -and $GITHUB_REPO_NAME -and
    $GITHUB_TOKEN -notmatch "^\*+$" -and $GITHUB_TOKEN -ne "ghp_********") {
    
    Write-Host "=== CONNEXION AUTOMATIQUE GITHUB ===" -ForegroundColor Cyan
    Write-Host "Configuration GitHub détectée" -ForegroundColor Green
    Write-Host "Utilisateur: $GITHUB_USERNAME" -ForegroundColor Gray
    Write-Host "Repository: $GITHUB_REPO_NAME" -ForegroundColor Gray
    Write-Host ""
    
    # Tester le token d'abord
    Write-Host "Vérification du token GitHub..." -NoNewline
    $tokenTest = Test-GitHubToken -Token $GITHUB_TOKEN
    
    if ($tokenTest.valid) {
        Write-Host " ✓" -ForegroundColor Green
        Write-Host "Token valide pour: $($tokenTest.username)" -ForegroundColor Green
        
        # Vérifier si le repository existe
        Write-Host "Vérification du repository..." -NoNewline
        $headers = @{
            Authorization = "token $GITHUB_TOKEN"
            Accept = "application/vnd.github.v3+json"
        }
        
        try {
            $repoCheck = Invoke-RestMethod -Uri "https://api.github.com/repos/$GITHUB_USERNAME/$GITHUB_REPO_NAME" `
                                          -Headers $headers `
                                          -ErrorAction Stop
            Write-Host " ✓ (existe déjà)" -ForegroundColor Green
            $repoExists = $true
        } catch {
            # Le repository n'existe pas, le créer automatiquement
            Write-Host " ✗ (n'existe pas)" -ForegroundColor Yellow
            Write-Host "Création automatique du repository..." -NoNewline
            
            $body = @{
                name = $GITHUB_REPO_NAME
                description = $GITHUB_REPO_DESCRIPTION
                private = $GITHUB_REPO_PRIVATE
            } | ConvertTo-Json
            
            try {
                $newRepo = Invoke-RestMethod -Uri "https://api.github.com/user/repos" `
                                             -Method POST `
                                             -Headers $headers `
                                             -Body $body `
                                             -ContentType "application/json"
                Write-Host " ✓" -ForegroundColor Green
                $repoExists = $true
            } catch {
                Write-Host " ✗" -ForegroundColor Red
                Write-Host "Erreur création: $_" -ForegroundColor Red
                $repoExists = $false
            }
        }
        
        if ($repoExists) {
            # Publier sur GitHub automatiquement
            Write-Host "Publication automatique sur GitHub..." -ForegroundColor Cyan
            
            $result = Publish-ToGitHubRepo -Token $GITHUB_TOKEN `
                                          -Username $GITHUB_USERNAME `
                                          -RepoName $GITHUB_REPO_NAME `
                                          -Description $GITHUB_REPO_DESCRIPTION `
                                          -IsPrivate $GITHUB_REPO_PRIVATE
            
            if ($result.success) {
                $autoConnectSuccess = $true
                Write-Host ""
                Write-Host "✅ CONNEXION AUTOMATIQUE RÉUSSIE !" -ForegroundColor Green
                Write-Host "Repository: $($result.repo_url)" -ForegroundColor Cyan
                Write-Host "Commit: $($result.commit)" -ForegroundColor Gray
                Write-Host ""
                
                # Demander si on veut voir le menu
                $showMenuAnswer = Read-Host "Voulez-vous voir le menu principal ? (O/N)"
                if ($showMenuAnswer -eq 'O' -or $showMenuAnswer -eq 'o') {
                    $showMenu = $true
                } else {
                    Write-Host "Au revoir!" -ForegroundColor Green
                    exit 0
                }
            } else {
                Write-Host ""
                Write-Host "❌ Connexion automatique échouée" -ForegroundColor Red
                if ($result.error) {
                    Write-Host "Erreur: $($result.error)" -ForegroundColor Red
                }
                Write-Host ""
                $showMenu = $true
            }
        } else {
            Write-Host "❌ Impossible de créer le repository" -ForegroundColor Red
            $showMenu = $true
        }
    } else {
        Write-Host " ✗" -ForegroundColor Red
        Write-Host "❌ Token GitHub invalide" -ForegroundColor Red
        Write-Host "Erreur: $($tokenTest.error)" -ForegroundColor Red
        Write-Host ""
        $showMenu = $true
    }
} else {
    Write-Host "⚠ Configuration GitHub incomplète ou token masqué" -ForegroundColor Yellow
    Write-Host "   Impossible de se connecter automatiquement à GitHub" -ForegroundColor Gray
    Write-Host ""
    $showMenu = $true
}

# ============================================================================
# MENU PRINCIPAL
# ============================================================================

if ($showMenu) {
    do {
        Clear-Host
        Write-Host ""
        Write-Host ("=" * 60) -ForegroundColor Cyan
        Write-Host "SHARE SPLIT 1M - $PROJECT_NAME" -ForegroundColor Cyan
        Write-Host ("=" * 60) -ForegroundColor Cyan
        Write-Host ""
        
        if ($autoConnectSuccess) {
            Write-Host "✅ Publication GitHub déjà effectuée" -ForegroundColor Green
            Write-Host ""
        }
        
        Write-Host "=== MENU PRINCIPAL ===" -ForegroundColor Cyan
        Write-Host "1. Publier sur GitHub Repository" -ForegroundColor Yellow
        Write-Host "2. Partager sur GitHub Gists" -ForegroundColor Yellow
        Write-Host "3. Générer seulement les fichiers locaux" -ForegroundColor Yellow
        Write-Host "4. Quitter" -ForegroundColor Red
        Write-Host ""
        
        $choice = Read-Host "Votre choix [1-4]"
        
        switch ($choice) {
            '1' {
                # OPTION 1: GitHub Repository
                Write-Host "`n=== PUBLICATION GITHUB REPOSITORY ===" -ForegroundColor Cyan
                
                # Demander les informations manquantes
                if (-not $GITHUB_TOKEN -or $GITHUB_TOKEN -match "^\*+$" -or $GITHUB_TOKEN -eq "ghp_********") {
                    Write-Host ""
                    Write-Host "🔑 TOKEN GITHUB REQUIS" -ForegroundColor Cyan
                    Write-Host "Pour créer un token:" -ForegroundColor Gray
                    Write-Host "1. https://github.com/settings/tokens" -ForegroundColor Gray
                    Write-Host "2. 'Generate new token (classic)'" -ForegroundColor Gray
                    Write-Host "3. Donnez un nom" -ForegroundColor Gray
                    Write-Host "4. Sélectionnez 'repo' (TOUTE la section)" -ForegroundColor Green
                    Write-Host "5. 'Generate token'" -ForegroundColor Gray
                    Write-Host "6. Copiez le token (commence par 'ghp_')" -ForegroundColor Gray
                    Write-Host ""
                    
                    $GITHUB_TOKEN = Read-Host "Collez votre token GitHub"
                }
                
                if (-not $GITHUB_USERNAME) {
                    $GITHUB_USERNAME = Read-Host "Nom d'utilisateur GitHub"
                }
                
                if (-not $GITHUB_REPO_NAME) {
                    $GITHUB_REPO_NAME = Read-Host "Nom du repository"
                }
                
                # Publier sur GitHub
                $result = Publish-ToGitHubRepo -Token $GITHUB_TOKEN `
                                              -Username $GITHUB_USERNAME `
                                              -RepoName $GITHUB_REPO_NAME `
                                              -Description $GITHUB_REPO_DESCRIPTION `
                                              -IsPrivate $GITHUB_REPO_PRIVATE
                
                if ($result.success) {
                    Write-Host ""
                    Write-Host "✅ Publication réussie sur GitHub!" -ForegroundColor Green
                    Write-Host "Repository: $($result.repo_url)" -ForegroundColor Cyan
                    Write-Host "Commit: $($result.commit)" -ForegroundColor Gray
                    $autoConnectSuccess = $true
                } else {
                    Write-Host ""
                    Write-Host "❌ Échec de la publication" -ForegroundColor Red
                    Write-Host "Erreur: $($result.error)" -ForegroundColor Red
                }
                
                Write-Host ""
                Write-Host "Appuyez sur Entrée pour continuer..."
                Read-Host
            }
            
            '2' {
                # OPTION 2: GitHub Gists
                $result = Share-ToGitHubGists
                if ($result.success) {
                    Write-Host ""
                    Write-Host "✅ Partage Gists réussi!" -ForegroundColor Green
                    Write-Host "Nombre de Gists créés: $($result.gists_count)" -ForegroundColor Cyan
                    Write-Host "Index local créé: $($result.index_file)" -ForegroundColor Gray
                } else {
                    Write-Host ""
                    Write-Host "❌ Échec du partage Gists" -ForegroundColor Red
                    Write-Host "Erreur: $($result.error)" -ForegroundColor Red
                }
                
                Write-Host ""
                Write-Host "Appuyez sur Entrée pour continuer..."
                Read-Host
            }
            
            '3' {
                # OPTION 3: Fichiers locaux seulement
                $result = Generate-LocalFiles
                if ($result.success) {
                    Write-Host ""
                    Write-Host "✅ Génération locale réussie!" -ForegroundColor Green
                    Write-Host "Fichier d'index: $($result.index_file)" -ForegroundColor Cyan
                    if ($result.share_files) {
                        Write-Host "Fichiers partagés: $($result.share_files.Count)" -ForegroundColor Cyan
                        foreach ($file in $result.share_files) {
                            Write-Host "  - $file" -ForegroundColor Gray
                        }
                    }
                    Write-Host "Nombre total de fichiers: $($result.file_count)" -ForegroundColor Yellow
                } else {
                    Write-Host ""
                    Write-Host "❌ Échec de la génération locale" -ForegroundColor Red
                    Write-Host "Erreur: $($result.error)" -ForegroundColor Red
                }
                
                Write-Host ""
                Write-Host "Appuyez sur Entrée pour continuer..."
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
    } while ($true)
}
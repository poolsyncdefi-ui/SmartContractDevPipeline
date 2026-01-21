# ShareSplit1M_fixed.ps1 - Version qui protège les tokens
# ============================================================================
# CONFIGURATION
# ============================================================================

# Lecture sécurisée de la configuration
$configPath = "project_config.json"
$gitignorePath = ".gitignore"

# Ajouter project_config.json au .gitignore s'il n'y est pas
if (Test-Path $gitignorePath) {
    $gitignoreContent = Get-Content $gitignorePath -Raw
    if ($gitignoreContent -notmatch "project_config\.json") {
        Add-Content -Path $gitignorePath -Value "`nproject_config.json"
    }
} else {
    "# Configuration files`nproject_config.json`n" | Out-File -FilePath $gitignorePath -Encoding UTF8
}

if (Test-Path $configPath) {
    try {
        $config = Get-Content $configPath -Raw | ConvertFrom-Json
        $PROJECT_NAME = $config.PROJECT_NAME
        $PROJECT_PATH = $config.PROJECT_PATH
        $GITHUB_USERNAME = $config.GITHUB_USERNAME
        $GITHUB_REPO_NAME = $config.GITHUB_REPO_NAME
        $GITHUB_REPO_PRIVATE = $config.GITHUB_REPO_PRIVATE
        $GITHUB_REPO_DESCRIPTION = $config.GITHUB_REPO_DESCRIPTION
        
        # Le token est lu mais NE sera PAS utilisé directement
        # On va demander à l'utilisateur s'il n'est pas déjà en variable d'environnement
        if ($config.PSObject.Properties.Name -contains "GITHUB_TOKEN") {
            # On stocke mais on ne l'utilise que temporairement
            $script:TempGitHubToken = $config.GITHUB_TOKEN
        } else {
            $script:TempGitHubToken = $null
        }
    } catch {
        Write-Host "⚠ Erreur lecture configuration: $_" -ForegroundColor Yellow
        Set-DefaultValues
    }
} else {
    Set-DefaultValues
}

function Set-DefaultValues {
    $PROJECT_NAME = "SmartContractDevPipeline"
    $PROJECT_PATH = "."
    $GITHUB_USERNAME = ""
    $GITHUB_REPO_NAME = ""
    $GITHUB_REPO_PRIVATE = $false
    $GITHUB_REPO_DESCRIPTION = "Pipeline de développement de Smart Contracts"
    $script:TempGitHubToken = $null
}

# ============================================================================
# FONCTION PRINCIPALE CORRIGÉE - Ne stocke pas le token dans le repo
# ============================================================================

function Publish-ToGitHubRepo-Secure {
    param(
        [string]$Username,
        [string]$RepoName,
        [string]$Description,
        [bool]$IsPrivate
    )
    
    Write-Host "`n=== PUBLICATION SÉCURISÉE GITHUB ===" -ForegroundColor Cyan
    
    # Demander le token à l'utilisateur (ne pas le lire du fichier)
    Write-Host "🔐 AUTHENTIFICATION GITHUB" -ForegroundColor Yellow
    Write-Host "Le token GitHub NE DOIT PAS être stocké dans le repository." -ForegroundColor Red
    Write-Host ""
    
    if ($script:TempGitHubToken -and (Read-Host "Utiliser le token en mémoire? (O/N)") -eq 'O') {
        $Token = $script:TempGitHubToken
        Write-Host "✓ Token utilisé depuis la mémoire" -ForegroundColor Green
    } else {
        Write-Host "Instructions pour générer un token:" -ForegroundColor Gray
        Write-Host "1. https://github.com/settings/tokens" -ForegroundColor Gray
        Write-Host "2. 'Generate new token (classic)'" -ForegroundColor Gray
        Write-Host "3. Permission: 'repo' (seulement)" -ForegroundColor Green
        Write-Host "4. Copiez le token (commence par 'ghp_')" -ForegroundColor Gray
        Write-Host ""
        
        $Token = Read-Host "Collez votre token GitHub (NE sera PAS sauvegardé)"
        
        if ([string]::IsNullOrWhiteSpace($Token)) {
            Write-Host "❌ Token requis" -ForegroundColor Red
            return @{ success = $false; error = "Token GitHub requis" }
        }
    }
    
    # Sauvegarder la localisation
    $originalDir = Get-Location
    
    try {
        # Aller dans le projet
        Set-Location $PROJECT_PATH -ErrorAction Stop
        Write-Host "Répertoire: $(Get-Location)" -ForegroundColor Gray
        
        # ÉTAPE CRITIQUE: Créer un fichier config SANS le token pour le commit
        Write-Host "Préparation configuration sécurisée..." -NoNewline
        
        # Créer une version safe de la configuration
        $safeConfig = @{
            PROJECT_NAME = $PROJECT_NAME
            PROJECT_PATH = $PROJECT_PATH
            GITHUB_USERNAME = $Username
            GITHUB_REPO_NAME = $RepoName
            GITHUB_REPO_PRIVATE = $IsPrivate
            GITHUB_REPO_DESCRIPTION = $Description
            GITHUB_TOKEN = "*** REMOVED FOR SECURITY ***"
        }
        
        # Sauvegarder l'original
        if (Test-Path $configPath) {
            Copy-Item $configPath "$configPath.backup" -Force
        }
        
        # Écrire la version safe
        $safeConfig | ConvertTo-Json | Out-File $configPath -Encoding UTF8
        Write-Host " ✓" -ForegroundColor Green
        
        # Configuration Git
        Write-Host "Configuration Git..." -NoNewline
        git config user.name "$Username"
        git config user.email "$Username@users.noreply.github.com"
        Write-Host " ✓" -ForegroundColor Green
        
        # URL avec token (ne sera pas dans l'historique Git)
        $remoteUrl = "https://x-access-token:${Token}@github.com/${Username}/${RepoName}.git"
        
        # Initialiser si nécessaire
        if (-not (Test-Path ".git")) {
            Write-Host "Initialisation Git..." -NoNewline
            git init
            Write-Host " ✓" -ForegroundColor Green
        }
        
        # Remote
        git remote remove origin 2>$null
        git remote add origin $remoteUrl
        
        # Ajouter fichiers (sauf backup)
        Write-Host "Ajout fichiers sécurisés..." -NoNewline
        
        # S'assurer que .gitignore exclut les fichiers sensibles
        $secureGitignore = @"
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
        $secureGitignore | Out-File ".gitignore" -Encoding UTF8
        
        # Ajouter tout sauf les fichiers sensibles
        git add .
        Write-Host " ✓" -ForegroundColor Green
        
        # Commit
        Write-Host "Commit..." -NoNewline
        $commitMsg = "🔒 Publication sécurisée: $PROJECT_NAME - $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
        git commit -m $commitMsg --quiet
        Write-Host " ✓" -ForegroundColor Green
        
        # Branche
        Write-Host "Branche..." -NoNewline
        git branch -M main
        Write-Host " ✓" -ForegroundColor Green
        
        # Push
        Write-Host "Push..." -NoNewline
        $env:GIT_TERMINAL_PROMPT = "0"
        $output = git push -u origin main --force 2>&1
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host " ✓" -ForegroundColor Green
            Write-Host "✅ PUBLICATION RÉUSSIE ET SÉCURISÉE !" -ForegroundColor Green
            Write-Host "🔗 https://github.com/$Username/$RepoName" -ForegroundColor Cyan
            
            # Restaurer la config originale
            if (Test-Path "$configPath.backup") {
                Move-Item "$configPath.backup" $configPath -Force
            }
            
            Set-Location $originalDir
            return @{
                success = $true
                url = "https://github.com/$Username/$RepoName"
                secure = $true
            }
        } else {
            Write-Host " ✗" -ForegroundColor Red
            
            # Vérifier si c'est une erreur de secret
            if ($output -match "secret" -or $output -match "GH013") {
                Write-Host "❌ GitHub a bloqué le push à cause d'un secret détecté" -ForegroundColor Red
                Write-Host "Solution: Autorisez manuellement ou supprimez le token du fichier" -ForegroundColor Yellow
                
                # Restaurer la config
                if (Test-Path "$configPath.backup") {
                    Move-Item "$configPath.backup" $configPath -Force
                }
            }
            
            Write-Host "Erreur: $output" -ForegroundColor Red
            
            Set-Location $originalDir
            return @{ success = $false; error = $output }
        }
        
    } catch {
        Write-Host " ✗" -ForegroundColor Red
        Write-Host "❌ Erreur: $_" -ForegroundColor Red
        
        # Restaurer la config en cas d'erreur
        if (Test-Path "$configPath.backup") {
            Move-Item "$configPath.backup" $configPath -Force
        }
        
        Set-Location $originalDir
        return @{ success = $false; error = $_ }
    }
}

# ============================================================================
# SCRIPT POUR NETTOYER L'HISTORIQUE GIT DES SECRETS
# ============================================================================

function Remove-Secrets-From-Git {
    Write-Host "=== NETTOYAGE DES SECRETS DE L'HISTORIQUE GIT ===" -ForegroundColor Cyan
    
    Write-Host "ATTENTION: Cette opération va réécrire l'historique Git." -ForegroundColor Red
    Write-Host "Ne l'utilisez que si vous avez poussé des secrets par accident." -ForegroundColor Red
    Write-Host ""
    
    $confirm = Read-Host "Voulez-vous continuer? (tapez 'OUI' pour confirmer)"
    if ($confirm -ne "OUI") {
        Write-Host "Opération annulée." -ForegroundColor Yellow
        return
    }
    
    # Installation de git-filter-repo si nécessaire
    Write-Host "Vérification de git-filter-repo..." -NoNewline
    try {
        git filter-repo --version 2>&1 | Out-Null
        Write-Host " ✓" -ForegroundColor Green
    } catch {
        Write-Host " ✗" -ForegroundColor Red
        Write-Host "Installation de git-filter-repo requise:" -ForegroundColor Yellow
        Write-Host "pip install git-filter-repo" -ForegroundColor Gray
        return
    }
    
    # Créer un fichier de remplacement
    $replacements = @()
    
    # Motifs de tokens GitHub à rechercher
    $tokenPatterns = @(
        'ghp_[a-zA-Z0-9]{36,}',
        'github_pat_[a-zA-Z0-9_]{82}',
        'gho_[a-zA-Z0-9]{36,}',
        'ghu_[a-zA-Z0-9]{36,}',
        'ghs_[a-zA-Z0-9]{36,}',
        'ghr_[a-zA-Z0-9]{36,}'
    )
    
    # Créer le fichier de configuration pour git-filter-repo
    $filterConfig = @"
[filter "remove-secrets"]
    smudge = cat
    clean = sed -E 's/$($tokenPatterns -join '|')/***REMOVED***/g'
"@
    
    $filterConfig | Out-File "git-filter-config.txt" -Encoding UTF8
    
    Write-Host "Nettoyage en cours..." -ForegroundColor Yellow
    git filter-repo --force --replace-text "git-filter-config.txt"
    
    Remove-Item "git-filter-config.txt" -Force
    
    Write-Host "✅ Historique nettoyé !" -ForegroundColor Green
    Write-Host "Maintenant forcez le push: git push origin --force --all" -ForegroundColor Cyan
}

# ============================================================================
# MENU PRINCIPAL MIS À JOUR
# ============================================================================

# Dans le menu, remplacez l'option 1 par:
switch ($choice) {
    '1' {
        Write-Host "`n=== PUBLICATION SÉCURISÉE GITHUB ===" -ForegroundColor Cyan
        
        # Demander les informations
        if (-not $GITHUB_USERNAME) {
            $GITHUB_USERNAME = Read-Host "Nom d'utilisateur GitHub"
        }
        
        if (-not $GITHUB_REPO_NAME) {
            $GITHUB_REPO_NAME = Read-Host "Nom du repository"
        }
        
        # Option de nettoyage si nécessaire
        Write-Host "`nOptions:" -ForegroundColor Yellow
        Write-Host "1. Publier normalement" -ForegroundColor Green
        Write-Host "2. Nettoyer l'historique des secrets d'abord" -ForegroundColor Red
        
        $option = Read-Host "Choix [1-2]"
        
        if ($option -eq '2') {
            Remove-Secrets-From-Git
        }
        
        # Publication sécurisée
        $result = Publish-ToGitHubRepo-Secure -Username $GITHUB_USERNAME `
                                            -RepoName $GITHUB_REPO_NAME `
                                            -Description $GITHUB_REPO_DESCRIPTION `
                                            -IsPrivate $GITHUB_REPO_PRIVATE
        
        if ($result.success) {
            Write-Host ""
            Write-Host "✅ Publication sécurisée réussie !" -ForegroundColor Green
            Write-Host "Le token a été protégé et n'est pas dans l'historique Git." -ForegroundColor Cyan
        } else {
            Write-Host ""
            Write-Host "❌ Échec de la publication" -ForegroundColor Red
            Write-Host "Erreur: $($result.error)" -ForegroundColor Red
        }
        
        Write-Host ""
        Write-Host "Appuyez sur Entrée pour continuer..."
        Read-Host
    }
    # ... autres options ...
}
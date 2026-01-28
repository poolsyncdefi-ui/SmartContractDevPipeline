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
            Write-Host "Appuyez sur Entrée pour continuer..."
            Read-Host
        }
        '2' {
            Write-Host "`n=== GITHUB GISTS ===" -ForegroundColor Cyan
            Write-Host "Fonctionnalité à implémenter" -ForegroundColor Gray
            Write-Host ""
            Read-Host "Appuyez sur Entrée pour continuer..."
        }
        '3' {
            Write-Host "`n=== FICHIERS LOCAUX ===" -ForegroundColor Cyan
            Write-Host "Fonctionnalité à implémenter" -ForegroundColor Gray
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
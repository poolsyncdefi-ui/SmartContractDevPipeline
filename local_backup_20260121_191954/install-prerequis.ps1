# =============================================================================
# install-prerequis.ps1 - Script d'installation des prérequis
# Version corrigée et améliorée
# =============================================================================

# Définition des variables au début pour une meilleure maintenance
$global:isAdmin = $false
$global:venvPath = "venv"
$global:requirementsFile = "requirements.txt"
$global:ollamaVersion = "latest"
$global:nodeVersion = "18.x"  # Version LTS recommandée

# Configuration du script
$ErrorActionPreference = "Stop"
$ProgressPreference = 'SilentlyContinue'

# -----------------------------------------------------------------------------
# Fonction : Test-Administrator
# Description : Vérifie si le script est exécuté en tant qu'administrateur
# -----------------------------------------------------------------------------
function Test-Administrator {
    try {
        $identity = [Security.Principal.WindowsIdentity]::GetCurrent()
        $principal = New-Object Security.Principal.WindowsPrincipal($identity)
        return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
    }
    catch {
        Write-Host "Impossible de vérifier les droits administrateur: $_" -ForegroundColor Yellow
        return $false
    }
}

# -----------------------------------------------------------------------------
# Fonction : Install-Chocolatey
# Description : Installe Chocolatey si nécessaire
# -----------------------------------------------------------------------------
function Install-Chocolatey {
    Write-Host "`n[1/7] Vérification de Chocolatey..." -ForegroundColor Green
    
    if (Get-Command choco -ErrorAction SilentlyContinue) {
        Write-Host "✓ Chocolatey est déjà installé" -ForegroundColor Cyan
        return $true
    }
    
    Write-Host "Installation de Chocolatey..." -ForegroundColor Yellow
    
    try {
        # Méthode officielle d'installation
        Set-ExecutionPolicy Bypass -Scope Process -Force
        [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072
        Invoke-Expression ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))
        
        # Ajout au PATH pour la session courante
        $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
        
        Write-Host "✓ Chocolatey installé avec succès" -ForegroundColor Green
        return $true
    }
    catch {
        Write-Host "✗ Échec de l'installation de Chocolatey: $_" -ForegroundColor Red
        return $false
    }
}

# -----------------------------------------------------------------------------
# Fonction : Install-PythonWithChoco
# Description : Installe Python via Chocolatey
# -----------------------------------------------------------------------------
function Install-PythonWithChoco {
    Write-Host "`n[2/7] Installation de Python..." -ForegroundColor Green
    
    if (Get-Command python -ErrorAction SilentlyContinue) {
        $version = & python --version 2>&1
        Write-Host "✓ Python déjà installé: $version" -ForegroundColor Cyan
        
        # Vérification de la version
        if ($version -match "Python 3\.(7|8|9|10|11|12)") {
            return $true
        } else {
            Write-Host "Version de Python obsolète, mise à jour..." -ForegroundColor Yellow
        }
    }
    
    try {
        Write-Host "Installation de Python 3.11 (recommandé)..." -ForegroundColor Yellow
        choco install python311 -y --no-progress
        
        # Rafraîchir le PATH
        refreshenv
        
        # Vérification
        $pythonCheck = & python --version 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✓ Python installé: $pythonCheck" -ForegroundColor Green
            return $true
        } else {
            throw "Python non détecté après installation"
        }
    }
    catch {
        Write-Host "✗ Échec de l'installation de Python: $_" -ForegroundColor Red
        
        # Solution de secours
        Write-Host "Tentative d'installation via le web..." -ForegroundColor Yellow
        try {
            $pythonInstaller = "https://www.python.org/ftp/python/3.11.4/python-3.11.4-amd64.exe"
            $installerPath = "$env:TEMP\python-installer.exe"
            
            Invoke-WebRequest -Uri $pythonInstaller -OutFile $installerPath
            Start-Process -FilePath $installerPath -Args "/quiet InstallAllUsers=1 PrependPath=1" -Wait
            
            Write-Host "✓ Python installé via l'installateur officiel" -ForegroundColor Green
            return $true
        }
        catch {
            Write-Host "✗ Échec de toutes les méthodes d'installation Python" -ForegroundColor Red
            return $false
        }
    }
}

# -----------------------------------------------------------------------------
# Fonction : Install-NodeWithChoco
# Description : Installe Node.js via Chocolatey
# -----------------------------------------------------------------------------
function Install-NodeWithChoco {
    Write-Host "`n[3/7] Installation de Node.js..." -ForegroundColor Green
    
    if (Get-Command node -ErrorAction SilentlyContinue) {
        $version = & node --version 2>&1
        Write-Host "✓ Node.js déjà installé: $version" -ForegroundColor Cyan
        return $true
    }
    
    try {
        Write-Host "Installation de Node.js LTS..." -ForegroundColor Yellow
        choco install nodejs-lts -y --no-progress
        
        # Rafraîchir le PATH
        refreshenv
        
        # Vérification
        $nodeCheck = & node --version 2>&1
        $npmCheck = & npm --version 2>&1
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✓ Node.js installé: $nodeCheck" -ForegroundColor Green
            Write-Host "✓ NPM installé: $npmCheck" -ForegroundColor Green
            return $true
        } else {
            throw "Node.js non détecté après installation"
        }
    }
    catch {
        Write-Host "✗ Échec de l'installation de Node.js: $_" -ForegroundColor Red
        return $false
    }
}

# -----------------------------------------------------------------------------
# Fonction : Install-Ollama
# Description : Installe Ollama pour les modèles IA
# -----------------------------------------------------------------------------
function Install-Ollama {
    Write-Host "`n[4/7] Installation d'Ollama..." -ForegroundColor Green
    
    # Vérifier si Ollama est déjà installé
    if (Get-Command ollama -ErrorAction SilentlyContinue) {
        $version = & ollama --version 2>&1
        Write-Host "✓ Ollama déjà installé: $version" -ForegroundColor Cyan
        return $true
    }
    
    try {
        Write-Host "Téléchargement et installation d'Ollama..." -ForegroundColor Yellow
        
        # Télécharger l'installateur Windows
        $ollamaURL = "https://ollama.com/download/OllamaSetup.exe"
        $installerPath = "$env:TEMP\OllamaSetup.exe"
        
        # Téléchargement avec barre de progression
        Write-Host "Téléchargement en cours..." -ForegroundColor Yellow
        Invoke-WebRequest -Uri $ollamaURL -OutFile $installerPath -UseBasicParsing
        
        # Installation silencieuse
        Write-Host "Installation en cours..." -ForegroundColor Yellow
        Start-Process -FilePath $installerPath -Args "/S" -Wait
        
        # Attendre que le service soit prêt
        Start-Sleep -Seconds 10
        
        # Vérification
        if (Get-Command ollama -ErrorAction SilentlyContinue) {
            Write-Host "✓ Ollama installé avec succès" -ForegroundColor Green
            
            # Démarrer le service
            Write-Host "Démarrage du service Ollama..." -ForegroundColor Yellow
            Start-Process "ollama" -ArgumentList "serve" -WindowStyle Hidden
            
            # Télécharger un modèle léger pour test
            Write-Host "Téléchargement du modèle de test (tinyllama)..." -ForegroundColor Yellow
            Start-Process "ollama" -ArgumentList "pull tinyllama" -NoNewWindow -Wait
            
            return $true
        } else {
            throw "Ollama non détecté après installation"
        }
    }
    catch {
        Write-Host "✗ Échec de l'installation d'Ollama: $_" -ForegroundColor Red
        Write-Host "Vous pouvez l'installer manuellement depuis: https://ollama.com" -ForegroundColor Yellow
        return $false
    }
}

# -----------------------------------------------------------------------------
# Fonction : Setup-PythonEnvironment
# Description : Configure l'environnement virtuel Python
# -----------------------------------------------------------------------------
function Setup-PythonEnvironment {
    Write-Host "`n[5/7] Configuration de l'environnement Python..." -ForegroundColor Green
    
    # Vérifier si venv existe déjà
    if (Test-Path $venvPath) {
        Write-Host "✓ Environnement virtuel déjà existant" -ForegroundColor Cyan
        
        # Vérifier s'il est actif
        if ($env:VIRTUAL_ENV) {
            Write-Host "✓ Environnement virtuel déjà activé" -ForegroundColor Cyan
        } else {
            # Activer l'environnement
            & "$venvPath\Scripts\Activate.ps1"
        }
    } else {
        try {
            # Créer l'environnement virtuel
            Write-Host "Création de l'environnement virtuel..." -ForegroundColor Yellow
            python -m venv $venvPath
            
            # Activer l'environnement
            & "$venvPath\Scripts\Activate.ps1"
            
            Write-Host "✓ Environnement virtuel créé et activé" -ForegroundColor Green
        }
        catch {
            Write-Host "✗ Échec de la création de l'environnement virtuel: $_" -ForegroundColor Red
            return $false
        }
    }
    
    # Mettre à jour pip
    try {
        Write-Host "Mise à jour de pip..." -ForegroundColor Yellow
        python -m pip install --upgrade pip
        Write-Host "✓ Pip mis à jour" -ForegroundColor Green
    }
    catch {
        Write-Host "✗ Échec de la mise à jour de pip: $_" -ForegroundColor Red
    }
    
    return $true
}

# -----------------------------------------------------------------------------
# Fonction : Install-PythonDependencies
# Description : Installe les dépendances Python depuis requirements.txt
# -----------------------------------------------------------------------------
function Install-PythonDependencies {
    Write-Host "`n[6/7] Installation des dépendances Python..." -ForegroundColor Green
    
    if (-not (Test-Path $requirementsFile)) {
        Write-Host "✗ Fichier $requirementsFile non trouvé" -ForegroundColor Red
        
        # Créer un fichier requirements.txt minimal
        Write-Host "Création d'un fichier requirements.txt minimal..." -ForegroundColor Yellow
        @"
# Dépendances minimales pour SmartContractPipeline
fastapi>=0.104.0
uvicorn[standard]>=0.24.0
pydantic>=2.4.0
python-dotenv>=1.0.0
requests>=2.31.0
web3>=6.10.0
"@ | Out-File -FilePath $requirementsFile -Encoding UTF8
        
        Write-Host "✓ Fichier $requirementsFile créé" -ForegroundColor Green
    }
    
    try {
        Write-Host "Installation des dépendances..." -ForegroundColor Yellow
        pip install -r $requirementsFile
        
        # Installation de dépendances optionnelles utiles
        Write-Host "Installation de dépendances supplémentaires..." -ForegroundColor Yellow
        pip install pytest pytest-asyncio black isort mypy
        
        Write-Host "✓ Dépendances installées avec succès" -ForegroundColor Green
        return $true
    }
    catch {
        Write-Host "✗ Échec de l'installation des dépendances: $_" -ForegroundColor Red
        
        # Essayer avec pip install individuel
        Write-Host "Tentative d'installation des packages essentiels..." -ForegroundColor Yellow
        try {
            pip install fastapi uvicorn web3
            Write-Host "✓ Packages essentiels installés" -ForegroundColor Green
            return $true
        }
        catch {
            Write-Host "✗ Échec de l'installation des packages essentiels" -ForegroundColor Red
            return $false
        }
    }
}

# -----------------------------------------------------------------------------
# Fonction : Test-Installations
# Description : Vérifie que toutes les installations fonctionnent
# -----------------------------------------------------------------------------
function Test-Installations {
    Write-Host "`n[7/7] Validation des installations..." -ForegroundColor Green
    
    $tests = @(
        @{Name="Python"; Command="python --version"; MinVersion="3.7"},
        @{Name="Node.js"; Command="node --version"; MinVersion="v18"},
        @{Name="NPM"; Command="npm --version"; MinVersion="8"},
        @{Name="Ollama"; Command="ollama --version"; Optional=$true}
    )
    
    $allPassed = $true
    
    foreach ($test in $tests) {
        try {
            $output = Invoke-Expression $test.Command 2>&1
            $success = $LASTEXITCODE -eq 0
            
            if ($success -or ($test.Optional -and -not $success)) {
                $color = if ($test.Optional -and -not $success) { "Yellow" } else { "Green" }
                $status = if ($test.Optional -and -not $success) { "⚠ Optionnel" } else { "✓ OK" }
                Write-Host "$status $($test.Name): $output" -ForegroundColor $color
            } else {
                Write-Host "✗ $($test.Name): Non disponible" -ForegroundColor Red
                $allPassed = $false
            }
        }
        catch {
            if ($test.Optional) {
                Write-Host "⚠ $($test.Name): Optionnel non installé" -ForegroundColor Yellow
            } else {
                Write-Host "✗ $($test.Name): Erreur de test" -ForegroundColor Red
                $allPassed = $false
            }
        }
    }
    
    # Test de l'environnement Python
    try {
        $pythonTest = & python -c "import sys; print(f'Python {sys.version}'); import fastapi; print('FastAPI disponible')" 2>&1
        Write-Host "✓ Environnement Python: OK" -ForegroundColor Green
    }
    catch {
        Write-Host "✗ Environnement Python: Problème avec les imports" -ForegroundColor Red
        $allPassed = $false
    }
    
    return $allPassed
}

# -----------------------------------------------------------------------------
# FONCTION PRINCIPALE
# -----------------------------------------------------------------------------
function Main {
    Write-Host "`n" + ("="*60) -ForegroundColor Cyan
    Write-Host "INSTALLATION DES PRÉREQUIS - SmartContractPipeline" -ForegroundColor Cyan
    Write-Host "="*60 -ForegroundColor Cyan
    
    # 1. Vérification des droits administrateur
    $global:isAdmin = Test-Administrator
    
    if (-not $isAdmin) {
        Write-Host "`n⚠ ATTENTION: Ce script nécessite des droits administrateur" -ForegroundColor Red
        Write-Host "Veuillez exécuter PowerShell en tant qu'Administrateur" -ForegroundColor Yellow
        Write-Host "1. Cliquez droit sur PowerShell" -ForegroundColor Yellow
        Write-Host "2. Sélectionnez 'Exécuter en tant qu'administrateur'" -ForegroundColor Yellow
        Write-Host "3. Relancez ce script" -ForegroundColor Yellow
        
        $choice = Read-Host "`nVoulez-vous quand même continuer? (oui/non)"
        if ($choice -notmatch "^(oui|yes|o|y)$") {
            exit 1
        }
    }
    
    # Journalisation
    $logFile = "install-prerequis-$(Get-Date -Format 'yyyyMMdd-HHmmss').log"
    Start-Transcript -Path $logFile -Append
    
    try {
        # 2. Installation des composants
        $chocoInstalled = Install-Chocolatey
        if (-not $chocoInstalled) {
            throw "Échec de l'installation de Chocolatey"
        }
        
        $pythonInstalled = Install-PythonWithChoco
        if (-not $pythonInstalled) {
            throw "Échec de l'installation de Python"
        }
        
        $nodeInstalled = Install-NodeWithChoco
        if (-not $nodeInstalled) {
            Write-Host "Node.js optionnel pour certains composants" -ForegroundColor Yellow
        }
        
        $ollamaInstalled = Install-Ollama
        if (-not $ollamaInstalled) {
            Write-Host "Ollama optionnel mais recommandé pour les agents IA" -ForegroundColor Yellow
        }
        
        # 3. Configuration Python
        $envSetup = Setup-PythonEnvironment
        if (-not $envSetup) {
            throw "Échec de la configuration de l'environnement Python"
        }
        
        $depsInstalled = Install-PythonDependencies
        if (-not $depsInstalled) {
            throw "Échec de l'installation des dépendances Python"
        }
        
        # 4. Validation finale
        $testsPassed = Test-Installations
        
        Write-Host "`n" + ("="*60) -ForegroundColor Cyan
        
        if ($testsPassed) {
            Write-Host "✅ INSTALLATION RÉUSSIE" -ForegroundColor Green
            Write-Host "Tous les prérequis sont installés et configurés." -ForegroundColor Green
            
            Write-Host "`nProchaines étapes:" -ForegroundColor Yellow
            Write-Host "1. Votre environnement virtuel Python est activé" -ForegroundColor White
            Write-Host "2. Vous pouvez lancer le pipeline avec: python main.py" -ForegroundColor White
            Write-Host "3. Pour désactiver l'environnement: deactivate" -ForegroundColor White
            Write-Host "`nLog d'installation: $logFile" -ForegroundColor Gray
        } else {
            Write-Host "⚠ INSTALLATION PARTIELLE" -ForegroundColor Yellow
            Write-Host "Certains composants ont échoué mais l'essentiel est installé." -ForegroundColor Yellow
            Write-Host "Consultez le log pour plus de détails: $logFile" -ForegroundColor Gray
        }
        
    }
    catch {
        Write-Host "`n❌ ERREUR CRITIQUE" -ForegroundColor Red
        Write-Host "Message: $_" -ForegroundColor Red
        Write-Host "Stack: $($_.ScriptStackTrace)" -ForegroundColor DarkGray
        Write-Host "`nConsultez le log complet: $logFile" -ForegroundColor Yellow
        
        exit 1
    }
    finally {
        Stop-Transcript
        
        # Afficher un résumé
        Write-Host "`n" + ("-"*60) -ForegroundColor DarkGray
        Write-Host "Résumé de l'installation:" -ForegroundColor Gray
        Write-Host "- Python: $(if (Get-Command python -ErrorAction SilentlyContinue) {'✓'} else {'✗'})" -ForegroundColor Gray
        Write-Host "- Node.js: $(if (Get-Command node -ErrorAction SilentlyContinue) {'✓'} else {'✗'})" -ForegroundColor Gray
        Write-Host "- Ollama: $(if (Get-Command ollama -ErrorAction SilentlyContinue) {'✓'} else {'✗'})" -ForegroundColor Gray
        Write-Host "- Environnement virtuel: $(if (Test-Path $venvPath) {'✓'} else {'✗'})" -ForegroundColor Gray
        Write-Host "- Dépendances: $(if (Test-Path "$venvPath\Scripts\pip.exe") {'✓'} else {'✗'})" -ForegroundColor Gray
        Write-Host "- Log: $logFile" -ForegroundColor Gray
    }
}

# -----------------------------------------------------------------------------
# POINT D'ENTRÉE DU SCRIPT
# -----------------------------------------------------------------------------

# Vérifier la version de Windows
if ([Environment]::OSVersion.Version.Major -lt 10) {
    Write-Host "Ce script nécessite Windows 10 ou supérieur" -ForegroundColor Red
    exit 1
}

# Exécuter la fonction principale
Main
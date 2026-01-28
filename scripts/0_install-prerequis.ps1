# =============================================================================
# install-prerequis.ps1 - Installation des prérequis pour SmartContractPipeline
# Version: 2.2.0 - Corrections Ollama complètes
# =============================================================================

# -----------------------------------------------------------------------------
# CONFIGURATION
# -----------------------------------------------------------------------------

class InstallationConfig {
    [string]$ProjectName = "SmartContractPipeline"
    [string]$Version = "2.2.0"
    
    # Chemins
    [string]$ProjectRoot
    [string]$LogDir
    [string]$VenvPath
    [string]$RequirementsFile
    [string]$TempDir = "D:\Temp"
    
    # URLs
    [hashtable]$Urls = @{
        Ollama = "https://ollama.com/download/OllamaSetup.exe"
        Python = "https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe"
    }
    
    # Versions minimales
    [hashtable]$MinVersions = @{
        Windows = @{Build=19041}
    }
    
    # Packages
    [string[]]$ChocolateyPackages = @(
        "python311",
        "nodejs-lts",
        "git",
        "vscode",
        "postman",
        "curl",
        "7zip"
    )
    
    # Modèles Ollama
    [string[]]$OllamaModels = @(
        "deepseek-coder:6.7b",
        "llama2:7b",
        "mistral:7b"
    )
    
    # Chemins sur D:
    [hashtable]$InstallPaths = @{
        Ollama = "D:\Ollama"
        Models = "D:\Ollama\Models"
    }
    
    # Constructeur
    InstallationConfig([string]$projectRoot) {
        $this.ProjectRoot = $projectRoot
        $this.LogDir = Join-Path $projectRoot "logs"
        $this.VenvPath = Join-Path $projectRoot "venv"
        $this.RequirementsFile = Join-Path $projectRoot "requirements.txt"
        
        # Assurer D:\Temp existe
        if (-not (Test-Path $this.TempDir)) {
            New-Item -Path $this.TempDir -ItemType Directory -Force | Out-Null
        }
    }
}

# -----------------------------------------------------------------------------
# INITIALISATION
# -----------------------------------------------------------------------------

$global:ScriptConfig = $null

function Initialize-Configuration {
    [OutputType([InstallationConfig])]
    param()
    
    try {
        $projectRoot = $PSScriptRoot
        
        # Valider le répertoire
        if (-not (Test-Path (Join-Path $projectRoot "agents"))) {
            throw "Dossier 'agents' introuvable. Mauvais répertoire ?"
        }
        
        # Créer configuration
        $config = [InstallationConfig]::new($projectRoot)
        $global:ScriptConfig = $config
        
        Write-Host "Configuration initialisée" -ForegroundColor Green
        return $config
        
    } catch {
        Write-Host "ERREUR Initialisation: $_" -ForegroundColor Red
        throw
    }
}

function Get-Config {
    [OutputType([InstallationConfig])]
    param()
    
    if ($null -eq $global:ScriptConfig) {
        throw "Configuration non initialisée"
    }
    return $global:ScriptConfig
}

# -----------------------------------------------------------------------------
# UTILITAIRES
# -----------------------------------------------------------------------------

function Write-Log {
    param(
        [string]$Message,
        [string]$Level = 'Info',
        [switch]$NoNewLine
    )
    
    $timestamp = Get-Date -Format "HH:mm:ss"
    $colors = @{Info='White'; Success='Green'; Warning='Yellow'; Error='Red'}
    $symbols = @{Info='»'; Success='✓'; Warning='⚠'; Error='✗'}
    
    $output = "[$timestamp] $($symbols[$Level]) $Message"
    Write-Host $output -ForegroundColor $colors[$Level] -NoNewLine:$NoNewLine
    
    # Log fichier
    try {
        $config = Get-Config
        $logFile = Join-Path $config.LogDir "install-$(Get-Date -Format 'yyyyMMdd').log"
        "[$timestamp] [$Level] $Message" | Out-File $logFile -Append -Encoding UTF8
    } catch {}
}

function Test-Admin {
    try {
        $identity = [Security.Principal.WindowsIdentity]::GetCurrent()
        $principal = New-Object Security.Principal.WindowsPrincipal($identity)
        return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
    } catch {
        return $false
    }
}

function Test-DriveSpace {
    try {
        $drive = Get-PSDrive -Name "D" -ErrorAction Stop
        $freeGB = [math]::Round($drive.Free / 1GB, 2)
        Write-Log "D: a $freeGB GB libre" -Level Info
        return ($freeGB -ge 20)
    } catch {
        Write-Log "Impossible de vérifier D:" -Level Error
        return $false
    }
}

# -----------------------------------------------------------------------------
# FONCTIONS D'INSTALLATION
# -----------------------------------------------------------------------------

function Install-Chocolatey {
    if (Get-Command choco -ErrorAction SilentlyContinue) {
        Write-Log "Chocolatey déjà installé" -Level Success
        return $true
    }
    
    Write-Log "Installation Chocolatey..." -Level Info
    
    try {
        $originalPolicy = Get-ExecutionPolicy -Scope Process
        Set-ExecutionPolicy Bypass -Scope Process -Force
        
        [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072
        iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))
        
        Set-ExecutionPolicy $originalPolicy -Scope Process -Force
        
        Start-Sleep -Seconds 3
        if (Get-Command choco -ErrorAction SilentlyContinue) {
            Write-Log "Chocolatey installé" -Level Success
            return $true
        }
        throw "Installation échouée"
    } catch {
        Write-Log "Échec Chocolatey: $_" -Level Error
        return $false
    }
}

function Install-BasePackages {
    $config = Get-Config
    Write-Log "Installation packages..." -Level Info
    
    $success = 0
    foreach ($package in $config.ChocolateyPackages) {
        try {
            Write-Log "  $package..." -Level Info -NoNewLine
            
            if (choco list --local-only $package --exact) {
                Write-Log " (déjà installé)" -Level Success
                $success++
                continue
            }
            
            choco install $package -y --no-progress
            if ($LASTEXITCODE -eq 0) {
                Write-Log " ✓" -Level Success
                $success++
            } else {
                Write-Log " (code $LASTEXITCODE)" -Level Warning
            }
        } catch {
            Write-Log " (erreur)" -Level Warning
        }
    }
    
    refreshenv
    return $true
}

function Install-Python {
    if (Get-Command python -ErrorAction SilentlyContinue) {
        $version = python --version 2>&1
        Write-Log "Python: $version" -Level Success
        return $true
    }
    
    Write-Log "Installation Python..." -Level Info
    
    try {
        choco install python311 -y --no-progress
        refreshenv
        Start-Sleep -Seconds 3
        
        if (Get-Command python -ErrorAction SilentlyContinue) {
            Write-Log "Python installé" -Level Success
            return $true
        }
        throw "Python non détecté"
    } catch {
        Write-Log "Échec Python: $_" -Level Error
        return $false
    }
}

function Setup-PythonEnvironment {
    $config = Get-Config
    Write-Log "Configuration environnement Python..." -Level Info
    
    # Environnement virtuel
    if (-not (Test-Path $config.VenvPath)) {
        try {
            python -m venv $config.VenvPath
            Write-Log "Environnement créé" -Level Success
        } catch {
            Write-Log "Échec création environnement: $_" -Level Error
            return $false
        }
    }
    
    # Activer
    try {
        $activate = Join-Path $config.VenvPath "Scripts\Activate.ps1"
        if (Test-Path $activate) {
            . $activate
        }
    } catch {}
    
    # Mettre à jour pip
    try {
        python -m pip install --upgrade pip --disable-pip-version-check
    } catch {}
    
    return $true
}

function Install-PythonDependencies {
    $config = Get-Config
    
    # Créer requirements.txt si absent
    if (-not (Test-Path $config.RequirementsFile)) {
        @"
fastapi>=0.104.0
uvicorn[standard]>=0.24.0
web3>=6.10.0
pydantic>=2.4.0
langchain>=0.1.0
ollama>=0.1.0
requests>=2.31.0
"@ | Out-File $config.RequirementsFile -Encoding UTF8
    }
    
    Write-Log "Installation dépendances..." -Level Info
    
    try {
        pip install -r $config.RequirementsFile --no-cache-dir
        Write-Log "Dépendances installées" -Level Success
        return $true
    } catch {
        Write-Log "Échec dépendances: $_" -Level Error
        return $false
    }
}

function Install-Ollama {
    Write-Log "Installation d'Ollama..." -Level Info
    
    # Chemin D: cible
    $ollamaPath = "D:\Ollama"
    $ollamaExe = Join-Path $ollamaPath "ollama.exe"
    
    # Vérifier si déjà installé sur D:
    if (Test-Path $ollamaExe) {
        $version = & $ollamaExe --version 2>&1
        Write-Log "[OK] Ollama déjà installé sur D:: $version" -Level Success
        return $true
    }
    
    # Télécharger
    Write-Log "Téléchargement d'Ollama (1.2GB)..." -Level Info
    
    try {
        $installerPath = Join-Path $Script:Config.TempDir "OllamaSetup.exe"
        
        # Nettoyer l'ancien fichier
        if (Test-Path $installerPath) {
            Remove-Item -Path $installerPath -Force -ErrorAction SilentlyContinue
        }
        
        # Télécharger
        $progressPreference = 'SilentlyContinue'
        Invoke-WebRequest -Uri $Script:Config.Urls.Ollama -OutFile $installerPath -UseBasicParsing
        
        $size = [math]::Round((Get-Item $installerPath).Length/1MB, 2)
        Write-Log "[OK] Téléchargement réussi ($size MB)" -Level Success
        
        # === MÉTHODE DÉFINITIVE : Installation Interactive avec Contrôle ===
        
        # 1. Préparer D:\Ollama
        if (-not (Test-Path $ollamaPath)) {
            New-Item -Path $ollamaPath -ItemType Directory -Force | Out-Null
            Write-Log "Dossier préparé: $ollamaPath" -Level Info
        }
        
        # 2. Instructions CLAIRES
        Write-Host "`n" -ForegroundColor Cyan
        Write-Host "┌────────────────────────────────────────────────────────────┐" -ForegroundColor Cyan
        Write-Host "│                INSTALLATION OLLAMA - IMPORTANT             │" -ForegroundColor Red
        Write-Host "├────────────────────────────────────────────────────────────┤" -ForegroundColor Cyan
        Write-Host "│ L'installateur va s'ouvrir. SUIVEZ CES ÉTAPES :           │" -ForegroundColor Yellow
        Write-Host "│                                                            │" -ForegroundColor Yellow
        Write-Host "│ 1. Dans l'installateur, cliquez sur 'Browse...'           │" -ForegroundColor White
        Write-Host "│ 2. Naviguez vers : D:\                                    │" -ForegroundColor White
        Write-Host "│ 3. Cliquez sur 'Make New Folder'                          │" -ForegroundColor White
        Write-Host "│ 4. Nommez le dossier : Ollama                            │" -ForegroundColor White
        Write-Host "│ 5. Sélectionnez D:\Ollama                                 │" -ForegroundColor Green
        WriteHost "│ 6. Décochez 'Create Desktop Shortcut' (optionnel)         │" -ForegroundColor White
        Write-Host "│ 7. Cliquez sur Install                                    │" -ForegroundColor White
        Write-Host "│                                                            │" -ForegroundColor Yellow
        Write-Host "│ ⚠  NE LAISSEZ PAS l'installation par défaut sur C:\ !     │" -ForegroundColor Red
        Write-Host "└────────────────────────────────────────────────────────────┘" -ForegroundColor Cyan
        Write-Host "`n"
        
        # 3. Donner le temps de lire
        Write-Host "L'installateur s'ouvre dans 10 secondes..." -ForegroundColor Yellow
        for ($i = 10; $i -gt 0; $i--) {
            Write-Host "  $i..." -ForegroundColor Gray -NoNewline
            Start-Sleep -Seconds 1
        }
        Write-Host "`n"
        
        # 4. Ouvrir l'installateur
        Write-Log "Ouverture de l'installateur Ollama..." -Level Info
        $process = Start-Process -FilePath $installerPath -Wait -PassThru
        
        # 5. Attendre et vérifier
        Write-Log "Attente de l'installation..." -Level Info
        Start-Sleep -Seconds 20
        
        # 6. Vérifier l'installation sur D:
        if (Test-Path $ollamaExe) {
            Write-Log "[OK] Ollama installé sur D:" -Level Success
            
            # Configurer le PATH
            $env:Path += ";$ollamaPath"
            [Environment]::SetEnvironmentVariable("Path", $env:Path, [EnvironmentVariableTarget]::Machine)
            
            # Configurer les modèles sur D:
            $modelsPath = "D:\Ollama\Models"
            if (-not (Test-Path $modelsPath)) {
                New-Item -Path $modelsPath -ItemType Directory -Force | Out-Null
            }
            
            [Environment]::SetEnvironmentVariable("OLLAMA_MODELS", $modelsPath, [EnvironmentVariableTarget]::User)
            [Environment]::SetEnvironmentVariable("OLLAMA_MODELS", $modelsPath, [EnvironmentVariableTarget]::Machine)
            $env:OLLAMA_MODELS = $modelsPath
            
            Write-Log "Dossier des modèles configuré: $modelsPath" -Level Success
            
            # Démarrer le service
            Write-Log "Démarrage du service Ollama..." -Level Info
            Start-Process $ollamaExe -ArgumentList "serve" -WindowStyle Hidden
            Start-Sleep -Seconds 10
            
            # Télécharger les modèles
            Write-Log "Téléchargement des modèles IA..." -Level Info
            
            foreach ($model in $Script:Config.OllamaModels) {
                try {
                    Write-Log "  Téléchargement de $model..." -Level Info -NoNewLine
                    & $ollamaExe pull $model 2>&1 | Out-Null
                    Write-Log " [OK]" -Level Success
                } catch {
                    Write-Log " [ECHEC]" -Level Warning
                }
            }
            
            Write-Log "[OK] Ollama installé et configuré sur D:" -Level Success
            return $true
            
        } else {
            # Vérifier si installé sur C: par erreur
            $ollamaC = Get-Command ollama -ErrorAction SilentlyContinue
            if ($ollamaC) {
                Write-Log "[ERREUR] Ollama installé sur C: au lieu de D:" -Level Error
                Write-Host "`n⚠ PROBLEME DETECTE : Ollama est installé sur C:\" -ForegroundColor Red
                Write-Host "Pour corriger :" -ForegroundColor Yellow
                Write-Host "1. Désinstallez Ollama depuis le Panneau de configuration" -ForegroundColor White
                Write-Host "2. Relancez ce script" -ForegroundColor White
                Write-Host "3. Cette fois, CHOISISSEZ D:\Ollama dans l'installateur" -ForegroundColor White
            } else {
                Write-Log "[ERREUR] Ollama non installé" -Level Error
            }
            
            return $false
        }
        
    } catch {
        Write-Log "Échec de l'installation d'Ollama: $_" -Level Error
        
        # Instructions de secours
        Write-Host "`n" + ("="*60) -ForegroundColor Yellow
        Write-Host "INSTRUCTIONS MANUELLES" -ForegroundColor Yellow
        Write-Host "="*60 -ForegroundColor Yellow
        Write-Host "1. Ouvrez : https://ollama.com/download/OllamaSetup.exe" -ForegroundColor White
        Write-Host "2. Enregistrez le fichier dans : D:\Temp\" -ForegroundColor White
        Write-Host "3. Exécutez l'installateur" -ForegroundColor White
        Write-Host "4. IMPORTANT : Choisissez D:\Ollama comme chemin" -ForegroundColor Green
        Write-Host "5. Après installation, testez : ollama --version" -ForegroundColor White
        Write-Host "="*60 -ForegroundColor Yellow
        
        return $false
    }
}

function Install-NodeJS {
    if (Get-Command node -ErrorAction SilentlyContinue) {
        $version = node --version
        Write-Log "Node.js: $version" -Level Success
        return $true
    }
    
    Write-Log "Installation Node.js..." -Level Info
    
    try {
        choco install nodejs-lts -y --no-progress
        refreshenv
        Start-Sleep -Seconds 3
        
        if (Get-Command node -ErrorAction SilentlyContinue) {
            Write-Log "Node.js installé" -Level Success
            return $true
        }
        return $false
    } catch {
        Write-Log "Échec Node.js: $_" -Level Warning
        return $false
    }
}

function Install-Git {
    if (Get-Command git -ErrorAction SilentlyContinue) {
        $version = git --version
        Write-Log "Git: $version" -Level Success
        return $true
    }
    
    Write-Log "Installation Git..." -Level Info
    
    try {
        choco install git -y --no-progress
        refreshenv
        Write-Log "Git installé" -Level Success
        return $true
    } catch {
        Write-Log "Échec Git: $_" -Level Warning
        return $false
    }
}

function Test-Installations {
    $config = Get-Config
    Write-Log "Validation finale..." -Level Info
    
    $tests = @(
        @{Name="Python"; Test={Get-Command python -ErrorAction SilentlyContinue}},
        @{Name="Environnement"; Test={Test-Path $config.VenvPath}},
        @{Name="Node.js"; Test={Get-Command node -ErrorAction SilentlyContinue}},
        @{Name="Git"; Test={Get-Command git -ErrorAction SilentlyContinue}},
        @{Name="Ollama"; Test={
            $ollamaExe = Join-Path $config.InstallPaths.Ollama "ollama.exe"
            (Test-Path $ollamaExe) -or (Get-Command ollama -ErrorAction SilentlyContinue)
        }}
    )
    
    $allPassed = $true
    foreach ($test in $tests) {
        $passed = & $test.Test
        $status = if ($passed) { "✓" } else { "✗" }
        $level = if ($passed) { "Success" } else { "Warning" }
        
        Write-Log "$status $($test.Name)" -Level $level
        
        if (-not $passed -and $test.Name -in @("Python", "Environnement")) {
            $allPassed = $false
        }
    }
    
    return $allPassed
}

# -----------------------------------------------------------------------------
# FONCTION PRINCIPALE
# -----------------------------------------------------------------------------

function Main {
    # En-tête
    Write-Host "`n" + ("="*70) -ForegroundColor Cyan
    Write-Host "SMART CONTRACT PIPELINE - INSTALLATION COMPLÈTE" -ForegroundColor Cyan
    Write-Host "Version: 2.2.0" -ForegroundColor Cyan
    Write-Host "="*70 -ForegroundColor Cyan
    Write-Host "`n"
    
    try {
        # Initialisation
        $config = Initialize-Configuration
        
        # Créer logs
        if (-not (Test-Path $config.LogDir)) {
            New-Item -Path $config.LogDir -ItemType Directory -Force | Out-Null
        }
        
        $logFile = Join-Path $config.LogDir "install-$(Get-Date -Format 'yyyyMMdd-HHmmss').log"
        Start-Transcript -Path $logFile -Append
        
        Write-Log "Début installation complète" -Level Info
        
        # Vérifications
        Write-Log "Étape 1: Vérifications système" -Level Info
        if (-not (Test-DriveSpace)) {
            throw "Espace D: insuffisant"
        }
        
        if (-not (Test-Admin)) {
            Write-Log "⚠ Administration recommandée" -Level Warning
        }
        
        # Chocolatey
        Write-Log "`nÉtape 2: Chocolatey" -Level Info
        if (-not (Install-Chocolatey)) {
            throw "Échec Chocolatey"
        }
        
        # Packages
        Write-Log "`nÉtape 3: Packages système" -Level Info
        Install-BasePackages
        
        # Python
        Write-Log "`nÉtape 4: Python" -Level Info
        if (-not (Install-Python)) {
            throw "Échec Python"
        }
        
        if (-not (Setup-PythonEnvironment)) {
            throw "Échec environnement Python"
        }
        
        if (-not (Install-PythonDependencies)) {
            throw "Échec dépendances Python"
        }
        
        # Node.js
        Write-Log "`nÉtape 5: Node.js" -Level Info
        Install-NodeJS
        
        # Ollama (CRITIQUE - avec nettoyage)
        Write-Log "`nÉtape 6: Ollama (Agents IA)" -Level Info
        if (-not (Install-Ollama)) {
            Write-Log "Ollama nécessite installation manuelle" -Level Error
            # Mais on continue, c'est optionnel pour le pipeline de base
        }
        
        # Git
        Write-Log "`nÉtape 7: Git" -Level Info
        Install-Git
        
        # Validation
        Write-Log "`nÉtape 8: Validation" -Level Info
        $allPassed = Test-Installations
        
        # Conclusion
        Write-Host "`n" + ("="*70) -ForegroundColor Cyan
        if ($allPassed) {
            Write-Host "✅ INSTALLATION RÉUSSIE" -ForegroundColor Green
        } else {
            Write-Host "⚠ INSTALLATION PARTIELLE" -ForegroundColor Yellow
        }
        
        Write-Host "="*70 -ForegroundColor Cyan
        
        # Instructions finales
        Write-Host "`nProchaines étapes:" -ForegroundColor Yellow
        Write-Host "1. Environnement virtuel activé" -ForegroundColor White
        Write-Host "2. Testez: python -c 'import web3; print(\"Web3 OK\")'" -ForegroundColor White
        Write-Host "3. Si Ollama installé: ollama list" -ForegroundColor White
        Write-Host "4. Lancez le pipeline: python main.py" -ForegroundColor White
        
        # Marqueur
        $marker = Join-Path $config.ProjectRoot ".installed"
        @{
            Date = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
            Version = $config.Version
            Success = $allPassed
            OllamaInstalled = (Test-Path (Join-Path $config.InstallPaths.Ollama "ollama.exe"))
        } | ConvertTo-Json | Out-File $marker -Encoding UTF8
        
        Write-Log "Installation terminée" -Level Success
        return $allPassed
        
    } catch {
        Write-Log "ERREUR: $_" -Level Error
        return $false
    } finally {
        Stop-Transcript | Out-Null
        Write-Host "`nLog: $logFile" -ForegroundColor Gray
    }
}

# -----------------------------------------------------------------------------
# EXÉCUTION
# -----------------------------------------------------------------------------

try {
    # Désactiver l'environnement virtuel actuel si présent
    if ($env:VIRTUAL_ENV) {
        deactivate 2>$null
    }
    
    $success = Main
    exit $(if ($success) { 0 } else { 1 })
} catch {
    Write-Host "ERREUR FATALE: $_" -ForegroundColor Red
    exit 1
}
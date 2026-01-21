# install-prerequis.ps1
# Exécuter en tant qu'Administrateur
param([switch]$SkipChecks)

Write-Host "=== INSTALLATION DES PREREQUIS COMPLETE ===" -ForegroundColor Cyan
Write-Host "Date: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor Gray
Write-Host ""

# Fonction pour vérifier les installations
function Test-CommandExists {
    param([string]$Command)
    try {
        Get-Command $Command -ErrorAction Stop | Out-Null
        return $true
    } catch {
        return $false
    }
}

# 1. Vérifier et installer Winget
Write-Host "1. VÉRIFICATION WINGET..." -ForegroundColor Yellow
if (-not (Test-CommandExists "winget") -and -not $SkipChecks) {
    Write-Host "   Installation de Winget..." -ForegroundColor Gray
    # Télécharger et installer Winget depuis GitHub
    $wingetUrl = "https://github.com/microsoft/winget-cli/releases/latest/download/Microsoft.DesktopAppInstaller_8wekyb3d8bbwe.msixbundle"
    $wingetPath = "$env:TEMP\winget.msixbundle"
    
    try {
        Invoke-WebRequest -Uri $wingetUrl -OutFile $wingetPath -ErrorAction Stop
        Add-AppxPackage -Path $wingetPath -ErrorAction Stop
        Write-Host "   ✅ Winget installé" -ForegroundColor Green
    } catch {
        Write-Host "   ⚠️  Impossible d'installer Winget automatiquement" -ForegroundColor Yellow
        Write-Host "   Veuillez installer Winget depuis le Microsoft Store" -ForegroundColor White
        Write-Host "   Lien: ms-windows-store://pdp/?productid=9NBLGGH4NNS1" -ForegroundColor Cyan
        Start-Process "ms-windows-store://pdp/?productid=9NBLGGH4NNS1"
        Read-Host "   Appuyez sur Entrée après l'installation"
    }
} else {
    Write-Host "   ✅ Winget déjà installé" -ForegroundColor Green
}

# 2. Installer Node.js LTS (version spécifique stable)
Write-Host "`n2. INSTALLATION NODE.JS..." -ForegroundColor Yellow
if (-not (Test-CommandExists "node") -or $SkipChecks) {
    Write-Host "   Installation de Node.js 20.11.1 LTS..." -ForegroundColor Gray
    winget install --id OpenJS.NodeJS.LTS --exact --version 20.11.1 --accept-package-agreements --accept-source-agreements --silent
    Write-Host "   ✅ Node.js installé" -ForegroundColor Green
} else {
    $nodeVersion = (node --version).Trim()
    Write-Host "   ✅ Node.js déjà installé: $nodeVersion" -ForegroundColor Green
}

# 3. Installer Python 3.12
Write-Host "`n3. INSTALLATION PYTHON..." -ForegroundColor Yellow
if (-not (Test-CommandExists "python") -or $SkipChecks) {
    Write-Host "   Installation de Python 3.12.1..." -ForegroundColor Gray
    winget install --id Python.Python.3.12 --exact --version 3.12.1 --accept-package-agreements --accept-source-agreements --silent
    Write-Host "   ✅ Python installé" -ForegroundColor Green
} else {
    $pythonVersion = (python --version 2>&1).ToString()
    Write-Host "   ✅ Python déjà installé: $pythonVersion" -ForegroundColor Green
}

# 4. Installer Git
Write-Host "`n4. INSTALLATION GIT..." -ForegroundColor Yellow
if (-not (Test-CommandExists "git") -or $SkipChecks) {
    Write-Host "   Installation de Git..." -ForegroundColor Gray
    winget install --id Git.Git --accept-package-agreements --accept-source-agreements --silent
    Write-Host "   ✅ Git installé" -ForegroundColor Green
} else {
    $gitVersion = (git --version).Trim()
    Write-Host "   ✅ Git déjà installé: $gitVersion" -ForegroundColor Green
}

# 5. Installer Ollama
Write-Host "`n5. INSTALLATION OLLAMA..." -ForegroundColor Yellow
if (-not (Test-Path "$env:LOCALAPPDATA\Programs\Ollama\ollama.exe") -or $SkipChecks) {
    Write-Host "   Téléchargement d'Ollama..." -ForegroundColor Gray
    $ollamaUrl = "https://ollama.com/download/windows"
    $installerPath = "$env:TEMP\ollama-setup.exe"
    
    try {
        Invoke-WebRequest -Uri $ollamaUrl -OutFile $installerPath -ErrorAction Stop
        Write-Host "   Installation en cours..." -ForegroundColor Gray
        Start-Process -FilePath $installerPath -ArgumentList "/S" -Wait
        Start-Sleep -Seconds 5
        Write-Host "   ✅ Ollama installé" -ForegroundColor Green
    } catch {
        Write-Host "   ❌ Erreur lors de l'installation d'Ollama" -ForegroundColor Red
        Write-Host "   Message: $_" -ForegroundColor Red
    }
} else {
    Write-Host "   ✅ Ollama déjà installé" -ForegroundColor Green
}

# 6. Installer Docker Desktop
Write-Host "`n6. INSTALLATION DOCKER DESKTOP..." -ForegroundColor Yellow
if (-not (Test-CommandExists "docker") -or $SkipChecks) {
    Write-Host "   Installation de Docker Desktop..." -ForegroundColor Gray
    winget install --id Docker.DockerDesktop --accept-package-agreements --accept-source-agreements --silent
    Write-Host "   ⚠️  Redémarrage requis pour Docker" -ForegroundColor Yellow
    Write-Host "   ✅ Docker Desktop installé" -ForegroundColor Green
} else {
    $dockerVersion = (docker --version).Trim()
    Write-Host "   ✅ Docker déjà installé: $dockerVersion" -ForegroundColor Green
}

# 7. Installer VS Code
Write-Host "`n7. INSTALLATION VS CODE..." -ForegroundColor Yellow
if (-not (Test-Path "$env:LOCALAPPDATA\Programs\Microsoft VS Code\Code.exe") -or $SkipChecks) {
    Write-Host "   Installation de VS Code..." -ForegroundColor Gray
    winget install --id Microsoft.VisualStudioCode --accept-package-agreements --accept-source-agreements --silent
    Write-Host "   ✅ VS Code installé" -ForegroundColor Green
} else {
    Write-Host "   ✅ VS Code déjà installé" -ForegroundColor Green
}

# 8. Configurer les variables d'environnement
Write-Host "`n8. CONFIGURATION ENVIRONNEMENT..." -ForegroundColor Yellow
$pathsToAdd = @(
    "$env:USERPROFILE\.cargo\bin",
    "$env:LOCALAPPDATA\Programs\Python\Python312\Scripts",
    "$env:LOCALAPPDATA\Programs\Python\Python312",
    "$env:USERPROFILE\AppData\Roaming\npm",
    "$env:LOCALAPPDATA\Programs\Ollama"
)

$currentPath = [Environment]::GetEnvironmentVariable("Path", "User")
$updated = $false

foreach ($path in $pathsToAdd) {
    if (Test-Path $path -ErrorAction SilentlyContinue) {
        if ($currentPath -notlike "*$path*") {
            $currentPath += ";$path"
            $updated = $true
            Write-Host "   ✅ Chemin ajouté: $path" -ForegroundColor Green
        }
    }
}

if ($updated) {
    [Environment]::SetEnvironmentVariable("Path", $currentPath, "User")
    Write-Host "   Variables d'environnement mises à jour" -ForegroundColor Green
}

Write-Host "`n✅ PREREQUIS INSTALLES AVEC SUCCES" -ForegroundColor Green
Write-Host "Redémarrez PowerShell pour que les changements prennent effet." -ForegroundColor Yellow
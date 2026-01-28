# install-blockchain.ps1 - Script d'installation des outils blockchain
# Version corrigée pour détecter Foundry sur D: - 2026-01-27

# ========== FONCTIONS ==========
function Test-CommandExists {
    param([string]$CommandName)
    try {
        # Essayer d'abord la méthode standard
        $cmd = Get-Command $CommandName -ErrorAction SilentlyContinue
        if ($null -ne $cmd) {
            return $true
        }
        
        # Vérifier sur le disque D: spécifiquement
        if ($CommandName -eq "forge") {
            $forgePaths = @(
                "D:\Foundry\forge.exe",
                "D:\foundry\forge.exe",
                "$env:ProgramFiles\Foundry\bin\forge.exe",
                "$env:USERPROFILE\.foundry\bin\forge.exe"
            )
            
            foreach ($path in $forgePaths) {
                if (Test-Path $path) {
                    # Ajouter au PATH de la session si trouvé
                    $binDir = Split-Path $path -Parent
                    if ($env:Path -notlike "*$binDir*") {
                        $env:Path += ";$binDir"
                    }
                    return $true
                }
            }
        }
        
        return $false
    } catch {
        return $false
    }
}

function Write-InstallLog {
    param([string]$Message, [string]$Type = "INFO")
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $color = "White"
    if ($Type -eq "SUCCESS") { $color = "Green" }
    elseif ($Type -eq "ERROR") { $color = "Red" }
    elseif ($Type -eq "WARNING") { $color = "Yellow" }
    Write-Host "[$timestamp] $Type : $Message" -ForegroundColor $color
}

function Invoke-Silent {
    param([string]$Command)
    try {
        Invoke-Expression $Command 2>$null 1>$null
        return $true
    } catch {
        return $false
    }
}

# ========== INSTALLATION DES OUTILS ==========
Write-Host "`n=== INSTALLATION DES OUTILS BLOCKCHAIN ===" -ForegroundColor Cyan
$installDate = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
Write-Host "Date: $installDate`n"

# 1. VÉRIFICATION FOUNDRY (VERSION CORRIGÉE POUR D:)
Write-Host "1. VÉRIFICATION FOUNDRY..." -ForegroundColor Yellow

# Vérifier spécifiquement sur D:
$foundryFound = $false
$foundryPath = $null

$possiblePaths = @(
    "D:\Foundry\forge.exe",
    "D:\foundry\forge.exe",  # Votre installation
    "D:\Foundry\bin\forge.exe",
    "D:\foundry\bin\forge.exe",
    "$env:ProgramFiles\Foundry\bin\forge.exe",
    "$env:USERPROFILE\.foundry\bin\forge.exe"
)

foreach ($path in $possiblePaths) {
    if (Test-Path $path) {
        $foundryFound = $true
        $foundryPath = $path
        $binDir = Split-Path $path -Parent
        
        # Ajouter au PATH de la session si nécessaire
        if ($env:Path -notlike "*$binDir*") {
            $env:Path += ";$binDir"
            Write-InstallLog "Ajouté au PATH de la session: $binDir" -Type "INFO"
        }
        break
    }
}

if ($foundryFound) {
    Write-InstallLog "Foundry trouvé à: $foundryPath" -Type "SUCCESS"
    
    # Tenter de vérifier la version
    try {
        $forgeVersion = forge --version 2>&1 | Select-Object -First 1
        if ($forgeVersion -match "forge") {
            Write-InstallLog "Version: $forgeVersion" -Type "INFO"
        } else {
            # Essayer en appelant directement
            $directPath = $foundryPath
            & $directPath --version 2>&1 | ForEach-Object {
                if ($_ -match "forge") {
                    Write-InstallLog "Version: $_" -Type "INFO"
                }
            }
        }
    } catch {
        Write-InstallLog "Impossible de vérifier la version de Foundry" -Type "WARNING"
    }
} else {
    Write-InstallLog "Foundry non détecté" -Type "WARNING"
    Write-Host "`nFoundry semble être installé sur D:\foundry\" -ForegroundColor Yellow
    Write-Host "Mais n'est pas dans le PATH de cette session." -ForegroundColor White
    Write-Host "`nPour corriger:" -ForegroundColor Yellow
    Write-Host "1. Ajoutez D:\foundry\ au PATH système:" -ForegroundColor White
    Write-Host "   [Environment]::SetEnvironmentVariable('Path', `$env:Path + ';D:\foundry', 'Machine')" -ForegroundColor Gray
    Write-Host "2. Redémarrez PowerShell" -ForegroundColor White
    Write-Host "3. Testez: forge --version" -ForegroundColor White
    Write-Host "`nOU exécutez cette commande maintenant:" -ForegroundColor Yellow
    Write-Host "   `$env:Path += ';D:\foundry'" -ForegroundColor Gray
}

# 2. INSTALLATION HARDHAT
Write-Host "`n2. INSTALLATION HARDHAT..." -ForegroundColor Yellow

if (Test-CommandExists "npm") {
    # Vérifier si Hardhat est déjà disponible
    $hardhatCheck = $false
    try {
        $output = npx hardhat --version 2>$null
        if ($LASTEXITCODE -eq 0) {
            $hardhatCheck = $true
        }
    } catch {
        $hardhatCheck = $false
    }
    
    if (-not $hardhatCheck) {
        Write-InstallLog "Installation Hardhat..." -Type "INFO"
        try {
            npm install -g hardhat 2>$null
            Write-InstallLog "Hardhat installé" -Type "SUCCESS"
        } catch {
            Write-InstallLog "Erreur installation Hardhat" -Type "ERROR"
        }
    } else {
        Write-InstallLog "Hardhat déjà disponible" -Type "INFO"
    }
} else {
    Write-InstallLog "npm non disponible" -Type "WARNING"
}

# 3. INSTALLATION OUTILS SECURITE
Write-Host "`n3. INSTALLATION OUTILS SECURITE..." -ForegroundColor Yellow

# Vérifier Python/pip
$pipExists = Test-CommandExists "pip"

$securityTools = @(
    @{Name="Solhint"; Command="solhint"; Type="npm"; Install="npm install -g solhint"}
)

# Ajouter outils pip seulement si pip existe
if ($pipExists) {
    Write-InstallLog "pip détecté, ajout des outils Python..." -Type "INFO"
    $securityTools += @{Name="Slither"; Command="slither"; Type="pip"; Install="pip install slither-analyzer --user"}
    $securityTools += @{Name="Mythril"; Command="myth"; Type="pip"; Install="pip install mythril --user"}
} else {
    Write-InstallLog "pip non détecté, outils Python ignorés" -Type "INFO"
}

foreach ($tool in $securityTools) {
    # Vérifier si déjà installé
    if (Test-CommandExists $tool.Command) {
        Write-InstallLog "$($tool.Name) déjà installé" -Type "INFO"
        continue
    }
    
    Write-InstallLog "Installation $($tool.Name)..." -Type "INFO"
    
    if ($tool.Type -eq "npm") {
        try {
            Invoke-Silent "npm install -g solhint"
            Write-InstallLog "$($tool.Name) installé" -Type "SUCCESS"
        } catch {
            Write-InstallLog "Erreur installation $($tool.Name)" -Type "ERROR"
        }
    } elseif ($tool.Type -eq "pip") {
        try {
            Invoke-Silent $tool.Install
            Write-InstallLog "$($tool.Name) installé" -Type "SUCCESS"
        } catch {
            Write-InstallLog "Erreur installation $($tool.Name)" -Type "ERROR"
        }
    }
}

# 4. INSTALLATION OUTILS FRONTEND
Write-Host "`n4. INSTALLATION OUTILS FRONTEND..." -ForegroundColor Yellow

$frontendTools = @(
    @{Name="TypeScript"; Command="tsc"; Install="npm install -g typescript"},
    @{Name="Yarn"; Command="yarn"; Install="npm install -g yarn"}
)

foreach ($tool in $frontendTools) {
    if (Test-CommandExists $tool.Command) {
        Write-InstallLog "$($tool.Name) déjà installé" -Type "INFO"
    } else {
        Write-InstallLog "Installation $($tool.Name)..." -Type "INFO"
        try {
            Invoke-Silent $tool.Install
            Write-InstallLog "$($tool.Name) installé" -Type "SUCCESS"
        } catch {
            Write-InstallLog "Erreur installation $($tool.Name)" -Type "ERROR"
        }
    }
}

Write-InstallLog "Next.js: utiliser 'npx create-next-app'" -Type "INFO"

# 5. INSTALLATION LIBRAIRIES WEB3
Write-Host "`n5. INSTALLATION LIBRAIRIES WEB3..." -ForegroundColor Yellow

# Wagmi CLI
if (-not (Test-CommandExists "wagmi")) {
    Write-InstallLog "Installation @wagmi/cli..." -Type "INFO"
    try {
        Invoke-Silent "npm install -g @wagmi/cli"
        Write-InstallLog "@wagmi/cli installé" -Type "SUCCESS"
    } catch {
        Write-InstallLog "Erreur installation @wagmi/cli" -Type "ERROR"
    }
} else {
    Write-InstallLog "@wagmi/cli déjà installé" -Type "INFO"
}

# Viem - Installation locale seulement
Write-InstallLog "Installation Viem (local)..." -Type "INFO"
try {
    # Vérifier si package.json existe
    if (-not (Test-Path "package.json")) {
        '{"name":"web3-temp","version":"1.0.0","private":true}' | Out-File "package.json" -Encoding UTF8
        Write-InstallLog "package.json créé" -Type "INFO"
    }
    
    # Installer viem localement
    Invoke-Silent "npm install viem"
    Write-InstallLog "Viem installé localement" -Type "SUCCESS"
} catch {
    Write-InstallLog "Erreur installation Viem" -Type "ERROR"
}

# 6. CONFIGURATION RPC ENDPOINTS
Write-Host "`n6. CONFIGURATION RPC ENDPOINTS..." -ForegroundColor Yellow

$rpcConfig = @{
    "ethereum_mainnet" = "https://eth.llamarpc.com"
    "polygon" = "https://polygon.llamarpc.com"
    "arbitrum" = "https://arbitrum.llamarpc.com"
    "optimism" = "https://optimism.llamarpc.com"
    "base" = "https://base.llamarpc.com"
}

$configPath = "$PWD\rpc_endpoints.json"
try {
    $rpcConfig | ConvertTo-Json | Set-Content $configPath -Encoding UTF8
    Write-InstallLog "Configuration RPC sauvegardée dans $configPath" -Type "SUCCESS"
} catch {
    Write-InstallLog "Erreur sauvegarde RPC" -Type "ERROR"
}

# 7. VERIFICATION DES INSTALLATIONS
Write-Host "`n7. VERIFICATION DES INSTALLATIONS..." -ForegroundColor Cyan

# Vérifier Foundry avec notre fonction améliorée
$forgeInstalled = Test-CommandExists "forge"

# Vérifications des autres outils
$toolsToVerify = @(
    @{Name="Foundry"; Installed=$forgeInstalled},
    @{Name="Hardhat"; Installed=(Test-CommandExists "npx")},
    @{Name="Solhint"; Installed=(Test-CommandExists "solhint")},
    @{Name="TypeScript"; Installed=(Test-CommandExists "tsc")},
    @{Name="Yarn"; Installed=(Test-CommandExists "yarn")},
    @{Name="Wagmi CLI"; Installed=(Test-CommandExists "wagmi")}
)

Write-Host "`nRésumé des installations:" -ForegroundColor White
Write-Host ("-" * 50) -ForegroundColor Gray

foreach ($tool in $toolsToVerify) {
    if ($tool.Installed) {
        Write-Host "  ✅ $($tool.Name)" -ForegroundColor Green
    } else {
        Write-Host "  ❌ $($tool.Name)" -ForegroundColor Red
    }
}

# Vérifier Viem
$viemInstalled = Test-Path "node_modules/viem"
Write-Host "`n  Vérification Viem..." -ForegroundColor White
if ($viemInstalled) {
    Write-Host "  ✅ Viem (local)" -ForegroundColor Green
} else {
    Write-Host "  ❌ Viem" -ForegroundColor Red
}

Write-Host ("`n" + "-" * 50) -ForegroundColor Gray

# 8. CRÉATION DU FICHIER DE RÉSUMÉ
$summary = @"
=== RÉSUMÉ DE L'INSTALLATION BLOCKCHAIN ===
Date: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')
Répertoire: $PWD

STATUT DES INSTALLATIONS:
$(foreach ($tool in $toolsToVerify) {
    $status = if ($tool.Installed) { "✓" } else { "✗" }
    "  $status $($tool.Name)"
})

$(if ($viemInstalled) { "  ✓ Viem (local)" } else { "  ✗ Viem" })

FICHIERS CONFIGURÉS:
• rpc_endpoints.json - Endpoints RPC

PROCHAINES ÉTAPES:
1. Pour Foundry: Exécuter 'forge --version' pour vérifier
2. Pour développer: npx hardhat init
3. Pour tester: forge test
4. Voir documentation dans SmartContractPipeline\

NOTES:
$(if (-not $forgeInstalled) { "- Foundry installé sur D:\\foundry\\ mais pas dans le PATH" })
$(if (-not $pipExists) { "- pip non détecté, outils Python non installés" })
"@

try {
    $summary | Out-File "$PWD\installation_summary.txt" -Encoding UTF8
    Write-InstallLog "Résumé sauvegardé dans installation_summary.txt" -Type "SUCCESS"
} catch {
    Write-InstallLog "Erreur sauvegarde résumé" -Type "ERROR"
}

Write-Host "`n=== INSTALLATION TERMINÉE ===" -ForegroundColor Green
Write-Host "Consultez 'installation_summary.txt' pour le rapport complet" -ForegroundColor Cyan

if (-not $forgeInstalled) {
    Write-Host "`n⚠  Foundry détecté sur D:\foundry\ mais pas accessible" -ForegroundColor Red
    Write-Host "Pour rendre Foundry accessible:" -ForegroundColor Yellow
    
    Write-Host "`nOption 1 - Ajouter au PATH de cette session:" -ForegroundColor White
    Write-Host "   `$env:Path += ';D:\foundry'" -ForegroundColor Gray
    Write-Host "   forge --version" -ForegroundColor Gray
    
    Write-Host "`nOption 2 - Ajouter au PATH système (redémarrage requis):" -ForegroundColor White
    Write-Host "   [Environment]::SetEnvironmentVariable('Path', `$env:Path + ';D:\foundry', 'Machine')" -ForegroundColor Gray
    Write-Host "   Redémarrez PowerShell" -ForegroundColor Gray
    
    Write-Host "`nOption 3 - Créer un alias:" -ForegroundColor White
    Write-Host "   Set-Alias forge D:\foundry\forge.exe" -ForegroundColor Gray
    Write-Host "   Set-Alias anvil D:\foundry\anvil.exe" -ForegroundColor Gray
    Write-Host "   Set-Alias cast D:\foundry\cast.exe" -ForegroundColor Gray
}
# install-blockchain.ps1
Write-Host "=== INSTALLATION DES OUTILS BLOCKCHAIN ===" -ForegroundColor Cyan
Write-Host "Date: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor Gray
Write-Host ""

# Variables de versions stables
$versions = @{
    Foundry = "v0.2.0"
    Hardhat = "2.19.5"
    Node = "20.11.1"
}

# 1. Installer Foundry (version spécifique)
Write-Host "1. INSTALLATION FOUNDRY..." -ForegroundColor Yellow
if (-not (Test-CommandExists "forge")) {
    Write-Host "   Installation de Foundry $($versions.Foundry)..." -ForegroundColor Gray
    try {
        # Utiliser l'installateur officiel
        irm https://getfoundry.sh -OutFile "$env:TEMP\foundryup.ps1"
        & "$env:TEMP\foundryup.ps1"
        
        # Vérifier l'installation
        Start-Sleep -Seconds 5
        if (Test-CommandExists "forge") {
            $forgeVersion = (forge --version 2>&1 | Select-String "forge").ToString().Trim()
            Write-Host "   ✅ Foundry installé: $forgeVersion" -ForegroundColor Green
        } else {
            Write-Host "   ⚠️  Foundry installé mais non détecté dans PATH" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "   ❌ Erreur lors de l'installation de Foundry" -ForegroundColor Red
        Write-Host "   Message: $_" -ForegroundColor Red
    }
} else {
    $forgeVersion = (forge --version 2>&1 | Select-String "forge").ToString().Trim()
    Write-Host "   ✅ Foundry déjà installé: $forgeVersion" -ForegroundColor Green
}

# 2. Installer Hardhat
Write-Host "`n2. INSTALLATION HARDHAT..." -ForegroundColor Yellow
if (-not (Test-CommandExists "hardhat")) {
    Write-Host "   Installation de Hardhat $($versions.Hardhat)..." -ForegroundColor Gray
    try {
        npm install -g hardhat@$($versions.Hardhat) --force
        $hardhatVersion = (npx hardhat --version 2>&1).ToString().Trim()
        Write-Host "   ✅ Hardhat installé: $hardhatVersion" -ForegroundColor Green
    } catch {
        Write-Host "   ❌ Erreur lors de l'installation de Hardhat" -ForegroundColor Red
    }
} else {
    $hardhatVersion = (npx hardhat --version 2>&1).ToString().Trim()
    Write-Host "   ✅ Hardhat déjà installé: $hardhatVersion" -ForegroundColor Green
}

# 3. Installer les outils de sécurité
Write-Host "`n3. INSTALLATION OUTILS SECURITE..." -ForegroundColor Yellow
$securityTools = @(
    @{Name="Slither"; Command="slither"; Install="pip install slither-analyzer==0.10.0"},
    @{Name="Solhint"; Command="solhint"; Install="npm install -g solhint@3.6.2"},
    @{Name="Mythril"; Command="myth"; Install="pip install mythril==0.23.28"}
)

foreach ($tool in $securityTools) {
    Write-Host "   $($tool.Name)..." -ForegroundColor Gray
    if (-not (Test-CommandExists $tool.Command)) {
        try {
            Invoke-Expression $tool.Install
            Write-Host "   ✅ $($tool.Name) installé" -ForegroundColor Green
        } catch {
            Write-Host "   ⚠️  Erreur lors de l'installation de $($tool.Name)" -ForegroundColor Yellow
        }
    } else {
        Write-Host "   ✅ $($tool.Name) déjà installé" -ForegroundColor Green
    }
}

# 4. Installer les outils de développement frontend
Write-Host "`n4. INSTALLATION OUTILS FRONTEND..." -ForegroundColor Yellow
$frontendTools = @(
    @{Name="Next.js CLI"; Command="create-next-app"; Install="npm install -g create-next-app@14.1.0"},
    @{Name="TypeScript"; Command="tsc"; Install="npm install -g typescript@5.3.3"},
    @{Name="Yarn"; Command="yarn"; Install="npm install -g yarn@1.22.21"}
)

foreach ($tool in $frontendTools) {
    Write-Host "   $($tool.Name)..." -ForegroundColor Gray
    if (-not (Test-CommandExists $tool.Command)) {
        try {
            Invoke-Expression $tool.Install
            Write-Host "   ✅ $($tool.Name) installé" -ForegroundColor Green
        } catch {
            Write-Host "   ⚠️  Erreur lors de l'installation de $($tool.Name)" -ForegroundColor Yellow
        }
    } else {
        Write-Host "   ✅ $($tool.Name) déjà installé" -ForegroundColor Green
    }
}

# 5. Installer les librairies Web3
Write-Host "`n5. INSTALLATION LIBRAIRIES WEB3..." -ForegroundColor Yellow
$web3Libs = @(
    @{Name="Wagmi CLI"; Command="wagmi"; Install="npm install -g wagmi@2.0.10"},
    @{Name="Viem"; Install="npm install -g viem@1.19.11"}
)

foreach ($lib in $web3Libs) {
    Write-Host "   $($lib.Name)..." -ForegroundColor Gray
    try {
        Invoke-Expression $lib.Install
        Write-Host "   ✅ $($lib.Name) installé" -ForegroundColor Green
    } catch {
        Write-Host "   ⚠️  Erreur lors de l'installation de $($lib.Name)" -ForegroundColor Yellow
    }
}

# 6. Configurer les RPC endpoints
Write-Host "`n6. CONFIGURATION RPC ENDPOINTS..." -ForegroundColor Yellow
$rpcConfigDir = "$env:USERPROFILE\.web3"
if (-not (Test-Path $rpcConfigDir)) {
    New-Item -ItemType Directory -Path $rpcConfigDir -Force | Out-Null
}

$rpcConfig = @{
    endpoints = @{
        ethereum = @{
            mainnet = "https://eth-mainnet.g.alchemy.com/v2/demo"
            sepolia = "https://eth-sepolia.g.alchemy.com/v2/demo"
        }
        arbitrum = @{
            mainnet = "https://arb-mainnet.g.alchemy.com/v2/demo"
            sepolia = "https://arb-sepolia.g.alchemy.com/v2/demo"
        }
        optimism = @{
            mainnet = "https://opt-mainnet.g.alchemy.com/v2/demo"
            sepolia = "https://opt-sepolia.g.alchemy.com/v2/demo"
        }
    }
    versions = @{
        web3 = "1.19.11"
        ethers = "6.8.0"
    }
}

$rpcConfig | ConvertTo-Json -Depth 10 | Out-File -FilePath "$rpcConfigDir\endpoints.json" -Force
Write-Host "   ✅ Configuration RPC sauvegardée" -ForegroundColor Green

# 7. Installer Anvil
Write-Host "`n7. INSTALLATION ANVIL..." -ForegroundColor Yellow
if (-not (Test-CommandExists "anvil")) {
    Write-Host "   Installation d'Anvil via Cargo..." -ForegroundColor Gray
    try {
        if (-not (Test-CommandExists "cargo")) {
            Write-Host "   Installation de Rust..." -ForegroundColor Gray
            winget install --id Rustlang.Rustup --accept-package-agreements --accept-source-agreements --silent
        }
        
        cargo install --git https://github.com/foundry-rs/foundry anvil --profile local --locked
        Write-Host "   ✅ Anvil installé" -ForegroundColor Green
    } catch {
        Write-Host "   ⚠️  Erreur lors de l'installation d'Anvil" -ForegroundColor Yellow
        Write-Host "   Alternative: Anvil est inclus avec Foundry" -ForegroundColor Gray
    }
} else {
    Write-Host "   ✅ Anvil déjà installé" -ForegroundColor Green
}

# 8. Vérifier les installations
Write-Host "`n8. VERIFICATION DES INSTALLATIONS..." -ForegroundColor Yellow
$toolsToCheck = @(
    @{Name="Foundry"; Command="forge --version 2>&1 | Select-String 'forge' | ForEach-Object { $_.ToString().Trim() }"},
    @{Name="Hardhat"; Command="npx hardhat --version 2>&1"},
    @{Name="Node.js"; Command="node --version"},
    @{Name="Python"; Command="python --version 2>&1"},
    @{Name="Git"; Command="git --version"}
)

foreach ($tool in $toolsToCheck) {
    try {
        $version = Invoke-Expression $tool.Command
        Write-Host "   ✅ $($tool.Name): $version" -ForegroundColor Green
    } catch {
        Write-Host "   ❌ $($tool.Name): NON INSTALLE" -ForegroundColor Red
    }
}

Write-Host "`n✅ OUTILS BLOCKCHAIN INSTALLES" -ForegroundColor Green
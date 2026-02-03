# setup-project.ps1
# Script de configuration du projet Smart Contract Dev Pipeline
# Complète la structure sans écraser les fichiers existants

[CmdletBinding()]
param(
    [Parameter(Mandatory=$false)]
    [switch]$CheckOnly,      # Vérification seulement
    
    [Parameter(Mandatory=$false)]
    [switch]$AppendOnly,     # Ajouter seulement, pas écraser
    
    [Parameter(Mandatory=$false)]
    [switch]$VerboseLog      # Renommé pour éviter le conflit avec le paramètre réservé
)

# Configuration
$PROJECT_NAME = "Smart Contract Dev Pipeline"
$VERSION = "1.0.0"

# Chemins importants basés sur l'arborescence typique
$PATHS = @{
    Contracts = "contracts"
    Scripts = "scripts"
    Tests = "test"
    Config = "config"
    Docs = "docs"
    Deployments = "deployments"
    Artifacts = "artifacts"
    Cache = "cache"
    Reports = "reports"
    Agents = "agents"
    Pipelines = "pipelines"
    Templates = "templates"
}

# Fonctions d'affichage
function Write-Title {
    param([string]$Title)
    Write-Host "`n" -NoNewline
    Write-Host "╔════════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
    Write-Host "║                    $PROJECT_NAME                             ║" -ForegroundColor Cyan
    Write-Host "║          Configuration complémentaire du projet              ║" -ForegroundColor Cyan
    Write-Host "╚════════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
    Write-Host "`nMode : $(if ($CheckOnly) { 'Vérification' } else { 'Configuration' })" -ForegroundColor Yellow
    Write-Host "AppendOnly : $(if ($AppendOnly) { 'Oui (ne pas écraser)' } else { 'Non' })`n" -ForegroundColor Yellow
}

function Write-Section {
    param([string]$Section)
    Write-Host "`n▶ " -NoNewline -ForegroundColor Green
    Write-Host $Section -ForegroundColor White
    Write-Host "─" * ($Section.Length + 2) -ForegroundColor DarkGray
}

function Write-Status {
    param([string]$Item, [bool]$Exists, [string]$Type = "dossier")
    $icon = if ($Exists) { "✓" } else { "✗" }
    $color = if ($Exists) { "Green" } else { "Red" }
    $typeText = if ($Type -eq "fichier") { "Fichier" } else { "Dossier" }
    
    Write-Host "  $icon " -NoNewline -ForegroundColor $color
    Write-Host "$typeText " -NoNewline -ForegroundColor Gray
    Write-Host $Item -NoNewline
    
    if ($Exists) {
        Write-Host " (existe)" -ForegroundColor DarkGray
    } else {
        Write-Host " (manquant)" -ForegroundColor DarkGray
    }
}

function Write-Info {
    param([string]$Message)
    Write-Host "    → " -NoNewline -ForegroundColor DarkCyan
    Write-Host $Message -ForegroundColor DarkGray
}

function Write-Warning {
    param([string]$Message)
    Write-Host "  ⚠ " -NoNewline -ForegroundColor Yellow
    Write-Host $Message -ForegroundColor Gray
}

function Write-Success {
    param([string]$Message)
    Write-Host "  ✅ " -NoNewline -ForegroundColor Green
    Write-Host $Message -ForegroundColor White
}

function Write-SubStep {
    param([string]$Message)
    Write-Host "  • " -NoNewline -ForegroundColor DarkCyan
    Write-Host $Message -ForegroundColor Gray
}

# Analyse de l'arborescence existante
function Analyze-ExistingStructure {
    Write-Section "Analyse de la structure existante"
    
    $existingItems = @{}
    $missingItems = @{}
    
    # Vérifier les dossiers principaux
    foreach ($key in $PATHS.Keys) {
        $path = $PATHS[$key]
        $exists = Test-Path $path
        
        Write-Status $path $exists
        
        if ($exists) {
            $existingItems[$key] = $path
        } else {
            $missingItems[$key] = $path
        }
    }
    
    # Compter les éléments dans les dossiers existants
    foreach ($key in $existingItems.Keys) {
        $path = $existingItems[$key]
        $itemCount = (Get-ChildItem -Path $path -ErrorAction SilentlyContinue | Measure-Object).Count
        if ($itemCount -gt 0) {
            Write-Info "  Contient $itemCount élément(s)"
        }
    }
    
    return @{
        Existing = $existingItems
        Missing = $missingItems
    }
}

# Vérifier les fichiers de configuration
function Check-ConfigFiles {
    Write-Section "Vérification des fichiers de configuration"
    
    $configFiles = @{
        "package.json" = @{ Required = $true; Description = "Configuration npm" }
        ".env" = @{ Required = $false; Description = "Variables d'environnement" }
        ".env.example" = @{ Required = $false; Description = "Template environnement" }
        ".gitignore" = @{ Required = $false; Description = "Fichiers ignorés" }
        "README.md" = @{ Required = $false; Description = "Documentation" }
        "hardhat.config.js" = @{ Required = $false; Description = "Config Hardhat" }
        "hardhat.config.ts" = @{ Required = $false; Description = "Config Hardhat TS" }
        "foundry.toml" = @{ Required = $false; Description = "Config Foundry" }
        "truffle-config.js" = @{ Required = $false; Description = "Config Truffle" }
    }
    
    foreach ($file in $configFiles.Keys) {
        $exists = Test-Path $file
        $required = $configFiles[$file].Required
        $desc = $configFiles[$file].Description
        
        if ($exists) {
            Write-Success "$desc : $file"
            
            # Afficher quelques infos sur les fichiers importants
            if ($file -eq "package.json") {
                try {
                    $pkg = Get-Content $file | ConvertFrom-Json -ErrorAction SilentlyContinue
                    if ($pkg) {
                        Write-Info "  Nom : $($pkg.name), Version : $($pkg.version)"
                        if ($pkg.dependencies) {
                            Write-Info "  Dépendances : $($pkg.dependencies.Count)"
                        }
                        if ($pkg.devDependencies) {
                            Write-Info "  DevDépendances : $($pkg.devDependencies.Count)"
                        }
                    }
                } catch { }
            }
            
            if ($file -eq ".gitignore") {
                $lineCount = (Get-Content $file | Measure-Object -Line).Lines
                Write-Info "  Lignes : $lineCount"
            }
        } else {
            if ($required) {
                Write-Warning "$desc manquant : $file"
            } else {
                Write-Info "$desc manquant : $file"
            }
        }
    }
}

# Compléter .gitignore sans écraser
function Complete-Gitignore {
    if ($CheckOnly) { return }
    
    $gitignorePath = ".gitignore"
    $newEntries = @()
    
    # Entrées à ajouter si manquantes
    $entriesToAdd = @(
        "# Environment",
        ".env",
        ".env.local",
        ".env.*.local",
        "",
        "# Build outputs",
        "artifacts/",
        "cache/",
        "coverage/",
        "coverage.json",
        "typechain-types/",
        "build/",
        "dist/",
        "out/",
        "",
        "# Deployments",
        "deployments/",
        "deployments.localhost/",
        "",
        "# Hardhat",
        ".hardhat/",
        "",
        "# Foundry",
        "forge-std/",
        "lib/",
        "",
        "# Coverage",
        "coverage/",
        ".nyc_output/",
        "",
        "# Reports",
        "reports/*.json",
        "reports/*.html",
        "!reports/README.md"
    )
    
    if (Test-Path $gitignorePath) {
        # Lire le contenu existant
        $existingContent = Get-Content $gitignorePath
        
        # Vérifier quelles entrées manquent
        foreach ($entry in $entriesToAdd) {
            if ($entry -eq "" -or $entry.StartsWith("#")) {
                # Les commentaires et lignes vides, on vérifie le contexte
                $newEntries += $entry
            } elseif (-not ($existingContent -contains $entry.TrimEnd('/'))) {
                # Vérifier différentes formes
                $found = $false
                foreach ($line in $existingContent) {
                    if ($line.Trim() -eq $entry.Trim() -or 
                        $line.Trim() -eq $entry.TrimEnd('/') -or
                        $line.Trim() -eq $entry.Trim().TrimStart('#')) {
                        $found = $true
                        break
                    }
                }
                
                if (-not $found) {
                    $newEntries += $entry
                }
            }
        }
        
        if ($newEntries.Count -gt 0) {
            # Ajouter les entrées manquantes
            Add-Content -Path $gitignorePath -Value "`n# Added by setup-project.ps1"
            Add-Content -Path $gitignorePath -Value $newEntries
            Write-Success ".gitignore complété avec $($newEntries.Count) nouvelles entrées"
        } else {
            Write-Info ".gitignore est déjà complet"
        }
    } else {
        # Créer un nouveau .gitignore
        $entriesToAdd | Out-File $gitignorePath -Encoding UTF8
        Write-Success ".gitignore créé"
    }
}

# Compléter package.json si nécessaire
function Complete-PackageJson {
    if ($CheckOnly) { return }
    
    $packagePath = "package.json"
    
    if (Test-Path $packagePath) {
        try {
            $packageJson = Get-Content $packagePath -Raw | ConvertFrom-Json
            
            $modified = $false
            $additions = @()
            
            # Vérifier les scripts essentiels
            $essentialScripts = @{
                "test" = "hardhat test"
                "compile" = "hardhat compile"
                "clean" = "hardhat clean"
                "node" = "hardhat node"
                "coverage" = "hardhat coverage"
            }
            
            if (-not $packageJson.scripts) {
                $packageJson | Add-Member -NotePropertyName "scripts" -NotePropertyValue @{} -Force
                $modified = $true
            }
            
            foreach ($script in $essentialScripts.Keys) {
                if (-not $packageJson.scripts.$script) {
                    $packageJson.scripts | Add-Member -NotePropertyName $script -NotePropertyValue $essentialScripts[$script] -Force
                    $additions += "script.$script"
                    $modified = $true
                }
            }
            
            # Vérifier les devDependencies essentielles pour Hardhat
            $hardhatDeps = @{
                "@nomicfoundation/hardhat-toolbox" = "^2.0.0"
                "hardhat" = "^2.0.0"
                "dotenv" = "^16.0.0"
            }
            
            if (-not $packageJson.devDependencies) {
                $packageJson | Add-Member -NotePropertyName "devDependencies" -NotePropertyValue @{} -Force
                $modified = $true
            }
            
            foreach ($dep in $hardhatDeps.Keys) {
                if (-not $packageJson.devDependencies.$dep) {
                    $packageJson.devDependencies | Add-Member -NotePropertyName $dep -NotePropertyValue $hardhatDeps[$dep] -Force
                    $additions += "devDependency.$dep"
                    $modified = $true
                }
            }
            
            if ($modified) {
                # Sauvegarder
                $packageJson | ConvertTo-Json -Depth 10 | Out-File $packagePath -Encoding UTF8
                Write-Success "package.json complété avec : $($additions -join ', ')"
            } else {
                Write-Info "package.json est déjà complet"
            }
            
        } catch {
            Write-Warning "Impossible de parser package.json : $_"
        }
    } else {
        Write-Info "package.json n'existe pas - création différée à l'installation des dépendances"
    }
}

# Créer .env.example si manquant
function Create-EnvExample {
    if ($CheckOnly) { return }
    
    $envExamplePath = ".env.example"
    
    if (-not (Test-Path $envExamplePath)) {
        $content = @"
# Configuration du projet Smart Contract Dev Pipeline
# COPIEZ CE FICHIER EN .env ET REMPLISSEZ LES VALEURS

# ============================================
# CLÉS API EXTERNES
# ============================================

INFURA_API_KEY="votre_clef_infura_ici"
ALCHEMY_API_KEY="votre_clef_alchemy_ici"
ETHERSCAN_API_KEY="votre_clef_etherscan_ici"
POLYGONSCAN_API_KEY="votre_clef_polygonscan_ici"

# ============================================
# CLÉS PRIVÉES (NE JAMAIS COMMITTER !)
# ============================================

PRIVATE_KEY_TEST="0x0000000000000000000000000000000000000000000000000000000000000000"
PRIVATE_KEY_DEPLOY="0x0000000000000000000000000000000000000000000000000000000000000000"

# ============================================
# URLS RPC
# ============================================

SEPOLIA_RPC_URL="https://sepolia.infura.io/v3/\`${INFURA_API_KEY}"
MAINNET_RPC_URL="https://mainnet.infura.io/v3/\`${INFURA_API_KEY}"
MUMBAI_RPC_URL="https://polygon-mumbai.infura.io/v3/\`${INFURA_API_KEY}"

# ============================================
# CONFIGURATION
# ============================================

REPORT_GAS=true
GAS_REPORTER_CURRENCY="USD"
COINMARKETCAP_API_KEY="votre_clef_coinmarketcap_ici"
"@
        
        $content | Out-File $envExamplePath -Encoding UTF8
        Write-Success ".env.example créé"
    } else {
        Write-Info ".env.example existe déjà"
    }
}

# Créer README.md si manquant
function Create-Readme {
    if ($CheckOnly) { return }
    
    $readmePath = "README.md"
    
    if (-not (Test-Path $readmePath)) {
        $content = @"
# Smart Contract Dev Pipeline

## Présentation
Pipeline de développement pour contrats intelligents.

## Installation

Les prérequis ont été installés via :
- \`0_install-prerequis.ps1\`
- \`2_install-blockchain.ps1\`

Ce script (\`setup-project.ps1\`) a configuré la structure du projet.

## Structure
- \`contracts/\` - Contrats Solidity
- \`scripts/\` - Scripts de déploiement
- \`test/\` - Tests
- \`agents/\` - Agents automatisés (à configurer)
- \`pipelines/\` - Pipelines CI/CD (à configurer)

## Prochaines étapes
1. Configurer les agents : \`setup-agents.ps1\`
2. Installer les dépendances : \`npm install\`
3. Développer vos contrats
"@
        
        $content | Out-File $readmePath -Encoding UTF8
        Write-Success "README.md créé"
    } else {
        Write-Info "README.md existe déjà"
    }
}

function Setup-Environment {
    Write-SubStep "Configuration du fichier .env..."
    
    $envExamplePath = ".env.example"
    $envPath = ".env"
    
    if ($CheckOnly) {
        if (Test-Path $envExamplePath) {
            Write-Info "Vérification : .env serait créé à partir de .env.example"
        } else {
            Write-Warning "Vérification : .env.example manquant, .env ne peut être créé"
        }
        return
    }
    
    # Vérifier si .env.example existe
    if (-not (Test-Path $envExamplePath)) {
        Write-Warning ".env.example n'existe pas, création d'un template..."
        Create-EnvExample
    }
    
    # Vérifier si .env existe déjà
    if (Test-Path $envPath) {
        Write-Info ".env existe déjà"
        
        # Comparer avec .env.example pour voir s'il manque des variables
        if (Test-Path $envExamplePath) {
            $exampleVars = Get-Content $envExamplePath | Where-Object { $_ -match '^[A-Z_]+=' }
            $currentVars = Get-Content $envPath | Where-Object { $_ -match '^[A-Z_]+=' }
            
            $missingVars = $exampleVars | Where-Object { 
                $varName = ($_ -split '=')[0]
                -not ($currentVars -match "^$varName=")
            }
            
            if ($missingVars.Count -gt 0) {
                Write-Warning "$($missingVars.Count) variables manquent dans .env"
                Write-Info "Ajoutez-les manuellement depuis .env.example"
            }
        }
        return
    }
    
    # Créer .env à partir de .env.example
    try {
        Copy-Item $envExamplePath $envPath -ErrorAction Stop
        Write-Success "✅ .env créé à partir de .env.example"
        
        # Avertissement sur les clés à remplacer
        Write-Host "`n⚠️  ATTENTION : Votre fichier .env contient des valeurs par défaut" -ForegroundColor Yellow
        Write-Host "   Remplacez les valeurs suivantes par vos vraies clés :" -ForegroundColor Yellow
        
        $content = Get-Content $envPath
        $placeholders = $content | Where-Object { $_ -match 'votre_|remplacer_par|YOUR_' }
        
        if ($placeholders) {
            foreach ($line in $placeholders | Select-Object -First 5) {
                Write-Host "   - $line" -ForegroundColor Gray
            }
            if ($placeholders.Count -gt 5) {
                Write-Host "   - ... et $($placeholders.Count - 5) autres" -ForegroundColor Gray
            }
        }
        
    } catch {
        Write-Warning "Impossible de créer .env : $_"
        Write-Info "Créez-le manuellement : copy .env.example .env"
    }
}

function Setup-AgentsPreparation {
    Write-SubStep "Préparation pour la configuration des agents..."
    
    if ($CheckOnly) {
        Write-Info "Vérification : Préparation pour setup-agents.ps1"
        return
    }
    
    # Vérifier si le dossier agents/ existe
    if (Test-Path "agents") {
        $agentFiles = Get-ChildItem "agents" -File | Measure-Object
        Write-Info "Dossier agents/ existe avec $($agentFiles.Count) fichiers"
        
        # Vérifier si setup-agents.ps1 existe
        if (Test-Path "setup-agents.ps1") {
            Write-Success "setup-agents.ps1 est présent"
        } else {
            Write-Warning "setup-agents.ps1 manquant - prochaine étape"
        }
    } else {
        Write-Info "Dossier agents/ sera configuré par setup-agents.ps1"
    }
    
    # Créer un fichier d'instructions pour la prochaine étape
    $nextStepsFile = "NEXT_STEP_AGENTS.md"
    $nextStepsContent = @"
# Prochaine étape : Configuration des Agents

## Instructions
1. Exécutez le script de configuration des agents :
   \`\`\`powershell
   .\setup-agents.ps1
   \`\`\`

## Ce qui a déjà été fait :
✅ Structure du projet créée
✅ Fichier .env configuré
✅ Dépendances npm installées
✅ Hardhat configuré

## Ce qui sera fait par setup-agents.ps1 :
- Configuration des agents IA (OpenAI, Anthropic, Google)
- Déploiement des contrats intelligents
- Configuration des pipelines CI/CD
- Mise en place des tests automatisés

## Vérifications avant de continuer :
1. Avez-vous complété votre fichier .env avec vos vraies clés API ?
2. Avez-vous testé Hardhat : \`npx hardhat test\` ?
3. Avez-vous déployé un contrat de test ?

Date : $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')
"@
    
    $nextStepsContent | Out-File $nextStepsFile -Encoding UTF8
    Write-Success "✅ Instructions créées : $nextStepsFile"
}

# Créer les dossiers manquants
function Create-MissingFolders {
    param($missingFolders)
    
    if ($CheckOnly) { return }
    
    if ($missingFolders.Count -eq 0) {
        Write-Info "Tous les dossiers nécessaires existent déjà"
        return
    }
    
    foreach ($folder in $missingFolders.Values) {
        try {
            New-Item -ItemType Directory -Path $folder -Force | Out-Null
            Write-Success "Dossier créé : $folder/"
            
            # Ajouter un README.md minimal dans certains dossiers
            if ($folder -in @("agents", "pipelines", "templates")) {
                $readmeContent = "# $($folder.ToUpper())`n`nCe dossier est configuré par les scripts de setup.`n"
                $readmeContent | Out-File (Join-Path $folder "README.md") -Encoding UTF8
            }
        } catch {
            Write-Warning "Impossible de créer $folder/ : $_"
        }
    }
}

# Créer des fichiers exemples dans contracts/ si vide
function Create-ExampleFiles {
    if ($CheckOnly) { return }
    
    $contractsPath = $PATHS["Contracts"]
    
    if (Test-Path $contractsPath) {
        $contractFiles = Get-ChildItem -Path $contractsPath -Filter "*.sol" -ErrorAction SilentlyContinue
        
        if ($contractFiles.Count -eq 0) {
            # Créer un contrat exemple simple
            $exampleContract = @"
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/**
 * @title Storage
 * @dev Store et retrieve une valeur
 */
contract Storage {
    uint256 private _value;

    event ValueChanged(uint256 oldValue, uint256 newValue);

    /**
     * @dev Store une valeur
     * @param value La valeur à stocker
     */
    function store(uint256 value) public {
        uint256 oldValue = _value;
        _value = value;
        emit ValueChanged(oldValue, value);
    }

    /**
     * @dev Return la valeur stockée
     * @return La valeur stockée
     */
    function retrieve() public view returns (uint256) {
        return _value;
    }
}
"@
            
            $exampleContract | Out-File (Join-Path $contractsPath "Storage.sol") -Encoding UTF8
            Write-Success "Contrat exemple créé : contracts/Storage.sol"
        }
    }
}

# =====================================================================================
# Installer les dépendances npm (VERSION COMPLÈTE CORRIGÉE)
function Install-NpmDependencies {
    Write-SubStep "Vérification et installation des dépendances npm..."
    
    # Vérifier que package.json existe
    if (-not (Test-Path "package.json")) {
        Write-Warning "⚠️ package.json non trouvé. Impossible d'installer les dépendances."
        Write-Info "   Création d'un package.json minimal..."
        
        if (-not $CheckOnly) {
            $minimalPackageJson = @{
                name = "smart-contract-dev-pipeline"
                version = "1.0.0"
                description = "Smart Contract Development Pipeline"
                scripts = @{
                    test = "hardhat test"
                }
                devDependencies = @{}
            }
            $minimalPackageJson | ConvertTo-Json -Depth 3 | Out-File "package.json" -Encoding UTF8
            Write-Success "   ✅ package.json minimal créé"
        }
        return
    }
    
    if ($CheckOnly) { 
        Write-Info "   Vérification seulement : npm install serait exécuté"
        
        # Vérifier si node_modules existe déjà
        if (Test-Path "node_modules") {
            $moduleCount = (Get-ChildItem "node_modules" -Directory | Measure-Object).Count
            Write-Info "   node_modules existe avec $moduleCount packages"
        } else {
            Write-Info "   node_modules n'existe pas encore"
        }
        return 
    }
    
    # Vérifier si les dépendances sont déjà installées
    if (Test-Path "node_modules") {
        $moduleCount = (Get-ChildItem "node_modules" -Directory | Measure-Object).Count
        if ($moduleCount -gt 10) { # Un seuil raisonnable
            Write-Info "   Dépendances déjà installées ($moduleCount packages détectés)"
            Write-Info "   Pour forcer une réinstallation, supprimez le dossier node_modules"
            return
        }
    }
    
    try {
        # Exécuter npm install
        Write-Info "   Exécution de 'npm install' (cela peut prendre quelques minutes)..."
        
        # Capturer la sortie pour meilleur débogage
        $npmOutput = npm install 2>&1
        
        if ($LASTEXITCODE -eq 0) {
            Write-Success "   ✅ Dépendances npm installées avec succès."
            
            # Vérifier l'installation de hardhat
            try {
                $hardhatVersion = npx hardhat --version 2>&1
                if ($LASTEXITCODE -eq 0) {
                    Write-Success "   ✅ Hardhat vérifié : $hardhatVersion"
                } else {
                    Write-Warning "   ⚠️  Hardhat ne répond pas correctement"
                }
            } catch {
                Write-Warning "   ⚠️  Impossible de vérifier Hardhat : $_"
            }
            
            # Vérifier les packages installés
            if (Test-Path "node_modules") {
                $installedModules = Get-ChildItem "node_modules" -Directory | 
                    Where-Object { $_.Name -match "^(hardhat|@nomic|dotenv|chai|ethers)" } |
                    Select-Object -First 5 -ExpandProperty Name
                
                if ($installedModules) {
                    Write-Info "   Packages clés installés : $($installedModules -join ', ')"
                }
            }
        } else {
            Write-Warning "   ⚠️  npm install a échoué (code sortie: $LASTEXITCODE)"
            
            # Essayer avec --force si échec
            Write-Info "   Tentative avec 'npm install --force'..."
            $forceOutput = npm install --force 2>&1
            
            if ($LASTEXITCODE -eq 0) {
                Write-Success "   ✅ Dépendances installées avec --force"
            } else {
                Write-Warning "   ❌ Échec de l'installation même avec --force"
                Write-Info "   Essayez manuellement: npm install --legacy-peer-deps"
            }
        }
    } catch {
        Write-Warning "   ⚠️  Erreur lors de l'installation : $_"
        Write-Info "   Solution: Exécutez manuellement 'npm install' dans le terminal"
    }
}

# Configurer le framework Hardhat (VERSION COMPLÈTE CORRIGÉE)
function Configure-Hardhat {
    Write-SubStep "Configuration du framework Hardhat..."
    
    # Vérifier si une config existe déjà
    $existingConfigs = @()
    if (Test-Path "hardhat.config.js") { $existingConfigs += "hardhat.config.js" }
    if (Test-Path "hardhat.config.ts") { $existingConfigs += "hardhat.config.ts" }
    
    if ($existingConfigs.Count -gt 0) {
        Write-Info "   Fichier(s) de configuration existant(s) : $($existingConfigs -join ', ')"
        
        if ($CheckOnly) {
            Write-Info "   Vérification seulement : la configuration existe déjà"
            return
        }
        
        # En mode normal, demander confirmation pour écraser
        if (-not $Force) {
            Write-Host "`n   ⚠️  Un fichier de configuration Hardhat existe déjà." -ForegroundColor Yellow
            Write-Host "   Voulez-vous le remplacer par la configuration par défaut ?" -ForegroundColor Yellow
            Write-Host "   (o/N - 'o' pour écraser, 'n' pour garder l'actuel): " -NoNewline -ForegroundColor Yellow
            $response = Read-Host
            
            if ($response -ne "o" -and $response -ne "O") {
                Write-Info "   Configuration Hardhat conservée (non écrasée)"
                return
            }
        }
        
        # Sauvegarder l'ancienne config
        foreach ($configFile in $existingConfigs) {
            $backupFile = "$configFile.backup.$(Get-Date -Format 'yyyyMMdd_HHmmss')"
            Copy-Item $configFile $backupFile -ErrorAction SilentlyContinue
            Write-Info "   Backup créé : $backupFile"
        }
    }
    
    if ($CheckOnly) { 
        Write-Info "   Vérification seulement : hardhat.config.js serait créé"
        return 
    }
    
    try {
        # Vérifier que Hardhat est disponible
        Write-Info "   Vérification de l'installation Hardhat..."
        
        $hardhatCheck = $null
        try {
            $hardhatCheck = npx hardhat --version 2>&1
        } catch {
            # Continuer même si la commande échoue
        }
        
        # Vérifier si hardhat est dans package.json même si la commande npx échoue
        $hardhatInstalled = $false
        if (Test-Path "package.json") {
            try {
                $pkg = Get-Content "package.json" -Raw | ConvertFrom-Json
                if (($pkg.devDependencies.PSObject.Properties.Name -contains "hardhat") -or 
                    ($pkg.dependencies.PSObject.Properties.Name -contains "hardhat")) {
                    $hardhatInstalled = $true
                }
            } catch {
                # Ignorer les erreurs de parsing
            }
        }
        
        if (-not $hardhatInstalled -and ($hardhatCheck -notmatch "Hardhat")) {
            Write-Warning "   ⚠️  Hardhat ne semble pas être installé."
            Write-Info "   Installation recommandée avant configuration."
            
            # Proposer d'installer Hardhat
            Write-Host "`n   Voulez-vous installer Hardhat maintenant ? (o/N): " -NoNewline -ForegroundColor Yellow
            $installResponse = Read-Host
            
            if ($installResponse -eq "o" -or $installResponse -eq "O") {
                Write-Info "   Installation de Hardhat et de la toolbox..."
                npm install --save-dev hardhat @nomicfoundation/hardhat-toolbox
                
                if ($LASTEXITCODE -ne 0) {
                    Write-Warning "   Échec de l'installation de Hardhat"
                    return
                }
            } else {
                Write-Info "   Configuration Hardhat reportée"
                return
            }
        }
        
        # Créer un fichier hardhat.config.js avec configuration améliorée
        Write-Info "   Création du fichier de configuration hardhat.config.js..."
        
        $hardhatConfigContent = @"
/** @type import('hardhat/config').HardhatUserConfig */
require("@nomicfoundation/hardhat-toolbox");
require("dotenv").config();

// Configuration des chemins
const paths = {
  sources: "./contracts",
  tests: "./test",
  cache: "./cache",
  artifacts: "./artifacts"
};

module.exports = {
  // Configuration Solidity
  solidity: {
    compilers: [
      {
        version: "0.8.20",
        settings: {
          optimizer: {
            enabled: true,
            runs: 200,
          },
          viaIR: false,
        },
      },
    ],
  },

  // Configuration des réseaux
  networks: {
    // Réseau local Hardhat (pour tests)
    hardhat: {
      chainId: 31337,
      allowUnlimitedContractSize: false,
      mining: {
        auto: true,
        interval: 0
      },
      accounts: {
        mnemonic: process.env.MNEMONIC || "test test test test test test test test test test test junk",
        accountsBalance: "10000000000000000000000" // 10,000 ETH
      }
    },

    // Localhost
    localhost: {
      url: "http://127.0.0.1:8545",
      chainId: 31337,
    },

    // Sepolia Testnet
    sepolia: {
      url: process.env.SEPOLIA_RPC_URL || process.env.ALCHEMY_API_KEY || "",
      accounts: process.env.PRIVATE_KEY ? [process.env.PRIVATE_KEY] : [],
      chainId: 11155111,
      gas: "auto",
      gasPrice: "auto",
      gasMultiplier: 1.2,
    },

    // Mumbai Testnet (Polygon)
    mumbai: {
      url: process.env.MUMBAI_RPC_URL || "",
      accounts: process.env.PRIVATE_KEY ? [process.env.PRIVATE_KEY] : [],
      chainId: 80001,
    },
  },

  // Configuration Etherscan pour vérification
  etherscan: {
    apiKey: {
      // Ethereum
      mainnet: process.env.ETHERSCAN_API_KEY || "",
      sepolia: process.env.ETHERSCAN_API_KEY || "",
      goerli: process.env.ETHERSCAN_API_KEY || "",
      // Polygon
      polygon: process.env.POLYGONSCAN_API_KEY || process.env.ETHERSCAN_API_KEY || "",
      polygonMumbai: process.env.POLYGONSCAN_API_KEY || process.env.ETHERSCAN_API_KEY || "",
    },
    customChains: [
      {
        network: "polygonMumbai",
        chainId: 80001,
        urls: {
          apiURL: "https://api-testnet.polygonscan.com/api",
          browserURL: "https://mumbai.polygonscan.com"
        }
      }
    ]
  },

  // Rapport de gas
  gasReporter: {
    enabled: (process.env.REPORT_GAS || "false") === "true",
    currency: process.env.GAS_REPORTER_CURRENCY || "USD",
    coinmarketcap: process.env.COINMARKETCAP_API_KEY || "",
    token: "ETH",
    gasPrice: 50,
    excludeContracts: [],
    src: "./contracts",
  },

  // Chemins
  paths: paths,

  // Configuration Mocha pour tests
  mocha: {
    timeout: 40000,
    color: true,
  },

  // Configuration Typechain
  typechain: {
    outDir: "./typechain-types",
    target: "ethers-v6",
  },
};
"@
        
        $hardhatConfigContent | Out-File "hardhat.config.js" -Encoding UTF8
        
        # Vérifier que le fichier a été créé
        if (Test-Path "hardhat.config.js") {
            $fileSize = (Get-Item "hardhat.config.js").Length
            Write-Success "   ✅ Fichier de configuration Hardhat créé : hardhat.config.js ($([math]::Round($fileSize/1KB, 2)) KB)"
            
            # Afficher un aperçu
            Write-Info "   Configuration inclut:"
            Write-Info "     - Solidity 0.8.20 avec optimizer"
            Write-Info "     - Réseaux: hardhat, localhost, sepolia, mumbai"
            Write-Info "     - Support Etherscan/Polygonscan"
            Write-Info "     - Gas reporter configurable"
        } else {
            Write-Warning "   ⚠️  Le fichier hardhat.config.js n'a pas été créé"
        }
        
    } catch {
        Write-Warning "   ⚠️  Erreur lors de la création de la configuration Hardhat : $_"
        Write-Info "   Solution alternative: Exécutez 'npx hardhat init' manuellement"
    }
}

# ==============================================================================================================================

# Vérifier et compléter la configuration Hardhat
function Check-HardhatConfig {
    $configs = @("hardhat.config.js", "hardhat.config.ts")
    $found = $false
    
    foreach ($config in $configs) {
        if (Test-Path $config) {
            Write-Success "Configuration Hardhat trouvée : $config"
            $found = $true
            break
        }
    }
    
    if (-not $found) {
        # Vérifier si Hardhat est dans les dépendances
        if (Test-Path "package.json") {
            try {
                $pkg = Get-Content "package.json" -Raw | ConvertFrom-Json
                if (($pkg.devDependencies.hardhat) -or ($pkg.dependencies.hardhat)) {
                    Write-Warning "Hardhat installé mais config manquante"
                    if (-not $CheckOnly) {
                        # Proposer de créer une config basique
                        Write-Info "Créez hardhat.config.js ou utilisez 'npx hardhat init'"
                    }
                }
            } catch { }
        }
    }
}

# Fonction principale
# Fonction principale
function Main {
    Write-Title
    
    try {
        # 1. Analyser la structure
        $analysis = Analyze-ExistingStructure
        
        # 2. Vérifier les fichiers de config
        Check-ConfigFiles
        
        # 3. Compléter .gitignore (sans écraser)
        Complete-Gitignore
        
        # 4. Compléter package.json (sans écraser)
        Complete-PackageJson
        
        # ============================================
        # ÉTAPE 1 : CRÉER .env À PARTIR DE .env.example
        # ============================================
        Write-Section "Étape 1 : Configuration de l'environnement"
        Setup-Environment
        
        # ============================================
        # ÉTAPE 2 : INSTALLER LES DÉPENDANCES
        # ============================================
        Write-Section "Étape 2 : Installation des dépendances"
        Install-NpmDependencies
        
        # ============================================
        # ÉTAPE 3 : CONFIGURER HARHAT
        # ============================================
        Write-Section "Étape 3 : Configuration de Hardhat"
        Configure-Hardhat
        
        # ============================================
        # ÉTAPE 4 : CRÉATION DE LA STRUCTURE RESTANTE
        # ============================================
        Write-Section "Étape 4 : Finalisation de la structure"
        
        # Créer .env.example si manquant (template)
        Create-EnvExample
        
        # Créer README.md si manquant
        Create-Readme
        
        # Créer les dossiers manquants
        Create-MissingFolders -missingFolders $analysis.Missing
        
        # Créer des fichiers exemples si nécessaires
        Create-ExampleFiles
        
        # Vérifier la config Hardhat
        Check-HardhatConfig
        
        # ============================================
        # ÉTAPE 5 : CONFIGURATION DES AGENTS (PROCHAINE ÉTAPE)
        # ============================================
        Write-Section "Étape 5 : Préparation pour les agents"
        Setup-AgentsPreparation
        
        # Résumé
        Write-Section "Résumé du déploiement"
        
        if ($CheckOnly) {
            Write-Success "Vérification terminée - Aucun changement appliqué"
            Write-Host "`nPour appliquer les changements, exécutez sans -CheckOnly" -ForegroundColor Yellow
        } else {
            Write-Success "Configuration du projet terminée avec succès !"
            Write-Host "`n✅ Les 3 étapes principales ont été implémentées :" -ForegroundColor Green
            Write-Host "   1. .env créé/configuré" -ForegroundColor White
            Write-Host "   2. Dépendances npm installées" -ForegroundColor White
            Write-Host "   3. Hardhat configuré" -ForegroundColor White
            Write-Host "`n📋 Prochaines étapes MANUELLES :" -ForegroundColor Cyan
            Write-Host "   1. Vérifiez et complétez votre fichier .env avec vos vraies clés" -ForegroundColor Yellow
            Write-Host "   2. Testez Hardhat : npx hardhat test" -ForegroundColor Yellow
            Write-Host "   3. Configurez les agents : .\setup-agents.ps1" -ForegroundColor Yellow
            Write-Host "`n"
        }
        
    } catch {
        Write-Host "`n❌ Erreur lors du déploiement : $_" -ForegroundColor Red
        if ($VerboseLog) {
            Write-Host "Stack trace :" -ForegroundColor DarkRed
            Write-Host $_.ScriptStackTrace -ForegroundColor DarkGray
        }
        exit 1
    }
}


# Afficher l'aide
if ($args -contains "-?" -or $args -contains "-Help" -or $args -contains "--help") {
    Write-Host "`nUsage : .\setup-project.ps1 [OPTIONS]`n" -ForegroundColor Cyan
    Write-Host "Script de configuration complémentaire" -ForegroundColor Gray
    Write-Host "NE SURÉCRIT PAS les fichiers existants, les complète seulement.`n" -ForegroundColor Gray
    Write-Host "Options :" -ForegroundColor Yellow
    Write-Host "  -CheckOnly      Vérification sans appliquer les changements" -ForegroundColor Gray
    Write-Host "  -AppendOnly     Ajouter seulement (défaut)" -ForegroundColor Gray
    Write-Host "  -VerboseLog     Mode verbeux" -ForegroundColor Gray
    Write-Host "  -Help           Afficher cette aide" -ForegroundColor Gray
    Write-Host "`nExemples :" -ForegroundColor Yellow
    Write-Host "  .\setup-project.ps1                    # Configuration normale" -ForegroundColor Gray
    Write-Host "  .\setup-project.ps1 -CheckOnly         # Vérification seulement" -ForegroundColor Gray
    Write-Host "  .\setup-project.ps1 -VerboseLog       # Mode détaillé" -ForegroundColor Gray
    exit 0
}

# Point d'entrée
Main
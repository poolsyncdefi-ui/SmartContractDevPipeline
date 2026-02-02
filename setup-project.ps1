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
        
        # 5. Créer .env.example si manquant
        Create-EnvExample
        
        # 6. Créer README.md si manquant
        Create-Readme
        
        # 7. Créer les dossiers manquants
        Create-MissingFolders -missingFolders $analysis.Missing
        
        # 8. Créer des fichiers exemples si nécessaires
        Create-ExampleFiles
        
        # 9. Vérifier la config Hardhat
        Check-HardhatConfig
        
        # Résumé
        Write-Section "Résumé"
        
        if ($CheckOnly) {
            Write-Success "Vérification terminée - Aucun changement appliqué"
            Write-Host "`nPour appliquer les changements, exécutez sans -CheckOnly" -ForegroundColor Yellow
        } else {
            Write-Success "Configuration complémentaire terminée !"
            Write-Host "`nAucun fichier existant n'a été écrasé." -ForegroundColor Green
        }
        
        Write-Host "`n📋 Prochaines étapes :" -ForegroundColor Cyan
        Write-Host "  1. Vérifiez .env.example et créez .env si nécessaire" -ForegroundColor White
        Write-Host "  2. Installez les dépendances : npm install" -ForegroundColor White
        Write-Host "  3. Configurez les agents : .\setup-agents.ps1" -ForegroundColor White
        Write-Host "  4. Développez vos contrats dans contracts/" -ForegroundColor White
        Write-Host "`n"
        
    } catch {
        Write-Host "`n❌ Erreur : $_" -ForegroundColor Red
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
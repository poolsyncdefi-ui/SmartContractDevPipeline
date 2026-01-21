# setup-project.ps1 - Version corrigée
Write-Host "=== SETUP COMPLET DU PROJET SMART CONTRACT PIPELINE ===" -ForegroundColor Cyan
Write-Host ""

# 1. Vérifier et installer les prérequis
Write-Host "1. INSTALLATION DES PREREQUIS..." -ForegroundColor Yellow
if (-not (Test-Path ".\install-prerequis.ps1")) {
    Write-Host "❌ Script install-prerequis.ps1 non trouvé" -ForegroundColor Red
    exit 1
}
powershell -ExecutionPolicy Bypass -File .\install-prerequis.ps1

# 2. Attendre que l'utilisateur redémarre PowerShell si nécessaire
Write-Host "`n2. VERIFICATION DE L'INSTALLATION..." -ForegroundColor Yellow
Read-Host "Si on vous a demandé de redémarrer PowerShell, faites-le maintenant. Appuyez sur Entrée pour continuer"

# 3. Installer les outils blockchain
Write-Host "`n3. INSTALLATION DES OUTILS BLOCKCHAIN..." -ForegroundColor Yellow
if (Test-Path ".\install-blockchain.ps1") {
    powershell -ExecutionPolicy Bypass -File .\install-blockchain.ps1
} else {
    Write-Host "⚠️  Script install-blockchain.ps1 non trouvé, installation manuelle..." -ForegroundColor Yellow
}

# 4. Initialiser Hardhat dans le dossier workspace/contracts
Write-Host "`n4. INITIALISATION HARPHAT..." -ForegroundColor Yellow
$contractsDir = ".\workspace\contracts"
if (-not (Test-Path $contractsDir)) {
    New-Item -ItemType Directory -Path $contractsDir -Force | Out-Null
}

Set-Location $contractsDir

# Vérifier si Hardhat est installé
try {
    npx hardhat --version 2>&1 | Out-Null
    Write-Host "✅ Hardhat est installé" -ForegroundColor Green
} catch {
    Write-Host "❌ Hardhat non installé, installation..." -ForegroundColor Red
    npm init -y
    npm install --save-dev hardhat
}

# Initialiser un projet Hardhat
if (-not (Test-Path "hardhat.config.js") -and -not (Test-Path "hardhat.config.ts")) {
    Write-Host "Initialisation d'un nouveau projet Hardhat..." -ForegroundColor Gray
    npx hardhat init --typescript
    
    # Ajouter des dépendances supplémentaires
    npm install --save-dev @nomicfoundation/hardhat-toolbox @typechain/hardhat typechain @typechain/ethers-v6 @openzeppelin/contracts dotenv
    npm install ethers
} else {
    Write-Host "✅ Projet Hardhat déjà initialisé" -ForegroundColor Green
}

# Retour au dossier principal
Set-Location ..\..

# 5. Créer la structure du projet
Write-Host "`n5. CREATION DE LA STRUCTURE DU PROJET..." -ForegroundColor Yellow
if (Test-Path ".\setup-structure.ps1") {
    powershell -ExecutionPolicy Bypass -File .\setup-structure.ps1
} else {
    # Créer la structure de base
    $folders = @(
        "agents",
        "agents\architect",
        "agents\coder", 
        "agents\communication",
        "agents\documenter",
        "agents\formal_verification",
        "agents\frontend_web3",
        "agents\fuzzing_simulation", 
        "agents\quality_metrics",
        "agents\smart_contract",
        "agents\tester",
        "agents\orchestrator",
        "agents\shared",
        "config",
        "context",
        "memory",
        "memory\vector_store",
        "memory\history", 
        "memory\learnings",
        "workspace",
        "workspace\contracts",
        "workspace\frontend",
        "sprints",
        "reports",
        "logs",
        "scripts",
        "tests"
    )
    
    foreach ($folder in $folders) {
        New-Item -ItemType Directory -Path $folder -Force | Out-Null
        Write-Host "  📁 $folder" -ForegroundColor Gray
    }
}

# 6. Créer les fichiers de base
Write-Host "`n6. CREATION DES FICHIERS DE BASE..." -ForegroundColor Yellow

# package.json principal
$packageJson = @'
{
  "name": "smart-contract-pipeline",
  "version": "1.0.0",
  "description": "Pipeline automatisé de développement Smart Contract avec agents IA",
  "main": "index.js",
  "scripts": {
    "start": "python main.py",
    "test": "python -m pytest",
    "setup": "powershell -ExecutionPolicy Bypass -File .\\setup-project.ps1",
    "deploy-agents": "powershell -ExecutionPolicy Bypass -File .\\deploy-all-agents.ps1",
    "deploy-subagents": "powershell -ExecutionPolicy Bypass -File .\\deploy-subagents.ps1",
    "test-all": "python test_all_agents.py",
    "hardhat": "cd workspace\\contracts && npx hardhat",
    "frontend": "cd workspace\\frontend && npm run dev"
  },
  "keywords": ["blockchain", "smart-contract", "ai", "automation", "web3"],
  "author": "SmartContractPipeline",
  "license": "MIT",
  "dependencies": {},
  "devDependencies": {}
}
'@

$packageJson | Out-File -FilePath "package.json" -Force -Encoding UTF8

# requirements.txt
$requirements = @'
# Core AI & ML
langchain==0.1.0
langgraph==0.0.5
chromadb==0.4.18
openai==1.6.1

# Web3 & Blockchain
web3==6.11.1
eth-account==0.11.0

# Web Framework & API
fastapi==0.104.1
uvicorn[standard]==0.24.0
requests==2.31.0
aiohttp==3.9.1

# Data Processing
pandas==2.1.4
numpy==1.26.2
pyyaml==6.0.1
python-dotenv==1.0.0

# Utilities
pydantic==2.5.0
pytest==7.4.3
pytest-asyncio==0.21.1
black==23.11.0
flake8==6.1.0
'@

$requirements | Out-File -FilePath "requirements.txt" -Force -Encoding UTF8

# 7. Créer l'environnement virtuel Python
Write-Host "`n7. CREATION ENVIRONNEMENT VIRTUEL PYTHON..." -ForegroundColor Yellow
if (-not (Test-Path ".venv")) {
    python -m venv .venv
    Write-Host "✅ Environnement virtuel créé" -ForegroundColor Green
} else {
    Write-Host "✅ Environnement virtuel déjà existant" -ForegroundColor Green
}

# 8. Installer les dépendances Python
Write-Host "`n8. INSTALLATION DEPENDANCES PYTHON..." -ForegroundColor Yellow
& .\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt

# 9. Tester l'installation
Write-Host "`n9. TEST DE L'INSTALLATION..." -ForegroundColor Yellow
try {
    python -c "import web3; print('✅ Web3 installé:', web3.__version__)"
    python -c "import langchain; print('✅ LangChain installé')"
    Write-Host "✅ Toutes les dépendances Python sont installées" -ForegroundColor Green
} catch {
    Write-Host "❌ Erreur lors du test des dépendances Python: $_" -ForegroundColor Red
}

# 10. Message final
Write-Host "`n" + "="*60 -ForegroundColor Cyan
Write-Host "🎉 SETUP DU PROJET COMPLETE AVEC SUCCES !" -ForegroundColor Green
Write-Host "="*60 -ForegroundColor Cyan
Write-Host ""
Write-Host "📁 STRUCTURE CREEE:" -ForegroundColor Yellow
Get-ChildItem -Path . -Directory | ForEach-Object { Write-Host "  • $($_.Name)" -ForegroundColor White }
Write-Host ""
Write-Host "⚡ COMMANDES DISPONIBLES:" -ForegroundColor Yellow
Write-Host "  npm run setup           - Réexécuter le setup" -ForegroundColor White
Write-Host "  npm run deploy-agents   - Déployer tous les agents" -ForegroundColor White
Write-Host "  npm run test-all        - Tester tous les agents" -ForegroundColor White
Write-Host "  npm run hardhat         - Lancer Hardhat" -ForegroundColor White
Write-Host ""
Write-Host "📝 PROCHAINES ETAPES:" -ForegroundColor Yellow
Write-Host "  1. Déployer les agents: npm run deploy-agents" -ForegroundColor White
Write-Host "  2. Tester le système: npm run test-all" -ForegroundColor White
Write-Host "  3. Personnaliser la configuration dans config/" -ForegroundColor White
Write-Host ""
Write-Host "✅ PRET A DEVELOPPER DES SMART CONTRATS AVEC IA !" -ForegroundColor Green
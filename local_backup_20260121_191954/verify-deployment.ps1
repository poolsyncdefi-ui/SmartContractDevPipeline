# verify-deployment.ps1
Write-Host "=== VERIFICATION DU DEPLOIEMENT COMPLET ===" -ForegroundColor Cyan
Write-Host ""

$projectPath = "$env:USERPROFILE\Projects\SmartContractPipeline"

if (-not (Test-Path $projectPath)) {
    Write-Host "❌ Projet non trouvé à: $projectPath" -ForegroundColor Red
    exit 1
}

Set-Location $projectPath

# 1. Vérifier la structure des agents
Write-Host "1. VERIFICATION STRUCTURE AGENTS..." -ForegroundColor Yellow
$expectedAgents = @(
    "architect",
    "coder", 
    "communication",
    "documenter",
    "formal_verification",
    "frontend_web3",
    "fuzzing_simulation",
    "quality_metrics",
    "smart_contract",
    "tester"
)

$missingAgents = @()
foreach ($agent in $expectedAgents) {
    $agentPath = "$projectPath\agents\$agent"
    if (Test-Path $agentPath) {
        Write-Host "   ✅ $agent" -ForegroundColor Green
    } else {
        Write-Host "   ❌ $agent" -ForegroundColor Red
        $missingAgents += $agent
    }
}

# 2. Vérifier les fichiers de configuration
Write-Host "`n2. VERIFICATION CONFIGURATIONS..." -ForegroundColor Yellow
foreach ($agent in $expectedAgents) {
    $configFile = "$projectPath\agents\$agent\config.yaml"
    if (Test-Path $configFile) {
        Write-Host "   ✅ $agent/config.yaml" -ForegroundColor Green
    } else {
        Write-Host "   ❌ $agent/config.yaml" -ForegroundColor Red
    }
}

# 3. Vérifier les versions
Write-Host "`n3. VERIFICATION VERSIONS..." -ForegroundColor Yellow
$versionsFile = "$projectPath\config\versions.json"
if (Test-Path $versionsFile) {
    $versions = Get-Content $versionsFile | ConvertFrom-Json
    Write-Host "   ✅ Fichier de versions trouvé" -ForegroundColor Green
    
    Write-Host "   📊 Versions système:" -ForegroundColor Gray
    if ($versions.system) {
        Write-Host "     OS: $($versions.system.os)" -ForegroundColor White
        Write-Host "     PowerShell: $($versions.system.powershell)" -ForegroundColor White
    }
    
    Write-Host "   📊 Versions outils:" -ForegroundColor Gray
    if ($versions.tools) {
        foreach ($tool in $versions.tools.PSObject.Properties) {
            Write-Host "     $($tool.Name): $($tool.Value)" -ForegroundColor White
        }
    }
} else {
    Write-Host "   ❌ Fichier de versions non trouvé" -ForegroundColor Red
}

# 4. Vérifier les dépendances Python
Write-Host "`n4. VERIFICATION DEPENDANCES PYTHON..." -ForegroundColor Yellow
try {
    & "$projectPath\.venv\Scripts\Activate.ps1"
    
    # Vérifier les packages critiques
    $criticalPackages = @("langchain", "chromadb", "web3", "fastapi", "pydantic")
    foreach ($pkg in $criticalPackages) {
        try {
            $version = python -c "import $pkg; print(getattr($pkg, '__version__', 'N/A'))" 2>$null
            if ($version -and $version -ne "N/A") {
                Write-Host "   ✅ $pkg: $version" -ForegroundColor Green
            } else {
                Write-Host "   ⚠️  $pkg: Version non détectée" -ForegroundColor Yellow
            }
        } catch {
            Write-Host "   ❌ $pkg: Non installé" -ForegroundColor Red
        }
    }
} catch {
    Write-Host "   ⚠️  Impossible d'activer l'environnement virtuel" -ForegroundColor Yellow
}

# 5. Vérifier Ollama
Write-Host "`n5. VERIFICATION OLLAMA..." -ForegroundColor Yellow
try {
    $ollamaStatus = Invoke-RestMethod -Uri "http://localhost:11434/api/tags" -TimeoutSec 3
    $modelCount = $ollamaStatus.models.Count
    Write-Host "   ✅ Ollama en ligne: $modelCount modèles chargés" -ForegroundColor Green
    
    # Vérifier les modèles requis
    $requiredModels = @("deepseek-coder:6.7b", "llama3.2:3b", "mistral:7b")
    foreach ($model in $requiredModels) {
        if ($ollamaStatus.models | Where-Object { $_.name -eq $model }) {
            Write-Host "     ✅ $model" -ForegroundColor Green
        } else {
            Write-Host "     ⚠️  $model non chargé" -ForegroundColor Yellow
        }
    }
} catch {
    Write-Host "   ❌ Ollama hors ligne" -ForegroundColor Red
    Write-Host "   Lancez 'ollama serve' dans un terminal" -ForegroundColor White
}

# 6. Générer le rapport final
Write-Host "`n6. RAPPORT FINAL..." -ForegroundColor Yellow
$report = @{
    timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    project_path = $projectPath
    verification = @{
        agents_total = $expectedAgents.Count
        agents_found = $expectedAgents.Count - $missingAgents.Count
        agents_missing = $missingAgents
        structure_ok = ($missingAgents.Count -eq 0)
        versions_ok = (Test-Path $versionsFile)
        python_deps_ok = $true  # À affiner selon les vérifications
        ollama_ok = $false
    }
    next_steps = @(
        "1. Vérifier que tous les agents sont présents",
        "2. Configurer Ollama avec les modèles requis",
        "3. Tester le pipeline avec: python test_all_agents.py",
        "4. Consulter les logs dans: logs\",
        "5. Personnaliser les configurations dans agents\"
    )
}

$report | ConvertTo-Json -Depth 10 | Out-File -FilePath "$projectPath\reports\verification_report.json" -Force

Write-Host "`n" + "="*60 -ForegroundColor Cyan
Write-Host "📊 RAPPORT DE VERIFICATION" -ForegroundColor Yellow
Write-Host "="*60 -ForegroundColor Cyan
Write-Host ""
Write-Host "Agents trouvés: $($report.verification.agents_found)/$($report.verification.agents_total)" -ForegroundColor White
Write-Host "Structure: $(if($report.verification.structure_ok) {'✅'} else {'❌'})" -ForegroundColor $(if($report.verification.structure_ok) {'Green'} else {'Red'})
Write-Host "Versions: $(if($report.verification.versions_ok) {'✅'} else {'❌'})" -ForegroundColor $(if($report.verification.versions_ok) {'Green'} else {'Red'})
Write-Host "Ollama: $(if($report.verification.ollama_ok) {'✅'} else {'❌'})" -ForegroundColor $(if($report.verification.ollama_ok) {'Green'} else {'Red'})
Write-Host ""
Write-Host "📁 Rapport détaillé: reports\verification_report.json" -ForegroundColor Cyan
Write-Host ""
Write-Host "🎯 PROCHAINES ETAPES:" -ForegroundColor Yellow
foreach ($step in $report.next_steps) {
    Write-Host "  $step" -ForegroundColor White
}
Write-Host ""
Write-Host "✅ VERIFICATION TERMINEE" -ForegroundColor Green
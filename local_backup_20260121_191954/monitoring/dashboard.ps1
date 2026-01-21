# dashboard.ps1
function Show-Dashboard {
    Clear-Host
    Write-Host "="*60 -ForegroundColor Cyan
    Write-Host "📊 DASHBOARD PIPELINE SMART CONTRACT" -ForegroundColor Yellow
    Write-Host "="*60 -ForegroundColor Cyan
    Write-Host ""
    
    # 1. Vérifier Ollama
    Write-Host "🤖 AGENTS IA:" -ForegroundColor Green
    try {
        $ollamaStatus = Invoke-RestMethod -Uri "http://localhost:11434/api/tags" -TimeoutSec 2
        Write-Host "  ✅ Ollama: $($ollamaStatus.models.count) modèles chargés" -ForegroundColor White
    } catch {
        Write-Host "  ❌ Ollama: Hors ligne" -ForegroundColor Red
    }
    
    # 2. Vérifier Anvil
    Write-Host "`n⛓️  BLOCKCHAIN:" -ForegroundColor Green
    try {
        $blockchainStatus = Invoke-RestMethod -Uri "http://localhost:8545" -Method Post -Body '{"jsonrpc":"2.0","method":"eth_blockNumber","params":[],"id":1}' -TimeoutSec 2
        Write-Host "  ✅ Anvil: En ligne (Port 8545)" -ForegroundColor White
    } catch {
        Write-Host "  ❌ Anvil: Hors ligne" -ForegroundColor Red
    }
    
    # 3. Vérifier Frontend
    Write-Host "`n🎨 FRONTEND:" -ForegroundColor Green
    try {
        $frontendStatus = Invoke-WebRequest -Uri "http://localhost:3000" -TimeoutSec 2
        Write-Host "  ✅ Frontend: En ligne (Port 3000)" -ForegroundColor White
    } catch {
        Write-Host "  ❌ Frontend: Hors ligne" -ForegroundColor Red
    }
    
    # 4. Afficher les derniers rapports
    Write-Host "`n📈 RAPPORTS RECENTS:" -ForegroundColor Green
    $reports = Get-ChildItem "$env:USERPROFILE\Projects\SmartContractPipeline\reports\*.json" | Sort-Object LastWriteTime -Descending | Select-Object -First 3
    
    foreach ($report in $reports) {
        $content = Get-Content $report.FullName | ConvertFrom-Json
        $date = [DateTime]::Parse($content.timestamp)
        Write-Host "  📄 $($report.Name) - $($date.ToString('HH:mm'))" -ForegroundColor Gray
    }
    
    # 5. Statistiques des agents
    Write-Host "`n📊 STATISTIQUES:" -ForegroundColor Green
    if (Test-Path "$env:USERPROFILE\Projects\SmartContractPipeline\workspace\contracts\results\contract_output.json") {
        $contractData = Get-Content "$env:USERPROFILE\Projects\SmartContractPipeline\workspace\contracts\results\contract_output.json" | ConvertFrom-Json
        Write-Host "  📝 Contrats générés: 1" -ForegroundColor White
        Write-Host "  ✅ Tests: $($contractData.tests.success)" -ForegroundColor White
    }
    
    # 6. Menu interactif
    Write-Host "`n" + "="*60 -ForegroundColor Cyan
    Write-Host "🔧 MENU INTERACTIF" -ForegroundColor Yellow
    Write-Host "1. Redémarrer le pipeline"
    Write-Host "2. Voir les logs"
    Write-Host "3. Générer un nouveau contrat"
    Write-Host "4. Arrêter le système"
    Write-Host "Q. Quitter"
    Write-Host "="*60 -ForegroundColor Cyan
    
    $choice = Read-Host "`nChoix"
    
    switch ($choice) {
        "1" { .\run-pipeline.ps1 }
        "2" { 
            Get-Content "$env:USERPROFILE\Projects\SmartContractPipeline\reports\health_monitor.json" | Write-Host
            Read-Host "Appuyez sur Entrée pour continuer"
            Show-Dashboard
        }
        "3" { 
            .\deploy-agents.ps1
            Show-Dashboard
        }
        "4" { .\stop-all.ps1 }
        "Q" { exit }
        default { Show-Dashboard }
    }
}

Show-Dashboard
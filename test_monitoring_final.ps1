# test_monitoring_final.ps1
Write-Host "="*60 -ForegroundColor Cyan
Write-Host "🧪 TEST DE L'AGENT MONITORING" -ForegroundColor Cyan
Write-Host "="*60 -ForegroundColor Cyan

# Configuration
$ProjectRoot = "D:\Web3Projects\SmartContractDevPipeline"
$ReportsPath = "$ProjectRoot\reports\monitoring"

# 1. Vérifier que le dossier reports existe
if (-not (Test-Path $ReportsPath)) {
    New-Item -ItemType Directory -Path $ReportsPath -Force | Out-Null
    Write-Host "✅ Dossier créé: $ReportsPath" -ForegroundColor Green
}

# 2. Tester l'import
Write-Host "`n📋 Test d'import..." -ForegroundColor Yellow
python -c @"
import sys
sys.path.insert(0, r'$ProjectRoot')
try:
    from agents.monitoring.agent import MonitoringAgent
    print('✅ Agent importé')
    from reports.monitoring.dashboard_generator import DashboardGenerator
    print('✅ Générateur importé')
except Exception as e:
    print(f'❌ Erreur: {e}')
"@

# 3. Exécution complète
Write-Host "`n📋 Exécution de l'agent..." -ForegroundColor Yellow

$tempFile = [System.IO.Path]::GetTempFileName() -replace '\.tmp$','.py'
@"
import sys
import asyncio
sys.path.insert(0, r'$ProjectRoot')
from agents.monitoring.agent import MonitoringAgent

async def run():
    agent = MonitoringAgent()
    print('⏳ Initialisation...')
    await agent.initialize()
    print(f'✅ Agent initialisé - Statut: {agent.status}')
    
    print('📊 Génération du dashboard...')
    dashboard = await agent.generate_dashboard()
    print(f'✅ Dashboard: {dashboard}')
    
    print('🛑 Arrêt...')
    await agent.shutdown()
    return dashboard

loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)
result = loop.run_until_complete(run())
print(f'\n🎉 SUCCÈS - Dashboard: {result}')
"@ | Out-File -FilePath $tempFile -Encoding UTF8

python $tempFile
Remove-Item $tempFile -Force

# 4. Afficher le résultat
$latest = Get-ChildItem -Path $ReportsPath -Filter "command_center_*.html" | Sort-Object LastWriteTime -Descending | Select-Object -First 1
if ($latest) {
    Write-Host "`n📄 Dashboard: $($latest.Name)" -ForegroundColor Green
    Write-Host "📏 Taille: $([math]::Round($latest.Length/1KB, 2)) KB" -ForegroundColor Green
}

Write-Host "`n" + "="*60 -ForegroundColor Cyan

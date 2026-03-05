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

# 2. Vérifier l'import du générateur
Write-Host "`n📋 Test 1: Import du DashboardGenerator" -ForegroundColor Yellow
python -c @"
import sys
sys.path.insert(0, r'$ProjectRoot')
try:
    from reports.monitoring.dashboard_generator import DashboardGenerator
    print('✅ DashboardGenerator importé')
except Exception as e:
    print(f'❌ Erreur: {e}')
"@

# 3. Vérifier l'import de l'agent
Write-Host "`n📋 Test 2: Import du MonitoringAgent" -ForegroundColor Yellow
python -c @"
import sys
sys.path.insert(0, r'$ProjectRoot')
try:
    from agents.monitoring.agent import MonitoringAgent
    print('✅ MonitoringAgent importé')
except Exception as e:
    print(f'❌ Erreur: {e}')
"@

# 4. Test complet avec fichier temporaire
Write-Host "`n📋 Test 3: Exécution complète" -ForegroundColor Yellow

$tempFile = [System.IO.Path]::GetTempFileName() -replace '\.tmp$','.py'
@"
import sys
import asyncio
from pathlib import Path

sys.path.insert(0, r'$ProjectRoot')

try:
    from agents.monitoring.agent import MonitoringAgent
    print('✅ Agent importé')
    
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
    
except Exception as e:
    print(f'❌ ERREUR: {e}')
    import traceback
    traceback.print_exc()
"@ | Out-File -FilePath $tempFile -Encoding UTF8

python $tempFile
Remove-Item $tempFile -Force

Write-Host "`n" + "="*60 -ForegroundColor Cyan
# stop-all.ps1
Write-Host "=== ARRET DU SYSTEME ===" -ForegroundColor Cyan

# Arrêter tous les processus
$processes = @("anvil", "node", "ollama", "python")

foreach ($process in $processes) {
    Write-Host "Arrêt de $process..." -ForegroundColor Yellow
    Get-Process -Name $process -ErrorAction SilentlyContinue | Stop-Process -Force
}

# Sauvegarder l'état
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$backupDir = "$env:USERPROFILE\Projects\SmartContractPipeline\backups\$timestamp"

New-Item -ItemType Directory -Force -Path $backupDir | Out-Null

Copy-Item -Path "$env:USERPROFILE\Projects\SmartContractPipeline\reports\*" -Destination "$backupDir\" -Recurse -Force
Copy-Item -Path "$env:USERPROFILE\Projects\SmartContractPipeline\workspace\contracts\out\*" -Destination "$backupDir\" -Recurse -Force

Write-Host "`n✅ Systeme arrete proprement" -ForegroundColor Green
Write-Host "📁 Backup sauvegarde dans: $backupDir" -ForegroundColor Cyan
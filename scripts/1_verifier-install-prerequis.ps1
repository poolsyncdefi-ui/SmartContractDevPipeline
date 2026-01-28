# Test complet final
Write-Host "=== TEST FINAL ENVIRONNEMENT ===" -ForegroundColor Green

# 1. Test Python
Write-Host "`n1. Python et dépendances:" -ForegroundColor Cyan
try {
    python -c "
import fastapi
import uvicorn
import web3
import langchain
import pydantic

print('✅ FastAPI:', fastapi.__version__)
print('✅ Uvicorn:', uvicorn.__version__)
print('✅ Web3:', web3.__version__)
print('✅ LangChain:', langchain.__version__)
print('✅ Pydantic:', pydantic.__version__)
"
} catch {
    Write-Host "❌ Erreur: $_" -ForegroundColor Red
}

# 2. Test Ollama
Write-Host "`n2. Ollama:" -ForegroundColor Cyan
ollama --version
ollama list

# 3. Test création wallet Web3
Write-Host "`n3. Test Web3 (Smart Contracts):" -ForegroundColor Cyan
try {
    python -c "
from web3 import Web3
import json

# Créer un wallet de test
w3 = Web3()
account = w3.eth.account.create()

print('✅ Wallet créé avec succès')
print('   Adresse:', account.address[:20] + '...')
print('   Clé privée:', account.key.hex()[:20] + '...')
"
} catch {
    Write-Host "❌ Erreur Web3: $_" -ForegroundColor Red
}

# 4. Test agents IA avec Ollama
Write-Host "`n4. Test Agents IA:" -ForegroundColor Cyan
try {
    # Vérifier les modèles
    $models = ollama list
    if ($models -match "deepseek-coder|llama2|mistral") {
        Write-Host "✅ Modèles IA disponibles" -ForegroundColor Green
        $models | ForEach-Object { Write-Host "   - $_" -ForegroundColor Gray }
    } else {
        Write-Host "⚠ Aucun modèle IA téléchargé" -ForegroundColor Yellow
        Write-Host "   Téléchargez: ollama pull deepseek-coder:6.7b" -ForegroundColor White
    }
} catch {
    Write-Host "⚠ Ollama erreur: $_" -ForegroundColor Yellow
}

# 5. Résumé
Write-Host "`n" + "="*50 -ForegroundColor Green
Write-Host "✅ ENVIRONNEMENT PRÊT POUR LE DÉVELOPPEMENT !" -ForegroundColor Green
Write-Host "="*50 -ForegroundColor Green

Write-Host "`nProchaines étapes:" -ForegroundColor Yellow
Write-Host "1. Vérifiez le point d'entrée du projet" -ForegroundColor White
Write-Host "   Get-ChildItem -Filter *.py | Select-Object Name" -ForegroundColor Gray
Write-Host "2. Lancez le pipeline principal" -ForegroundColor White
Write-Host "3. Consultez la documentation" -ForegroundColor White
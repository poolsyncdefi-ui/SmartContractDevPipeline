# diagnostic_coder.ps1
Write-Host "🔍 DIAGNOSTIC CODER AGENT" -ForegroundColor Cyan
Write-Host "==========================" -ForegroundColor Cyan

# 1. Structure
Write-Host "`n1. STRUCTURE DES FICHIERS:" -ForegroundColor Yellow
Write-Host "agents/coder/:" -ForegroundColor Gray
ls agents/coder/ | Format-Table Name, Length, LastWriteTime

# 2. Contenu config.yaml
Write-Host "`n2. CONFIG YAML:" -ForegroundColor Yellow
if (Test-Path agents/coder/config.yaml) {
    $config = Get-Content agents/coder/config.yaml -Raw
    Write-Host "Contenu:" -ForegroundColor Gray
    $config
} else {
    Write-Host "❌ config.yaml non trouvé" -ForegroundColor Red
}

# 3. Contenu __init__.py
Write-Host "`n3. __INIT__.PY:" -ForegroundColor Yellow
if (Test-Path agents/coder/__init__.py) {
    Get-Content agents/coder/__init__.py
} else {
    Write-Host "⚠ __init__.py manquant" -ForegroundColor Yellow
    "@"
from .coder import CoderAgent

__all__ = ['CoderAgent']
"@" | Out-File agents/coder/__init__.py -Encoding UTF8
    Write-Host "✓ __init__.py créé" -ForegroundColor Green
}

# 4. Test Python
Write-Host "`n4. TEST PYTHON:" -ForegroundColor Yellow

$testScript = @"
import sys
import os

print("Python sys.path:")
for p in sys.path[:3]:
    print(f"  {p}")

print("\nContenu agents.coder:")
try:
    import agents.coder
    print(f"  ✓ Module importé")
    print(f"  Attributs: {dir(agents.coder)}")
except ImportError as e:
    print(f"  ❌ Erreur: {e}")

print("\nImport direct:")
try:
    # Essayer différents noms
    try:
        from agents.coder.coder import CoderAgent
        print("  ✓ Import depuis coder.py")
    except ImportError:
        try:
            from agents.coder.agent import CoderAgent
            print("  ✓ Import depuis agent.py")
        except ImportError:
            try:
                from agents.coder.coder_agent import CoderAgent
                print("  ✓ Import depuis coder_agent.py")
            except ImportError as e:
                print(f"  ❌ Aucun import ne fonctionne: {e}")
except Exception as e:
    print(f"  ❌ Erreur générale: {e}")
"@

$testScript | python

# 5. Recommandation
Write-Host "`n5. RECOMMANDATION:" -ForegroundColor Green
Write-Host "Si le fichier s'appelle coder.py mais la config dit 'agent':" -ForegroundColor White
Write-Host "1. Soit renommer coder.py → agent.py" -ForegroundColor White
Write-Host "2. Soit modifier config.yaml: module_path: 'agents.coder.coder'" -ForegroundColor White
Write-Host "`nExécutez:" -ForegroundColor Yellow
Write-Host "   python .\diagnostic_coder.ps1" -ForegroundColor White
#!/usr/bin/env python3
"""
Script de démarrage du pipeline
"""
import subprocess
import sys

print("🚀 DÉMARRAGE SMART CONTRACT PIPELINE")
print("=" * 60)

def run_command(cmd, description):
    """Exécute une commande"""
    print(f"
{description}...")
    print(f"Commande: {cmd}")
    
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ Succès")
            if result.stdout:
                print(f"Sortie: {result.stdout[:200]}...")
            return True
        else:
            print(f"❌ Échec (code: {result.returncode})")
            if result.stderr:
                print(f"Erreur: {result.stderr[:200]}...")
            return False
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False

# 1. Tester l'orchestrateur
print("
1. Test de l'orchestrateur...")
success = run_command(
    f'"{sys.executable}" orchestrator/orchestrator.py --test',
    "Test de santé de l'orchestrateur"
)

if success:
    print("
" + "=" * 60)
    print("🎉 PIPELINE OPÉRATIONNEL !")
    print("=" * 60)
    
    print("
Commandes disponibles:")
    print("• Test de santé:    python orchestrator/orchestrator.py --test")
    print("• Workflow test:    python orchestrator/orchestrator.py --workflow test")
    print("• Mode interactif:  python orchestrator/orchestrator.py")
    
    print("
Structure déployée:")
    print("• 5 agents principaux (architect, coder, smart_contract, frontend_web3, tester)")
    print("• 17 sous-agents spécialisés")
    print("• Orchestrateur central")
    
else:
    print("
" + "=" * 60)
    print("⚠️  PROBLÈME DÉTECTÉ")
    print("=" * 60)
    
    print("
Solutions:")
    print("1. Vérifiez les dépendances: pip install PyYAML aiohttp")
    print("2. Testez avec: python test_simple.py")
    print("3. Recréez la structure: python deploy_pipeline.py --force")
    
    print("
Test simple:")
    run_command(f'"{sys.executable}" test_simple.py', "Test simple")

print("
" + "=" * 60)

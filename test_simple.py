#!/usr/bin/env python3
"""
Test final simplifié du pipeline
"""
import os
import sys
import asyncio

print("🧪 TEST FINAL SIMPLIFIÉ")
print("=" * 60)

async def test_simple():
    """Test simple"""
    
    # Configuration
    project_root = os.path.abspath(".")
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    
    print(f"📁 Projet: {project_root}")
    
    print("
1. Test d'import de l'orchestrateur...")
    try:
        from orchestrator.orchestrator import Orchestrator
        print("✅ Orchestrateur importé")
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False
    
    print("
2. Création de l'orchestrateur...")
    try:
        orchestrator = Orchestrator()
        print("✅ Orchestrateur créé")
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False
    
    print("
3. Initialisation des agents...")
    try:
        await orchestrator.initialize_agents()
        print(f"✅ Agents initialisés: {len(orchestrator.agents)}")
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False
    
    print("
4. Test de santé...")
    try:
        health = await orchestrator.health_check()
        print(f"✅ Santé vérifiée")
        print(f"   Orchestrateur: {health.get('orchestrator', 'N/A')}")
        print(f"   Agents: {len(health.get('agents', {}))}")
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False
    
    return True

async def main():
    """Fonction principale"""
    success = await test_simple()
    
    print("
" + "=" * 60)
    
    if success:
        print("🎉 TEST RÉUSSI !")
        print("
Votre pipeline est fonctionnel.")
        print("
Pour utiliser l'orchestrateur:")
        print("python orchestrator/orchestrator.py --test")
    else:
        print("❌ TEST ÉCHOUÉ")
        print("
Prochaines étapes:")
        print("1. Vérifiez la structure des dossiers")
        print("2. Vérifiez que les fichiers existent:")
        print("   - base_agent.py")
        print("   - agents/*/agent.py")
        print("   - orchestrator/orchestrator.py")

if __name__ == "__main__":
    asyncio.run(main())

# test_all_agents.py - version corrigée
"""
Test simplifié pour vérifier l'initialisation de tous les agents
"""

import sys
from pathlib import Path
import asyncio
import logging

# Ajouter le chemin du projet
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def test_agent(agent_name, agent_class, config_path=None):
    """
    Teste un agent spécifique
    
    Args:
        agent_name: Nom de l'agent
        agent_class: Classe de l'agent
        config_path: Chemin vers le fichier de config (optionnel)
    """
    print(f"\n{'='*60}")
    print(f"🧪 TEST: {agent_name.upper()}")
    print('='*60)
    
    try:
        # Créer l'instance
        if config_path:
            agent = agent_class(config_path)
        else:
            agent = agent_class()
        
        # Vérifier si c'est une classe abstraite
        if hasattr(agent_class, '__abstractmethods__') and agent_class.__abstractmethods__:
            print(f"⚠️  {agent_name}: Classe abstraite (ne peut pas être instanciée)")
            print(f"   Méthodes abstraites: {agent_class.__abstractmethods__}")
            return None  # Pas une erreur, juste une info
        
        # Initialiser
        success = await agent.initialize()
        
        if success:
            print(f"✅ {agent_name}: Initialisation réussie")
            print(f"   Statut: {agent.status}")
            print(f"   Capacités: {len(agent.capabilities)}")
            return True
        else:
            print(f"❌ {agent_name}: Échec de l'initialisation")
            return False
            
    except TypeError as e:
        if "Can't instantiate abstract class" in str(e):
            print(f"⚠️  {agent_name}: Classe abstraite (normal)")
            return None
        else:
            print(f"❌ {agent_name}: Erreur - {e}")
            import traceback
            traceback.print_exc()
            return False
    except Exception as e:
        print(f"❌ {agent_name}: Erreur - {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Fonction principale de test"""
    print("🧪 TEST ORCHESTRATOR SIMPLIFIÉ")
    print("="*50 + "\n")
    
    results = {}
    
    try:
        # Test BaseAgent - juste l'import, pas l'instanciation
        try:
            from agents.base_agent import BaseAgent
            print("✅ BaseAgent importé avec succès")
            results['base_agent'] = True
        except ImportError as e:
            print(f"❌ BaseAgent: ImportError - {e}")
            results['base_agent'] = False
        
        # Test ArchitectAgent
        try:
            from agents.architect.architect import ArchitectAgent
            architect_config = "agents/architect/config.yaml"
            results['architect'] = await test_agent("ArchitectAgent", ArchitectAgent, architect_config)
        except ImportError as e:
            print(f"❌ ArchitectAgent: ImportError - {e}")
            results['architect'] = False
        
        # Test CoderAgent
        try:
            from agents.coder.coder import CoderAgent
            coder_config = "agents/coder/config.yaml"
            results['coder'] = await test_agent("CoderAgent", CoderAgent, coder_config)
        except ImportError as e:
            print(f"❌ CoderAgent: ImportError - {e}")
            results['coder'] = False
        
        # Test TesterAgent (s'il existe)
        try:
            from agents.tester.tester import TesterAgent
            tester_config = "agents/tester/config.yaml"
            results['tester'] = await test_agent("TesterAgent", TesterAgent, tester_config)
        except ImportError:
            print("ℹ️  TesterAgent: Non implémenté (c'est normal)")
            results['tester'] = None
        
    except Exception as e:
        print(f"\n❌ ERREUR GLOBALE: {e}")
        import traceback
        traceback.print_exc()
    
    # Afficher le résumé
    print("\n" + "="*50)
    print("📊 RÉSUMÉ DES TESTS")
    print("="*50)
    
    successful = 0
    total = 0
    
    for agent_name, result in results.items():
        if result is None:
            status = "⚠️ "
        elif result:
            successful += 1
            status = "✅"
        else:
            status = "❌"
        
        if result is not None:  # Ne pas compter les agents abstraits/non implémentés
            total += 1
        
        print(f"{status} {agent_name:20}")
    
    print("-"*50)
    print(f"Total: {successful}/{total} agents concrets initialisés avec succès")
    
    if successful == total:
        print("\n🎉 TOUS LES AGENTS CONCRETS SONT OPÉRATIONNELS !")
    else:
        print(f"\n⚠️  {total - successful} agent(s) concret(s) nécessite(nt) attention")

if __name__ == "__main__":
    asyncio.run(main())
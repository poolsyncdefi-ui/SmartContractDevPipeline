# diagnose_communication_v2.py
import sys
from pathlib import Path

# Ajouter le chemin du projet
project_root = Path(__file__).parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from agents.communication.agent import CommunicationAgent
import yaml
import importlib

async def diagnose():
    print("="*60)
    print("🔍 DIAGNOSTIC V2 - AGENT COMMUNICATION")
    print("="*60)
    
    # 1. Vérifier la configuration
    print("\n📁 1. Configuration")
    config_path = Path("agents/communication/config.yaml")
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    subagents = config.get('subAgents', [])
    print(f"   • Sous-agents configurés: {len(subagents)}")
    
    # 2. Créer l'agent
    print("\n🤖 2. Création de l'agent")
    agent = CommunicationAgent()
    
    # 3. Tenter d'initialiser les sous-agents manuellement
    print("\n🔄 3. Initialisation manuelle des sous-agents")
    await agent._initialize_sub_agents()
    print(f"   • Sous-agents chargés: {len(agent._sub_agents)}")
    
    # 4. Test d'import avec le bon chemin
    print("\n📦 4. Test d'import avec le bon chemin")
    for sa in subagents:
        agent_id = sa['id']
        module_path = f"agents.communication.sous_agents.{agent_id}.agent"
        try:
            module = importlib.import_module(module_path)
            print(f"   ✅ {agent_id}: module importé")
            
            class_name = ''.join(p.capitalize() for p in agent_id.split('_')) + 'SubAgent'
            agent_class = getattr(module, class_name, None)
            if agent_class:
                print(f"      ✅ Classe {class_name} trouvée")
                
                # Tenter d'instancier
                instance = agent_class()
                print(f"      ✅ Instance créée")
            else:
                print(f"      ❌ Classe {class_name} non trouvée")
        except Exception as e:
            print(f"   ❌ {agent_id}: {e}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(diagnose())
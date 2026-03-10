#!/usr/bin/env python3
"""
Script de diagnostic pour les sous-agents communication
"""

import sys
import traceback
from pathlib import Path

# Ajouter le chemin du projet
project_root = Path(__file__).parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

def test_import(agent_id: str):
    """Teste l'import d'un sous-agent"""
    print(f"\n🔍 Test d'import pour {agent_id}...")
    try:
        module_name = f"agents.communication.sous_agents.{agent_id}.agent"
        print(f"   Module: {module_name}")
        
        module = __import__(module_name, fromlist=[''])
        print(f"   ✅ Module chargé")
        
        class_name = ''.join(p.capitalize() for p in agent_id.split('_')) + 'SubAgent'
        agent_class = getattr(module, class_name, None)
        
        if agent_class:
            print(f"   ✅ Classe {class_name} trouvée")
            
            # Tenter d'instancier
            instance = agent_class()
            print(f"   ✅ Instance créée")
            
            return True
        else:
            print(f"   ❌ Classe {class_name} non trouvée")
            return False
            
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
        traceback.print_exc()
        return False

def main():
    print("=" * 60)
    print("🔧 DIAGNOSTIC DES SOUS-AGENTS COMMUNICATION")
    print("=" * 60)
    
    # Vérifier la version Python
    print(f"\n📌 Version Python: {sys.version}")
    
    # Lister les sous-agents
    subagents_path = Path("agents/communication/sous_agents")
    if not subagents_path.exists():
        print(f"❌ Dossier {subagents_path} introuvable")
        return
    
    sub_agents = [d.name for d in subagents_path.iterdir() if d.is_dir()]
    print(f"\n📋 Sous-agents trouvés: {', '.join(sub_agents)}")
    
    # Tester chaque sous-agent
    success_count = 0
    for agent_id in sub_agents:
        if test_import(agent_id):
            success_count += 1
    
    print("\n" + "=" * 60)
    print(f"📊 RÉSULTAT: {success_count}/{len(sub_agents)} sous-agents importables")
    print("=" * 60)

if __name__ == "__main__":
    main()
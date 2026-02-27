#!/usr/bin/env python3
"""
Test d'import simple pour l'orchestrator
"""

import sys
import os
import traceback

print("\n" + "="*70)
print("🔍 TEST D'IMPORT DE L'ORCHESTRATOR")
print("="*70)

# Ajouter le chemin
sys.path.insert(0, os.path.dirname(__file__))

try:
    print("🔄 Tentative d'import: agents.orchestrator.agent")
    module = __import__('agents.orchestrator.agent', fromlist=['OrchestratorAgent'])
    
    if hasattr(module, 'OrchestratorAgent'):
        print(f"✅ Classe OrchestratorAgent trouvée")
        agent_class = getattr(module, 'OrchestratorAgent')
        
        # Tester l'instanciation
        try:
            agent = agent_class()
            print(f"✅ Agent instancié avec succès")
        except Exception as e:
            print(f"❌ Erreur instanciation: {e}")
            traceback.print_exc()
    else:
        print(f"❌ Classe OrchestratorAgent non trouvée")
        # Lister les classes disponibles
        classes = [attr for attr in dir(module) if attr.endswith('Agent')]
        print(f"   Classes trouvées: {classes}")
        
except ImportError as e:
    print(f"❌ Erreur import: {e}")
    traceback.print_exc()
    
    # Vérifier si le fichier existe
    agent_path = os.path.join("agents", "orchestrator", "agent.py")
    if os.path.exists(agent_path):
        print(f"✅ Fichier trouvé: {agent_path}")
        print(f"📄 Taille: {os.path.getsize(agent_path)} octets")
    else:
        print(f"❌ Fichier non trouvé: {agent_path}")

print("="*70)
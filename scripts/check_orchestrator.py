#!/usr/bin/env python3
"""
Script de diagnostic pour l'orchestrator
"""

import os
import sys
import importlib

print("\n" + "="*70)
print("🔍 DIAGNOSTIC DE L'ORCHESTRATOR")
print("="*70)

# Vérifier le fichier
orchestrator_path = os.path.join("agents", "orchestrator", "agent.py")
if os.path.exists(orchestrator_path):
    print(f"✅ Fichier trouvé: {orchestrator_path}")
    print(f"📄 Taille: {os.path.getsize(orchestrator_path)} octets")
else:
    print(f"❌ Fichier introuvable: {orchestrator_path}")

# Essayer d'importer
try:
    print("\n🔄 Tentative d'import...")
    module = importlib.import_module("agents.orchestrator.agent")
    print(f"✅ Module importé avec succès")
    
    # Lister les classes
    classes = [attr for attr in dir(module) if attr.endswith('Agent')]
    print(f"📋 Classes trouvées: {classes}")
    
    if 'OrchestratorAgent' in classes:
        AgentClass = getattr(module, 'OrchestratorAgent')
        print(f"✅ Classe OrchestratorAgent trouvée")
        
        # Tester l'instanciation
        try:
            agent = AgentClass()
            print(f"✅ Agent instancié avec succès")
        except Exception as e:
            print(f"❌ Erreur instanciation: {e}")
    else:
        print(f"❌ Classe OrchestratorAgent non trouvée")
        
except Exception as e:
    print(f"❌ Erreur import: {e}")

print("\n" + "="*70)
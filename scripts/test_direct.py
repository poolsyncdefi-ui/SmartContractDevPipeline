import sys
import os
import importlib.util

print("="*60)
print("🚀 IMPORT DIRECT - Contournement du bug")
print("="*60)

# Chemin absolu vers architect.py
architect_path = os.path.abspath("agents/architect/architect.py")
print(f"Chemin: {architect_path}")

if not os.path.exists(architect_path):
    print("❌ Fichier non trouvé!")
    exit(1)

# Import direct avec importlib
try:
    spec = importlib.util.spec_from_file_location("ArchitectAgent", architect_path)
    architect_module = importlib.util.module_from_spec(spec)
    
    # Exécuter le module
    spec.loader.exec_module(architect_module)
    
    # Récupérer la classe
    ArchitectAgent = getattr(architect_module, "ArchitectAgent")
    print("✅ Classe ArchitectAgent chargée directement")
    
    # Créer une config simple
    class SimpleConfig:
        def __init__(self, **kwargs):
            self.__dict__.update(kwargs)
    
    config = SimpleConfig(
        name="DirectArchitect",
        capabilities=["DESIGN"],
        description="Test direct"
    )
    
    # Instancier
    agent = ArchitectAgent(config)
    print(f"✅ Agent instancié: {agent.name}")
    print(f"   - Capabilités: {len(agent.capabilities)}")
    
except Exception as e:
    print(f"❌ Erreur: {e}")
    import traceback
    traceback.print_exc()

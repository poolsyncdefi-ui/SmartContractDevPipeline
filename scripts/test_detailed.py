import sys
import os
import traceback
sys.path.insert(0, '.')

print("="*60)
print("🧪 TEST DÉTAILLÉ ARCHITECT AGENT")
print("="*60)

try:
    # 1. Import avec plus de logs
    print("1. Import ArchitectAgent...")
    from agents.architect.architect import ArchitectAgent
    print("   ✅ Import réussi")
    
    # 2. Import AgentConfiguration
    print("2. Import AgentConfiguration...")
    from agents.base_agent.base_agent import AgentConfiguration
    print("   ✅ Import réussi")
    
    # 3. Création configuration
    print("3. Création configuration...")
    config = AgentConfiguration(
        name="TestArchitect",
        capabilities=["DESIGN_SYSTEM_ARCHITECTURE"],
        description="Agent de test"
    )
    print("   ✅ Configuration créée")
    
    # 4. Instanciation avec try-catch détaillé
    print("4. Instanciation de l'agent...")
    try:
        agent = ArchitectAgent(config=config)
        print(f"   ✅ Instanciation réussie: {agent.__class__.__name__}")
        
        # Vérifier les attributs
        print(f"   - Nom: {getattr(agent, 'name', 'NON DÉFINI')}")
        print(f"   - Capabilités: {len(getattr(agent, 'capabilities', []))}")
        print(f"   - Statut: {getattr(agent, 'status', 'NON DÉFINI')}")
        
    except Exception as inst_error:
        print(f"   ❌ Erreur instanciation: {inst_error}")
        print("   Stack trace:")
        traceback.print_exc()
    
except ImportError as e:
    print(f"❌ ImportError: {e}")
    traceback.print_exc()
except Exception as e:
    print(f"❌ Autre erreur: {e}")
    traceback.print_exc()

print("\n" + "="*60)
print("FIN DU TEST")
print("="*60)

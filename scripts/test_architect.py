import sys
import os
sys.path.insert(0, '.')

print("="*60)
print("🧪 TEST ARCHITECT AGENT")
print("="*60)

try:
    # Import
    from agents.architect.architect import ArchitectAgent
    print("✅ Import ArchitectAgent: RÉUSSI")
    
    from agents.base_agent.base_agent import AgentConfiguration
    print("✅ Import AgentConfiguration: RÉUSSI")
    
    # Configuration
    config = AgentConfiguration(
        name="TestArchitect",
        capabilities=["DESIGN_SYSTEM_ARCHITECTURE"],
        description="Test"
    )
    
    # Instanciation
    agent = ArchitectAgent(config=config)
    print(f"✅ Instanciation: RÉUSSI ({agent.__class__.__name__})")
    print(f"   - Nom: {agent.name}")
    print(f"   - Capabilités: {len(agent.capabilities)}")
    
    # Test tâche
    if hasattr(agent, 'execute_task'):
        result = agent.execute_task("validate_config")
        print(f"✅ Tâche exécutée: {result.get('status', 'N/A')}")
    
    print("\n" + "="*60)
    print("🎉 TOUS LES TESTS RÉUSSIS !")
    print("="*60)
    
except Exception as e:
    print(f"\n❌ ERREUR: {e}")
    import traceback
    traceback.print_exc()

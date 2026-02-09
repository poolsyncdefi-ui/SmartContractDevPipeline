import sys
sys.path.insert(0, '.')

print("🧪 TEST ORCHESTRATOR SIMPLIFIÉ")
print("="*50)

# Importer et tester chaque agent
agents_to_test = ["architect", "coder", "tester"]

for agent_name in agents_to_test:
    try:
        module_name = f"agents.{agent_name}.{agent_name}"
        print(f"\nTest {agent_name}...")
        
        # Import dynamique
        module = __import__(module_name, fromlist=[agent_name])
        
        # Trouver la classe (ex: ArchitectAgent, CoderAgent)
        class_name = f"{agent_name.capitalize()}Agent"
        if hasattr(module, class_name):
            AgentClass = getattr(module, class_name)
            
            # Instancier
            agent = AgentClass()
            print(f"✅ {class_name}: {agent.name} ({len(agent.capabilities)} capacités)")
        else:
            print(f"⚠️  Classe {class_name} non trouvée")
            
    except Exception as e:
        print(f"❌ {agent_name}: {str(e)[:100]}")

print("\n" + "="*50)
print("FIN DU TEST MULTI-AGENTS")

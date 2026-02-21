import asyncio
from orchestrator.orchestrator import OrchestratorAgent

async def test():
    agent = OrchestratorAgent()
    await agent.initialize()
    
    # Sprint complet avec génération automatique
    report = await agent.prepare_and_execute_sprint(
        project_name="MyDeFiApp",
        project_type="defi",
        strategy="largeur_dabord"
    )
    
    print(f'✅ Sprint {report["sprint"]} terminé')
    print(f'📊 Fragments: {report["fragments_info"]["total"]}')
    print(f'📈 Succès: {report["metrics"]["success_rate"]:.1f}%')

if __name__ == "__main__":
    asyncio.run(test())
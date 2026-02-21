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
    
    # 🔥 CORRECTION ICI - Utilise la bonne clé
    fragments_total = report["metrics"]["total_fragments"]
    success_rate = report["metrics"]["success_rate"]
    
    print(f'📊 Fragments: {fragments_total}')
    print(f'📈 Succès: {success_rate:.1f}%')
    
    # Affiche les recommandations
    if "recommendations" in report and report["recommendations"]:
        print("\n💡 Recommandations:")
        for rec in report["recommendations"]:
            print(f"  • {rec}")

if __name__ == "__main__":
    asyncio.run(test())
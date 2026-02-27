import asyncio
from agents.fuzzing_simulation.fuzzing_agent import FuzzingSimulationAgent

async def test_fuzzing():
    print("🧪 TEST AGENT DE FUZZING")
    print("="*50)
    
    agent = FuzzingSimulationAgent()
    await agent.initialize()
    
    # Lancer une campagne
    campaign = await agent.run_fuzzing_campaign(
        contract_path="./contracts/Token.sol",
        campaign_name="Test Fuzzing",
        template="comprehensive"
    )
    
    # Afficher les résultats
    print(f"\n📊 Résultats:")
    print(f"  ✅ Campagne: {campaign.id}")
    print(f"  ✅ Statut: {campaign.status}")
    print(f"  ✅ Tests: {campaign.total_tests}")
    print(f"  🔴 Vulnérabilités: {len(campaign.vulnerabilities)}")
    
    for vuln in campaign.vulnerabilities[:3]:
        print(f"\n  🔥 {vuln['severity'].upper()}: {vuln['description']}")
        print(f"     → {vuln['remediation']}")
    
    print(f"\n  📄 Rapport: {campaign.report_path}")

asyncio.run(test_fuzzing())
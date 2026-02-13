import asyncio
from agents.frontend_web3.frontend_agent import __version__
from agents.frontend_web3.frontend_agent import FrontendWeb3Agent


async def test_frontend_2_0():
    print("🎨 TEST FRONTEND WEB3 2.0 - BANKING + LENDING + NFT")
    print("="*60)
    
    agent = FrontendWeb3Agent("agents/frontend_web3/config.yaml")
    await agent.initialize()
    
    print(f"✅ Agent version: {__version__}")
    print(f"✅ Capacités 2.0: {len(agent._load_capabilities_2_0())}")
    print(f"✅ Templates 2.0: {list(agent._templates_2_0.keys())}")
    
    # Générer un projet avec les composants 2.0
    project = await agent.generate_project(
        project_name="BankingWeb3",
        contract_paths=["./contracts/SimpleNFT.sol"],
        components=[
            "banking_dashboard_2_0",
            "virtual_cards",
            "savings_pods",
            "credit_scoring",
            "nft_lending",
            "defi_composer"
        ],
        framework="nextjs"
    )
    
    print(f"\n📦 Projet 2.0 généré!")
    print(f"  📁 Output: {project.output_path}")
    print(f"  📄 Composants 2.0: {len(project.components)}")
    print(f"\n🚀 Lancer le projet:")
    print(f"  cd {project.output_path}")
    print(f"  npm install")
    print(f"  npm run dev")
    print(f"\n🌐 http://localhost:3000/banking")

asyncio.run(test_frontend_2_0())
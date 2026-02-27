import asyncio
from agents.frontend_web3.frontend_agent import FrontendWeb3Agent

async def test_frontend_config():
    print("🎨 TEST AGENT AVEC CONFIGURATION YAML")
    print("="*50)
    
    # Utiliser le fichier de config
    agent = FrontendWeb3Agent("agents/frontend_web3/config.yaml")
    await agent.initialize()
    
    print(f"✅ Agent: {agent._display_name}")
    print(f"✅ Version: {agent._version}")
    print(f"✅ Capacités: {len(agent._agent_config['agent']['capabilities'])}")
    
    # Extraire l'ABI du nouveau contrat
    abi_info = await agent.extract_contract_abi("./contracts/SimpleNFT.sol")
    
    if abi_info["abi"]:
        print(f"✅ ABI extraite: {len(abi_info['abi'])} fonctions")
    else:
        print("⚠️ ABI non trouvée - compilation nécessaire")
    
    # Générer le projet
    project = await agent.generate_project(
        project_name="NFTCollection",
        contract_paths=["./contracts/SimpleNFT.sol"],
        components=["mint_page", "nft_gallery", "dashboard"],
        framework="nextjs"
    )
    
    print(f"\n📦 Projet généré!")
    print(f"  📁 Output: {project.output_path}")
    print(f"  📄 Composants: {len(project.components)}")
    print(f"  📄 Contrats: {len(project.contracts)}")
    print(f"\n🚀 Lancer le projet:")
    print(f"  cd {project.output_path}")
    print(f"  npm install")
    print(f"  npm run dev")

asyncio.run(test_frontend_config())
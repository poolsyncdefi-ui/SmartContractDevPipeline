import asyncio
from agents.frontend_web3.frontend_agent import FrontendWeb3Agent

async def test_frontend():
    print("🎨 TEST AGENT FRONTEND WEB3")
    print("="*50)
    
    agent = FrontendWeb3Agent()
    await agent.initialize()
    
    # Générer un projet Next.js
    project = await agent.generate_project(
        project_name="CryptoKitties Clone",
        contract_paths=["./contracts/Token.sol"],
        components=["mint_page", "nft_gallery"],
        framework="nextjs"
    )
    
    print(f"\n📦 Projet généré!")
    print(f"  📁 Output: {project.output_path}")
    print(f"  🖥️  Framework: {project.framework.value}")
    print(f"  📄 Composants: {len(project.components)}")
    print(f"\n✅ Pour lancer le projet:")
    print(f"  cd {project.output_path}")
    print(f"  npm install")
    print(f"  npm run dev")
    print(f"\n🌐 http://localhost:3000")

asyncio.run(test_frontend())
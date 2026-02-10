# test_coder_simple.py
# Test simple d'instanciation de l'agent Coder

import os
import sys
import asyncio
import logging

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Chemin du projet
PROJECT_PATH = r"D:\Web3Projects\SmartContractDevPipeline"
if PROJECT_PATH not in sys.path:
    sys.path.insert(0, PROJECT_PATH)

async def test_coder_agent():
    """Test simple d'instanciation"""
    print("🧪 TEST CODER AGENT - INSTANCIATION SIMPLE")
    print("=" * 60)
    
    try:
        # 1. Import
        print("\n1. Import des modules...")
        from agents.coder.coder import CoderAgent
        print("   ✓ CoderAgent importé")
        
        # 2. Vérifier le chemin de config
        coder_path = os.path.join(PROJECT_PATH, "agents", "coder")
        config_path = os.path.join(coder_path, "config.yaml")
        
        print(f"\n2. Vérification des fichiers...")
        print(f"   Chemin coder: {coder_path}")
        print(f"   Config YAML: {config_path}")
        
        if os.path.exists(config_path):
            print("   ✓ config.yaml trouvé")
            with open(config_path, 'r') as f:
                content = f.read()
                print(f"   Taille: {len(content)} caractères")
        else:
            print("   ⚠ config.yaml non trouvé")
        
        # 3. Instanciation
        print("\n3. Instanciation de l'agent...")
        if os.path.exists(config_path):
            coder = CoderAgent(config_path)
            print(f"   ✓ Instancié AVEC config YAML")
        else:
            coder = CoderAgent()
            print(f"   ✓ Instancié SANS config YAML (par défaut)")
        
        # 4. Informations de base
        print(f"\n4. Informations agent:")
        print(f"   ID: {coder.agent_id}")
        print(f"   Display Name: {coder.display_name}")
        print(f"   Spécialisation: {coder.specialization}")
        print(f"   Version: {coder.version}")
        
        # 5. Test santé
        print(f"\n5. Test santé...")
        health = await coder.health_check()
        print(f"   Statut: {health['status']}")
        print(f"   Config chargée: {health['config_loaded']}")
        
        # 6. Test exécution simple
        print(f"\n6. Test exécution...")
        task_data = {
            "task_type": "generate_contract",
            "parameters": {
                "name": "TestToken",
                "language": "solidity",
                "template": "erc20"
            }
        }
        
        result = await coder.execute(task_data, {})
        print(f"   Tâche exécutée: {result['task_type']}")
        print(f"   Succès: {result['success']}")
        
        if result['success']:
            contract = result['result']
            print(f"   Contrat généré: {contract['contract_name']}")
            print(f"   Lignes: {contract['line_count']}")
        
        print("\n" + "=" * 60)
        print("✅ TEST RÉUSSI - CoderAgent fonctionnel")
        print("=" * 60)
        
        return True
        
    except ImportError as e:
        print(f"\n❌ ERREUR D'IMPORT: {e}")
        print("\nVérifiez que:")
        print("1. Le fichier agents/coder/coder.py existe")
        print("2. Le fichier agents/base_agent/base_agent.py existe")
        print("3. Les imports sont corrects")
        return False
        
    except Exception as e:
        print(f"\n❌ ERREUR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    # Exécuter le test
    success = asyncio.run(test_coder_agent())
    
    if not success:
        print("\n🔧 DIAGNOSTIC:")
        print("1. Vérifiez la structure des fichiers:")
        print("   ls agents/coder/")
        print("\n2. Testez l'import simple:")
        print("   python -c \"from agents.base_agent.base_agent import BaseAgent; print('BaseAgent OK')\"")
        print("\n3. Vérifiez le PYTHONPATH:")
        print("   python -c \"import sys; print(sys.path)\"")
    
    exit(0 if success else 1)
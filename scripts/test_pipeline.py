import asyncio
from agents.tester.tester import TesterAgent
from agents.formal_verification.formal_verification import FormalVerificationAgent

async def test_pipeline():
    print('🧪 PIPELINE COMPLET DE VÉRIFICATION')
    print('='*50)
    
    # 1. Agent de test
    tester = TesterAgent()
    await tester.initialize()
    print(f'✅ TesterAgent: {tester.status.value}')
    
    # 2. Agent de vérification formelle
    formal = FormalVerificationAgent()
    await formal.initialize()
    print(f'✅ FormalAgent: {formal.status.value}')
    
    # 3. Génération de tests
    test_result = await tester._generate_tests(
        {'contract_name': 'Token', 'framework': 'foundry'},
        {}
    )
    print(f'✅ Tests générés: {test_result["generated_file"]}')
    
    # 4. Vérification formelle
    proof = await formal.verify_contract('./contracts/Token.sol')
    print(f'✅ Preuve générée: {proof.id}')
    print(f'✅ Propriétés vérifiées: {len(proof.verified_properties)}')
    
    print('='*50)
    print('🎉 PIPELINE COMPLET OPÉRATIONNEL')
    print('='*50)

asyncio.run(test_pipeline())
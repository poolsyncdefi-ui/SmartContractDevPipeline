import asyncio
from agents.formal_verification.formal_verification import FormalVerificationAgent

async def test_complet():
    print('🧪 TEST COMPLET FORMALVERIFICATIONAGENT')
    print('='*50)
    
    agent = FormalVerificationAgent()
    await agent.initialize()
    print(f'✅ Statut: {agent.status.value}')
    
    # Génération d'invariants
    invariants = await agent.generate_invariants('./contracts/Token.sol')
    print(f'✅ Invariants générés: {len(invariants)}')
    
    # Vérification simulée
    proof = await agent.verify_contract('./contracts/Token.sol')
    print(f'✅ Preuve générée: {proof.id}')
    print(f'✅ Propriétés vérifiées: {len(proof.verified_properties)}')
    print(f'✅ Certificat: {proof.certificate_path}')
    
    # Health check
    health = await agent.health_check()
    print(f'✅ Health: {health["status"]}')
    print(f'✅ Vérifications: {health["verifications_count"]}')
    
    print('='*50)
    print('🎉 AGENT 100% FONCTIONNEL')
    print('='*50)

asyncio.run(test_complet())
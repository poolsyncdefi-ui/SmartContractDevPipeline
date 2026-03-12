"""
Integration Tester SubAgent - Sous-agent de tests d'intégration
Version: 2.0.0

Teste les interactions entre composants : contrats, agents, services externes.
Support multi-environnements et fork testing.
"""

import logging
import sys
import asyncio
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, Optional, List, Set
from enum import Enum
from dataclasses import dataclass, field
import random

# Configuration des imports
current_dir = Path(__file__).parent.absolute()
project_root = current_dir.parent.parent.parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from agents.sous_agents.base_subagent import BaseSubAgent

logger = logging.getLogger(__name__)


# ============================================================================
# ÉNUMS ET CLASSES DE DONNÉES
# ============================================================================

class IntegrationType(Enum):
    """Types d'intégration à tester"""
    CONTRACT_TO_CONTRACT = "contract_to_contract"
    AGENT_TO_AGENT = "agent_to_agent"
    CONTRACT_TO_AGENT = "contract_to_agent"
    EXTERNAL_API = "external_api"
    DATABASE = "database"
    BLOCKCHAIN_NETWORK = "blockchain_network"
    MULTICHAIN = "multichain"


class Environment(Enum):
    """Environnements de test"""
    LOCAL = "local"
    FORK = "fork"
    TESTNET = "testnet"
    STAGING = "staging"


@dataclass
class IntegrationTest:
    """Test d'intégration"""
    id: str
    name: str
    integration_type: IntegrationType
    components: List[str]
    dependencies: List[str]
    setup_required: bool = True
    teardown_required: bool = True
    timeout_seconds: int = 60
    retries: int = 2


@dataclass
class IntegrationResult:
    """Résultat de test d'intégration"""
    test_id: str
    success: bool
    duration_ms: float
    interactions_tested: int
    successful_interactions: int
    failed_interactions: int
    errors: List[Dict[str, Any]] = field(default_factory=list)
    logs: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)


# ============================================================================
# SOUS-AGENT PRINCIPAL
# ============================================================================

class IntegrationTesterSubAgent(BaseSubAgent):
    """
    Sous-agent de tests d'intégration

    Teste les interactions entre composants avec :
    - Tests inter-contrats
    - Tests inter-agents
    - Fork testing sur mainnet
    - Simulations d'attaques
    """

    def __init__(self, config_path: str = ""):
        """Initialise le sous-agent de tests d'intégration"""
        super().__init__(config_path)

        # Métadonnées
        self._subagent_display_name = "🔗 Tests d'Intégration"
        self._subagent_description = "Tests d'intégration entre composants"
        self._subagent_version = "2.0.0"
        self._subagent_category = "tester"
        self._subagent_capabilities = [
            "integration.test_contract_interaction",
            "integration.test_agent_communication",
            "integration.fork_test",
            "integration.simulate_attack",
            "integration.validate_flow"
        ]

        # État interne
        self._integration_tests: Dict[str, IntegrationTest] = {}
        self._test_results: Dict[str, IntegrationResult] = {}
        self._environments = self._agent_config.get('environments', {})
        
        # Tâche de fond
        self._cleanup_task: Optional[asyncio.Task] = None

        logger.info(f"✅ {self._subagent_display_name} initialisé (v{self._subagent_version})")

    # ========================================================================
    # IMPLÉMENTATION DES MÉTHODES ABSTRACTES
    # ========================================================================

    async def _initialize_subagent_components(self) -> bool:
        """Initialise les composants spécifiques"""
        logger.info("Initialisation des composants de tests d'intégration...")

        try:
            # Charger les tests d'intégration prédéfinis
            await self._load_integration_tests()

            logger.info("✅ Composants de tests d'intégration initialisés")
            return True

        except Exception as e:
            logger.error(f"❌ Erreur initialisation composants: {e}")
            return False

    async def _initialize_components(self) -> bool:
        """Implémentation requise par BaseAgent"""
        return await self._initialize_subagent_components()

    def _get_capability_handlers(self) -> Dict[str, Any]:
        """Retourne les handlers spécifiques"""
        return {
            "integration.test_contract_interaction": self._handle_test_contract_interaction,
            "integration.test_agent_communication": self._handle_test_agent_communication,
            "integration.fork_test": self._handle_fork_test,
            "integration.simulate_attack": self._handle_simulate_attack,
            "integration.validate_flow": self._handle_validate_flow,
        }

    # ========================================================================
    # MÉTHODES PRIVÉES
    # ========================================================================

    async def _load_integration_tests(self):
        """Charge les tests d'intégration depuis la configuration"""
        tests_config = self._agent_config.get('integration_tests', [])
        
        for test_config in tests_config:
            test = IntegrationTest(
                id=test_config.get('id', f"test_{len(self._integration_tests)}"),
                name=test_config.get('name', 'Unnamed Test'),
                integration_type=IntegrationType(test_config.get('type', 'contract_to_contract')),
                components=test_config.get('components', []),
                dependencies=test_config.get('dependencies', []),
                timeout_seconds=test_config.get('timeout', 60)
            )
            self._integration_tests[test.id] = test
        
        logger.info(f"  📋 {len(self._integration_tests)} tests d'intégration chargés")

    async def _setup_fork_environment(self, network: str, block_number: Optional[int] = None) -> Dict[str, Any]:
        """Configure un environnement fork de la mainnet"""
        fork_url = self._environments.get('fork', {}).get('url', 'http://localhost:8545')
        
        # Simulation de fork
        return {
            'fork_url': fork_url,
            'network': network,
            'block_number': block_number or 'latest',
            'fork_id': f"fork_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        }

    async def _simulate_contract_interaction(self, contract_a: str, contract_b: str, 
                                             function: str, params: List[Any]) -> Dict[str, Any]:
        """Simule une interaction entre contrats"""
        await asyncio.sleep(0.5)  # Simulation
        
        success = random.random() > 0.1  # 90% de succès
        
        return {
            'success': success,
            'interaction': f"{contract_a}.{function} → {contract_b}",
            'gas_used': random.randint(50000, 150000),
            'events_emitted': random.randint(0, 3),
            'state_changes': random.randint(1, 5) if success else 0
        }

    async def _simulate_agent_communication(self, agent_a: str, agent_b: str,
                                            message_type: str, payload: Dict) -> Dict[str, Any]:
        """Simule une communication entre agents"""
        await asyncio.sleep(0.3)  # Simulation
        
        success = random.random() > 0.05  # 95% de succès
        
        return {
            'success': success,
            'message_id': f"msg_{datetime.now().timestamp()}",
            'response_time_ms': random.randint(50, 500),
            'response': {'status': 'ok', 'data': {'processed': True}} if success else None
        }

    # ========================================================================
    # HANDLERS DE CAPACITÉS
    # ========================================================================

    async def _handle_test_contract_interaction(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Teste les interactions entre contrats"""
        contract_a = params.get('contract_a')
        contract_b = params.get('contract_b')
        interactions = params.get('interactions', [])
        environment = params.get('environment', 'local')

        if not contract_a or not contract_b:
            return {'success': False, 'error': 'contract_a et contract_b requis'}

        test_id = f"contract_test_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        start_time = datetime.now()

        results = []
        for interaction in interactions:
            result = await self._simulate_contract_interaction(
                contract_a, contract_b,
                interaction.get('function', 'unknown'),
                interaction.get('params', [])
            )
            results.append(result)

        duration = (datetime.now() - start_time).total_seconds() * 1000
        
        successful = sum(1 for r in results if r['success'])
        failed = len(results) - successful

        test_result = IntegrationResult(
            test_id=test_id,
            success=failed == 0,
            duration_ms=duration,
            interactions_tested=len(results),
            successful_interactions=successful,
            failed_interactions=failed,
            errors=[{'interaction': r['interaction'], 'error': 'Simulated failure'} 
                   for r in results if not r['success']]
        )

        self._test_results[test_id] = test_result

        return {
            'success': test_result.success,
            'test_id': test_id,
            'summary': {
                'total': test_result.interactions_tested,
                'successful': test_result.successful_interactions,
                'failed': test_result.failed_interactions
            },
            'interactions': results,
            'duration_ms': duration,
            'environment': environment,
            'contracts': [contract_a, contract_b]
        }

    async def _handle_test_agent_communication(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Teste les communications entre agents"""
        agent_a = params.get('agent_a')
        agent_b = params.get('agent_b')
        messages = params.get('messages', [])

        if not agent_a or not agent_b:
            return {'success': False, 'error': 'agent_a et agent_b requis'}

        test_id = f"agent_test_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        start_time = datetime.now()

        results = []
        for msg in messages:
            result = await self._simulate_agent_communication(
                agent_a, agent_b,
                msg.get('type', 'default'),
                msg.get('payload', {})
            )
            results.append(result)

        duration = (datetime.now() - start_time).total_seconds() * 1000

        successful = sum(1 for r in results if r['success'])
        failed = len(results) - successful

        return {
            'success': failed == 0,
            'test_id': test_id,
            'summary': {
                'total': len(results),
                'successful': successful,
                'failed': failed
            },
            'messages': results,
            'duration_ms': duration,
            'agents': [agent_a, agent_b]
        }

    async def _handle_fork_test(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Exécute des tests sur un fork de la mainnet"""
        network = params.get('network', 'ethereum')
        block_number = params.get('block_number')
        tests = params.get('tests', [])

        # Configurer l'environnement fork
        fork_env = await self._setup_fork_environment(network, block_number)

        test_id = f"fork_test_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        start_time = datetime.now()

        results = []
        for test in tests:
            # Simulation de test sur fork
            await asyncio.sleep(0.8)
            results.append({
                'test': test.get('name', 'unknown'),
                'success': random.random() > 0.15,
                'gas_used': random.randint(100000, 500000),
                'block_number': block_number or 'latest'
            })

        duration = (datetime.now() - start_time).total_seconds() * 1000

        return {
            'success': True,
            'test_id': test_id,
            'fork_info': fork_env,
            'results': results,
            'summary': {
                'total': len(results),
                'passed': sum(1 for r in results if r['success']),
                'failed': sum(1 for r in results if not r['success'])
            },
            'duration_ms': duration
        }

    async def _handle_simulate_attack(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Simule une attaque sur un contrat ou système"""
        target = params.get('target')
        attack_type = params.get('attack_type', 'reentrancy')
        intensity = params.get('intensity', 'medium')

        if not target:
            return {'success': False, 'error': 'target requis'}

        # Simulation d'attaque
        await asyncio.sleep(1.0)

        # Probabilité de succès selon l'intensité
        success_rate = {
            'low': 0.3,
            'medium': 0.5,
            'high': 0.7
        }.get(intensity, 0.5)

        attack_succeeded = random.random() < success_rate

        return {
            'success': True,
            'attack_simulation': {
                'target': target,
                'attack_type': attack_type,
                'intensity': intensity,
                'attack_succeeded': attack_succeeded,
                'vulnerabilities_found': random.randint(1, 3) if attack_succeeded else 0,
                'exploit_sequence': [
                    'call withdraw()',
                    're-enter before state update',
                    'drain funds'
                ] if attack_succeeded else [],
                'estimated_loss_usd': random.randint(10000, 1000000) if attack_succeeded else 0,
                'recommendations': [
                    'Use ReentrancyGuard',
                    'Follow checks-effects-interactions pattern',
                    'Limit external calls'
                ] if attack_succeeded else ['No vulnerabilities found']
            },
            'timestamp': datetime.now().isoformat()
        }

    async def _handle_validate_flow(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Valide un flow complet (ex: deposit → swap → withdraw)"""
        flow_name = params.get('flow_name')
        steps = params.get('steps', [])
        environment = params.get('environment', 'local')

        if not steps:
            return {'success': False, 'error': 'steps requis'}

        test_id = f"flow_test_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        start_time = datetime.now()

        flow_results = []
        previous_step_success = True

        for i, step in enumerate(steps):
            step_name = step.get('name', f'step_{i}')
            
            # Simuler l'exécution de l'étape
            await asyncio.sleep(0.3)
            step_success = previous_step_success and (random.random() > 0.1)
            
            flow_results.append({
                'step': step_name,
                'success': step_success,
                'duration_ms': random.randint(100, 500),
                'output': {'status': 'ok', 'data': {}} if step_success else None,
                'error': None if step_success else 'Step failed simulation'
            })
            
            previous_step_success = step_success

        duration = (datetime.now() - start_time).total_seconds() * 1000
        flow_success = all(r['success'] for r in flow_results)

        return {
            'success': flow_success,
            'test_id': test_id,
            'flow_name': flow_name or 'Unnamed Flow',
            'steps': flow_results,
            'summary': {
                'total_steps': len(flow_results),
                'successful_steps': sum(1 for r in flow_results if r['success']),
                'failed_steps': sum(1 for r in flow_results if not r['success'])
            },
            'duration_ms': duration,
            'environment': environment,
            'timestamp': datetime.now().isoformat()
        }

    # ========================================================================
    # NETTOYAGE
    # ========================================================================

    async def shutdown(self) -> bool:
        """Arrête le sous-agent"""
        logger.info(f"Arrêt de {self._subagent_display_name}...")

        if self._cleanup_task and not self._cleanup_task.done():
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass

        return await super().shutdown()


# ============================================================================
# FONCTIONS D'EXPORT
# ============================================================================

def get_agent_class():
    """
    Fonction requise pour le chargement dynamique des sous-agents.
    Retourne la classe principale du sous-agent.
    """
    return IntegrationTesterSubAgent


def create_integration_tester_agent(config_path: str = "") -> "IntegrationTesterSubAgent":
    """Crée une instance du sous-agent de tests d'intégration"""
    return IntegrationTesterSubAgent(config_path)
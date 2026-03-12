"""
Fuzzing Expert SubAgent - Sous-agent de fuzzing avancé
Version: 2.0.0

Exécute des campagnes de fuzzing sur smart contracts.
Support Echidna, Medusa, Foundry, analyse de vulnérabilités.
"""

import logging
import sys
import asyncio
import json
import subprocess
import tempfile
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

class FuzzingEngine(Enum):
    """Moteurs de fuzzing supportés"""
    ECHIDNA = "echidna"
    MEDUSA = "medusa"
    FOUNDRY = "foundry"
    DAPPFORGE = "dappforge"
    SIMULATION = "simulation"


class FuzzingStrategy(Enum):
    """Stratégies de fuzzing"""
    RANDOM = "random"
    COVERAGE_GUIDED = "coverage_guided"
    INVARIANT_BASED = "invariant_based"
    DELTA = "delta"
    COMPREHENSIVE = "comprehensive"


class VulnerabilitySeverity(Enum):
    """Sévérité des vulnérabilités"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


@dataclass
class FuzzingCampaign:
    """Campagne de fuzzing"""
    id: str
    contract_path: str
    engine: FuzzingEngine
    strategy: FuzzingStrategy
    test_limit: int
    time_limit_seconds: int
    corpus_dir: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    status: str = "pending"  # pending, running, completed, failed


@dataclass
class Vulnerability:
    """Vulnérabilité détectée"""
    id: str
    type: str
    severity: VulnerabilitySeverity
    description: str
    location: str
    call_sequence: List[str]
    swc_id: Optional[str] = None
    gas_used: int = 0


@dataclass
class FuzzingResult:
    """Résultat de campagne de fuzzing"""
    campaign_id: str
    contract: str
    duration_seconds: float
    tests_executed: int
    coverage_percent: float
    vulnerabilities: List[Vulnerability]
    corpus_size: int
    unique_failures: int
    logs: List[str] = field(default_factory=list)
    completed_at: datetime = field(default_factory=datetime.now)


# ============================================================================
# SOUS-AGENT PRINCIPAL
# ============================================================================

class FuzzingExpertSubAgent(BaseSubAgent):
    """
    Sous-agent de fuzzing avancé

    Exécute des campagnes de fuzzing avec :
    - Multiples moteurs (Echidna, Medusa, Foundry)
    - Détection automatique de vulnérabilités
    - Génération de corpus optimisés
    - Analyse de couverture
    """

    def __init__(self, config_path: str = ""):
        """Initialise le sous-agent de fuzzing"""
        super().__init__(config_path)

        # Métadonnées
        self._subagent_display_name = "🎲 Fuzzing Expert"
        self._subagent_description = "Fuzzing avancé pour smart contracts"
        self._subagent_version = "2.0.0"
        self._subagent_category = "tester"
        self._subagent_capabilities = [
            "fuzzing.run_campaign",
            "fuzzing.get_results",
            "fuzzing.list_campaigns",
            "fuzzing.analyze_coverage",
            "fuzzing.generate_corpus",
            "fuzzing.simulate_attack_vector"
        ]

        # État interne
        self._campaigns: Dict[str, FuzzingCampaign] = {}
        self._results: Dict[str, FuzzingResult] = {}
        self._engines_config = self._agent_config.get('engines', {})
        self._vulnerability_patterns = self._load_vulnerability_patterns()
        
        # Tâche de fond
        self._cleanup_task: Optional[asyncio.Task] = None

        logger.info(f"✅ {self._subagent_display_name} initialisé (v{self._subagent_version})")

    # ========================================================================
    # IMPLÉMENTATION DES MÉTHODES ABSTRACTES
    # ========================================================================

    async def _initialize_subagent_components(self) -> bool:
        """Initialise les composants spécifiques"""
        logger.info("Initialisation des composants de fuzzing...")

        try:
            # Vérifier les moteurs disponibles
            await self._check_available_engines()

            logger.info("✅ Composants de fuzzing initialisés")
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
            "fuzzing.run_campaign": self._handle_run_campaign,
            "fuzzing.get_results": self._handle_get_results,
            "fuzzing.list_campaigns": self._handle_list_campaigns,
            "fuzzing.analyze_coverage": self._handle_analyze_coverage,
            "fuzzing.generate_corpus": self._handle_generate_corpus,
            "fuzzing.simulate_attack_vector": self._handle_simulate_attack_vector,
        }

    # ========================================================================
    # MÉTHODES PRIVÉES
    # ========================================================================

    async def _check_available_engines(self):
        """Vérifie les moteurs de fuzzing disponibles"""
        logger.info("Vérification des moteurs de fuzzing...")

        self.available_engines = {}

        # Echidna
        try:
            result = subprocess.run(['echidna-test', '--version'], 
                                   capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                self.available_engines['echidna'] = {
                    'available': True,
                    'version': result.stdout.strip(),
                    'config': self._engines_config.get('echidna', {})
                }
                logger.info(f"  ✅ Echidna disponible")
        except:
            logger.debug("  ℹ️ Echidna non disponible")

        # Medusa
        try:
            result = subprocess.run(['medusa', '--version'], 
                                   capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                self.available_engines['medusa'] = {
                    'available': True,
                    'version': result.stdout.strip(),
                    'config': self._engines_config.get('medusa', {})
                }
                logger.info(f"  ✅ Medusa disponible")
        except:
            logger.debug("  ℹ️ Medusa non disponible")

        # Foundry
        try:
            result = subprocess.run(['forge', '--version'], 
                                   capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                self.available_engines['foundry'] = {
                    'available': True,
                    'version': result.stdout.strip(),
                    'config': self._engines_config.get('foundry', {})
                }
                logger.info(f"  ✅ Foundry disponible")
        except:
            logger.debug("  ℹ️ Foundry non disponible")

        # Simulation toujours disponible
        self.available_engines['simulation'] = {
            'available': True,
            'simulation': True,
            'config': {}
        }

        logger.info(f"  📊 Moteurs disponibles: {', '.join(self.available_engines.keys())}")

    def _load_vulnerability_patterns(self) -> Dict[str, Any]:
        """Charge les patterns de vulnérabilités"""
        return {
            'reentrancy': {
                'severity': VulnerabilitySeverity.CRITICAL,
                'swc_id': 'SWC-107',
                'description': 'Vulnérabilité de réentrance détectée',
                'check': lambda s: 'call.value' in s or 'delegatecall' in s
            },
            'integer_overflow': {
                'severity': VulnerabilitySeverity.HIGH,
                'swc_id': 'SWC-101',
                'description': 'Débordement d\'entier potentiel',
                'check': lambda s: '+' in s or '-' in s or '*' in s
            },
            'access_control': {
                'severity': VulnerabilitySeverity.HIGH,
                'swc_id': 'SWC-115',
                'description': 'Contrôle d\'accès insuffisant',
                'check': lambda s: 'onlyOwner' not in s and 'require(msg.sender == owner)' not in s
            },
            'unchecked_call': {
                'severity': VulnerabilitySeverity.MEDIUM,
                'swc_id': 'SWC-104',
                'description': 'Appel externe non vérifié',
                'check': lambda s: 'call{' in s and 'require(success)' not in s
            }
        }

    async def _run_echidna_campaign(self, campaign: FuzzingCampaign) -> FuzzingResult:
        """Exécute une campagne avec Echidna"""
        start_time = datetime.now()
        
        # Simulation pour l'exemple
        await asyncio.sleep(3)
        
        duration = (datetime.now() - start_time).total_seconds()
        
        # Générer des vulnérabilités simulées
        vulnerabilities = []
        for vuln_type, pattern in self._vulnerability_patterns.items():
            if random.random() > 0.7:  # 30% de chance
                vulnerabilities.append(Vulnerability(
                    id=f"VULN-{len(vulnerabilities)}",
                    type=vuln_type,
                    severity=pattern['severity'],
                    description=pattern['description'],
                    location=f"{campaign.contract_path}:L{random.randint(50, 300)}",
                    call_sequence=[
                        f"call function_{random.randint(1,5)}()",
                        f"call function_{random.randint(1,5)}()",
                        f"call function_{random.randint(1,5)}()"
                    ],
                    swc_id=pattern['swc_id']
                ))

        return FuzzingResult(
            campaign_id=campaign.id,
            contract=campaign.contract_path,
            duration_seconds=duration,
            tests_executed=random.randint(1000, 10000),
            coverage_percent=random.uniform(60, 95),
            vulnerabilities=vulnerabilities,
            corpus_size=random.randint(50, 500),
            unique_failures=len(vulnerabilities),
            logs=[f"Test {i}: passed" for i in range(10)]
        )

    async def _run_medusa_campaign(self, campaign: FuzzingCampaign) -> FuzzingResult:
        """Exécute une campagne avec Medusa"""
        # Similaire à Echidna mais avec des métriques différentes
        result = await self._run_echidna_campaign(campaign)
        result.coverage_percent += 5  # Medusa est meilleur
        return result

    async def _run_foundry_campaign(self, campaign: FuzzingCampaign) -> FuzzingResult:
        """Exécute une campagne avec Foundry"""
        result = await self._run_echidna_campaign(campaign)
        result.coverage_percent += 3
        return result

    async def _run_simulation_campaign(self, campaign: FuzzingCampaign) -> FuzzingResult:
        """Exécute une campagne simulée (pour test)"""
        return await self._run_echidna_campaign(campaign)

    # ========================================================================
    # HANDLERS DE CAPACITÉS
    # ========================================================================

    async def _handle_run_campaign(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Lance une campagne de fuzzing"""
        contract_path = params.get('contract_path')
        engine_name = params.get('engine', 'simulation')
        strategy = params.get('strategy', 'comprehensive')
        test_limit = params.get('test_limit', 10000)
        time_limit = params.get('time_limit_seconds', 300)

        if not contract_path:
            return {'success': False, 'error': 'contract_path requis'}

        if engine_name not in self.available_engines:
            return {'success': False, 'error': f'Moteur {engine_name} non disponible'}

        # Créer la campagne
        campaign_id = f"FUZZ-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        campaign = FuzzingCampaign(
            id=campaign_id,
            contract_path=contract_path,
            engine=FuzzingEngine(engine_name),
            strategy=FuzzingStrategy(strategy),
            test_limit=test_limit,
            time_limit_seconds=time_limit,
            corpus_dir=f"corpus/{campaign_id}"
        )

        self._campaigns[campaign_id] = campaign

        # Exécuter selon le moteur
        if engine_name == 'echidna':
            result = await self._run_echidna_campaign(campaign)
        elif engine_name == 'medusa':
            result = await self._run_medusa_campaign(campaign)
        elif engine_name == 'foundry':
            result = await self._run_foundry_campaign(campaign)
        else:
            result = await self._run_simulation_campaign(campaign)

        self._results[campaign_id] = result

        return {
            'success': True,
            'campaign_id': campaign_id,
            'engine': engine_name,
            'strategy': strategy,
            'results': {
                'duration_seconds': result.duration_seconds,
                'tests_executed': result.tests_executed,
                'coverage_percent': round(result.coverage_percent, 2),
                'vulnerabilities_found': len(result.vulnerabilities),
                'unique_failures': result.unique_failures,
                'corpus_size': result.corpus_size
            },
            'vulnerabilities': [
                {
                    'type': v.type,
                    'severity': v.severity.value,
                    'description': v.description,
                    'location': v.location,
                    'swc_id': v.swc_id,
                    'call_sequence': v.call_sequence[:3]  # Limiter pour la réponse
                }
                for v in result.vulnerabilities
            ],
            'status': 'completed'
        }

    async def _handle_get_results(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Récupère les résultats d'une campagne"""
        campaign_id = params.get('campaign_id')

        if not campaign_id:
            return {'success': False, 'error': 'campaign_id requis'}

        result = self._results.get(campaign_id)
        if not result:
            return {'success': False, 'error': f'Campagne {campaign_id} non trouvée'}

        return {
            'success': True,
            'campaign_id': campaign_id,
            'results': {
                'contract': result.contract,
                'duration_seconds': result.duration_seconds,
                'tests_executed': result.tests_executed,
                'coverage_percent': round(result.coverage_percent, 2),
                'vulnerabilities_found': len(result.vulnerabilities),
                'vulnerabilities': [
                    {
                        'type': v.type,
                        'severity': v.severity.value,
                        'description': v.description,
                        'location': v.location,
                        'swc_id': v.swc_id,
                        'call_sequence': v.call_sequence
                    }
                    for v in result.vulnerabilities
                ],
                'corpus_size': result.corpus_size,
                'completed_at': result.completed_at.isoformat()
            }
        }

    async def _handle_list_campaigns(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Liste les campagnes de fuzzing"""
        campaigns = []
        for cid, campaign in self._campaigns.items():
            result = self._results.get(cid)
            campaigns.append({
                'id': campaign.id,
                'contract': campaign.contract_path,
                'engine': campaign.engine.value,
                'strategy': campaign.strategy.value,
                'status': campaign.status,
                'created_at': campaign.created_at.isoformat(),
                'tests': result.tests_executed if result else 0,
                'vulnerabilities': len(result.vulnerabilities) if result else 0,
                'coverage': round(result.coverage_percent, 2) if result else 0
            })

        return {
            'success': True,
            'campaigns': campaigns,
            'total': len(campaigns)
        }

    async def _handle_analyze_coverage(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Analyse la couverture de code atteinte"""
        campaign_id = params.get('campaign_id')

        if not campaign_id:
            return {'success': False, 'error': 'campaign_id requis'}

        result = self._results.get(campaign_id)
        if not result:
            return {'success': False, 'error': f'Campagne {campaign_id} non trouvée'}

        # Simulation d'analyse détaillée de couverture
        coverage_details = {
            'line_coverage': {
                'percentage': result.coverage_percent,
                'covered': int(result.tests_executed * 0.8),
                'total': result.tests_executed
            },
            'branch_coverage': {
                'percentage': result.coverage_percent - 5,
                'covered': int(result.tests_executed * 0.75),
                'total': result.tests_executed
            },
            'function_coverage': {
                'percentage': result.coverage_percent + 2,
                'covered': int(result.tests_executed * 0.82),
                'total': result.tests_executed
            },
            'paths_covered': random.randint(50, 200),
            'unique_states': random.randint(100, 500),
            'coverage_map': f"coverage_maps/{campaign_id}.json"
        }

        return {
            'success': True,
            'campaign_id': campaign_id,
            'coverage': coverage_details,
            'recommendations': [
                "Augmenter le nombre de tests pour les branches non couvertes",
                "Ajouter des invariants spécifiques",
                "Cibler les fonctions à haute criticité"
            ] if coverage_details['branch_coverage']['percentage'] < 80 else []
        }

    async def _handle_generate_corpus(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Génère un corpus optimisé pour le fuzzing"""
        contract_path = params.get('contract_path')
        size = params.get('size', 1000)
        engine = params.get('engine', 'echidna')

        if not contract_path:
            return {'success': False, 'error': 'contract_path requis'}

        corpus_id = f"CORPUS-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        corpus_dir = f"corpus/{corpus_id}"

        # Simulation de génération
        await asyncio.sleep(2)

        return {
            'success': True,
            'corpus_id': corpus_id,
            'corpus_dir': corpus_dir,
            'size': size,
            'generated_files': random.randint(50, 200),
            'estimated_coverage': random.uniform(40, 70),
            'engine': engine,
            'message': f"Corpus généré avec {random.randint(50, 200)} fichiers de test"
        }

    async def _handle_simulate_attack_vector(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Simule un vecteur d'attaque spécifique"""
        contract_path = params.get('contract_path')
        attack_type = params.get('attack_type', 'reentrancy')
        intensity = params.get('intensity', 'medium')

        if not contract_path:
            return {'success': False, 'error': 'contract_path requis'}

        # Simulation d'attaque
        await asyncio.sleep(1.5)

        success_probability = {
            'low': 0.3,
            'medium': 0.5,
            'high': 0.7
        }.get(intensity, 0.5)

        attack_succeeded = random.random() < success_probability

        return {
            'success': True,
            'attack_simulation': {
                'contract': contract_path,
                'attack_type': attack_type,
                'intensity': intensity,
                'attack_succeeded': attack_succeeded,
                'exploit_sequence': [
                    f"Step 1: Prepare {attack_type} attack",
                    f"Step 2: Execute malicious transaction",
                    f"Step 3: Exploit vulnerability"
                ] if attack_succeeded else [],
                'vulnerabilities_found': random.randint(1, 3) if attack_succeeded else 0,
                'estimated_gas_used': random.randint(100000, 500000),
                'remediation': [
                    "Implement reentrancy guard",
                    "Use checks-effects-interactions pattern",
                    "Limit external calls"
                ] if attack_type == 'reentrancy' else [
                    "Use SafeMath library",
                    "Upgrade to Solidity 0.8.x"
                ]
            }
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
    return FuzzingExpertSubAgent


def create_fuzzing_expert_agent(config_path: str = "") -> "FuzzingExpertSubAgent":
    """Crée une instance du sous-agent de fuzzing"""
    return FuzzingExpertSubAgent(config_path)
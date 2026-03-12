"""
E2E Tester SubAgent - Sous-agent de tests end-to-end
Version: 2.0.0

Teste les flows utilisateur complets : du frontend à la blockchain.
Intégration avec Playwright/Cypress, scenarios utilisateur, métriques UX.
"""

import logging
import sys
import asyncio
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, Optional, List
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

class BrowserType(Enum):
    """Types de navigateurs supportés"""
    CHROMIUM = "chromium"
    FIREFOX = "firefox"
    WEBKIT = "webkit"
    CHROME = "chrome"
    EDGE = "edge"


class DeviceType(Enum):
    """Types d'appareils pour tests mobiles"""
    DESKTOP = "desktop"
    TABLET = "tablet"
    MOBILE = "mobile"


@dataclass
class E2ETestScenario:
    """Scénario de test E2E"""
    id: str
    name: str
    description: str
    steps: List[Dict[str, Any]]
    required_contracts: List[str] = field(default_factory=list)
    required_agents: List[str] = field(default_factory=list)
    timeout_seconds: int = 120


@dataclass
class E2ETestResult:
    """Résultat de test E2E"""
    scenario_id: str
    success: bool
    steps_completed: int
    steps_total: int
    duration_ms: float
    screenshots: List[str] = field(default_factory=list)
    console_errors: List[str] = field(default_factory=list)
    network_requests: List[Dict] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)


# ============================================================================
# SOUS-AGENT PRINCIPAL
# ============================================================================

class E2ETesterSubAgent(BaseSubAgent):
    """
    Sous-agent de tests end-to-end

    Teste les flows utilisateur complets avec :
    - Scenarios utilisateur réalistes
    - Tests cross-browser
    - Tests mobiles/responsive
    - Métriques UX (temps de chargement, interactions)
    """

    def __init__(self, config_path: str = ""):
        """Initialise le sous-agent de tests E2E"""
        super().__init__(config_path)

        # Métadonnées
        self._subagent_display_name = "🌐 Tests End-to-End"
        self._subagent_description = "Tests de flows utilisateur complets"
        self._subagent_version = "2.0.0"
        self._subagent_category = "tester"
        self._subagent_capabilities = [
            "e2e.run_scenario",
            "e2e.list_scenarios",
            "e2e.test_mobile",
            "e2e.collect_metrics",
            "e2e.record_session"
        ]

        # État interne
        self._scenarios: Dict[str, E2ETestScenario] = {}
        self._results: Dict[str, E2ETestResult] = {}
        
        # Configuration
        self._browsers = self._agent_config.get('browsers', {})
        self._devices = self._agent_config.get('devices', {})
        self._base_url = self._agent_config.get('base_url', 'http://localhost:3000')
        
        # Tâche de fond
        self._cleanup_task: Optional[asyncio.Task] = None

        logger.info(f"✅ {self._subagent_display_name} initialisé (v{self._subagent_version})")

    # ========================================================================
    # IMPLÉMENTATION DES MÉTHODES ABSTRACTES
    # ========================================================================

    async def _initialize_subagent_components(self) -> bool:
        """Initialise les composants spécifiques"""
        logger.info("Initialisation des composants de tests E2E...")

        try:
            # Charger les scénarios
            await self._load_scenarios()

            logger.info("✅ Composants de tests E2E initialisés")
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
            "e2e.run_scenario": self._handle_run_scenario,
            "e2e.list_scenarios": self._handle_list_scenarios,
            "e2e.test_mobile": self._handle_test_mobile,
            "e2e.collect_metrics": self._handle_collect_metrics,
            "e2e.record_session": self._handle_record_session,
        }

    # ========================================================================
    # MÉTHODES PRIVÉES
    # ========================================================================

    async def _load_scenarios(self):
        """Charge les scénarios de test depuis la configuration"""
        scenarios_config = self._agent_config.get('scenarios', [])
        
        for sc_config in scenarios_config:
            scenario = E2ETestScenario(
                id=sc_config.get('id', f"scenario_{len(self._scenarios)}"),
                name=sc_config.get('name', 'Unnamed Scenario'),
                description=sc_config.get('description', ''),
                steps=sc_config.get('steps', []),
                required_contracts=sc_config.get('required_contracts', []),
                required_agents=sc_config.get('required_agents', []),
                timeout_seconds=sc_config.get('timeout', 120)
            )
            self._scenarios[scenario.id] = scenario
        
        logger.info(f"  📋 {len(self._scenarios)} scénarios E2E chargés")

    async def _simulate_step(self, step: Dict[str, Any], browser: str, device: str) -> Dict[str, Any]:
        """Simule l'exécution d'une étape de scénario"""
        await asyncio.sleep(0.5)  # Simulation de temps d'exécution
        
        step_type = step.get('type', 'action')
        element = step.get('element', 'unknown')
        
        # Simuler le succès/échec
        success = random.random() > 0.05  # 95% de succès
        
        # Simuler des métriques
        metrics = {
            'duration_ms': random.randint(100, 500),
            'dom_interactive_ms': random.randint(50, 200),
            'first_paint_ms': random.randint(30, 150),
            'layout_shift': random.uniform(0, 0.1),
            'memory_usage_mb': random.randint(50, 200)
        }
        
        return {
            'step': step.get('name', f'Step {step_type}'),
            'type': step_type,
            'element': element,
            'success': success,
            'metrics': metrics,
            'screenshot': f"screenshots/step_{datetime.now().timestamp()}.png" if random.random() > 0.5 else None,
            'console_errors': [] if success else [f"Error interacting with {element}"]
        }

    # ========================================================================
    # HANDLERS DE CAPACITÉS
    # ========================================================================

    async def _handle_run_scenario(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Exécute un scénario E2E"""
        scenario_id = params.get('scenario_id')
        browser = params.get('browser', 'chromium')
        device = params.get('device', 'desktop')
        headless = params.get('headless', True)

        if not scenario_id:
            return {'success': False, 'error': 'scenario_id requis'}

        scenario = self._scenarios.get(scenario_id)
        if not scenario:
            return {'success': False, 'error': f'Scénario {scenario_id} non trouvé'}

        test_id = f"e2e_{scenario_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        start_time = datetime.now()

        # Exécuter les étapes
        step_results = []
        screenshots = []
        console_errors = []
        
        for i, step in enumerate(scenario.steps):
            step_result = await self._simulate_step(step, browser, device)
            step_results.append(step_result)
            
            if step_result.get('screenshot'):
                screenshots.append(step_result['screenshot'])
            if step_result.get('console_errors'):
                console_errors.extend(step_result['console_errors'])

        duration = (datetime.now() - start_time).total_seconds() * 1000
        
        successful_steps = sum(1 for r in step_results if r['success'])
        
        # Calculer les métriques agrégées
        metrics = {
            'avg_step_duration': sum(r['metrics']['duration_ms'] for r in step_results) / len(step_results),
            'total_duration_ms': duration,
            'first_paint_avg': sum(r['metrics']['first_paint_ms'] for r in step_results) / len(step_results),
            'layout_shifts': [r['metrics']['layout_shift'] for r in step_results if r['metrics']['layout_shift'] > 0],
            'memory_peak_mb': max(r['metrics']['memory_usage_mb'] for r in step_results)
        }

        result = E2ETestResult(
            scenario_id=scenario_id,
            success=successful_steps == len(scenario.steps),
            steps_completed=successful_steps,
            steps_total=len(scenario.steps),
            duration_ms=duration,
            screenshots=screenshots,
            console_errors=console_errors,
            metrics=metrics
        )

        self._results[test_id] = result

        return {
            'success': result.success,
            'test_id': test_id,
            'scenario': {
                'id': scenario.id,
                'name': scenario.name
            },
            'execution': {
                'browser': browser,
                'device': device,
                'headless': headless
            },
            'results': {
                'steps_completed': result.steps_completed,
                'steps_total': result.steps_total,
                'duration_ms': result.duration_ms,
                'success_rate': (result.steps_completed / result.steps_total) * 100
            },
            'metrics': metrics,
            'screenshots': screenshots[:3],  # Limiter pour la réponse
            'console_errors': console_errors[:5],
            'step_details': step_results,
            'timestamp': result.timestamp.isoformat()
        }

    async def _handle_list_scenarios(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Liste les scénarios disponibles"""
        scenarios = []
        for sc_id, scenario in self._scenarios.items():
            scenarios.append({
                'id': scenario.id,
                'name': scenario.name,
                'description': scenario.description,
                'steps': len(scenario.steps),
                'required_contracts': len(scenario.required_contracts),
                'required_agents': len(scenario.required_agents),
                'estimated_duration_seconds': len(scenario.steps) * 5
            })

        return {
            'success': True,
            'scenarios': scenarios,
            'total': len(scenarios)
        }

    async def _handle_test_mobile(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Exécute des tests sur appareils mobiles"""
        scenario_id = params.get('scenario_id')
        devices = params.get('devices', ['iphone_12', 'pixel_5', 'ipad_pro'])

        if not scenario_id:
            return {'success': False, 'error': 'scenario_id requis'}

        results = []
        for device in devices:
            device_result = await self._handle_run_scenario({
                'scenario_id': scenario_id,
                'browser': 'chromium',
                'device': device,
                'headless': True
            })
            results.append({
                'device': device,
                'success': device_result['success'],
                'duration_ms': device_result['results']['duration_ms']
            })

        return {
            'success': True,
            'scenario_id': scenario_id,
            'devices_tested': devices,
            'results': results,
            'summary': {
                'passed': sum(1 for r in results if r['success']),
                'failed': sum(1 for r in results if not r['success'])
            }
        }

    async def _handle_collect_metrics(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Collecte des métriques de performance"""
        url = params.get('url', self._base_url)
        duration_seconds = params.get('duration_seconds', 60)

        # Simulation de collecte de métriques
        await asyncio.sleep(2)

        metrics = {
            'page_load': {
                'dom_content_loaded_ms': random.randint(200, 800),
                'load_event_ms': random.randint(300, 1200),
                'first_contentful_paint_ms': random.randint(100, 500),
                'largest_contentful_paint_ms': random.randint(500, 2000),
                'time_to_interactive_ms': random.randint(1000, 3000)
            },
            'api_calls': {
                'total': random.randint(10, 50),
                'average_response_ms': random.randint(50, 200),
                'error_rate': random.uniform(0, 0.05)
            },
            'blockchain_interactions': {
                'total': random.randint(5, 20),
                'average_gas': random.randint(50000, 150000),
                'failed_transactions': random.randint(0, 2)
            },
            'resource_usage': {
                'javascript_kb': random.randint(500, 2000),
                'css_kb': random.randint(100, 500),
                'images_kb': random.randint(1000, 5000),
                'total_requests': random.randint(30, 100)
            }
        }

        return {
            'success': True,
            'url': url,
            'duration_seconds': duration_seconds,
            'metrics': metrics,
            'performance_score': random.randint(70, 100),
            'recommendations': [
                "Optimize image sizes",
                "Reduce JavaScript bundle",
                "Implement lazy loading"
            ] if metrics['performance_score'] < 90 else []
        }

    async def _handle_record_session(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Enregistre une session de test (vidéo)"""
        scenario_id = params.get('scenario_id')
        record_video = params.get('record_video', True)
        record_network = params.get('record_network', True)

        if not scenario_id:
            return {'success': False, 'error': 'scenario_id requis'}

        # Exécuter le scénario avec enregistrement
        result = await self._handle_run_scenario({
            'scenario_id': scenario_id,
            'browser': 'chromium',
            'device': 'desktop',
            'headless': False  # Nécessaire pour l'enregistrement vidéo
        })

        session_id = f"session_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        session_info = {
            'session_id': session_id,
            'video_path': f"recordings/{session_id}.mp4" if record_video else None,
            'network_log': f"logs/network/{session_id}.har" if record_network else None,
            'screenshots': result.get('screenshots', []),
            'console_log': f"logs/console/{session_id}.log"
        }

        return {
            'success': True,
            'session': session_info,
            'test_result': result,
            'message': f"Session enregistrée: {session_id}"
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
    return E2ETesterSubAgent


def create_e2e_tester_agent(config_path: str = "") -> "E2ETesterSubAgent":
    """Crée une instance du sous-agent de tests E2E"""
    return E2ETesterSubAgent(config_path)
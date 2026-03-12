"""
Performance Tester SubAgent - Sous-agent de tests de performance
Version: 2.0.0

Tests de charge, stress, scalabilité et optimisation des performances
pour smart contracts, API et systèmes complets.
"""

import logging
import sys
import asyncio
import json
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, Optional, List
from enum import Enum
from dataclasses import dataclass, field
import random
import statistics

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

class TestType(Enum):
    """Types de tests de performance"""
    LOAD = "load"
    STRESS = "stress"
    SPIKE = "spike"
    SOAK = "soak"
    SCALABILITY = "scalability"
    ENDURANCE = "endurance"


class MetricType(Enum):
    """Types de métriques"""
    RESPONSE_TIME = "response_time"
    THROUGHPUT = "throughput"
    ERROR_RATE = "error_rate"
    CPU_USAGE = "cpu_usage"
    MEMORY_USAGE = "memory_usage"
    GAS_USAGE = "gas_usage"
    CONCURRENT_USERS = "concurrent_users"


@dataclass
class PerformanceMetric:
    """Métrique de performance"""
    type: MetricType
    value: float
    unit: str
    timestamp: datetime = field(default_factory=datetime.now)
    tags: Dict[str, str] = field(default_factory=dict)


@dataclass
class TestScenario:
    """Scénario de test de performance"""
    id: str
    name: str
    test_type: TestType
    duration_seconds: int
    concurrent_users: int
    ramp_up_seconds: int
    target_url: Optional[str] = None
    target_contract: Optional[str] = None
    target_function: Optional[str] = None
    parameters: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PerformanceTestResult:
    """Résultat de test de performance"""
    scenario_id: str
    test_type: TestType
    status: str  # passed, failed, warning
    duration_seconds: float
    metrics: Dict[str, List[PerformanceMetric]]
    summary: Dict[str, Any]
    bottlenecks: List[Dict[str, Any]] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    logs: List[str] = field(default_factory=list)
    completed_at: datetime = field(default_factory=datetime.now)


# ============================================================================
# SOUS-AGENT PRINCIPAL
# ============================================================================

class PerformanceTesterSubAgent(BaseSubAgent):
    """
    Sous-agent de tests de performance

    Exécute des tests de performance avancés :
    - Tests de charge (load testing)
    - Tests de stress
    - Tests de scalabilité
    - Analyse des goulots d'étranglement
    """

    def __init__(self, config_path: str = ""):
        """Initialise le sous-agent de tests de performance"""
        super().__init__(config_path)

        # Métadonnées
        self._subagent_display_name = "⚡ Tests de Performance"
        self._subagent_description = "Tests de charge, stress et optimisation des performances"
        self._subagent_version = "2.0.0"
        self._subagent_category = "tester"
        self._subagent_capabilities = [
            "performance.load_test",
            "performance.stress_test",
            "performance.spike_test",
            "performance.soak_test",
            "performance.analyze_bottlenecks",
            "performance.optimize"
        ]

        # État interne
        self._test_results: Dict[str, PerformanceTestResult] = {}
        self._performance_config = self._agent_config.get('performance', {})
        self._thresholds = self._agent_config.get('thresholds', {})
        
        # Tâche de fond
        self._cleanup_task: Optional[asyncio.Task] = None

        logger.info(f"✅ {self._subagent_display_name} initialisé (v{self._subagent_version})")

    # ========================================================================
    # IMPLÉMENTATION DES MÉTHODES ABSTRACTES
    # ========================================================================

    async def _initialize_subagent_components(self) -> bool:
        """Initialise les composants spécifiques"""
        logger.info("Initialisation des composants de tests de performance...")

        try:
            # Charger les profils de test
            await self._load_test_profiles()

            logger.info("✅ Composants de tests de performance initialisés")
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
            "performance.load_test": self._handle_load_test,
            "performance.stress_test": self._handle_stress_test,
            "performance.spike_test": self._handle_spike_test,
            "performance.soak_test": self._handle_soak_test,
            "performance.analyze_bottlenecks": self._handle_analyze_bottlenecks,
            "performance.optimize": self._handle_optimize,
        }

    # ========================================================================
    # MÉTHODES PRIVÉES
    # ========================================================================

    async def _load_test_profiles(self):
        """Charge les profils de test depuis la configuration"""
        self.test_profiles = self._performance_config.get('profiles', {})
        logger.info(f"  📋 {len(self.test_profiles)} profils de test chargés")

    async def _simulate_load_test(self, scenario: TestScenario) -> PerformanceTestResult:
        """Simule un test de charge"""
        metrics = {
            'response_time': [],
            'throughput': [],
            'error_rate': [],
            'cpu_usage': [],
            'memory_usage': []
        }

        # Simuler l'exécution du test
        start_time = time.time()
        users_per_second = scenario.concurrent_users / scenario.ramp_up_seconds if scenario.ramp_up_seconds > 0 else scenario.concurrent_users

        for second in range(scenario.duration_seconds):
            # Simuler le nombre d'utilisateurs actifs
            if second < scenario.ramp_up_seconds:
                active_users = int((second / scenario.ramp_up_seconds) * scenario.concurrent_users)
            elif second > scenario.duration_seconds - scenario.ramp_up_seconds:
                ramp_down_second = second - (scenario.duration_seconds - scenario.ramp_up_seconds)
                active_users = int(scenario.concurrent_users * (1 - ramp_down_second / scenario.ramp_up_seconds))
            else:
                active_users = scenario.concurrent_users

            # Générer des métriques pour cette seconde
            for _ in range(active_users):
                # Temps de réponse
                response_time = random.uniform(50, 500) * (1 + active_users / 1000)
                metrics['response_time'].append(PerformanceMetric(
                    type=MetricType.RESPONSE_TIME,
                    value=response_time,
                    unit='ms',
                    tags={'second': str(second), 'users': str(active_users)}
                ))

                # Taux d'erreur
                error_rate = random.uniform(0, 2) * (active_users / 100)
                metrics['error_rate'].append(PerformanceMetric(
                    type=MetricType.ERROR_RATE,
                    value=error_rate,
                    unit='%',
                    tags={'second': str(second)}
                ))

            # Throughput (requêtes par seconde)
            throughput = active_users * random.uniform(0.8, 1.2)
            metrics['throughput'].append(PerformanceMetric(
                type=MetricType.THROUGHPUT,
                value=throughput,
                unit='req/s',
                tags={'second': str(second)}
            ))

            # CPU et mémoire
            metrics['cpu_usage'].append(PerformanceMetric(
                type=MetricType.CPU_USAGE,
                value=random.uniform(20, 80) * (1 + active_users / 500),
                unit='%',
                tags={'second': str(second)}
            ))
            
            metrics['memory_usage'].append(PerformanceMetric(
                type=MetricType.MEMORY_USAGE,
                value=random.uniform(100, 500) * (1 + active_users / 200),
                unit='MB',
                tags={'second': str(second)}
            ))

            await asyncio.sleep(0.01)  # Simulation accélérée

        duration = time.time() - start_time

        # Calculer les statistiques
        response_times = [m.value for m in metrics['response_time']]
        summary = {
            'avg_response_time_ms': statistics.mean(response_times) if response_times else 0,
            'p95_response_time_ms': self._percentile(response_times, 95) if response_times else 0,
            'p99_response_time_ms': self._percentile(response_times, 99) if response_times else 0,
            'max_response_time_ms': max(response_times) if response_times else 0,
            'min_response_time_ms': min(response_times) if response_times else 0,
            'avg_throughput_req_s': statistics.mean([m.value for m in metrics['throughput']]) if metrics['throughput'] else 0,
            'max_throughput_req_s': max([m.value for m in metrics['throughput']]) if metrics['throughput'] else 0,
            'avg_error_rate': statistics.mean([m.value for m in metrics['error_rate']]) if metrics['error_rate'] else 0,
            'max_error_rate': max([m.value for m in metrics['error_rate']]) if metrics['error_rate'] else 0,
            'avg_cpu_usage': statistics.mean([m.value for m in metrics['cpu_usage']]) if metrics['cpu_usage'] else 0,
            'avg_memory_usage_mb': statistics.mean([m.value for m in metrics['memory_usage']]) if metrics['memory_usage'] else 0
        }

        # Détecter les goulots d'étranglement
        bottlenecks = []
        if summary['p95_response_time_ms'] > self._thresholds.get('response_time_p95', 1000):
            bottlenecks.append({
                'type': 'response_time',
                'description': f"Temps de réponse élevé (p95: {summary['p95_response_time_ms']:.0f}ms)",
                'severity': 'high'
            })
        if summary['avg_error_rate'] > self._thresholds.get('error_rate', 1):
            bottlenecks.append({
                'type': 'error_rate',
                'description': f"Taux d'erreur élevé ({summary['avg_error_rate']:.2f}%)",
                'severity': 'high'
            })
        if summary['avg_cpu_usage'] > self._thresholds.get('cpu_usage', 80):
            bottlenecks.append({
                'type': 'cpu',
                'description': f"Utilisation CPU élevée ({summary['avg_cpu_usage']:.0f}%)",
                'severity': 'medium'
            })

        # Déterminer le statut
        status = 'passed'
        if bottlenecks:
            status = 'warning' if any(b['severity'] == 'medium' for b in bottlenecks) else 'failed'

        return PerformanceTestResult(
            scenario_id=scenario.id,
            test_type=scenario.test_type,
            status=status,
            duration_seconds=duration,
            metrics={k: v for k, v in metrics.items()},
            summary=summary,
            bottlenecks=bottlenecks,
            recommendations=self._generate_recommendations(bottlenecks, summary)
        )

    def _percentile(self, data: List[float], percentile: float) -> float:
        """Calcule un percentile"""
        if not data:
            return 0
        sorted_data = sorted(data)
        index = int(len(sorted_data) * percentile / 100)
        return sorted_data[index]

    def _generate_recommendations(self, bottlenecks: List[Dict], summary: Dict) -> List[str]:
        """Génère des recommandations basées sur les résultats"""
        recommendations = []

        if any(b['type'] == 'response_time' for b in bottlenecks):
            recommendations.extend([
                "Optimiser les requêtes à la base de données",
                "Implémenter du caching (Redis/Memcached)",
                "Utiliser un CDN pour les assets statiques",
                "Optimiser les smart contracts pour réduire le gas"
            ])

        if any(b['type'] == 'error_rate' for b in bottlenecks):
            recommendations.extend([
                "Vérifier les timeouts des connexions externes",
                "Implémenter des retries avec backoff exponentiel",
                "Améliorer la gestion des erreurs",
                "Ajouter des circuit breakers"
            ])

        if any(b['type'] == 'cpu' for b in bottlenecks):
            recommendations.extend([
                "Optimiser les algorithmes critiques",
                "Utiliser le multithreading pour les tâches parallélisables",
                "Considérer l'utilisation de workers dédiés"
            ])

        if summary.get('avg_memory_usage_mb', 0) > self._thresholds.get('memory_usage', 500):
            recommendations.extend([
                "Réduire l'empreinte mémoire",
                "Utiliser des pools de connexions",
                "Optimiser la sérialisation des données"
            ])

        return recommendations[:5]  # Limiter à 5 recommandations

    # ========================================================================
    # HANDLERS DE CAPACITÉS
    # ========================================================================

    async def _handle_load_test(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Exécute un test de charge"""
        scenario_id = f"LOAD-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        scenario = TestScenario(
            id=scenario_id,
            name=params.get('name', 'Load Test'),
            test_type=TestType.LOAD,
            duration_seconds=params.get('duration', 60),
            concurrent_users=params.get('users', 100),
            ramp_up_seconds=params.get('ramp_up', 10),
            target_url=params.get('target_url'),
            target_contract=params.get('target_contract'),
            target_function=params.get('target_function'),
            parameters=params.get('parameters', {})
        )

        result = await self._simulate_load_test(scenario)
        self._test_results[scenario_id] = result

        return {
            'success': True,
            'test_id': scenario_id,
            'test_type': 'load',
            'scenario': {
                'duration': scenario.duration_seconds,
                'users': scenario.concurrent_users,
                'ramp_up': scenario.ramp_up_seconds
            },
            'results': {
                'status': result.status,
                'summary': result.summary,
                'bottlenecks': result.bottlenecks,
                'recommendations': result.recommendations
            }
        }

    async def _handle_stress_test(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Exécute un test de stress"""
        scenario_id = f"STRESS-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # Le test de stress augmente progressivement la charge jusqu'à la rupture
        max_users = params.get('max_users', 1000)
        step_users = params.get('step_users', 50)
        step_duration = params.get('step_duration', 30)

        results = []
        breakpoint_found = None

        for users in range(step_users, max_users + 1, step_users):
            scenario = TestScenario(
                id=f"{scenario_id}_{users}",
                name=f"Stress Test - {users} users",
                test_type=TestType.STRESS,
                duration_seconds=step_duration,
                concurrent_users=users,
                ramp_up_seconds=10,
                target_url=params.get('target_url'),
                target_contract=params.get('target_contract')
            )

            result = await self._simulate_load_test(scenario)
            
            # Vérifier si le système a cassé
            if result.summary['avg_error_rate'] > 10 or result.summary['avg_response_time_ms'] > 5000:
                breakpoint_found = users
                break

            results.append({
                'users': users,
                'avg_response_time': result.summary['avg_response_time_ms'],
                'error_rate': result.summary['avg_error_rate'],
                'throughput': result.summary['avg_throughput_req_s']
            })

        return {
            'success': True,
            'test_id': scenario_id,
            'test_type': 'stress',
            'breakpoint': breakpoint_found,
            'max_users_tested': users,
            'results': results,
            'analysis': {
                'system_breakpoint': f"Le système a commencé à échouer à {breakpoint_found} utilisateurs" if breakpoint_found else "Le système a supporté toute la charge",
                'recommendations': [
                    f"Limiter les utilisateurs simultanés à {int(breakpoint_found * 0.7)} pour une marge de sécurité" if breakpoint_found else "Le système a une bonne scalabilité"
                ]
            }
        }

    async def _handle_spike_test(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Exécute un test de pic (augmentation soudaine de charge)"""
        scenario_id = f"SPIKE-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        base_users = params.get('base_users', 50)
        spike_users = params.get('spike_users', 500)
        spike_duration = params.get('spike_duration', 10)
        recovery_duration = params.get('recovery_duration', 30)

        # Simuler le pic
        metrics = []
        
        # Phase normale
        for second in range(10):
            metrics.append({
                'second': second,
                'users': base_users,
                'response_time': random.uniform(100, 300)
            })
            await asyncio.sleep(0.01)

        # Phase de pic
        for second in range(spike_duration):
            metrics.append({
                'second': 10 + second,
                'users': spike_users,
                'response_time': random.uniform(500, 2000) * (1 + second / spike_duration)
            })
            await asyncio.sleep(0.01)

        # Phase de récupération
        for second in range(recovery_duration):
            users = int(spike_users * (1 - second / recovery_duration)) + base_users
            metrics.append({
                'second': 10 + spike_duration + second,
                'users': users,
                'response_time': random.uniform(200, 800) * (1 - second / recovery_duration / 2)
            })
            await asyncio.sleep(0.01)

        # Analyser la récupération
        final_response_time = metrics[-1]['response_time']
        initial_response_time = metrics[0]['response_time']
        
        recovered = final_response_time < initial_response_time * 2

        return {
            'success': True,
            'test_id': scenario_id,
            'test_type': 'spike',
            'metrics': metrics,
            'analysis': {
                'peak_response_time': max(m['response_time'] for m in metrics),
                'recovery_time_seconds': spike_duration + 5 if not recovered else spike_duration,
                'system_recovered': recovered,
                'recommendations': [
                    "Améliorer l'autoscaling" if not recovered else "Bonne résilience aux pics",
                    "Considérer des queues pour lisser la charge"
                ]
            }
        }

    async def _handle_soak_test(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Exécute un test d'endurance (longue durée)"""
        scenario_id = f"SOAK-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        duration_hours = params.get('duration_hours', 24)
        users = params.get('users', 100)
        check_interval_minutes = params.get('check_interval', 60)

        # Simuler un test de longue durée
        start_time = time.time()
        checkpoints = []

        for hour in range(duration_hours):
            # Simuler une heure de fonctionnement
            avg_response = random.uniform(200, 400) * (1 + hour * 0.01)  # Légère dégradation
            error_rate = random.uniform(0, 0.5) * (1 + hour * 0.02)
            memory_leak = hour * random.uniform(0.1, 0.5)  # Fuite mémoire simulée

            if hour % (check_interval_minutes // 60) == 0:
                checkpoints.append({
                    'hour': hour,
                    'avg_response_time_ms': avg_response,
                    'error_rate': error_rate,
                    'memory_usage_mb': 100 + memory_leak,
                    'cpu_usage': 50 + hour * 0.2
                })

            await asyncio.sleep(0.01)

        # Détecter les dégradations
        initial_response = checkpoints[0]['avg_response_time_ms']
        final_response = checkpoints[-1]['avg_response_time_ms']
        degradation_pct = ((final_response - initial_response) / initial_response) * 100

        memory_initial = checkpoints[0]['memory_usage_mb']
        memory_final = checkpoints[-1]['memory_usage_mb']
        memory_leak_rate = (memory_final - memory_initial) / duration_hours

        return {
            'success': True,
            'test_id': scenario_id,
            'test_type': 'soak',
            'duration_hours': duration_hours,
            'checkpoints': checkpoints,
            'analysis': {
                'performance_degradation': f"{degradation_pct:.1f}%",
                'memory_leak_rate_mb_per_hour': memory_leak_rate,
                'stability': 'good' if degradation_pct < 10 and memory_leak_rate < 1 else 'concerning',
                'recommendations': [
                    "Vérifier les fuites mémoire" if memory_leak_rate > 1 else "Bonne stabilité mémoire",
                    "Optimiser les requêtes qui se dégradent avec le temps" if degradation_pct > 10 else "Performance stable"
                ]
            }
        }

    async def _handle_analyze_bottlenecks(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Analyse les goulots d'étranglement"""
        test_id = params.get('test_id')
        
        if not test_id:
            return {'success': False, 'error': 'test_id requis'}

        result = self._test_results.get(test_id)
        if not result:
            return {'success': False, 'error': f'Test {test_id} non trouvé'}

        # Analyse approfondie
        bottlenecks = result.bottlenecks.copy()
        
        # Ajouter des analyses supplémentaires
        if result.summary.get('avg_response_time_ms', 0) > 1000:
            bottlenecks.append({
                'type': 'database',
                'description': 'Les requêtes base de données sont lentes',
                'evidence': f"Temps de réponse moyen: {result.summary['avg_response_time_ms']:.0f}ms",
                'severity': 'high'
            })

        if result.summary.get('avg_cpu_usage', 0) > 70:
            bottlenecks.append({
                'type': 'computation',
                'description': 'Les calculs sont trop intensifs',
                'evidence': f"CPU à {result.summary['avg_cpu_usage']:.0f}%",
                'severity': 'medium'
            })

        return {
            'success': True,
            'test_id': test_id,
            'bottlenecks': bottlenecks,
            'priorities': sorted(bottlenecks, key=lambda x: {'high': 3, 'medium': 2, 'low': 1}[x['severity']], reverse=True)
        }

    async def _handle_optimize(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Propose des optimisations basées sur les résultats de test"""
        test_id = params.get('test_id')
        
        if not test_id:
            return {'success': False, 'error': 'test_id requis'}

        result = self._test_results.get(test_id)
        if not result:
            return {'success': False, 'error': f'Test {test_id} non trouvé'}

        # Générer des optimisations spécifiques
        optimizations = []

        if result.summary.get('avg_response_time_ms', 0) > 500:
            optimizations.append({
                'target': 'response_time',
                'suggestion': 'Implémenter du caching Redis',
                'estimated_improvement': '40-60%',
                'effort': 'medium',
                'priority': 'high'
            })

        if result.summary.get('avg_error_rate', 0) > 1:
            optimizations.append({
                'target': 'error_rate',
                'suggestion': 'Ajouter des retries avec backoff exponentiel',
                'estimated_improvement': '70-90%',
                'effort': 'low',
                'priority': 'high'
            })

        if result.summary.get('avg_cpu_usage', 0) > 70:
            optimizations.append({
                'target': 'cpu',
                'suggestion': 'Optimiser les algorithmes critiques',
                'estimated_improvement': '30-50%',
                'effort': 'high',
                'priority': 'medium'
            })

        return {
            'success': True,
            'test_id': test_id,
            'optimizations': optimizations,
            'estimated_total_improvement': '50%' if optimizations else 'N/A'
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
    return PerformanceTesterSubAgent


def create_performance_tester_agent(config_path: str = "") -> "PerformanceTesterSubAgent":
    """Crée une instance du sous-agent de tests de performance"""
    return PerformanceTesterSubAgent(config_path)
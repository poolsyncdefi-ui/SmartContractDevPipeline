"""
Performance Optimizer SubAgent - Optimisateur de performance
Version: 2.0.0

Optimise les performances avec :
- Analyse en temps réel des métriques
- Détection automatique des goulots d'étranglement
- Suggestions d'optimisation intelligentes
- Ajustement automatique des paramètres
- Prédiction des performances futures
"""

import logging
import sys
import asyncio
import json
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple, Callable
from enum import Enum
from dataclasses import dataclass, field
from collections import deque, defaultdict
import statistics
import math

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

class OptimizationTarget(Enum):
    """Cibles d'optimisation"""
    THROUGHPUT = "throughput"
    LATENCY = "latency"
    RESOURCES = "resources"
    RELIABILITY = "reliability"
    COST = "cost"


class BottleneckType(Enum):
    """Types de goulots d'étranglement"""
    CPU = "cpu"
    MEMORY = "memory"
    IO = "io"
    NETWORK = "network"
    QUEUE = "queue"
    LOCK = "lock"
    DATABASE = "database"


class OptimizationStrategy(Enum):
    """Stratégies d'optimisation"""
    SCALE_OUT = "scale_out"
    SCALE_UP = "scale_up"
    CACHE_OPTIMIZATION = "cache_optimization"
    BATCH_PROCESSING = "batch_processing"
    COMPRESSION = "compression"
    QUERY_OPTIMIZATION = "query_optimization"
    CONNECTION_POOLING = "connection_pooling"
    LOAD_BALANCING = "load_balancing"


@dataclass
class PerformanceMetrics:
    """Métriques de performance"""
    timestamp: datetime = field(default_factory=datetime.now)
    throughput: float = 0.0  # messages/seconde
    latency_p50: float = 0.0  # ms
    latency_p95: float = 0.0  # ms
    latency_p99: float = 0.0  # ms
    error_rate: float = 0.0   # pourcentage
    cpu_usage: float = 0.0    # pourcentage
    memory_usage: float = 0.0  # pourcentage
    queue_size: int = 0
    active_connections: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convertit en dictionnaire"""
        return {
            "timestamp": self.timestamp.isoformat(),
            "throughput": round(self.throughput, 2),
            "latency_p50": round(self.latency_p50, 2),
            "latency_p95": round(self.latency_p95, 2),
            "latency_p99": round(self.latency_p99, 2),
            "error_rate": round(self.error_rate, 2),
            "cpu_usage": round(self.cpu_usage, 2),
            "memory_usage": round(self.memory_usage, 2),
            "queue_size": self.queue_size,
            "active_connections": self.active_connections
        }


@dataclass
class Bottleneck:
    """Goulot d'étranglement détecté"""
    type: BottleneckType
    severity: float  # 0-100
    component: str
    description: str
    metrics: PerformanceMetrics
    suggestions: List[str] = field(default_factory=list)


@dataclass
class OptimizationSuggestion:
    """Suggestion d'optimisation"""
    id: str
    target: OptimizationTarget
    strategy: OptimizationStrategy
    expected_impact: float  # pourcentage d'amélioration estimé
    effort: str  # low, medium, high
    description: str
    implementation: List[str]
    metrics_before: PerformanceMetrics
    metrics_after: Optional[PerformanceMetrics] = None
    applied: bool = False
    created_at: datetime = field(default_factory=datetime.now)
    applied_at: Optional[datetime] = None


@dataclass
class PerformanceReport:
    """Rapport de performance"""
    id: str
    generated_at: datetime
    time_window_minutes: int
    metrics_summary: Dict[str, Any]
    bottlenecks: List[Bottleneck]
    suggestions: List[OptimizationSuggestion]
    trends: Dict[str, float]
    recommendations: List[str]
    performance_score: float


# ============================================================================
# SOUS-AGENT PRINCIPAL
# ============================================================================

class PerformanceOptimizerSubAgent(BaseSubAgent):
    """
    Sous-agent Performance Optimizer - Optimisateur de performance

    Analyse et optimise les performances avec :
    - Surveillance continue des métriques
    - Détection automatique des goulots d'étranglement
    - Suggestions d'optimisation intelligentes
    - Ajustement automatique des paramètres
    - Prédiction des tendances
    """

    def __init__(self, config_path: str = ""):
        """Initialise l'optimisateur de performance"""
        super().__init__(config_path)

        # Métadonnées
        self._subagent_display_name = "⚡ Performance Optimizer"
        self._subagent_description = "Optimisateur de performance"
        self._subagent_version = "2.0.0"
        self._subagent_category = "communication"
        self._subagent_capabilities = [
            "perf.analyze",
            "perf.optimize",
            "perf.tune",
            "perf.bottlenecks",
            "perf.predict",
            "perf.report"
        ]

        # État interne
        self._metrics_history: deque = deque(maxlen=10000)  # Garder 10000 points
        self._suggestions: Dict[str, OptimizationSuggestion] = {}
        self._bottlenecks: List[Bottleneck] = []
        self._optimization_history: List[OptimizationSuggestion] = []

        # Configuration
        self._default_config = self._agent_config.get('performance_optimizer', {}).get('defaults', {})
        self._metric_config = self._agent_config.get('performance_optimizer', {}).get('metrics', [])
        self._thresholds = self._agent_config.get('performance_optimizer', {}).get('thresholds', {})

        # Tâche d'optimisation automatique
        self._optimization_task: Optional[asyncio.Task] = None
        self._analysis_task: Optional[asyncio.Task] = None

        logger.info(f"✅ {self._subagent_display_name} initialisé")

    # ========================================================================
    # IMPLÉMENTATION DES MÉTHODES ABSTRACTES
    # ========================================================================

    async def _initialize_subagent_components(self) -> bool:
        """Initialise les composants spécifiques"""
        logger.info("Initialisation des composants Performance Optimizer...")

        # Démarrer les tâches de fond
        analysis_window = self._default_config.get('analysis_window', 3600)
        opt_interval = self._default_config.get('optimization_interval', 300)

        self._analysis_task = asyncio.create_task(self._analysis_loop(analysis_window))
        if self._default_config.get('auto_tune', False):
            self._optimization_task = asyncio.create_task(self._optimization_loop(opt_interval))

        logger.info("✅ Composants Performance Optimizer initialisés")
        return True

    async def _initialize_components(self) -> bool:
        """Implémentation requise par BaseAgent"""
        return await self._initialize_subagent_components()

    def _get_capability_handlers(self) -> Dict[str, Any]:
        """Retourne les handlers spécifiques"""
        return {
            "perf.analyze": self._handle_analyze,
            "perf.optimize": self._handle_optimize,
            "perf.tune": self._handle_tune,
            "perf.bottlenecks": self._handle_bottlenecks,
            "perf.predict": self._handle_predict,
            "perf.report": self._handle_report,
        }

    # ========================================================================
    # COLLECTE ET ANALYSE DES MÉTRIQUES
    # ========================================================================

    async def _collect_metrics(self) -> PerformanceMetrics:
        """Collecte les métriques actuelles"""
        # Dans un vrai système, on interrogerait les composants
        # Pour la simulation, on génère des valeurs réalistes

        # Simuler des variations
        import random

        base_throughput = 1000 + random.randint(-200, 200)
        base_latency = 50 + random.randint(-10, 30)

        metrics = PerformanceMetrics(
            throughput=max(0, base_throughput),
            latency_p50=max(1, base_latency),
            latency_p95=max(1, base_latency * 1.5 + random.randint(-10, 20)),
            latency_p99=max(1, base_latency * 2.0 + random.randint(-10, 30)),
            error_rate=random.uniform(0, 2),
            cpu_usage=random.uniform(30, 80),
            memory_usage=random.uniform(40, 70),
            queue_size=random.randint(0, 500),
            active_connections=random.randint(50, 200)
        )

        self._metrics_history.append(metrics)
        return metrics

    async def _analyze_metrics(self, time_window_seconds: int) -> Dict[str, Any]:
        """Analyse les métriques sur une période"""
        cutoff = datetime.now() - timedelta(seconds=time_window_seconds)

        relevant = [m for m in self._metrics_history if m.timestamp >= cutoff]

        if not relevant:
            return {
                "error": "Pas assez de données"
            }

        # Calculer les statistiques
        throughputs = [m.throughput for m in relevant]
        latencies_p95 = [m.latency_p95 for m in relevant]
        error_rates = [m.error_rate for m in relevant]
        cpu_usages = [m.cpu_usage for m in relevant]

        result = {
            "period_seconds": time_window_seconds,
            "data_points": len(relevant),
            "throughput": {
                "avg": statistics.mean(throughputs),
                "max": max(throughputs),
                "min": min(throughputs),
                "trend": self._calculate_trend(throughputs)
            },
            "latency_p95": {
                "avg": statistics.mean(latencies_p95),
                "max": max(latencies_p95),
                "p95": statistics.quantiles(latencies_p95, n=20)[18] if len(latencies_p95) > 20 else max(latencies_p95),
                "trend": self._calculate_trend(latencies_p95)
            },
            "error_rate": {
                "avg": statistics.mean(error_rates),
                "max": max(error_rates),
                "trend": self._calculate_trend(error_rates)
            },
            "cpu_usage": {
                "avg": statistics.mean(cpu_usages),
                "max": max(cpu_usages),
                "trend": self._calculate_trend(cpu_usages)
            }
        }

        return result

    def _calculate_trend(self, values: List[float]) -> str:
        """Calcule la tendance d'une série de valeurs"""
        if len(values) < 2:
            return "stable"

        # Comparer la première moitié à la seconde
        half = len(values) // 2
        first_half = values[:half]
        second_half = values[half:]

        avg_first = statistics.mean(first_half) if first_half else 0
        avg_second = statistics.mean(second_half) if second_half else 0

        diff = (avg_second - avg_first) / max(1, avg_first)

        if diff > 0.1:
            return "increasing"
        elif diff < -0.1:
            return "decreasing"
        else:
            return "stable"

    # ========================================================================
    # DÉTECTION DES GOULOTS D'ÉTRANGLEMENT
    # ========================================================================

    async def _detect_bottlenecks(self, metrics: PerformanceMetrics) -> List[Bottleneck]:
        """Détecte les goulots d'étranglement actuels"""
        bottlenecks = []

        # Vérifier la CPU
        if metrics.cpu_usage > 90:
            bottlenecks.append(Bottleneck(
                type=BottleneckType.CPU,
                severity=metrics.cpu_usage,
                component="system",
                description="Utilisation CPU critique",
                metrics=metrics,
                suggestions=["Augmenter les ressources CPU", "Optimiser le code", "Distribuer la charge"]
            ))
        elif metrics.cpu_usage > 75:
            bottlenecks.append(Bottleneck(
                type=BottleneckType.CPU,
                severity=metrics.cpu_usage,
                component="system",
                description="Utilisation CPU élevée",
                metrics=metrics,
                suggestions=["Surveiller l'utilisation CPU", "Vérifier les processus"]
            ))

        # Vérifier la mémoire
        if metrics.memory_usage > 90:
            bottlenecks.append(Bottleneck(
                type=BottleneckType.MEMORY,
                severity=metrics.memory_usage,
                component="system",
                description="Utilisation mémoire critique",
                metrics=metrics,
                suggestions=["Augmenter la mémoire", "Optimiser le cache", "Vérifier les fuites mémoire"]
            ))

        # Vérifier la latence
        critical_latency = self._thresholds.get('critical_latency_ms', 1000)
        high_latency = self._thresholds.get('high_latency_ms', 500)

        if metrics.latency_p95 > critical_latency:
            bottlenecks.append(Bottleneck(
                type=BottleneckType.IO,
                severity=min(100, (metrics.latency_p95 / critical_latency) * 100),
                component="processing",
                description="Latence critique",
                metrics=metrics,
                suggestions=["Optimiser les requêtes", "Augmenter le cache", "Revoir l'architecture"]
            ))
        elif metrics.latency_p95 > high_latency:
            bottlenecks.append(Bottleneck(
                type=BottleneckType.IO,
                severity=50 + (metrics.latency_p95 - high_latency) / 10,
                component="processing",
                description="Latence élevée",
                metrics=metrics,
                suggestions=["Analyser les requêtes lentes", "Optimiser les index"]
            ))

        # Vérifier la file d'attente
        queue_threshold = self._thresholds.get('critical_queue_size', 0.9)
        if metrics.queue_size > 1000:
            severity = min(100, (metrics.queue_size / 2000) * 100)
            bottlenecks.append(Bottleneck(
                type=BottleneckType.QUEUE,
                severity=severity,
                component="messaging",
                description="File d'attente importante",
                metrics=metrics,
                suggestions=["Augmenter les consommateurs", "Optimiser le traitement", "Batch processing"]
            ))

        # Vérifier le taux d'erreur
        critical_error = self._thresholds.get('critical_error_rate', 5.0)
        high_error = self._thresholds.get('high_error_rate', 2.0)

        if metrics.error_rate > critical_error:
            bottlenecks.append(Bottleneck(
                type=BottleneckType.IO,
                severity=min(100, metrics.error_rate * 10),
                component="system",
                description="Taux d'erreur critique",
                metrics=metrics,
                suggestions=["Vérifier les services externes", "Analyser les logs", "Circuit breaker"]
            ))
        elif metrics.error_rate > high_error:
            bottlenecks.append(Bottleneck(
                type=BottleneckType.IO,
                severity=metrics.error_rate * 5,
                component="system",
                description="Taux d'erreur élevé",
                metrics=metrics,
                suggestions=["Surveiller les erreurs", "Vérifier les dépendances"]
            ))

        self._bottlenecks = bottlenecks
        return bottlenecks

    # ========================================================================
    # GÉNÉRATION DE SUGGESTIONS D'OPTIMISATION
    # ========================================================================

    async def _generate_suggestions(self, target: OptimizationTarget,
                                     constraints: Dict[str, Any] = None) -> List[OptimizationSuggestion]:
        """Génère des suggestions d'optimisation"""
        import uuid
        suggestions = []

        metrics = await self._collect_metrics()
        bottlenecks = await self._detect_bottlenecks(metrics)

        if target == OptimizationTarget.THROUGHPUT:
            if metrics.throughput < 800:
                suggestions.append(OptimizationSuggestion(
                    id=str(uuid.uuid4()),
                    target=OptimizationTarget.THROUGHPUT,
                    strategy=OptimizationStrategy.SCALE_OUT,
                    expected_impact=30,
                    effort="medium",
                    description="Augmenter le nombre de workers de traitement",
                    implementation=[
                        "Augmenter le pool de threads",
                        "Ajouter des instances de traitement",
                        "Répartir la charge"
                    ],
                    metrics_before=metrics
                ))

                suggestions.append(OptimizationSuggestion(
                    id=str(uuid.uuid4()),
                    target=OptimizationTarget.THROUGHPUT,
                    strategy=OptimizationStrategy.BATCH_PROCESSING,
                    expected_impact=20,
                    effort="low",
                    description="Optimiser le traitement par lots",
                    implementation=[
                        "Augmenter la taille des batches",
                        "Réduire le nombre de requêtes",
                        "Utiliser le streaming"
                    ],
                    metrics_before=metrics
                ))

        elif target == OptimizationTarget.LATENCY:
            if metrics.latency_p95 > 200:
                suggestions.append(OptimizationSuggestion(
                    id=str(uuid.uuid4()),
                    target=OptimizationTarget.LATENCY,
                    strategy=OptimizationStrategy.CACHE_OPTIMIZATION,
                    expected_impact=40,
                    effort="medium",
                    description="Optimiser le cache pour réduire la latence",
                    implementation=[
                        "Augmenter la taille du cache",
                        "Préchauffer le cache",
                        "Utiliser un cache distribué"
                    ],
                    metrics_before=metrics
                ))

                suggestions.append(OptimizationSuggestion(
                    id=str(uuid.uuid4()),
                    target=OptimizationTarget.LATENCY,
                    strategy=OptimizationStrategy.COMPRESSION,
                    expected_impact=15,
                    effort="low",
                    description="Compresser les messages pour accélérer le transfert",
                    implementation=[
                        "Activer la compression gzip",
                        "Optimiser la sérialisation",
                        "Utiliser des formats binaires"
                    ],
                    metrics_before=metrics
                ))

        elif target == OptimizationTarget.RESOURCES:
            if metrics.cpu_usage > 70:
                suggestions.append(OptimizationSuggestion(
                    id=str(uuid.uuid4()),
                    target=OptimizationTarget.RESOURCES,
                    strategy=OptimizationStrategy.CONNECTION_POOLING,
                    expected_impact=25,
                    effort="medium",
                    description="Optimiser le pooling de connexions",
                    implementation=[
                        "Augmenter le pool de connexions",
                        "Réutiliser les connexions",
                        "Timeout plus agressif"
                    ],
                    metrics_before=metrics
                ))

        # Suggestions basées sur les goulots d'étranglement
        for bottleneck in bottlenecks[:2]:  # Top 2
            if bottleneck.type == BottleneckType.CPU:
                suggestions.append(OptimizationSuggestion(
                    id=str(uuid.uuid4()),
                    target=OptimizationTarget.RESOURCES,
                    strategy=OptimizationStrategy.SCALE_UP,
                    expected_impact=30,
                    effort="high",
                    description="Augmenter la puissance CPU",
                    implementation=[
                        "Migrer vers des instances plus puissantes",
                        "Optimiser les algorithmes",
                        "Réduire le logging"
                    ],
                    metrics_before=metrics
                ))

            elif bottleneck.type == BottleneckType.MEMORY:
                suggestions.append(OptimizationSuggestion(
                    id=str(uuid.uuid4()),
                    target=OptimizationTarget.RESOURCES,
                    strategy=OptimizationStrategy.CACHE_OPTIMIZATION,
                    expected_impact=35,
                    effort="medium",
                    description="Optimiser l'utilisation mémoire",
                    implementation=[
                        "Réduire la taille du cache",
                        "Utiliser des structures plus efficaces",
                        "Nettoyer plus fréquemment"
                    ],
                    metrics_before=metrics
                ))

        return suggestions

    # ========================================================================
    # PRÉDICTION DES PERFORMANCES
    # ========================================================================

    async def _predict_performance(self, horizon_minutes: int,
                                    scenario: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Prédit les performances futures"""
        if len(self._metrics_history) < 10:
            return {"error": "Pas assez de données pour la prédiction"}

        # Prendre les dernières métriques
        recent = list(self._metrics_history)[-100:]

        # Calculer les tendances
        throughput_trend = self._calculate_trend([m.throughput for m in recent])
        latency_trend = self._calculate_trend([m.latency_p95 for m in recent])

        # Prédictions simples (extrapolation linéaire)
        last_throughput = recent[-1].throughput
        last_latency = recent[-1].latency_p95
        last_error = recent[-1].error_rate

        # Facteur de croissance (simulé)
        growth_factor = 1.0
        if scenario:
            if scenario.get("load_increase"):
                growth_factor = 1.0 + (scenario["load_increase"] / 100)

        predictions = {
            "horizon_minutes": horizon_minutes,
            "throughput": {
                "current": round(last_throughput, 2),
                "predicted": round(last_throughput * growth_factor * (1 + 0.1 * math.log(horizon_minutes + 1)), 2),
                "trend": throughput_trend
            },
            "latency_p95": {
                "current": round(last_latency, 2),
                "predicted": round(last_latency * (1 + 0.05 * math.log(horizon_minutes + 1)), 2),
                "trend": latency_trend
            },
            "error_rate": {
                "current": round(last_error, 2),
                "predicted": round(min(100, last_error * (1 + 0.02 * math.log(horizon_minutes + 1))), 2)
            },
            "confidence": max(0, 95 - horizon_minutes) / 100  # Moins de confiance pour l'horizon lointain
        }

        # Appliquer le scénario
        if scenario:
            predictions["scenario_applied"] = scenario

        return predictions

    # ========================================================================
    # TÂCHES DE FOND
    # ========================================================================

    async def _analysis_loop(self, window_seconds: int):
        """Boucle d'analyse périodique"""
        logger.info(f"🔄 Boucle d'analyse démarrée (fenêtre: {window_seconds}s)")

        while self._status.value == "ready":
            try:
                # Collecter les métriques
                metrics = await self._collect_metrics()

                # Analyser
                analysis = await self._analyze_metrics(window_seconds)

                # Détecter les goulots
                bottlenecks = await self._detect_bottlenecks(metrics)

                if bottlenecks:
                    logger.info(f"📊 {len(bottlenecks)} goulots détectés")

                await asyncio.sleep(60)  # Collecte toutes les minutes

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"❌ Erreur dans l'analyse: {e}")
                await asyncio.sleep(60)

    async def _optimization_loop(self, interval_seconds: int):
        """Boucle d'optimisation automatique"""
        logger.info(f"🔄 Boucle d'optimisation démarrée (intervalle: {interval_seconds}s)")

        while self._status.value == "ready":
            try:
                await asyncio.sleep(interval_seconds)

                # Analyser les performances
                metrics = await self._collect_metrics()
                bottlenecks = await self._detect_bottlenecks(metrics)

                if bottlenecks:
                    # Générer des suggestions
                    suggestions = await self._generate_suggestions(OptimizationTarget.THROUGHPUT)

                    for suggestion in suggestions[:2]:  # Top 2 suggestions
                        logger.info(f"💡 Suggestion: {suggestion.description}")
                        self._suggestions[suggestion.id] = suggestion

                        # Appliquer automatiquement si configuré
                        if self._default_config.get('auto_tune', False):
                            logger.info(f"⚙️ Application automatique: {suggestion.description}")
                            suggestion.applied = True
                            suggestion.applied_at = datetime.now()
                            self._optimization_history.append(suggestion)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"❌ Erreur dans l'optimisation: {e}")

    # ========================================================================
    # HANDLERS DE CAPACITÉS
    # ========================================================================

    async def _handle_analyze(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Analyse les performances actuelles"""
        time_window = params.get("time_window", 3600)
        metrics_list = params.get("metrics", self._metric_config)

        analysis = await self._analyze_metrics(time_window)

        return {
            "success": True,
            "analysis": analysis,
            "timestamp": datetime.now().isoformat()
        }

    async def _handle_optimize(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Propose des optimisations"""
        target_str = params.get("target", "throughput")
        try:
            target = OptimizationTarget(target_str)
        except ValueError:
            return {"success": False, "error": f"Cible invalide: {target_str}"}

        constraints = params.get("constraints", {})

        suggestions = await self._generate_suggestions(target, constraints)

        return {
            "success": True,
            "target": target.value,
            "suggestions": [
                {
                    "id": s.id,
                    "description": s.description,
                    "expected_impact": s.expected_impact,
                    "effort": s.effort,
                    "strategy": s.strategy.value,
                    "implementation": s.implementation
                }
                for s in suggestions
            ],
            "count": len(suggestions),
            "timestamp": datetime.now().isoformat()
        }

    async def _handle_tune(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Ajuste automatiquement les paramètres"""
        component = params.get("component", "system")
        parameters = params.get("parameters", {})

        # Simuler l'ajustement
        logger.info(f"⚙️ Ajustement de {component} avec {parameters}")

        return {
            "success": True,
            "component": component,
            "parameters_applied": parameters,
            "message": f"Paramètres ajustés pour {component}",
            "timestamp": datetime.now().isoformat()
        }

    async def _handle_bottlenecks(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Détecte les goulots d'étranglement"""
        threshold = params.get("threshold", 50)

        metrics = await self._collect_metrics()
        bottlenecks = await self._detect_bottlenecks(metrics)

        # Filtrer par sévérité
        filtered = [b for b in bottlenecks if b.severity >= threshold]

        return {
            "success": True,
            "bottlenecks": [
                {
                    "type": b.type.value,
                    "severity": round(b.severity, 2),
                    "component": b.component,
                    "description": b.description,
                    "suggestions": b.suggestions,
                    "metrics": b.metrics.to_dict()
                }
                for b in filtered
            ],
            "count": len(filtered),
            "threshold": threshold,
            "timestamp": datetime.now().isoformat()
        }

    async def _handle_predict(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Prédit les performances futures"""
        horizon = params.get("horizon", 60)
        scenario = params.get("scenario")

        predictions = await self._predict_performance(horizon, scenario)

        return {
            "success": True,
            "predictions": predictions,
            "timestamp": datetime.now().isoformat()
        }

    async def _handle_report(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Génère un rapport de performance"""
        import uuid

        time_range = params.get("time_range", 60)  # minutes
        format = params.get("format", "json")

        # Collecter les données
        metrics = await self._collect_metrics()
        analysis = await self._analyze_metrics(time_range * 60)
        bottlenecks = await self._detect_bottlenecks(metrics)
        suggestions = await self._generate_suggestions(OptimizationTarget.THROUGHPUT)

        # Calculer le score de performance
        performance_score = 100
        performance_score -= min(30, metrics.cpu_usage / 3)
        performance_score -= min(30, metrics.latency_p95 / 20)
        performance_score -= min(20, metrics.error_rate * 5)
        performance_score = max(0, performance_score)

        # Générer des recommandations
        recommendations = []
        if metrics.cpu_usage > 80:
            recommendations.append("CPU élevé - envisager de scaler")
        if metrics.latency_p95 > 500:
            recommendations.append("Latence élevée - vérifier les requêtes lentes")
        if metrics.error_rate > 2:
            recommendations.append("Taux d'erreur élevé - vérifier les logs")
        if metrics.queue_size > 1000:
            recommendations.append("File d'attente importante - augmenter les workers")

        report = PerformanceReport(
            id=str(uuid.uuid4()),
            generated_at=datetime.now(),
            time_window_minutes=time_range,
            metrics_summary=analysis,
            bottlenecks=bottlenecks,
            suggestions=suggestions[:5],  # Top 5
            trends={
                "throughput": self._calculate_trend([m.throughput for m in list(self._metrics_history)[-100:]]),
                "latency": self._calculate_trend([m.latency_p95 for m in list(self._metrics_history)[-100:]])
            },
            recommendations=recommendations,
            performance_score=round(performance_score, 2)
        )

        if format == "json":
            return {
                "success": True,
                "report_id": report.id,
                "generated_at": report.generated_at.isoformat(),
                "time_window_minutes": report.time_window_minutes,
                "performance_score": report.performance_score,
                "metrics_summary": report.metrics_summary,
                "bottlenecks": [
                    {
                        "type": b.type.value,
                        "severity": round(b.severity, 2),
                        "description": b.description
                    }
                    for b in report.bottlenecks
                ],
                "suggestions": [
                    {
                        "id": s.id,
                        "description": s.description,
                        "expected_impact": s.expected_impact
                    }
                    for s in report.suggestions
                ],
                "trends": report.trends,
                "recommendations": report.recommendations,
                "timestamp": datetime.now().isoformat()
            }
        else:
            return {
                "success": True,
                "report_id": report.id,
                "format": format,
                "data": report
            }

    # ========================================================================
    # SURCHARGE POUR LE NETTOYAGE
    # ========================================================================

    async def shutdown(self) -> bool:
        """Arrête le sous-agent"""
        logger.info(f"Arrêt de {self._subagent_display_name}...")

        for task in [self._analysis_task, self._optimization_task]:
            if task and not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass

        return await super().shutdown()


# ============================================================================
# FONCTION D'USINE
# ============================================================================

def create_performance_optimizer_agent(config_path: str = "") -> "PerformanceOptimizerSubAgent":
    """Crée une instance du sous-agent performance optimizer"""
    return PerformanceOptimizerSubAgent(config_path)
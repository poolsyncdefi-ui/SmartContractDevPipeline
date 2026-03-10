"""
Dead Letter Analyzer SubAgent - Analyseur de messages échoués
Version: 2.0.0

Analyse les messages échoués avec :
- Détection de patterns d'échec
- Corrélation des erreurs
- Recommandations de récupération
- Génération de rapports
- Statistiques détaillées
"""

import logging
import sys
import asyncio
import json
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple, Counter as CounterType
from enum import Enum
from dataclasses import dataclass, field
from collections import defaultdict, Counter
import hashlib

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

class ErrorSeverity(Enum):
    """Niveaux de sévérité des erreurs"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RetryStrategy(Enum):
    """Stratégies de réessai"""
    IMMEDIATE = "immediate"
    DELAYED = "delayed"
    EXPONENTIAL = "exponential"


@dataclass
class DeadLetterMessage:
    """Message dans la dead letter queue"""
    id: str
    original_message: Any
    error: str
    error_type: str
    severity: ErrorSeverity
    source: str
    timestamp: datetime = field(default_factory=datetime.now)
    retry_count: int = 0
    last_retry: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    resolved: bool = False
    resolution: Optional[str] = None
    tags: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convertit en dictionnaire"""
        return {
            "id": self.id,
            "error": self.error,
            "error_type": self.error_type,
            "severity": self.severity.value,
            "source": self.source,
            "timestamp": self.timestamp.isoformat(),
            "retry_count": self.retry_count,
            "last_retry": self.last_retry.isoformat() if self.last_retry else None,
            "resolved": self.resolved,
            "resolution": self.resolution,
            "tags": self.tags,
            "metadata": self.metadata
        }


@dataclass
class ErrorPattern:
    """Pattern d'erreur détecté"""
    id: str
    error_type: str
    frequency: int
    first_seen: datetime
    last_seen: datetime
    sources: List[str]
    example_messages: List[Any]
    recommendation: Optional[str] = None
    severity: ErrorSeverity = ErrorSeverity.MEDIUM
    resolution_rate: float = 0.0


@dataclass
class AnalysisReport:
    """Rapport d'analyse"""
    id: str
    generated_at: datetime
    time_window_hours: int
    total_messages: int
    unique_errors: int
    patterns_detected: List[ErrorPattern]
    top_sources: List[Tuple[str, int]]
    top_errors: List[Tuple[str, int]]
    recommendations: List[str]
    resolution_rate: float
    severity_breakdown: Dict[str, int]


# ============================================================================
# SOUS-AGENT PRINCIPAL
# ============================================================================

class DeadLetterAnalyzerSubAgent(BaseSubAgent):
    """
    Sous-agent Dead Letter Analyzer - Analyseur de messages échoués

    Analyse les messages échoués avec :
    - Détection automatique de patterns
    - Corrélation des erreurs par source
    - Recommandations de résolution
    - Statistiques et tendances
    - Rapports détaillés
    """

    def __init__(self, config_path: str = ""):
        """Initialise l'analyseur dead letter"""
        super().__init__(config_path)

        # Métadonnées
        self._subagent_display_name = "💀 Dead Letter Analyzer"
        self._subagent_description = "Analyseur de messages échoués"
        self._subagent_version = "2.0.0"
        self._subagent_category = "communication"
        self._subagent_capabilities = [
            "dlq.add",
            "dlq.list",
            "dlq.analyze",
            "dlq.retry",
            "dlq.delete",
            "dlq.stats",
            "dlq.report"
        ]

        # État interne
        self._messages: Dict[str, DeadLetterMessage] = {}
        self._message_queue: asyncio.Queue = asyncio.Queue()
        self._error_patterns: Dict[str, ErrorPattern] = {}
        self._analysis_history: List[AnalysisReport] = []

        # Index pour recherche rapide
        self._messages_by_source: Dict[str, List[str]] = defaultdict(list)
        self._messages_by_error: Dict[str, List[str]] = defaultdict(list)
        self._messages_by_severity: Dict[str, List[str]] = defaultdict(list)

        # Configuration
        self._default_config = self._agent_config.get('dead_letter_analyzer', {}).get('defaults', {})
        self._analysis_config = self._agent_config.get('dead_letter_analyzer', {}).get('analysis', {})
        self._retry_config = self._agent_config.get('dead_letter_analyzer', {}).get('retry', {})

        # Tâche d'analyse automatique
        self._analysis_task: Optional[asyncio.Task] = None

        logger.info(f"✅ {self._subagent_display_name} initialisé")

    # ========================================================================
    # IMPLÉMENTATION DES MÉTHODES ABSTRACTES
    # ========================================================================

    async def _initialize_subagent_components(self) -> bool:
        """Initialise les composants spécifiques"""
        logger.info("Initialisation des composants Dead Letter Analyzer...")

        if self._default_config.get('auto_analyze', True):
            interval = self._default_config.get('analysis_interval', 3600)
            self._analysis_task = asyncio.create_task(self._auto_analyze_loop(interval))

        logger.info("✅ Composants Dead Letter Analyzer initialisés")
        return True

    async def _initialize_components(self) -> bool:
        """Implémentation requise par BaseAgent"""
        return await self._initialize_subagent_components()

    def _get_capability_handlers(self) -> Dict[str, Any]:
        """Retourne les handlers spécifiques"""
        return {
            "dlq.add": self._handle_add,
            "dlq.list": self._handle_list,
            "dlq.analyze": self._handle_analyze,
            "dlq.retry": self._handle_retry,
            "dlq.delete": self._handle_delete,
            "dlq.stats": self._handle_stats,
            "dlq.report": self._handle_report,
        }

    # ========================================================================
    # GESTION DES MESSAGES
    # ========================================================================

    async def _add_message(self, message: Any, error: str, source: str,
                           severity: str = "medium", **kwargs) -> Dict[str, Any]:
        """Ajoute un message à la dead letter queue"""
        import uuid

        # Vérifier la limite de taille
        max_size = self._default_config.get('max_size', 10000)
        if len(self._messages) >= max_size:
            # Supprimer le plus ancien
            oldest = min(self._messages.values(), key=lambda m: m.timestamp)
            await self._delete_message(oldest.id)

        # Déterminer le type d'erreur
        error_type = error.split(':')[0] if ':' in error else error.split()[0]

        try:
            severity_enum = ErrorSeverity(severity.lower())
        except ValueError:
            severity_enum = ErrorSeverity.MEDIUM

        msg = DeadLetterMessage(
            id=str(uuid.uuid4()),
            original_message=message,
            error=error,
            error_type=error_type,
            severity=severity_enum,
            source=source,
            metadata=kwargs
        )

        self._messages[msg.id] = msg
        self._messages_by_source[source].append(msg.id)
        self._messages_by_error[error_type].append(msg.id)
        self._messages_by_severity[severity_enum.value].append(msg.id)

        logger.info(f"📥 Message {msg.id} ajouté à la DLQ (source: {source}, type: {error_type})")

        return {
            "success": True,
            "message_id": msg.id,
            "timestamp": msg.timestamp.isoformat(),
            "queue_size": len(self._messages)
        }

    async def _delete_message(self, message_id: str) -> Dict[str, Any]:
        """Supprime un message de la DLQ"""
        if message_id not in self._messages:
            return {
                "success": False,
                "error": f"Message {message_id} non trouvé"
            }

        msg = self._messages[message_id]

        # Retirer des index
        self._messages_by_source[msg.source].remove(message_id)
        self._messages_by_error[msg.error_type].remove(message_id)
        self._messages_by_severity[msg.severity.value].remove(message_id)

        del self._messages[message_id]

        logger.info(f"🗑️ Message {message_id} supprimé de la DLQ")

        return {
            "success": True,
            "message_id": message_id
        }

    async def _retry_message(self, message_id: str, force: bool = False) -> Dict[str, Any]:
        """Tente de renvoyer un message"""
        if message_id not in self._messages:
            return {
                "success": False,
                "error": f"Message {message_id} non trouvé"
            }

        msg = self._messages[message_id]

        # Vérifier les tentatives
        max_attempts = self._retry_config.get('max_attempts', 3)
        if msg.retry_count >= max_attempts and not force:
            return {
                "success": False,
                "error": f"Nombre maximum de tentatives atteint ({max_attempts})"
            }

        # Simuler un réessai
        msg.retry_count += 1
        msg.last_retry = datetime.now()

        # Dans un vrai système, on renverrait le message
        # Pour la simulation, on considère que ça a réussi
        success = True

        if success:
            msg.resolved = True
            msg.resolution = "Retry successful"
            logger.info(f"✅ Message {message_id} résolu après {msg.retry_count} tentative(s)")
        else:
            logger.warning(f"⚠️ Échec du réessai pour {message_id}")

        return {
            "success": success,
            "message_id": message_id,
            "retry_count": msg.retry_count,
            "resolved": msg.resolved
        }

    # ========================================================================
    # ANALYSE DES PATTERNS
    # ========================================================================

    async def _detect_patterns(self, time_window_hours: int = 24) -> List[ErrorPattern]:
        """Détecte les patterns d'erreur"""
        cutoff = datetime.now() - timedelta(hours=time_window_hours)

        # Compter les erreurs par type
        error_counts: Dict[str, int] = Counter()
        error_sources: Dict[str, List[str]] = defaultdict(list)
        error_examples: Dict[str, List[Any]] = defaultdict(list)

        for msg in self._messages.values():
            if msg.timestamp < cutoff:
                continue

            error_counts[msg.error_type] += 1
            error_sources[msg.error_type].append(msg.source)

            if len(error_examples[msg.error_type]) < 3:  # Garder 3 exemples
                error_examples[msg.error_type].append(msg.original_message)

        # Créer les patterns
        patterns = []
        for error_type, count in error_counts.items():
            if count < 2:  # Ignorer les erreurs isolées
                continue

            sources = list(set(error_sources[error_type]))
            first_seen = min(
                (msg.timestamp for msg in self._messages.values()
                 if msg.error_type == error_type and msg.timestamp >= cutoff),
                default=datetime.now()
            )
            last_seen = max(
                (msg.timestamp for msg in self._messages.values()
                 if msg.error_type == error_type and msg.timestamp >= cutoff),
                default=datetime.now()
            )

            # Calculer le taux de résolution
            resolved = sum(1 for msg in self._messages.values()
                          if msg.error_type == error_type and msg.resolved)
            total = error_counts[error_type]
            resolution_rate = resolved / total if total > 0 else 0

            # Déterminer la sévérité
            if count > 100:
                severity = ErrorSeverity.CRITICAL
            elif count > 50:
                severity = ErrorSeverity.HIGH
            elif count > 10:
                severity = ErrorSeverity.MEDIUM
            else:
                severity = ErrorSeverity.LOW

            pattern = ErrorPattern(
                id=hashlib.md5(f"{error_type}:{time_window_hours}".encode()).hexdigest()[:8],
                error_type=error_type,
                frequency=count,
                first_seen=first_seen,
                last_seen=last_seen,
                sources=sources,
                example_messages=error_examples[error_type],
                severity=severity,
                resolution_rate=resolution_rate,
                recommendation=self._generate_recommendation(error_type, count, sources)
            )

            patterns.append(pattern)

        return patterns

    def _generate_recommendation(self, error_type: str, count: int,
                                  sources: List[str]) -> str:
        """Génère une recommandation basée sur le pattern"""
        if "Timeout" in error_type:
            return "Augmenter les timeouts ou vérifier la latence du service"
        elif "Connection" in error_type:
            return "Vérifier la connectivité réseau et les firewalls"
        elif "Auth" in error_type or "Permission" in error_type:
            return "Vérifier les tokens d'authentification et les permissions"
        elif "Validation" in error_type:
            return "Valider le format des messages avant envoi"
        elif "Rate" in error_type or "Limit" in error_type:
            return "Implémenter un rate limiting ou augmenter les quotas"
        elif len(sources) > 3:
            return "Problème systémique - vérifier les dépendances communes"
        else:
            return "Analyser les logs pour identifier la cause racine"

    async def _generate_report(self, time_window_hours: int = 24,
                               format: str = "json") -> Dict[str, Any]:
        """Génère un rapport d'analyse"""
        import uuid

        patterns = await self._detect_patterns(time_window_hours)

        # Statistiques globales
        cutoff = datetime.now() - timedelta(hours=time_window_hours)
        recent_messages = [m for m in self._messages.values() if m.timestamp >= cutoff]

        total = len(recent_messages)
        resolved = sum(1 for m in recent_messages if m.resolved)

        # Top sources
        source_counts = Counter(m.source for m in recent_messages)
        top_sources = source_counts.most_common(5)

        # Top erreurs
        error_counts = Counter(m.error_type for m in recent_messages)
        top_errors = error_counts.most_common(5)

        # Répartition par sévérité
        severity_counts = Counter(m.severity.value for m in recent_messages)

        # Générer des recommandations globales
        recommendations = []
        if patterns:
            critical_patterns = [p for p in patterns if p.severity == ErrorSeverity.CRITICAL]
            if critical_patterns:
                recommendations.append(f"⚠️ {len(critical_patterns)} patterns critiques détectés")
            for p in patterns[:3]:
                if p.recommendation:
                    recommendations.append(f"• {p.error_type}: {p.recommendation}")

        report = AnalysisReport(
            id=str(uuid.uuid4()),
            generated_at=datetime.now(),
            time_window_hours=time_window_hours,
            total_messages=total,
            unique_errors=len(error_counts),
            patterns_detected=patterns,
            top_sources=top_sources,
            top_errors=top_errors,
            recommendations=recommendations,
            resolution_rate=resolved / total if total > 0 else 1.0,
            severity_breakdown=dict(severity_counts)
        )

        self._analysis_history.append(report)

        if format == "json":
            return {
                "success": True,
                "report_id": report.id,
                "generated_at": report.generated_at.isoformat(),
                "time_window_hours": report.time_window_hours,
                "total_messages": report.total_messages,
                "unique_errors": report.unique_errors,
                "resolution_rate": round(report.resolution_rate * 100, 2),
                "patterns": [
                    {
                        "error_type": p.error_type,
                        "frequency": p.frequency,
                        "severity": p.severity.value,
                        "sources": p.sources,
                        "recommendation": p.recommendation
                    }
                    for p in patterns
                ],
                "top_sources": top_sources,
                "top_errors": top_errors,
                "recommendations": recommendations,
                "severity_breakdown": report.severity_breakdown
            }
        else:
            # Pour les autres formats, on retourne le même contenu
            return {
                "success": True,
                "report_id": report.id,
                "format": format,
                "data": report
            }

    async def _auto_analyze_loop(self, interval: int):
        """Boucle d'analyse automatique"""
        logger.info(f"🔄 Boucle d'analyse automatique démarrée (intervalle: {interval}s)")

        while self._status.value == "ready":
            try:
                await asyncio.sleep(interval)

                patterns = await self._detect_patterns(24)
                if patterns:
                    logger.info(f"📊 Analyse auto: {len(patterns)} patterns détectés")

                    # Alerter sur les patterns critiques
                    critical = [p for p in patterns if p.severity == ErrorSeverity.CRITICAL]
                    if critical:
                        logger.warning(f"⚠️ {len(critical)} patterns critiques détectés!")

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"❌ Erreur dans l'analyse auto: {e}")

    # ========================================================================
    # HANDLERS DE CAPACITÉS
    # ========================================================================

    async def _handle_add(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Ajoute un message à la DLQ"""
        message = params.get("message")
        error = params.get("error")
        source = params.get("source")

        if message is None:
            return {"success": False, "error": "message requis"}
        if not error:
            return {"success": False, "error": "error requis"}
        if not source:
            return {"success": False, "error": "source requis"}

        return await self._add_message(
            message=message,
            error=error,
            source=source,
            severity=params.get("severity", "medium"),
            **params.get("metadata", {})
        )

    async def _handle_list(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Liste les messages de la DLQ"""
        filter_str = params.get("filter", "")
        limit = params.get("limit", 100)
        offset = params.get("offset", 0)

        messages = []
        for msg in sorted(self._messages.values(), key=lambda m: m.timestamp, reverse=True):
            if filter_str and filter_str not in msg.error and filter_str not in msg.source:
                continue

            messages.append(msg.to_dict())

        paginated = messages[offset:offset + limit]

        return {
            "success": True,
            "messages": paginated,
            "total": len(messages),
            "returned": len(paginated),
            "offset": offset,
            "limit": limit,
            "timestamp": datetime.now().isoformat()
        }

    async def _handle_analyze(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Analyse les patterns d'échec"""
        time_window = params.get("time_window", 24)
        group_by = params.get("group_by", "error_type")

        patterns = await self._detect_patterns(time_window)

        if group_by == "source":
            # Grouper par source
            source_patterns = defaultdict(list)
            for p in patterns:
                for source in p.sources:
                    source_patterns[source].append(p)

            result = {
                "by_source": {
                    source: [
                        {
                            "error_type": p.error_type,
                            "frequency": p.frequency,
                            "severity": p.severity.value
                        }
                        for p in pats
                    ]
                    for source, pats in source_patterns.items()
                }
            }
        else:
            result = {
                "patterns": [
                    {
                        "error_type": p.error_type,
                        "frequency": p.frequency,
                        "severity": p.severity.value,
                        "sources": p.sources,
                        "first_seen": p.first_seen.isoformat(),
                        "last_seen": p.last_seen.isoformat(),
                        "resolution_rate": round(p.resolution_rate * 100, 2),
                        "recommendation": p.recommendation
                    }
                    for p in patterns
                ]
            }

        return {
            "success": True,
            "time_window_hours": time_window,
            "patterns_detected": len(patterns),
            **result,
            "timestamp": datetime.now().isoformat()
        }

    async def _handle_retry(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Tente de renvoyer un message"""
        message_id = params.get("message_id")
        if not message_id:
            return {"success": False, "error": "message_id requis"}

        return await self._retry_message(
            message_id=message_id,
            force=params.get("force", False)
        )

    async def _handle_delete(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Supprime un message"""
        message_id = params.get("message_id")
        if not message_id:
            return {"success": False, "error": "message_id requis"}

        return await self._delete_message(message_id)

    async def _handle_stats(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Statistiques des échecs"""
        detailed = params.get("detailed", False)

        total = len(self._messages)
        resolved = sum(1 for m in self._messages.values() if m.resolved)
        unresolved = total - resolved

        # Statistiques par sévérité
        severity_stats = {
            sev: len(self._messages_by_severity.get(sev, []))
            for sev in ["critical", "high", "medium", "low"]
        }

        # Statistiques par source
        source_stats = {
            source: len(ids) for source, ids in self._messages_by_source.items()
        }

        # Statistiques par type d'erreur
        error_stats = {
            err: len(ids) for err, ids in self._messages_by_error.items()
        }

        result = {
            "total_messages": total,
            "resolved": resolved,
            "unresolved": unresolved,
            "resolution_rate": round((resolved / total * 100), 2) if total > 0 else 0,
            "by_severity": severity_stats,
            "unique_sources": len(source_stats),
            "unique_errors": len(error_stats),
            "queue_usage_percent": round((total / self._default_config.get('max_size', 10000)) * 100, 2)
        }

        if detailed:
            result["by_source"] = source_stats
            result["by_error"] = error_stats
            result["oldest_message"] = min(
                (m.timestamp for m in self._messages.values()),
                default=None
            )
            result["newest_message"] = max(
                (m.timestamp for m in self._messages.values()),
                default=None
            )

        return {
            "success": True,
            "stats": result,
            "timestamp": datetime.now().isoformat()
        }

    async def _handle_report(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Génère un rapport d'analyse"""
        time_window = params.get("time_window", 24)
        format = params.get("format", "json")

        return await self._generate_report(
            time_window_hours=time_window,
            format=format
        )

    # ========================================================================
    # SURCHARGE POUR LE NETTOYAGE
    # ========================================================================

    async def shutdown(self) -> bool:
        """Arrête le sous-agent"""
        logger.info(f"Arrêt de {self._subagent_display_name}...")

        if self._analysis_task and not self._analysis_task.done():
            self._analysis_task.cancel()
            try:
                await self._analysis_task
            except asyncio.CancelledError:
                pass

        return await super().shutdown()


# ============================================================================
# FONCTION D'USINE
# ============================================================================

def create_dead_letter_analyzer_agent(config_path: str = "") -> "DeadLetterAnalyzerSubAgent":
    """Crée une instance du sous-agent dead letter analyzer"""
    return DeadLetterAnalyzerSubAgent(config_path)
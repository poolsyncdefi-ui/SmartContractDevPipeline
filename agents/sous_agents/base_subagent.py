"""
BaseSubAgent - Classe de base pour TOUS les sous-agents du système
Version: 2.0.1 (CORRIGÉ - Avec initialisation robuste de _config)

Fournit les fonctionnalités fondamentales pour tous les sous-agents :
- Cycle de vie complet (initialisation, démarrage, pause, arrêt)
- Gestion avancée des tâches asynchrones avec priorités
- Cache multi-stratégies avec statistiques
- Métriques et monitoring détaillés
- Communication avec l'agent parent
- Validation des entrées et sécurité
- Audit et traçabilité
- Points d'extension pour personnalisation
"""

import logging
import sys
import asyncio
import json
import time
import hashlib
import uuid
import inspect
import traceback
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, Optional, List, Union, Callable, Awaitable, Set, Tuple
from enum import Enum
from dataclasses import dataclass, field, asdict
from abc import ABC, abstractmethod
from collections import defaultdict, deque
import importlib

# Configuration des imports
current_dir = Path(__file__).parent.absolute()
project_root = current_dir.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from agents.base_agent.base_agent import BaseAgent, AgentStatus, Message, MessageType

logger = logging.getLogger(__name__)


# ============================================================================
# ÉNUMS ET CLASSES DE DONNÉES (basés sur la config)
# ============================================================================

class SubAgentTaskPriority(Enum):
    """Priorités des tâches (aligné sur config.yaml)"""
    LOW = 0
    NORMAL = 1
    HIGH = 2
    CRITICAL = 3
    
    @classmethod
    def from_string(cls, priority_str: str) -> 'SubAgentTaskPriority':
        """Convertit une chaîne en priorité"""
        mapping = {
            "low": cls.LOW,
            "normal": cls.NORMAL,
            "high": cls.HIGH,
            "critical": cls.CRITICAL
        }
        return mapping.get(priority_str.lower(), cls.NORMAL)
    
    def to_config(self) -> Dict[str, Any]:
        """Retourne la configuration de cette priorité"""
        configs = {
            SubAgentTaskPriority.LOW: {
                "value": 0,
                "max_concurrent": 10,
                "timeout_multiplier": 0.5,
                "color": "⚪"
            },
            SubAgentTaskPriority.NORMAL: {
                "value": 1,
                "max_concurrent": 5,
                "timeout_multiplier": 1.0,
                "color": "🟢"
            },
            SubAgentTaskPriority.HIGH: {
                "value": 2,
                "max_concurrent": 2,
                "timeout_multiplier": 1.5,
                "color": "🟠"
            },
            SubAgentTaskPriority.CRITICAL: {
                "value": 3,
                "max_concurrent": 1,
                "timeout_multiplier": 2.0,
                "color": "🔴"
            }
        }
        return configs.get(self, configs[SubAgentTaskPriority.NORMAL])


class SubAgentTaskStatus(Enum):
    """Statuts des tâches"""
    PENDING = "pending"
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"


class CacheEvictionPolicy(Enum):
    """Politiques d'éviction du cache"""
    LRU = "lru"  # Least Recently Used
    LFU = "lfu"  # Least Frequently Used
    FIFO = "fifo"  # First In First Out
    TTL = "ttl"  # Time To Live only


class MessageDeliveryGuarantee(Enum):
    """Garanties de livraison des messages"""
    AT_MOST_ONCE = "at_most_once"
    AT_LEAST_ONCE = "at_least_once"
    EXACTLY_ONCE = "exactly_once"


@dataclass
class SubAgentTask:
    """Représentation d'une tâche de sous-agent"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    type: str = ""
    params: Dict[str, Any] = field(default_factory=dict)
    priority: SubAgentTaskPriority = SubAgentTaskPriority.NORMAL
    status: SubAgentTaskStatus = SubAgentTaskStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    queued_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    timeout_seconds: int = 300
    retry_count: int = 0
    max_retries: int = 3
    result: Any = None
    error: Optional[str] = None
    stack_trace: Optional[str] = None
    cacheable: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)
    parent_task_id: Optional[str] = None
    owner: str = ""  # Agent parent qui a soumis la tâche
    
    @property
    def duration_ms(self) -> float:
        """Calcule la durée d'exécution en ms"""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds() * 1000
        return 0.0
    
    @property
    def queue_wait_ms(self) -> float:
        """Calcule le temps d'attente en file en ms"""
        if self.queued_at and self.started_at:
            return (self.started_at - self.queued_at).total_seconds() * 1000
        return 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertit en dictionnaire pour sérialisation"""
        return {
            "id": self.id,
            "type": self.type,
            "priority": self.priority.value,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "queued_at": self.queued_at.isoformat() if self.queued_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "timeout_seconds": self.timeout_seconds,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
            "duration_ms": self.duration_ms,
            "queue_wait_ms": self.queue_wait_ms,
            "success": self.error is None,
            "error": self.error,
            "metadata": self.metadata,
            "owner": self.owner
        }


@dataclass
class CacheEntry:
    """Entrée dans le cache"""
    key: str
    value: Any
    created_at: datetime = field(default_factory=datetime.now)
    accessed_at: datetime = field(default_factory=datetime.now)
    access_count: int = 0
    ttl_seconds: int = 300
    
    @property
    def is_expired(self) -> bool:
        """Vérifie si l'entrée a expiré"""
        return (datetime.now() - self.created_at).total_seconds() > self.ttl_seconds
    
    def access(self):
        """Marque un accès à cette entrée"""
        self.accessed_at = datetime.now()
        self.access_count += 1


@dataclass
class MetricValue:
    """Valeur de métrique avec timestamp"""
    value: float
    timestamp: datetime = field(default_factory=datetime.now)
    labels: Dict[str, str] = field(default_factory=dict)


class MetricType(Enum):
    """Types de métriques"""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"


@dataclass
class SubAgentMetrics:
    """Métriques de performance pour sous-agent"""
    tasks_processed: int = 0
    tasks_succeeded: int = 0
    tasks_failed: int = 0
    tasks_by_type: Dict[str, int] = field(default_factory=dict)
    tasks_by_priority: Dict[int, int] = field(default_factory=dict)
    task_durations: List[float] = field(default_factory=list)
    queue_wait_times: List[float] = field(default_factory=list)
    cache_hits: int = 0
    cache_misses: int = 0
    cache_evictions: int = 0
    parent_messages_sent: int = 0
    parent_messages_received: int = 0
    parent_errors: int = 0
    last_activity: Optional[datetime] = None
    start_time: datetime = field(default_factory=datetime.now)
    
    def record_task(self, task_type: str, priority: int, success: bool, 
                   duration_ms: float, queue_wait_ms: float):
        """Enregistre l'exécution d'une tâche"""
        self.tasks_processed += 1
        if success:
            self.tasks_succeeded += 1
        else:
            self.tasks_failed += 1
        
        self.tasks_by_type[task_type] = self.tasks_by_type.get(task_type, 0) + 1
        self.tasks_by_priority[priority] = self.tasks_by_priority.get(priority, 0) + 1
        
        self.task_durations.append(duration_ms)
        self.queue_wait_times.append(queue_wait_ms)
        
        # Limiter la taille des listes
        if len(self.task_durations) > 1000:
            self.task_durations = self.task_durations[-1000:]
        if len(self.queue_wait_times) > 1000:
            self.queue_wait_times = self.queue_wait_times[-1000:]
        
        self.last_activity = datetime.now()
    
    def get_success_rate(self) -> float:
        """Calcule le taux de succès"""
        if self.tasks_processed == 0:
            return 100.0
        return (self.tasks_succeeded / self.tasks_processed) * 100
    
    def get_avg_duration_ms(self) -> float:
        """Calcule la durée moyenne"""
        if not self.task_durations:
            return 0.0
        return sum(self.task_durations) / len(self.task_durations)
    
    def get_p95_duration_ms(self) -> float:
        """Calcule le percentile 95 des durées"""
        if not self.task_durations:
            return 0.0
        sorted_durations = sorted(self.task_durations)
        idx = int(len(sorted_durations) * 0.95)
        return sorted_durations[idx]
    
    def get_avg_queue_wait_ms(self) -> float:
        """Calcule le temps d'attente moyen"""
        if not self.queue_wait_times:
            return 0.0
        return sum(self.queue_wait_times) / len(self.queue_wait_times)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertit en dictionnaire pour export"""
        return {
            "uptime_seconds": (datetime.now() - self.start_time).total_seconds(),
            "tasks": {
                "total": self.tasks_processed,
                "succeeded": self.tasks_succeeded,
                "failed": self.tasks_failed,
                "success_rate": round(self.get_success_rate(), 2),
                "by_type": self.tasks_by_type,
                "by_priority": self.tasks_by_priority
            },
            "performance": {
                "avg_duration_ms": round(self.get_avg_duration_ms(), 2),
                "p95_duration_ms": round(self.get_p95_duration_ms(), 2),
                "avg_queue_wait_ms": round(self.get_avg_queue_wait_ms(), 2)
            },
            "cache": {
                "hits": self.cache_hits,
                "misses": self.cache_misses,
                "evictions": self.cache_evictions,
                "hit_rate": round(self._get_cache_hit_rate(), 2)
            },
            "parent_communication": {
                "messages_sent": self.parent_messages_sent,
                "messages_received": self.parent_messages_received,
                "errors": self.parent_errors
            },
            "last_activity": self.last_activity.isoformat() if self.last_activity else None
        }
    
    def _get_cache_hit_rate(self) -> float:
        """Calcule le taux de hit du cache"""
        total = self.cache_hits + self.cache_misses
        if total == 0:
            return 100.0
        return (self.cache_hits / total) * 100


# ============================================================================
# CLASSE DE BASE POUR TOUS LES SOUS-AGENTS
# ============================================================================

class BaseSubAgent(BaseAgent, ABC):
    """
    Classe de base abstraite pour TOUS les sous-agents du système.
    
    Fournit:
    - Cycle de vie complet (initialize, shutdown, pause, resume)
    - Gestion avancée des tâches asynchrones avec priorités
    - Cache multi-stratégies (LRU, LFU, FIFO, TTL)
    - Métriques et monitoring détaillés
    - Communication avec l'agent parent
    - Validation des entrées selon schémas
    - Audit et traçabilité
    - Points d'extension pour personnalisation
    """
    
    def __init__(self, config_path: str = ""):
        """Initialise le sous-agent de base avec configuration"""
        super().__init__(config_path)
        
        # 🔧 CORRECTION ROBUSTE POUR _config
        # ============================================================
        # Cette correction garantit que self._config est toujours défini,
        # même si BaseAgent ne l'a pas initialisé correctement.
        # Elle est 100% rétrocompatible et ne casse rien.
        # ============================================================
        
        # Cas 1: _config existe déjà (hérité de BaseAgent)
        if hasattr(self, '_config') and self._config is not None:
            # Déjà bon, ne rien faire
            pass
        
        # Cas 2: _agent_config existe (utilisé par BaseAgent)
        elif hasattr(self, '_agent_config'):
            self._config = self._agent_config
            logger.debug(f"🔧 _config initialisé depuis _agent_config pour {self.__class__.__name__}")
        
        # Cas 3: Charger directement depuis le fichier
        elif config_path and Path(config_path).exists():
            self._config = self._load_config_direct(config_path)
            logger.debug(f"🔧 _config chargé directement depuis {config_path}")
        
        # Cas 4: Valeur par défaut
        else:
            self._config = {}
            logger.debug(f"🔧 _config initialisé à {{}} pour {self.__class__.__name__}")
        
        # ====================================================================
        # MÉTADONNÉES (à surcharger par les sous-classes)
        # ====================================================================
        self._subagent_display_name = "Base SubAgent"
        self._subagent_description = "Classe de base pour tous les sous-agents"
        self._subagent_version = self._config.get('base_subagent', {}).get('version', '2.0.1')
        self._subagent_category = self._config.get('base_subagent', {}).get('parent_relationship', {}).get('type', 'generic')
        self._subagent_capabilities: List[str] = []
        
        # ====================================================================
        # ÉTAT INTERNE
        # ====================================================================
        self._initialized = False
        self._components: Dict[str, Any] = {}
        
        # === GESTION DES TÂCHES ===
        self._task_queue: asyncio.PriorityQueue = asyncio.PriorityQueue()
        self._active_tasks: Dict[str, asyncio.Task] = {}
        self._task_results: Dict[str, SubAgentTask] = {}
        self._task_history: deque = deque(maxlen=1000)
        self._task_locks: Dict[str, asyncio.Lock] = {}
        
        # Statistiques de tâches par priorité
        self._priority_semaphores: Dict[SubAgentTaskPriority, asyncio.Semaphore] = {}
        self._init_priority_semaphores()
        
        # === CACHE ===
        self._cache: Dict[str, CacheEntry] = {}
        self._cache_lru: deque = deque(maxlen=1000)  # Pour LRU
        self._cache_access_counts: Dict[str, int] = defaultdict(int)  # Pour LFU
        self._cache_eviction_policy = CacheEvictionPolicy.LRU
        
        # === MÉTRIQUES ===
        self._metrics = SubAgentMetrics()
        self._custom_metrics: Dict[str, List[MetricValue]] = defaultdict(list)
        self._metrics_lock = asyncio.Lock()
        
        # === COMMUNICATION PARENT ===
        self._parent_agent: Optional[BaseAgent] = None
        self._parent_registered = False
        self._parent_connection_healthy = True
        self._parent_message_queue: asyncio.Queue = asyncio.Queue()
        
        # === VALIDATION ===
        self._input_schemas: Dict[str, Dict[str, Any]] = {}
        self._load_input_schemas()
        
        # === AUDIT ===
        self._audit_log: deque = deque(maxlen=1000)
        self._audit_enabled = self._config.get('security', {}).get('audit', {}).get('enabled', True)
        
        # === EXTENSIONS ===
        self._extensions: Dict[str, Any] = {}
        self._extension_hooks: Dict[str, List[Callable]] = defaultdict(list)
        
        # === CONFIGURATION CHARGÉE ===
        self._load_configuration()
        
        # === TÂCHES DE FOND ===
        self._processor_task: Optional[asyncio.Task] = None
        self._metrics_task: Optional[asyncio.Task] = None
        self._cleanup_task: Optional[asyncio.Task] = None
        self._heartbeat_task: Optional[asyncio.Task] = None
        self._parent_comm_task: Optional[asyncio.Task] = None
        
        logger.info(f"✅ BaseSubAgent v2.0.1 initialisé pour {self._subagent_display_name}")

    def _load_config_direct(self, config_path: str) -> Dict[str, Any]:
        """Charge directement la configuration depuis un fichier (méthode de secours)"""
        try:
            import yaml
            with open(config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f) or {}
        except Exception as e:
            logger.error(f"❌ Erreur chargement direct config {config_path}: {e}")
            return {}

    # ========================================================================
    # MÉTHODES DE CONFIGURATION
    # ========================================================================

    def _load_configuration(self):
        """Charge et valide la configuration depuis le fichier YAML"""
        try:
            config = self._config.get('base_subagent', {})
            
            # Configuration système
            system_config = config.get('system', {})
            self._log_level = system_config.get('logging', {}).get('default_level', 'INFO')
            self._timeout_default = system_config.get('performance', {}).get('timeouts', {}).get('default', 60)
            
            # Configuration des tâches
            task_config = config.get('task_management', {})
            self._task_default_timeout = task_config.get('task_types', {}).get('EXECUTE', {}).get('timeout', 300)
            self._task_max_retries = task_config.get('task_types', {}).get('EXECUTE', {}).get('max_attempts', 3)
            self._queue_max_size = task_config.get('queue', {}).get('max_size', 1000)
            
            # Configuration du cache
            cache_config = config.get('cache', {})
            self._cache_enabled = cache_config.get('enabled', True)
            self._cache_default_ttl = cache_config.get('default_ttl_seconds', 300)
            self._cache_max_size = cache_config.get('max_size', 1000)
            
            policy_str = cache_config.get('eviction_policy', 'LRU').upper()
            self._cache_eviction_policy = CacheEvictionPolicy[policy_str]
            
            # Configuration de la communication parent
            parent_config = config.get('parent_communication', {})
            self._parent_heartbeat_interval = parent_config.get('reliability', {}).get('heartbeat_interval', 30)
            self._parent_message_retries = parent_config.get('reliability', {}).get('max_retries', 3)
            
            # Configuration des métriques
            metrics_config = config.get('metrics', {}).get('collection', {})
            self._metrics_interval = metrics_config.get('interval', 60)
            
            # Configuration de la sécurité
            security_config = config.get('security', {})
            self._input_validation_enabled = security_config.get('input_validation', {}).get('enabled', True)
            self._sensitive_data_masking = security_config.get('sensitive_data', {}).get('mask_in_logs', True)
            
            logger.debug(f"Configuration chargée pour {self._subagent_display_name}")
            
        except Exception as e:
            logger.error(f"Erreur lors du chargement de la configuration: {e}")
            # Utiliser les valeurs par défaut

    def _init_priority_semaphores(self):
        """Initialise les sémaphores pour chaque niveau de priorité"""
        for priority in SubAgentTaskPriority:
            config = priority.to_config()
            self._priority_semaphores[priority] = asyncio.Semaphore(config["max_concurrent"])

    def _load_input_schemas(self):
        """Charge les schémas de validation des entrées"""
        try:
            schemas = self._config.get('security', {}).get('input_validation', {}).get('schemas', {})
            self._input_schemas = schemas
            logger.debug(f"Schémas de validation chargés: {list(schemas.keys())}")
        except Exception as e:
            logger.warning(f"Impossible de charger les schémas: {e}")

    # ========================================================================
    # MÉTHODES ABSTRACTES À IMPLÉMENTER
    # ========================================================================

    @abstractmethod
    async def _initialize_subagent_components(self) -> bool:
        """
        Initialise les composants spécifiques du sous-agent.
        À implémenter par chaque sous-agent concret.
        """
        pass

    @abstractmethod
    def _get_capability_handlers(self) -> Dict[str, Callable]:
        """
        Retourne les handlers pour les capacités spécifiques.
        Format: {"capability_name": self._handler_method}
        """
        return {}

    # ========================================================================
    # CYCLE DE VIE (surcharge de BaseAgent)
    # ========================================================================

    async def initialize(self) -> bool:
        """Initialise le sous-agent"""
        try:
            self._set_status(AgentStatus.INITIALIZING)
            logger.info(f"🚀 Initialisation de {self._subagent_display_name}...")

            # Exécuter les hooks pre-initialization
            await self._run_extension_hooks("pre_initialization")

            # Initialisation de BaseAgent
            base_result = await super().initialize()
            if not base_result:
                return False

            # Composants communs
            self._components = {
                "version": self._subagent_version,
                "category": self._subagent_category,
                "capabilities": self._subagent_capabilities,
                "initialized_at": datetime.now().isoformat()
            }

            # Initialisation spécifique
            spec_result = await self._initialize_subagent_components()
            if not spec_result:
                logger.error(f"Échec de l'initialisation spécifique de {self._subagent_display_name}")
                return False

            # Enregistrement auprès du parent
            await self._register_with_parent()

            # Démarrer les tâches de fond
            self._start_background_tasks()

            # Exécuter les hooks post-initialization
            await self._run_extension_hooks("post_initialization")

            self._initialized = True
            self._set_status(AgentStatus.READY)
            
            # Audit
            await self._audit("SUBAGENT_STARTED", {
                "display_name": self._subagent_display_name,
                "version": self._subagent_version,
                "category": self._subagent_category
            })
            
            logger.info(f"✅ {self._subagent_display_name} prêt")
            return True

        except Exception as e:
            logger.error(f"❌ Erreur initialisation {self._subagent_display_name}: {e}")
            logger.error(traceback.format_exc())
            self._set_status(AgentStatus.ERROR)
            return False

    def _start_background_tasks(self):
        """Démarre toutes les tâches de fond"""
        loop = asyncio.get_event_loop()
        
        # Processeur de tâches
        self._processor_task = loop.create_task(self._task_processor())
        
        # Métriques
        metrics_config = self._config.get('metrics', {}).get('collection', {})
        if metrics_config.get('enabled', True):
            self._metrics_task = loop.create_task(self._metrics_collector())
        
        # Nettoyage
        self._cleanup_task = loop.create_task(self._cleanup_worker())
        
        # Heartbeat parent
        parent_config = self._config.get('parent_communication', {}).get('reliability', {})
        if parent_config.get('heartbeat_enabled', True):
            self._heartbeat_task = loop.create_task(self._heartbeat_sender())
        
        # Communication parent
        self._parent_comm_task = loop.create_task(self._parent_message_processor())
        
        logger.debug(f"🔄 Tâches de fond démarrées pour {self._subagent_display_name}")

    async def shutdown(self) -> bool:
        """Arrête le sous-agent proprement"""
        logger.info(f"🛑 Arrêt de {self._subagent_display_name}...")
        self._set_status(AgentStatus.STOPPING)

        # Exécuter les hooks pre-shutdown
        await self._run_extension_hooks("pre_shutdown")

        # Annuler les tâches de fond
        bg_tasks = [
            self._processor_task,
            self._metrics_task,
            self._cleanup_task,
            self._heartbeat_task,
            self._parent_comm_task
        ]
        
        for task in bg_tasks:
            if task and not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass

        # Annuler les tâches actives
        for task_id, task in list(self._active_tasks.items()):
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        
        self._active_tasks.clear()

        # Sauvegarder l'état si nécessaire
        await self._save_state()

        # Audit
        await self._audit("SUBAGENT_STOPPED", {
            "uptime_seconds": (datetime.now() - self._metrics.start_time).total_seconds()
        })

        # Appeler la méthode parent (mais ignorer son retour)
        await super().shutdown()  # ← NE PAS retourner cette valeur

        logger.info(f"✅ {self._subagent_display_name} arrêté")
        return True  # ← TOUJOURS retourner True

    async def pause(self) -> bool:
        """Met en pause le sous-agent"""
        logger.info(f"⏸️ Pause de {self._subagent_display_name}...")
        self._set_status(AgentStatus.PAUSED)
        
        await self._audit("SUBAGENT_PAUSED", {})
        return True

    async def resume(self) -> bool:
        """Reprend l'activité"""
        logger.info(f"▶️ Reprise de {self._subagent_display_name}...")
        self._set_status(AgentStatus.READY)
        
        await self._audit("SUBAGENT_RESUMED", {})
        return True

    # ========================================================================
    # GESTION DES TÂCHES
    # ========================================================================

    async def submit_task(self, task_type: str, params: Dict[str, Any] = None,
                         priority: Union[str, SubAgentTaskPriority] = SubAgentTaskPriority.NORMAL,
                         timeout: Optional[int] = None,
                         cacheable: bool = True,
                         owner: str = "") -> str:
        """
        Soumet une nouvelle tâche pour exécution asynchrone.
        
        Returns:
            ID de la tâche soumise
        """
        # Convertir la priorité si nécessaire
        if isinstance(priority, str):
            priority = SubAgentTaskPriority.from_string(priority)
        
        # Créer la tâche
        task = SubAgentTask(
            type=task_type,
            params=params or {},
            priority=priority,
            timeout_seconds=timeout or self._task_default_timeout,
            max_retries=self._task_max_retries,
            cacheable=cacheable,
            owner=owner,
            metadata={
                "submitted_at": datetime.now().isoformat(),
                "submitted_by": owner or "unknown"
            }
        )
        
        # Valider les paramètres
        if self._input_validation_enabled and task_type in self._input_schemas:
            is_valid, error = self._validate_against_schema(params, self._input_schemas[task_type])
            if not is_valid:
                raise ValueError(f"Paramètres invalides pour la tâche {task_type}: {error}")
        
        # Mettre en file d'attente avec priorité (priorité négative pour que la plus haute sorte en premier)
        # Format: (-priority_value, timestamp, task)
        await self._task_queue.put((-priority.value, datetime.now().timestamp(), task))
        
        task.status = SubAgentTaskStatus.QUEUED
        task.queued_at = datetime.now()
        
        self._task_results[task.id] = task
        
        logger.debug(f"📥 Tâche {task.id} ({task_type}) soumise avec priorité {priority.name}")
        
        return task.id

    async def get_task_result(self, task_id: str, wait: bool = False, 
                             timeout: Optional[int] = None) -> Optional[SubAgentTask]:
        """
        Récupère le résultat d'une tâche.
        
        Args:
            task_id: ID de la tâche
            wait: Si True, attend la fin de la tâche
            timeout: Timeout en secondes (si wait=True)
        
        Returns:
            La tâche avec son résultat, ou None si non trouvée
        """
        task = self._task_results.get(task_id)
        
        if not task:
            return None
        
        if wait and task.status in [SubAgentTaskStatus.PENDING, SubAgentTaskStatus.QUEUED, SubAgentTaskStatus.PROCESSING]:
            # Attendre que la tâche se termine
            start_time = time.time()
            while task.status not in [SubAgentTaskStatus.COMPLETED, SubAgentTaskStatus.FAILED, SubAgentTaskStatus.CANCELLED]:
                if timeout and (time.time() - start_time) > timeout:
                    raise TimeoutError(f"Timeout en attendant la tâche {task_id}")
                await asyncio.sleep(0.1)
        
        return task

    async def cancel_task(self, task_id: str, force: bool = False) -> bool:
        """
        Annule une tâche en cours ou en attente.
        
        Returns:
            True si la tâche a été annulée
        """
        task = self._task_results.get(task_id)
        
        if not task:
            logger.warning(f"Tentative d'annulation de tâche inconnue: {task_id}")
            return False
        
        if task.status == SubAgentTaskStatus.PROCESSING:
            # Tâche en cours d'exécution
            if task_id in self._active_tasks:
                self._active_tasks[task_id].cancel()
                task.status = SubAgentTaskStatus.CANCELLED
                task.completed_at = datetime.now()
                logger.info(f"✅ Tâche {task_id} annulée (en cours)")
                return True
                
        elif task.status == SubAgentTaskStatus.QUEUED:
            # Tâche en file d'attente - difficile à retirer de la PriorityQueue
            # On la marque simplement comme annulée
            task.status = SubAgentTaskStatus.CANCELLED
            task.completed_at = datetime.now()
            logger.info(f"✅ Tâche {task_id} annulée (en file)")
            return True
        
        elif force:
            # Forcer l'annulation même si déjà terminée
            task.status = SubAgentTaskStatus.CANCELLED
            return True
        
        return False

    async def _task_processor(self):
        """Processeur de tâches asynchrone avec gestion des priorités"""
        logger.info(f"🔄 Processeur de tâches démarré pour {self._subagent_display_name}")
        
        while self._status == AgentStatus.READY:
            try:
                # Récupérer la prochaine tâche (bloquant)
                neg_priority, timestamp, task = await self._task_queue.get()
                priority = SubAgentTaskPriority(-neg_priority)
                
                # Vérifier que la tâche n'a pas été annulée
                if task.status == SubAgentTaskStatus.CANCELLED:
                    self._task_queue.task_done()
                    continue
                
                # Vérifier le sémaphore de priorité
                semaphore = self._priority_semaphores[priority]
                
                # Attendre d'avoir un slot pour cette priorité
                await semaphore.acquire()
                
                # Lancer la tâche
                task.status = SubAgentTaskStatus.PROCESSING
                task.started_at = datetime.now()
                
                # Créer la coroutine d'exécution
                coro = self._execute_task(task)
                
                # Lancer avec timeout
                try:
                    async with asyncio.timeout(task.timeout_seconds):
                        execution_task = asyncio.create_task(coro)
                        self._active_tasks[task.id] = execution_task
                        await execution_task
                except asyncio.TimeoutError:
                    task.status = SubAgentTaskStatus.TIMEOUT
                    task.error = f"Timeout après {task.timeout_seconds}s"
                    task.completed_at = datetime.now()
                    logger.warning(f"⏱️ Tâche {task.id} timeout")
                except Exception as e:
                    task.status = SubAgentTaskStatus.FAILED
                    task.error = str(e)
                    task.stack_trace = traceback.format_exc()
                    task.completed_at = datetime.now()
                    logger.error(f"❌ Tâche {task.id} échouée: {e}")
                finally:
                    # Libérer le sémaphore
                    semaphore.release()
                    
                    # Nettoyer la tâche active
                    if task.id in self._active_tasks:
                        del self._active_tasks[task.id]
                    
                    self._task_queue.task_done()
                    
                    # Ajouter à l'historique
                    self._task_history.append(task)
                    
                    # Enregistrer les métriques
                    self._metrics.record_task(
                        task.type,
                        task.priority.value,
                        task.error is None,
                        task.duration_ms,
                        task.queue_wait_ms
                    )
                    
                    # Notifier le parent si nécessaire
                    if task.owner and task.owner != self.name:
                        await self._send_to_parent("TASK_RESULT", {
                            "task_id": task.id,
                            "status": task.status.value,
                            "result": task.result if task.error is None else None,
                            "error": task.error
                        })
                    
                    logger.debug(f"✅ Tâche {task.id} terminée en {task.duration_ms:.0f}ms")
                
            except asyncio.CancelledError:
                logger.info("🛑 Processeur de tâches arrêté")
                break
            except Exception as e:
                logger.error(f"❌ Erreur processeur tâches: {e}")
                logger.error(traceback.format_exc())
                await asyncio.sleep(1)

    async def _execute_task(self, task: SubAgentTask):
        """Exécute une tâche spécifique"""
        # Vérifier le cache d'abord
        if task.cacheable and self._cache_enabled:
            cache_key = self._get_cache_key(task.type, task.params)
            cached_result = await self._get_from_cache(cache_key)
            if cached_result is not None:
                task.result = cached_result
                task.completed_at = datetime.now()
                self._metrics.cache_hits += 1
                logger.debug(f"🎯 Cache hit pour tâche {task.id}")
                return
        
        self._metrics.cache_misses += 1
        
        # Obtenir le handler pour ce type de tâche
        handlers = self._get_capability_handlers()
        
        if task.type not in handlers:
            raise ValueError(f"Type de tâche inconnu: {task.type}")
        
        handler = handlers[task.type]
        
        # Exécuter le handler
        try:
            # Exécuter les hooks pre-task
            await self._run_extension_hooks("pre_task_execution", task=task)
            
            # Appeler le handler
            if asyncio.iscoroutinefunction(handler):
                result = await handler(task.params)
            else:
                result = handler(task.params)
            
            task.result = result
            task.completed_at = datetime.now()
            
            # Mettre en cache si approprié
            if task.cacheable and self._cache_enabled and result is not None:
                cache_key = self._get_cache_key(task.type, task.params)
                await self._add_to_cache(cache_key, result)
            
            # Exécuter les hooks post-task
            await self._run_extension_hooks("post_task_execution", task=task, result=result)
            
        except Exception as e:
            # Gestion des retries
            if task.retry_count < task.max_retries:
                task.retry_count += 1
                logger.warning(f"🔄 Retry {task.retry_count}/{task.max_retries} pour tâche {task.id}")
                
                # Backoff exponentiel
                delay = self._config.get('system', {}).get('retry_policy', {}).get('initial_delay_ms', 100) / 1000
                delay *= (2 ** (task.retry_count - 1))
                await asyncio.sleep(delay)
                
                # Remettre en file
                await self._task_queue.put((-task.priority.value, datetime.now().timestamp(), task))
            else:
                raise

    # ========================================================================
    # GESTION DU CACHE
    # ========================================================================

    def _get_cache_key(self, task_type: str, params: Dict[str, Any]) -> str:
        """Génère une clé de cache unique pour une tâche et ses paramètres"""
        content = json.dumps({
            "type": task_type,
            "params": params
        }, sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()

    async def _get_from_cache(self, key: str) -> Optional[Any]:
        """Récupère une valeur du cache"""
        if not self._cache_enabled:
            return None
        
        if key not in self._cache:
            return None
        
        entry = self._cache[key]
        
        # Vérifier l'expiration
        if entry.is_expired:
            del self._cache[key]
            self._remove_from_lru(key)
            return None
        
        # Mettre à jour les stats d'accès
        entry.access()
        
        # Mettre à jour LRU
        self._update_lru(key)
        
        return entry.value

    async def _add_to_cache(self, key: str, value: Any, ttl: Optional[int] = None):
        """Ajoute une valeur au cache"""
        if not self._cache_enabled:
            return
        
        # Vérifier la taille
        if len(self._cache) >= self._cache_max_size:
            await self._evict_cache_entry()
        
        entry = CacheEntry(
            key=key,
            value=value,
            ttl_seconds=ttl or self._cache_default_ttl
        )
        
        self._cache[key] = entry
        self._update_lru(key)

    def _update_lru(self, key: str):
        """Met à jour l'ordre LRU"""
        if key in self._cache_lru:
            self._cache_lru.remove(key)
        self._cache_lru.append(key)

    def _remove_from_lru(self, key: str):
        """Retire une clé de LRU"""
        if key in self._cache_lru:
            self._cache_lru.remove(key)

    async def _evict_cache_entry(self):
        """Évince une entrée du cache selon la politique"""
        if not self._cache:
            return
        
        key_to_evict = None
        
        if self._cache_eviction_policy == CacheEvictionPolicy.LRU:
            # Least Recently Used
            if self._cache_lru:
                key_to_evict = self._cache_lru.popleft()
        
        elif self._cache_eviction_policy == CacheEvictionPolicy.FIFO:
            # First In First Out
            key_to_evict = next(iter(self._cache.keys()))
        
        elif self._cache_eviction_policy == CacheEvictionPolicy.LFU:
            # Least Frequently Used
            if self._cache:
                key_to_evict = min(self._cache.keys(), 
                                  key=lambda k: self._cache[k].access_count)
        
        elif self._cache_eviction_policy == CacheEvictionPolicy.TTL:
            # Expiration par TTL
            now = datetime.now()
            expired = [k for k, e in self._cache.items() if e.is_expired]
            if expired:
                key_to_evict = expired[0]
            else:
                # Si pas d'expirés, prendre le plus vieux
                key_to_evict = min(self._cache.keys(),
                                  key=lambda k: self._cache[k].created_at)
        
        if key_to_evict:
            del self._cache[key_to_evict]
            self._remove_from_lru(key_to_evict)
            self._metrics.cache_evictions += 1

    async def clear_cache(self):
        """Vide complètement le cache"""
        size = len(self._cache)
        self._cache.clear()
        self._cache_lru.clear()
        logger.info(f"🧹 Cache vidé ({size} entrées)")
        
        await self._audit("CACHE_CLEARED", {"entries_removed": size})

    def get_cache_stats(self) -> Dict[str, Any]:
        """Retourne les statistiques du cache"""
        return {
            "size": len(self._cache),
            "max_size": self._cache_max_size,
            "hits": self._metrics.cache_hits,
            "misses": self._metrics.cache_misses,
            "evictions": self._metrics.cache_evictions,
            "hit_rate": round(self._metrics._get_cache_hit_rate(), 2),
            "policy": self._cache_eviction_policy.value,
            "entries": [
                {
                    "key": k[:8] + "...",
                    "age_seconds": (datetime.now() - e.created_at).total_seconds(),
                    "access_count": e.access_count,
                    "ttl_seconds": e.ttl_seconds,
                    "expired": e.is_expired
                }
                for k, e in list(self._cache.items())[:10]  # Top 10 seulement
            ]
        }

    # ========================================================================
    # COMMUNICATION AVEC L'AGENT PARENT
    # ========================================================================

    async def _register_with_parent(self):
        """S'enregistre auprès de l'agent parent"""
        try:
            # Essayer de trouver l'agent parent dans le registre
            # Cette partie dépend de l'implémentation du registre
            parent_name = self._config.get('base_subagent', {}).get('parent_relationship', {}).get('parent_name')
            
            if parent_name:
                # Envoyer un message d'enregistrement
                await self._send_to_parent("REGISTER", {
                    "subagent_id": self.name,
                    "display_name": self._subagent_display_name,
                    "capabilities": self._subagent_capabilities,
                    "version": self._subagent_version
                })
                
                self._parent_registered = True
                logger.info(f"✅ Enregistré auprès du parent {parent_name}")
            
        except Exception as e:
            logger.warning(f"⚠️ Impossible de s'enregistrer auprès du parent: {e}")

    async def _send_to_parent(self, message_type: str, payload: Any, 
                             require_response: bool = False,
                             timeout: int = 30) -> Optional[Any]:
        """
        Envoie un message à l'agent parent.
        
        Returns:
            Réponse si require_response=True, None sinon
        """
        try:
            # Créer le message
            message = Message(
                sender=self.name,
                recipient=self._config.get('base_subagent', {}).get('parent_relationship', {}).get('parent_name', 'orchestrator'),
                content=payload,
                message_type=f"subagent.{message_type.lower()}",
                correlation_id=str(uuid.uuid4()) if require_response else None,
                metadata={
                    "subagent_display_name": self._subagent_display_name,
                    "subagent_version": self._subagent_version,
                    "timestamp": datetime.now().isoformat()
                }
            )
            
            # Envoyer via BaseAgent
            if require_response:
                response = await self.send_message_and_wait(message, timeout)
                self._metrics.parent_messages_sent += 1
                self._metrics.parent_messages_received += 1
                return response
            else:
                await self.send_message(message)
                self._metrics.parent_messages_sent += 1
                return None
                
        except Exception as e:
            self._metrics.parent_errors += 1
            logger.error(f"❌ Erreur envoi message au parent: {e}")
            raise

    async def _parent_message_processor(self):
        """Traite les messages entrants du parent"""
        logger.info(f"📨 Processeur de messages parent démarré")
        
        while self._status == AgentStatus.READY:
            try:
                # Cette méthode serait appelée par le système de messagerie
                # Pour l'instant, on fait juste une boucle simple
                await asyncio.sleep(1)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"❌ Erreur processeur messages parent: {e}")
                await asyncio.sleep(5)

    async def _heartbeat_sender(self):
        """Envoie périodiquement des heartbeat au parent"""
        interval = self._parent_heartbeat_interval
        
        while self._status == AgentStatus.READY:
            try:
                await asyncio.sleep(interval)
                
                if self._parent_registered:
                    await self._send_to_parent("HEARTBEAT", {
                        "status": self._status.value,
                        "queue_size": self._task_queue.qsize(),
                        "active_tasks": len(self._active_tasks),
                        "uptime_seconds": (datetime.now() - self._metrics.start_time).total_seconds()
                    }, require_response=False)
                    
                    logger.debug(f"💓 Heartbeat envoyé au parent")
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"❌ Erreur envoi heartbeat: {e}")
                self._parent_connection_healthy = False
                await asyncio.sleep(interval)

    # ========================================================================
    # MÉTRIQUES ET MONITORING
    # ========================================================================

    async def _metrics_collector(self):
        """Collecte et exporte périodiquement les métriques"""
        interval = self._metrics_interval
        
        while self._status == AgentStatus.READY:
            try:
                await asyncio.sleep(interval)
                
                # Collecter les métriques actuelles
                metrics = self._metrics.to_dict()
                
                # Ajouter les métriques système
                import psutil
                process = psutil.Process()
                metrics["system"] = {
                    "cpu_percent": process.cpu_percent(),
                    "memory_rss": process.memory_info().rss,
                    "memory_percent": process.memory_percent(),
                    "open_files": len(process.open_files()),
                    "threads": process.num_threads()
                }
                
                # Ajouter les métriques de cache
                metrics["cache"] = self.get_cache_stats()
                
                # Ajouter les métriques de file
                metrics["queue"] = {
                    "size": self._task_queue.qsize(),
                    "active_tasks": len(self._active_tasks),
                    "history_size": len(self._task_history)
                }
                
                # Logger les métriques
                logger.debug(f"📊 Métriques: {json.dumps(metrics, default=str)[:500]}...")
                
                # Exporter vers le parent
                await self._send_to_parent("METRICS", metrics, require_response=False)
                
                # Sauvegarder si nécessaire
                await self._save_metrics(metrics)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"❌ Erreur collecte métriques: {e}")
                await asyncio.sleep(interval)

    async def _save_metrics(self, metrics: Dict[str, Any]):
        """Sauvegarde les métriques sur disque"""
        try:
            metrics_config = self._config.get('metrics', {}).get('storage', {})
            if not metrics_config.get('export', {}).get('enabled', True):
                return
            
            path = Path(metrics_config.get('export', {}).get('formats', [{}])[0].get('path', 'data/subagents/metrics'))
            path.mkdir(parents=True, exist_ok=True)
            
            filename = f"metrics_{self.name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            filepath = path / filename
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(metrics, f, indent=2, default=str)
            
            # Nettoyer les vieux fichiers
            await self._cleanup_old_metrics(path)
            
        except Exception as e:
            logger.warning(f"⚠️ Impossible de sauvegarder les métriques: {e}")

    async def _cleanup_old_metrics(self, path: Path):
        """Nettoie les vieux fichiers de métriques"""
        try:
            retention_days = self._config.get('metrics', {}).get('storage', {}).get('retention_hours', 24) / 24
            cutoff = datetime.now() - timedelta(days=retention_days)
            
            for file in path.glob(f"metrics_{self.name}_*.json"):
                try:
                    mtime = datetime.fromtimestamp(file.stat().st_mtime)
                    if mtime < cutoff:
                        file.unlink()
                        logger.debug(f"🗑️ Ancien fichier métrique supprimé: {file.name}")
                except Exception as e:
                    logger.warning(f"⚠️ Erreur suppression {file.name}: {e}")
                    
        except Exception as e:
            logger.warning(f"⚠️ Erreur nettoyage métriques: {e}")

    # ========================================================================
    # VALIDATION DES ENTRÉES
    # ========================================================================

    def _validate_against_schema(self, data: Any, schema: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """
        Valide des données contre un schéma JSON simple.
        
        Returns:
            (is_valid, error_message)
        """
        if not schema:
            return True, None
        
        try:
            # Vérification de base du type
            if "type" in schema:
                expected_type = schema["type"]
                
                if expected_type == "object":
                    if not isinstance(data, dict):
                        return False, f"Devrait être un objet, reçu {type(data).__name__}"
                    
                    # Vérifier les champs requis
                    if "required" in schema:
                        for field in schema["required"]:
                            if field not in data:
                                return False, f"Champ requis manquant: {field}"
                    
                    # Vérifier les propriétés
                    if "properties" in schema:
                        for field, field_schema in schema["properties"].items():
                            if field in data:
                                valid, err = self._validate_against_schema(data[field], field_schema)
                                if not valid:
                                    return False, f"Champ '{field}': {err}"
                
                elif expected_type == "array":
                    if not isinstance(data, list):
                        return False, f"Devrait être un tableau, reçu {type(data).__name__}"
                    
                    if "items" in schema and data:
                        for i, item in enumerate(data):
                            valid, err = self._validate_against_schema(item, schema["items"])
                            if not valid:
                                return False, f"Élément {i}: {err}"
                    
                    if "minItems" in schema and len(data) < schema["minItems"]:
                        return False, f"Minimum {schema['minItems']} éléments, reçu {len(data)}"
                    
                    if "maxItems" in schema and len(data) > schema["maxItems"]:
                        return False, f"Maximum {schema['maxItems']} éléments, reçu {len(data)}"
                
                elif expected_type == "string":
                    if not isinstance(data, str):
                        return False, f"Devrait être une chaîne, reçu {type(data).__name__}"
                    
                    if "minLength" in schema and len(data) < schema["minLength"]:
                        return False, f"Longueur minimale {schema['minLength']}, reçu {len(data)}"
                    
                    if "maxLength" in schema and len(data) > schema["maxLength"]:
                        return False, f"Longueur maximale {schema['maxLength']}, reçu {len(data)}"
                    
                    if "pattern" in schema:
                        import re
                        if not re.match(schema["pattern"], data):
                            return False, f"Ne correspond pas au pattern {schema['pattern']}"
                    
                    if "enum" in schema and data not in schema["enum"]:
                        return False, f"Doit être l'une des valeurs: {schema['enum']}"
                
                elif expected_type in ["number", "integer"]:
                    if not isinstance(data, (int, float)):
                        return False, f"Devrait être un nombre, reçu {type(data).__name__}"
                    
                    if expected_type == "integer" and not isinstance(data, int):
                        return False, f"Devrait être un entier, reçu float"
                    
                    if "minimum" in schema and data < schema["minimum"]:
                        return False, f"Minimum {schema['minimum']}, reçu {data}"
                    
                    if "maximum" in schema and data > schema["maximum"]:
                        return False, f"Maximum {schema['maximum']}, reçu {data}"
                
                elif expected_type == "boolean":
                    if not isinstance(data, bool):
                        return False, f"Devrait être un booléen, reçu {type(data).__name__}"
                
                elif expected_type == "null":
                    if data is not None:
                        return False, f"Devrait être null, reçu {type(data).__name__}"
            
            return True, None
            
        except Exception as e:
            return False, str(e)

    # ========================================================================
    # AUDIT
    # ========================================================================

    async def _audit(self, event_type: str, data: Dict[str, Any]):
        """Enregistre un événement d'audit"""
        if not self._audit_enabled:
            return
        
        audit_entry = {
            "timestamp": datetime.now().isoformat(),
            "subagent": self.name,
            "display_name": self._subagent_display_name,
            "event_type": event_type,
            "data": data
        }
        
        # Ajouter à la file d'audit
        self._audit_log.append(audit_entry)
        
        # Logger
        logger.info(f"📋 AUDIT [{event_type}]: {json.dumps(data, default=str)}")
        
        # Sauvegarder périodiquement
        if len(self._audit_log) >= 100:
            await self._flush_audit_log()

    async def _flush_audit_log(self):
        """Sauvegarde le journal d'audit sur disque"""
        if not self._audit_log:
            return
        
        try:
            audit_config = self._config.get('security', {}).get('audit', {}).get('storage', {})
            path = Path(audit_config.get('path', 'logs/audit/subagents'))
            path.mkdir(parents=True, exist_ok=True)
            
            filename = f"audit_{self.name}_{datetime.now().strftime('%Y%m%d')}.log"
            filepath = path / filename
            
            with open(filepath, 'a', encoding='utf-8') as f:
                for entry in list(self._audit_log):
                    f.write(json.dumps(entry, default=str) + '\n')
            
            self._audit_log.clear()
            
        except Exception as e:
            logger.warning(f"⚠️ Impossible de sauvegarder l'audit: {e}")

    # ========================================================================
    # EXTENSIONS
    # ========================================================================

    async def _load_extensions(self):
        """Charge les extensions configurées"""
        try:
            extensions_config = self._config.get('extensions', {})
            
            if not extensions_config.get('auto_load', True):
                return
            
            extension_dirs = extensions_config.get('extension_dirs', [])
            
            for ext_dir in extension_dirs:
                ext_path = Path(ext_dir)
                if ext_path.exists():
                    for ext_file in ext_path.glob("*.py"):
                        if ext_file.name.startswith('_'):
                            continue
                        
                        try:
                            module_name = ext_file.stem
                            spec = importlib.util.spec_from_file_location(module_name, ext_file)
                            if spec and spec.loader:
                                module = importlib.util.module_from_spec(spec)
                                spec.loader.exec_module(module)
                                
                                # Chercher les classes d'extension
                                for name, obj in inspect.getmembers(module):
                                    if inspect.isclass(obj) and hasattr(obj, 'extension_point'):
                                        ext_instance = obj(self)
                                        self._extensions[name] = ext_instance
                                        
                                        # Enregistrer les hooks
                                        for hook_name in getattr(obj, 'hooks', []):
                                            self._extension_hooks[hook_name].append(
                                                getattr(ext_instance, f"on_{hook_name}")
                                            )
                                        
                                        logger.debug(f"🔌 Extension chargée: {name}")
                                        
                        except Exception as e:
                            logger.warning(f"⚠️ Erreur chargement extension {ext_file}: {e}")
            
            logger.info(f"✅ {len(self._extensions)} extensions chargées")
            
        except Exception as e:
            logger.warning(f"⚠️ Erreur chargement extensions: {e}")

    async def _run_extension_hooks(self, hook_name: str, **kwargs):
        """Exécute tous les hooks d'extension pour un point donné"""
        if hook_name not in self._extension_hooks:
            return
        
        for hook in self._extension_hooks[hook_name]:
            try:
                if asyncio.iscoroutinefunction(hook):
                    await hook(**kwargs)
                else:
                    hook(**kwargs)
            except Exception as e:
                logger.error(f"❌ Erreur dans le hook {hook_name}: {e}")

    # ========================================================================
    # NETTOYAGE
    # ========================================================================

    async def _cleanup_worker(self):
        """Tâche de nettoyage périodique"""
        logger.info(f"🧹 Tâche de nettoyage démarrée pour {self._subagent_display_name}")
        
        while self._status == AgentStatus.READY:
            try:
                await asyncio.sleep(3600)  # Toutes les heures
                
                # Nettoyer le cache
                if self._cache_enabled:
                    await self._cleanup_cache_expired()
                
                # Nettoyer les vieux résultats de tâches
                await self._cleanup_old_tasks()
                
                # Sauvegarder l'audit
                await self._flush_audit_log()
                
                logger.debug(f"🧹 Nettoyage périodique terminé")
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"❌ Erreur dans cleanup_worker: {e}")
                await asyncio.sleep(300)

    async def _cleanup_cache_expired(self):
        """Nettoie les entrées expirées du cache"""
        expired = [k for k, e in self._cache.items() if e.is_expired]
        for k in expired:
            del self._cache[k]
            self._remove_from_lru(k)
        
        if expired:
            logger.debug(f"🗑️ {len(expired)} entrées de cache expirées supprimées")

    async def _cleanup_old_tasks(self):
        """Nettoie les vieux résultats de tâches"""
        cutoff = datetime.now() - timedelta(hours=24)
        old_tasks = [tid for tid, task in self._task_results.items() 
                    if task.completed_at and task.completed_at < cutoff]
        
        for tid in old_tasks:
            del self._task_results[tid]
        
        if old_tasks:
            logger.debug(f"🗑️ {len(old_tasks)} anciennes tâches supprimées")

    async def _save_state(self):
        """Sauvegarde l'état du sous-agent"""
        try:
            persistence_config = self._config.get('persistence', {}).get('state_persistence', {})
            if not persistence_config.get('enabled', False):
                return
            
            path = Path(persistence_config.get('storage_path', 'data/subagents/states'))
            path.mkdir(parents=True, exist_ok=True)
            
            state = {
                "name": self.name,
                "display_name": self._subagent_display_name,
                "version": self._subagent_version,
                "capabilities": self._subagent_capabilities,
                "metrics": self._metrics.to_dict(),
                "queue_size": self._task_queue.qsize(),
                "active_tasks": len(self._active_tasks),
                "cache_size": len(self._cache),
                "saved_at": datetime.now().isoformat()
            }
            
            filename = f"{self.name}_state.json"
            filepath = path / filename
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(state, f, indent=2, default=str)
            
            logger.debug(f"💾 État sauvegardé dans {filepath}")
            
        except Exception as e:
            logger.warning(f"⚠️ Impossible de sauvegarder l'état: {e}")

    # ========================================================================
    # HANDLERS COMMUNS (surcharge de BaseAgent)
    # ========================================================================

    async def _handle_custom_message(self, message: Message) -> Optional[Message]:
        """Gère les messages personnalisés"""
        try:
            msg_type = message.message_type
            logger.debug(f"📨 Message reçu: {msg_type} de {message.sender}")

            # Valider le message si nécessaire
            if self._input_validation_enabled:
                is_valid, error = self._validate_against_schema(
                    message.content, 
                    self._input_schemas.get(msg_type, {})
                )
                if not is_valid:
                    logger.warning(f"⚠️ Message invalide: {error}")
                    return Message(
                        sender=self.name,
                        recipient=message.sender,
                        content={"error": f"Message invalide: {error}"},
                        message_type=MessageType.ERROR.value,
                        correlation_id=message.message_id
                    )

            # Handlers standards
            handlers = self._get_standard_handlers()
            
            # Ajouter les handlers spécifiques
            handlers.update(self._get_capability_handlers())

            # Ajouter les handlers pour les tâches
            if msg_type == f"{self.name}.submit_task" or (message.content and 'task' in message.content):
                return await self._handle_task_submission(message)

            if msg_type in handlers:
                # Exécuter les hooks pre-handler
                await self._run_extension_hooks("pre_message_handler", message=message, handler_name=msg_type)
                
                result = await handlers[msg_type](message)
                
                # Exécuter les hooks post-handler
                await self._run_extension_hooks("post_message_handler", message=message, result=result)
                
                return result

            return None

        except Exception as e:
            logger.error(f"❌ Erreur traitement message: {e}")
            logger.error(traceback.format_exc())
            return Message(
                sender=self.name,
                recipient=message.sender,
                content={"error": str(e)},
                message_type=MessageType.ERROR.value,
                correlation_id=message.message_id
            )

    def _get_standard_handlers(self) -> Dict[str, Callable]:
        """Retourne les handlers standards communs"""
        return {
            f"{self.name}.status": self._handle_status,
            f"{self.name}.metrics": self._handle_metrics,
            f"{self.name}.health": self._handle_health,
            f"{self.name}.capabilities": self._handle_capabilities,
            f"{self.name}.info": self._handle_info,
            f"{self.name}.cache_stats": self._handle_cache_stats,
            f"{self.name}.clear_cache": self._handle_clear_cache,
            f"{self.name}.task_status": self._handle_task_status,
            f"{self.name}.cancel_task": self._handle_cancel_task,
        }

    async def _handle_task_submission(self, message: Message) -> Message:
        """Gère la soumission de tâche"""
        content = message.content
        task_type = content.get('task') or content.get('task_type')
        params = content.get('params', {})
        priority = content.get('priority', 'normal')
        timeout = content.get('timeout')
        cacheable = content.get('cacheable', True)
        
        try:
            task_id = await self.submit_task(
                task_type=task_type,
                params=params,
                priority=priority,
                timeout=timeout,
                cacheable=cacheable,
                owner=message.sender
            )
            
            return Message(
                sender=self.name,
                recipient=message.sender,
                content={
                    "success": True,
                    "task_id": task_id,
                    "status": "queued"
                },
                message_type=f"{self.name}.task_submitted",
                correlation_id=message.message_id
            )
            
        except Exception as e:
            return Message(
                sender=self.name,
                recipient=message.sender,
                content={
                    "success": False,
                    "error": str(e)
                },
                message_type=MessageType.ERROR.value,
                correlation_id=message.message_id
            )

    async def _handle_task_status(self, message: Message) -> Message:
        """Retourne le statut d'une tâche"""
        task_id = message.content.get('task_id')
        wait = message.content.get('wait', False)
        timeout = message.content.get('timeout', 30)
        
        try:
            task = await self.get_task_result(task_id, wait=wait, timeout=timeout)
            
            if task:
                return Message(
                    sender=self.name,
                    recipient=message.sender,
                    content=task.to_dict(),
                    message_type=f"{self.name}.task_status_response",
                    correlation_id=message.message_id
                )
            else:
                return Message(
                    sender=self.name,
                    recipient=message.sender,
                    content={
                        "success": False,
                        "error": f"Tâche {task_id} non trouvée"
                    },
                    message_type=MessageType.ERROR.value,
                    correlation_id=message.message_id
                )
                
        except TimeoutError:
            return Message(
                sender=self.name,
                recipient=message.sender,
                content={
                    "success": False,
                    "error": f"Timeout en attendant la tâche {task_id}"
                },
                message_type=MessageType.ERROR.value,
                correlation_id=message.message_id
            )

    async def _handle_cancel_task(self, message: Message) -> Message:
        """Annule une tâche"""
        task_id = message.content.get('task_id')
        force = message.content.get('force', False)
        
        cancelled = await self.cancel_task(task_id, force=force)
        
        return Message(
            sender=self.name,
            recipient=message.sender,
            content={
                "task_id": task_id,
                "cancelled": cancelled
            },
            message_type=f"{self.name}.task_cancelled" if cancelled else MessageType.ERROR.value,
            correlation_id=message.message_id
        )

    async def _handle_status(self, message: Message) -> Message:
        """Retourne le statut général"""
        return Message(
            sender=self.name,
            recipient=message.sender,
            content={
                'status': self._status.value,
                'initialized': self._initialized,
                'display_name': self._subagent_display_name,
                'category': self._subagent_category,
                'stats': {
                    'tasks_processed': self._metrics.tasks_processed,
                    'success_rate': round(self._metrics.get_success_rate(), 2),
                    'uptime_seconds': (datetime.now() - self._metrics.start_time).total_seconds()
                },
                'queue_size': self._task_queue.qsize(),
                'active_tasks': len(self._active_tasks),
                'cache_size': len(self._cache),
                'parent_registered': self._parent_registered,
                'parent_connected': self._parent_connection_healthy
            },
            message_type=f"{self.name}.status_response",
            correlation_id=message.message_id
        )

    async def _handle_metrics(self, message: Message) -> Message:
        """Retourne les métriques détaillées"""
        detail_level = message.content.get('detail_level', 'summary')
        
        metrics = self._metrics.to_dict()
        
        if detail_level == 'detailed':
            metrics['cache_detail'] = self.get_cache_stats()
            metrics['task_history'] = [
                {
                    'id': t.id,
                    'type': t.type,
                    'status': t.status.value,
                    'duration_ms': t.duration_ms,
                    'success': t.error is None
                }
                for t in list(self._task_history)[-20:]  # 20 dernières tâches
            ]
            metrics['extensions'] = list(self._extensions.keys())
        
        return Message(
            sender=self.name,
            recipient=message.sender,
            content=metrics,
            message_type=f"{self.name}.metrics_response",
            correlation_id=message.message_id
        )

    async def _handle_health(self, message: Message) -> Message:
        """Retourne l'état de santé"""
        health = await self.health_check()
        return Message(
            sender=self.name,
            recipient=message.sender,
            content=health,
            message_type=f"{self.name}.health_response",
            correlation_id=message.message_id
        )

    async def _handle_capabilities(self, message: Message) -> Message:
        """Liste les capacités disponibles"""
        return Message(
            sender=self.name,
            recipient=message.sender,
            content={
                'capabilities': self._subagent_capabilities,
                'version': self._subagent_version,
                'display_name': self._subagent_display_name,
                'category': self._subagent_category,
                'handlers': list(self._get_capability_handlers().keys())
            },
            message_type=f"{self.name}.capabilities_response",
            correlation_id=message.message_id
        )

    async def _handle_info(self, message: Message) -> Message:
        """Retourne les informations générales"""
        return Message(
            sender=self.name,
            recipient=message.sender,
            content=self.get_agent_info(),
            message_type=f"{self.name}.info_response",
            correlation_id=message.message_id
        )

    async def _handle_cache_stats(self, message: Message) -> Message:
        """Retourne les statistiques du cache"""
        return Message(
            sender=self.name,
            recipient=message.sender,
            content=self.get_cache_stats(),
            message_type=f"{self.name}.cache_stats_response",
            correlation_id=message.message_id
        )

    async def _handle_clear_cache(self, message: Message) -> Message:
        """Vide le cache"""
        await self.clear_cache()
        return Message(
            sender=self.name,
            recipient=message.sender,
            content={"success": True},
            message_type=f"{self.name}.cache_cleared",
            correlation_id=message.message_id
        )

    # ========================================================================
    # SANTÉ ET INFORMATION
    # ========================================================================

    async def health_check(self) -> Dict[str, Any]:
        """Vérifie la santé du sous-agent"""
        base_health = await super().health_check()

        # Vérifications spécifiques
        issues = []
        
        # Vérifier la file d'attente
        queue_size = self._task_queue.qsize()
        if queue_size > 100:
            issues.append(f"File d'attente élevée: {queue_size}")
        
        # Vérifier les tâches actives
        active_count = len(self._active_tasks)
        if active_count > 10:
            issues.append(f"Tâches actives élevées: {active_count}")
        
        # Vérifier la connexion parent
        if not self._parent_connection_healthy:
            issues.append("Connexion parent dégradée")
        
        # Vérifier les erreurs récentes
        recent_failures = self._metrics.tasks_failed
        if recent_failures > 10:
            issues.append(f"Échecs récents: {recent_failures}")
        
        health_status = "healthy" if not issues else "degraded"

        return {
            **base_health,
            "agent": self.name,
            "display_name": self._subagent_display_name,
            "category": self._subagent_category,
            "status": self._status.value,
            "ready": self._status == AgentStatus.READY,
            "initialized": self._initialized,
            "health_status": health_status,
            "issues": issues,
            "metrics": {
                "tasks_processed": self._metrics.tasks_processed,
                "success_rate": round(self._metrics.get_success_rate(), 2),
                "queue_size": queue_size,
                "active_tasks": active_count,
                "cache_size": len(self._cache),
                "cache_hit_rate": round(self._metrics._get_cache_hit_rate(), 2),
                "parent_connected": self._parent_connection_healthy
            },
            "timestamp": datetime.now().isoformat()
        }

    def get_agent_info(self) -> Dict[str, Any]:
        """Informations pour le registre"""
        return {
            "id": self.name,
            "name": self.__class__.__name__,
            "display_name": self._subagent_display_name,
            "category": self._subagent_category,
            "version": self._subagent_version,
            "description": self._subagent_description,
            "status": self._status.value,
            "capabilities": self._subagent_capabilities,
            "parent_agent": self._config.get('base_subagent', {}).get('parent_relationship', {}).get('parent_name'),
            "stats": {
                "tasks_processed": self._metrics.tasks_processed,
                "success_rate": round(self._metrics.get_success_rate(), 2),
                "uptime_seconds": (datetime.now() - self._metrics.start_time).total_seconds(),
                "queue_size": self._task_queue.qsize(),
                "active_tasks": len(self._active_tasks),
                "cache_size": len(self._cache),
                "extensions_loaded": len(self._extensions)
            }
        }


# ============================================================================
# FONCTION D'USINE
# ============================================================================

def create_base_subagent(config_path: str = "") -> BaseSubAgent:
    """
    Crée une instance de BaseSubAgent (pour tests uniquement).
    En pratique, cette classe ne doit pas être instanciée directement.
    """
    logger.warning("⚠️ BaseSubAgent est une classe abstraite et ne devrait pas être instanciée directement")
    return BaseSubAgent(config_path)
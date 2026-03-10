"""
Communication Agent - Système de messagerie centralisé haute performance
Gestion des files d'attente, QoS, pub/sub, routage intelligent
Version: 2.1.0 (CORRIGÉ - ALIGNÉ SUR ARCHITECT/CODER/SMARTCONTRACT/FRONTEND/LEARNING)
"""

import logging
import os
import sys
import json
import asyncio
import time
import traceback
import importlib
from pathlib import Path
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Any, Optional, Union, Set, Callable
from collections import defaultdict, deque
from dataclasses import dataclass, field
from uuid import uuid4
import hashlib

# ============================================================================
# CONFIGURATION DES IMPORTS - Chemin absolu
# ============================================================================

current_dir = Path(__file__).parent.absolute()
project_root = current_dir.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from agents.base_agent.base_agent import BaseAgent, AgentStatus, Message, MessageType

logger = logging.getLogger(__name__)


# ============================================================================
# ÉNUMS ET STRUCTURES DE DONNÉES
# ============================================================================

class MessagePriority(Enum):
    """Niveaux de priorité des messages"""
    LOW = 0
    NORMAL = 1
    HIGH = 2
    CRITICAL = 3
    SYSTEM = 4


class MessageStatus(Enum):
    """Statuts possibles d'un message"""
    PENDING = "pending"
    QUEUED = "queued"
    PROCESSING = "processing"
    DELIVERED = "delivered"
    FAILED = "failed"
    EXPIRED = "expired"
    RETRYING = "retrying"
    DEAD_LETTER = "dead_letter"


class DeliveryGuarantee(Enum):
    """Garanties de livraison"""
    AT_MOST_ONCE = "at_most_once"
    AT_LEAST_ONCE = "at_least_once"
    EXACTLY_ONCE = "exactly_once"


class QueueType(Enum):
    """Types de files d'attente"""
    FIFO = "fifo"
    LIFO = "lifo"
    PRIORITY = "priority"
    DEAD_LETTER = "dead_letter"


@dataclass
class MessageEnvelope:
    """Enveloppe de message avec métadonnées"""
    id: str = field(default_factory=lambda: str(uuid4()))
    correlation_id: Optional[str] = None
    sender: str = ""
    recipient: str = ""
    message_type: str = ""
    content: Any = None
    priority: MessagePriority = MessagePriority.NORMAL
    status: MessageStatus = MessageStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    queued_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    ttl_seconds: int = 3600
    retry_count: int = 0
    max_retries: int = 3
    metadata: Dict[str, Any] = field(default_factory=dict)

    def is_expired(self) -> bool:
        """Vérifie si le message a expiré"""
        if not self.queued_at:
            return False
        expiry = self.queued_at + timedelta(seconds=self.ttl_seconds)
        return datetime.now() > expiry

    def to_dict(self) -> Dict[str, Any]:
        """Convertit en dictionnaire"""
        return {
            "id": self.id,
            "correlation_id": self.correlation_id,
            "sender": self.sender,
            "recipient": self.recipient,
            "message_type": self.message_type,
            "content": self.content,
            "priority": self.priority.value,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "queued_at": self.queued_at.isoformat() if self.queued_at else None,
            "delivered_at": self.delivered_at.isoformat() if self.delivered_at else None,
            "ttl_seconds": self.ttl_seconds,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
            "metadata": self.metadata
        }


class PriorityQueue:
    """File d'attente prioritaire thread-safe"""

    def __init__(self, name: str, max_size: int = 10000, priority_levels: int = 5):
        self.name = name
        self.max_size = max_size
        self.priority_levels = priority_levels
        self._queues = [deque() for _ in range(priority_levels)]
        self._lock = asyncio.Lock()
        self._size = 0
        self._stats = {
            "enqueued": 0,
            "dequeued": 0,
            "expired": 0,
            "current_size": 0
        }

    async def enqueue(self, message: MessageEnvelope) -> bool:
        """Ajoute un message à la file"""
        async with self._lock:
            if self._size >= self.max_size:
                logger.warning(f"Queue {self.name} pleine, message rejeté")
                return False

            priority_idx = min(message.priority.value, self.priority_levels - 1)
            self._queues[priority_idx].append(message)
            self._size += 1
            self._stats["enqueued"] += 1
            self._stats["current_size"] = self._size
            message.queued_at = datetime.now()
            message.status = MessageStatus.QUEUED
            return True

    async def dequeue(self) -> Optional[MessageEnvelope]:
        """Récupère le message prioritaire le plus haut"""
        async with self._lock:
            for queue in reversed(self._queues):
                if queue:
                    message = queue.popleft()
                    self._size -= 1
                    self._stats["dequeued"] += 1
                    self._stats["current_size"] = self._size
                    
                    # Vérifier expiration
                    if message.is_expired():
                        message.status = MessageStatus.EXPIRED
                        self._stats["expired"] += 1
                        logger.debug(f"Message {message.id} expiré")
                        continue
                    
                    message.status = MessageStatus.PROCESSING
                    return message
            return None

    async def peek(self) -> Optional[MessageEnvelope]:
        """Regarde le prochain message sans le retirer"""
        async with self._lock:
            for queue in reversed(self._queues):
                if queue:
                    return queue[0]
            return None

    async def size(self) -> int:
        """Retourne la taille de la file"""
        async with self._lock:
            return self._size

    async def clear(self) -> int:
        """Vide la file"""
        async with self._lock:
            total = self._size
            for queue in self._queues:
                queue.clear()
            self._size = 0
            self._stats["current_size"] = 0
            return total

    async def get_stats(self) -> Dict[str, Any]:
        """Retourne les statistiques"""
        async with self._lock:
            return {
                **self._stats,
                "current_size": self._size,
                "queues": [len(q) for q in self._queues]
            }


class TopicManager:
    """Gestionnaire de topics pub/sub"""

    def __init__(self):
        self._topics: Dict[str, Set[str]] = defaultdict(set)  # topic -> set d'abonnés
        self._subscribers: Dict[str, Set[str]] = defaultdict(set)  # subscriber -> set de topics
        self._lock = asyncio.Lock()

    async def subscribe(self, topic: str, subscriber_id: str) -> bool:
        """Abonne un agent à un topic"""
        async with self._lock:
            self._topics[topic].add(subscriber_id)
            self._subscribers[subscriber_id].add(topic)
            return True

    async def unsubscribe(self, topic: str, subscriber_id: str) -> bool:
        """Désabonne un agent d'un topic"""
        async with self._lock:
            self._topics[topic].discard(subscriber_id)
            self._subscribers[subscriber_id].discard(topic)
            return True

    async def get_subscribers(self, topic: str) -> Set[str]:
        """Retourne les abonnés d'un topic"""
        async with self._lock:
            return self._topics.get(topic, set()).copy()

    async def get_topics(self, subscriber_id: str) -> Set[str]:
        """Retourne les topics auxquels un agent est abonné"""
        async with self._lock:
            return self._subscribers.get(subscriber_id, set()).copy()

    async def match_topic(self, pattern: str) -> List[str]:
        """Trouve les topics correspondant à un pattern (wildcards)"""
        import fnmatch
        async with self._lock:
            return [t for t in self._topics.keys() if fnmatch.fnmatch(t, pattern)]

    async def remove_subscriber(self, subscriber_id: str):
        """Supprime tous les abonnements d'un agent"""
        async with self._lock:
            topics = self._subscribers.pop(subscriber_id, set())
            for topic in topics:
                self._topics[topic].discard(subscriber_id)


# ============================================================================
# AGENT PRINCIPAL - COMMUNICATION (ALIGNÉ)
# ============================================================================

class CommunicationAgent(BaseAgent):
    """
    Agent de communication centralisé haute performance
    Gère les files d'attente prioritaires, pub/sub, routage intelligent
    Version 2.1 - Alignée sur l'architecture des agents
    """

    def __init__(self, config_path: Optional[str] = None):
        """Initialise l'agent de communication"""
        if config_path is None:
            config_path = str(project_root / "agents" / "communication" / "config.yaml")

        # Appel au constructeur parent
        super().__init__(config_path)

        # Configuration spécifique
        agent_config = self._agent_config.get('agent', {})
        self._display_name = agent_config.get('display_name', '💬 Communication Agent')
        
        # Récupérer la configuration spécifique
        self._comm_config = self._agent_config.get('communication', {})
        
        # Configuration des files d'attente
        queues_config = self._comm_config.get('queues', {})
        self._default_queue_config = queues_config.get('default', {})
        self._high_priority_config = queues_config.get('high_priority', {})
        self._batch_config = queues_config.get('batch', {})
        self._dead_letter_config = queues_config.get('dead_letter', {})

        # Performance targets
        self._perf_targets = self._comm_config.get('performance_targets', {})
        
        # Delivery guarantees
        self._delivery_config = self._comm_config.get('delivery', {})
        
        # Persistence config
        self._persistence_config = self._comm_config.get('persistence', {})

        # État interne
        self._queues: Dict[str, PriorityQueue] = {}
        self._init_queues()

        self._topic_manager = TopicManager()
        
        self._message_store: Dict[str, MessageEnvelope] = {}  # id -> message
        self._correlation_map: Dict[str, str] = {}  # correlation_id -> message_id
        self._pending_requests: Dict[str, asyncio.Future] = {}  # correlation_id -> Future
        
        self._retry_queue: deque = deque()
        self._dead_letter_queue: deque = deque()
        
        self._circuit_breakers: Dict[str, Dict[str, Any]] = {}  # recipient -> state
        
        # Sous-agents
        self._sub_agents: Dict[str, Any] = {}
        self._components: Dict[str, Any] = {}
        self._initialized = False
        
        # Tâches de fond
        self._processor_task: Optional[asyncio.Task] = None
        self._cleanup_task_obj: Optional[asyncio.Task] = None
        self._retry_task: Optional[asyncio.Task] = None

        # Statistiques internes
        self._stats = {
            "messages_received": 0,
            "messages_sent": 0,
            "messages_processed": 0,
            "messages_failed": 0,
            "messages_expired": 0,
            "messages_retried": 0,
            "messages_deduplicated": 0,
            "active_subscribers": 0,
            "active_topics": 0,
            "queue_size_current": 0,
            "queue_size_max": 0,
            "processing_latency_p50": 0,
            "processing_latency_p95": 0,
            "processing_latency_p99": 0,
            "throughput_current": 0,
            "throughput_peak": 0,
            "uptime_start": datetime.now().isoformat()
        }

        self._logger.info("💬 Communication Agent créé")

    def _init_queues(self):
        """Initialise les files d'attente"""
        # File par défaut
        self._queues["default"] = PriorityQueue(
            name="default",
            max_size=self._default_queue_config.get('max_size', 100000),
            priority_levels=self._default_queue_config.get('priority_levels', 5)
        )
        
        # Haute priorité
        self._queues["high_priority"] = PriorityQueue(
            name="high_priority",
            max_size=self._high_priority_config.get('max_size', 50000),
            priority_levels=self._high_priority_config.get('priority_levels', 3)
        )
        
        # Batch
        self._queues["batch"] = PriorityQueue(
            name="batch",
            max_size=self._batch_config.get('max_size', 10000)
        )

    # ============================================================================
    # CYCLE DE VIE (ALIGNÉ)
    # ============================================================================

    async def initialize(self) -> bool:
        """Initialise l'agent"""
        try:
            self._set_status(AgentStatus.INITIALIZING)
            self._logger.info("💬 Initialisation du Communication Agent...")

            # Appeler l'initialisation du parent
            base_result = await super().initialize()
            if not base_result:
                return False

            # Initialiser les composants
            await self._initialize_components()

            # Initialiser les sous-agents
            await self._initialize_sub_agents()

            # Démarrer les tâches de fond
            self._start_background_tasks()

            self._initialized = True
            self._set_status(AgentStatus.READY)
            self._logger.info("✅ Communication Agent prêt")
            return True

        except Exception as e:
            self._logger.error(f"❌ Erreur initialisation: {e}")
            self._logger.error(traceback.format_exc())
            self._set_status(AgentStatus.ERROR)
            return False

    async def _initialize_components(self) -> bool:
        """
        Initialise les composants spécifiques.
        Appelé par BaseAgent.initialize().
        """
        try:
            self._logger.info("Initialisation des composants Communication...")
            
            self._components = {
                "queues": list(self._queues.keys()),
                "priority_levels": self._default_queue_config.get('priority_levels', 5),
                "pubsub_enabled": self._comm_config.get('pubsub', {}).get('enabled', True),
                "persistence_enabled": self._persistence_config.get('enabled', False),
                "circuit_breakers_enabled": self._comm_config.get('circuit_breaker', {}).get('enabled', True),
                "rate_limiting_enabled": self._comm_config.get('rate_limiting', {}).get('enabled', True)
            }

            self._logger.info(f"✅ Composants: {list(self._components.keys())}")
            return True

        except Exception as e:
            self._logger.error(f"Erreur composants: {e}")
            return False

    async def _initialize_sub_agents(self):
        """
        Initialise les sous-agents spécialisés de manière robuste
        Cette méthode ne doit jamais lever d'exception
        """
        self._sub_agents = {}

        try:
            # Liste des sous-agents à tenter de charger (basée sur config.yaml)
            sub_agent_configs = self._agent_config.get('agent', {}).get('subAgents', [])

            # Si la liste est vide, utiliser les sous-agents par défaut
            if not sub_agent_configs:
                sub_agent_configs = [
                    {"id": "queue_manager", "name": "Queue Manager", "enabled": True},
                    {"id": "pubsub_manager", "name": "PubSub Manager", "enabled": True},
                    {"id": "circuit_breaker", "name": "Circuit Breaker", "enabled": True},
                    {"id": "message_router", "name": "Message Router", "enabled": True},
                    {"id": "dead_letter_analyzer", "name": "Dead Letter Analyzer", "enabled": True},
                    {"id": "performance_optimizer", "name": "Performance Optimizer", "enabled": True},
                    {"id": "security_validator", "name": "Security Validator", "enabled": True},
                ]

            for config in sub_agent_configs:
                agent_id = config.get('id')
                if not config.get('enabled', True):
                    continue

                try:
                    # Tentative d'import dynamique du module
                    module_name = f"agents.communication.sous_agents.{agent_id}.agent"
                    class_name = self._get_sub_agent_class_name(agent_id)

                    # Vérifier si le fichier existe
                    module_path = Path(__file__).parent / "sous_agents" / agent_id / "agent.py"
                    if not module_path.exists():
                        self._logger.debug(f"  ℹ️ Sous-agent {agent_id} non développé (fichier manquant)")
                        continue

                    module = importlib.import_module(module_name)
                    agent_class = getattr(module, class_name, None)

                    if agent_class:
                        config_path = config.get('config_path', str(Path(__file__).parent / "sous_agents" / agent_id / "config.yaml"))
                        sub_agent = agent_class(config_path)
                        self._sub_agents[agent_id] = sub_agent
                        self._logger.info(f"  ✓ Sous-agent {agent_id} initialisé")
                    else:
                        self._logger.debug(f"  ℹ️ Classe {class_name} non trouvée dans {agent_id}")

                except ImportError as e:
                    self._logger.debug(f"  ℹ️ Sous-agent {agent_id} non disponible: {e}")
                except Exception as e:
                    self._logger.warning(f"  ⚠️ Erreur initialisation {agent_id}: {e}")

        except Exception as e:
            self._logger.error(f"❌ Erreur globale initialisation sous-agents: {e}")

        self._logger.info(f"✅ Sous-agents chargés: {len(self._sub_agents)}")

    def _get_sub_agent_class_name(self, agent_id: str) -> str:
        """Convertit un ID de sous-agent en nom de classe"""
        # Convertit "queue_manager" en "QueueManagerSubAgent"
        parts = agent_id.split('_')
        class_name = ''.join(p.capitalize() for p in parts) + 'SubAgent'
        return class_name

    def _start_background_tasks(self):
        """Démarre les tâches de fond"""
        loop = asyncio.get_event_loop()
        self._processor_task = loop.create_task(self._message_processor())
        self._cleanup_task_obj = loop.create_task(self._cleanup_worker())
        self._retry_task = loop.create_task(self._retry_worker())
        self._logger.debug("🔄 Tâches de fond démarrées")

    async def _cleanup_worker(self):
        """Nettoie périodiquement les messages expirés et les vieilles données"""
        interval = self._comm_config.get('performance', {}).get('cleanup_interval', 60)
        
        self._logger.info("🧹 Tâche de nettoyage démarrée")
        while self._status == AgentStatus.READY:
            try:
                await asyncio.sleep(interval)
                
                # Nettoyer les messages expirés dans le store
                expired = []
                now = datetime.now()
                for msg_id, msg in self._message_store.items():
                    if msg.queued_at and (now - msg.queued_at).total_seconds() > msg.ttl_seconds:
                        expired.append(msg_id)
                
                for msg_id in expired:
                    self._message_store.pop(msg_id, None)
                    self._stats["messages_expired"] += 1
                
                # Nettoyer les futures en timeout
                timed_out = []
                for corr_id, future in self._pending_requests.items():
                    if future.done() or future.cancelled():
                        timed_out.append(corr_id)
                
                for corr_id in timed_out:
                    self._pending_requests.pop(corr_id, None)
                
                if expired or timed_out:
                    self._logger.debug(f"🧹 Nettoyage: {len(expired)} messages, {len(timed_out)} requests")
                    
            except asyncio.CancelledError:
                self._logger.info("🛑 Tâche de nettoyage arrêtée")
                break
            except Exception as e:
                self._logger.error(f"Erreur dans cleanup_worker: {e}")

    async def shutdown(self) -> bool:
        """Arrête l'agent proprement"""
        self._logger.info("Arrêt de l'agent Communication...")
        self._set_status(AgentStatus.SHUTTING_DOWN)

        # Annuler les tâches de fond
        for task in [self._processor_task, self._cleanup_task_obj, self._retry_task]:
            if task and not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass

        # Arrêter les sous-agents
        for agent_name, agent_instance in self._sub_agents.items():
            try:
                await agent_instance.shutdown()
                self._logger.debug(f"  ✓ Sous-agent {agent_name} arrêté")
            except Exception as e:
                self._logger.warning(f"  ⚠️ Erreur arrêt sous-agent {agent_name}: {e}")

        # Vider les files
        for queue in self._queues.values():
            await queue.clear()
        
        self._topic_manager = TopicManager()
        self._message_store.clear()
        self._correlation_map.clear()
        self._pending_requests.clear()

        # Sauvegarder les statistiques
        await self._save_stats()

        # Appeler la méthode parent
        await super().shutdown()

        self._logger.info("✅ Agent Communication arrêté")
        return True

    async def pause(self) -> bool:
        """Met l'agent en pause"""
        self._logger.info("Pause de l'agent Communication...")

        # Mettre en pause les sous-agents
        for agent_name, agent_instance in self._sub_agents.items():
            try:
                await agent_instance.pause()
            except Exception as e:
                self._logger.warning(f"⚠️ Erreur pause sous-agent {agent_name}: {e}")

        self._set_status(AgentStatus.PAUSED)
        return True

    async def resume(self) -> bool:
        """Reprend l'activité"""
        self._logger.info("Reprise de l'agent Communication...")

        # Reprendre les sous-agents
        for agent_name, agent_instance in self._sub_agents.items():
            try:
                await agent_instance.resume()
            except Exception as e:
                self._logger.warning(f"⚠️ Erreur reprise sous-agent {agent_name}: {e}")

        self._set_status(AgentStatus.READY)
        return True

    async def _save_stats(self):
        """Sauvegarde les statistiques"""
        try:
            stats_file = Path("./reports") / "communication" / f"stats_{datetime.now().strftime('%Y%m%d')}.json"
            stats_file.parent.mkdir(parents=True, exist_ok=True)
            with open(stats_file, 'w', encoding='utf-8') as f:
                json.dump({
                    "stats": self._stats,
                    "queues": await self.get_queue_stats(),
                    "topics": await self.get_topic_stats(),
                    "timestamp": datetime.now().isoformat()
                }, f, indent=2)
            self._logger.info(f"✅ Statistiques sauvegardées")
        except Exception as e:
            self._logger.warning(f"⚠️ Impossible de sauvegarder: {e}")

    # ============================================================================
    # MÉTHODES DE SANTÉ ET D'INFORMATION (ALIGNÉES)
    # ============================================================================

    async def health_check(self) -> Dict[str, Any]:
        """Vérifie la santé de l'agent"""
        base_health = await super().health_check()

        # Calculer l'uptime
        uptime = None
        if self._stats.get('uptime_start'):
            start = datetime.fromisoformat(self._stats['uptime_start'])
            uptime = str(datetime.now() - start)

        # Vérifier la santé des sous-agents
        sub_agents_health = await self.get_sub_agents_status()

        try:
            stats = await self.get_stats()
            
            # Vérifier les métriques critiques
            queue_sizes = [q["current_size"] for q in stats["queues"].values()]
            total_queue_size = sum(queue_sizes)
            
            health_status = "healthy"
            issues = []
            
            if total_queue_size > 10000:
                issues.append(f"Files d'attente élevées: {total_queue_size}")
                health_status = "degraded"
            
            if stats["processing_latency_p95"] > 1000:  # > 1s
                issues.append(f"Latence élevée: {stats['processing_latency_p95']}ms")
                health_status = "degraded"
            
            if stats["success_rate"] < 95:
                issues.append(f"Taux de succès bas: {stats['success_rate']}%")
                health_status = "degraded"
            
            base_health["communication_specific"] = {
                "queues": {
                    "total_size": total_queue_size,
                    "by_queue": queue_sizes
                },
                "throughput": stats["throughput_current"],
                "latency_p95": stats["processing_latency_p95"],
                "success_rate": stats["success_rate"],
                "dead_letter_size": stats["dead_letter_size"],
                "circuit_breakers": len(stats["circuit_breakers"]),
                "health_status": health_status,
                "issues": issues,
                "sub_agents": sub_agents_health
            }
            
        except Exception as e:
            self._logger.error(f"Erreur dans health_check: {e}")
            base_health["communication_specific"] = {"error": str(e)}
        
        return {
            **base_health,
            "agent": self.name,
            "display_name": self._display_name,
            "status": self._status.value if hasattr(self._status, 'value') else str(self._status),
            "ready": self._status == AgentStatus.READY,
            "initialized": self._initialized,
            "uptime": uptime,
            "timestamp": datetime.now().isoformat()
        }

    def get_agent_info(self) -> Dict[str, Any]:
        """Informations de l'agent pour le registre"""
        agent_config = self._agent_config.get('agent', {})
        capabilities = agent_config.get('capabilities', [])
        
        if capabilities and isinstance(capabilities[0], dict):
            capabilities = [cap.get('name') for cap in capabilities if cap.get('name')]

        return {
            "id": self.name,
            "name": "CommunicationAgent",
            "display_name": self._display_name,
            "version": agent_config.get('version', '2.1.0'),
            "description": agent_config.get('description', 'Système de communication centralisé'),
            "status": self._status.value if hasattr(self._status, 'value') else str(self._status),
            "capabilities": capabilities,
            "features": {
                "queues": list(self._queues.keys()),
                "priority_levels": self._default_queue_config.get('priority_levels', 5),
                "pubsub_enabled": self._components.get("pubsub_enabled", True),
                "circuit_breakers_enabled": self._components.get("circuit_breakers_enabled", True),
                "sub_agents": list(self._sub_agents.keys())
            },
            "stats": {
                "messages_processed": self._stats["messages_processed"],
                "throughput": round(self._stats["throughput_current"], 2),
                "queue_size": self._stats["queue_size_current"],
                "success_rate": round(
                    (self._stats["messages_processed"] / max(1, self._stats["messages_received"])) * 100, 2
                )
            }
        }

    async def get_sub_agents_status(self) -> Dict[str, Any]:
        """Retourne le statut de tous les sous-agents"""
        status = {}
        for agent_name, agent_instance in self._sub_agents.items():
            try:
                health = await agent_instance.health_check()
                status[agent_name] = {
                    "status": health.get("status", "unknown"),
                    "agent_info": agent_instance.get_agent_info()
                }
            except Exception as e:
                status[agent_name] = {
                    "status": "error",
                    "error": str(e)
                }

        return {
            "total_sub_agents": len(self._sub_agents),
            "sub_agents": status
        }

    async def delegate_to_sub_agent(self, task_type: str, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Délègue une tâche à un sous-agent approprié.

        Args:
            task_type: Type de tâche à déléguer
            task_data: Données de la tâche

        Returns:
            Résultat de l'exécution par le sous-agent
        """
        # Mapping des types de tâches vers les sous-agents
        sub_agent_mapping = {
            "queue": "queue_manager",
            "pubsub": "pubsub_manager",
            "circuit": "circuit_breaker",
            "router": "message_router",
            "dead": "dead_letter_analyzer",
            "performance": "performance_optimizer",
            "security": "security_validator"
        }

        for pattern, agent_name in sub_agent_mapping.items():
            if task_type.startswith(pattern):
                if agent_name in self._sub_agents:
                    self._logger.info(f"➡️ Délégation de la tâche {task_type} au sous-agent {agent_name}")
                    # Créer un message pour le sous-agent
                    msg = Message(
                        sender=self.name,
                        recipient=agent_name,
                        content=task_data,
                        message_type=f"communication.{task_type}",
                        correlation_id=f"delegate_{datetime.now().timestamp()}"
                    )
                    return await self._sub_agents[agent_name].handle_message(msg)

        # Fallback: utiliser l'agent principal
        self._logger.info(f"ℹ️ Aucun sous-agent trouvé pour {task_type}, utilisation de l'agent principal")
        
        # Exécuter la tâche localement selon le type
        if task_type == "send":
            return await self.send_communication(
                task_data.get("recipient"),
                task_data.get("content"),
                task_data.get("message_type", "command"),
                MessagePriority(task_data.get("priority", 1)),
                task_data.get("correlation_id"),
                task_data.get("ttl_seconds")
            )
        elif task_type == "publish":
            return await self.publish(
                task_data.get("topic"),
                task_data.get("content"),
                task_data.get("message_type", "event"),
                MessagePriority(task_data.get("priority", 1))
            )
        else:
            return {"success": False, "error": f"Type de tâche non supporté: {task_type}"}

    # ============================================================================
    # API PUBLIQUE - MÉTHODES SPÉCIFIQUES
    # ============================================================================

    async def send_communication(self, 
                                recipient: str,
                                content: Any,
                                message_type: str = "command",
                                priority: MessagePriority = MessagePriority.NORMAL,
                                correlation_id: Optional[str] = None,
                                ttl_seconds: Optional[int] = None,
                                **kwargs) -> Dict[str, Any]:
        """
        Envoie un message à un destinataire (version spécifique à Communication)
        
        Args:
            recipient: Destinataire du message
            content: Contenu du message
            message_type: Type de message
            priority: Priorité du message
            correlation_id: ID de corrélation (pour request/reply)
            ttl_seconds: Durée de vie en secondes
            **kwargs: Métadonnées supplémentaires
            
        Returns:
            Métadonnées du message envoyé
        """
        self._logger.debug(f"📨 send: {message_type} -> {recipient} (prio:{priority.name})")
        
        # Créer l'enveloppe
        message = MessageEnvelope(
            sender=self.name,
            recipient=recipient,
            message_type=message_type,
            content=content,
            priority=priority,
            correlation_id=correlation_id or str(uuid4()),
            ttl_seconds=ttl_seconds or self._default_queue_config.get('timeout', {}).get('default_seconds', 30),
            metadata=kwargs
        )
        
        # Vérifier le circuit breaker
        if not await self._check_circuit_breaker(recipient):
            self._logger.warning(f"Circuit breaker ouvert pour {recipient}")
            message.status = MessageStatus.FAILED
            self._stats["messages_failed"] += 1
            return {
                "success": False,
                "message_id": message.id,
                "error": f"Circuit breaker ouvert pour {recipient}"
            }
        
        # Stocker le message
        self._message_store[message.id] = message
        
        # Mettre en file d'attente
        queue_name = self._select_queue(priority)
        queue = self._queues.get(queue_name, self._queues["default"])
        
        success = await queue.enqueue(message)
        
        if success:
            self._stats["messages_received"] += 1
            self._stats["queue_size_current"] = await queue.size()
            self._stats["queue_size_max"] = max(self._stats["queue_size_max"], self._stats["queue_size_current"])
            
            # Si correlation_id, préparer une Future pour la réponse
            if correlation_id:
                self._pending_requests[correlation_id] = asyncio.Future()
        
        return {
            "success": success,
            "message_id": message.id,
            "correlation_id": message.correlation_id,
            "queue": queue_name,
            "priority": priority.name,
            "timestamp": message.created_at.isoformat()
        }

    async def request(self,
                     recipient: str,
                     content: Any,
                     message_type: str = "request",
                     priority: MessagePriority = MessagePriority.HIGH,
                     timeout_seconds: int = 30,
                     **kwargs) -> Any:
        """
        Envoie une requête et attend une réponse (pattern request/reply)
        
        Args:
            recipient: Destinataire
            content: Contenu de la requête
            message_type: Type de message
            priority: Priorité
            timeout_seconds: Timeout en secondes
            **kwargs: Métadonnées
            
        Returns:
            Réponse ou None si timeout
        """
        correlation_id = str(uuid4())
        
        result = await self.send_communication(
            recipient=recipient,
            content=content,
            message_type=message_type,
            priority=priority,
            correlation_id=correlation_id,
            ttl_seconds=timeout_seconds,
            **kwargs
        )
        
        if not result["success"]:
            return None
        
        # Attendre la réponse
        try:
            future = self._pending_requests.get(correlation_id)
            if future:
                response = await asyncio.wait_for(future, timeout=timeout_seconds)
                return response
        except asyncio.TimeoutError:
            self._logger.warning(f"Request timeout pour {correlation_id}")
            self._pending_requests.pop(correlation_id, None)
        
        return None

    async def publish(self,
                     topic: str,
                     content: Any,
                     message_type: str = "event",
                     priority: MessagePriority = MessagePriority.NORMAL,
                     **kwargs) -> Dict[str, Any]:
        """
        Publie un message sur un topic (pub/sub)
        
        Args:
            topic: Topic de publication
            content: Contenu du message
            message_type: Type de message
            priority: Priorité
            **kwargs: Métadonnées
            
        Returns:
            Résultat de la publication
        """
        self._logger.debug(f"📢 publish: {topic}")
        
        # Récupérer les abonnés
        subscribers = await self._topic_manager.get_subscribers(topic)
        
        if not subscribers:
            self._logger.debug(f"Aucun abonné pour le topic {topic}")
            return {
                "success": True,
                "topic": topic,
                "subscribers_count": 0,
                "message_id": None
            }
        
        # Envoyer à chaque abonné
        message_id = None
        for subscriber in subscribers:
            result = await self.send_communication(
                recipient=subscriber,
                content=content,
                message_type=message_type,
                priority=priority,
                metadata={"topic": topic, **kwargs}
            )
            if result["success"] and not message_id:
                message_id = result["message_id"]
        
        return {
            "success": True,
            "topic": topic,
            "subscribers_count": len(subscribers),
            "message_id": message_id
        }

    async def subscribe(self, topic: str) -> bool:
        """Abonne l'agent à un topic"""
        return await self._topic_manager.subscribe(topic, self.name)

    async def unsubscribe(self, topic: str) -> bool:
        """Désabonne l'agent d'un topic"""
        return await self._topic_manager.unsubscribe(topic, self.name)

    # ============================================================================
    # TRAITEMENT DES MESSAGES (CORRIGÉ)
    # ============================================================================

    async def _message_processor(self):
        """Tâche de traitement des messages en file d'attente"""
        self._logger.info("🔄 Processeur de messages démarré")
        
        latencies = deque(maxlen=1000)  # Pour calcul des percentiles
        
        while self._status == AgentStatus.READY:
            try:
                processed_any = False
                
                # Traiter les files par ordre de priorité
                for queue_name in ["high_priority", "default", "batch"]:
                    queue = self._queues.get(queue_name)
                    if not queue:
                        continue
                    
                    # Récupérer un message
                    message = await queue.dequeue()
                    if not message:
                        continue
                    
                    processed_any = True
                    
                    # Traiter le message
                    start_time = time.time()
                    
                    try:
                        await self._process_message(message)
                        latency = (time.time() - start_time) * 1000  # ms
                        latencies.append(latency)
                        
                        self._stats["messages_processed"] += 1
                        message.status = MessageStatus.DELIVERED
                        message.delivered_at = datetime.now()
                        
                    except Exception as e:
                        self._logger.error(f"Erreur traitement message {message.id}: {e}")
                        await self._handle_processing_failure(message)
                    
                    # Mettre à jour les statistiques de latence
                    if latencies:
                        sorted_lat = sorted(latencies)
                        self._stats["processing_latency_p50"] = sorted_lat[len(sorted_lat)//2]
                        self._stats["processing_latency_p95"] = sorted_lat[int(len(sorted_lat)*0.95)]
                        self._stats["processing_latency_p99"] = sorted_lat[int(len(sorted_lat)*0.99)]
                    
                    # Mettre à jour le throughput
                    self._stats["throughput_current"] = len(latencies) / 60  # moyenne sur 1 min
                    self._stats["throughput_peak"] = max(
                        self._stats["throughput_peak"],
                        self._stats["throughput_current"]
                    )
                
                # Petite pause si aucun message n'a été traité
                if not processed_any:
                    await asyncio.sleep(0.01)
                    
            except asyncio.CancelledError:
                self._logger.info("🛑 Processeur de messages arrêté")
                break
            except Exception as e:
                self._logger.error(f"Erreur dans le processeur: {e}")
                await asyncio.sleep(1)

    async def _process_message(self, message: MessageEnvelope):
        """Traite un message individuel"""
        self._logger.debug(f"⚙️ Traitement message {message.id} -> {message.recipient}")
        
        # Vérifier expiration
        if message.is_expired():
            self._stats["messages_expired"] += 1
            message.status = MessageStatus.EXPIRED
            return
        
        # Vérifier le destinataire
        if message.recipient == "*" or message.recipient == "broadcast":
            # Broadcast à tous les agents
            # TODO: Implémenter broadcast via le registre
            pass
        elif message.recipient == self.name:
            # Message pour nous-mêmes
            await self._handle_local_message(message)
        else:
            # Message pour un autre agent - utiliser le bus de messages de BaseAgent
            base_message = Message(
                sender=message.sender,
                recipient=message.recipient,
                content=message.content,
                message_type=message.message_type,
                correlation_id=message.correlation_id
            )
            # Appeler la méthode parent (celle de BaseAgent)
            await super().send_message(base_message)

    async def _handle_local_message(self, message: MessageEnvelope):
        """Gère un message destiné à l'agent lui-même"""
        if message.message_type == "reply" and message.correlation_id:
            # C'est une réponse à une requête
            future = self._pending_requests.get(message.correlation_id)
            if future and not future.done():
                future.set_result(message.content)
                self._pending_requests.pop(message.correlation_id, None)
        else:
            # C'est une commande pour l'agent
            self._logger.warning(f"Type de message local non géré: {message.message_type}")

    async def _handle_processing_failure(self, message: MessageEnvelope):
        """Gère un échec de traitement"""
        message.retry_count += 1
        self._stats["messages_failed"] += 1
        
        if message.retry_count < message.max_retries:
            # Réessayer plus tard
            self._stats["messages_retried"] += 1
            message.status = MessageStatus.RETRYING
            delay = self._default_queue_config.get('retry', {}).get('initial_delay_ms', 100) / 1000
            await asyncio.sleep(delay * (2 ** (message.retry_count - 1)))  # backoff exponentiel
            await self._queues["default"].enqueue(message)
        else:
            # Trop d'échecs, envoyer en dead letter
            message.status = MessageStatus.DEAD_LETTER
            self._dead_letter_queue.append(message)
            self._logger.warning(f"Message {message.id} envoyé en dead letter après {message.retry_count} tentatives")
            
            # Mettre à jour le circuit breaker
            await self._update_circuit_breaker(message.recipient, failed=True)

    # ============================================================================
    # SURCHARGE DE LA MÉTHODE PARENT
    # ============================================================================

    async def send_message(self, message: Message) -> bool:
        """
        Surcharge de BaseAgent.send_message pour utiliser notre système de messagerie
        """
        self._logger.debug(f"📨 send_message (parent): {message.message_type} -> {message.recipient}")
        
        # Convertir le Message de BaseAgent en MessageEnvelope
        result = await self.send_communication(
            recipient=message.recipient,
            content=message.content,
            message_type=message.message_type,
            priority=MessagePriority(message.priority) if hasattr(message, 'priority') else MessagePriority.NORMAL,
            correlation_id=message.correlation_id,
            ttl_seconds=getattr(message, 'ttl', 3600),
            **message.metadata
        )
        
        return result.get("success", False)

    # ============================================================================
    # CIRCUIT BREAKER
    # ============================================================================

    async def _check_circuit_breaker(self, recipient: str) -> bool:
        """Vérifie si le circuit breaker est fermé pour un destinataire"""
        cb_config = self._comm_config.get('circuit_breaker', {})
        if not cb_config.get('enabled', True):
            return True
        
        cb = self._circuit_breakers.get(recipient, {
            "state": "closed",
            "failures": 0,
            "last_failure": None,
            "open_until": None
        })
        
        # Vérifier si le circuit est ouvert
        if cb["state"] == "open":
            if cb["open_until"] and datetime.now() > cb["open_until"]:
                # Passer en half-open
                cb["state"] = "half-open"
                cb["failures"] = 0
                self._circuit_breakers[recipient] = cb
                return True
            return False
        
        return True

    async def _update_circuit_breaker(self, recipient: str, failed: bool):
        """Met à jour l'état du circuit breaker"""
        cb_config = self._comm_config.get('circuit_breaker', {})
        if not cb_config.get('enabled', True):
            return
        
        cb = self._circuit_breakers.get(recipient, {
            "state": "closed",
            "failures": 0,
            "last_failure": None,
            "open_until": None
        })
        
        if failed:
            cb["failures"] += 1
            cb["last_failure"] = datetime.now()
            
            threshold = cb_config.get('failure_threshold', 5)
            if cb["state"] == "closed" and cb["failures"] >= threshold:
                # Ouvrir le circuit
                cb["state"] = "open"
                timeout = cb_config.get('timeout_seconds', 30)
                cb["open_until"] = datetime.now() + timedelta(seconds=timeout)
                self._logger.warning(f"Circuit breaker ouvert pour {recipient}")
            
            elif cb["state"] == "half-open":
                # Retour en open si échec en half-open
                cb["state"] = "open"
                timeout = cb_config.get('timeout_seconds', 30)
                cb["open_until"] = datetime.now() + timedelta(seconds=timeout)
        else:
            # Succès
            if cb["state"] == "half-open":
                # Fermer le circuit
                cb["state"] = "closed"
                cb["failures"] = 0
                self._logger.info(f"Circuit breaker fermé pour {recipient}")
            elif cb["state"] == "closed":
                # Réinitialiser partiellement
                cb["failures"] = max(0, cb["failures"] - 1)
        
        self._circuit_breakers[recipient] = cb

    # ============================================================================
    # TÂCHES DE FOND
    # ============================================================================

    async def _retry_worker(self):
        """Gère les réessais des messages en dead letter"""
        interval = 30  # toutes les 30 secondes
        
        self._logger.info("🔄 Tâche de réessai démarrée")
        while self._status == AgentStatus.READY:
            try:
                await asyncio.sleep(interval)
                
                # Réessayer les messages en dead letter
                to_retry = []
                while self._dead_letter_queue and len(to_retry) < 100:
                    msg = self._dead_letter_queue.popleft()
                    if msg.retry_count < msg.max_retries * 2:  # Double maximum pour dead letter
                        to_retry.append(msg)
                    else:
                        self._logger.warning(f"Message {msg.id} abandonné définitivement")
                
                for msg in to_retry:
                    msg.retry_count += 1
                    await self._queues["default"].enqueue(msg)
                    self._stats["messages_retried"] += 1
                
                if to_retry:
                    self._logger.info(f"🔄 {len(to_retry)} messages réessayés depuis dead letter")
                    
            except asyncio.CancelledError:
                self._logger.info("🛑 Tâche de réessai arrêtée")
                break
            except Exception as e:
                self._logger.error(f"Erreur dans retry_worker: {e}")

    # ============================================================================
    # UTILITAIRES
    # ============================================================================

    def _select_queue(self, priority: MessagePriority) -> str:
        """Sélectionne la file appropriée selon la priorité"""
        if priority in [MessagePriority.CRITICAL, MessagePriority.SYSTEM]:
            return "high_priority"
        elif priority == MessagePriority.HIGH:
            return "high_priority"
        elif priority == MessagePriority.NORMAL:
            return "default"
        else:
            return "batch"

    async def get_queue_stats(self) -> Dict[str, Any]:
        """Retourne les statistiques des files"""
        stats = {}
        for name, queue in self._queues.items():
            stats[name] = await queue.get_stats()
        return stats

    async def get_topic_stats(self) -> Dict[str, Any]:
        """Retourne les statistiques des topics"""
        return {
            "topics_count": len(self._topic_manager._topics),
            "subscribers_count": len(self._topic_manager._subscribers),
            "topics": {
                topic: len(subscribers)
                for topic, subscribers in self._topic_manager._topics.items()
            }
        }

    # ============================================================================
    # STATISTIQUES ET MONITORING
    # ============================================================================

    async def get_stats(self) -> Dict[str, Any]:
        """Retourne les statistiques de communication"""
        stats = self._stats.copy()
        
        # Statistiques des files
        stats["queues"] = await self.get_queue_stats()
        
        # Statistiques des topics
        stats["topics"] = await self.get_topic_stats()
        
        # Circuit breakers
        stats["circuit_breakers"] = {
            recipient: {
                "state": cb["state"],
                "failures": cb["failures"]
            }
            for recipient, cb in self._circuit_breakers.items()
        }
        
        # Taille des structures internes
        stats["message_store_size"] = len(self._message_store)
        stats["pending_requests"] = len(self._pending_requests)
        stats["dead_letter_size"] = len(self._dead_letter_queue)
        
        # Calculs supplémentaires
        stats["success_rate"] = round(
            (stats["messages_processed"] / max(1, stats["messages_received"])) * 100, 2
        )
        
        return stats

    # ============================================================================
    # GESTION DES MESSAGES (hérités de BaseAgent)
    # ============================================================================

    async def _handle_custom_message(self, message: Message) -> Optional[Message]:
        """Gère les messages personnalisés"""
        try:
            msg_type = message.message_type
            self._logger.debug(f"Message personnalisé reçu: {msg_type} de {message.sender}")

            # D'abord, essayer de déléguer à un sous-agent
            if message.content and "sub_agent_task" in message.content:
                task_type = message.content.get("sub_agent_task")
                return await self.delegate_to_sub_agent(task_type, message.content)

            # Handlers standards
            handlers = {
                "communication.send": self._handle_send_request,
                "communication.request": self._handle_request,
                "communication.publish": self._handle_publish,
                "communication.subscribe": self._handle_subscribe,
                "communication.unsubscribe": self._handle_unsubscribe,
                "communication.stats": self._handle_stats_request,
                "communication.queue_stats": self._handle_queue_stats,
                "communication.topic_stats": self._handle_topic_stats,
                "communication.get_sub_agents_status": self._handle_get_sub_agents_status,
                "communication.pause": self._handle_pause,
                "communication.resume": self._handle_resume,
                "communication.shutdown": self._handle_shutdown,
            }

            if msg_type in handlers:
                return await handlers[msg_type](message)

            self._logger.warning(f"Aucun handler pour le type: {msg_type}")
            return None

        except Exception as e:
            self._logger.error(f"Erreur traitement message: {e}")
            return Message(
                sender=self.name,
                recipient=message.sender,
                content={"error": str(e), "traceback": traceback.format_exc()},
                message_type=MessageType.ERROR.value,
                correlation_id=message.message_id
            )

    async def _handle_send_request(self, message: Message) -> Message:
        content = message.content
        result = await self.send_communication(
            recipient=content.get("recipient"),
            content=content.get("content"),
            message_type=content.get("message_type", "command"),
            priority=MessagePriority(content.get("priority", 1)),
            correlation_id=content.get("correlation_id"),
            ttl_seconds=content.get("ttl_seconds"),
            **content.get("metadata", {})
        )
        return Message(
            sender=self.name,
            recipient=message.sender,
            content=result,
            message_type="communication.send_response",
            correlation_id=message.message_id
        )

    async def _handle_request(self, message: Message) -> Message:
        content = message.content
        response = await self.request(
            recipient=content.get("recipient"),
            content=content.get("content"),
            message_type=content.get("message_type", "request"),
            priority=MessagePriority(content.get("priority", 2)),
            timeout_seconds=content.get("timeout", 30),
            **content.get("metadata", {})
        )
        return Message(
            sender=self.name,
            recipient=message.sender,
            content={"response": response},
            message_type="communication.request_response",
            correlation_id=message.message_id
        )

    async def _handle_publish(self, message: Message) -> Message:
        content = message.content
        result = await self.publish(
            topic=content.get("topic"),
            content=content.get("content"),
            message_type=content.get("message_type", "event"),
            priority=MessagePriority(content.get("priority", 1)),
            **content.get("metadata", {})
        )
        return Message(
            sender=self.name,
            recipient=message.sender,
            content=result,
            message_type="communication.publish_response",
            correlation_id=message.message_id
        )

    async def _handle_subscribe(self, message: Message) -> Message:
        success = await self.subscribe(message.content.get("topic"))
        return Message(
            sender=self.name,
            recipient=message.sender,
            content={"success": success},
            message_type="communication.subscribe_response",
            correlation_id=message.message_id
        )

    async def _handle_unsubscribe(self, message: Message) -> Message:
        success = await self.unsubscribe(message.content.get("topic"))
        return Message(
            sender=self.name,
            recipient=message.sender,
            content={"success": success},
            message_type="communication.unsubscribe_response",
            correlation_id=message.message_id
        )

    async def _handle_stats_request(self, message: Message) -> Message:
        stats = await self.get_stats()
        return Message(
            sender=self.name,
            recipient=message.sender,
            content=stats,
            message_type="communication.stats_response",
            correlation_id=message.message_id
        )

    async def _handle_queue_stats(self, message: Message) -> Message:
        stats = await self.get_queue_stats()
        return Message(
            sender=self.name,
            recipient=message.sender,
            content=stats,
            message_type="communication.queue_stats_response",
            correlation_id=message.message_id
        )

    async def _handle_topic_stats(self, message: Message) -> Message:
        stats = await self.get_topic_stats()
        return Message(
            sender=self.name,
            recipient=message.sender,
            content=stats,
            message_type="communication.topic_stats_response",
            correlation_id=message.message_id
        )

    async def _handle_get_sub_agents_status(self, message: Message) -> Message:
        """Gère la récupération du statut des sous-agents"""
        status = await self.get_sub_agents_status()
        return Message(
            sender=self.name,
            recipient=message.sender,
            content=status,
            message_type="communication.sub_agents_status",
            correlation_id=message.message_id
        )

    async def _handle_pause(self, message: Message) -> Message:
        """Gère la pause"""
        await self.pause()
        return Message(
            sender=self.name,
            recipient=message.sender,
            content={"status": "paused"},
            message_type="communication.status_update",
            correlation_id=message.message_id
        )

    async def _handle_resume(self, message: Message) -> Message:
        """Gère la reprise"""
        await self.resume()
        return Message(
            sender=self.name,
            recipient=message.sender,
            content={"status": "resumed"},
            message_type="communication.status_update",
            correlation_id=message.message_id
        )

    async def _handle_shutdown(self, message: Message) -> Message:
        """Gère l'arrêt"""
        await self.shutdown()
        return Message(
            sender=self.name,
            recipient=message.sender,
            content={"status": "shutdown"},
            message_type="communication.status_update",
            correlation_id=message.message_id
        )


# ============================================================================
# FONCTION D'USINE
# ============================================================================

def create_communication_agent(config_path: Optional[str] = None) -> CommunicationAgent:
    """Crée une instance de l'agent communication"""
    return CommunicationAgent(config_path)


# ============================================================================
# POINT D'ENTRÉE POUR EXÉCUTION DIRECTE
# ============================================================================

if __name__ == "__main__":
    async def main():
        print("💬 TEST COMMUNICATION AGENT")
        print("="*60)
        
        agent = CommunicationAgent()
        await agent.initialize()
        
        agent_info = agent.get_agent_info()
        print(f"✅ Agent: {agent_info['name']} v{agent_info['version']}")
        print(f"✅ Statut: {agent_info['status']}")
        print(f"✅ Files: {agent_info['features']['queues']}")
        print(f"✅ Sous-agents: {agent_info['features']['sub_agents']}")
        
        # Test send
        print(f"\n📨 Test send...")
        result = await agent.send_communication(
            recipient="test_agent",
            content={"action": "test", "value": 123},
            message_type="test"
        )
        print(f"✅ Envoyé: {result}")
        
        # Test publish/subscribe
        print(f"\n📢 Test publish...")
        await agent.subscribe("test.topic")
        pub_result = await agent.publish(
            topic="test.topic",
            content={"event": "test_event"}
        )
        print(f"✅ Publié: {pub_result}")
        
        # Statistiques
        stats = await agent.get_stats()
        print(f"\n📊 Statistiques:")
        print(f"  Messages reçus: {stats['messages_received']}")
        print(f"  Messages traités: {stats['messages_processed']}")
        print(f"  Taux succès: {stats['success_rate']}%")
        print(f"  Latence p95: {stats['processing_latency_p95']:.2f}ms")
        
        health = await agent.health_check()
        print(f"\n❤️  Health: {health['status']}")
        
        print("\n" + "="*60)
        print("✅ COMMUNICATION AGENT OPÉRATIONNEL")
        print("="*60)
        
        await agent.shutdown()
    
    asyncio.run(main())
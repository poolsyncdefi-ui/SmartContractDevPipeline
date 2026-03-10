"""
Queue Manager SubAgent - Gestionnaire de files d'attente
Version: 2.0.0

Gère les files d'attente prioritaires avec QoS avancé,
monitoring en temps réel et persistance des messages.
"""

import logging
import sys
import asyncio
import json
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, Optional, List, Union
from enum import Enum
from dataclasses import dataclass, field
from collections import deque
import heapq

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

class QueueType(Enum):
    """Types de files d'attente supportés"""
    FIFO = "fifo"
    LIFO = "lifo"
    PRIORITY = "priority"


class MessageStatus(Enum):
    """Statuts possibles d'un message dans la file"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    EXPIRED = "expired"
    DEAD_LETTER = "dead_letter"


@dataclass
class QueueMessage:
    """Message dans une file d'attente"""
    id: str
    content: Any
    priority: int = 0
    status: MessageStatus = MessageStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    enqueued_at: Optional[datetime] = None
    dequeued_at: Optional[datetime] = None
    processed_at: Optional[datetime] = None
    ttl_seconds: int = 3600
    retry_count: int = 0
    max_retries: int = 3
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def is_expired(self) -> bool:
        """Vérifie si le message a expiré"""
        if not self.enqueued_at:
            return False
        expiry = self.enqueued_at + timedelta(seconds=self.ttl_seconds)
        return datetime.now() > expiry

    @property
    def queue_time_ms(self) -> Optional[float]:
        """Temps passé dans la file en ms"""
        if self.enqueued_at and self.dequeued_at:
            return (self.dequeued_at - self.enqueued_at).total_seconds() * 1000
        return None

    def to_dict(self) -> Dict[str, Any]:
        """Convertit en dictionnaire"""
        return {
            "id": self.id,
            "priority": self.priority,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "enqueued_at": self.enqueued_at.isoformat() if self.enqueued_at else None,
            "dequeued_at": self.dequeued_at.isoformat() if self.dequeued_at else None,
            "ttl_seconds": self.ttl_seconds,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
            "metadata": self.metadata,
            "is_expired": self.is_expired,
            "queue_time_ms": self.queue_time_ms
        }


@dataclass
class QueueStats:
    """Statistiques d'une file d'attente"""
    name: str
    queue_type: QueueType
    size: int = 0
    max_size: int = 10000
    enqueued_total: int = 0
    dequeued_total: int = 0
    expired_total: int = 0
    failed_total: int = 0
    created_at: datetime = field(default_factory=datetime.now)
    last_activity: Optional[datetime] = None
    avg_queue_time_ms: float = 0.0
    peak_size: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convertit en dictionnaire"""
        return {
            "name": self.name,
            "queue_type": self.queue_type.value,
            "size": self.size,
            "max_size": self.max_size,
            "usage_percent": round((self.size / self.max_size) * 100, 2) if self.max_size > 0 else 0,
            "enqueued_total": self.enqueued_total,
            "dequeued_total": self.dequeued_total,
            "expired_total": self.expired_total,
            "failed_total": self.failed_total,
            "created_at": self.created_at.isoformat(),
            "last_activity": self.last_activity.isoformat() if self.last_activity else None,
            "avg_queue_time_ms": round(self.avg_queue_time_ms, 2),
            "peak_size": self.peak_size,
            "uptime_seconds": (datetime.now() - self.created_at).total_seconds()
        }


# ============================================================================
# SOUS-AGENT PRINCIPAL
# ============================================================================

class QueueManagerSubAgent(BaseSubAgent):
    """
    Sous-agent Queue Manager - Gestionnaire de files d'attente

    Gère différents types de files (FIFO, LIFO, Priority) avec :
    - Monitoring en temps réel
    - Persistance optionnelle
    - Gestion des expirations
    - Dead letter queue
    - Statistiques détaillées
    """

    def __init__(self, config_path: str = ""):
        """Initialise le queue manager"""
        super().__init__(config_path)

        # Métadonnées
        self._subagent_display_name = "📊 Queue Manager"
        self._subagent_description = "Gestionnaire de files d'attente prioritaires"
        self._subagent_version = "2.0.0"
        self._subagent_category = "communication"
        self._subagent_capabilities = [
            "queue.create",
            "queue.delete",
            "queue.enqueue",
            "queue.dequeue",
            "queue.stats",
            "queue.list"
        ]

        # État interne
        self._queues: Dict[str, Any] = {}  # nom -> structure de file
        self._queue_stats: Dict[str, QueueStats] = {}
        self._queue_locks: Dict[str, asyncio.Lock] = {}
        self._dead_letter_queue: deque = deque(maxlen=10000)

        # Configuration
        self._default_config = self._agent_config.get('queue_manager', {}).get('defaults', {})
        self._queue_types = self._agent_config.get('queue_manager', {}).get('queue_types', {})

        # Tâche de nettoyage des expirés
        self._cleanup_task: Optional[asyncio.Task] = None

        logger.info(f"✅ {self._subagent_display_name} initialisé")

    # ========================================================================
    # IMPLÉMENTATION DES MÉTHODES ABSTRACTES
    # ========================================================================

    async def _initialize_subagent_components(self) -> bool:
        """Initialise les composants spécifiques"""
        logger.info("Initialisation des composants Queue Manager...")

        # Démarrer la tâche de nettoyage
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())

        logger.info("✅ Composants Queue Manager initialisés")
        return True

    async def _initialize_components(self) -> bool:
        """Implémentation requise par BaseAgent"""
        return await self._initialize_subagent_components()

    def _get_capability_handlers(self) -> Dict[str, Any]:
        """Retourne les handlers spécifiques"""
        return {
            "queue.create": self._handle_create,
            "queue.delete": self._handle_delete,
            "queue.enqueue": self._handle_enqueue,
            "queue.dequeue": self._handle_dequeue,
            "queue.stats": self._handle_stats,
            "queue.list": self._handle_list,
        }

    # ========================================================================
    # IMPLÉMENTATION DES FILES D'ATTENTE
    # ========================================================================

    def _create_queue_structure(self, queue_type: QueueType) -> Any:
        """Crée la structure de données appropriée pour le type de file"""
        if queue_type == QueueType.FIFO:
            return deque()
        elif queue_type == QueueType.LIFO:
            return []  # Utilisé comme pile avec append/pop
        elif queue_type == QueueType.PRIORITY:
            return []  # Heap pour la priorité
        else:
            raise ValueError(f"Type de file inconnu: {queue_type}")

    async def _get_queue_lock(self, queue_name: str) -> asyncio.Lock:
        """Récupère ou crée un verrou pour une file"""
        if queue_name not in self._queue_locks:
            self._queue_locks[queue_name] = asyncio.Lock()
        return self._queue_locks[queue_name]

    # ========================================================================
    # OPÉRATIONS SUR LES FILES
    # ========================================================================

    async def _create_queue(self, queue_name: str, queue_type: str = "fifo",
                            max_size: Optional[int] = None,
                            persistent: bool = False) -> Dict[str, Any]:
        """Crée une nouvelle file d'attente"""
        if queue_name in self._queues:
            return {
                "success": False,
                "error": f"La file {queue_name} existe déjà"
            }

        # Valider le type
        try:
            qtype = QueueType(queue_type)
        except ValueError:
            return {
                "success": False,
                "error": f"Type de file invalide: {queue_type}"
            }

        # Configuration
        config = self._queue_types.get(qtype.value, {})
        actual_max_size = max_size or config.get('max_size', self._default_config.get('max_size', 10000))

        # Créer la file
        self._queues[queue_name] = self._create_queue_structure(qtype)
        self._queue_stats[queue_name] = QueueStats(
            name=queue_name,
            queue_type=qtype,
            max_size=actual_max_size
        )

        logger.info(f"✅ File créée: {queue_name} ({qtype.value})")

        return {
            "success": True,
            "queue_name": queue_name,
            "queue_type": qtype.value,
            "max_size": actual_max_size,
            "persistent": persistent
        }

    async def _delete_queue(self, queue_name: str, force: bool = False) -> Dict[str, Any]:
        """Supprime une file d'attente"""
        if queue_name not in self._queues:
            return {
                "success": False,
                "error": f"File {queue_name} non trouvée"
            }

        stats = self._queue_stats[queue_name]

        # Vérifier si la file n'est pas vide
        if stats.size > 0 and not force:
            return {
                "success": False,
                "error": f"File non vide ({stats.size} messages). Utilisez force=True pour forcer"
            }

        # Supprimer
        del self._queues[queue_name]
        del self._queue_stats[queue_name]
        if queue_name in self._queue_locks:
            del self._queue_locks[queue_name]

        logger.info(f"🗑️ File supprimée: {queue_name}")

        return {
            "success": True,
            "queue_name": queue_name
        }

    async def _enqueue(self, queue_name: str, message: Any,
                       priority: int = 0, ttl_seconds: Optional[int] = None) -> Dict[str, Any]:
        """Ajoute un message à une file"""
        if queue_name not in self._queues:
            return {
                "success": False,
                "error": f"File {queue_name} non trouvée"
            }

        lock = await self._get_queue_lock(queue_name)
        async with lock:
            queue = self._queues[queue_name]
            stats = self._queue_stats[queue_name]

            # Vérifier la capacité
            if stats.size >= stats.max_size:
                return {
                    "success": False,
                    "error": f"File pleine (max: {stats.max_size})"
                }

            # Créer le message
            import uuid
            msg = QueueMessage(
                id=str(uuid.uuid4()),
                content=message,
                priority=priority,
                ttl_seconds=ttl_seconds or self._default_config.get('ttl_seconds', 3600),
                enqueued_at=datetime.now()
            )

            # Ajouter selon le type
            if stats.queue_type == QueueType.FIFO:
                queue.append(msg)
            elif stats.queue_type == QueueType.LIFO:
                queue.append(msg)  # On utilise pop() pour LIFO
            elif stats.queue_type == QueueType.PRIORITY:
                heapq.heappush(queue, (-priority, msg.enqueued_at.timestamp(), msg))

            # Mettre à jour les stats
            stats.size += 1
            stats.enqueued_total += 1
            stats.last_activity = datetime.now()
            if stats.size > stats.peak_size:
                stats.peak_size = stats.size

            logger.debug(f"📥 Message {msg.id} ajouté à {queue_name}")

            return {
                "success": True,
                "message_id": msg.id,
                "queue_name": queue_name,
                "position": stats.size
            }

    async def _dequeue(self, queue_name: str, timeout_seconds: Optional[int] = None,
                       peek_only: bool = False) -> Dict[str, Any]:
        """Récupère un message d'une file"""
        if queue_name not in self._queues:
            return {
                "success": False,
                "error": f"File {queue_name} non trouvée"
            }

        lock = await self._get_queue_lock(queue_name)
        async with lock:
            queue = self._queues[queue_name]
            stats = self._queue_stats[queue_name]

            if stats.size == 0:
                if timeout_seconds:
                    # Attendre un message (simplifié)
                    lock.release()
                    await asyncio.sleep(0.1)
                    return await self._dequeue(queue_name, 0, peek_only)
                return {
                    "success": False,
                    "error": "File vide"
                }

            # Récupérer le message selon le type
            msg = None
            if stats.queue_type == QueueType.FIFO:
                msg = queue[0] if peek_only else queue.popleft()
            elif stats.queue_type == QueueType.LIFO:
                msg = queue[-1] if peek_only else queue.pop()
            elif stats.queue_type == QueueType.PRIORITY:
                if peek_only:
                    msg = queue[0][2]  # Le tuple est (priority, timestamp, message)
                else:
                    _, _, msg = heapq.heappop(queue)

            if not peek_only:
                stats.size -= 1
                stats.dequeued_total += 1
                stats.last_activity = datetime.now()

            msg.dequeued_at = datetime.now()
            msg.status = MessageStatus.PROCESSING

            logger.debug(f"📤 Message {msg.id} récupéré de {queue_name}")

            return {
                "success": True,
                "message": msg.to_dict(),
                "queue_name": queue_name,
                "peek_only": peek_only
            }

    # ========================================================================
    # TÂCHES DE FOND
    # ========================================================================

    async def _cleanup_loop(self):
        """Nettoie périodiquement les messages expirés"""
        logger.info("🔄 Boucle de nettoyage démarrée")

        while self._status.value == "ready":
            try:
                await asyncio.sleep(60)  # Vérification toutes les minutes

                expired_count = 0
                for queue_name, stats in list(self._queue_stats.items()):
                    if queue_name not in self._queues:
                        continue

                    lock = await self._get_queue_lock(queue_name)
                    async with lock:
                        queue = self._queues[queue_name]
                        new_queue = self._create_queue_structure(stats.queue_type)
                        removed = 0

                        # Filtrer les messages expirés
                        if stats.queue_type == QueueType.FIFO:
                            while queue:
                                msg = queue.popleft()
                                if msg.is_expired:
                                    removed += 1
                                    self._dead_letter_queue.append(msg)
                                else:
                                    new_queue.append(msg)
                            self._queues[queue_name] = new_queue

                        elif stats.queue_type == QueueType.LIFO:
                            temp = []
                            while queue:
                                msg = queue.pop()
                                if msg.is_expired:
                                    removed += 1
                                    self._dead_letter_queue.append(msg)
                                else:
                                    temp.append(msg)
                            # Remettre dans l'ordre
                            while temp:
                                queue.append(temp.pop())

                        elif stats.queue_type == QueueType.PRIORITY:
                            temp = []
                            while queue:
                                _, _, msg = heapq.heappop(queue)
                                if msg.is_expired:
                                    removed += 1
                                    self._dead_letter_queue.append(msg)
                                else:
                                    temp.append(msg)
                            # Reconstruire le heap
                            for msg in temp:
                                heapq.heappush(queue, (-msg.priority, msg.enqueued_at.timestamp(), msg))

                        if removed > 0:
                            stats.size -= removed
                            stats.expired_total += removed
                            expired_count += removed
                            logger.debug(f"🧹 {removed} messages expirés supprimés de {queue_name}")

                if expired_count > 0:
                    logger.info(f"🧹 Nettoyage terminé: {expired_count} messages expirés")

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"❌ Erreur dans la boucle de nettoyage: {e}")

    # ========================================================================
    # HANDLERS DE CAPACITÉS
    # ========================================================================

    async def _handle_create(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Crée une nouvelle file"""
        queue_name = params.get("queue_name")
        if not queue_name:
            return {"success": False, "error": "queue_name requis"}

        return await self._create_queue(
            queue_name=queue_name,
            queue_type=params.get("queue_type", "fifo"),
            max_size=params.get("max_size"),
            persistent=params.get("persistent", False)
        )

    async def _handle_delete(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Supprime une file"""
        queue_name = params.get("queue_name")
        if not queue_name:
            return {"success": False, "error": "queue_name requis"}

        return await self._delete_queue(
            queue_name=queue_name,
            force=params.get("force", False)
        )

    async def _handle_enqueue(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Ajoute un message à une file"""
        queue_name = params.get("queue_name")
        message = params.get("message")

        if not queue_name:
            return {"success": False, "error": "queue_name requis"}
        if message is None:
            return {"success": False, "error": "message requis"}

        return await self._enqueue(
            queue_name=queue_name,
            message=message,
            priority=params.get("priority", 0),
            ttl_seconds=params.get("ttl_seconds")
        )

    async def _handle_dequeue(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Récupère un message d'une file"""
        queue_name = params.get("queue_name")
        if not queue_name:
            return {"success": False, "error": "queue_name requis"}

        return await self._dequeue(
            queue_name=queue_name,
            timeout_seconds=params.get("timeout_seconds"),
            peek_only=params.get("peek_only", False)
        )

    async def _handle_stats(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Statistiques d'une file"""
        queue_name = params.get("queue_name")
        detailed = params.get("detailed", False)

        if queue_name:
            if queue_name not in self._queue_stats:
                return {"success": False, "error": f"File {queue_name} non trouvée"}
            stats = {queue_name: self._queue_stats[queue_name].to_dict()}

            if detailed and queue_name in self._queues:
                # Ajouter un échantillon des messages
                lock = await self._get_queue_lock(queue_name)
                async with lock:
                    queue = self._queues[queue_name]
                    sample = []
                    if stats.queue_type == QueueType.PRIORITY:
                        sample = [msg[2].to_dict() for msg in list(queue)[:5]]
                    else:
                        sample = [msg.to_dict() for msg in list(queue)[:5]]
                    stats[queue_name]["sample_messages"] = sample
        else:
            stats = {name: s.to_dict() for name, s in self._queue_stats.items()}

        return {
            "success": True,
            "queues": stats,
            "count": len(stats),
            "dead_letter_size": len(self._dead_letter_queue),
            "timestamp": datetime.now().isoformat()
        }

    async def _handle_list(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Liste toutes les files"""
        filter_str = params.get("filter", "")
        include_stats = params.get("include_stats", False)

        queues = []
        for name, stats in self._queue_stats.items():
            if filter_str and filter_str not in name:
                continue

            queue_info = {
                "name": name,
                "type": stats.queue_type.value,
                "size": stats.size,
                "max_size": stats.max_size
            }

            if include_stats:
                queue_info["stats"] = stats.to_dict()

            queues.append(queue_info)

        return {
            "success": True,
            "queues": queues,
            "count": len(queues),
            "timestamp": datetime.now().isoformat()
        }

    # ========================================================================
    # SURCHARGE POUR LE NETTOYAGE
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
# FONCTION D'USINE
# ============================================================================

def create_queue_manager_agent(config_path: str = "") -> "QueueManagerSubAgent":
    """Crée une instance du sous-agent queue manager"""
    return QueueManagerSubAgent(config_path)
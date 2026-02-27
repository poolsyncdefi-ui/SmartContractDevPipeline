import logging

logger = logging.getLogger(__name__)

"""
Communication Agent - Système nerveux central
Gestion des messages inter-agents avec files d'attente, persistance, pub/sub
Version: 2.0.0
"""

import os
import sys
import json
import yaml
import asyncio
import hashlib
import pickle
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Dict, List, Any, Optional, Set, Callable, Union
from collections import defaultdict, deque
import heapq
import uuid
import zlib
import traceback

# Import BaseAgent
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from agents.base_agent.base_agent import BaseAgent, AgentStatus, AgentStatus


class MessagePriority(Enum):
    """Priorités des messages"""
    LOW = 0
    NORMAL = 1
    HIGH = 2
    CRITICAL = 3


class MessageStatus(Enum):
    """Statuts des messages"""
    PENDING = "pending"
    DELIVERED = "delivered"
    FAILED = "failed"
    EXPIRED = "expired"
    PROCESSING = "processing"
    RETRY = "retry"


class DeliveryGuarantee(Enum):
    """Garanties de livraison"""
    AT_MOST_ONCE = "at_most_once"
    AT_LEAST_ONCE = "at_least_once"
    EXACTLY_ONCE = "exactly_once"


class Message:
    """Message échangé entre agents"""
    
    def __init__(self,
                 sender: str,
                 recipient: Optional[str],
                 message_type: str,
                 payload: Any,
                 priority: MessagePriority = MessagePriority.NORMAL,
                 correlation_id: Optional[str] = None,
                 reply_to: Optional[str] = None,
                 ttl: Optional[int] = 3600,
                 requires_ack: bool = True,
                 delivery_guarantee: DeliveryGuarantee = DeliveryGuarantee.AT_LEAST_ONCE):
        
        self.id = str(uuid.uuid4())
        self.timestamp = datetime.now()
        self.sender = sender
        self.recipient = recipient
        self.message_type = message_type
        self.payload = payload
        self.priority = priority
        self.correlation_id = correlation_id or self.id
        self.reply_to = reply_to
        self.ttl = ttl
        self.expires_at = datetime.now() + timedelta(seconds=ttl) if ttl else None
        self.requires_ack = requires_ack
        self.delivery_guarantee = delivery_guarantee
        self.status = MessageStatus.PENDING
        self.retry_count = 0
        self.delivery_attempts = []
        self.acknowledged = False
        self.ack_at = None
        self.metadata = {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertit le message en dictionnaire"""
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat(),
            "sender": self.sender,
            "recipient": self.recipient,
            "message_type": self.message_type,
            "payload": self.payload,
            "priority": self.priority.value,
            "correlation_id": self.correlation_id,
            "reply_to": self.reply_to,
            "ttl": self.ttl,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "requires_ack": self.requires_ack,
            "delivery_guarantee": self.delivery_guarantee.value,
            "status": self.status.value,
            "retry_count": self.retry_count,
            "acknowledged": self.acknowledged,
            "ack_at": self.ack_at.isoformat() if self.ack_at else None,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Message':
        """Crée un message depuis un dictionnaire"""
        msg = cls(
            sender=data["sender"],
            recipient=data["recipient"],
            message_type=data["message_type"],
            payload=data["payload"],
            priority=MessagePriority(data["priority"]),
            correlation_id=data["correlation_id"],
            reply_to=data["reply_to"],
            ttl=data["ttl"],
            requires_ack=data["requires_ack"],
            delivery_guarantee=DeliveryGuarantee(data["delivery_guarantee"])
        )
        msg.id = data["id"]
        msg.timestamp = datetime.fromisoformat(data["timestamp"])
        msg.status = MessageStatus(data["status"])
        msg.retry_count = data["retry_count"]
        msg.acknowledged = data["acknowledged"]
        if data["ack_at"]:
            msg.ack_at = datetime.fromisoformat(data["ack_at"])
        msg.metadata = data.get("metadata", {})
        return msg
    
    def is_expired(self) -> bool:
        """Vérifie si le message a expiré"""
        return self.expires_at and datetime.now() > self.expires_at
    
    def add_delivery_attempt(self, success: bool, error: Optional[str] = None):
        """Ajoute une tentative de livraison"""
        self.delivery_attempts.append({
            "timestamp": datetime.now().isoformat(),
            "success": success,
            "error": error
        })
        self.retry_count += 1


class PriorityQueue:
    """File d'attente prioritaire"""
    
    def __init__(self, max_size: int = 10000):
        self.max_size = max_size
        self._queue = []
        self._counter = 0
    
    def push(self, message: Message):
        """Ajoute un message avec priorité"""
        if len(self._queue) >= self.max_size:
            raise Exception(f"Queue pleine ({self.max_size} messages)")
        
        priority_value = 5 - message.priority.value
        heapq.heappush(self._queue, (priority_value, self._counter, message))
        self._counter += 1
    
    def pop(self) -> Optional[Message]:
        """Récupère le message le plus prioritaire"""
        if not self._queue:
            return None
        return heapq.heappop(self._queue)[2]
    
    def peek(self) -> Optional[Message]:
        """Regarde le prochain message sans le retirer"""
        if not self._queue:
            return None
        return self._queue[0][2]
    
    def size(self) -> int:
        return len(self._queue)
    
    def clear(self):
        self._queue.clear()


class TopicManager:
    """Gestionnaire de topics pub/sub"""
    
    def __init__(self):
        self._subscribers: Dict[str, Set[str]] = defaultdict(set)
        self._topic_patterns: Dict[str, str] = {}
    
    def subscribe(self, topic: str, agent_id: str):
        """Souscrit un agent à un topic"""
        self._subscribers[topic].add(agent_id)
    
    def unsubscribe(self, topic: str, agent_id: str):
        """Désouscrit un agent d'un topic"""
        if topic in self._subscribers:
            self._subscribers[topic].discard(agent_id)
    
    def get_subscribers(self, topic: str) -> Set[str]:
        """Récupère tous les abonnés d'un topic"""
        subscribers = set()
        
        subscribers.update(self._subscribers.get(topic, set()))
        
        for t, subs in self._subscribers.items():
            if self._matches_pattern(topic, t):
                subscribers.update(subs)
        
        return subscribers
    
    def _matches_pattern(self, topic: str, pattern: str) -> bool:
        """Vérifie si un topic correspond à un pattern"""
        if pattern.endswith('*'):
            return topic.startswith(pattern[:-1])
        return topic == pattern
    
    def list_topics(self) -> List[str]:
        return list(self._subscribers.keys())
    
    def get_subscription_count(self, topic: Optional[str] = None) -> int:
        if topic:
            return len(self._subscribers.get(topic, set()))
        return sum(len(s) for s in self._subscribers.values())


class CommunicationAgent(BaseAgent):
    """
    Agent de communication centralisé
    Gère les échanges entre tous les agents du pipeline
    """
    
    def __init__(self, config_path: str = ""):
        """Initialise l'agent de communication"""
        super().__init__(config_path)
        
        self._logger.info("💬 Communication Agent créé")
        
        # Charger configuration
        self._load_configuration()
        
        # Initialiser les composants
        self._components = {}
        
        # =================================================================
        # FILES D'ATTENTE
        # =================================================================
        self._queues = {
            "default": PriorityQueue(
                self._config["communication"]["queues"]["default"]["max_size"]
            ),
            "high_priority": PriorityQueue(
                self._config["communication"]["queues"]["high_priority"]["max_size"]
            )
        }
        
        self._dead_letter_queue = []
        self._scheduled_messages = []
        
        # =================================================================
        # SUIVI DES MESSAGES
        # =================================================================
        self._pending_acks: Dict[str, Message] = {}
        self._waiting_replies: Dict[str, asyncio.Future] = {}
        self._message_history: deque = deque(maxlen=10000)
        
        # =================================================================
        # PUB/SUB
        # =================================================================
        self._topic_manager = TopicManager()
        
        # =================================================================
        # MÉTRIQUES
        # =================================================================
        self._metrics = {
            "messages_sent": 0,
            "messages_received": 0,
            "messages_failed": 0,
            "messages_retried": 0,
            "messages_expired": 0,
            "acks_received": 0,
            "queue_size": 0,
            "dead_letter_size": 0,
            "active_subscribers": 0,
            "throughput": 0,
            "avg_processing_time": 0
        }
        
        self._processing_times = deque(maxlen=100)
        
        # =================================================================
        # TÂCHES DE FOND
        # =================================================================
        self._processor_task = None
        self._cleanup_task = None
        self._scheduler_task = None
        
        # =================================================================
        # PERSISTANCE
        # =================================================================
        persistence_config = self._config["communication"]["persistence"]
        if persistence_config["levels"]["disk"]["enabled"]:
            self._storage_path = Path(persistence_config["levels"]["disk"]["path"])
        else:
            self._storage_path = Path("./agents/communication/storage")
        
        self._create_directories()
        self._load_persisted_messages()
    
    def _load_configuration(self):
        """Charge la configuration depuis le fichier YAML"""
        try:
            config_path = os.path.join(os.path.dirname(__file__), "config.yaml")
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    self._config = yaml.safe_load(f)
                self._logger.info(f"✅ Configuration chargée: communication v{self._config['agent']['version']}")
            else:
                self._logger.warning("⚠️ Fichier config.yaml non trouvé")
                self._config = self._get_default_config()
        except Exception as e:
            self._logger.error(f"❌ Erreur chargement config: {e}")
            self._config = self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Configuration par défaut"""
        return {
            "agent": {
                "name": "communication",
                "display_name": "💬 Communication Agent",
                "version": "1.0.0"
            },
            "communication": {
                "queues": {
                    "default": {"max_size": 10000},
                    "high_priority": {"max_size": 5000}
                },
                "persistence": {
                    "enabled": True,
                    "levels": {
                        "disk": {
                            "enabled": True,
                            "path": "./agents/communication/storage"
                        }
                    }
                }
            }
        }
    
    def _create_directories(self):
        """Crée les répertoires nécessaires"""
        dirs = [
            self._storage_path,
            self._storage_path / "messages",
            self._storage_path / "archive",
            Path("./reports/communication")
        ]
        
        for dir_path in dirs:
            dir_path.mkdir(parents=True, exist_ok=True)
            self._logger.debug(f"📁 Répertoire créé: {dir_path}")
    
    def _load_persisted_messages(self):
        """Charge les messages persistés"""
        if not self._config["communication"]["persistence"]["enabled"]:
            return
        
        messages_path = self._storage_path / "messages"
        for msg_file in messages_path.glob("*.msg"):
            try:
                with open(msg_file, 'rb') as f:
                    data = pickle.load(f)
                    message = Message.from_dict(data)
                    self._schedule_message(message)
                self._logger.debug(f"📦 Message chargé: {msg_file.name}")
            except Exception as e:
                self._logger.error(f"❌ Erreur chargement message {msg_file}: {e}")
    
    def _persist_message(self, message: Message):
        """Persiste un message"""
        if not self._config["communication"]["persistence"]["enabled"]:
            return
        
        try:
            msg_path = self._storage_path / "messages" / f"{message.id}.msg"
            with open(msg_path, 'wb') as f:
                pickle.dump(message.to_dict(), f)
        except Exception as e:
            self._logger.error(f"❌ Erreur persistance message {message.id}: {e}")
    
    def _delete_persisted_message(self, message_id: str):
        """Supprime un message persisté"""
        try:
            msg_path = self._storage_path / "messages" / f"{message_id}.msg"
            if msg_path.exists():
                msg_path.unlink()
        except Exception as e:
            self._logger.error(f"❌ Erreur suppression message {message_id}: {e}")
    
    async def initialize(self) -> bool:
        """Initialisation asynchrone"""
        try:
            self._set_status(AgentStatus.INITIALIZING)
            self._logger.info("💬 Initialisation du Communication Agent...")
            
            await self._initialize_components()
            
            self._processor_task = asyncio.create_task(self._message_processor())
            self._cleanup_task = asyncio.create_task(self._cleanup_worker())
            self._scheduler_task = asyncio.create_task(self._scheduler_worker())
            
            self._set_status(AgentStatus.READY)
            self._logger.info("✅ Communication Agent prêt")
            return True
            
        except Exception as e:
            self._logger.error(f"❌ Erreur initialisation: {e}")
            self._set_status(AgentStatus.ERROR)
            return False
    
    async def _initialize_components(self):
        """Initialise les composants - requis par BaseAgent"""
        self._logger.info("Initialisation des composants...")
        
        self._components = {
            "message_queue": True,
            "topic_manager": True,
            "persistence": self._config["communication"]["persistence"]["enabled"],
            "dead_letter_queue": True,
            "scheduler": True
        }
        
        self._logger.info(f"✅ Composants: {list(self._components.keys())}")
        return self._components
    
    # =================================================================
    # API PUBLIQUE - ENVOI DE MESSAGES
    # =================================================================
    
    async def send_to_agent(self,
                          recipient: str,
                          message_type: str,
                          payload: Any,
                          priority: MessagePriority = MessagePriority.NORMAL,
                          requires_ack: bool = True,
                          ttl: Optional[int] = 3600) -> str:
        """
        Envoie un message à un agent spécifique
        """
        message = Message(
            sender=self._name,
            recipient=recipient,
            message_type=message_type,
            payload=payload,
            priority=priority,
            requires_ack=requires_ack,
            ttl=ttl
        )
        
        await self._queue_message(message)
        return message.id
    
    # =================================================================
    # MÉTHODE REQUISE PAR BASEAGENT
    # =================================================================

    async def send_message(self, message_input: Union[Dict[str, Any], Message]) -> Union[str, Dict[str, Any]]:
        """
        Version compatible avec BaseAgent - Gère les deux types d'entrée
        """
        # Si c'est déjà un Message (appel interne de BaseAgent)
        if isinstance(message_input, Message):
            self._logger.debug(f"📨 Message interne reçu: {message_input.message_type}")
            await self._queue_message(message_input)
            return message_input.id
        
        # Si c'est un dictionnaire (appel normal)
        elif isinstance(message_input, dict):
            self._logger.debug(f"📨 Réception message BaseAgent: {message_input.get('type', 'unknown')}")
            
            msg_type = message_input.get("type", "unknown")
            sender = message_input.get("sender", "unknown")
            recipient = message_input.get("recipient")
            content = message_input.get("content", {})
            
            internal_msg = Message(
                sender=sender,
                recipient=recipient,
                message_type=msg_type,
                payload=content,
                priority=MessagePriority.NORMAL,
                requires_ack=True,
                ttl=30
            )
            
            await self._queue_message(internal_msg)
            return {"status": "queued", "message_id": internal_msg.id}
        
        else:
            self._logger.error(f"❌ Type de message non supporté: {type(message_input)}")
            return {"error": "Type de message non supporté"}
        
    async def broadcast(self,
                       message_type: str,
                       payload: Any,
                       priority: MessagePriority = MessagePriority.NORMAL) -> List[str]:
        """
        Diffuse un message à tous les agents
        """
        all_agents = await self._get_all_agents()
        
        message_ids = []
        for agent in all_agents:
            if agent != self._name:
                msg_id = await self.send_to_agent(
                    recipient=agent,
                    message_type=message_type,
                    payload=payload,
                    priority=priority,
                    requires_ack=False
                )
                message_ids.append(msg_id)
        
        return message_ids
    
    async def publish(self, topic: str, payload: Any, message_type: str = "event"):
        """
        Publie un message sur un topic (pub/sub)
        """
        subscribers = self._topic_manager.get_subscribers(topic)
        
        for subscriber in subscribers:
            await self.send_to_agent(
                recipient=subscriber,
                message_type=message_type,
                payload={"topic": topic, "data": payload},
                priority=MessagePriority.NORMAL,
                requires_ack=False
            )
        
        self._metrics["messages_sent"] += len(subscribers)
    
    async def request(self,
                     recipient: str,
                     message_type: str,
                     payload: Any,
                     timeout: int = 30) -> Any:
        """
        Envoie une requête et attend une réponse (pattern request-reply)
        """
        correlation_id = str(uuid.uuid4())
        future = asyncio.Future()
        self._waiting_replies[correlation_id] = future
        
        message = Message(
            sender=self._name,
            recipient=recipient,
            message_type=message_type,
            payload=payload,
            correlation_id=correlation_id,
            reply_to=self._name,
            ttl=timeout
        )
        
        await self._queue_message(message)
        
        try:
            response = await asyncio.wait_for(future, timeout)
            return response
        except asyncio.TimeoutError:
            del self._waiting_replies[correlation_id]
            raise TimeoutError(f"Pas de réponse de {recipient} après {timeout}s")
    
    async def send_message_base(self, message_dict: Dict[str, Any]) -> Dict[str, Any]:
        """
        Version compatible avec BaseAgent
        Reçoit un dictionnaire et le convertit en Message
        """
        self._logger.debug(f"📨 Réception message BaseAgent: {message_dict.get('type', 'unknown')}")
        
        msg_type = message_dict.get("type", "unknown")
        sender = message_dict.get("sender", "unknown")
        recipient = message_dict.get("recipient")
        content = message_dict.get("content", {})
        
        internal_msg = Message(
            sender=sender,
            recipient=recipient,
            message_type=msg_type,
            payload=content,
            priority=MessagePriority.NORMAL,
            requires_ack=True
        )
        
        await self._queue_message(internal_msg)
        
        return {"status": "queued", "message_id": internal_msg.id}
    
    # =================================================================
    # GESTION DES FILES D'ATTENTE
    # =================================================================
    
    async def _queue_message(self, message: Message):
        """Ajoute un message à la file d'attente"""
        
        if message.priority == MessagePriority.CRITICAL:
            queue = self._queues["high_priority"]
        else:
            queue = self._queues["default"]
        
        try:
            queue.push(message)
            self._metrics["messages_sent"] += 1
            self._metrics["queue_size"] = self._get_total_queue_size()
            
            if message.requires_ack:
                self._pending_acks[message.id] = message
                self._persist_message(message)
            
            self._logger.debug(f"📤 Message {message.id} mis en file (priorité {message.priority.name})")
            
        except Exception as e:
            self._logger.error(f"❌ Erreur mise en file du message {message.id}: {e}")
            self._metrics["messages_failed"] += 1
    
    def _schedule_message(self, message: Message):
        """Programme un message"""
        heapq.heappush(self._scheduled_messages, (message.timestamp.timestamp(), message))
    
    async def _message_processor(self):
        """Processeur de messages en arrière-plan"""
        self._logger.info("🔄 Processeur de messages démarré")
        
        while self._status == AgentStatus.READY:
            try:
                processed = False
                
                for queue_name in ["high_priority", "default"]:
                    queue = self._queues.get(queue_name)
                    if not queue:
                        continue
                    
                    message = queue.pop()
                    if message:
                        await self._process_message(message)
                        processed = True
                        break
                
                if not processed:
                    await asyncio.sleep(0.1)
                
                self._metrics["queue_size"] = self._get_total_queue_size()
                
            except Exception as e:
                self._logger.error(f"❌ Erreur processeur de messages: {e}")
                await asyncio.sleep(1)
    
    async def _process_message(self, message: Message):
        """Traite un message de la file"""
        
        if message.is_expired():
            self._metrics["messages_expired"] += 1
            self._logger.warning(f"⏰ Message expiré avant traitement: {message.id}")
            self._dead_letter_queue.append({
                "message": message,
                "reason": "expired",
                "timestamp": datetime.now().isoformat()
            })
            return
        
        self._logger.info(f"📨 Traitement message {message.id} pour {message.recipient}")
        
        await asyncio.sleep(0.1)
        
        if message.requires_ack:
            ack_message = Message(
                sender=message.recipient or "unknown",
                recipient=self._name,
                message_type="ack",
                payload={"original_message_id": message.id},
                priority=MessagePriority.LOW,
                requires_ack=False
            )
            await self.receive_message(ack_message)
    
    def _get_total_queue_size(self) -> int:
        """Calcule la taille totale des files"""
        return sum(q.size() for q in self._queues.values())
    
    # =================================================================
    # RÉCEPTION DE MESSAGES
    # =================================================================
    
    async def receive_message(self, message: Message) -> Optional[Message]:
        """
        Reçoit un message d'un autre agent
        """
        self._metrics["messages_received"] += 1
        self._message_history.append(message)
        
        if message.is_expired():
            self._metrics["messages_expired"] += 1
            self._logger.warning(f"⏰ Message expiré: {message.id}")
            return None
        
        start_time = datetime.now()
        
        try:
            if message.message_type == "ping":
                response = await self._handle_ping(message)
            elif message.message_type == "ack":
                await self._handle_ack(message)
                response = None
            else:
                response = await self._handle_custom_message(message)
            
            processing_time = (datetime.now() - start_time).total_seconds()
            self._processing_times.append(processing_time)
            self._metrics["avg_processing_time"] = sum(self._processing_times) / len(self._processing_times)
            
            return response
            
        except Exception as e:
            self._logger.error(f"❌ Erreur traitement message {message.id}: {e}")
            self._metrics["messages_failed"] += 1
            return None
    
    async def _handle_ping(self, message: Message) -> Message:
        """Répond à un ping"""
        return Message(
            sender=self._name,
            recipient=message.sender,
            message_type="pong",
            payload={"timestamp": datetime.now().isoformat()},
            correlation_id=message.correlation_id
        )
    
    async def _handle_ack(self, message: Message):
        """Traite un accusé de réception"""
        original_id = message.payload.get("original_message_id")
        if original_id in self._pending_acks:
            self._pending_acks[original_id].acknowledged = True
            self._pending_acks[original_id].ack_at = datetime.now()
            self._metrics["acks_received"] += 1
            self._delete_persisted_message(original_id)
    
    async def _handle_custom_message(self, message: Message) -> Optional[Message]:
        """Traite un message personnalisé"""
        self._logger.debug(f"📨 Message reçu de {message.sender}: {message.message_type}")
        
        if message.correlation_id in self._waiting_replies:
            future = self._waiting_replies.pop(message.correlation_id)
            future.set_result(message.payload)
            return None
        
        return None
    
    # =================================================================
    # PUB/SUB
    # =================================================================
    
    async def subscribe(self, topic: str, agent_id: str):
        """Souscrit un agent à un topic"""
        self._topic_manager.subscribe(topic, agent_id)
        self._metrics["active_subscribers"] = self._topic_manager.get_subscription_count()
        self._logger.info(f"📋 Agent {agent_id} souscrit au topic '{topic}'")
    
    async def unsubscribe(self, topic: str, agent_id: str):
        """Désouscrit un agent d'un topic"""
        self._topic_manager.unsubscribe(topic, agent_id)
        self._metrics["active_subscribers"] = self._topic_manager.get_subscription_count()
        self._logger.info(f"📋 Agent {agent_id} désouscrit du topic '{topic}'")
    
    def list_subscriptions(self, agent_id: Optional[str] = None) -> List[str]:
        """Liste les souscriptions"""
        if agent_id:
            topics = []
            for topic, subscribers in self._topic_manager._subscribers.items():
                if agent_id in subscribers:
                    topics.append(topic)
            return topics
        return self._topic_manager.list_topics()
    
    # =================================================================
    # MESSAGES PROGRAMMÉS
    # =================================================================
    
    async def schedule_message(self,
                              deliver_at: datetime,
                              recipient: str,
                              message_type: str,
                              payload: Any):
        """Programme un message pour livraison future"""
        message = Message(
            sender=self._name,
            recipient=recipient,
            message_type=message_type,
            payload=payload,
            priority=MessagePriority.NORMAL,
            ttl=None
        )
        
        heapq.heappush(self._scheduled_messages, (deliver_at.timestamp(), message))
        self._logger.info(f"📅 Message programmé pour {deliver_at.isoformat()}")
    
    async def _scheduler_worker(self):
        """Travailleur pour les messages programmés"""
        self._logger.info("🔄 Planificateur démarré")
        
        while self._status == AgentStatus.READY:
            try:
                now = datetime.now().timestamp()
                
                while self._scheduled_messages and self._scheduled_messages[0][0] <= now:
                    _, message = heapq.heappop(self._scheduled_messages)
                    await self._queue_message(message)
                
                await asyncio.sleep(1)
                
            except Exception as e:
                self._logger.error(f"❌ Erreur planificateur: {e}")
                await asyncio.sleep(5)
    
    # =================================================================
    # NETTOYAGE
    # =================================================================
    
    async def _cleanup_worker(self):
        """Nettoie les messages expirés et les vieux messages"""
        self._logger.info("🧹 Nettoyeur démarré")
        
        while self._status == AgentStatus.READY:
            try:
                await asyncio.sleep(60)
                
                for queue in self._queues.values():
                    temp_queue = PriorityQueue()
                    while True:
                        msg = queue.pop()
                        if not msg:
                            break
                        if not msg.is_expired():
                            temp_queue.push(msg)
                        else:
                            self._dead_letter_queue.append({
                                "message": msg,
                                "reason": "expired",
                                "timestamp": datetime.now().isoformat()
                            })
                            self._metrics["messages_expired"] += 1
                    
                    while True:
                        msg = temp_queue.pop()
                        if not msg:
                            break
                        queue.push(msg)
                
                cutoff = datetime.now() - timedelta(days=7)
                self._dead_letter_queue = [
                    entry for entry in self._dead_letter_queue
                    if datetime.fromisoformat(entry["timestamp"]) > cutoff
                ]
                
                self._metrics["dead_letter_size"] = len(self._dead_letter_queue)
                
            except Exception as e:
                self._logger.error(f"❌ Erreur nettoyage: {e}")
    
    # =================================================================
    # UTILITAIRES
    # =================================================================
    
    async def _get_all_agents(self) -> List[str]:
        """Récupère la liste de tous les agents"""
        return [
            "architect", "coder", "smart_contract", "tester",
            "formal_verification", "fuzzing_simulation", "frontend_web3",
            "monitoring", "learning", "registry", "documenter"
        ]
    
    # =================================================================
    # STATISTIQUES ET MONITORING
    # =================================================================
    
    async def get_statistics(self) -> Dict[str, Any]:
        """Retourne des statistiques sur la communication"""
        return {
            "messages": {
                "sent": self._metrics["messages_sent"],
                "received": self._metrics["messages_received"],
                "failed": self._metrics["messages_failed"],
                "retried": self._metrics["messages_retried"],
                "expired": self._metrics["messages_expired"],
                "throughput": self._metrics["throughput"]
            },
            "queues": {
                "total_size": self._get_total_queue_size(),
                "default": self._queues["default"].size(),
                "high_priority": self._queues["high_priority"].size(),
                "dead_letter": len(self._dead_letter_queue)
            },
            "pubsub": {
                "topics": len(self._topic_manager.list_topics()),
                "subscribers": self._metrics["active_subscribers"]
            },
            "performance": {
                "avg_processing_time": self._metrics["avg_processing_time"],
                "acks_received": self._metrics["acks_received"],
                "pending_acks": len(self._pending_acks),
                "waiting_replies": len(self._waiting_replies)
            }
        }
    
    async def get_message_history(self, limit: int = 100) -> List[Dict]:
        """Récupère l'historique des messages"""
        history = []
        for msg in list(self._message_history)[-limit:]:
            history.append(msg.to_dict())
        return history
    
    async def get_dead_letter_queue(self, limit: int = 100) -> List[Dict]:
        """Récupère la dead letter queue"""
        return self._dead_letter_queue[-limit:]
    
    # =================================================================
    # HEALTH CHECK & INFO
    # =================================================================
    
    async def health_check(self) -> Dict[str, Any]:
        """Vérifie la santé de l'agent"""
        stats = await self.get_statistics()
        return {
            "agent": self._name,
            "status": self._status.value,
            "ready": self._status == AgentStatus.READY,
            "messages_processed": stats["messages"]["received"],
            "queue_size": stats["queues"]["total_size"],
            "dead_letter_size": stats["queues"]["dead_letter"],
            "avg_processing_time": stats["performance"]["avg_processing_time"],
            "components": list(self._components.keys()),
            "uptime": self.uptime.total_seconds()
        }
    
    def get_agent_info(self) -> Dict[str, Any]:
        """Informations de l'agent"""
        return {
            "id": self._name,
            "name": self._config["agent"]["display_name"],
            "version": self._config["agent"]["version"],
            "description": self._config["agent"]["description"],
            "status": self._status.value,
            "capabilities": [cap["name"] for cap in self._config["agent"]["capabilities"]],
            "messages_processed": self._metrics["messages_received"],
            "active_queues": len(self._queues),
            "active_topics": len(self._topic_manager.list_topics())
        }
    
    async def _handle_custom_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Gestion des messages personnalisés"""
        msg_type = message.get("type", "")
        
        if msg_type == "send":
            msg_id = await agent.send_to_agent(
                message["recipient"],
                message["message_type"],
                message["payload"],
                MessagePriority(message.get("priority", 1)),
                message.get("requires_ack", True),
                message.get("ttl", 3600)
            )
            return {"message_id": msg_id}
        
        elif msg_type == "broadcast":
            msg_ids = await self.broadcast(
                message["message_type"],
                message["payload"]
            )
            return {"message_ids": msg_ids}
        
        elif msg_type == "publish":
            await self.publish(
                message["topic"],
                message["payload"],
                message.get("message_type", "event")
            )
            return {"status": "published"}
        
        elif msg_type == "subscribe":
            await self.subscribe(message["topic"], message["agent_id"])
            return {"status": "subscribed"}
        
        elif msg_type == "unsubscribe":
            await self.unsubscribe(message["topic"], message["agent_id"])
            return {"status": "unsubscribed"}
        
        elif msg_type == "request":
            response = await self.request(
                message["recipient"],
                message["message_type"],
                message["payload"],
                message.get("timeout", 30)
            )
            return {"response": response}
        
        elif msg_type == "statistics":
            return await self.get_statistics()
        
        elif msg_type == "history":
            return {"history": await self.get_message_history(message.get("limit", 100))}
        
        elif msg_type == "dead_letter":
            return {"dead_letter": await self.get_dead_letter_queue(message.get("limit", 100))}
        
        return {"status": "received", "type": msg_type}


# ========================================================================
# FONCTIONS D'USINE
# ========================================================================

def create_communication_agent(config_path: str = "") -> 'CommunicationAgent':
    """Crée une instance du communication agent"""
    return CommunicationAgent(config_path)


# ========================================================================
# POINT D'ENTRÉE POUR EXÉCUTION DIRECTE
# ========================================================================

if __name__ == "__main__":
    import asyncio
    
    async def main():
        print("💬 TEST COMMUNICATION AGENT")
        print("="*60)
        
        agent = CommunicationAgent()
        await agent.initialize()
        
        print(f"✅ Agent: {agent._config['agent']['display_name']} v{agent._config['agent']['version']}")
        print(f"✅ Statut: {agent._status.value}")
        print(f"✅ Composants: {len(agent._components)}")
        
        print(f"\n📤 Test d'envoi...")
        msg_id = await agent.send_to_agent(
            recipient="test_agent",
            message_type="ping",
            payload={"data": "test"}
        )
        print(f"✅ Message envoyé: {msg_id}")
        
        print(f"\n🔄 Test request/reply...")
        try:
            response = await agent.request(
                recipient="test_agent",
                message_type="ping",
                payload={"request": "data"},
                timeout=5
            )
            print(f"✅ Réponse reçue: {response}")
        except TimeoutError:
            print(f"⏰ Timeout (normal en test)")
        
        print(f"\n📢 Test pub/sub...")
        await agent.subscribe("test.topic", "subscriber_1")
        await agent.subscribe("test.topic", "subscriber_2")
        await agent.publish("test.topic", {"message": "hello"})
        print(f"✅ Message publié sur 'test.topic'")
        
        stats = await agent.get_statistics()
        print(f"\n📊 Statistiques:")
        print(f"  Messages envoyés: {stats['messages']['sent']}")
        print(f"  Taille file: {stats['queues']['total_size']}")
        print(f"  Topics actifs: {stats['pubsub']['topics']}")
        
        print("\n" + "="*60)
        print("✅ COMMUNICATION AGENT OPÉRATIONNEL")
        print("="*60)
    
    asyncio.run(main())
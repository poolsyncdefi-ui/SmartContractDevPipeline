"""
PubSub Manager SubAgent - Gestionnaire Publish/Subscribe
Version: 2.0.0

Gère les topics et abonnements publish/subscribe avec support de :
- Wildcards multi-niveaux
- Souscriptions durables
- Partitionnement
- Filtrage de messages
"""

import logging
import sys
import asyncio
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, Optional, List, Set, Tuple
from enum import Enum
from dataclasses import dataclass, field
from collections import defaultdict, deque
import fnmatch
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

class SubscriptionType(Enum):
    """Types d'abonnement"""
    VOLATILE = "volatile"    # Non persistant
    DURABLE = "durable"      # Persistant
    SHARED = "shared"        # Partagé entre plusieurs consommateurs


class MessageFilterEngine(Enum):
    """Moteurs de filtrage supportés"""
    JMESPATH = "jmespath"
    JSONATA = "jsonata"
    REGEX = "regex"


@dataclass
class Topic:
    """Topic de publication"""
    name: str
    partitions: int = 1
    created_at: datetime = field(default_factory=datetime.now)
    retention_days: int = 7
    messages_count: int = 0
    last_message_at: Optional[datetime] = None
    subscribers: Set[str] = field(default_factory=set)


@dataclass
class Subscription:
    """Abonnement à un topic"""
    id: str
    topic: str
    subscriber_id: str
    subscription_type: SubscriptionType = SubscriptionType.VOLATILE
    created_at: datetime = field(default_factory=datetime.now)
    filter_expression: Optional[str] = None
    filter_engine: MessageFilterEngine = MessageFilterEngine.JMESPATH
    last_message_at: Optional[datetime] = None
    pending_messages: deque = field(default_factory=lambda: deque(maxlen=1000))
    offset: int = 0


@dataclass
class PubSubMessage:
    """Message publié"""
    id: str
    topic: str
    partition: int
    content: Any
    created_at: datetime = field(default_factory=datetime.now)
    ttl_seconds: int = 3600
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def is_expired(self) -> bool:
        """Vérifie si le message a expiré"""
        expiry = self.created_at + timedelta(seconds=self.ttl_seconds)
        return datetime.now() > expiry


# ============================================================================
# SOUS-AGENT PRINCIPAL
# ============================================================================

class PubSubManagerSubAgent(BaseSubAgent):
    """
    Sous-agent PubSub Manager - Gestionnaire Publish/Subscribe

    Gère un système complet de publication/abonnement avec :
    - Topics hiérarchiques avec wildcards
    - Souscriptions durables et volatiles
    - Partitionnement pour le scaling
    - Filtrage avancé des messages
    - Persistance des messages non délivrés
    """

    def __init__(self, config_path: str = ""):
        """Initialise le pubsub manager"""
        super().__init__(config_path)

        # Métadonnées
        self._subagent_display_name = "📢 PubSub Manager"
        self._subagent_description = "Gestionnaire publish/subscribe"
        self._subagent_version = "2.0.0"
        self._subagent_category = "communication"
        self._subagent_capabilities = [
            "topic.create",
            "topic.delete",
            "topic.list",
            "subscribe",
            "unsubscribe",
            "publish",
            "stats"
        ]

        # État interne
        self._topics: Dict[str, Topic] = {}
        self._subscriptions: Dict[str, Subscription] = {}  # id -> Subscription
        self._subscriber_topics: Dict[str, Set[str]] = defaultdict(set)  # subscriber -> topics
        self._topic_subscriptions: Dict[str, Set[str]] = defaultdict(set)  # topic -> subscription_ids
        self._topic_messages: Dict[str, List[PubSubMessage]] = defaultdict(list)  # topic -> messages
        self._topic_locks: Dict[str, asyncio.Lock] = {}

        # Configuration
        self._default_config = self._agent_config.get('pubsub_manager', {}).get('defaults', {})
        self._wildcard_config = self._agent_config.get('pubsub_manager', {}).get('wildcard_support', {})
        self._partitioning_config = self._agent_config.get('pubsub_manager', {}).get('partitioning', {})

        # Tâche de nettoyage
        self._cleanup_task: Optional[asyncio.Task] = None

        logger.info(f"✅ {self._subagent_display_name} initialisé")

    # ========================================================================
    # IMPLÉMENTATION DES MÉTHODES ABSTRACTES
    # ========================================================================

    async def _initialize_subagent_components(self) -> bool:
        """Initialise les composants spécifiques"""
        logger.info("Initialisation des composants PubSub Manager...")

        self._cleanup_task = asyncio.create_task(self._cleanup_loop())

        logger.info("✅ Composants PubSub Manager initialisés")
        return True

    async def _initialize_components(self) -> bool:
        """Implémentation requise par BaseAgent"""
        return await self._initialize_subagent_components()

    def _get_capability_handlers(self) -> Dict[str, Any]:
        """Retourne les handlers spécifiques"""
        return {
            "topic.create": self._handle_create_topic,
            "topic.delete": self._handle_delete_topic,
            "topic.list": self._handle_list_topics,
            "subscribe": self._handle_subscribe,
            "unsubscribe": self._handle_unsubscribe,
            "publish": self._handle_publish,
            "stats": self._handle_stats,
        }

    # ========================================================================
    # OPÉRATIONS SUR LES TOPICS
    # ========================================================================

    async def _get_topic_lock(self, topic: str) -> asyncio.Lock:
        """Récupère ou crée un verrou pour un topic"""
        if topic not in self._topic_locks:
            self._topic_locks[topic] = asyncio.Lock()
        return self._topic_locks[topic]

    async def _create_topic(self, topic_name: str, partitions: Optional[int] = None,
                           retention_days: Optional[int] = None) -> Dict[str, Any]:
        """Crée un nouveau topic"""
        if topic_name in self._topics:
            return {
                "success": False,
                "error": f"Le topic {topic_name} existe déjà"
            }

        # Vérifier les wildcards (un topic ne peut pas contenir de wildcards)
        if '*' in topic_name or '#' in topic_name:
            return {
                "success": False,
                "error": "Les wildcards ne sont pas autorisés dans les noms de topics"
            }

        topic = Topic(
            name=topic_name,
            partitions=partitions or self._default_config.get('partitions', 1),
            retention_days=retention_days or self._default_config.get('retention_days', 7)
        )

        self._topics[topic_name] = topic
        logger.info(f"✅ Topic créé: {topic_name} ({topic.partitions} partitions)")

        return {
            "success": True,
            "topic": topic_name,
            "partitions": topic.partitions,
            "retention_days": topic.retention_days,
            "created_at": topic.created_at.isoformat()
        }

    async def _delete_topic(self, topic_name: str, force: bool = False) -> Dict[str, Any]:
        """Supprime un topic"""
        if topic_name not in self._topics:
            return {
                "success": False,
                "error": f"Topic {topic_name} non trouvé"
            }

        # Vérifier les abonnements
        subscriptions = self._topic_subscriptions.get(topic_name, set())
        if subscriptions and not force:
            return {
                "success": False,
                "error": f"Topic a {len(subscriptions)} abonnements. Utilisez force=True pour forcer"
            }

        # Supprimer les abonnements
        for sub_id in list(subscriptions):
            await self._unsubscribe(sub_id)

        # Supprimer le topic
        del self._topics[topic_name]
        if topic_name in self._topic_messages:
            del self._topic_messages[topic_name]
        if topic_name in self._topic_locks:
            del self._topic_locks[topic_name]

        logger.info(f"🗑️ Topic supprimé: {topic_name}")

        return {
            "success": True,
            "topic": topic_name
        }

    def _match_topic(self, pattern: str, topic: str) -> bool:
        """Vérifie si un topic correspond à un pattern avec wildcards"""
        if not self._wildcard_config.get('enabled', True):
            return pattern == topic

        single = self._wildcard_config.get('single_level', '*')
        multi = self._wildcard_config.get('multi_level', '#')

        # Convertir le pattern en expression fnmatch
        fn_pattern = pattern.replace(multi, '*').replace(single, '?')
        return fnmatch.fnmatch(topic, fn_pattern)

    async def _find_matching_topics(self, pattern: str) -> List[str]:
        """Trouve tous les topics correspondant à un pattern"""
        return [t for t in self._topics.keys() if self._match_topic(pattern, t)]

    # ========================================================================
    # OPÉRATIONS SUR LES ABONNEMENTS
    # ========================================================================

    async def _subscribe(self, topic_pattern: str, subscriber_id: str,
                         subscription_type: SubscriptionType = SubscriptionType.VOLATILE,
                         filter_expression: Optional[str] = None,
                         filter_engine: str = "jmespath") -> Dict[str, Any]:
        """Abonne un agent à un topic (avec support wildcards)"""
        import uuid

        # Créer l'abonnement
        sub_id = str(uuid.uuid4())
        subscription = Subscription(
            id=sub_id,
            topic=topic_pattern,
            subscriber_id=subscriber_id,
            subscription_type=subscription_type,
            filter_expression=filter_expression,
            filter_engine=MessageFilterEngine(filter_engine) if filter_engine else MessageFilterEngine.JMESPATH
        )

        self._subscriptions[sub_id] = subscription
        self._subscriber_topics[subscriber_id].add(topic_pattern)
        self._topic_subscriptions[topic_pattern].add(sub_id)

        # Si c'est un abonnement durable, charger les messages en attente
        if subscription_type == SubscriptionType.DURABLE:
            await self._load_pending_messages(subscription)

        logger.info(f"✅ {subscriber_id} abonné à {topic_pattern}")

        return {
            "success": True,
            "subscription_id": sub_id,
            "topic": topic_pattern,
            "subscriber": subscriber_id,
            "type": subscription_type.value
        }

    async def _unsubscribe(self, subscription_id: str) -> Dict[str, Any]:
        """Désabonne un agent"""
        if subscription_id not in self._subscriptions:
            return {
                "success": False,
                "error": f"Abonnement {subscription_id} non trouvé"
            }

        sub = self._subscriptions[subscription_id]
        self._subscriber_topics[sub.subscriber_id].discard(sub.topic)
        self._topic_subscriptions[sub.topic].discard(subscription_id)

        del self._subscriptions[subscription_id]

        logger.info(f"✅ {sub.subscriber_id} désabonné de {sub.topic}")

        return {
            "success": True,
            "subscription_id": subscription_id
        }

    async def _load_pending_messages(self, subscription: Subscription):
        """Charge les messages en attente pour un abonnement durable"""
        # Trouver tous les topics correspondant au pattern
        matching_topics = await self._find_matching_topics(subscription.topic)

        for topic in matching_topics:
            messages = self._topic_messages.get(topic, [])
            for msg in messages[messages:]:
                if await self._message_matches_filter(msg, subscription):
                    subscription.pending_messages.append(msg)

    # ========================================================================
    # PUBLICATION
    # ========================================================================

    def _calculate_partition(self, topic: str, partition_key: Optional[str]) -> int:
        """Calcule la partition pour un message"""
        topic_info = self._topics.get(topic)
        if not topic_info or topic_info.partitions <= 1:
            return 0

        if not partition_key:
            import random
            return random.randint(0, topic_info.partitions - 1)

        # Hash du partition key
        hash_val = int(hashlib.md5(partition_key.encode()).hexdigest(), 16)
        return hash_val % topic_info.partitions

    async def _message_matches_filter(self, message: PubSubMessage,
                                      subscription: Subscription) -> bool:
        """Vérifie si un message passe le filtre d'un abonnement"""
        if not subscription.filter_expression:
            return True

        try:
            if subscription.filter_engine == MessageFilterEngine.JMESPATH:
                import jmespath
                result = jmespath.search(subscription.filter_expression, message.content)
                return bool(result)

            elif subscription.filter_engine == MessageFilterEngine.REGEX:
                import re
                return bool(re.search(subscription.filter_expression, json.dumps(message.content)))

            elif subscription.filter_engine == MessageFilterEngine.JSONATA:
                # JSONATA non implémenté par défaut
                return True

        except Exception as e:
            logger.warning(f"Erreur de filtrage: {e}")
            return False

        return True

    async def _publish(self, topic: str, message: Any,
                       partition_key: Optional[str] = None) -> Dict[str, Any]:
        """Publie un message sur un topic"""
        import uuid

        if topic not in self._topics:
            # Création automatique du topic si configuré
            if self._default_config.get('auto_create_topics', False):
                await self._create_topic(topic)
            else:
                return {
                    "success": False,
                    "error": f"Topic {topic} non trouvé"
                }

        # Calculer la partition
        partition = self._calculate_partition(topic, partition_key)

        # Créer le message
        msg = PubSubMessage(
            id=str(uuid.uuid4()),
            topic=topic,
            partition=partition,
            content=message,
            ttl_seconds=self._default_config.get('message_ttl', 3600)
        )

        # Stocker le message
        lock = await self._get_topic_lock(topic)
        async with lock:
            self._topic_messages[topic].append(msg)
            self._topics[topic].messages_count += 1
            self._topics[topic].last_message_at = datetime.now()

        # Distribuer aux abonnés
        delivery_count = await self._deliver_to_subscribers(topic, msg)

        logger.debug(f"📢 Message {msg.id} publié sur {topic} (partition {partition})")

        return {
            "success": True,
            "message_id": msg.id,
            "topic": topic,
            "partition": partition,
            "delivery_count": delivery_count,
            "timestamp": msg.created_at.isoformat()
        }

    async def _deliver_to_subscribers(self, topic: str, message: PubSubMessage) -> int:
        """Distribue un message à tous les abonnés concernés"""
        delivery_count = 0

        # Trouver tous les patterns d'abonnement qui correspondent
        for pattern, sub_ids in list(self._topic_subscriptions.items()):
            if not self._match_topic(pattern, topic):
                continue

            for sub_id in list(sub_ids):
                sub = self._subscriptions.get(sub_id)
                if not sub:
                    continue

                # Vérifier le filtre
                if not await self._message_matches_filter(message, sub):
                    continue

                # Délivrer selon le type d'abonnement
                if sub.subscription_type == SubscriptionType.VOLATILE:
                    # Envoi immédiat (simulé)
                    delivery_count += 1
                    sub.last_message_at = datetime.now()

                elif sub.subscription_type == SubscriptionType.DURABLE:
                    # Mettre en file d'attente
                    sub.pending_messages.append(message)
                    delivery_count += 1

                elif sub.subscription_type == SubscriptionType.SHARED:
                    # Un seul consommateur dans le groupe (simplifié)
                    delivery_count += 1

        return delivery_count

    # ========================================================================
    # TÂCHES DE FOND
    # ========================================================================

    async def _cleanup_loop(self):
        """Nettoie les messages expirés et les abonnements orphelins"""
        logger.info("🔄 Boucle de nettoyage démarrée")

        while self._status.value == "ready":
            try:
                await asyncio.sleep(300)  # Toutes les 5 minutes

                # Nettoyer les messages expirés
                expired_count = 0
                for topic, messages in list(self._topic_messages.items()):
                    self._topic_messages[topic] = [
                        msg for msg in messages
                        if not msg.is_expired
                    ]
                    expired_count += len(messages) - len(self._topic_messages[topic])

                # Nettoyer les abonnements sans souscripteur (simulé)
                # Dans un vrai système, on vérifierait si le subscriber existe toujours

                if expired_count > 0:
                    logger.info(f"🧹 {expired_count} messages expirés supprimés")

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"❌ Erreur dans la boucle de nettoyage: {e}")

    # ========================================================================
    # HANDLERS DE CAPACITÉS
    # ========================================================================

    async def _handle_create_topic(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Crée un nouveau topic"""
        topic = params.get("topic_name")
        if not topic:
            return {"success": False, "error": "topic_name requis"}

        return await self._create_topic(
            topic_name=topic,
            partitions=params.get("partitions"),
            retention_days=params.get("retention_days")
        )

    async def _handle_delete_topic(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Supprime un topic"""
        topic = params.get("topic_name")
        if not topic:
            return {"success": False, "error": "topic_name requis"}

        return await self._delete_topic(
            topic_name=topic,
            force=params.get("force", False)
        )

    async def _handle_list_topics(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Liste les topics"""
        pattern = params.get("pattern", "*")
        include_stats = params.get("include_stats", False)

        if pattern == "*":
            topics = list(self._topics.keys())
        else:
            topics = await self._find_matching_topics(pattern)

        result = []
        for topic in topics:
            info = {
                "name": topic,
                "partitions": self._topics[topic].partitions,
                "messages": self._topics[topic].messages_count,
                "subscribers": len(self._topic_subscriptions.get(topic, []))
            }
            if include_stats:
                info["created_at"] = self._topics[topic].created_at.isoformat()
                info["retention_days"] = self._topics[topic].retention_days
            result.append(info)

        return {
            "success": True,
            "topics": result,
            "count": len(result),
            "pattern": pattern
        }

    async def _handle_subscribe(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Abonne un agent à un topic"""
        topic = params.get("topic")
        subscriber = params.get("subscriber_id") or params.get("subscriber")

        if not topic:
            return {"success": False, "error": "topic requis"}
        if not subscriber:
            return {"success": False, "error": "subscriber_id requis"}

        sub_type_str = params.get("type", "volatile")
        try:
            sub_type = SubscriptionType(sub_type_str)
        except ValueError:
            return {"success": False, "error": f"Type d'abonnement invalide: {sub_type_str}"}

        return await self._subscribe(
            topic_pattern=topic,
            subscriber_id=subscriber,
            subscription_type=sub_type,
            filter_expression=params.get("filter"),
            filter_engine=params.get("filter_engine", "jmespath")
        )

    async def _handle_unsubscribe(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Désabonne un agent"""
        subscription_id = params.get("subscription_id")
        if not subscription_id:
            return {"success": False, "error": "subscription_id requis"}

        return await self._unsubscribe(subscription_id)

    async def _handle_publish(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Publie un message"""
        topic = params.get("topic")
        message = params.get("message")

        if not topic:
            return {"success": False, "error": "topic requis"}
        if message is None:
            return {"success": False, "error": "message requis"}

        return await self._publish(
            topic=topic,
            message=message,
            partition_key=params.get("partition_key")
        )

    async def _handle_stats(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Statistiques des topics"""
        topic = params.get("topic")
        detailed = params.get("detailed", False)

        if topic:
            if topic not in self._topics:
                return {"success": False, "error": f"Topic {topic} non trouvé"}

            t = self._topics[topic]
            stats = {
                "name": t.name,
                "partitions": t.partitions,
                "messages_total": t.messages_count,
                "created_at": t.created_at.isoformat(),
                "last_message": t.last_message_at.isoformat() if t.last_message_at else None,
                "subscribers": len(self._topic_subscriptions.get(topic, []))
            }

            if detailed:
                stats["current_messages"] = len(self._topic_messages.get(topic, []))
                stats["subscriptions"] = list(self._topic_subscriptions.get(topic, []))

            return {
                "success": True,
                "topic": stats
            }

        # Statistiques globales
        total_messages = sum(t.messages_count for t in self._topics.values())
        current_messages = sum(len(msgs) for msgs in self._topic_messages.values())
        total_subscriptions = len(self._subscriptions)

        return {
            "success": True,
            "global": {
                "topics_total": len(self._topics),
                "subscriptions_total": total_subscriptions,
                "messages_total": total_messages,
                "messages_current": current_messages,
                "subscribers_unique": len(self._subscriber_topics)
            },
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

def create_pubsub_manager_agent(config_path: str = "") -> "PubSubManagerSubAgent":
    """Crée une instance du sous-agent pubsub manager"""
    return PubSubManagerSubAgent(config_path)
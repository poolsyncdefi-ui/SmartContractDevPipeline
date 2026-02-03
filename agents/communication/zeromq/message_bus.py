# agents/communication/zeromq/message_bus.py (corrigé)
import zmq
import json
import asyncio
import threading
import logging
from typing import Dict, Any, List, Callable, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum
import uuid

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ZeroMQMessageBus")

class MessagePriority(Enum):
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4

@dataclass
class Message:
    """Message format standardisé"""
    id: str
    sender: str
    receivers: List[str]
    message_type: str
    content: Dict[str, Any]
    timestamp: str
    priority: int = MessagePriority.NORMAL.value
    requires_ack: bool = True
    ttl: int = 300  # 5 minutes
    
    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "sender": self.sender,
            "receivers": self.receivers,
            "message_type": self.message_type,
            "content": self.content,
            "timestamp": self.timestamp,
            "priority": self.priority,
            "requires_ack": self.requires_ack,
            "ttl": self.ttl
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Message':
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            sender=data.get("sender", "unknown"),
            receivers=data.get("receivers", []),
            message_type=data.get("message_type", data.get("type", "unknown")),
            content=data.get("content", {}),
            timestamp=data.get("timestamp", datetime.now().isoformat()),
            priority=data.get("priority", MessagePriority.NORMAL.value),
            requires_ack=data.get("requires_ack", True),
            ttl=data.get("ttl", 300)
        )

class ZeroMQMessageBus:
    """Bus de messages basé sur ZeroMQ - Version corrigée"""
    
    def __init__(self, host: str = "127.0.0.1", pub_port: int = 5555):
        self.host = host
        self.pub_port = pub_port
        self.context = zmq.Context()
        
        # Configuration des sockets
        self.publisher = None
        self.subscribers_socket = None
        self.router_socket = None
        
        # Structures de données
        self.subscribers: Dict[str, List[str]] = {}
        self.message_handlers: Dict[str, List[Callable]] = {}
        self.message_cache: Dict[str, Message] = {}
        
        # État
        self.running = False
        self.receive_thread = None
        self.router_thread = None
        
        # Initialisation
        self._setup_sockets()
    
    def _setup_sockets(self):
        """Configure les sockets ZeroMQ"""
        try:
            # Socket PUB pour la publication
            self.publisher = self.context.socket(zmq.PUB)
            self.publisher.setsockopt(zmq.LINGER, 0)
            self.publisher.bind(f"tcp://{self.host}:{self.pub_port}")
            
            # Socket SUB pour les abonnements (exemple)
            self.subscribers_socket = self.context.socket(zmq.SUB)
            self.subscribers_socket.setsockopt_string(zmq.SUBSCRIBE, "")
            
            # Socket ROUTER pour requêtes/réponses
            self.router_socket = self.context.socket(zmq.ROUTER)
            self.router_socket.bind(f"tcp://{self.host}:{self.pub_port + 2}")
            
            logger.info(f"Sockets ZeroMQ configurées sur {self.host}:{self.pub_port}")
            
        except zmq.ZMQError as e:
            logger.error(f"Erreur configuration ZeroMQ: {e}")
            raise
    
    def start(self):
        """Démarre le bus de messages"""
        if self.running:
            logger.warning("Bus déjà en cours d'exécution")
            return
        
        self.running = True
        
        # Démarrer les threads
        self.receive_thread = threading.Thread(
            target=self._receive_loop, 
            daemon=True,
            name="ZeroMQ-Receiver"
        )
        
        self.router_thread = threading.Thread(
            target=self._router_loop,
            daemon=True,
            name="ZeroMQ-Router"
        )
        
        self.receive_thread.start()
        self.router_thread.start()
        
        logger.info("ZeroMQ Message Bus démarré")
    
    def stop(self):
        """Arrête le bus de messages"""
        self.running = False
        
        if self.receive_thread:
            self.receive_thread.join(timeout=2.0)
        
        if self.router_thread:
            self.router_thread.join(timeout=2.0)
        
        # Fermer les sockets
        if self.publisher:
            self.publisher.close()
        
        if self.subscribers_socket:
            self.subscribers_socket.close()
        
        if self.router_socket:
            self.router_socket.close()
        
        self.context.term()
        logger.info("ZeroMQ Message Bus arrêté")
    
    def _receive_loop(self):
        """Boucle de réception des messages - CORRIGÉE"""
        poller = zmq.Poller()
        poller.register(self.subscribers_socket, zmq.POLLIN)
        
        while self.running:
            try:
                socks = dict(poller.poll(timeout=1000))  # Timeout 1s
                
                if self.subscribers_socket in socks:
                    # Recevoir le message
                    topic = self.subscribers_socket.recv_string()
                    message_data = self.subscribers_socket.recv_json()
                    
                    # Traiter le message
                    message = Message.from_dict(message_data)
                    self._process_message(message)
                    
            except zmq.ZMQError as e:
                if self.running:  # Seulement loguer si on est censé tourner
                    logger.error(f"Erreur ZeroMQ dans receive_loop: {e}")
                break
            except Exception as e:
                logger.error(f"Erreur inattendue dans receive_loop: {e}")
    
    def _router_loop(self):
        """Boucle de gestion des requêtes/réponses - CORRIGÉE"""
        poller = zmq.Poller()
        poller.register(self.router_socket, zmq.POLLIN)
        
        while self.running:
            try:
                socks = dict(poller.poll(timeout=1000))
                
                if self.router_socket in socks:
                    # Recevoir la requête multipart
                    try:
                        identity = self.router_socket.recv()
                        empty = self.router_socket.recv()  # Frame vide
                        request_data = self.router_socket.recv()
                        
                        request = json.loads(request_data.decode('utf-8'))
                        response = self._handle_request(request)
                        
                        # Envoyer la réponse
                        response_data = json.dumps(response).encode('utf-8')
                        self.router_socket.send_multipart([
                            identity, 
                            b"", 
                            response_data
                        ])
                        
                    except (json.JSONDecodeError, UnicodeDecodeError) as e:
                        logger.error(f"Erreur décodage requête: {e}")
                        error_response = {"status": "error", "message": "Invalid request format"}
                        self.router_socket.send_multipart([
                            identity, 
                            b"", 
                            json.dumps(error_response).encode('utf-8')
                        ])
                        
            except zmq.ZMQError as e:
                if self.running:
                    logger.error(f"Erreur ZeroMQ dans router_loop: {e}")
                break
            except Exception as e:
                logger.error(f"Erreur inattendue dans router_loop: {e}")
    
    def _process_message(self, message: Message):
        """Traite un message reçu"""
        try:
            # Vérifier TTL
            message_time = datetime.fromisoformat(message.timestamp)
            current_time = datetime.now()
            time_diff = (current_time - message_time).total_seconds()
            
            if time_diff > message.ttl:
                logger.warning(f"Message {message.id} expiré (TTL: {message.ttl}s)")
                return
            
            logger.info(f"Message reçu: {message.id} de {message.sender} (type: {message.message_type})")
            
            # Appeler les handlers
            handlers = self.message_handlers.get(message.message_type, [])
            for handler in handlers:
                try:
                    handler(message)
                except Exception as e:
                    logger.error(f"Erreur dans le handler {handler.__name__}: {e}")
            
            # Mettre en cache
            self.message_cache[message.id] = message
            
            # Nettoyer le cache si nécessaire
            if len(self.message_cache) > 1000:
                self._cleanup_cache()
                
        except Exception as e:
            logger.error(f"Erreur dans _process_message: {e}")
    
    def _handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Traite une requête RPC"""
        request_type = request.get("type", "").lower()
        
        try:
            if request_type == "subscribe":
                return self._handle_subscribe(request)
            elif request_type == "unsubscribe":
                return self._handle_unsubscribe(request)
            elif request_type == "get_status":
                return self._handle_status(request)
            elif request_type == "search_messages":
                return self._handle_search(request)
            elif request_type == "ping":
                return {"status": "ok", "timestamp": datetime.now().isoformat()}
            else:
                return {
                    "status": "error",
                    "message": f"Type de requête inconnu: {request_type}"
                }
        except Exception as e:
            logger.error(f"Erreur traitement requête {request_type}: {e}")
            return {
                "status": "error",
                "message": f"Erreur interne: {str(e)}"
            }
    
    def _handle_subscribe(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Gère une souscription"""
        agent_id = request.get("agent_id")
        message_types = request.get("message_types", [])
        
        if not agent_id:
            return {"status": "error", "message": "agent_id requis"}
        
        if agent_id not in self.subscribers:
            self.subscribers[agent_id] = []
        
        added_types = []
        for msg_type in message_types:
            if msg_type not in self.subscribers[agent_id]:
                self.subscribers[agent_id].append(msg_type)
                added_types.append(msg_type)
        
        logger.info(f"Agent {agent_id} souscrit à: {added_types}")
        
        return {
            "status": "success",
            "agent_id": agent_id,
            "subscribed_to": self.subscribers[agent_id],
            "added": added_types
        }
    
    def _handle_unsubscribe(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Gère un désabonnement"""
        agent_id = request.get("agent_id")
        message_types = request.get("message_types", [])
        
        if agent_id not in self.subscribers:
            return {"status": "error", "message": f"Agent {agent_id} non trouvé"}
        
        removed_types = []
        for msg_type in message_types:
            if msg_type in self.subscribers[agent_id]:
                self.subscribers[agent_id].remove(msg_type)
                removed_types.append(msg_type)
        
        # Si plus d'abonnements, supprimer l'agent
        if not self.subscribers[agent_id]:
            del self.subscribers[agent_id]
        
        return {
            "status": "success",
            "removed": removed_types,
            "remaining": self.subscribers.get(agent_id, [])
        }
    
    def _handle_status(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Retourne le statut du bus"""
        return {
            "status": "running" if self.running else "stopped",
            "subscribers_count": len(self.subscribers),
            "cached_messages": len(self.message_cache),
            "host": self.host,
            "port": self.pub_port,
            "timestamp": datetime.now().isoformat()
        }
    
    def _handle_search(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Recherche dans les messages en cache"""
        search_term = request.get("search", "").lower()
        sender_filter = request.get("sender")
        message_type_filter = request.get("message_type")
        limit = min(request.get("limit", 50), 100)  # Max 100 résultats
        
        results = []
        for msg_id, message in self.message_cache.items():
            # Appliquer les filtres
            if sender_filter and message.sender != sender_filter:
                continue
            if message_type_filter and message.message_type != message_type_filter:
                continue
            
            # Recherche dans le contenu
            content_str = json.dumps(message.content).lower()
            if search_term in content_str or search_term in message.message_type.lower():
                results.append(message.to_dict())
            
            if len(results) >= limit:
                break
        
        return {
            "status": "success",
            "count": len(results),
            "results": results,
            "search_term": search_term
        }
    
    def _cleanup_cache(self):
        """Nettoie le cache des messages"""
        current_time = datetime.now()
        expired_ids = []
        
        for msg_id, message in self.message_cache.items():
            message_time = datetime.fromisoformat(message.timestamp)
            time_diff = (current_time - message_time).total_seconds()
            
            if time_diff > message.ttl:
                expired_ids.append(msg_id)
        
        # Supprimer les messages expirés
        for msg_id in expired_ids:
            del self.message_cache[msg_id]
        
        # Limiter la taille du cache
        if len(self.message_cache) > 800:
            # Garder les 800 messages les plus récents
            sorted_messages = sorted(
                self.message_cache.items(),
                key=lambda x: x[1].timestamp,
                reverse=True
            )[:800]
            self.message_cache = dict(sorted_messages)
    
    def publish(self, message: Message) -> bool:
        """Publie un message sur le bus"""
        if not self.running or not self.publisher:
            logger.error("Bus non démarré ou socket non disponible")
            return False
        
        try:
            # S'assurer que le message a un ID et timestamp
            if not message.id:
                message.id = str(uuid.uuid4())
            if not message.timestamp:
                message.timestamp = datetime.now().isoformat()
            
            # Convertir en JSON
            message_data = json.dumps(message.to_dict())
            
            # Publier le message
            self.publisher.send_string(message.message_type, zmq.SNDMORE)
            self.publisher.send_json(message.to_dict())
            
            logger.debug(f"Message publié: {message.id} (type: {message.message_type})")
            
            # Mettre en cache
            self.message_cache[message.id] = message
            
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de la publication: {e}")
            return False
    
    def subscribe(self, agent_id: str, message_types: List[str], 
                  handler: Optional[Callable] = None) -> bool:
        """Souscrit un agent à des types de messages"""
        try:
            # Enregistrer dans les subscribers
            if agent_id not in self.subscribers:
                self.subscribers[agent_id] = []
            
            for msg_type in message_types:
                if msg_type not in self.subscribers[agent_id]:
                    self.subscribers[agent_id].append(msg_type)
            
            # Enregistrer le handler
            if handler:
                for msg_type in message_types:
                    if msg_type not in self.message_handlers:
                        self.message_handlers[msg_type] = []
                    if handler not in self.message_handlers[msg_type]:
                        self.message_handlers[msg_type].append(handler)
            
            logger.info(f"Agent {agent_id} souscrit à {len(message_types)} type(s) de messages")
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de la souscription: {e}")
            return False
    
    def add_message_handler(self, message_type: str, handler: Callable):
        """Ajoute un handler pour un type de message spécifique"""
        if message_type not in self.message_handlers:
            self.message_handlers[message_type] = []
        
        if handler not in self.message_handlers[message_type]:
            self.message_handlers[message_type].append(handler)
            logger.debug(f"Handler ajouté pour le type: {message_type}")
    
    def remove_message_handler(self, message_type: str, handler: Callable):
        """Supprime un handler"""
        if message_type in self.message_handlers:
            if handler in self.message_handlers[message_type]:
                self.message_handlers[message_type].remove(handler)
                logger.debug(f"Handler supprimé pour le type: {message_type}")
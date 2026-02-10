"""
Base Agent - Classe de base abstraite pour tous les agents du système SmartContractDevPipeline
Fournit les fonctionnalités communes : configuration, logging, communication, cycle de vie
Version: 1.2.0
Auteur: PoolSync DeFi
Date: 2026-02-08
"""

import os
import sys
import yaml
import json
import logging
import asyncio
import inspect
from pathlib import Path
from abc import ABC, abstractmethod
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable, Union, Type, Tuple, Set
from enum import Enum, auto
from uuid import uuid4
import traceback
import hashlib

# -----------------------------------------------------------------------------
# CONSTANTES ET TYPES DE DONNÉES
# -----------------------------------------------------------------------------

class AgentStatus(Enum):
    """Statuts possibles d'un agent"""
    CREATED = "created"           # Agent créé mais non initialisé
    INITIALIZING = "initializing" # En cours d'initialisation
    READY = "ready"               # Prêt à traiter des messages
    PROCESSING = "processing"     # En cours de traitement
    BUSY = "busy"                 # Occupé (traitement long)
    PAUSED = "paused"             # En pause
    ERROR = "error"               # En erreur
    RECOVERING = "recovering"     # En cours de récupération
    SHUTTING_DOWN = "shutting_down" # En cours d'arrêt
    TERMINATED = "terminated"     # Arrêté

class MessageType(Enum):
    """Types de messages standardisés"""
    COMMAND = "command"           # Commande à exécuter
    QUERY = "query"               # Requête d'information
    RESPONSE = "response"         # Réponse à une requête
    NOTIFICATION = "notification" # Notification
    ERROR = "error"               # Message d'erreur
    HEARTBEAT = "heartbeat"       # Signal de vie
    TASK_RESULT = "task_result"   # Résultat de tâche
    CONFIG_UPDATE = "config_update" # Mise à jour de configuration

class LogLevel(Enum):
    """Niveaux de log"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

@dataclass
class Message:
    """Message envoyé entre agents"""
    sender: str
    recipient: str
    content: Dict[str, Any]
    message_type: Union[str, MessageType]
    timestamp: datetime = field(default_factory=datetime.now)
    message_id: str = field(default_factory=lambda: str(uuid4()))
    correlation_id: Optional[str] = None
    priority: int = 0  # 0 = normal, 1 = haute, 2 = urgente
    ttl: int = 3600  # Time To Live en secondes
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validation après initialisation"""
        if isinstance(self.message_type, MessageType):
            self.message_type = self.message_type.value
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertit le message en dictionnaire"""
        return {
            "message_id": self.message_id,
            "sender": self.sender,
            "recipient": self.recipient,
            "message_type": self.message_type,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "correlation_id": self.correlation_id,
            "priority": self.priority,
            "ttl": self.ttl,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Message':
        """Crée un message depuis un dictionnaire"""
        data = data.copy()
        data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        return cls(**data)
    
    def is_expired(self) -> bool:
        """Vérifie si le message a expiré"""
        expiry_time = self.timestamp + timedelta(seconds=self.ttl)
        return datetime.now() > expiry_time

@dataclass
class AgentCapability:
    """Capacité d'un agent"""
    name: str
    description: str
    version: str = "1.0.0"
    parameters: List[Dict[str, Any]] = field(default_factory=list)
    return_type: Optional[str] = None
    enabled: bool = True

@dataclass  
class AgentMetrics:
    """Métriques de performance d'un agent"""
    messages_received: int = 0
    messages_sent: int = 0
    messages_processed: int = 0
    errors_count: int = 0
    avg_processing_time: float = 0.0
    startup_time: Optional[datetime] = None
    uptime: Optional[timedelta] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertit les métriques en dictionnaire"""
        result = asdict(self)
        if self.startup_time:
            result['startup_time'] = self.startup_time.isoformat()
        if self.uptime:
            result['uptime'] = str(self.uptime)
        return result

# -----------------------------------------------------------------------------
# CLASSE BASE AGENT
# -----------------------------------------------------------------------------

class BaseAgent(ABC):
    """
    Classe de base abstraite pour tous les agents.
    Implémente les fonctionnalités communes : configuration, logging, communication,
    cycle de vie, métriques et gestion des erreurs.
    """
    
    # Configuration par défaut
    DEFAULT_CONFIG = {
        'agent': {
            'name': 'base_agent',
            'display_name': 'Agent de Base',
            'description': 'Classe de base abstraite pour tous les agents',
            'version': '1.0.0',
            'log_level': 'INFO',
            'max_retries': 3,
            'timeout_seconds': 300,
            'health_check_interval': 30
        }
    }
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialise l'agent avec sa configuration.
        
        Args:
            config_path: Chemin vers le fichier de configuration YAML
        """
        # Identité de l'agent
        self._name = "base_agent"
        self._display_name = "Agent de Base"
        self._description = "Classe de base abstraite pour tous les agents"
        self._version = "1.0.0"
        
        # Statut et cycle de vie
        self._status = AgentStatus.CREATED
        self._start_time = datetime.now()
        self._last_heartbeat = datetime.now()
        self._error_count = 0
        self._message_queue: asyncio.Queue = asyncio.Queue(maxsize=1000)
        
        # Configuration et état
        self._config_path = config_path
        self._agent_config: Dict[str, Any] = {}
        self._capabilities: List[AgentCapability] = []
        self._dependencies: List[str] = []
        self._metrics = AgentMetrics()
        self._metrics.startup_time = self._start_time
        
        # Callbacks et gestionnaires
        self._message_handlers: Dict[str, Callable] = {}
        self._task_registry: Dict[str, asyncio.Task] = {}
        self._error_handlers: List[Callable] = []
        
        # Initialiser le système
        self._setup_logging()
        self._logger = logging.getLogger(f"agent.{self.__class__.__name__}")
        self._initialize_default_handlers()
        
        # Charger la configuration si fournie
        if config_path:
            self._agent_config = self._load_config(config_path)
            
        # Mettre à jour les métriques
        self._update_uptime()
        
        self._logger.info(f"Agent {self._name} créé (config: {config_path})")
    
    # -------------------------------------------------------------------------
    # PROPRIÉTÉS
    # -------------------------------------------------------------------------
    
    @property
    def name(self) -> str:
        """Nom unique de l'agent"""
        return self._name
    
    @property
    def display_name(self) -> str:
        """Nom d'affichage de l'agent"""
        return self._display_name
    
    @property
    def description(self) -> str:
        """Description de l'agent"""
        return self._description
    
    @property
    def version(self) -> str:
        """Version de l'agent"""
        return self._version
    
    @property
    def status(self) -> AgentStatus:
        """Statut actuel de l'agent"""
        return self._status
    
    @property
    def config(self) -> Dict[str, Any]:
        """Configuration de l'agent"""
        return self._agent_config.copy()
    
    @property
    def capabilities(self) -> List[AgentCapability]:
        """Capacités de l'agent"""
        return self._capabilities.copy()
    
    @property
    def metrics(self) -> AgentMetrics:
        """Métriques de l'agent"""
        self._update_uptime()
        return self._metrics
    
    @property
    def is_ready(self) -> bool:
        """Vérifie si l'agent est prêt"""
        return self._status == AgentStatus.READY
    
    @property
    def is_error(self) -> bool:
        """Vérifie si l'agent est en erreur"""
        return self._status == AgentStatus.ERROR
    
    @property
    def uptime(self) -> timedelta:
        """Temps de fonctionnement depuis le démarrage"""
        return datetime.now() - self._start_time
    
    # -------------------------------------------------------------------------
    # CONFIGURATION ET INITIALISATION
    # -------------------------------------------------------------------------
    
    def _setup_logging(self):
        """Configure le logging pour l'agent"""
        # Créer le répertoire de logs si nécessaire
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        # Configurer le format
        log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        date_format = '%Y-%m-%d %H:%M:%S'
        
        # Configurer le handler console avec couleur
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(logging.Formatter(log_format, date_format))
        
        # Configurer le handler fichier
        file_handler = logging.FileHandler(
            f"logs/{self.__class__.__name__.lower()}.log",
            mode='a',
            encoding='utf-8'
        )
        file_handler.setFormatter(logging.Formatter(log_format, date_format))
        
        # Configurer le logger
        self._logger = logging.getLogger(f"agent.{self.__class__.__name__}")
        self._logger.setLevel(logging.INFO)
        self._logger.addHandler(console_handler)
        self._logger.addHandler(file_handler)
        self._logger.propagate = False
    
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """
        Charge la configuration depuis un fichier YAML.
        
        Args:
            config_path: Chemin vers le fichier YAML
            
        Returns:
            Dictionnaire de configuration
        """
        try:
            config_path_obj = Path(config_path)
            if not config_path_obj.exists():
                self._logger.warning(f"Fichier de configuration non trouvé: {config_path}")
                return self.DEFAULT_CONFIG
            
            with open(config_path_obj, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            if not config:
                self._logger.warning(f"Fichier de configuration vide: {config_path}")
                return self.DEFAULT_CONFIG
            
            # Fusionner avec la configuration par défaut
            merged_config = self._merge_configs(self.DEFAULT_CONFIG, config)
            
            # Extraire les informations de base
            agent_info = merged_config.get('agent', {})
            self._name = agent_info.get('name', self._name)
            self._display_name = agent_info.get('display_name', self._display_name)
            self._description = agent_info.get('description', self._description)
            self._version = agent_info.get('version', self._version)
            
            # Configurer le niveau de log
            log_level = agent_info.get('log_level', 'INFO')
            self._logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
            
            # Extraire les capacités
            capabilities_info = agent_info.get('capabilities', [])
            self._capabilities = [
                AgentCapability(
                    name=cap.get('name', ''),
                    description=cap.get('description', ''),
                    version=cap.get('version', '1.0.0'),
                    parameters=cap.get('parameters', []),
                    return_type=cap.get('return_type')
                )
                for cap in capabilities_info if isinstance(cap, dict)
            ]
            
            # Extraire les dépendances
            self._dependencies = agent_info.get('dependencies', [])
            
            self._logger.info(f"Configuration chargée: {self._name} v{self._version}")
            self._logger.debug(f"Capacités: {[c.name for c in self._capabilities]}")
            
            return merged_config
            
        except yaml.YAMLError as e:
            self._logger.error(f"Erreur YAML dans la configuration {config_path}: {e}")
            return self.DEFAULT_CONFIG
        except Exception as e:
            self._logger.error(f"Erreur lors du chargement de la configuration {config_path}: {e}")
            return self.DEFAULT_CONFIG
    
    def _merge_configs(self, default: Dict, custom: Dict) -> Dict:
        """Fusionne deux configurations de manière récursive"""
        merged = default.copy()
        
        for key, value in custom.items():
            if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
                merged[key] = self._merge_configs(merged[key], value)
            else:
                merged[key] = value
        
        return merged
    
    def _initialize_default_handlers(self):
        """Initialise les gestionnaires de messages par défaut"""
        self.register_message_handler("ping", self._handle_ping)
        self.register_message_handler("status", self._handle_status_request)
        self.register_message_handler("capabilities", self._handle_capabilities_request)
        self.register_message_handler("health_check", self._handle_health_check)
        self.register_message_handler("shutdown", self._handle_shutdown_request)
    
    async def initialize(self) -> bool:
        """
        Initialise l'agent (méthode asynchrone).
        
        Returns:
            True si l'initialisation a réussi
        """
        try:
            self._set_status(AgentStatus.INITIALIZING)
            self._logger.info(f"Initialisation de l'agent {self._name}...")
            
            # Valider la configuration
            if not self._validate_config():
                self._logger.error("Configuration invalide")
                self._set_status(AgentStatus.ERROR)
                return False
            
            # Vérifier les dépendances
            if not await self._check_dependencies():
                self._logger.error("Dépendances non satisfaites")
                self._set_status(AgentStatus.ERROR)
                return False
            
            # Initialiser les composants spécifiques
            success = await self._initialize_components()
            
            if success:
                self._set_status(AgentStatus.READY)
                self._start_background_tasks()
                self._metrics.startup_time = datetime.now()
                self._logger.info(f"Agent {self._name} initialisé avec succès")
                return True
            else:
                self._set_status(AgentStatus.ERROR)
                self._logger.error(f"Échec de l'initialisation de l'agent {self._name}")
                return False
                
        except Exception as e:
            self._logger.error(f"Erreur lors de l'initialisation: {e}")
            self._logger.error(traceback.format_exc())
            self._set_status(AgentStatus.ERROR)
            return False
    
    def _validate_config(self) -> bool:
        """
        Valide la configuration de l'agent.
        
        Returns:
            True si la configuration est valide
        """
        try:
            # Vérifications de base
            if not self._name or self._name == "base_agent":
                self._logger.warning("Nom d'agent non spécifié ou par défaut")
            
            if not self._capabilities:
                self._logger.warning("Aucune capacité définie pour l'agent")
            
            # Vérifier les champs obligatoires dans la configuration
            agent_config = self._agent_config.get('agent', {})
            required_fields = ['name', 'version']
            
            for field in required_fields:
                if field not in agent_config:
                    self._logger.warning(f"Champ obligatoire manquant: {field}")
            
            return True
            
        except Exception as e:
            self._logger.error(f"Erreur lors de la validation de la configuration: {e}")
            return False
    
    async def _check_dependencies(self) -> bool:
        """
        Vérifie si les dépendances de l'agent sont satisfaites.
        
        Returns:
            True si toutes les dépendances sont satisfaites
        """
        if not self._dependencies:
            return True
        
        self._logger.info(f"Vérification des dépendances: {self._dependencies}")
        
        # Dans une implémentation réelle, vérifierait avec le registre d'agents
        # Ici, on simule que toutes les dépendances sont satisfaites
        for dep in self._dependencies:
            self._logger.debug(f"Dépendance {dep} - OK (simulé)")
        
        return True
    
    @abstractmethod
    async def _initialize_components(self) -> bool:
        """
        Initialise les composants spécifiques de l'agent.
        À implémenter par les classes dérivées.
        
        Returns:
            True si l'initialisation a réussi
        """
        pass
    
    # -------------------------------------------------------------------------
    # GESTION DES MESSAGES
    # -------------------------------------------------------------------------
    
    def register_message_handler(self, message_type: str, handler: Callable):
        """
        Enregistre un gestionnaire pour un type de message spécifique.
        
        Args:
            message_type: Type de message
            handler: Fonction de gestion
        """
        self._message_handlers[message_type] = handler
        self._logger.debug(f"Gestionnaire enregistré pour le type: {message_type}")
    
    async def send_message(self, message: Message) -> bool:
        """
        Envoie un message à un autre agent.
        
        Args:
            message: Message à envoyer
            
        Returns:
            True si le message a été envoyé avec succès
        """
        try:
            # Vérifier si le message a expiré
            if message.is_expired():
                self._logger.warning(f"Message {message.message_id} expiré, non envoyé")
                return False
            
            # Dans une implémentation réelle, envoyer via le bus de messages
            # Ici, on simule l'envoi
            self._metrics.messages_sent += 1
            self._logger.debug(f"Message envoyé: {message.message_id} à {message.recipient}")
            
            # Simuler la réception par l'agent destinataire
            if message.recipient == self._name or message.recipient == "*":
                await self.receive_message(message)
            
            return True
            
        except Exception as e:
            self._logger.error(f"Erreur lors de l'envoi du message {message.message_id}: {e}")
            self._metrics.errors_count += 1
            return False
    
    async def receive_message(self, message: Message) -> Optional[Message]:
        """
        Reçoit et traite un message.
        
        Args:
            message: Message à traiter
            
        Returns:
            Réponse éventuelle
        """
        try:
            self._metrics.messages_received += 1
            
            # Vérifier si le message est pour cet agent
            if message.recipient != self._name and message.recipient != "*":
                self._logger.debug(f"Message {message.message_id} ignoré (destinataire: {message.recipient})")
                return None
            
            # Vérifier l'expiration
            if message.is_expired():
                self._logger.warning(f"Message {message.message_id} expiré, ignoré")
                return None
            
            # Mettre le message dans la file d'attente
            await self._message_queue.put(message)
            self._logger.debug(f"Message {message.message_id} mis en file d'attente")
            
            # Traiter le message
            response = await self._process_message_from_queue()
            
            return response
            
        except Exception as e:
            self._logger.error(f"Erreur lors de la réception du message {message.message_id}: {e}")
            self._metrics.errors_count += 1
            return None
    
    async def _process_message_from_queue(self) -> Optional[Message]:
        """Traite le prochain message de la file d'attente"""
        try:
            # Récupérer le message
            message = await self._message_queue.get()
            
            # Traiter le message
            start_time = datetime.now()
            self._set_status(AgentStatus.PROCESSING)
            
            response = await self._handle_message(message)
            
            processing_time = (datetime.now() - start_time).total_seconds()
            self._metrics.avg_processing_time = (
                self._metrics.avg_processing_time * self._metrics.messages_processed + processing_time
            ) / (self._metrics.messages_processed + 1)
            self._metrics.messages_processed += 1
            
            self._set_status(AgentStatus.READY)
            self._message_queue.task_done()
            
            return response
            
        except Exception as e:
            self._logger.error(f"Erreur lors du traitement du message: {e}")
            self._logger.error(traceback.format_exc())
            self._metrics.errors_count += 1
            self._set_status(AgentStatus.ERROR)
            return None
    
    async def _handle_message(self, message: Message) -> Optional[Message]:
        """
        Gère un message spécifique.
        
        Args:
            message: Message à traiter
            
        Returns:
            Réponse éventuelle
        """
        try:
            message_type = message.message_type
            
            # Chercher un gestionnaire spécifique
            handler = self._message_handlers.get(message_type)
            
            if handler:
                # Appeler le gestionnaire
                if inspect.iscoroutinefunction(handler):
                    result = await handler(message)
                else:
                    result = handler(message)
                
                # Créer une réponse si nécessaire
                if result is not None and not isinstance(result, Message):
                    response = Message(
                        sender=self._name,
                        recipient=message.sender,
                        content={"result": result} if not isinstance(result, dict) else result,
                        message_type=MessageType.RESPONSE.value,
                        correlation_id=message.message_id
                    )
                    return response
                elif isinstance(result, Message):
                    return result
            else:
                # Aucun gestionnaire trouvé, utiliser la méthode abstraite
                return await self._handle_custom_message(message)
            
            return None
            
        except Exception as e:
            self._logger.error(f"Erreur dans le gestionnaire de message {message.message_type}: {e}")
            
            # Créer un message d'erreur
            error_response = Message(
                sender=self._name,
                recipient=message.sender,
                content={
                    "error": str(e),
                    "traceback": traceback.format_exc()
                },
                message_type=MessageType.ERROR.value,
                correlation_id=message.message_id
            )
            return error_response
    
    @abstractmethod
    async def _handle_custom_message(self, message: Message) -> Optional[Message]:
        """
        Gère les messages personnalisés.
        À implémenter par les classes dérivées.
        
        Args:
            message: Message à traiter
            
        Returns:
            Réponse éventuelle
        """
        pass
    
    # -------------------------------------------------------------------------
    # GESTIONNAIRES DE MESSAGES PAR DÉFAUT
    # -------------------------------------------------------------------------
    
    async def _handle_ping(self, message: Message) -> Dict[str, Any]:
        """Gère un message ping"""
        return {
            "pong": True,
            "timestamp": datetime.now().isoformat(),
            "agent": self._name,
            "status": self._status.value
        }
    
    async def _handle_status_request(self, message: Message) -> Dict[str, Any]:
        """Gère une requête de statut"""
        self._update_uptime()
        return {
            "agent": self.get_status_report(),
            "metrics": self._metrics.to_dict(),
            "timestamp": datetime.now().isoformat()
        }
    
    async def _handle_capabilities_request(self, message: Message) -> Dict[str, Any]:
        """Gère une requête de capacités"""
        return {
            "capabilities": [
                {
                    "name": cap.name,
                    "description": cap.description,
                    "version": cap.version,
                    "enabled": cap.enabled
                }
                for cap in self._capabilities
            ]
        }
    
    async def _handle_health_check(self, message: Message) -> Dict[str, Any]:
        """Gère une vérification de santé"""
        health_status = {
            "status": self._status.value,
            "healthy": self._status == AgentStatus.READY,
            "uptime": str(self.uptime),
            "last_heartbeat": self._last_heartbeat.isoformat(),
            "message_queue_size": self._message_queue.qsize(),
            "error_count": self._error_count,
            "timestamp": datetime.now().isoformat()
        }
        
        # Vérifications supplémentaires
        checks = []
        
        # Check 1: Statut
        checks.append({
            "name": "agent_status",
            "healthy": self._status == AgentStatus.READY,
            "message": f"Statut: {self._status.value}"
        })
        
        # Check 2: File d'attente
        queue_healthy = self._message_queue.qsize() < 500
        checks.append({
            "name": "message_queue",
            "healthy": queue_healthy,
            "message": f"Taille file: {self._message_queue.qsize()}"
        })
        
        # Check 3: Dernier heartbeat
        heartbeat_healthy = (datetime.now() - self._last_heartbeat).total_seconds() < 60
        checks.append({
            "name": "heartbeat",
            "healthy": heartbeat_healthy,
            "message": f"Dernier heartbeat: {self._last_heartbeat.isoformat()}"
        })
        
        health_status["checks"] = checks
        health_status["all_healthy"] = all(check["healthy"] for check in checks)
        
        return health_status
    
    async def _handle_shutdown_request(self, message: Message) -> Dict[str, Any]:
        """Gère une requête d'arrêt"""
        self._logger.info(f"Reçu requête d'arrêt de {message.sender}")
        
        # Planifier l'arrêt
        asyncio.create_task(self.shutdown())
        
        return {
            "acknowledged": True,
            "message": f"Agent {self._name} en cours d'arrêt",
            "timestamp": datetime.now().isoformat()
        }
    
    # -------------------------------------------------------------------------
    # TÂCHES EN ARRIÈRE-PLAN
    # -------------------------------------------------------------------------
    
    def _start_background_tasks(self):
        """Démarre les tâches en arrière-plan"""
        # Tâche de heartbeat
        self._task_registry["heartbeat"] = asyncio.create_task(self._heartbeat_task())
        
        # Tâche de nettoyage
        self._task_registry["cleanup"] = asyncio.create_task(self._cleanup_task())
        
        # Tâche de traitement des messages
        self._task_registry["message_processor"] = asyncio.create_task(self._message_processor_task())
    
    async def _heartbeat_task(self):
        """Tâche de heartbeat périodique"""
        while self._status != AgentStatus.TERMINATED:
            try:
                await asyncio.sleep(10)  # Toutes les 10 secondes
                
                if self._status == AgentStatus.READY:
                    self._last_heartbeat = datetime.now()
                    self._logger.debug(f"Heartbeat - {self._name}")
                    
                    # Envoyer un heartbeat aux agents intéressés
                    heartbeat_msg = Message(
                        sender=self._name,
                        recipient="monitoring",
                        content={"agent": self._name, "status": self._status.value},
                        message_type=MessageType.HEARTBEAT.value
                    )
                    await self.send_message(heartbeat_msg)
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                self._logger.error(f"Erreur dans la tâche heartbeat: {e}")
                await asyncio.sleep(30)  # Attendre plus longtemps en cas d'erreur
    
    async def _cleanup_task(self):
        """Tâche de nettoyage périodique"""
        while self._status != AgentStatus.TERMINATED:
            try:
                await asyncio.sleep(60)  # Toutes les minutes
                
                # Nettoyer les tâches terminées
                completed_tasks = [
                    task_id for task_id, task in self._task_registry.items()
                    if task.done()
                ]
                
                for task_id in completed_tasks:
                    if task_id != "heartbeat" and task_id != "cleanup" and task_id != "message_processor":
                        try:
                            self._task_registry[task_id].result()  # Récupérer le résultat
                        except Exception:
                            pass  # Ignorer les erreurs
                        del self._task_registry[task_id]
                
                self._logger.debug(f"Nettoyage effectué - {len(completed_tasks)} tâches terminées")
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self._logger.error(f"Erreur dans la tâche de nettoyage: {e}")
    
    async def _message_processor_task(self):
        """Tâche de traitement continu des messages"""
        while self._status != AgentStatus.TERMINATED:
            try:
                # Attendre un message si la file n'est pas vide
                if not self._message_queue.empty():
                    await self._process_message_from_queue()
                else:
                    await asyncio.sleep(0.1)  # Petite pause pour éviter la boucle CPU
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                self._logger.error(f"Erreur dans le processeur de messages: {e}")
                await asyncio.sleep(1)
    
    # -------------------------------------------------------------------------
    # GESTION DU CYCLE DE VIE
    # -------------------------------------------------------------------------
    
    async def shutdown(self):
        """
        Arrête l'agent proprement.
        """
        try:
            self._set_status(AgentStatus.SHUTTING_DOWN)
            self._logger.info(f"Arrêt de l'agent {self._name}...")
            
            # Annuler toutes les tâches en arrière-plan
            for task_id, task in self._task_registry.items():
                if not task.done():
                    task.cancel()
                    try:
                        await task
                    except asyncio.CancelledError:
                        pass
            
            # Vider la file d'attente
            while not self._message_queue.empty():
                try:
                    self._message_queue.get_nowait()
                    self._message_queue.task_done()
                except asyncio.QueueEmpty:
                    break
            
            # Appeler le nettoyage spécifique
            await self._cleanup()
            
            # Mettre à jour le statut
            self._set_status(AgentStatus.TERMINATED)
            self._update_uptime()
            
            runtime = datetime.now() - self._start_time
            self._logger.info(f"Agent {self._name} arrêté (runtime: {runtime})")
            
        except Exception as e:
            self._logger.error(f"Erreur lors de l'arrêt: {e}")
            self._logger.error(traceback.format_exc())
    
    async def _cleanup(self):
        """
        Nettoie les ressources de l'agent.
        À implémenter par les classes dérivées si nécessaire.
        """
        # Méthode par défaut, peut être surchargée
        self._logger.debug(f"Nettoyage des ressources de {self._name}")
    
    def _set_status(self, new_status: AgentStatus):
        """Change le statut de l'agent de manière sécurisée"""
        old_status = self._status
        self._status = new_status
        
        if old_status != new_status:
            self._logger.info(f"Changement de statut: {old_status.value} -> {new_status.value}")
            
            # Notifier les observateurs
            notification = Message(
                sender=self._name,
                recipient="monitoring",
                content={
                    "agent": self._name,
                    "old_status": old_status.value,
                    "new_status": new_status.value,
                    "timestamp": datetime.now().isoformat()
                },
                message_type=MessageType.NOTIFICATION.value
            )
            
            # Envoyer la notification de manière asynchrone
            asyncio.create_task(self.send_message(notification))
    
    # -------------------------------------------------------------------------
    # MÉTHODES UTILITAIRES
    # -------------------------------------------------------------------------
    
    def _update_uptime(self):
        """Met à jour le temps de fonctionnement dans les métriques"""
        if self._metrics.startup_time:
            self._metrics.uptime = datetime.now() - self._metrics.startup_time
    
    def get_status_report(self) -> Dict[str, Any]:
        """
        Génère un rapport de statut de l'agent.
        
        Returns:
            Dictionnaire avec les informations de statut
        """
        self._update_uptime()
        
        return {
            "name": self._name,
            "display_name": self._display_name,
            "description": self._description,
            "status": self._status.value,
            "version": self._version,
            "start_time": self._start_time.isoformat(),
            "uptime": str(self.uptime),
            "capabilities": [
                {
                    "name": cap.name,
                    "description": cap.description,
                    "version": cap.version,
                    "enabled": cap.enabled
                }
                for cap in self._capabilities
            ],
            "dependencies": self._dependencies,
            "config_loaded": bool(self._agent_config),
            "message_queue_size": self._message_queue.qsize(),
            "active_tasks": len(self._task_registry)
        }
    
    def add_capability(self, capability: AgentCapability):
        """
        Ajoute une capacité à l'agent.
        
        Args:
            capability: Capacité à ajouter
        """
        self._capabilities.append(capability)
        self._logger.info(f"Capacité ajoutée: {capability.name}")
    
    def remove_capability(self, capability_name: str) -> bool:
        """
        Supprime une capacité de l'agent.
        
        Args:
            capability_name: Nom de la capacité à supprimer
            
        Returns:
            True si la capacité a été supprimée
        """
        for i, cap in enumerate(self._capabilities):
            if cap.name == capability_name:
                self._capabilities.pop(i)
                self._logger.info(f"Capacité supprimée: {capability_name}")
                return True
        
        self._logger.warning(f"Capacité non trouvée: {capability_name}")
        return False
    
    def has_capability(self, capability_name: str) -> bool:
        """
        Vérifie si l'agent a une capacité spécifique.
        
        Args:
            capability_name: Nom de la capacité
            
        Returns:
            True si l'agent a la capacité
        """
        return any(cap.name == capability_name for cap in self._capabilities)
    
    def execute_capability(self, capability_name: str, **kwargs) -> Any:
        """
        Exécute une capacité de l'agent.
        
        Args:
            capability_name: Nom de la capacité
            **kwargs: Arguments pour la capacité
            
        Returns:
            Résultat de l'exécution
        """
        # Cette méthode devrait être implémentée par les sous-classes
        # pour exécuter réellement les capacités
        self._logger.warning(f"Exécution de capacité non implémentée: {capability_name}")
        return None
    
    # -------------------------------------------------------------------------
    # GESTION DES ERREURS
    # -------------------------------------------------------------------------
    
    def register_error_handler(self, handler: Callable):
        """
        Enregistre un gestionnaire d'erreurs.
        
        Args:
            handler: Fonction de gestion d'erreurs
        """
        self._error_handlers.append(handler)
        self._logger.debug(f"Gestionnaire d'erreurs enregistré")
    
    async def handle_error(self, error: Exception, context: Dict[str, Any] = None):
        """
        Gère une erreur.
        
        Args:
            error: Exception à gérer
            context: Contexte supplémentaire
        """
        self._error_count += 1
        self._metrics.errors_count += 1
        
        # Appeler les gestionnaires d'erreurs
        for handler in self._error_handlers:
            try:
                if inspect.iscoroutinefunction(handler):
                    await handler(error, context)
                else:
                    handler(error, context)
            except Exception as e:
                self._logger.error(f"Erreur dans le gestionnaire d'erreurs: {e}")
        
        # Journaliser l'erreur
        self._logger.error(f"Erreur dans {self._name}: {error}")
        if context:
            self._logger.error(f"Contexte: {context}")
        
        # Changer le statut si nécessaire
        if self._error_count > 10:  # Trop d'erreurs
            self._set_status(AgentStatus.ERROR)
    
    # -------------------------------------------------------------------------
    # REPRÉSENTATION
    # -------------------------------------------------------------------------
    
    def __str__(self) -> str:
        """Représentation textuelle de l'agent"""
        return f"{self.__class__.__name__}(name={self._name}, status={self._status.value}, version={self._version})"
    
    def __repr__(self) -> str:
        """Représentation formelle de l'agent"""
        return f"{self.__class__.__name__}(name={self._name}, config_path={self._config_path})"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertit l'agent en dictionnaire"""
        return self.get_status_report()
    
    @classmethod
    def get_agent_info(cls) -> Dict[str, Any]:
        """Retourne des informations sur la classe d'agent"""
        return {
            "class_name": cls.__name__,
            "module": cls.__module__,
            "abstract": inspect.isabstract(cls),
            "methods": [
                name for name, method in inspect.getmembers(cls, predicate=inspect.isfunction)
                if not name.startswith('_')
            ],
            "docstring": cls.__doc__
        }

# -----------------------------------------------------------------------------
# FONCTIONS UTILITAIRES
# -----------------------------------------------------------------------------

def create_message(
    sender: str,
    recipient: str,
    content: Dict[str, Any],
    message_type: Union[str, MessageType] = MessageType.COMMAND.value,
    **kwargs
) -> Message:
    """
    Crée un message avec des paramètres par défaut.
    
    Args:
        sender: Expéditeur du message
        recipient: Destinataire du message
        content: Contenu du message
        message_type: Type de message
        **kwargs: Arguments supplémentaires pour Message
        
    Returns:
        Message créé
    """
    return Message(
        sender=sender,
        recipient=recipient,
        content=content,
        message_type=message_type,
        **kwargs
    )

def validate_agent_config(config: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Valide une configuration d'agent.
    
    Args:
        config: Configuration à valider
        
    Returns:
        Tuple (valide, liste_d_erreurs)
    """
    errors = []
    
    # Vérifier la structure de base
    if 'agent' not in config:
        errors.append("Section 'agent' manquante")
        return False, errors
    
    agent_config = config['agent']
    
    # Vérifier les champs obligatoires
    required_fields = ['name', 'version']
    for field in required_fields:
        if field not in agent_config:
            errors.append(f"Champ obligatoire manquant: agent.{field}")
    
    # Vérifier les types
    if 'name' in agent_config and not isinstance(agent_config['name'], str):
        errors.append("agent.name doit être une chaîne de caractères")
    
    if 'version' in agent_config and not isinstance(agent_config['version'], str):
        errors.append("agent.version doit être une chaîne de caractères")
    
    if 'capabilities' in agent_config and not isinstance(agent_config['capabilities'], list):
        errors.append("agent.capabilities doit être une liste")
    
    return len(errors) == 0, errors

# -----------------------------------------------------------------------------
# POINT D'ENTRÉE POUR LES TESTS
# -----------------------------------------------------------------------------

async def test_base_agent():
    """Teste la classe BaseAgent"""
    print("🧪 Test de BaseAgent...")
    
    # Créer une sous-classe concrète pour le test
    class TestAgent(BaseAgent):
        async def _initialize_components(self) -> bool:
            print("  Initialisation des composants de TestAgent")
            return True
        
        async def _handle_custom_message(self, message: Message) -> Optional[Message]:
            print(f"  Traitement du message personnalisé: {message.message_type}")
            return None
    
    # Créer et initialiser l'agent
    agent = TestAgent()
    
    print(f"  Création: {agent}")
    print(f"  Nom: {agent.name}")
    print(f"  Statut: {agent.status}")
    
    # Initialiser
    success = await agent.initialize()
    print(f"  Initialisation: {'✅' if success else '❌'}")
    print(f"  Statut après init: {agent.status}")
    
    # Envoyer un message ping
    ping_msg = create_message(
        sender="test_runner",
        recipient=agent.name,
        content={},
        message_type="ping"
    )
    
    response = await agent.receive_message(ping_msg)
    print(f"  Réponse au ping: {response.content if response else 'Aucune'}")
    
    # Obtenir le statut
    status_msg = create_message(
        sender="test_runner",
        recipient=agent.name,
        content={},
        message_type="status"
    )
    
    status_response = await agent.receive_message(status_msg)
    print(f"  Rapport de statut: {status_response.content['agent']['name'] if status_response else 'Erreur'}")
    
    # Arrêter l'agent
    await agent.shutdown()
    print(f"  Statut final: {agent.status}")
    
    print("✅ Test BaseAgent terminé")

if __name__ == "__main__":
    # Exécuter le test si le fichier est exécuté directement
    asyncio.run(test_base_agent())
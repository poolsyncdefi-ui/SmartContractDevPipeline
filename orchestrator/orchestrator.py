#!/usr/bin/env python3
"""
Orchestrator Principal - SmartContractDevPipeline
Version: 2.2.0
Responsable: Gestion et coordination de tous les agents
"""

import os
import sys
import yaml
import json
import logging
import asyncio
import importlib
import importlib.util
import traceback
import inspect
import hashlib
from datetime import datetime
from typing import Dict, List, Optional, Any, Type, Union, Callable
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import threading
import queue
import time

# ============================================================================
# CONFIGURATION ET CONSTANTES
# ============================================================================

@dataclass
class OrchestratorConfig:
    """Configuration de l'orchestrator"""
    config_path: str
    agents_dir: str = "agents"
    log_level: str = "INFO"
    max_concurrent_tasks: int = 5
    auto_discover: bool = True
    health_check_interval: int = 30
    task_timeout: int = 300
    enable_api: bool = True
    api_host: str = "127.0.0.1"
    api_port: int = 8000
    
    @classmethod
    def from_yaml(cls, config_path: str) -> 'OrchestratorConfig':
        """Charge la configuration depuis un fichier YAML"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = yaml.safe_load(f)
            
            # Extraire la section orchestrator
            orch_config = config_data.get('orchestrator', {})
            
            return cls(
                config_path=config_path,
                agents_dir=orch_config.get('agents_dir', 'agents'),
                log_level=orch_config.get('log_level', 'INFO'),
                max_concurrent_tasks=orch_config.get('max_concurrent_tasks', 5),
                auto_discover=orch_config.get('auto_discover', True),
                health_check_interval=orch_config.get('health_check_interval', 30),
                task_timeout=orch_config.get('task_timeout', 300),
                enable_api=orch_config.get('enable_api', True),
                api_host=orch_config.get('api_host', '127.0.0.1'),
                api_port=orch_config.get('api_port', 8000)
            )
        except Exception as e:
            print(f"⚠️ Erreur chargement config {config_path}: {e}")
            return cls(config_path=config_path)

# ============================================================================
# SYSTÈME DE LOGGING AVANCÉ
# ============================================================================

class OrchestratorLogger:
    """Logger avancé pour l'orchestrator"""
    
    COLOR_CODES = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Vert
        'WARNING': '\033[33m',    # Jaune
        'ERROR': '\033[31m',      # Rouge
        'CRITICAL': '\033[35m',   # Magenta
        'RESET': '\033[0m'
    }
    
    def __init__(self, name: str = "orchestrator", log_file: Optional[str] = None):
        self.name = name
        self.log_file = log_file
        self._lock = threading.RLock()
        
        # Créer le dossier de logs si nécessaire
        if log_file:
            log_dir = os.path.dirname(log_file)
            if log_dir and not os.path.exists(log_dir):
                os.makedirs(log_dir, exist_ok=True)
    
    def log(self, level: str, message: str, **kwargs):
        """Log un message avec niveau"""
        with self._lock:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
            color = self.COLOR_CODES.get(level, self.COLOR_CODES['RESET'])
            reset = self.COLOR_CODES['RESET']
            
            # Formater le message
            log_msg = f"{color}[{timestamp}] [{level:8}] {self.name}: {message}{reset}"
            
            # Ajouter les détails si présents
            if kwargs:
                details = ' '.join(f'{k}={v}' for k, v in kwargs.items())
                log_msg += f" {details}"
            
            # Afficher à l'écran
            print(log_msg)
            
            # Écrire dans le fichier si configuré
            if self.log_file:
                try:
                    with open(self.log_file, 'a', encoding='utf-8') as f:
                        file_msg = f"[{timestamp}] [{level}] {self.name}: {message}"
                        if kwargs:
                            file_msg += f" {kwargs}"
                        f.write(file_msg + '\n')
                except Exception:
                    pass  # Ne pas échouer sur une erreur de log
    
    def debug(self, message: str, **kwargs):
        self.log('DEBUG', message, **kwargs)
    
    def info(self, message: str, **kwargs):
        self.log('INFO', message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        self.log('WARNING', message, **kwargs)
    
    def error(self, message: str, **kwargs):
        self.log('ERROR', message, **kwargs)
    
    def critical(self, message: str, **kwargs):
        self.log('CRITICAL', message, **kwargs)

# ============================================================================
# CLASSES DE DONNÉES
# ============================================================================

@dataclass
class AgentInfo:
    """Informations sur un agent"""
    name: str
    display_name: str
    config_path: str
    agent_type: str
    enabled: bool
    instantiate: bool
    dependencies: List[str]
    initialization_order: int
    parent: Optional[str]
    purpose: str
    mandatory: bool
    
    @classmethod
    def from_config(cls, agent_name: str, config_data: Dict[str, Any]) -> 'AgentInfo':
        """Crée à partir de la configuration"""
        return cls(
            name=agent_name,
            display_name=config_data.get('display_name', agent_name),
            config_path=config_data.get('config_path', f"agents/{agent_name}/config.yaml"),
            agent_type=config_data.get('agent_type', 'concrete'),
            enabled=config_data.get('enabled', True),
            instantiate=config_data.get('instantiate', True),
            dependencies=config_data.get('dependencies', []),
            initialization_order=config_data.get('initialization_order', 99),
            parent=config_data.get('parent', None),
            purpose=config_data.get('purpose', ''),
            mandatory=config_data.get('mandatory', False)
        )

@dataclass
class TaskInfo:
    """Informations sur une tâche"""
    task_id: str
    agent_name: str
    task_type: str
    parameters: Dict[str, Any]
    priority: int = 50
    status: str = "PENDING"
    result: Optional[Any] = None
    error: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    
    @classmethod
    def create(cls, agent_name: str, task_type: str, parameters: Dict[str, Any], 
               priority: int = 50) -> 'TaskInfo':
        """Crée une nouvelle tâche"""
        task_id = hashlib.md5(
            f"{agent_name}_{task_type}_{datetime.now().timestamp()}".encode()
        ).hexdigest()[:12]
        
        return cls(
            task_id=task_id,
            agent_name=agent_name,
            task_type=task_type,
            parameters=parameters,
            priority=priority
        )

# ============================================================================
# ORCHESTRATOR PRINCIPAL
# ============================================================================

class Orchestrator:
    """Orchestrator principal pour la gestion des agents"""
    
    def __init__(self, config_path: str = "config/project_config.yaml"):
        """
        Initialise l'orchestrator.
        
        Args:
            config_path: Chemin vers le fichier de configuration
        """
        # Configuration
        self.config_path = config_path
        self.config = OrchestratorConfig.from_yaml(config_path)
        
        # Logging
        log_file = f"logs/orchestrator_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        self.logger = OrchestratorLogger("orchestrator", log_file)
        
        # État
        self.initialized = False
        self.running = False
        
        # Agents
        self.agent_configs: Dict[str, Dict[str, Any]] = {}
        self.agent_infos: Dict[str, AgentInfo] = {}
        self.agents: Dict[str, Any] = {}  # Agents instanciés
        self.agent_classes: Dict[str, Type] = {}  # Classes d'agents
        
        # Tâches
        self.task_queue = queue.PriorityQueue()
        self.active_tasks: Dict[str, TaskInfo] = {}
        self.task_history: List[TaskInfo] = []
        
        # Verrous
        self._agents_lock = threading.RLock()
        self._tasks_lock = threading.RLock()
        
        # API (optionnel)
        self.api_server = None
        
        self.logger.info(f"Orchestrator initialisé avec config: {config_path}")
    
    # ============================================================================
    # MÉTHODES D'INITIALISATION
    # ============================================================================
    
    def initialize(self) -> bool:
        """
        Initialise complètement l'orchestrator.
        
        Returns:
            bool: True si l'initialisation réussit
        """
        try:
            self.logger.info("=" * 60)
            self.logger.info("INITIALISATION DE L'ORCHESTRATOR")
            self.logger.info("=" * 60)
            
            # Étape 1: Charger la configuration complète
            self.logger.info("Étape 1: Chargement configuration...")
            if not self._load_full_config():
                self.logger.error("❌ Échec chargement configuration")
                return False
            
            # Étape 2: Découvrir les agents
            self.logger.info("Étape 2: Découverte des agents...")
            discovered = self.discover_agents()
            self.logger.info(f"  → {len(discovered)} agents découverts")
            
            # Étape 3: Charger les classes d'agents
            self.logger.info("Étape 3: Chargement des classes...")
            loaded = self._load_agent_classes()
            self.logger.info(f"  → {len(loaded)} classes chargées")
            
            # Étape 4: Valider les dépendances
            self.logger.info("Étape 4: Validation dépendances...")
            if not self._validate_dependencies():
                self.logger.warning("⚠️ Problèmes de dépendances détectés")
            
            # Étape 5: Initialiser les agents (dans le bon ordre)
            self.logger.info("Étape 5: Initialisation des agents...")
            initialized = self.initialize_agents()
            self.logger.info(f"  → {len(initialized)} agents initialisés")
            
            # Étape 6: Démarrer l'API si activée
            if self.config.enable_api:
                self.logger.info("Étape 6: Démarrage API...")
                self._start_api()
            
            # Étape 7: Démarrer le processeur de tâches
            self.logger.info("Étape 7: Démarrage processeur tâches...")
            self._start_task_processor()
            
            self.initialized = True
            self.running = True
            
            self.logger.info("✅ INITIALISATION RÉUSSIE")
            self.logger.info(f"   Agents actifs: {len(self.agents)}")
            self.logger.info(f"   Classes disponibles: {len(self.agent_classes)}")
            
            # Afficher le résumé
            self._print_summary()
            
            return True
            
        except Exception as e:
            self.logger.critical(f"❌ ERREUR D'INITIALISATION: {e}")
            self.logger.error(traceback.format_exc())
            return False
    
    def _load_full_config(self) -> bool:
        """Charge la configuration complète depuis le YAML"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                full_config = yaml.safe_load(f)
            
            # Charger la configuration des agents
            agents_config = full_config.get('agents', {})
            
            # Convertir en AgentInfo
            for agent_name, agent_data in agents_config.items():
                self.agent_infos[agent_name] = AgentInfo.from_config(agent_name, agent_data)
                self.agent_configs[agent_name] = agent_data
            
            self.logger.info(f"Configuration chargée: {len(self.agent_infos)} agents configurés")
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur chargement config: {e}")
            return False
    
    # ============================================================================
    # DÉCOUVERTE ET CHARGEMENT DES AGENTS
    # ============================================================================
    
    def discover_agents(self) -> List[str]:
        """
        Découvre automatiquement les agents disponibles.
        
        Returns:
            List[str]: Liste des noms d'agents découverts
        """
        discovered = []
        
        try:
            agents_dir = Path(self.config.agents_dir)
            
            if not agents_dir.exists():
                self.logger.warning(f"⚠️ Dossier agents non trouvé: {agents_dir}")
                return discovered
            
            # Parcourir tous les sous-dossiers
            for agent_dir in agents_dir.iterdir():
                if agent_dir.is_dir():
                    agent_name = agent_dir.name
                    
                    # Vérifier si l'agent a un config.yaml
                    config_file = agent_dir / "config.yaml"
                    if config_file.exists():
                        discovered.append(agent_name)
                        self.logger.debug(f"Découvert: {agent_name}")
            
            # Ajouter les agents de la config même sans dossier
            for agent_name in self.agent_infos.keys():
                if agent_name not in discovered:
                    discovered.append(agent_name)
                    self.logger.debug(f"Ajouté depuis config: {agent_name}")
            
            # Trier par ordre d'initialisation
            discovered.sort(key=lambda x: self.agent_infos.get(x, AgentInfo(x, x, "", "", True, True, [], 99, None, "", False)).initialization_order)
            
            self.logger.info(f"Agents découverts: {', '.join(discovered)}")
            return discovered
            
        except Exception as e:
            self.logger.error(f"Erreur découverte agents: {e}")
            return discovered
    
    def _load_agent_classes(self) -> Dict[str, Type]:
        """
        Charge les classes de tous les agents.
        
        Returns:
            Dict[str, Type]: Dictionnaire nom_agent -> classe
        """
        loaded_classes = {}
        
        for agent_name, agent_info in self.agent_infos.items():
            if not agent_info.enabled:
                self.logger.debug(f"Agent désactivé: {agent_name}")
                continue
            
            try:
                # Charger la classe
                agent_class = self._load_single_agent_class(agent_info)
                
                if agent_class:
                    self.agent_classes[agent_name] = agent_class
                    loaded_classes[agent_name] = agent_class
                    self.logger.info(f"✅ Classe chargée: {agent_name}")
                else:
                    self.logger.warning(f"⚠️ Classe non chargée: {agent_name}")
                    
            except Exception as e:
                self.logger.error(f"❌ Erreur chargement {agent_name}: {e}")
        
        return loaded_classes
    
    def _load_single_agent_class(self, agent_info: AgentInfo) -> Optional[Type]:
        """
        Charge la classe d'un agent spécifique.
        
        Args:
            agent_info: Informations sur l'agent
            
        Returns:
            Optional[Type]: La classe chargée ou None
        """
        try:
            # CRITIQUE: Pour BaseAgent, on utilise l'import direct
            if agent_info.name == "base_agent":
                self.logger.info("Chargement BaseAgent (spécial)...")
                
                # Essayer plusieurs méthodes
                try:
                    # Méthode 1: Via agents.base_agent
                    from agents.base_agent import BaseAgent
                    self.logger.info("  → BaseAgent importé via agents.base_agent")
                    return BaseAgent
                except ImportError as e1:
                    self.logger.debug(f"  → Échec méthode 1: {e1}")
                    
                    try:
                        # Méthode 2: Direct depuis le fichier
                        import sys
                        sys.path.insert(0, os.getcwd())
                        from agents.base_agent.base_agent import BaseAgent
                        self.logger.info("  → BaseAgent importé directement")
                        return BaseAgent
                    except ImportError as e2:
                        self.logger.debug(f"  → Échec méthode 2: {e2}")
                        
                        try:
                            # Méthode 3: Via le proxy base_agent
                            import base_agent
                            if hasattr(base_agent, 'BaseAgent'):
                                self.logger.info("  → BaseAgent importé via proxy")
                                return base_agent.BaseAgent
                        except ImportError as e3:
                            self.logger.debug(f"  → Échec méthode 3: {e3}")
                
                # Si tout échoue, créer une classe de secours
                self.logger.warning("Création classe BaseAgent de secours")
                
                class FallbackBaseAgent:
                    def __init__(self, config=None):
                        self.name = "FallbackBaseAgent"
                        self.config = config or {}
                        self.status = "FALLBACK"
                    
                    def execute_task(self, task):
                        return {"error": "BaseAgent en mode secours"}
                
                return FallbackBaseAgent
            
            # Pour les autres agents, charger depuis leur config.yaml
            config_path = Path(agent_info.config_path)
            
            if not config_path.exists():
                self.logger.warning(f"Config non trouvée: {config_path}")
                return None
            
            # Lire la configuration de l'agent
            with open(config_path, 'r', encoding='utf-8') as f:
                agent_config = yaml.safe_load(f)
            
            agent_spec = agent_config.get('agent', {})
            module_path = agent_spec.get('module_path', '')
            class_name = agent_spec.get('class_name', '')
            
            if not module_path or not class_name:
                self.logger.error(f"Module ou classe manquant pour {agent_info.name}")
                return None
            
            # Importer dynamiquement
            self.logger.debug(f"Import dynamique: {module_path}.{class_name}")
            
            try:
                module = importlib.import_module(module_path)
                agent_class = getattr(module, class_name)
                
                # Vérifier que la classe hérite de BaseAgent
                from agents.base_agent import BaseAgent as BaseAgentClass
                if not issubclass(agent_class, BaseAgentClass):
                    self.logger.warning(f"{agent_info.name} n'hérite pas de BaseAgent")
                
                return agent_class
                
            except Exception as e:
                self.logger.error(f"Erreur import {module_path}.{class_name}: {e}")
                return None
                
        except Exception as e:
            self.logger.error(f"Erreur chargement classe {agent_info.name}: {e}")
            return None
    
    # ============================================================================
    # INITIALISATION DES AGENTS
    # ============================================================================
    
    def initialize_agents(self) -> Dict[str, Any]:
        """
        Initialise tous les agents (dans le bon ordre).
        
        Returns:
            Dict[str, Any]: Agents instanciés
        """
        # Trier les agents par ordre d'initialisation
        agents_to_initialize = sorted(
            self.agent_infos.items(),
            key=lambda x: x[1].initialization_order
        )
        
        initialized = {}
        
        for agent_name, agent_info in agents_to_initialize:
            if not agent_info.enabled:
                self.logger.debug(f"Agent désactivé: {agent_name}")
                continue
            
            if not agent_info.instantiate:
                self.logger.debug(f"Agent non instantiable: {agent_name}")
                continue
            
            try:
                # Initialiser l'agent
                agent_instance = self._initialize_single_agent(agent_name, agent_info)
                
                if agent_instance:
                    self.agents[agent_name] = agent_instance
                    initialized[agent_name] = agent_instance
                    
                    self.logger.info(f"✅ Agent initialisé: {agent_name} ({agent_info.display_name})")
                else:
                    if agent_info.mandatory:
                        self.logger.error(f"❌ Agent obligatoire non initialisé: {agent_name}")
                    else:
                        self.logger.warning(f"⚠️ Agent optionnel non initialisé: {agent_name}")
                        
            except Exception as e:
                self.logger.error(f"❌ Erreur initialisation {agent_name}: {e}")
                if agent_info.mandatory:
                    raise
        
        return initialized
    
    def _initialize_single_agent(self, agent_name: str, agent_info: AgentInfo) -> Optional[Any]:
        """
        Initialise un agent spécifique.
        
        Args:
            agent_name: Nom de l'agent
            agent_info: Informations sur l'agent
            
        Returns:
            Optional[Any]: Instance de l'agent ou None
        """
        try:
            # Vérifier que la classe est chargée
            if agent_name not in self.agent_classes:
                self.logger.error(f"Classe non chargée pour {agent_name}")
                return None
            
            agent_class = self.agent_classes[agent_name]
            
            # Charger la configuration spécifique
            agent_config = self._load_agent_configuration(agent_name)
            
            # CRITIQUE: Pour BaseAgent, configuration spéciale
            if agent_name == "base_agent":
                from agents.base_agent.base_agent import AgentConfiguration
                
                # BaseAgent a besoin d'une configuration spéciale
                base_config = AgentConfiguration(
                    name="BaseAgent",
                    capabilities=["ABSTRACT_BASE"],
                    description="Classe de base abstraite pour tous les agents",
                    version="2.2.0"
                )
                
                # Instancier avec la configuration
                agent_instance = agent_class(config=base_config)
                
            else:
                # Pour les autres agents, utiliser la configuration du YAML
                from agents.base_agent.base_agent import AgentConfiguration
                
                # Créer la configuration à partir du YAML
                config_dict = agent_config.get('agent', {})
                
                # S'assurer que les champs requis sont présents
                required_fields = ['name', 'capabilities', 'description']
                for field in required_fields:
                    if field not in config_dict:
                        config_dict[field] = agent_info.display_name if field == 'name' else []
                
                # Créer l'objet de configuration
                config_obj = AgentConfiguration(**config_dict)
                
                # Instancier l'agent
                agent_instance = agent_class(config=config_obj)
            
            # Configurer les métadonnées
            if hasattr(agent_instance, '_orchestrator'):
                agent_instance._orchestrator = self
            
            if hasattr(agent_instance, '_logger'):
                agent_instance._logger = self.logger
            
            return agent_instance
            
        except Exception as e:
            self.logger.error(f"Erreur instanciation {agent_name}: {e}")
            self.logger.error(traceback.format_exc())
            return None
    
    def _load_agent_configuration(self, agent_name: str) -> Dict[str, Any]:
        """
        Charge la configuration d'un agent.
        
        Args:
            agent_name: Nom de l'agent
            
        Returns:
            Dict[str, Any]: Configuration de l'agent
        """
        try:
            agent_info = self.agent_infos.get(agent_name)
            if not agent_info:
                return {}
            
            config_path = Path(agent_info.config_path)
            
            if config_path.exists():
                with open(config_path, 'r', encoding='utf-8') as f:
                    return yaml.safe_load(f)
            else:
                # Retourner une configuration par défaut
                return {
                    'agent': {
                        'name': agent_info.display_name,
                        'description': agent_info.purpose,
                        'capabilities': [],
                        'configuration': {}
                    }
                }
                
        except Exception as e:
            self.logger.error(f"Erreur chargement config {agent_name}: {e}")
            return {}
    
    # ============================================================================
    # VALIDATION DES DÉPENDANCES
    # ============================================================================
    
    def _validate_dependencies(self) -> bool:
        """
        Valide les dépendances entre agents.
        
        Returns:
            bool: True si toutes les dépendances sont satisfaites
        """
        all_valid = True
        
        for agent_name, agent_info in self.agent_infos.items():
            if not agent_info.dependencies:
                continue
            
            for dep_name in agent_info.dependencies:
                # Vérifier si la dépendance existe
                if dep_name not in self.agent_infos:
                    self.logger.error(f"❌ {agent_name}: Dépendance manquante: {dep_name}")
                    all_valid = False
                    continue
                
                # Vérifier si la dépendance est activée
                dep_info = self.agent_infos[dep_name]
                if not dep_info.enabled:
                    self.logger.error(f"❌ {agent_name}: Dépendance désactivée: {dep_name}")
                    all_valid = False
                
                # Vérifier l'ordre d'initialisation
                if dep_info.initialization_order >= agent_info.initialization_order:
                    self.logger.warning(
                        f"⚠️ {agent_name}: Dépendance {dep_name} s'initialise après "
                        f"({dep_info.initialization_order} >= {agent_info.initialization_order})"
                    )
        
        return all_valid
    
    # ============================================================================
    # GESTION DES TÂCHES
    # ============================================================================
    
    def submit_task(self, agent_name: str, task_type: str, 
                    parameters: Dict[str, Any], priority: int = 50) -> Optional[str]:
        """
        Soumet une tâche pour exécution.
        
        Args:
            agent_name: Nom de l'agent
            task_type: Type de tâche
            parameters: Paramètres de la tâche
            priority: Priorité (1-100)
            
        Returns:
            Optional[str]: ID de la tâche ou None
        """
        try:
            # Vérifier que l'agent existe
            if agent_name not in self.agents:
                self.logger.error(f"Agent inconnu: {agent_name}")
                return None
            
            # Créer la tâche
            task = TaskInfo.create(agent_name, task_type, parameters, priority)
            
            # Ajouter à la file d'attente
            self.task_queue.put((-priority, task))  # Négatif pour priorité inversée
            
            # Enregistrer
            with self._tasks_lock:
                self.active_tasks[task.task_id] = task
            
            self.logger.info(f"Tâche soumise: {task.task_id} pour {agent_name}")
            return task.task_id
            
        except Exception as e:
            self.logger.error(f"Erreur soumission tâche: {e}")
            return None
    
    def _start_task_processor(self):
        """Démarre le processeur de tâches en arrière-plan"""
        def process_tasks():
            while self.running:
                try:
                    # Prendre une tâche de la file (bloquant avec timeout)
                    priority, task = self.task_queue.get(timeout=1.0)
                    
                    # Exécuter la tâche
                    self._execute_task(task)
                    
                    # Marquer comme terminée
                    self.task_queue.task_done()
                    
                except queue.Empty:
                    continue  # File vide, continuer
                except Exception as e:
                    self.logger.error(f"Erreur processeur tâches: {e}")
        
        # Démarrer le thread
        processor_thread = threading.Thread(target=process_tasks, daemon=True)
        processor_thread.start()
        
        self.logger.info("Processeur de tâches démarré")
    
    def _execute_task(self, task: TaskInfo):
        """Exécute une tâche spécifique"""
        try:
            task.start_time = datetime.now()
            task.status = "EXECUTING"
            
            self.logger.info(f"Exécution tâche {task.task_id}: {task.agent_name}.{task.task_type}")
            
            # Récupérer l'agent
            agent = self.agents.get(task.agent_name)
            if not agent:
                task.status = "FAILED"
                task.error = f"Agent non trouvé: {task.agent_name}"
                return
            
            # Exécuter la tâche
            if hasattr(agent, 'execute_task'):
                result = agent.execute_task(task.task_type, task.parameters)
                task.result = result
                task.status = "COMPLETED"
                
                self.logger.info(f"Tâche {task.task_id} terminée avec succès")
            else:
                task.status = "FAILED"
                task.error = f"Agent {task.agent_name} n'a pas de méthode execute_task"
                self.logger.error(f"Agent sans execute_task: {task.agent_name}")
                
        except Exception as e:
            task.status = "FAILED"
            task.error = str(e)
            self.logger.error(f"Erreur exécution tâche {task.task_id}: {e}")
            
        finally:
            task.end_time = datetime.now()
            
            # Déplacer vers l'historique
            with self._tasks_lock:
                if task.task_id in self.active_tasks:
                    del self.active_tasks[task.task_id]
                self.task_history.append(task)
    
    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        Récupère le statut d'une tâche.
        
        Args:
            task_id: ID de la tâche
            
        Returns:
            Optional[Dict[str, Any]]: Statut de la tâche
        """
        with self._tasks_lock:
            # Chercher dans les tâches actives
            if task_id in self.active_tasks:
                task = self.active_tasks[task_id]
            else:
                # Chercher dans l'historique
                task = next((t for t in self.task_history if t.task_id == task_id), None)
            
            if task:
                return {
                    'task_id': task.task_id,
                    'agent_name': task.agent_name,
                    'task_type': task.task_type,
                    'status': task.status,
                    'error': task.error,
                    'start_time': task.start_time.isoformat() if task.start_time else None,
                    'end_time': task.end_time.isoformat() if task.end_time else None,
                    'duration': (task.end_time - task.start_time).total_seconds() 
                               if task.start_time and task.end_time else None
                }
        
        return None
    
    # ============================================================================
    # GESTION DES AGENTS
    # ============================================================================
    
    def get_agent(self, agent_name: str) -> Optional[Any]:
        """
        Récupère un agent par son nom.
        
        Args:
            agent_name: Nom de l'agent
            
        Returns:
            Optional[Any]: Instance de l'agent ou None
        """
        return self.agents.get(agent_name)
    
    def get_agent_status(self, agent_name: str) -> Optional[Dict[str, Any]]:
        """
        Récupère le statut d'un agent.
        
        Args:
            agent_name: Nom de l'agent
            
        Returns:
            Optional[Dict[str, Any]]: Statut de l'agent
        """
        agent = self.get_agent(agent_name)
        if not agent:
            return None
        
        status = {
            'name': agent_name,
            'class': agent.__class__.__name__,
            'initialized': True,
            'timestamp': datetime.now().isoformat()
        }
        
        # Ajouter des informations spécifiques si disponibles
        if hasattr(agent, 'status'):
            status['agent_status'] = agent.status
        
        if hasattr(agent, 'capabilities'):
            status['capabilities'] = agent.capabilities
        
        return status
    
    def list_agents(self) -> List[Dict[str, Any]]:
        """
        Liste tous les agents disponibles.
        
        Returns:
            List[Dict[str, Any]]: Liste des agents
        """
        agents_list = []
        
        for agent_name, agent_info in self.agent_infos.items():
            agent_data = {
                'name': agent_name,
                'display_name': agent_info.display_name,
                'type': agent_info.agent_type,
                'enabled': agent_info.enabled,
                'instantiate': agent_info.instantiate,
                'initialized': agent_name in self.agents,
                'dependencies': agent_info.dependencies,
                'initialization_order': agent_info.initialization_order,
                'purpose': agent_info.purpose,
                'mandatory': agent_info.mandatory
            }
            
            agents_list.append(agent_data)
        
        # Trier par nom
        agents_list.sort(key=lambda x: x['name'])
        
        return agents_list
    
    # ============================================================================
    # API REST (FASTAPI)
    # ============================================================================
    
    def _start_api(self):
        """Démarre l'API REST (optionnel)"""
        try:
            # Importer FastAPI dynamiquement
            import fastapi
            from fastapi import FastAPI, HTTPException
            import uvicorn
            
            # Créer l'application
            app = FastAPI(
                title="SmartContractDevPipeline Orchestrator",
                description="API de gestion des agents IA",
                version="2.2.0"
            )
            
            # ========== ENDPOINTS ==========
            
            @app.get("/")
            async def root():
                return {
                    "service": "Orchestrator API",
                    "version": "2.2.0",
                    "status": "running",
                    "agents_count": len(self.agents),
                    "initialized": self.initialized
                }
            
            @app.get("/agents")
            async def get_agents():
                return self.list_agents()
            
            @app.get("/agents/{agent_name}")
            async def get_agent(agent_name: str):
                agent = self.get_agent(agent_name)
                if not agent:
                    raise HTTPException(status_code=404, detail=f"Agent {agent_name} non trouvé")
                
                return self.get_agent_status(agent_name)
            
            @app.post("/tasks")
            async def create_task(
                agent_name: str,
                task_type: str,
                parameters: Dict[str, Any],
                priority: int = 50
            ):
                task_id = self.submit_task(agent_name, task_type, parameters, priority)
                if not task_id:
                    raise HTTPException(status_code=400, detail="Échec création tâche")
                
                return {"task_id": task_id, "status": "submitted"}
            
            @app.get("/tasks/{task_id}")
            async def get_task(task_id: str):
                status = self.get_task_status(task_id)
                if not status:
                    raise HTTPException(status_code=404, detail=f"Tâche {task_id} non trouvée")
                
                return status
            
            @app.get("/health")
            async def health_check():
                return {
                    "status": "healthy" if self.initialized else "initializing",
                    "timestamp": datetime.now().isoformat(),
                    "agents_initialized": len(self.agents),
                    "tasks_pending": self.task_queue.qsize(),
                    "tasks_active": len(self.active_tasks)
                }
            
            # Démarrer le serveur dans un thread
            def run_server():
                uvicorn.run(
                    app,
                    host=self.config.api_host,
                    port=self.config.api_port,
                    log_level="warning"
                )
            
            api_thread = threading.Thread(target=run_server, daemon=True)
            api_thread.start()
            
            self.api_server = app
            self.logger.info(f"API démarrée: http://{self.config.api_host}:{self.config.api_port}")
            
        except ImportError:
            self.logger.warning("FastAPI non installé - API désactivée")
        except Exception as e:
            self.logger.error(f"Erreur démarrage API: {e}")
    
    # ============================================================================
    # UTILITAIRES
    # ============================================================================
    
    def _print_summary(self):
        """Affiche un résumé de l'initialisation"""
        self.logger.info("\n" + "=" * 60)
        self.logger.info("RÉSUMÉ DE L'INITIALISATION")
        self.logger.info("=" * 60)
        
        # Agents initialisés
        initialized_count = len(self.agents)
        total_agents = len([a for a in self.agent_infos.values() if a.enabled and a.instantiate])
        
        self.logger.info(f"Agents: {initialized_count}/{total_agents} initialisés")
        
        # Lister les agents
        for agent_name, agent in self.agents.items():
            agent_info = self.agent_infos.get(agent_name)
            if agent_info:
                status = "✅" if hasattr(agent, 'status') else "⚡"
                self.logger.info(f"  {status} {agent_name:20} ({agent_info.display_name})")
        
        # Tâches en attente
        self.logger.info(f"\nTâches en file d'attente: {self.task_queue.qsize()}")
        
        # API
        if self.api_server:
            self.logger.info(f"API: http://{self.config.api_host}:{self.config.api_port}")
        
        self.logger.info("=" * 60)
    
    def stop(self):
        """Arrête proprement l'orchestrator"""
        self.logger.info("Arrêt de l'orchestrator...")
        
        self.running = False
        
        # Arrêter tous les agents
        for agent_name, agent in self.agents.items():
            try:
                if hasattr(agent, 'stop'):
                    agent.stop()
                    self.logger.info(f"Agent arrêté: {agent_name}")
            except Exception as e:
                self.logger.error(f"Erreur arrêt {agent_name}: {e}")
        
        # Nettoyer
        self.agents.clear()
        self.agent_classes.clear()
        
        self.logger.info("Orchestrator arrêté")
    
    def diagnose(self) -> Dict[str, Any]:
        """
        Génère un diagnostic complet.
        
        Returns:
            Dict[str, Any]: Diagnostic détaillé
        """
        return {
            'timestamp': datetime.now().isoformat(),
            'orchestrator': {
                'initialized': self.initialized,
                'running': self.running,
                'config': self.config.__dict__,
                'api_enabled': self.config.enable_api and self.api_server is not None
            },
            'agents': {
                'configured': len(self.agent_infos),
                'classes_loaded': len(self.agent_classes),
                'initialized': len(self.agents),
                'list': self.list_agents()
            },
            'tasks': {
                'queue_size': self.task_queue.qsize(),
                'active_tasks': len(self.active_tasks),
                'history_size': len(self.task_history)
            },
            'system': {
                'python_version': sys.version,
                'platform': sys.platform,
                'cwd': os.getcwd(),
                'sys_path': sys.path[:3]
            }
        }

# ============================================================================
# FONCTIONS UTILITAIRES
# ============================================================================

def test_agent_initialization():
    """Teste l'initialisation d'un agent simple"""
    print("🧪 TEST D'INITIALISATION D'AGENT")
    print("=" * 50)
    
    try:
        # Importer BaseAgent
        from agents.base_agent import BaseAgent, AgentConfiguration
        
        print("✅ BaseAgent importé")
        
        # Créer une configuration simple
        config = AgentConfiguration(
            name="TestAgent",
            capabilities=["TESTING"],
            description="Agent de test",
            version="1.0.0"
        )
        
        # Instancier
        agent = BaseAgent(config=config)
        
        print(f"✅ Agent instancié: {agent.name}")
        print(f"   - Status: {agent.status}")
        print(f"   - Capabilities: {agent.capabilities}")
        
        # Tester une tâche simple
        if hasattr(agent, 'execute_task'):
            result = agent.execute_task("test", {"message": "Hello"})
            print(f"✅ Tâche exécutée: {result}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_orchestrator_simple(config_path: str = "config/project_config.yaml"):
    """Teste l'orchestrator de manière simple"""
    print("\n🧪 TEST ORCHESTRATOR SIMPLE")
    print("=" * 50)
    
    try:
        # Initialiser l'orchestrator
        orchestrator = Orchestrator(config_path)
        
        # Initialiser
        success = orchestrator.initialize()
        
        if success:
            print("✅ Orchestrator initialisé avec succès")
            
            # Afficher les agents
            agents = orchestrator.list_agents()
            print(f"\n📋 Agents disponibles ({len(agents)}):")
            for agent in agents[:5]:  # 5 premiers
                status = "✅" if agent['initialized'] else "❌"
                print(f"  {status} {agent['name']:20} ({agent['display_name']})")
            
            if len(agents) > 5:
                print(f"  ... et {len(agents) - 5} autres")
            
            return True
        else:
            print("❌ Échec initialisation orchestrator")
            return False
            
    except Exception as e:
        print(f"❌ Erreur orchestrator: {e}")
        import traceback
        traceback.print_exc()
        return False

# ============================================================================
# POINT D'ENTRÉE PRINCIPAL
# ============================================================================

def main():
    """Fonction principale"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Orchestrator SmartContractDevPipeline")
    parser.add_argument("--config", default="config/project_config.yaml", 
                       help="Chemin vers le fichier de configuration")
    parser.add_argument("--test", action="store_true", 
                       help="Exécuter les tests")
    parser.add_argument("--diagnose", action="store_true",
                       help="Générer un diagnostic")
    parser.add_argument("--simple", action="store_true",
                       help="Mode simple sans API")
    
    args = parser.parse_args()
    
    print("\n" + "=" * 60)
    print("ORCHESTRATOR - SmartContractDevPipeline v2.2.0")
    print("=" * 60)
    
    if args.test:
        # Mode test
        print("Mode test activé")
        
        # Test 1: Initialisation agent simple
        test1 = test_agent_initialization()
        
        # Test 2: Orchestrator simple
        test2 = test_orchestrator_simple(args.config)
        
        print("\n" + "=" * 60)
        print("RÉSULTATS DES TESTS:")
        print(f"  Test agent: {'✅' if test1 else '❌'}")
        print(f"  Test orchestrator: {'✅' if test2 else '❌'}")
        print("=" * 60)
        
        exit(0 if test1 and test2 else 1)
    
    # Mode normal
    try:
        # Configurer l'orchestrator
        if args.simple:
            print("Mode simple - API désactivée")
            config = OrchestratorConfig.from_yaml(args.config)
            config.enable_api = False
            orchestrator = Orchestrator(config_path=args.config)
            orchestrator.config = config
        else:
            orchestrator = Orchestrator(config_path=args.config)
        
        # Initialiser
        success = orchestrator.initialize()
        
        if not success:
            print("❌ Échec initialisation orchestrator")
            exit(1)
        
        # Mode diagnostic
        if args.diagnose:
            diagnosis = orchestrator.diagnose()
            print("\n🔍 DIAGNOSTIC COMPLET:")
            print(json.dumps(diagnosis, indent=2, default=str))
            exit(0)
        
        # Mode interactif
        print("\n🎯 Orchestrator prêt - En attente de tâches")
        print("   Commande: Ctrl+C pour arrêter")
        print("=" * 60)
        
        # Boucle principale
        try:
            while orchestrator.running:
                time.sleep(1)
                
                # Afficher le statut toutes les 30 secondes
                if int(time.time()) % 30 == 0:
                    pending = orchestrator.task_queue.qsize()
                    active = len(orchestrator.active_tasks)
                    if pending > 0 or active > 0:
                        print(f"📊 Statut: {pending} tâches en attente, {active} actives")
                        
        except KeyboardInterrupt:
            print("\n\n🛑 Arrêt demandé...")
        
        finally:
            # Arrêt propre
            orchestrator.stop()
            print("👋 Orchestrator arrêté")
        
    except Exception as e:
        print(f"💥 ERREUR FATALE: {e}")
        import traceback
        traceback.print_exc()
        exit(1)

if __name__ == "__main__":
    main()
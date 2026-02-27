import logging

logger = logging.getLogger(__name__)

"""
Registry Agent - Catalogue intelligent des agents
Version 2.0.0 - Découverte · Versioning · Dépendances · Cache
"""

import os
import sys
import json
import yaml
import asyncio
import hashlib
import semver
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Dict, List, Any, Optional, Set, Tuple
from collections import defaultdict, deque
import pickle
import shutil
import traceback

# Import BaseAgent
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from agents.base_agent.base_agent import BaseAgent, AgentStatus, AgentStatus

# =====================================================================
# ENUMS
# =====================================================================

class RegistryEvent(Enum):
    """Événements du registry"""
    AGENT_REGISTERED = "agent_registered"
    AGENT_UPDATED = "agent_updated"
    AGENT_DEPRECATED = "agent_deprecated"
    AGENT_REMOVED = "agent_removed"
    DEPENDENCY_CYCLE = "dependency_cycle_detected"


class RegistryAgentStatus(Enum):
    """Statut d'un agent dans le registry"""
    ACTIVE = "active"
    DEPRECATED = "deprecated"
    ARCHIVED = "archived"
    BETA = "beta"
    EXPERIMENTAL = "experimental"
    ERROR = "error"  # 🔥 AJOUTE CETTE LIGNE


# =====================================================================
# AGENT PRINCIPAL
# =====================================================================

class RegistryAgent(BaseAgent):
    """
    Agent Registry - Catalogue central intelligent
    Gère l'enregistrement, la découverte, le versioning et les dépendances
    """
    
    def __init__
    async def _initialize_components(self):
        """Initialise les composants spécifiques."""
        self.logger.info(f"Initialisation des composants de {class_name}...")
        return True
(self, config_path: str = ""):
        """Initialise le registry agent"""
        super().__init__
    async def _initialize_components(self):
        """Initialise les composants spécifiques."""
        self.logger.info(f"Initialisation des composants de {class_name}...")
        return True
(config_path)
        
        self._logger.info("🗄️ Registry Agent créé")
        
        # Charger configuration
        self._load_configuration()
        
        # =================================================================
        # BASES DE DONNÉES
        # =================================================================
        self._agents: Dict[str, Dict] = {}           # nom → métadonnées
        self._versions: Dict[str, List[Dict]] = defaultdict(list)  # nom → versions
        self._dependencies: Dict[str, List[str]] = defaultdict(list)  # nom → dépendances
        self._capabilities_index: Dict[str, Set[str]] = defaultdict(set)  # capacité → agents
        self._tags_index: Dict[str, Set[str]] = defaultdict(set)  # tag → agents
        
        # =================================================================
        # CACHE
        # =================================================================
        self._instance_cache: Dict[str, Tuple[Any, datetime]] = {}  # nom → (instance, timestamp)
        self._cache_stats = {
            "hits": 0,
            "misses": 0,
            "size_bytes": 0
        }
        
        # =================================================================
        # GRAPHE DE DÉPENDANCES
        # =================================================================
        self._dependency_graph: Dict[str, Set[str]] = defaultdict(set)
        self._reverse_deps: Dict[str, Set[str]] = defaultdict(set)
        
        # =================================================================
        # MÉTRIQUES
        # =================================================================
        self._registry_metrics = {  # 🔥 Nouveau nom
            "registrations_total": 0,
            "discovery_queries": 0,
            "dependency_resolutions": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "active_agents": 0,
            "deprecated_agents": 0,
            "dependency_cycles": 0
        }
        
        # =================================================================
        # ÉTAT INTERNE
        # =================================================================
        self._events_queue = asyncio.Queue()
        self._websocket_connections = []
        self._background_tasks = []
        
        # Créer les répertoires
        self._create_directories()
        
        # Charger les données existantes
        self._load_data()
        
        self._logger.info(f"✅ Registry initialisé avec {len(self._agents)} agents")
    
    def _load_configuration(self):
        """Charge la configuration depuis le fichier YAML"""
        try:
            config_path = os.path.join(os.path.dirname(__file__), "config.yaml")
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    file_config = yaml.safe_load(f)
                    if file_config:
                        self._agent_config.update(file_config)
                        
                        # Extraire les infos de l'agent
                        agent_info = file_config.get('agent', {})
                        self._name = agent_info.get('name', self._name)
                        self._display_name = agent_info.get('display_name', self._display_name)
                        self._version = agent_info.get('version', self._version)
                        
                        self._logger.info(f"✅ Configuration chargée: {self._name} v{self._version}")
        except Exception as e:
            self._logger.warning(f"⚠️ Erreur chargement config: {e}")
    
    def _create_directories(self):
        """Crée les répertoires nécessaires"""
        storage_path = Path(self._agent_config["registry"]["storage"]["path"])
        dirs = [
            storage_path,
            storage_path / "cache",
            Path("./reports/registry")
        ]
        
        for dir_path in dirs:
            dir_path.mkdir(parents=True, exist_ok=True)
            self._logger.debug(f"📁 Répertoire créé: {dir_path}")
    
    def _load_data(self):
        """Charge les données depuis le disque"""
        storage = self._agent_config["registry"]["storage"]
        base_path = Path(storage["path"])
        
        # Charger les agents
        agents_file = base_path / storage["agents_file"]
        if agents_file.exists():
            try:
                with open(agents_file, 'r', encoding='utf-8') as f:
                    self._agents = json.load(f)
                self._logger.info(f"✅ Agents chargés: {len(self._agents)}")
            except Exception as e:
                self._logger.error(f"❌ Erreur chargement agents: {e}")
        
        # Charger les versions
        versions_file = base_path / storage["versions_file"]
        if versions_file.exists():
            try:
                with open(versions_file, 'r', encoding='utf-8') as f:
                    self._versions = defaultdict(list, json.load(f))
            except Exception as e:
                self._logger.error(f"❌ Erreur chargement versions: {e}")
        
        # Charger les dépendances
        deps_file = base_path / storage["dependencies_file"]
        if deps_file.exists():
            try:
                with open(deps_file, 'r', encoding='utf-8') as f:
                    deps_data = json.load(f)
                    self._dependencies = defaultdict(list, deps_data)
                    
                    # Reconstruire le graphe
                    for agent, deps in deps_data.items():
                        self._dependency_graph[agent] = set(deps)
                        for dep in deps:
                            self._reverse_deps[dep].add(agent)
            except Exception as e:
                self._logger.error(f"❌ Erreur chargement dépendances: {e}")
        
        # Reconstruire les index
        self._rebuild_indexes()
    
    def _save_data(self):
        """Sauvegarde les données sur le disque"""
        storage = self._agent_config["registry"]["storage"]
        base_path = Path(storage["path"])
        
        try:
            # Sauvegarder les agents
            with open(base_path / storage["agents_file"], 'w', encoding='utf-8') as f:
                json.dump(self._agents, f, indent=2, ensure_ascii=False)
            
            # Sauvegarder les versions
            with open(base_path / storage["versions_file"], 'w', encoding='utf-8') as f:
                json.dump(dict(self._versions), f, indent=2, ensure_ascii=False)
            
            # Sauvegarder les dépendances
            with open(base_path / storage["dependencies_file"], 'w', encoding='utf-8') as f:
                json.dump(dict(self._dependencies), f, indent=2, ensure_ascii=False)
            
            self._logger.debug("💾 Données sauvegardées")
            
        except Exception as e:
            self._logger.error(f"❌ Erreur sauvegarde: {e}")
    
    def _rebuild_indexes(self):
        """Reconstruit les index de recherche"""
        self._capabilities_index.clear()
        self._tags_index.clear()
        
        for agent_name, agent_info in self._agents.items():
            # Index des capacités
            for cap in agent_info.get("capabilities", []):
                self._capabilities_index[cap].add(agent_name)
            
            # Index des tags
            for tag in agent_info.get("tags", []):
                self._tags_index[tag].add(agent_name)
    
    async def initialize(self) -> bool:
        """Initialisation asynchrone"""
        try:
            self._set_status(AgentStatus.INITIALIZING)
            self._logger.info("🗄️ Initialisation du Registry...")
            
            # Vérifier les dépendances
            await self._check_dependencies()
            
            # Initialiser les composants
            self._initialize_components()
            
            # Vérifier les cycles de dépendances
            await self._detect_dependency_cycles()
            
            # Démarrer les tâches de fond
            self._background_tasks = [
                asyncio.create_task(self._backup_worker()),
                asyncio.create_task(self._metrics_worker()),
                asyncio.create_task(self._events_worker())
            ]
            
            self._set_status(AgentStatus.READY)
            self._logger.info(f"✅ Registry prêt - {len(self._agents)} agents enregistrés")
            return True
            
        except Exception as e:
            self._logger.error(f"❌ Erreur initialisation: {e}")
            self._set_status(AgentStatus.ERROR)
            return False
    
    async def _check_dependencies(self) -> bool:
        """Vérifie les dépendances"""
        self._logger.info("Vérification des dépendances...")
        return True  # Indépendant
    
    def _initialize_components(self):
        """Initialise les composants internes"""
        self._components = {
            "agent_registry": self._init_agent_registry(),
            "version_manager": self._init_version_manager(),
            "dependency_resolver": self._init_dependency_resolver(),
            "cache_manager": self._init_cache_manager(),
            "metrics_collector": self._init_metrics_collector()
        }
        self._logger.info(f"✅ Composants: {list(self._components.keys())}")
    
    def _init_agent_registry(self) -> Dict[str, Any]:
        return {
            "agents_count": len(self._agents),
            "capabilities_count": len(self._capabilities_index),
            "tags_count": len(self._tags_index)
        }
    
    def _init_version_manager(self) -> Dict[str, Any]:
        return {
            "versions_count": sum(len(v) for v in self._versions.values()),
            "strategy": self._agent_config["registry"]["versioning"]["strategy"]
        }
    
    def _init_dependency_resolver(self) -> Dict[str, Any]:
        return {
            "max_depth": self._agent_config["registry"]["dependencies"]["max_depth"],
            "detect_cycles": self._agent_config["registry"]["dependencies"]["detect_cycles"]
        }
    
    def _init_cache_manager(self) -> Dict[str, Any]:
        return {
            "enabled": self._agent_config["registry"]["cache"]["enabled"],
            "max_size_mb": self._agent_config["registry"]["cache"]["max_size_mb"],
            "ttl_seconds": self._agent_config["registry"]["cache"]["ttl_seconds"]
        }
    
    def _init_metrics_collector(self) -> Dict[str, Any]:
        return {
            "metrics": self._registry_metrics.copy()
        }
    
    # -----------------------------------------------------------------
    # API PUBLIQUE - ENREGISTREMENT
    # -----------------------------------------------------------------
    
    async def register_agent(self, agent_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enregistre un agent dans le registry
        
        Args:
            agent_data: Métadonnées de l'agent (nom, version, capacités, etc.)
            
        Returns:
            Agent enregistré avec métadonnées complètes
        """
        self._logger.info(f"📝 Enregistrement agent: {agent_data.get('name')}")
        
        # Valider les données
        validation_result = await self._validate_agent_data(agent_data)
        if not validation_result["valid"]:
            return {"error": validation_result["errors"], "success": False}
        
        name = agent_data["name"]
        version = agent_data["version"]
        
        # Vérifier si l'agent existe déjà
        if name in self._agents:
            existing = self._agents[name]
            # Comparer les versions
            if semver.compare(version, existing["version"]) > 0:
                # Nouvelle version
                await self._archive_version(name, existing)
            else:
                return {"error": f"Agent {name} déjà enregistré en version {existing['version']}", "success": False}
        
        # Ajouter les métadonnées
        agent_entry = {
            **agent_data,
            "registered_at": datetime.now().isoformat(),
            "last_seen": datetime.now().isoformat(),
            "status": "active",  # ✅ String, pas l'enum
            "usage_count": 0
        }
        
        # Enregistrer
        self._agents[name] = agent_entry
        self._versions[name].append({
            "version": version,
            "registered_at": datetime.now().isoformat(),
            "data": agent_data
        })
        
        # Mettre à jour les dépendances
        deps = agent_data.get("dependencies", [])
        self._dependencies[name] = deps
        self._dependency_graph[name] = set(deps)
        for dep in deps:
            self._reverse_deps[dep].add(name)
        
        # Mettre à jour les index
        for cap in agent_data.get("capabilities", []):
            self._capabilities_index[cap].add(name)
        for tag in agent_data.get("tags", []):
            self._tags_index[tag].add(name)
        
        # Métriques
        self._registry_metrics["registrations_total"] += 1
        self._registry_metrics["active_agents"] = len([a for a in self._agents.values() if a.get("status") == "active"])
        
        # Sauvegarder
        self._save_data()
        
        # Émettre événement
        await self._emit_event(RegistryEvent.AGENT_REGISTERED, {
            "name": name,
            "version": version,
            "capabilities": agent_data.get("capabilities", [])
        })
        
        self._logger.info(f"✅ Agent {name} v{version} enregistré")
        
        return {"agent": agent_entry, "success": True}
    
    async def _validate_agent_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Valide les données d'un agent contre le schéma"""
        errors = []
        
        # Champs requis
        required = self._agent_config["schema"]["required_fields"]
        for field in required:
            if field not in data:
                errors.append(f"Champ requis manquant: {field}")
        
        if errors:
            return {"valid": False, "errors": errors}
        
        # Validation du nom
        import re
        name_pattern = self._agent_config["schema"]["validation"]["name_pattern"]
        if not re.match(name_pattern, data["name"]):
            errors.append(f"Nom invalide: doit correspondre à {name_pattern}")
        
        # Validation de la version
        version_pattern = self._agent_config["schema"]["validation"]["version_pattern"]
        if not re.match(version_pattern, data["version"]):
            errors.append(f"Version invalide: doit être semver")
        
        # Validation des capacités
        if len(data.get("capabilities", [])) > self._agent_config["schema"]["validation"]["capabilities_max"]:
            errors.append(f"Trop de capacités: max {self._agent_config['schema']['validation']['capabilities_max']}")
        
        # Validation des dépendances
        if len(data.get("dependencies", [])) > self._agent_config["schema"]["validation"]["dependencies_max"]:
            errors.append(f"Trop de dépendances: max {self._agent_config['schema']['validation']['dependencies_max']}")
        
        return {"valid": len(errors) == 0, "errors": errors}
    
    async def _archive_version(self, name: str, agent_data: Dict):
        """Archive une ancienne version"""
        agent_data["status"] = "archived"
        agent_data["archived_at"] = datetime.now().isoformat()
        self._versions[name].append({
            "version": agent_data["version"],
            "archived_at": datetime.now().isoformat(),
            "data": agent_data
        })
    
    # -----------------------------------------------------------------
    # API PUBLIQUE - DÉCOUVERTE
    # -----------------------------------------------------------------
    
    async def discover_agents(self, query: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Découvre des agents selon des critères
        
        Args:
            query: Critères de recherche (name, capability, tag, version, status)
            
        Returns:
            Liste des agents correspondants
        """
        self._registry_metrics["discovery_queries"] += 1
        
        results = set()
        
        # Par nom (wildcard supporté)
        if "name" in query:
            name_pattern = query["name"].replace("*", ".*")
            import re
            for agent_name in self._agents:
                if re.match(name_pattern, agent_name):
                    results.add(agent_name)
        
        # Par capacité
        if "capability" in query:
            results.update(self._capabilities_index.get(query["capability"], set()))
        
        # Par tag
        if "tag" in query:
            results.update(self._tags_index.get(query["tag"], set()))
        
        # Si aucun critère, tous les agents
        if not results:
            results = set(self._agents.keys())
        
        # Filtrer par version
        agents_list = []
        for name in results:
            agent = self._agents.get(name)
            if not agent:
                continue
            
            # Filtre par version
            if "version" in query and agent["version"] != query["version"]:
                continue
            
            # Filtre par statut
            if "status" in query and agent.get("status") != query["status"]:
                continue
            
            agents_list.append(agent)
        
        # Limiter les résultats
        max_results = self._agent_config["registry"]["discovery"]["max_results"]
        return agents_list[:max_results]
    
    async def get_agent(self, name: str, version: Optional[str] = None) -> Optional[Dict]:
        """
        Récupère les informations d'un agent spécifique
        
        Args:
            name: Nom de l'agent
            version: Version spécifique (sinon dernière)
            
        Returns:
            Métadonnées de l'agent ou None
        """
        if version:
            # Chercher dans l'historique des versions
            for v in self._versions.get(name, []):
                if v.get("version") == version:
                    return v.get("data")
            return None
        else:
            return self._agents.get(name)
    
    async def get_versions(self, name: str) -> List[Dict]:
        """Récupère l'historique des versions d'un agent"""
        return self._versions.get(name, [])
    
    # -----------------------------------------------------------------
    # API PUBLIQUE - DÉPENDANCES
    # -----------------------------------------------------------------
    
    async def resolve_dependencies(self, agent_name: str, 
                                   transitive: bool = True) -> Dict[str, Any]:
        """
        Résout les dépendances d'un agent
        
        Args:
            agent_name: Nom de l'agent
            transitive: Inclure les dépendances transitives
            
        Returns:
            Ordre de résolution et graphe
        """
        self._registry_metrics["dependency_resolutions"] += 1
        
        if agent_name not in self._agents:
            return {"error": f"Agent {agent_name} non trouvé", "success": False}
        
        visited = set()
        order = []
        graph = {}
        
        def dfs(name, depth=0):
            if name in visited:
                return
            if depth > self._agent_config["registry"]["dependencies"]["max_depth"]:
                return
            
            visited.add(name)
            deps = self._dependencies.get(name, [])
            
            graph[name] = deps
            
            for dep in deps:
                if transitive:
                    dfs(dep, depth + 1)
            
            order.append(name)
        
        dfs(agent_name)
        
        return {
            "agent": agent_name,
            "resolution_order": order,
            "graph": graph,
            "transitive": transitive,
            "success": True
        }
    
    async def get_dependents(self, agent_name: str) -> List[str]:
        """Récupère les agents qui dépendent de celui-ci"""
        return list(self._reverse_deps.get(agent_name, set()))
    
    async def _detect_dependency_cycles(self) -> List[List[str]]:
        """Détecte les cycles dans le graphe de dépendances"""
        cycles = []
        visited = set()
        stack = []
        
        def dfs(node):
            if node in stack:
                cycle = stack[stack.index(node):] + [node]
                cycles.append(cycle)
                self._registry_metrics["dependency_cycles"] += 1
                return
            if node in visited:
                return
            
            visited.add(node)
            stack.append(node)
            
            for dep in self._dependencies.get(node, []):
                dfs(dep)
            
            stack.pop()
        
        for agent in self._agents:
            dfs(agent)
        
        if cycles:
            self._logger.warning(f"⚠️ Cycles de dépendances détectés: {cycles}")
            await self._emit_event(RegistryEvent.DEPENDENCY_CYCLE, {"cycles": cycles})
        
        return cycles
    
    # -----------------------------------------------------------------
    # API PUBLIQUE - CACHE
    # -----------------------------------------------------------------
    
    async def get_instance(self, agent_name: str, 
                          create_if_missing: bool = False) -> Optional[Any]:
        """
        Récupère une instance en cache d'un agent
        
        Args:
            agent_name: Nom de l'agent
            create_if_missing: Créer l'instance si absente
            
        Returns:
            Instance de l'agent ou None
        """
        cache_config = self._agent_config["registry"]["cache"]
        if not cache_config["enabled"]:
            return None
        
        # Vérifier le cache
        if agent_name in self._instance_cache:
            instance, timestamp = self._instance_cache[agent_name]
            age = (datetime.now() - timestamp).total_seconds()
            
            if age < cache_config["ttl_seconds"]:
                self._cache_stats["hits"] += 1
                self._registry_metrics["cache_hits"] += 1
                return instance
            else:
                # Expiré
                del self._instance_cache[agent_name]
                self._cache_stats["misses"] += 1
                self._registry_metrics["cache_misses"] += 1
        
        if not create_if_missing:
            return None
        
        # Créer l'instance
        agent_info = self._agents.get(agent_name)
        if not agent_info:
            return None
        
        try:
            # Importer dynamiquement la classe
            module_path = agent_info["class_path"]
            class_name = agent_info.get("class_name", agent_info["name"].title() + "Agent")
            
            module = __import__(module_path, fromlist=[class_name])
            agent_class = getattr(module, class_name)
            
            instance = agent_class()
            await instance.initialize()
            
            # Mettre en cache
            self._instance_cache[agent_name] = (instance, datetime.now())
            
            # Mettre à jour les stats
            self._cache_stats["misses"] += 1
            self._registry_metrics["cache_misses"] += 1
            
            return instance
            
        except Exception as e:
            self._logger.error(f"❌ Erreur création instance {agent_name}: {e}")
            return None
    
    async def clear_cache(self, agent_name: Optional[str] = None):
        """Vide le cache"""
        if agent_name:
            self._instance_cache.pop(agent_name, None)
        else:
            self._instance_cache.clear()
        self._logger.info("🧹 Cache vidé")
    
    # -----------------------------------------------------------------
    # TÂCHES DE FOND
    # -----------------------------------------------------------------
    
    async def _backup_worker(self):
        """Sauvegarde périodique des données"""
        backup_config = self._agent_config["registry"]["storage"]
        if not backup_config.get("backup_enabled", False):
            return
        
        interval = backup_config.get("backup_interval", 3600)
        
        while self._status == AgentStatus.READY:  # ✅ CORRIGÉ
            try:
                await asyncio.sleep(interval)
                self._save_data()
                
                # Backup
                backup_dir = Path(backup_config["path"]) / "backups"
                backup_dir.mkdir(exist_ok=True)
                
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_file = backup_dir / f"registry_backup_{timestamp}.json"
                
                backup_data = {
                    "agents": self._agents,
                    "versions": dict(self._versions),
                    "dependencies": dict(self._dependencies),
                    "timestamp": datetime.now().isoformat()
                }
                
                with open(backup_file, 'w', encoding='utf-8') as f:
                    json.dump(backup_data, f, indent=2)
                
                # Nettoyer les vieux backups
                await self._cleanup_old_backups(backup_dir)
                
            except Exception as e:
                self._logger.error(f"❌ Erreur backup: {e}")
    
    async def _cleanup_old_backups(self, backup_dir: Path):
        """Nettoie les vieux backups"""
        retention = self._agent_config["registry"]["storage"].get("backup_retention", 7)
        cutoff = datetime.now() - timedelta(days=retention)
        
        for backup_file in backup_dir.glob("registry_backup_*.json"):
            try:
                # Extraire la date du nom du fichier
                date_str = backup_file.stem.replace("registry_backup_", "")
                file_date = datetime.strptime(date_str, "%Y%m%d_%H%M%S")
                
                if file_date < cutoff:
                    backup_file.unlink()
                    self._logger.debug(f"🗑️ Backup supprimé: {backup_file.name}")
            except Exception as e:
                self._logger.error(f"❌ Erreur nettoyage backup: {e}")
    
    async def _metrics_worker(self):
        """Collecte et exporte les métriques"""
        while self._status == AgentStatus.READY:  # ✅ CORRIGÉ
            try:
                await asyncio.sleep(60)
                
                # Mettre à jour les métriques
                self._registry_metrics["active_agents"] = len([a for a in self._agents.values() if a.get("status") == "active"])
                self._registry_metrics["deprecated_agents"] = len([a for a in self._agents.values() if a.get("status") == "deprecated"])
                
            except Exception as e:
                self._logger.error(f"❌ Erreur métriques: {e}")
    
    async def _events_worker(self):
        """Traite les événements en file d'attente"""
        while self._status == AgentStatus.READY:  # ✅ CORRIGÉ
            try:
                event = await self._events_queue.get()
                await self._process_event(event)
            except Exception as e:
                self._logger.error(f"❌ Erreur traitement événement: {e}")
    
    async def _emit_event(self, event_type: RegistryEvent, data: Dict[str, Any]):
        """Émet un événement - Version simplifiée sans send_message"""
        self._logger.debug(f"📢 Événement: {event_type.value}")
        
        # Stocker l'événement en interne seulement
        if not hasattr(self, '_events'):
            self._events = []
        self._events.append({
            "type": event_type.value,
            "timestamp": datetime.now().isoformat(),
            "data": data
        })
        
        # Limiter la taille de l'historique
        if len(self._events) > 100:
            self._events = self._events[-100:]
    
    async def _process_event(self, event: Dict[str, Any]):
        """Traite un événement"""
        self._logger.debug(f"📢 Événement: {event['type']}")
        
        # Notifier les websockets
        for ws in self._websocket_connections:
            try:
                await ws.send(json.dumps(event))
            except:
                self._websocket_connections.remove(ws)
    
    # -----------------------------------------------------------------
    # API PUBLIQUE - UTILITAIRES
    # -----------------------------------------------------------------
    
    async def get_statistics(self) -> Dict[str, Any]:
        """Retourne des statistiques sur le registry"""
        return {
            "agents": {
                "total": len(self._agents),
                "active": self._registry_metrics["active_agents"],
                "deprecated": self._registry_metrics["deprecated_agents"]
            },
            "versions": {
                "total": sum(len(v) for v in self._versions.values()),
                "per_agent_avg": sum(len(v) for v in self._versions.values()) / max(len(self._agents), 1)
            },
            "capabilities": {
                "total": len(self._capabilities_index),
                "unique": len(set().union(*self._capabilities_index.values()))
            },
            "dependencies": {
                "total": sum(len(d) for d in self._dependencies.values()),
                "cycles": self._registry_metrics["dependency_cycles"]
            },
            "cache": {
                "hits": self._cache_stats["hits"],
                "misses": self._cache_stats["misses"],
                "hit_ratio": self._cache_stats["hits"] / max(self._cache_stats["hits"] + self._cache_stats["misses"], 1),
                "size_bytes": self._cache_stats["size_bytes"]
            },
            "metrics": self._registry_metrics  # 🔥 ICI
        }
    
    async def export_catalog(self, format: str = "json") -> Dict[str, Any]:
        """Exporte le catalogue complet"""
        return {
            "agents": self._agents,
            "versions": dict(self._versions),
            "dependencies": dict(self._dependencies),
            "capabilities_index": {k: list(v) for k, v in self._capabilities_index.items()},
            "tags_index": {k: list(v) for k, v in self._tags_index.items()},
            "statistics": await self.get_statistics(),
            "exported_at": datetime.now().isoformat()
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Vérifie la santé de l'agent"""
        stats = await self.get_statistics()
        return {
            "agent": self._name,
            "status": self._status.value,  # ✅ C'est le statut BaseAgent, pas le registry
            "ready": self._status == RegistryAgentStatus.READY,
            "agents_registered": len(self._agents),
            "cache_hit_ratio": stats["cache"]["hit_ratio"],
            "dependency_cycles": stats["dependencies"]["cycles"],
            "components": list(self._components.keys()),
            "uptime": self.uptime.total_seconds()
        }
    
    def get_agent_info(self) -> Dict[str, Any]:
        """Informations de l'agent"""
        return {
            "id": self._name,
            "name": self._display_name,
            "version": self._version,
            "description": self._description,
            "status": self._status.value,
            "capabilities": self._agent_config["agent"]["capabilities"],
            "agents_count": len(self._agents),
            "cache_stats": self._cache_stats
        }
    
    async def _handle_custom_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Gestion des messages personnalisés"""
        msg_type = message.get("type", "")
        
        if msg_type == "register":
            return await self.register_agent(message.get("agent_data", {}))
        
        elif msg_type == "discover":
            return {"agents": await self.discover_agents(message.get("query", {}))}
        
        elif msg_type == "get_agent":
            agent = await self.get_agent(
                message["name"],
                message.get("version")
            )
            return {"agent": agent} if agent else {"error": "Agent not found"}
        
        elif msg_type == "get_versions":
            return {"versions": await self.get_versions(message["name"])}
        
        elif msg_type == "resolve_deps":
            return await self.resolve_dependencies(
                message["agent_name"],
                message.get("transitive", True)
            )
        
        elif msg_type == "get_dependents":
            return {"dependents": await self.get_dependents(message["agent_name"])}
        
        elif msg_type == "get_instance":
            instance = await self.get_instance(
                message["agent_name"],
                message.get("create_if_missing", False)
            )
            return {"instance": instance is not None, "cached": instance is not None}
        
        elif msg_type == "clear_cache":
            await self.clear_cache(message.get("agent_name"))
            return {"status": "cache cleared"}
        
        elif msg_type == "statistics":
            return await self.get_statistics()
        
        elif msg_type == "export":
            return await self.export_catalog(message.get("format", "json"))
        
        return {"status": "received", "type": msg_type}


# ------------------------------------------------------------------------
# FONCTIONS D'USINE
# ------------------------------------------------------------------------

def create_registry_agent(config_path: str = "") -> RegistryAgent:
    """Crée une instance du registry agent"""
    return RegistryAgent(config_path)


# ------------------------------------------------------------------------
# POINT D'ENTRÉE POUR EXÉCUTION DIRECTE
# ------------------------------------------------------------------------

if __name__ == "__main__":
    async def main():
        print("🗄️ TEST REGISTRY AGENT")
        print("="*60)
        
        agent = RegistryAgent()
        await agent.initialize()
        
        print(f"✅ Agent: {agent._display_name} v{agent._version}")
        print(f"✅ Statut: {agent._status.value}")
        print(f"✅ Agents enregistrés: {len(agent._agents)}")
        
        # Test d'enregistrement
        test_agent = {
            "name": "test_agent",
            "version": "1.0.0",
            "class_path": "agents.test.test_agent",
            "capabilities": ["test", "demo"],
            "dependencies": [],
            "tags": ["test", "example"],
            "description": "Agent de test"
        }
        
        result = await agent.register_agent(test_agent)
        if result.get("success"):
            print(f"\n✅ Agent test enregistré: {result['agent']['name']} v{result['agent']['version']}")
        
        # Test de découverte
        discovered = await agent.discover_agents({"capability": "test"})
        print(f"\n🔍 Agents avec capacité 'test': {len(discovered)}")
        
        # Test de dépendances
        deps = await agent.resolve_dependencies("test_agent")
        print(f"\n📊 Dépendances résolues: {deps['resolution_order']}")
        
        # Statistiques
        stats = await agent.get_statistics()
        print(f"\n📈 Statistiques: {stats['agents']['total']} agents, {stats['capabilities']['total']} capacités")
        
        print("\n" + "="*60)
        print("✅ REGISTRY AGENT OPÉRATIONNEL")
        print("="*60)
    
    asyncio.run(main())
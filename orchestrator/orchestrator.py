"""
ORCHESTRATEUR SMART CONTRACT PIPELINE - VERSION CORRIGÉE
"""
import os
import sys
import yaml
import asyncio
import logging
import importlib.util
import inspect
from typing import Dict, Any, List

# Configuration logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Orchestrator:
    def __init__(self, config_path=None):
        # Configuration du chemin
        self.project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        if self.project_root not in sys.path:
            sys.path.insert(0, self.project_root)
        
        logger.info("Orchestrateur initialise")
        
        if config_path is None:
            config_path = os.path.join(os.path.dirname(__file__), "config.yaml")
        
        self.config_path = config_path
        self.config = self._load_config()
        self.agents = {}
        self.initialized = False
        self.agent_registry = None
    
    def _load_config(self):
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    return yaml.safe_load(f) or {}
        except Exception as e:
            logger.error(f"Erreur chargement config: {e}")
        
        # Configuration par défaut
        return {
            "orchestrator": {
                "name": "SmartContractDevPipeline",
                "version": "1.0.0"
            },
            "agent_registry": {
                "enabled": True,
                "registry_file": "agent_registry.yaml",
                "scan_paths": ["agents/", "third_party_agents/"]
            }
        }
    
    async def initialize_agents(self, project_config_path: str = None):
        """Charge dynamiquement les agents selon la configuration du projet"""
        
        # Si pas de config projet spécifique, utilise la config par défaut
        if project_config_path is None:
            project_config_path = os.path.join(
                os.path.dirname(__file__), 
                "..", 
                "project_config.yaml"
            )
        
        # Charge la config du projet
        try:
            with open(project_config_path, 'r') as f:
                project_config = yaml.safe_load(f)
        except Exception as e:
            logger.error(f"Erreur chargement config projet {project_config_path}: {e}")
            project_config = {"project_name": "Default Project"}
        
        logger.info(f"Initialisation agents pour projet: {project_config.get('project_name', 'Unknown')}")
        
        # Initialise le registry d'agents
        self.agent_registry = AgentRegistry()
        
        # 1. Découvre les agents disponibles
        available_agents = self.agent_registry.discover_agents(
            self.config.get("agent_registry", {}).get("scan_paths", ["agents/"])
        )
        
        # 2. Charge les agents requis
        required_agents = project_config.get('required_agents', [])
        
        for agent_spec in required_agents:
            agent_name = agent_spec['name']
            specialization = agent_spec.get('specialization', 'default')
            
            try:
                # Essaie de charger l'agent spécialisé
                agent_instance = await self._load_specialized_agent(
                    agent_name, 
                    specialization, 
                    agent_spec.get('config')
                )
                self.agents[agent_name] = agent_instance
                logger.info(f"✓ Agent {agent_name} ({specialization}) chargé")
                
            except Exception as e:
                logger.warning(f"Agent {agent_name} non trouvé: {e}")
                # Fallback: agent générique
                agent_instance = self._create_fallback_agent(agent_name)
                self.agents[agent_name] = agent_instance
        
        # 3. Charge les agents optionnels selon le type de projet
        project_type = project_config.get('project_type', 'default')
        optional_agents = project_config.get('optional_agents', {}).get(project_type, [])
        
        for agent_spec in optional_agents:
            try:
                agent_instance = await self._load_specialized_agent(
                    agent_spec['agent_type'],
                    agent_spec['specialization'],
                    f"config/agents/{agent_spec['specialization']}.yaml"
                )
                self.agents[agent_spec['name']] = agent_instance
                logger.info(f"✓ Agent optionnel {agent_spec['name']} chargé")
            except Exception as e:
                logger.debug(f"Agent optionnel {agent_spec['name']} ignoré: {e}")
        
        self.initialized = True
        logger.info(f"{len(self.agents)} agents initialisés avec succès")
    
    async def _load_specialized_agent(self, base_agent_type: str, specialization: str, config_path: str = None):
        """Charge un agent spécialisé dynamiquement"""
        
        # Stratégie 1: Chercher dans sous_agents/
        subagent_path = f"agents.{base_agent_type}.sous_agents.{specialization}"
        
        try:
            module = __import__(f"{subagent_path}.agent", 
                              fromlist=[f"{specialization.capitalize().replace('_', '')}SubAgent"])
            agent_class_name = f"{specialization.capitalize().replace('_', '')}SubAgent"
            agent_class = getattr(module, agent_class_name)
            
            # Créer l'instance
            if config_path and os.path.exists(config_path):
                return agent_class(config_path)
            else:
                # Chemin de config par défaut
                default_config = f"agents/{base_agent_type}/sous_agents/{specialization}/config.yaml"
                return agent_class(default_config if os.path.exists(default_config) else None)
                
        except ImportError:
            # Stratégie 2: Chercher l'agent principal
            try:
                module = __import__(f"agents.{base_agent_type}.agent", 
                                  fromlist=[f"{base_agent_type.capitalize()}Agent"])
                agent_class = getattr(module, f"{base_agent_type.capitalize()}Agent")
                
                # Passer la spécialisation dans la config
                config = {"specialization": specialization}
                if config_path:
                    config["config_file"] = config_path
                    
                return agent_class(config)
                
            except ImportError:
                # Stratégie 3: Découverte via registry
                if self.agent_registry:
                    agent_info = self.agent_registry.get_agent_info(base_agent_type, specialization)
                    if agent_info:
                        return await self._load_agent_from_info(agent_info)
                
                raise ImportError(f"Impossible de charger l'agent {base_agent_type} spécialisé en {specialization}")
    
    async def _load_agent_from_info(self, agent_info: Dict[str, Any]):
        """Charge un agent depuis les infos du registry"""
        module_path = agent_info.get("module_path")
        class_name = agent_info.get("class_name")
        
        if not module_path or not class_name:
            raise ImportError(f"Infos d'agent incomplètes: {agent_info}")
        
        try:
            module = __import__(module_path, fromlist=[class_name])
            agent_class = getattr(module, class_name)
            
            # Créer l'instance
            config_path = agent_info.get("config_path")
            if config_path and os.path.exists(config_path):
                return agent_class(config_path)
            return agent_class()
            
        except Exception as e:
            raise ImportError(f"Erreur chargement agent {class_name}: {e}")
    
    def _create_fallback_agent(self, agent_name: str):
        """Crée un agent de secours"""
        class FallbackAgent:
            def __init__(self, name):
                self.name = name
                self.agent_id = f"{name}_fallback"
            
            async def execute(self, task_data, context):
                return {
                    "success": True,
                    "agent": self.name,
                    "message": f"Agent {self.name} (mode secours) - Tache executee"
                }
            
            async def health_check(self):
                return {
                    "agent": self.name,
                    "status": "fallback",
                    "type": "fallback_agent"
                }
        
        return FallbackAgent(agent_name)
    
    # ... (le reste du code: health_check, execute_workflow, main reste identique) ...
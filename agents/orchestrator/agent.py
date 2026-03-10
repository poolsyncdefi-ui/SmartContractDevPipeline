"""
Orchestrator Agent - Orchestration des workflows et sprints
Version corrigée avec compatibilité infrastructure existante
Version: 2.0.1
"""

import os
import sys
import yaml
import asyncio
import json
import random
import traceback
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Any, Optional, Union, Set
from pathlib import Path
from collections import defaultdict

# Import compatible avec l'infrastructure existante
from agents.base_agent.base_agent import BaseAgent, AgentStatus


# =====================================================================
# CONSTANTES
# =====================================================================

DEFAULT_CONFIG = {
    "sprint_config": {
        "enabled": True,
        "default_strategy": "largeur_dabord",
        "max_iterations_per_fragment": 3,
        "reports_path": "./reports/sprints/",
        "timeout_per_fragment": 300
    },
    "workflow_config": {
        "continue_on_error": False,
        "max_concurrent_steps": 5,
        "default_timeout": 300
    },
    "paths": {
        "specs_dir": "./specs/projects/",
        "reports_dir": "./reports/sprints/",
        "artifacts_dir": "./artifacts/workflows/"
    }
}


# =====================================================================
# ÉNUMÉRATIONS
# =====================================================================

class WorkflowStatus(Enum):
    """Statuts d'un workflow"""
    PENDING = "pending"
    PLANNING = "planning"
    READY = "ready"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class StepStatus(Enum):
    """Statuts d'une étape"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    BLOCKED = "blocked"


class DomainType(Enum):
    """Types de domaines supportés"""
    SMART_CONTRACT = "smart_contract"
    BACKEND = "backend"
    FRONTEND = "frontend"
    DATABASE = "database"
    DEVOPS = "devops"
    MONITORING = "monitoring"
    DOCUMENTATION = "documentation"


class FragmentStatus(Enum):
    """Statuts d'un fragment"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    VALIDATED = "validated"
    FAILED = "failed"
    BLOCKED = "blocked"


# =====================================================================
# EXCEPTIONS SPÉCIFIQUES
# =====================================================================

class WorkflowError(Exception):
    """Erreur lors de l'exécution d'un workflow"""
    pass


class SprintError(Exception):
    """Erreur lors de l'exécution d'un sprint"""
    pass


class StepExecutionError(Exception):
    """Erreur lors de l'exécution d'une étape"""
    pass


class FragmentExecutionError(Exception):
    """Erreur lors de l'exécution d'un fragment"""
    pass


# =====================================================================
# CLASSES DE BASE
# =====================================================================

class WorkflowStep:
    """Étape d'un workflow"""
    
    def __init__(self, 
                 name: str,
                 agent_type: str,
                 task_type: str,
                 parameters: Dict[str, Any] = None,
                 depends_on: List[str] = None,
                 timeout: int = 300,
                 retry_count: int = 0,
                 max_retries: int = 3,
                 metadata: Dict[str, Any] = None):
        
        self.id = f"step_{int(datetime.now().timestamp())}_{name}"
        self.name = name
        self.agent_type = agent_type
        self.task_type = task_type
        self.parameters = parameters or {}
        self.depends_on = depends_on or []
        self.timeout = timeout
        self.retry_count = retry_count
        self.max_retries = max_retries
        self.metadata = metadata or {}
        self.status = StepStatus.PENDING
        self.result = None
        self.error = None
        self.started_at = None
        self.completed_at = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertit l'étape en dictionnaire"""
        return {
            "id": self.id,
            "name": self.name,
            "agent_type": self.agent_type,
            "task_type": self.task_type,
            "parameters": self.parameters,
            "depends_on": self.depends_on,
            "status": self.status.value,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
            "metadata": self.metadata,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "error": self.error
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'WorkflowStep':
        """Crée une étape depuis un dictionnaire"""
        step = cls(
            name=data["name"],
            agent_type=data["agent_type"],
            task_type=data["task_type"],
            parameters=data.get("parameters", {}),
            depends_on=data.get("depends_on", []),
            timeout=data.get("timeout", 300),
            max_retries=data.get("max_retries", 3),
            metadata=data.get("metadata", {})
        )
        step.id = data.get("id", step.id)
        step.status = StepStatus(data.get("status", "pending"))
        step.retry_count = data.get("retry_count", 0)
        step.error = data.get("error")
        return step


class Workflow:
    """Workflow complet"""
    
    def __init__(self, 
                 name: str, 
                 workflow_type: str = "standard",
                 metadata: Dict[str, Any] = None):
        
        self.id = f"workflow_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.name = name
        self.workflow_type = workflow_type
        self.metadata = metadata or {}
        self.status = WorkflowStatus.PENDING
        self.steps: List[WorkflowStep] = []
        self.steps_by_id: Dict[str, WorkflowStep] = {}
        self.created_at = datetime.now()
        self.started_at = None
        self.completed_at = None
        self.context: Dict[str, Any] = {}
        self.results: Dict[str, Any] = {}
        self.artifacts: List[str] = []
        self.report_path = None
        self.error = None
    
    def add_step(self, step: WorkflowStep) -> None:
        """Ajoute une étape au workflow"""
        self.steps.append(step)
        self.steps_by_id[step.id] = step
    
    def get_step(self, step_identifier: str) -> Optional[WorkflowStep]:
        """Récupère une étape par son nom ou son ID"""
        # Chercher par ID d'abord
        if step_identifier in self.steps_by_id:
            return self.steps_by_id[step_identifier]
        
        # Sinon chercher par nom
        for step in self.steps:
            if step.name == step_identifier:
                return step
        return None
    
    def get_step_by_name(self, name: str) -> Optional[WorkflowStep]:
        """Récupère une étape par son nom"""
        return self.get_step(name)
    
    def update_step_status(self, step_id: str, status: StepStatus, 
                          result: Any = None, error: str = None) -> None:
        """Met à jour le statut d'une étape"""
        step = self.steps_by_id.get(step_id)
        if step:
            step.status = status
            if result is not None:
                step.result = result
            if error:
                step.error = error
            if status == StepStatus.RUNNING:
                step.started_at = datetime.now()
            elif status in [StepStatus.COMPLETED, StepStatus.FAILED, StepStatus.SKIPPED]:
                step.completed_at = datetime.now()
    
    def is_completed(self) -> bool:
        """Vérifie si le workflow est terminé"""
        return self.status in [WorkflowStatus.COMPLETED, WorkflowStatus.FAILED, WorkflowStatus.CANCELLED]
    
    def get_pending_steps(self) -> List[WorkflowStep]:
        """Retourne les étapes en attente"""
        return [s for s in self.steps if s.status == StepStatus.PENDING]
    
    def get_running_steps(self) -> List[WorkflowStep]:
        """Retourne les étapes en cours"""
        return [s for s in self.steps if s.status == StepStatus.RUNNING]
    
    def get_completed_steps(self) -> List[WorkflowStep]:
        """Retourne les étapes terminées"""
        return [s for s in self.steps if s.status == StepStatus.COMPLETED]
    
    def get_failed_steps(self) -> List[WorkflowStep]:
        """Retourne les étapes en échec"""
        return [s for s in self.steps if s.status == StepStatus.FAILED]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertit le workflow en dictionnaire"""
        return {
            "id": self.id,
            "name": self.name,
            "type": self.workflow_type,
            "status": self.status.value,
            "steps": [s.to_dict() for s in self.steps],
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "results": self.results,
            "artifacts": self.artifacts,
            "error": self.error
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Workflow':
        """Crée un workflow depuis un dictionnaire"""
        workflow = cls(
            name=data["name"],
            workflow_type=data.get("type", "standard"),
            metadata=data.get("metadata", {})
        )
        workflow.id = data.get("id", workflow.id)
        workflow.status = WorkflowStatus(data.get("status", "pending"))
        workflow.results = data.get("results", {})
        workflow.artifacts = data.get("artifacts", [])
        workflow.error = data.get("error")
        
        # Restaurer les étapes
        for step_data in data.get("steps", []):
            step = WorkflowStep.from_dict(step_data)
            workflow.add_step(step)
        
        return workflow


# =====================================================================
# SPRINT MANAGER
# =====================================================================

class SprintManager:
    """
    Gestionnaire de sprints multi-domaines
    Coordonne le développement parallèle sur tous les aspects du projet
    """
    
    def __init__(self, config: Dict[str, Any], logger=None):
        self.config = config
        self.current_sprint = None
        self.fragments: Dict[str, Dict] = {}
        self.dependency_graph: Dict[str, List[str]] = {}
        self.results: Dict[str, Any] = {}
        self.logger = logger or print
        
        self.metrics = {
            "sprints_completed": 0,
            "fragments_total": 0,
            "fragments_completed": 0,
            "fragments_failed": 0,
            "iterations_total": 0,
            "avg_iterations_per_fragment": 0.0,
            "success_rate": 0.0,
            
            # Métriques par domaine
            "by_domain": {
                "smart_contract": {"total": 0, "completed": 0, "failed": 0},
                "backend": {"total": 0, "completed": 0, "failed": 0},
                "frontend": {"total": 0, "completed": 0, "failed": 0},
                "database": {"total": 0, "completed": 0, "failed": 0},
                "devops": {"total": 0, "completed": 0, "failed": 0},
                "monitoring": {"total": 0, "completed": 0, "failed": 0},
                "documentation": {"total": 0, "completed": 0, "failed": 0}
            }
        }
    
    def set_logger(self, logger):
        """Définit le logger"""
        self.logger = logger
    
    def _log_info(self, msg):
        """Log niveau info"""
        self.logger(f"ℹ️ {msg}")
    
    def _log_error(self, msg):
        """Log niveau erreur"""
        self.logger(f"❌ {msg}")
    
    def _log_warning(self, msg):
        """Log niveau avertissement"""
        self.logger(f"⚠️ {msg}")
    
    def _log_debug(self, msg):
        """Log niveau debug"""
        self.logger(f"🔍 {msg}")
    
    def load_specs(self, spec_file: str) -> Dict[str, Any]:
        """Charge les spécifications depuis un fichier JSON"""
        self._log_info(f"Chargement des spécifications: {spec_file}")
        
        try:
            with open(spec_file, 'r', encoding='utf-8') as f:
                specs = json.load(f)
        except FileNotFoundError:
            self._log_error(f"Fichier non trouvé: {spec_file}")
            # Retourner des spécifications par défaut pour les tests
            specs = self._get_default_specs()
        except Exception as e:
            self._log_error(f"Erreur chargement: {e}")
            specs = self._get_default_specs()
        
        # Indexer les fragments par ID
        for fragment in specs.get("fragments", []):
            self.fragments[fragment["id"]] = fragment
            self.metrics["fragments_total"] += 1
            
            # Statistiques par domaine
            domain = fragment.get("domain", "unknown")
            if domain in self.metrics["by_domain"]:
                self.metrics["by_domain"][domain]["total"] += 1
        
        # Construire le graphe de dépendances
        for dep in specs.get("dependencies", []):
            from_id = dep["from"]
            to_id = dep["to"]
            
            if from_id not in self.dependency_graph:
                self.dependency_graph[from_id] = []
            self.dependency_graph[from_id].append(to_id)
        
        self.current_sprint = {
            "id": specs.get("sprint", "SPRINT-000"),
            "name": specs.get("name", "Sans nom"),
            "strategy": specs.get("strategy", "largeur_dabord"),
            "fragments": list(self.fragments.keys()),
            "dependencies": self.dependency_graph,
            "specs": specs
        }
        
        return specs
    
    def _get_default_specs(self) -> Dict[str, Any]:
        """Retourne des spécifications par défaut pour les tests"""
        return {
            "sprint": "SPRINT-001",
            "name": "Sprint de test",
            "strategy": "largeur_dabord",
            "fragments": [
                {
                    "id": "TEST_001",
                    "domain": "smart_contract",
                    "name": "Fragment test",
                    "language": "solidity",
                    "complexity": 2
                }
            ],
            "dependencies": []
        }
    
    def plan_sprint(self) -> List[Dict]:
        """Planifie l'ordre d'exécution des fragments"""
        if not self.current_sprint:
            return []
        
        strategy = self.current_sprint["strategy"]
        
        if strategy == "largeur_dabord":
            return self._plan_largeur()
        elif strategy == "profondeur_dabord":
            return self._plan_profondeur()
        else:
            return self._resolve_dependencies()
    
    def _plan_largeur(self) -> List[Dict]:
        """Planification en largeur : tous les domaines en parallèle"""
        fragments_by_domain = defaultdict(list)
        
        for fragment_id, fragment in self.fragments.items():
            domain = fragment.get("domain", "unknown")
            fragments_by_domain[domain].append(fragment)
        
        # Trier par complexité au sein de chaque domaine
        for domain in fragments_by_domain:
            fragments_by_domain[domain].sort(
                key=lambda x: x.get("complexity", 5)
            )
        
        # Entrelacer les fragments simples de tous les domaines
        plan = []
        max_len = max((len(f) for f in fragments_by_domain.values()), default=0)
        
        for i in range(max_len):
            for domain in fragments_by_domain:
                if i < len(fragments_by_domain[domain]):
                    plan.append(fragments_by_domain[domain][i])
        
        return plan
    
    def _plan_profondeur(self) -> List[Dict]:
        """Planification en profondeur : domaine par domaine"""
        # Priorité : smart_contract → backend → frontend → database → devops
        priority = ["smart_contract", "backend", "frontend", "database", "devops", "monitoring", "documentation"]
        
        plan = []
        for domain in priority:
            domain_fragments = [
                f for f in self.fragments.values()
                if f.get("domain") == domain
            ]
            domain_fragments.sort(key=lambda x: x.get("complexity", 5))
            plan.extend(domain_fragments)
        
        return plan
    
    def _resolve_dependencies(self) -> List[Dict]:
        """Résout le graphe de dépendances (tri topologique)"""
        visited = set()
        order = []
        
        def dfs(fragment_id: str) -> None:
            if fragment_id in visited:
                return
            visited.add(fragment_id)
            
            for dep in self.dependency_graph.get(fragment_id, []):
                dfs(dep)
            
            if fragment_id in self.fragments:
                order.append(self.fragments[fragment_id])
        
        for fragment_id in self.fragments:
            if fragment_id not in visited:
                dfs(fragment_id)
        
        return order


# =====================================================================
# ORCHESTRATOR AGENT
# =====================================================================

class OrchestratorAgent(BaseAgent):
    """
    Agent orchestrateur principal
    Gère l'exécution des workflows et des sprints
    """
    
    def __init__(self, config_path: str = ""):
        """Initialise l'orchestrateur"""
        super().__init__(config_path)
        
        self._logger.info("🚀 Orchestrator Agent créé")
        
        # Charger la configuration
        self._load_configuration()
        
        # État interne
        self._agents: Dict[str, Any] = {}
        self._workflows: Dict[str, Workflow] = {}
        self._current_workflow: Optional[Workflow] = None
        self._sprint_manager: Optional[SprintManager] = None
        self._initialized = False
        
        # Statistiques
        self._stats = {
            "workflows_executed": 0,
            "workflows_completed": 0,
            "workflows_failed": 0,
            "steps_executed": 0,
            "steps_failed": 0,
            "sprints_completed": 0,
            "fragments_executed": 0,
            "start_time": datetime.now()
        }
        
        # Composants
        self._components = {}
    
    def _load_configuration(self):
        """Charge la configuration depuis le fichier YAML"""
        try:
            if self._config_path and os.path.exists(self._config_path):
                with open(self._config_path, 'r', encoding='utf-8') as f:
                    file_config = yaml.safe_load(f) or {}
                
                # Merge avec la config par défaut
                self._agent_config = self._merge_configs(DEFAULT_CONFIG, file_config)
                self._logger.info(f"✅ Configuration chargée depuis {self._config_path}")
            else:
                self._logger.warning("⚠️ Fichier de configuration non trouvé, utilisation des valeurs par défaut")
                self._agent_config = DEFAULT_CONFIG.copy()
        except Exception as e:
            self._logger.error(f"❌ Erreur chargement config: {e}")
            self._agent_config = DEFAULT_CONFIG.copy()
    
    def _merge_configs(self, default: Dict, override: Dict) -> Dict:
        """Fusionne deux configurations récursivement"""
        result = default.copy()
        
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_configs(result[key], value)
            else:
                result[key] = value
        
        return result
    
    async def initialize(self) -> bool:
        """Initialisation asynchrone"""
        try:
            self._status = AgentStatus.INITIALIZING
            self._logger.info("Initialisation de l'orchestrateur...")
            
            # Créer les répertoires nécessaires
            await self._ensure_directories()
            
            # Initialiser les composants
            await self._initialize_components()
            
            # Initialiser le sprint manager
            self._sprint_manager = SprintManager(self._agent_config.get("sprint_config", {}))
            self._sprint_manager.set_logger(self._logger.info)
            
            self._initialized = True
            self._status = AgentStatus.READY
            self._logger.info("✅ Orchestrateur prêt")
            return True
            
        except Exception as e:
            self._logger.error(f"❌ Erreur initialisation: {e}")
            self._logger.error(traceback.format_exc())
            self._status = AgentStatus.ERROR
            return False
    
    async def _ensure_directories(self):
        """Crée les répertoires nécessaires"""
        paths = self._agent_config.get("paths", {})
        for path_name, path_value in paths.items():
            path = Path(path_value)
            path.mkdir(parents=True, exist_ok=True)
            self._logger.debug(f"📁 Répertoire créé/vérifié: {path}")
    
    async def _initialize_components(self):
        """Initialise les composants"""
        self._logger.info("Initialisation des composants...")
        
        self._components = {
            "workflow_engine": True,
            "sprint_manager": True,
            "agent_registry": False  # Sera activé quand le registry sera disponible
        }
        
        self._logger.info(f"✅ Composants: {list(self._components.keys())}")
        return self._components
    
    async def generate_project_spec(self, 
                                   project_name: str, 
                                   project_type: str = "defi",
                                   output_dir: Optional[str] = None) -> str:
        """
        Génère un fichier de spécification complet pour un projet
        
        Args:
            project_name: Nom du projet
            project_type: Type de projet (defi, nft, gaming, dao)
            output_dir: Répertoire de sortie (optionnel)
        
        Returns:
            Chemin vers le fichier JSON généré
        """
        self._logger.info(f"📋 Génération de spécification pour projet: {project_name} (type: {project_type})")
        
        # Template de base selon le type de projet
        templates = {
            "defi": self._get_defi_template,
            "nft": self._get_nft_template,
            "gaming": self._get_gaming_template,
            "dao": self._get_dao_template
        }
        
        template_func = templates.get(project_type, self._get_defi_template)
        spec = template_func(project_name)
        
        # Déterminer le répertoire de sortie
        if output_dir:
            specs_dir = Path(output_dir)
        else:
            specs_dir = Path(self._agent_config.get("paths", {}).get("specs_dir", "./specs/projects/"))
        
        specs_dir.mkdir(parents=True, exist_ok=True)
        
        # Générer le nom du fichier
        safe_name = project_name.lower().replace(' ', '_')
        filename = f"{safe_name}_{project_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        filepath = specs_dir / filename
        
        # Sauvegarder le fichier
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(spec, f, indent=2, ensure_ascii=False)
        
        self._logger.info(f"✅ Spécification projet générée: {filepath}")
        return str(filepath)

    async def _get_agent(self, agent_name: str) -> Optional[Any]:
        """
        Récupère une instance d'agent depuis le registry
        
        Args:
            agent_name: Nom de l'agent à récupérer
            
        Returns:
            Instance de l'agent ou None si non disponible
        """
        self._logger.debug(f"🔍 Recherche de l'agent: {agent_name}")
        
        try:
            # Essayer d'importer le registry
            from agents.registry.agent import RegistryAgent
            
            # Créer une instance du registry
            registry = RegistryAgent()
            await registry.initialize()
            
            # Récupérer l'agent depuis le registry
            agent_info = await registry.get_agent(agent_name)
            
            if agent_info:
                # Importer dynamiquement la classe
                module_path = agent_info.get("module_path", f"agents.{agent_name}.agent")
                class_name = agent_info.get("class_name", f"{agent_name.capitalize()}Agent")
                
                module = __import__(module_path, fromlist=[class_name])
                agent_class = getattr(module, class_name)
                
                # Créer et initialiser l'instance
                agent_instance = agent_class()
                await agent_instance.initialize()
                
                self._logger.info(f"✅ Agent {agent_name} chargé depuis le registry")
                return agent_instance
                
        except ImportError:
            self._logger.warning(f"⚠️ Registry non disponible, utilisation du mode simulation")
        except Exception as e:
            self._logger.error(f"❌ Erreur chargement agent {agent_name}: {e}")
        
        # Mode simulation
        self._logger.warning(f"⚠️ Agent {agent_name} non disponible (simulation)")
        return None

    async def prepare_and_execute_sprint(self, 
                                        project_name: str, 
                                        project_type: str = "defi",
                                        strategy: str = "largeur_dabord") -> Dict[str, Any]:
        """
        Prépare et exécute un sprint complet :
        1. Génère la spec globale
        2. Appelle architect pour découpage en fragments
        3. Exécute le sprint
        
        Args:
            project_name: Nom du projet
            project_type: Type de projet
            strategy: Stratégie de sprint
        
        Returns:
            Rapport complet du sprint
        """
        self._logger.info(f"🚀 Préparation du sprint pour projet: {project_name} (stratégie: {strategy})")
        
        # Étape 1: Générer la spec globale
        spec_file = await self.generate_project_spec(project_name, project_type)
        
        # Étape 2: Appeler l'agent architect pour le découpage
        architect_agent = await self._get_agent("architect")
        if not architect_agent:
            self._logger.warning("⚠️ Agent architect non disponible, utilisation du découpage par défaut")
            fragments_info = {"by_domain": {}, "metadata": {"total_fragments": 0}}
        else:
            # Charger la spec
            with open(spec_file, 'r') as f:
                global_spec = json.load(f)
            
            # Demander le découpage
            fragments_info = await architect_agent.split_spec_into_fragments(global_spec, strategy)
        
        # Étape 3: Exécuter le sprint
        report = await self.execute_sprint(spec_file)
        
        # Ajouter les infos de découpage au rapport
        report["fragments_info"] = {
            "total": fragments_info["metadata"]["total_fragments"],
            "by_domain": {k: len(v) for k, v in fragments_info["by_domain"].items()},
            "estimated_sprints": fragments_info["metadata"].get("estimated_sprints", 1)
        }
        
        # Mettre à jour les métriques
        self._stats["sprints_completed"] += 1
        
        return report

    def _get_defi_template(self, project_name: str) -> Dict:
        """Template pour projet DeFi"""
        safe_name = project_name.lower().replace(' ', '_')
        symbol = project_name[:5].upper()
        
        return {
            "project": project_name,
            "type": "defi",
            "version": "1.0.0",
            "generated_at": datetime.now().isoformat(),
            "description": "Plateforme DeFi complète avec token, staking, et interface web",
            "domains": ["smart_contract", "backend", "frontend", "database", "devops", "documentation"],
            "fragments": [
                {
                    "id": f"{safe_name}_SC_001",
                    "domain": "smart_contract",
                    "name": "Token ERC20",
                    "description": "Token standard avec mint/burn",
                    "language": "solidity",
                    "version": "0.8.19",
                    "framework": "foundry",
                    "complexity": 2,
                    "dependencies": ["openzeppelin/contracts@4.9.0"],
                    "specification": {
                        "contract_name": f"{safe_name}Token",
                        "symbol": symbol,
                        "features": ["mint", "burn", "transfer", "approve"]
                    },
                    "tests": {
                        "unit": 8,
                        "integration": 3
                    }
                },
                {
                    "id": f"{safe_name}_SC_002",
                    "domain": "smart_contract",
                    "name": "Staking Pool",
                    "description": "Pool de staking avec récompenses",
                    "language": "solidity",
                    "version": "0.8.19",
                    "framework": "foundry",
                    "complexity": 4,
                    "depends_on": [f"{safe_name}_SC_001"],
                    "specification": {
                        "contract_name": f"{safe_name}Staking",
                        "features": ["stake", "unstake", "claim", "compound"]
                    },
                    "tests": {
                        "unit": 12,
                        "integration": 5
                    }
                },
                {
                    "id": f"{safe_name}_BE_001",
                    "domain": "backend",
                    "name": "API FastAPI",
                    "description": "API REST pour le projet",
                    "language": "python",
                    "version": "3.11",
                    "framework": "fastapi",
                    "complexity": 3,
                    "depends_on": [f"{safe_name}_SC_001", f"{safe_name}_DB_001"],
                    "specification": {
                        "endpoints": ["/balance", "/transfer", "/stake", "/rewards"],
                        "database": "postgresql",
                        "cache": "redis"
                    },
                    "tests": {
                        "unit": 10,
                        "integration": 4
                    }
                },
                {
                    "id": f"{safe_name}_FE_001",
                    "domain": "frontend",
                    "name": "Interface React",
                    "description": "Application React avec WalletConnect",
                    "language": "typescript",
                    "version": "5.0",
                    "framework": "nextjs",
                    "complexity": 3,
                    "depends_on": [f"{safe_name}_BE_001"],
                    "specification": {
                        "pages": ["dashboard", "staking", "admin"],
                        "wallets": ["metamask", "walletconnect"]
                    },
                    "tests": {
                        "unit": 8,
                        "e2e": 3
                    }
                },
                {
                    "id": f"{safe_name}_DB_001",
                    "domain": "database",
                    "name": "Schéma PostgreSQL",
                    "description": "Base de données du projet",
                    "language": "sql",
                    "version": "15",
                    "framework": "alembic",
                    "complexity": 2,
                    "specification": {
                        "tables": ["users", "transactions", "staking_positions"]
                    }
                },
                {
                    "id": f"{safe_name}_DO_001",
                    "domain": "devops",
                    "name": "Infrastructure Docker",
                    "description": "Déploiement conteneurisé",
                    "language": "yaml",
                    "version": "docker-compose-v3",
                    "complexity": 3,
                    "depends_on": [f"{safe_name}_BE_001", f"{safe_name}_FE_001", f"{safe_name}_DB_001"],
                    "specification": {
                        "services": ["postgres", "redis", "backend", "frontend", "nginx"],
                        "environments": ["development", "staging", "production"]
                    }
                },
                {
                    "id": f"{safe_name}_DOC_001",
                    "domain": "documentation",
                    "name": "Documentation",
                    "description": "Documentation complète",
                    "language": "markdown",
                    "framework": "mkdocs",
                    "complexity": 2,
                    "depends_on": ["*"],
                    "specification": {
                        "sections": ["introduction", "architecture", "api", "deployment", "user_guide"]
                    }
                }
            ],
            "dependencies": [
                {"from": f"{safe_name}_SC_002", "to": f"{safe_name}_SC_001"},
                {"from": f"{safe_name}_BE_001", "to": f"{safe_name}_SC_001"},
                {"from": f"{safe_name}_BE_001", "to": f"{safe_name}_DB_001"},
                {"from": f"{safe_name}_FE_001", "to": f"{safe_name}_BE_001"},
                {"from": f"{safe_name}_DO_001", "to": f"{safe_name}_BE_001"},
                {"from": f"{safe_name}_DO_001", "to": f"{safe_name}_FE_001"},
                {"from": f"{safe_name}_DO_001", "to": f"{safe_name}_DB_001"},
                {"from": f"{safe_name}_DOC_001", "to": "*"}
            ]
        }

    def _get_nft_template(self, project_name: str) -> Dict:
        """Template pour projet NFT"""
        template = self._get_defi_template(project_name)
        template["type"] = "nft"
        template["description"] = "Collection NFT avec mint, marketplace et royalties"
        
        # Adapter pour NFT
        safe_name = project_name.lower().replace(' ', '_')
        for fragment in template["fragments"]:
            if fragment["domain"] == "smart_contract" and "SC_001" in fragment["id"]:
                fragment["name"] = "NFT ERC721"
                fragment["specification"]["contract_name"] = f"{safe_name}NFT"
                fragment["specification"]["features"] = ["mint", "transfer", "burn", "royalties"]
            elif fragment["domain"] == "smart_contract" and "SC_002" in fragment["id"]:
                fragment["name"] = "Marketplace"
                fragment["specification"]["features"] = ["list", "buy", "offer", "auction"]
        
        return template

    def _get_gaming_template(self, project_name: str) -> Dict:
        """Template pour projet Gaming"""
        template = self._get_defi_template(project_name)
        template["type"] = "gaming"
        template["description"] = "Jeu Web3 avec tokens, items et marketplace"
        
        # Adapter pour Gaming
        safe_name = project_name.lower().replace(' ', '_')
        for fragment in template["fragments"]:
            if fragment["domain"] == "smart_contract" and "SC_001" in fragment["id"]:
                fragment["name"] = "Game Token ERC20"
            elif fragment["domain"] == "smart_contract" and "SC_002" in fragment["id"]:
                fragment["name"] = "Items NFT"
                fragment["specification"]["features"] = ["mint", "transfer", "burn", "upgrade"]
        
        return template

    def _get_dao_template(self, project_name: str) -> Dict:
        """Template pour projet DAO"""
        template = self._get_defi_template(project_name)
        template["type"] = "dao"
        template["description"] = "DAO avec gouvernance, treasury et votes"
        
        # Adapter pour DAO
        safe_name = project_name.lower().replace(' ', '_')
        for fragment in template["fragments"]:
            if fragment["domain"] == "smart_contract" and "SC_001" in fragment["id"]:
                fragment["name"] = "Governance Token"
            elif fragment["domain"] == "smart_contract" and "SC_002" in fragment["id"]:
                fragment["name"] = "DAO Contract"
                fragment["specification"]["features"] = ["propose", "vote", "execute", "treasury"]
        
        return template
        
    # =================================================================
    # GESTION DES WORKFLOWS
    # =================================================================
    
    async def create_workflow(self, 
                             name: str,
                             steps: List[Dict[str, Any]] = None,
                             workflow_type: str = "standard",
                             metadata: Dict[str, Any] = None) -> Workflow:
        """
        Crée un nouveau workflow
        
        Args:
            name: Nom du workflow
            steps: Liste des étapes
            workflow_type: Type de workflow
            metadata: Métadonnées additionnelles
            
        Returns:
            Workflow créé
        """
        self._logger.info(f"📋 Création du workflow: {name} (type: {workflow_type})")
        
        workflow = Workflow(name, workflow_type, metadata)
        
        if steps:
            for i, step_config in enumerate(steps):
                step = WorkflowStep(
                    name=step_config["name"],
                    agent_type=step_config["agent"],
                    task_type=step_config["task"],
                    parameters=step_config.get("parameters", {}),
                    depends_on=step_config.get("depends_on", []),
                    timeout=step_config.get("timeout", 300),
                    max_retries=step_config.get("max_retries", 3),
                    metadata=step_config.get("metadata", {"order": i})
                )
                workflow.add_step(step)
        
        self._workflows[workflow.id] = workflow
        workflow.status = WorkflowStatus.READY
        
        self._logger.info(f"✅ Workflow créé: {workflow.id} ({len(workflow.steps)} étapes)")
        
        return workflow
    
    async def execute_workflow(self, workflow_id: str) -> Dict[str, Any]:
        """
        Exécute un workflow
        
        Args:
            workflow_id: ID du workflow
            
        Returns:
            Résultats du workflow
        """
        if workflow_id not in self._workflows:
            raise WorkflowError(f"Workflow {workflow_id} non trouvé")
        
        workflow = self._workflows[workflow_id]
        
        if workflow.is_completed():
            self._logger.warning(f"⚠️ Workflow {workflow_id} déjà terminé")
            return workflow.to_dict()
        
        workflow.status = WorkflowStatus.RUNNING
        workflow.started_at = datetime.now()
        
        self._logger.info(f"🚀 Exécution du workflow: {workflow.name} ({workflow_id})")
        self._stats["workflows_executed"] += 1
        
        try:
            # Résoudre l'ordre d'exécution
            execution_order = self._resolve_execution_order(workflow)
            self._logger.info(f"📊 Ordre d'exécution: {[s.name for s in execution_order]}")
            
            # Exécuter les étapes
            results = {}
            
            for step in execution_order:
                # Vérifier les dépendances
                deps_satisfied = all(
                    results.get(dep, {}).get("success", False)
                    for dep in step.depends_on
                )
                
                if not deps_satisfied:
                    self._logger.error(f"❌ Étape {step.name}: dépendances non satisfaites")
                    workflow.update_step_status(step.id, StepStatus.BLOCKED)
                    workflow.status = WorkflowStatus.FAILED
                    workflow.error = f"Étape {step.name} bloquée par dépendances"
                    break
                
                # Exécuter l'étape
                result = await self._execute_step(step, workflow.context)
                results[step.name] = result
                workflow.results[step.name] = result
                self._stats["steps_executed"] += 1
                
                if not result.get("success", False):
                    self._stats["steps_failed"] += 1
                    
                    if not self._agent_config.get("workflow_config", {}).get("continue_on_error", False):
                        workflow.status = WorkflowStatus.FAILED
                        workflow.error = f"Étape {step.name} en échec"
                        break
            
            # Finaliser le workflow
            workflow.completed_at = datetime.now()
            
            if all(s.status == StepStatus.COMPLETED for s in workflow.steps):
                workflow.status = WorkflowStatus.COMPLETED
                self._stats["workflows_completed"] += 1
                self._logger.info(f"🎉 Workflow {workflow.name} terminé avec succès")
            else:
                if workflow.status != WorkflowStatus.FAILED:
                    workflow.status = WorkflowStatus.FAILED
                self._stats["workflows_failed"] += 1
                self._logger.warning(f"⚠️ Workflow {workflow.name} terminé avec des échecs")
            
            # Sauvegarder les résultats
            await self._save_workflow_artifacts(workflow)
            
            return workflow.to_dict()
            
        except Exception as e:
            self._logger.error(f"❌ Erreur workflow: {e}")
            self._logger.error(traceback.format_exc())
            workflow.status = WorkflowStatus.FAILED
            workflow.error = str(e)
            workflow.completed_at = datetime.now()
            self._stats["workflows_failed"] += 1
            
            return workflow.to_dict()
    
    def _resolve_execution_order(self, workflow: Workflow) -> List[WorkflowStep]:
        """Résout l'ordre d'exécution des étapes (tri topologique)"""
        # Construire le graphe des dépendances
        graph = {step.name: set(step.depends_on) for step in workflow.steps}
        
        # Tri topologique
        visited = set()
        order = []
        
        def dfs(node_name: str) -> None:
            if node_name in visited:
                return
            visited.add(node_name)
            
            step = workflow.get_step_by_name(node_name)
            if step:
                for dep in step.depends_on:
                    if dep not in visited:
                        dfs(dep)
                
                order.append(step)
        
        for step in workflow.steps:
            if step.name not in visited:
                dfs(step.name)
        
        return order
    
    async def _execute_step(self, step: WorkflowStep, context: Dict) -> Dict[str, Any]:
        """Exécute une étape du workflow"""
        self._logger.info(f"⚙️ Exécution: {step.name} ({step.agent_type}.{step.task_type})")
        
        step.status = StepStatus.RUNNING
        step.started_at = datetime.now()
        
        try:
            # TODO: Implémenter l'appel réel aux agents
            # Simulation pour l'instant
            await asyncio.sleep(0.5)
            
            step.status = StepStatus.COMPLETED
            step.completed_at = datetime.now()
            step.result = {"message": "Étape exécutée avec succès", "timestamp": datetime.now().isoformat()}
            
            self._logger.debug(f"✅ Étape {step.name} terminée")
            
            return {
                "success": True,
                "step": step.name,
                "result": step.result
            }
            
        except Exception as e:
            step.status = StepStatus.FAILED
            step.error = str(e)
            step.completed_at = datetime.now()
            
            self._logger.error(f"❌ Étape {step.name} échouée: {e}")
            
            return {
                "success": False,
                "step": step.name,
                "error": str(e)
            }
    
    async def _save_workflow_artifacts(self, workflow: Workflow) -> None:
        """Sauvegarde les artefacts du workflow"""
        artifacts_dir = Path(self._agent_config.get("paths", {}).get("artifacts_dir", "./artifacts/workflows/"))
        artifacts_dir.mkdir(parents=True, exist_ok=True)
        
        # Sauvegarder le workflow
        workflow_file = artifacts_dir / f"{workflow.id}.json"
        with open(workflow_file, 'w', encoding='utf-8') as f:
            json.dump(workflow.to_dict(), f, indent=2, ensure_ascii=False)
        
        workflow.artifacts.append(str(workflow_file))
        self._logger.debug(f"💾 Workflow sauvegardé: {workflow_file}")
    
    # =================================================================
    # GESTION DES SPRINTS
    # =================================================================

    def _generate_sprint_report(self, specs: Dict, results: List[Dict], metrics: Dict) -> Dict:
        """
        Génère un rapport détaillé du sprint
        
        Args:
            specs: Spécifications originales
            results: Résultats des fragments
            metrics: Métriques du sprint
        
        Returns:
            Rapport complet
        """
        # Compter les succès par domaine
        by_domain = {}
        for result in results:
            domain = result.get("domain", "unknown")
            if domain not in by_domain:
                by_domain[domain] = {"total": 0, "success": 0, "failed": 0}
            
            by_domain[domain]["total"] += 1
            if result.get("success", False):
                by_domain[domain]["success"] += 1
            else:
                by_domain[domain]["failed"] += 1
        
        # Calculer les métriques globales
        total_fragments = len(results)
        successful = sum(1 for r in results if r.get("success", False))
        success_rate = (successful / total_fragments * 100) if total_fragments > 0 else 0
        
        # Générer les recommandations
        recommendations = self._generate_recommendations(metrics, results)
        
        report = {
            "sprint": specs.get("sprint", "SPRINT-000"),
            "name": specs.get("name", "Sans nom"),
            "timestamp": datetime.now().isoformat(),
            "metrics": {
                "total_fragments": total_fragments,
                "successful": successful,
                "failed": total_fragments - successful,
                "success_rate": round(success_rate, 1),
                "by_domain": by_domain,
                **metrics
            },
            "results": results,
            "recommendations": recommendations
        }
        
        return report
    
    async def execute_sprint(self, spec_file: str) -> Dict[str, Any]:
        """
        Exécute un sprint complet
        
        Args:
            spec_file: Chemin vers le fichier de spécification
            
        Returns:
            Rapport détaillé du sprint
        """
        self._logger.info(f"🚀 Démarrage du sprint avec spécifications: {spec_file}")
        
        # Vérifier que le sprint manager est initialisé
        if not self._sprint_manager:
            self._sprint_manager = SprintManager(self._agent_config.get("sprint_config", {}))
            self._sprint_manager.set_logger(self._logger.info)
        
        # Charger les spécifications
        specs = self._sprint_manager.load_specs(spec_file)
        
        # Planifier le sprint
        fragments = self._sprint_manager.plan_sprint()
        self._logger.info(f"📋 Planification: {len(fragments)} fragments à exécuter")
        
        # Exécuter chaque fragment
        results = []
        for fragment in fragments:
            result = await self._execute_fragment(fragment)
            results.append(result)
            
            # Mettre à jour les métriques
            self._sprint_manager.results[fragment["id"]] = result
            
            if result.get("success"):
                self._sprint_manager.metrics["fragments_completed"] += 1
            else:
                self._sprint_manager.metrics["fragments_failed"] += 1
            
            self._sprint_manager.metrics["iterations_total"] += result.get("iterations", 1)
        
        # Calculer les métriques finales
        total = self._sprint_manager.metrics["fragments_total"]
        completed = self._sprint_manager.metrics["fragments_completed"]
        self._sprint_manager.metrics["success_rate"] = (completed / total * 100) if total > 0 else 0
        self._sprint_manager.metrics["sprints_completed"] += 1
        self._stats["sprints_completed"] += 1
        self._stats["fragments_executed"] += len(results)
        
        # Générer le rapport
        report = self._generate_sprint_report(specs, results, self._sprint_manager.metrics)
        
        # Sauvegarder les artefacts
        await self._save_sprint_artifacts(specs, results, report)
        
        self._logger.info(f"✅ Sprint {report['sprint']} terminé - Taux de succès: {report['metrics']['success_rate']:.1f}%")
        
        return report
    
    async def _execute_fragment(self, fragment: Dict) -> Dict[str, Any]:
        """
        Exécute un fragment unique avec probabilité de succès adaptative
        
        Args:
            fragment: Spécification du fragment à exécuter
            
        Returns:
            Résultat de l'exécution avec métadonnées
        """
        fragment_id = fragment["id"]
        domain = fragment.get("domain", "unknown")
        language = fragment.get("language", "unknown")
        complexity = fragment.get("complexity", 3)
        name = fragment.get("name", "")
        
        self._logger.info(f"📦 [{domain}] Fragment {fragment_id} ({language}) - {name}")
        self._logger.debug(f"   📊 Complexité: {complexity}")
        
        # Simulation d'exécution avec délai basé sur la complexité
        execution_time = 0.2 * complexity
        await asyncio.sleep(execution_time)
        
        # =================================================================
        # CALCUL DU TAUX DE SUCCÈS DE BASE
        # =================================================================
        
        # Base rate selon la complexité
        if complexity <= 2:
            base_rate = 0.95  # 95% pour les fragments simples
        elif complexity <= 3:
            base_rate = 0.85  # 85% pour les fragments moyens
        elif complexity <= 4:
            base_rate = 0.75  # 75% pour les fragments complexes
        else:
            base_rate = 0.60  # 60% pour les fragments très complexes
        
        success_rate = base_rate
        bonuses = []
        
        # =================================================================
        # BONUS SELON LE DOMAINE
        # =================================================================
        
        # Bonus pour le frontend (souvent plus difficile)
        if domain == "frontend":
            success_rate += 0.10  # +10% pour le frontend
            bonuses.append("frontend_bonus")
            self._logger.debug(f"   🎨 Bonus frontend appliqué: +10%")
        
        # Bonus pour la documentation (souvent plus simple)
        if domain == "documentation":
            success_rate += 0.15  # +15% pour la doc
            bonuses.append("doc_bonus")
        
        # Bonus pour le backend (bien standardisé)
        if domain == "backend":
            success_rate += 0.05  # +5% pour le backend
            bonuses.append("backend_bonus")
        
        # =================================================================
        # BONUS POUR LES DÉPENDANCES SATISFAITES
        # =================================================================
        
        # Vérifier si les dépendances existent et ont réussi
        depends_on = fragment.get("depends_on", [])
        if depends_on and self._sprint_manager:
            deps_satisfied = True
            for dep_id in depends_on:
                if dep_id == "*":  # Dépend de tous
                    continue
                if dep_id in self._sprint_manager.results:
                    if not self._sprint_manager.results[dep_id].get("success", False):
                        deps_satisfied = False
                        self._logger.debug(f"   ⚠️ Dépendance non satisfaite: {dep_id}")
                else:
                    deps_satisfied = False
                    self._logger.debug(f"   ⚠️ Dépendance manquante: {dep_id}")
            
            if deps_satisfied:
                success_rate += 0.10  # +10% si toutes les dépendances sont OK
                bonuses.append("dependencies_ok")
                self._logger.debug(f"   🔗 Bonus dépendances: +10%")
        
        # =================================================================
        # BONUS SPÉCIFIQUE POUR STAKING POOL
        # =================================================================
        
        if "Staking" in name or "SC_002" in fragment_id:
            self._logger.debug(f"   ⚙️ Application de règles spéciales pour StakingPool")
            
            # Vérifier que le token de base existe (SC_001)
            token_fragment_id = fragment_id.replace("SC_002", "SC_001")
            
            if self._sprint_manager:
                results = self._sprint_manager.results
                if token_fragment_id in results and results[token_fragment_id].get("success", False):
                    success_rate += 0.15  # +15% de bonus
                    bonuses.append("staking_bonus")
                    self._logger.debug(f"   ✅ Dépendance {token_fragment_id} validée, bonus +15% appliqué")
        
        # =================================================================
        # BONUS POUR LES FRAGMENTS AVEC TESTS DÉTAILLÉS
        # =================================================================
        
        if "tests" in fragment and len(fragment.get("tests", {}).get("unit", [])) > 5:
            success_rate += 0.05  # +5% si beaucoup de tests
            bonuses.append("good_test_coverage")
        
        # =================================================================
        # MALUS POUR LES FRAGMENTS TRÈS COMPLEXES
        # =================================================================
        
        if complexity >= 4 and "staking" in name.lower():
            success_rate -= 0.10  # -10% pour staking complexe
            self._logger.debug(f"   ⚠️ Malus complexité staking: -10%")
        
        # Limiter le taux entre 0.5 et 0.98
        success_rate = max(0.5, min(0.98, success_rate))
        
        # =================================================================
        # EXÉCUTION SIMULÉE
        # =================================================================
        
        success = random.random() < success_rate
        
        # Nombre d'itérations simulé
        if success:
            iterations = random.randint(1, 3)
            if complexity >= 4:
                iterations += random.randint(0, 1)  # Une itération de plus pour les complexes
        else:
            iterations = random.randint(3, 5)
            if bonuses:
                iterations -= 1  # Moins d'itérations si on avait des bonus
        
        iterations = max(1, iterations)
        
        # =================================================================
        # PRÉPARATION DU RÉSULTAT
        # =================================================================
        
        result = {
            "fragment_id": fragment_id,
            "domain": domain,
            "name": name,
            "complexity": complexity,
            "success": success,
            "iterations": iterations,
            "success_rate": round(success_rate * 100, 1),
            "bonuses": bonuses,
            "timestamp": datetime.now().isoformat()
        }
        
        # Ajouter des raisons d'échec si nécessaire
        if not success:
            reasons = []
            if complexity > 3:
                reasons.append("Complexité élevée")
            if "staking" in name.lower():
                reasons.append("Logique de récompense complexe")
            if random.random() < 0.3:
                reasons.append("Problème de gas estimation")
            if domain == "frontend":
                reasons.append("Compatibilité navigateur")
                reasons.append("Intégration WalletConnect")
            
            result["failure_reasons"] = reasons
            self._logger.debug(f"   📋 Raisons: {', '.join(reasons)}")
        
        # =================================================================
        # LOGGING DU RÉSULTAT
        # =================================================================
        
        if success:
            self._logger.info(f"   ✅ Fragment {fragment_id} validé")
            self._logger.debug(f"      📈 Taux: {success_rate:.0%} | Itérations: {iterations} | Bonus: {len(bonuses)}")
        else:
            self._logger.warning(f"   ❌ Fragment {fragment_id} échoué")
            self._logger.debug(f"      📉 Taux: {success_rate:.0%} | Itérations: {iterations}")
        
        return result
    
    def _generate_recommendations(self, metrics: Dict, results: List[Dict]) -> List[str]:
        """
        Génère des recommandations pour le prochain sprint
        
        Args:
            metrics: Métriques du sprint
            results: Résultats des fragments
        
        Returns:
            Liste de recommandations
        """
        recommendations = []
        
        # Analyser les taux d'échec par domaine
        by_domain = {}
        for result in results:
            domain = result.get("domain", "unknown")
            if domain not in by_domain:
                by_domain[domain] = {"total": 0, "failed": 0}
            
            by_domain[domain]["total"] += 1
            if not result.get("success", False):
                by_domain[domain]["failed"] += 1
        
        for domain, stats in by_domain.items():
            if stats["total"] > 0 and stats["failed"] > 0:
                fail_rate = stats["failed"] / stats["total"] * 100
                if fail_rate > 30:
                    recommendations.append(
                        f"⚠️ Domaine '{domain}': taux d'échec élevé ({fail_rate:.1f}%). "
                        "Revoir les spécifications."
                    )
        
        # Recommandations globales
        success_rate = metrics.get("success_rate", 0)
        if success_rate < 70:
            recommendations.append(
                f"🎯 Taux de succès global faible ({success_rate:.1f}%). "
                "Envisager une phase de conception plus approfondie."
            )
        
        # Fragments lents
        slow_fragments = [r for r in results if r.get("iterations", 0) > 3]
        if slow_fragments:
            recommendations.append(
                f"🐢 {len(slow_fragments)} fragments ont nécessité plus de 3 itérations. "
                "Les détailler davantage."
            )
        
        # Recommandations spécifiques
        failed_fragments = [r for r in results if not r.get("success", False)]
        if failed_fragments:
            failed_ids = [r["fragment_id"] for r in failed_fragments[:3]]
            recommendations.append(
                f"🔍 Analyser les échecs: {', '.join(failed_ids)}"
            )
        
        return recommendations
    
    async def _save_sprint_artifacts(self, specs: Dict, results: List[Dict], report: Dict):
        """Sauvegarde les artefacts du sprint"""
        sprint_id = specs.get("sprint", "SPRINT-000")
        base_path = Path(self._agent_config.get("sprint_config", {}).get("reports_path", "./reports/sprints/"))
        base_path.mkdir(parents=True, exist_ok=True)
        
        # Rapport JSON
        report_file = base_path / f"{sprint_id}_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        self._logger.info(f"💾 Rapport sauvegardé: {report_file}")
    
    # =================================================================
    # GESTION DES WORKFLOWS (API Publique)
    # =================================================================
    
    async def get_workflow(self, workflow_id: str) -> Optional[Dict]:
        """Retourne un workflow par son ID"""
        if workflow_id not in self._workflows:
            return None
        return self._workflows[workflow_id].to_dict()
    
    async def get_workflow_status(self, workflow_id: str) -> Optional[Dict]:
        """Retourne le statut d'un workflow"""
        workflow = await self.get_workflow(workflow_id)
        if not workflow:
            return None
        return {
            "workflow_id": workflow["id"],
            "name": workflow["name"],
            "status": workflow["status"],
            "steps_total": len(workflow["steps"]),
            "steps_completed": sum(1 for s in workflow["steps"] if s["status"] == "completed"),
            "steps_failed": sum(1 for s in workflow["steps"] if s["status"] == "failed"),
            "started_at": workflow["started_at"],
            "completed_at": workflow["completed_at"]
        }
    
    async def list_workflows(self, status: Optional[str] = None) -> List[Dict]:
        """Liste tous les workflows"""
        workflows = []
        for workflow in self._workflows.values():
            if status and workflow.status.value != status:
                continue
            workflows.append(workflow.to_dict())
        return workflows
    
    async def cancel_workflow(self, workflow_id: str) -> bool:
        """Annule un workflow en cours"""
        if workflow_id not in self._workflows:
            return False
        
        workflow = self._workflows[workflow_id]
        if workflow.status == WorkflowStatus.RUNNING:
            workflow.status = WorkflowStatus.CANCELLED
            workflow.completed_at = datetime.now()
            self._logger.info(f"🛑 Workflow {workflow_id} annulé")
            return True
        
        return False
    
    async def delete_workflow(self, workflow_id: str) -> bool:
        """Supprime un workflow"""
        if workflow_id in self._workflows:
            del self._workflows[workflow_id]
            self._logger.info(f"🗑️ Workflow {workflow_id} supprimé")
            return True
        return False
    
    # =================================================================
    # STATISTIQUES
    # =================================================================
    
    async def get_statistics(self) -> Dict[str, Any]:
        """Retourne les statistiques"""
        uptime = (datetime.now() - self._stats["start_time"]).total_seconds()
        
        return {
            **self._stats,
            "uptime_seconds": uptime,
            "uptime_formatted": str(timedelta(seconds=int(uptime))),
            "active_workflows": len([w for w in self._workflows.values() if w.status == WorkflowStatus.RUNNING]),
            "total_workflows": len(self._workflows)
        }
    
    async def reset_statistics(self) -> None:
        """Réinitialise les statistiques"""
        self._stats = {
            "workflows_executed": 0,
            "workflows_completed": 0,
            "workflows_failed": 0,
            "steps_executed": 0,
            "steps_failed": 0,
            "sprints_completed": 0,
            "fragments_executed": 0,
            "start_time": datetime.now()
        }
        self._logger.info("📊 Statistiques réinitialisées")
    
    # =================================================================
    # REQUIS PAR BASEAGENT
    # =================================================================
    
    async def health_check(self) -> Dict[str, Any]:
        """Vérifie la santé de l'agent"""
        stats = await self.get_statistics()
        
        # Vérifications supplémentaires
        components_healthy = all(self._components.values())
        
        return {
            "agent": self._name,
            "status": self._status.value if hasattr(self._status, 'value') else str(self._status),
            "ready": self._status == AgentStatus.READY and components_healthy,
            "initialized": self._initialized,
            "workflows": {
                "executed": stats["workflows_executed"],
                "active": stats["active_workflows"]
            },
            "sprints_completed": stats["sprints_completed"],
            "components": {k: "healthy" if v else "unhealthy" for k, v in self._components.items()},
            "uptime": stats["uptime_formatted"]
        }
    
    def get_agent_info(self) -> Dict[str, Any]:
        """Informations de l'agent"""
        return {
            "id": self._name,
            "name": "🚀 Orchestrator Agent",
            "version": "2.0.1",
            "description": "Orchestration des workflows et sprints",
            "status": self._status.value if hasattr(self._status, 'value') else str(self._status),
            "capabilities": [
                "workflow_orchestration",
                "sprint_management",
                "multi_domain_planning",
                "fragment_execution",
                "report_generation",
                "project_spec_generation"
            ],
            "initialized": self._initialized,
            "workflows_created": len(self._workflows),
            "sprints_completed": self._stats["sprints_completed"],
            "components": list(self._components.keys())
        }
    
    async def _handle_custom_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Gestion des messages personnalisés"""
        msg_type = message.get("type", "")
        msg_id = message.get("message_id", "unknown")
        
        self._logger.debug(f"📨 Message reçu: {msg_type} (id: {msg_id})")
        
        try:
            if msg_type == "create_workflow":
                workflow = await self.create_workflow(
                    name=message.get("name", "Workflow"),
                    steps=message.get("steps"),
                    workflow_type=message.get("workflow_type", "standard"),
                    metadata=message.get("metadata")
                )
                return {
                    "message_id": msg_id,
                    "success": True,
                    "workflow_id": workflow.id,
                    "status": "created"
                }
            
            elif msg_type == "execute_workflow":
                result = await self.execute_workflow(message["workflow_id"])
                return {
                    "message_id": msg_id,
                    "success": result.get("status") in ["completed", "failed"],
                    "result": result
                }
            
            elif msg_type == "execute_sprint":
                report = await self.execute_sprint(message["spec_file"])
                return {
                    "message_id": msg_id,
                    "success": True,
                    "report": report
                }
            
            elif msg_type == "prepare_and_execute_sprint":
                report = await self.prepare_and_execute_sprint(
                    project_name=message["project_name"],
                    project_type=message.get("project_type", "defi"),
                    strategy=message.get("strategy", "largeur_dabord")
                )
                return {
                    "message_id": msg_id,
                    "success": True,
                    "report": report
                }
            
            elif msg_type == "generate_project_spec":
                spec_file = await self.generate_project_spec(
                    project_name=message["project_name"],
                    project_type=message.get("project_type", "defi"),
                    output_dir=message.get("output_dir")
                )
                return {
                    "message_id": msg_id,
                    "success": True,
                    "spec_file": spec_file
                }
            
            elif msg_type == "get_workflow":
                workflow = await self.get_workflow(message["workflow_id"])
                return {
                    "message_id": msg_id,
                    "success": workflow is not None,
                    "workflow": workflow
                }
            
            elif msg_type == "list_workflows":
                workflows = await self.list_workflows(message.get("status"))
                return {
                    "message_id": msg_id,
                    "success": True,
                    "workflows": workflows,
                    "count": len(workflows)
                }
            
            elif msg_type == "workflow_status":
                status = await self.get_workflow_status(message["workflow_id"])
                return {
                    "message_id": msg_id,
                    "success": status is not None,
                    "status": status
                }
            
            elif msg_type == "cancel_workflow":
                cancelled = await self.cancel_workflow(message["workflow_id"])
                return {
                    "message_id": msg_id,
                    "success": cancelled,
                    "message": "Workflow annulé" if cancelled else "Workflow non trouvé ou non annulable"
                }
            
            elif msg_type == "delete_workflow":
                deleted = await self.delete_workflow(message["workflow_id"])
                return {
                    "message_id": msg_id,
                    "success": deleted,
                    "message": "Workflow supprimé" if deleted else "Workflow non trouvé"
                }
            
            elif msg_type == "statistics":
                stats = await self.get_statistics()
                return {
                    "message_id": msg_id,
                    "success": True,
                    "statistics": stats
                }
            
            elif msg_type == "reset_statistics":
                await self.reset_statistics()
                return {
                    "message_id": msg_id,
                    "success": True,
                    "message": "Statistiques réinitialisées"
                }
            
            elif msg_type == "ping":
                return {
                    "message_id": msg_id,
                    "success": True,
                    "pong": True,
                    "timestamp": datetime.now().isoformat()
                }
            
            else:
                self._logger.warning(f"⚠️ Type de message non supporté: {msg_type}")
                return {
                    "message_id": msg_id,
                    "success": False,
                    "error": f"Type de message non supporté: {msg_type}"
                }
                
        except Exception as e:
            self._logger.error(f"❌ Erreur traitement message {msg_type}: {e}")
            self._logger.error(traceback.format_exc())
            return {
                "message_id": msg_id,
                "success": False,
                "error": str(e)
            }


# =====================================================================
# FONCTIONS D'USINE
# =====================================================================

def create_orchestrator_agent(config_path: str = "") -> OrchestratorAgent:
    """Crée une instance de l'orchestrateur"""
    return OrchestratorAgent(config_path)


async def get_orchestrator_agent(config_path: str = "") -> OrchestratorAgent:
    """Crée et initialise une instance de l'orchestrateur"""
    agent = create_orchestrator_agent(config_path)
    await agent.initialize()
    return agent


# =====================================================================
# POINT D'ENTRÉE POUR EXÉCUTION DIRECTE
# =====================================================================

if __name__ == "__main__":
    async def main():
        print("=" * 70)
        print("🚀 TEST ORCHESTRATOR AGENT".center(70))
        print("=" * 70)
        
        agent = await get_orchestrator_agent()
        
        info = agent.get_agent_info()
        print(f"\n✅ Agent: {info['name']}")
        print(f"✅ Version: {info['version']}")
        print(f"✅ Statut: {info['status']}")
        print(f"✅ Composants: {', '.join(info['components'])}")
        
        # Test création workflow
        print(f"\n📋 Test création workflow...")
        workflow = await agent.create_workflow(
            name="Test Workflow",
            steps=[
                {
                    "name": "step1",
                    "agent": "test_agent",
                    "task": "test_task",
                    "parameters": {"param": "value"},
                    "metadata": {"order": 0}
                }
            ]
        )
        print(f"   ✅ Workflow créé: {workflow.id}")
        
        # Test exécution
        print(f"\n🚀 Test exécution workflow...")
        result = await agent.execute_workflow(workflow.id)
        print(f"   ✅ Statut: {result['status']}")
        
        # Test sprint avec projet DeFi
        print(f"\n📦 Test sprint avec projet DeFi...")
        report = await agent.prepare_and_execute_sprint(
            project_name="MyDeFiApp",
            project_type="defi",
            strategy="largeur_dabord"
        )
        print(f"   ✅ Sprint {report['sprint']} terminé")
        print(f"   📊 Taux de succès: {report['metrics']['success_rate']:.1f}%")
        print(f"   📋 Fragments: {report['metrics']['total_fragments']}")
        
        # Statistiques
        print(f"\n📊 Statistiques:")
        stats = await agent.get_statistics()
        print(f"   📈 Workflows: {stats['workflows_executed']}")
        print(f"   📈 Sprints: {stats['sprints_completed']}")
        print(f"   ⏱️  Uptime: {stats['uptime_formatted']}")
        
        print("\n" + "=" * 70)
        print("✅ ORCHESTRATOR AGENT OPÉRATIONNEL".center(70))
        print("=" * 70)
    
    asyncio.run(main())
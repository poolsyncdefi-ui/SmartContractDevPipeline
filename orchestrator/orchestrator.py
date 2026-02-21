"""
Orchestrator Agent - Orchestration des workflows et sprints
Gère l'exécution des pipelines et le développement par sprints
Version: 2.0.0
"""

import os
import sys
import yaml
import asyncio
import json
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Any, Optional, Union
from pathlib import Path
from collections import defaultdict
import traceback

# Ajouter le chemin pour l'import de BaseAgent
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from agents.base_agent.base_agent import BaseAgent, AgentStatus
except ImportError:
    # Fallback pour les tests
    class AgentStatus(Enum):
        CREATED = "created"
        INITIALIZING = "initializing"
        READY = "ready"
        ERROR = "error"
    
    class BaseAgent:
        def __init__(self, config_path: str = ""):
            self.config_path = config_path
            self._logger = print
            self._name = "orchestrator"
            self._status = AgentStatus.CREATED
            self.config = {}
            self._start_time = datetime.now()
        
        async def initialize(self) -> bool:
            self._status = AgentStatus.READY
            return True
        
        @property
        def uptime(self):
            return datetime.now() - self._start_time


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
                 max_retries: int = 3):
        
        self.id = f"step_{datetime.now().timestamp()}_{name}"
        self.name = name
        self.agent_type = agent_type
        self.task_type = task_type
        self.parameters = parameters or {}
        self.depends_on = depends_on or []
        self.timeout = timeout
        self.retry_count = retry_count
        self.max_retries = max_retries
        self.status = StepStatus.PENDING
        self.result = None
        self.error = None
        self.started_at = None
        self.completed_at = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "agent_type": self.agent_type,
            "task_type": self.task_type,
            "parameters": self.parameters,
            "depends_on": self.depends_on,
            "status": self.status.value,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries
        }


class Workflow:
    """Workflow complet"""
    
    def __init__(self, name: str, workflow_type: str = "standard"):
        self.id = f"workflow_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        self.name = name
        self.workflow_type = workflow_type
        self.status = WorkflowStatus.PENDING
        self.steps: List[WorkflowStep] = []
        self.created_at = datetime.now()
        self.started_at = None
        self.completed_at = None
        self.context: Dict[str, Any] = {}
        self.results: Dict[str, Any] = {}
        self.artifacts: List[str] = []
        self.report_path = None
    
    def add_step(self, step: WorkflowStep):
        """Ajoute une étape au workflow"""
        self.steps.append(step)
    
    def get_step(self, step_name: str) -> Optional[WorkflowStep]:
        """Récupère une étape par son nom"""
        for step in self.steps:
            if step.name == step_name:
                return step
        return None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "type": self.workflow_type,
            "status": self.status.value,
            "steps": [s.to_dict() for s in self.steps],
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None
        }


# =====================================================================
# SPRINT MANAGER
# =====================================================================

class SprintManager:
    """
    Gestionnaire de sprints multi-domaines
    Coordonne le développement parallèle sur tous les aspects du projet
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.current_sprint = None
        self.fragments: Dict[str, Dict] = {}
        self.dependency_graph: Dict[str, List[str]] = {}
        self.results: Dict[str, Any] = {}
        self.logger = print  # Sera remplacé par l'orchestrateur
        
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
    
    def load_specs(self, spec_file: str) -> Dict[str, Any]:
        """Charge les spécifications depuis un fichier JSON"""
        self.logger(f"📋 Chargement des spécifications: {spec_file}")
        
        try:
            with open(spec_file, 'r', encoding='utf-8') as f:
                specs = json.load(f)
        except FileNotFoundError:
            self.logger(f"❌ Fichier non trouvé: {spec_file}")
            # Retourner des spécifications par défaut pour les tests
            specs = self._get_default_specs()
        except Exception as e:
            self.logger(f"❌ Erreur chargement: {e}")
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
        
        def dfs(fragment_id):
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
        
        # Statistiques
        self._stats = {
            "workflows_executed": 0,
            "workflows_completed": 0,
            "workflows_failed": 0,
            "steps_executed": 0,
            "steps_failed": 0,
            "sprints_completed": 0,
            "start_time": datetime.now()
        }
        
        # Composants
        self._components = {}
    
    def _load_configuration(self):
        """Charge la configuration depuis le fichier YAML"""
        try:
            # Utiliser self._config_path au lieu de self.config_path
            if self._config_path and os.path.exists(self._config_path):
                with open(self._config_path, 'r', encoding='utf-8') as f:
                    file_config = yaml.safe_load(f) or {}
                
                # Stocker dans self._agent_config (pas self.config)
                self._agent_config = file_config
                self._logger.info(f"✅ Configuration chargée depuis {self._config_path}")
                
                # Configuration par défaut pour les sprints
                if "sprint_config" not in self._agent_config:
                    self._agent_config["sprint_config"] = {
                        "enabled": True,
                        "default_strategy": "largeur_dabord",
                        "max_iterations_per_fragment": 3,
                        "reports_path": "./reports/sprints/"
                    }
            else:
                self._logger.warning("⚠️ Fichier de configuration non trouvé")
                self._agent_config = {
                    "sprint_config": {
                        "enabled": True,
                        "default_strategy": "largeur_dabord",
                        "max_iterations_per_fragment": 3,
                        "reports_path": "./reports/sprints/"
                    }
                }
        except Exception as e:
            self._logger.error(f"❌ Erreur chargement config: {e}")
            self._agent_config = {
                "sprint_config": {
                    "enabled": True,
                    "default_strategy": "largeur_dabord",
                    "max_iterations_per_fragment": 3,
                    "reports_path": "./reports/sprints/"
                }
            }
    
    async def initialize(self) -> bool:
        """Initialisation asynchrone"""
        try:
            self._status = AgentStatus.INITIALIZING
            self._logger.info("Initialisation de l'orchestrateur...")
            
            # Initialiser les composants
            await self._initialize_components()
            
            # Initialiser le sprint manager
            self._sprint_manager = SprintManager(self.config.get("sprint_config", {}))
            self._sprint_manager.set_logger(self._logger.info)
            
            self._status = AgentStatus.READY
            self._logger.info("✅ Orchestrateur prêt")
            return True
            
        except Exception as e:
            self._logger.error(f"❌ Erreur initialisation: {e}")
            self._logger.error(traceback.format_exc())
            self._status = AgentStatus.ERROR
            return False
    
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
    
    async def generate_project_spec(self, project_name: str, project_type: str = "defi") -> str:
    """
    Génère un fichier de spécification complet pour un projet
    
    Args:
        project_name: Nom du projet
        project_type: Type de projet (defi, nft, gaming, dao)
    
    Returns:
        Chemin vers le fichier JSON généré
    """
    self._logger.info(f"📋 Génération de spécification pour projet: {project_name}")
    
    # Template de base selon le type de projet
    templates = {
        "defi": self._get_defi_template,
        "nft": self._get_nft_template,
        "gaming": self._get_gaming_template,
        "dao": self._get_dao_template
    }
    
    template_func = templates.get(project_type, self._get_defi_template)
    spec = template_func(project_name)
    
    # Sauvegarder le fichier
    specs_dir = Path("./specs/projects")
    specs_dir.mkdir(parents=True, exist_ok=True)
    
    filename = f"{project_name.lower().replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.json"
    filepath = specs_dir / filename
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(spec, f, indent=2, ensure_ascii=False)
    
    self._logger.info(f"✅ Spécification projet générée: {filepath}")
    return str(filepath)

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
        self._logger.info(f"🚀 Préparation du sprint pour projet: {project_name}")
        
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
            "estimated_sprints": fragments_info["metadata"]["estimated_sprints"]
        }
        
        return report

    def _get_defi_template(self, project_name: str) -> Dict:
        """Template pour projet DeFi"""
        return {
            "project": project_name,
            "type": "defi",
            "version": "1.0.0",
            "generated_at": datetime.now().isoformat(),
            "description": "Plateforme DeFi complète avec token, staking, et interface web",
            "domains": ["smart_contract", "backend", "frontend", "database", "devops", "documentation"],
            "fragments": [
                {
                    "id": f"{project_name}_SC_001",
                    "domain": "smart_contract",
                    "name": "Token ERC20",
                    "description": "Token standard avec mint/burn",
                    "language": "solidity",
                    "version": "0.8.19",
                    "framework": "foundry",
                    "complexity": 2,
                    "dependencies": ["openzeppelin/contracts@4.9.0"],
                    "specification": {
                        "contract_name": f"{project_name}Token",
                        "symbol": project_name[:5].upper(),
                        "features": ["mint", "burn", "transfer", "approve"]
                    }
                },
                {
                    "id": f"{project_name}_SC_002",
                    "domain": "smart_contract",
                    "name": "Staking Pool",
                    "description": "Pool de staking avec récompenses",
                    "language": "solidity",
                    "version": "0.8.19",
                    "framework": "foundry",
                    "complexity": 4,
                    "depends_on": [f"{project_name}_SC_001"],
                    "specification": {
                        "contract_name": f"{project_name}Staking",
                        "features": ["stake", "unstake", "claim", "compound"]
                    }
                },
                {
                    "id": f"{project_name}_BE_001",
                    "domain": "backend",
                    "name": "API FastAPI",
                    "description": "API REST pour le projet",
                    "language": "python",
                    "version": "3.11",
                    "framework": "fastapi",
                    "complexity": 3,
                    "depends_on": [f"{project_name}_SC_001", f"{project_name}_DB_001"],
                    "specification": {
                        "endpoints": ["/balance", "/transfer", "/stake", "/rewards"],
                        "database": "postgresql",
                        "cache": "redis"
                    }
                },
                {
                    "id": f"{project_name}_FE_001",
                    "domain": "frontend",
                    "name": "Interface React",
                    "description": "Application React avec WalletConnect",
                    "language": "typescript",
                    "version": "5.0",
                    "framework": "nextjs",
                    "complexity": 3,
                    "depends_on": [f"{project_name}_BE_001"],
                    "specification": {
                        "pages": ["dashboard", "staking", "admin"],
                        "wallets": ["metamask", "walletconnect"]
                    }
                },
                {
                    "id": f"{project_name}_DB_001",
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
                    "id": f"{project_name}_DO_001",
                    "domain": "devops",
                    "name": "Infrastructure Docker",
                    "description": "Déploiement conteneurisé",
                    "language": "yaml",
                    "version": "docker-compose-v3",
                    "complexity": 3,
                    "depends_on": [f"{project_name}_BE_001", f"{project_name}_FE_001", f"{project_name}_DB_001"],
                    "specification": {
                        "services": ["postgres", "redis", "backend", "frontend", "nginx"],
                        "environments": ["development", "staging", "production"]
                    }
                },
                {
                    "id": f"{project_name}_DOC_001",
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
                {"from": f"{project_name}_SC_002", "to": f"{project_name}_SC_001"},
                {"from": f"{project_name}_BE_001", "to": f"{project_name}_SC_001"},
                {"from": f"{project_name}_BE_001", "to": f"{project_name}_DB_001"},
                {"from": f"{project_name}_FE_001", "to": f"{project_name}_BE_001"},
                {"from": f"{project_name}_DO_001", "to": f"{project_name}_BE_001"},
                {"from": f"{project_name}_DO_001", "to": f"{project_name}_FE_001"},
                {"from": f"{project_name}_DO_001", "to": f"{project_name}_DB_001"},
                {"from": f"{project_name}_DOC_001", "to": "*"}
            ]
        }

    def _get_nft_template(self, project_name: str) -> Dict:
        """Template pour projet NFT"""
        # Similaire mais adapté aux NFTs
        template = self._get_defi_template(project_name)
        template["type"] = "nft"
        template["description"] = "Collection NFT avec mint, marketplace et royalties"
        # Adapter les fragments pour NFT...
        return template

    def _get_gaming_template(self, project_name: str) -> Dict:
        """Template pour projet Gaming"""
        template = self._get_defi_template(project_name)
        template["type"] = "gaming"
        template["description"] = "Jeu Web3 avec tokens, items et marketplace"
        return template

    def _get_dao_template(self, project_name: str) -> Dict:
        """Template pour projet DAO"""
        template = self._get_defi_template(project_name)
        template["type"] = "dao"
        template["description"] = "DAO avec gouvernance, treasury et votes"
        return template
        
    # =================================================================
    # GESTION DES WORKFLOWS
    # =================================================================
    
    async def create_workflow(self, 
                             name: str,
                             steps: List[Dict[str, Any]] = None,
                             workflow_type: str = "standard") -> Workflow:
        """
        Crée un nouveau workflow
        
        Args:
            name: Nom du workflow
            steps: Liste des étapes
            workflow_type: Type de workflow
            
        Returns:
            Workflow créé
        """
        self._logger.info(f"📋 Création du workflow: {name}")
        
        workflow = Workflow(name, workflow_type)
        
        if steps:
            for step_config in steps:
                step = WorkflowStep(
                    name=step_config["name"],
                    agent_type=step_config["agent"],
                    task_type=step_config["task"],
                    parameters=step_config.get("parameters", {}),
                    depends_on=step_config.get("depends_on", [])
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
            raise ValueError(f"Workflow {workflow_id} non trouvé")
        
        workflow = self._workflows[workflow_id]
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
                    step.status = StepStatus.BLOCKED
                    workflow.status = WorkflowStatus.FAILED
                    break
                
                # Exécuter l'étape
                result = await self._execute_step(step, workflow.context)
                results[step.name] = result
                self._stats["steps_executed"] += 1
                
                if not result.get("success", False):
                    self._stats["steps_failed"] += 1
                    if not self.config.get("continue_on_error", False):
                        workflow.status = WorkflowStatus.FAILED
                        break
            
            # Finaliser le workflow
            workflow.completed_at = datetime.now()
            
            if all(s.status == StepStatus.COMPLETED for s in workflow.steps):
                workflow.status = WorkflowStatus.COMPLETED
                self._stats["workflows_completed"] += 1
                self._logger.info(f"🎉 Workflow {workflow.name} terminé avec succès")
            else:
                workflow.status = WorkflowStatus.FAILED
                self._stats["workflows_failed"] += 1
                self._logger.warning(f"⚠️ Workflow {workflow.name} terminé avec des échecs")
            
            return {
                "workflow_id": workflow.id,
                "status": workflow.status.value,
                "steps_completed": sum(1 for s in workflow.steps if s.status == StepStatus.COMPLETED),
                "steps_failed": sum(1 for s in workflow.steps if s.status == StepStatus.FAILED),
                "duration_seconds": (workflow.completed_at - workflow.started_at).total_seconds(),
                "results": results
            }
            
        except Exception as e:
            self._logger.error(f"❌ Erreur workflow: {e}")
            workflow.status = WorkflowStatus.FAILED
            self._stats["workflows_failed"] += 1
            return {
                "workflow_id": workflow.id,
                "status": "failed",
                "error": str(e)
            }
    
    def _resolve_execution_order(self, workflow: Workflow) -> List[WorkflowStep]:
        """Résout l'ordre d'exécution des étapes (tri topologique)"""
        # Construire le graphe des dépendances
        graph = {step.name: set(step.depends_on) for step in workflow.steps}
        
        # Tri topologique
        visited = set()
        order = []
        
        def dfs(node_name):
            visited.add(node_name)
            step = next(s for s in workflow.steps if s.name == node_name)
            
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
            # Simuler l'exécution pour l'instant
            await asyncio.sleep(0.5)
            
            step.status = StepStatus.COMPLETED
            step.completed_at = datetime.now()
            
            return {
                "success": True,
                "step": step.name,
                "result": {"message": "Étape exécutée avec succès"}
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
    
    # =================================================================
    # GESTION DES SPRINTS
    # =================================================================
    
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
            self._sprint_manager = SprintManager(self.config.get("sprint_config", {}))
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
            if result.get("success"):
                self._sprint_manager.metrics["fragments_completed"] += 1
            else:
                self._sprint_manager.metrics["fragments_failed"] += 1
        
        # Calculer les métriques finales
        total = self._sprint_manager.metrics["fragments_total"]
        completed = self._sprint_manager.metrics["fragments_completed"]
        self._sprint_manager.metrics["success_rate"] = (completed / total * 100) if total > 0 else 0
        self._sprint_manager.metrics["sprints_completed"] += 1
        self._stats["sprints_completed"] += 1
        
        # Générer le rapport
        report = self._generate_sprint_report(specs, results, self._sprint_manager.metrics)
        
        # Sauvegarder les artefacts
        await self._save_sprint_artifacts(specs, results, report)
        
        return report
    
    async def _execute_fragment(self, fragment: Dict) -> Dict[str, Any]:
        """
        Exécute un fragment unique
        """
        fragment_id = fragment["id"]
        domain = fragment.get("domain", "unknown")
        language = fragment.get("language", "unknown")
        
        self._logger.info(f"📦 [{domain}] Fragment {fragment_id} ({language})")
        
        # Simulation d'exécution
        await asyncio.sleep(0.3)
        
        # Succès aléatoire pour la simulation (80%)
        import random
        success = random.random() > 0.2
        
        result = {
            "fragment_id": fragment_id,
            "domain": domain,
            "success": success,
            "iterations": random.randint(1, 4) if success else 3,
            "timestamp": datetime.now().isoformat()
        }
        
        if success:
            self._logger.info(f"  ✅ Fragment {fragment_id} validé")
        else:
            self._logger.warning(f"  ❌ Fragment {fragment_id} échoué")
        
        return result
    
    def _generate_sprint_report(self, specs: Dict, results: List[Dict], metrics: Dict) -> Dict:
        """Génère un rapport détaillé du sprint"""
        report = {
            "sprint": specs.get("sprint", "SPRINT-000"),
            "name": specs.get("name", "Sans nom"),
            "timestamp": datetime.now().isoformat(),
            "metrics": metrics,
            "results": results,
            "recommendations": self._generate_recommendations(metrics, results)
        }
        
        return report
    
    def _generate_recommendations(self, metrics: Dict, results: List[Dict]) -> List[str]:
        """Génère des recommandations pour le prochain sprint"""
        recommendations = []
        
        # Analyser les taux d'échec par domaine
        for domain, stats in metrics["by_domain"].items():
            if stats["total"] > 0:
                fail_rate = stats["failed"] / stats["total"] * 100
                if fail_rate > 30:
                    recommendations.append(
                        f"⚠️ Domaine '{domain}': taux d'échec élevé ({fail_rate:.1f}%). "
                        "Revoir les spécifications."
                    )
        
        # Recommandations globales
        if metrics["success_rate"] < 70:
            recommendations.append(
                f"🎯 Taux de succès global faible ({metrics['success_rate']:.1f}%). "
                "Envisager une phase de conception plus approfondie."
            )
        
        # Fragments lents
        slow_fragments = [r for r in results if r.get("iterations", 0) > 3]
        if slow_fragments:
            recommendations.append(
                f"🐢 {len(slow_fragments)} fragments ont nécessité plus de 3 itérations. "
                "Les détailler davantage."
            )
        
        return recommendations
    
    async def _save_sprint_artifacts(self, specs: Dict, results: List[Dict], report: Dict):
        """Sauvegarde les artefacts du sprint"""
        sprint_id = specs.get("sprint", "SPRINT-000")
        base_path = Path(self.config.get("sprint_config", {}).get("reports_path", "./reports/sprints/"))
        base_path.mkdir(parents=True, exist_ok=True)
        
        # Rapport JSON
        report_file = base_path / f"{sprint_id}_report.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        self._logger.info(f"💾 Rapport sauvegardé: {report_file}")
    
    # =================================================================
    # UTILITAIRES
    # =================================================================
    
    async def get_workflow_status(self, workflow_id: str) -> Optional[Dict]:
        """Retourne le statut d'un workflow"""
        if workflow_id not in self._workflows:
            return None
        return self._workflows[workflow_id].to_dict()
    
    async def list_workflows(self, status: Optional[str] = None) -> List[Dict]:
        """Liste tous les workflows"""
        workflows = []
        for workflow in self._workflows.values():
            if status and workflow.status.value != status:
                continue
            workflows.append(workflow.to_dict())
        return workflows
    
    async def get_statistics(self) -> Dict[str, Any]:
        """Retourne les statistiques"""
        return {
            **self._stats,
            "uptime_seconds": (datetime.now() - self._stats["start_time"]).total_seconds(),
            "active_workflows": len([w for w in self._workflows.values() if w.status == WorkflowStatus.RUNNING])
        }
    
    # =================================================================
    # REQUIS PAR BASEAGENT
    # =================================================================
    
    async def health_check(self) -> Dict[str, Any]:
        """Vérifie la santé de l'agent"""
        stats = await self.get_statistics()
        
        return {
            "agent": self._name,
            "status": self._status.value if hasattr(self._status, 'value') else str(self._status),
            "ready": self._status == AgentStatus.READY,
            "workflows_executed": stats["workflows_executed"],
            "sprints_completed": stats["sprints_completed"],
            "components": list(self._components.keys()),
            "uptime": stats["uptime_seconds"]
        }
    
    def get_agent_info(self) -> Dict[str, Any]:
        """Informations de l'agent"""
        return {
            "id": self._name,
            "name": "🚀 Orchestrator Agent",
            "version": "2.0.0",
            "description": "Orchestration des workflows et sprints",
            "status": self._status.value if hasattr(self._status, 'value') else str(self._status),
            "capabilities": [
                "workflow_orchestration",
                "sprint_management",
                "multi_domain_planning",
                "fragment_execution",
                "report_generation"
            ],
            "workflows_created": len(self._workflows),
            "sprints_completed": self._stats["sprints_completed"]
        }
    
    async def _handle_custom_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Gestion des messages personnalisés"""
        msg_type = message.get("type", "")
        
        if msg_type == "create_workflow":
            workflow = await self.create_workflow(
                name=message.get("name", "Workflow"),
                steps=message.get("steps"),
                workflow_type=message.get("type", "standard")
            )
            return {"workflow_id": workflow.id, "status": "created"}
        
        elif msg_type == "execute_workflow":
            result = await self.execute_workflow(message["workflow_id"])
            return result
        
        elif msg_type == "execute_sprint":
            report = await self.execute_sprint(message["spec_file"])
            return report
        
        elif msg_type == "list_workflows":
            workflows = await self.list_workflows(message.get("status"))
            return {"workflows": workflows}
        
        elif msg_type == "workflow_status":
            status = await self.get_workflow_status(message["workflow_id"])
            return status or {"error": "Workflow not found"}
        
        elif msg_type == "statistics":
            return await self.get_statistics()
        
        return {"status": "received", "type": msg_type}


# =====================================================================
# FONCTIONS D'USINE
# =====================================================================

def create_orchestrator_agent(config_path: str = "") -> OrchestratorAgent:
    """Crée une instance de l'orchestrateur"""
    return OrchestratorAgent(config_path)


# =====================================================================
# POINT D'ENTRÉE POUR EXÉCUTION DIRECTE
# =====================================================================

if __name__ == "__main__":
    async def main():
        print("🚀 TEST ORCHESTRATOR AGENT")
        print("="*60)
        
        agent = OrchestratorAgent()
        await agent.initialize()
        
        print(f"✅ Agent: {agent.get_agent_info()['name']}")
        print(f"✅ Statut: {agent._status.value if hasattr(agent._status, 'value') else agent._status}")
        print(f"✅ Composants: {list(agent._components.keys())}")
        
        # Test création workflow
        workflow = await agent.create_workflow(
            name="Test Workflow",
            steps=[
                {
                    "name": "step1",
                    "agent": "test_agent",
                    "task": "test_task",
                    "parameters": {"param": "value"}
                }
            ]
        )
        print(f"\n📋 Workflow créé: {workflow.id}")
        
        # Test exécution
        result = await agent.execute_workflow(workflow.id)
        print(f"🚀 Exécution: {result['status']}")
        
        # Test sprint
        print(f"\n📦 Test sprint manager...")
        report = await agent.execute_sprint("specs/defi_app.json")
        print(f"✅ Sprint {report['sprint']} terminé")
        print(f"📊 Taux de succès: {report['metrics']['success_rate']:.1f}%")
        
        print("\n" + "="*60)
        print("✅ ORCHESTRATOR AGENT OPÉRATIONNEL")
        print("="*60)
    
    asyncio.run(main())
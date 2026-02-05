# orchestrator.py - Orchestrateur complet pour SmartContractDevPipeline
import yaml
import logging
import asyncio
import json
import sys
import os
import uuid
import importlib.util
import inspect
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Set, Tuple, Callable, Union
from dataclasses import dataclass, field, asdict
from enum import Enum
import traceback

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/orchestrator.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("SmartContractOrchestrator")

# Types de statut
class AgentStatus(Enum):
    NOT_LOADED = "not_loaded"
    LOADING = "loading"
    READY = "ready"
    BUSY = "busy"
    ERROR = "error"
    DISABLED = "disabled"

class TaskStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    BLOCKED = "blocked"

class SprintStatus(Enum):
    PLANNING = "planning"
    IN_PROGRESS = "in_progress"
    REVIEW = "review"
    COMPLETED = "completed"
    BLOCKED = "blocked"

class WorkflowStatus(Enum):
    NOT_STARTED = "not_started"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

@dataclass
class AgentInfo:
    """Information sur un agent"""
    name: str
    display_name: str
    specialization: str
    config_path: str
    agent_type: str
    enabled: bool
    instantiate: bool
    dependencies: List[str]
    initialization_order: int
    parent: Optional[str] = None
    status: AgentStatus = AgentStatus.NOT_LOADED
    instance: Any = None
    capabilities: List[str] = field(default_factory=list)
    last_health_check: Optional[datetime] = None
    mandatory: bool = True
    purpose: str = ""

@dataclass
class TaskDefinition:
    """Définition d'une tâche"""
    id: str
    name: str
    description: str
    required_agents: List[str]
    estimated_duration: int  # en minutes
    dependencies: List[str]
    priority: int = 3  # 1=haute, 5=basse
    required: bool = True
    phase: str = ""

@dataclass
class PhaseDefinition:
    """Définition d'une phase de workflow"""
    id: str
    name: str
    description: str
    order: int
    parallel_execution: bool
    timeout_minutes: int
    tasks: List[TaskDefinition]
    deliverables: List[str]
    success_criteria: List[str]
    required_agents: List[str] = field(default_factory=list)

@dataclass
class SprintInput:
    """Input pour un sprint"""
    sprint_id: str
    sprint_number: int
    title: str
    description: str
    objectives: List[str]
    user_stories: List[Dict[str, Any]]
    acceptance_criteria: Dict[str, List[str]]
    technical_constraints: Dict[str, Any]
    priority_features: List[str]
    start_date: datetime
    end_date: datetime
    dependencies: Dict[str, Any] = field(default_factory=dict)
    previous_sprint_output: Optional[Dict[str, Any]] = None

@dataclass
class SprintOutput:
    """Output d'un sprint"""
    sprint_id: str
    sprint_number: int
    status: SprintStatus
    start_date: datetime
    end_date: datetime
    actual_end_date: Optional[datetime] = None
    
    # Résultats
    objectives_achieved: List[str] = field(default_factory=list)
    objectives_pending: List[str] = field(default_factory=list)
    
    # Fonctionnalités
    features_completed: List[Dict[str, Any]] = field(default_factory=list)
    features_in_progress: List[Dict[str, Any]] = field(default_factory=list)
    features_blocked: List[Dict[str, Any]] = field(default_factory=list)
    
    # Qualité
    bugs_identified: List[Dict[str, Any]] = field(default_factory=list)
    bugs_resolved: List[Dict[str, Any]] = field(default_factory=list)
    bugs_open: List[Dict[str, Any]] = field(default_factory=list)
    
    # Métriques
    code_metrics: Dict[str, Any] = field(default_factory=dict)
    test_metrics: Dict[str, Any] = field(default_factory=dict)
    performance_metrics: Dict[str, Any] = field(default_factory=dict)
    security_metrics: Dict[str, Any] = field(default_factory=dict)
    
    # Documentation
    documentation_generated: List[Dict[str, Any]] = field(default_factory=list)
    documentation_updated: List[Dict[str, Any]] = field(default_factory=list)
    
    # Déploiement
    deployment_status: str = "not_deployed"
    deployment_artifacts: List[str] = field(default_factory=list)
    
    # Recommendations pour le prochain sprint
    recommendations_next_sprint: List[str] = field(default_factory=list)
    
    # Notes de rétrospective
    retrospective_notes: str = ""
    
    # Évaluation
    sprint_velocity: float = 0.0
    team_satisfaction: int = 0  # 1-5
    quality_score: int = 0  # 1-5
    
    # Fichiers générés
    generated_files: List[str] = field(default_factory=list)

@dataclass
class WorkflowExecution:
    """Exécution d'un workflow"""
    execution_id: str
    workflow_name: str
    start_time: datetime
    end_time: Optional[datetime] = None
    status: WorkflowStatus = WorkflowStatus.NOT_STARTED
    current_phase: Optional[str] = None
    current_task: Optional[str] = None
    phases_completed: List[str] = field(default_factory=list)
    phases_failed: List[str] = field(default_factory=list)
    tasks_completed: List[str] = field(default_factory=list)
    tasks_failed: List[str] = field(default_factory=list)
    tasks_blocked: List[str] = field(default_factory=list)
    results: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    execution_log: List[Dict[str, Any]] = field(default_factory=list)

@dataclass
class ProjectContext:
    """Contexte du projet"""
    project_name: str
    project_version: str
    current_sprint: Optional[int] = None
    active_workflows: List[str] = field(default_factory=list)
    completed_workflows: List[str] = field(default_factory=list)
    agents_available: List[str] = field(default_factory=list)
    agents_busy: List[str] = field(default_factory=list)
    last_update: datetime = field(default_factory=datetime.now)

# --------------------------------------------------------------------------
# CLASSE DE BASE POUR LES AGENTS
# --------------------------------------------------------------------------

class BaseAgent:
    """Classe de base pour tous les agents"""
    
    def __init__(self, name: str, agent_info: AgentInfo):
        self.name = name
        self.agent_info = agent_info
        self.config: Dict[str, Any] = {}
        self.capabilities: List[str] = []
        self.status: str = "initializing"
        self.last_execution: Optional[datetime] = None
        self.execution_history: List[Dict[str, Any]] = []
        self.task_queue: List[Dict[str, Any]] = []
        
        # Charger la configuration
        self.load_configuration()
        
        logger.info(f"Agent {name} initialisé")
    
    def load_configuration(self) -> bool:
        """Charge la configuration depuis le fichier YAML"""
        if not self.agent_info or not self.agent_info.config_path:
            logger.warning(f"Agent {self.name}: pas de chemin de configuration")
            return False
        
        try:
            config_file = self.agent_info.config_path
            if not os.path.exists(config_file):
                # Essayer de trouver le fichier dans différents chemins
                possible_paths = [
                    config_file,
                    f"../{config_file}",
                    f"../../{config_file}",
                    os.path.join("agents", self.name, "config.yaml"),
                    os.path.join("agents", self.agent_info.parent or "", "sous_agents", self.name, "config.yaml")
                ]
                
                for path in possible_paths:
                    if os.path.exists(path):
                        config_file = path
                        break
                else:
                    logger.warning(f"Agent {self.name}: fichier de configuration non trouvé")
                    return False
            
            with open(config_file, 'r', encoding='utf-8') as file:
                self.config = yaml.safe_load(file) or {}
            
            # Extraire les capacités
            self.capabilities = self.config.get('capabilities', [])
            
            logger.info(f"Agent {self.name}: configuration chargée ({len(self.capabilities)} capacités)")
            return True
            
        except Exception as e:
            logger.error(f"Agent {self.name}: erreur lors du chargement de la configuration: {e}")
            return False
    
    async def execute(self, task: str, **kwargs) -> Dict[str, Any]:
        """Exécute une tâche"""
        self.last_execution = datetime.now()
        start_time = datetime.now()
        
        logger.info(f"Agent {self.name} exécute la tâche: {task}")
        
        # Vérifier si la tâche est dans les capacités
        if task not in self.capabilities and "*" not in self.capabilities:
            error_msg = f"Tâche {task} non supportée par l'agent {self.name}"
            logger.warning(f"{error_msg}. Capacités: {self.capabilities}")
            
            return {
                "status": "failed",
                "error": error_msg,
                "capabilities": self.capabilities,
                "agent": self.name,
                "task": task,
                "execution_time": 0
            }
        
        try:
            # Vérifier s'il y a une méthode spécifique pour cette tâche
            task_method_name = f"execute_{task}"
            if hasattr(self, task_method_name):
                task_method = getattr(self, task_method_name)
                if callable(task_method):
                    result = await task_method(**kwargs)
                else:
                    result = await self._execute_generic_task(task, **kwargs)
            else:
                result = await self._execute_generic_task(task, **kwargs)
            
            # Ajouter des métadonnées
            if isinstance(result, dict):
                result.update({
                    "agent": self.name,
                    "task": task,
                    "execution_time": (datetime.now() - start_time).total_seconds(),
                    "timestamp": datetime.now().isoformat()
                })
                
                if "status" not in result:
                    result["status"] = "success"
            else:
                result = {
                    "status": "success",
                    "agent": self.name,
                    "task": task,
                    "result": result,
                    "execution_time": (datetime.now() - start_time).total_seconds(),
                    "timestamp": datetime.now().isoformat()
                }
            
            # Enregistrer dans l'historique
            self.execution_history.append({
                "task": task,
                "timestamp": datetime.now().isoformat(),
                "duration": result.get("execution_time", 0),
                "status": result.get("status", "unknown"),
                "parameters": kwargs
            })
            
            # Limiter la taille de l'historique
            if len(self.execution_history) > 100:
                self.execution_history = self.execution_history[-100:]
            
            return result
            
        except Exception as e:
            error_msg = f"Erreur lors de l'exécution de {task} par {self.name}: {e}"
            logger.error(error_msg)
            logger.error(traceback.format_exc())
            
            return {
                "status": "failed",
                "error": str(e),
                "traceback": traceback.format_exc(),
                "agent": self.name,
                "task": task,
                "execution_time": (datetime.now() - start_time).total_seconds(),
                "timestamp": datetime.now().isoformat()
            }
    
    async def _execute_generic_task(self, task: str, **kwargs) -> Dict[str, Any]:
        """Exécute une tâche générique"""
        # Simulation de l'exécution d'une tâche
        await asyncio.sleep(0.5)  # Simulation de travail
        
        return {
            "message": f"Tâche {task} exécutée par {self.name}",
            "details": kwargs,
            "simulated": True
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Vérification de santé de l'agent"""
        try:
            health_data = {
                "agent": self.name,
                "status": "healthy",
                "capabilities": len(self.capabilities),
                "last_execution": self.last_execution.isoformat() if self.last_execution else None,
                "execution_history_count": len(self.execution_history),
                "config_loaded": bool(self.config),
                "timestamp": datetime.now().isoformat()
            }
            
            # Vérifications supplémentaires selon le type d'agent
            if hasattr(self, 'additional_health_checks'):
                additional_checks = await self.additional_health_checks()
                health_data.update(additional_checks)
            
            return health_data
            
        except Exception as e:
            logger.error(f"Erreur lors du health check de {self.name}: {e}")
            return {
                "agent": self.name,
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def get_capabilities(self) -> List[str]:
        """Retourne les capacités de l'agent"""
        return self.capabilities
    
    async def get_status(self) -> Dict[str, Any]:
        """Retourne le statut détaillé de l'agent"""
        return {
            "name": self.name,
            "status": self.status,
            "config_loaded": bool(self.config),
            "capabilities": self.capabilities,
            "last_execution": self.last_execution,
            "execution_count": len(self.execution_history),
            "queue_length": len(self.task_queue)
        }

# --------------------------------------------------------------------------
# AGENTS SPÉCIALISÉS (exemples)
# --------------------------------------------------------------------------

class ArchitectAgent(BaseAgent):
    """Agent architecte pour la conception système"""
    
    def __init__(self, name: str, agent_info: AgentInfo):
        super().__init__(name, agent_info)
        self.architecture_designs = []
        self.tech_stacks = []
    
    async def execute_system_architecture(self, requirements: List[Dict], constraints: Dict) -> Dict[str, Any]:
        """Conçoit l'architecture système"""
        logger.info(f"{self.name} conçoit l'architecture pour {len(requirements)} exigences")
        
        # Simulation de conception d'architecture
        await asyncio.sleep(1)
        
        architecture = {
            "components": [
                {
                    "name": "Smart Contract Layer",
                    "technologies": ["Solidity", "Hardhat", "OpenZeppelin"],
                    "responsibilities": ["Logique métier", "Sécurité", "Transparence"]
                },
                {
                    "name": "Backend API",
                    "technologies": ["Node.js", "Express", "PostgreSQL"],
                    "responsibilities": ["Orchestration", "Persistance", "API Gateway"]
                },
                {
                    "name": "Frontend DApp",
                    "technologies": ["React", "Web3.js", "Ethers.js"],
                    "responsibilities": ["Interface utilisateur", "Connexion wallet", "Visualisation"]
                }
            ],
            "patterns": ["Microservices", "Event-Driven", "CQRS"],
            "security_considerations": ["Audit des contrats", "Validation des entrées", "Gestion des clés"],
            "scalability": ["Couche de cache", "Load balancing", "Base de données distribuée"],
            "created_by": self.name,
            "timestamp": datetime.now().isoformat()
        }
        
        self.architecture_designs.append(architecture)
        return architecture
    
    async def execute_select_tech_stack(self, requirements: Dict, constraints: Dict) -> Dict[str, Any]:
        """Sélectionne la stack technique"""
        tech_stack = {
            "blockchain": {
                "network": "Ethereum",
                "testnet": "Sepolia",
                "development_framework": "Hardhat",
                "testing_framework": "Waffle",
                "libraries": ["OpenZeppelin", "SafeMath"]
            },
            "backend": {
                "runtime": "Node.js 18+",
                "framework": "Express.js",
                "database": "PostgreSQL",
                "orm": "Prisma",
                "authentication": "JWT"
            },
            "frontend": {
                "framework": "React 18",
                "web3_library": "Ethers.js",
                "ui_library": "Material-UI",
                "state_management": "Redux Toolkit",
                "testing": "Jest + React Testing Library"
            },
            "devops": {
                "ci_cd": "GitHub Actions",
                "containerization": "Docker",
                "orchestration": "Kubernetes",
                "monitoring": "Prometheus + Grafana"
            }
        }
        
        self.tech_stacks.append(tech_stack)
        return tech_stack

class SmartContractAgent(BaseAgent):
    """Agent pour le développement de smart contracts"""
    
    def __init__(self, name: str, agent_info: AgentInfo):
        super().__init__(name, agent_info)
        self.contracts_developed = []
        self.security_audits = []
    
    async def execute_develop_contract(self, specification: Dict, requirements: Dict) -> Dict[str, Any]:
        """Développe un smart contract"""
        contract_name = specification.get('name', 'UnknownContract')
        logger.info(f"{self.name} développe le contrat: {contract_name}")
        
        await asyncio.sleep(2)  # Simulation de développement
        
        contract = {
            "name": contract_name,
            "type": specification.get('type', 'ERC20'),
            "solidity_version": ">=0.8.0 <0.9.0",
            "features": specification.get('features', []),
            "security_features": [
                "Reentrancy guard",
                "Overflow/underflow protection",
                "Access control",
                "Event emissions"
            ],
            "functions": self._generate_contract_functions(specification),
            "events": self._generate_contract_events(specification),
            "tests_included": True,
            "documentation": f"docs/contracts/{contract_name}.md",
            "source_code": f"contracts/{contract_name}.sol",
            "developed_by": self.name,
            "timestamp": datetime.now().isoformat()
        }
        
        self.contracts_developed.append(contract)
        return contract
    
    def _generate_contract_functions(self, spec: Dict) -> List[Dict]:
        """Génère les fonctions du contrat"""
        functions = []
        
        if spec.get('type') == 'ERC20':
            functions = [
                {"name": "transfer", "visibility": "public", "returns": "bool"},
                {"name": "approve", "visibility": "public", "returns": "bool"},
                {"name": "transferFrom", "visibility": "public", "returns": "bool"},
                {"name": "balanceOf", "visibility": "view", "returns": "uint256"},
                {"name": "totalSupply", "visibility": "view", "returns": "uint256"}
            ]
        
        if 'mint' in spec.get('features', []):
            functions.append({"name": "mint", "visibility": "public", "returns": "bool"})
        
        if 'burn' in spec.get('features', []):
            functions.append({"name": "burn", "visibility": "public", "returns": "bool"})
        
        return functions
    
    def _generate_contract_events(self, spec: Dict) -> List[Dict]:
        """Génère les événements du contrat"""
        events = [
            {"name": "Transfer", "parameters": ["address indexed from", "address indexed to", "uint256 value"]},
            {"name": "Approval", "parameters": ["address indexed owner", "address indexed spender", "uint256 value"]}
        ]
        
        if 'mint' in spec.get('features', []):
            events.append({"name": "Mint", "parameters": ["address indexed to", "uint256 amount"]})
        
        if 'burn' in spec.get('features', []):
            events.append({"name": "Burn", "parameters": ["address indexed from", "uint256 amount"]})
        
        return events

class TesterAgent(BaseAgent):
    """Agent pour les tests et la qualité"""
    
    def __init__(self, name: str, agent_info: AgentInfo):
        super().__init__(name, agent_info)
        self.test_reports = []
        self.bugs_found = []
    
    async def execute_security_audit(self, contracts: List[Dict], requirements: Dict) -> Dict[str, Any]:
        """Effectue un audit de sécurité"""
        logger.info(f"{self.name} effectue un audit de sécurité sur {len(contracts)} contrats")
        
        await asyncio.sleep(1.5)
        
        vulnerabilities = []
        
        # Simulation de détection de vulnérabilités
        for contract in contracts:
            contract_name = contract.get('name', 'Unknown')
            
            # Vulnérabilités simulées (dans un vrai système, utiliser des outils comme Slither)
            potential_vulns = [
                {
                    "contract": contract_name,
                    "severity": "low",
                    "type": "missing_events",
                    "description": "Fonctions critiques ne déclenchent pas d'événements",
                    "recommendation": "Ajouter des événements pour toutes les fonctions modifiant l'état"
                },
                {
                    "contract": contract_name,
                    "severity": "medium",
                    "type": "access_control",
                    "description": "Contrôles d'accès insuffisants pour les fonctions sensibles",
                    "recommendation": "Implémenter un système de contrôle d'accès avec rôles"
                }
            ]
            
            vulnerabilities.extend(potential_vulns)
        
        audit_report = {
            "audit_date": datetime.now().isoformat(),
            "contracts_audited": len(contracts),
            "vulnerabilities_found": len(vulnerabilities),
            "vulnerabilities": vulnerabilities,
            "security_score": max(0, 100 - len(vulnerabilities) * 10),
            "recommendations": [
                "Effectuer des tests formels",
                "Implémenter plus de tests unitaires",
                "Revue manuelle du code par un expert"
            ],
            "auditor": self.name
        }
        
        self.test_reports.append(audit_report)
        self.bugs_found.extend(vulnerabilities)
        
        return audit_report

# --------------------------------------------------------------------------
# ORCHESTRATEUR PRINCIPAL
# --------------------------------------------------------------------------

class SmartContractOrchestrator:
    """Orchestrateur principal qui gère les agents et les sprints"""
    
    def __init__(self, config_path: str = "project_config.yaml"):
        self.config_path = config_path
        self.project_config: Dict[str, Any] = {}
        self.agents: Dict[str, AgentInfo] = {}
        self.agent_instances: Dict[str, Any] = {}
        self.sprints: Dict[str, SprintOutput] = {}
        self.active_workflows: Dict[str, WorkflowExecution] = {}
        self.task_queue: List[Dict[str, Any]] = []
        self.project_context = ProjectContext(
            project_name="SmartContractDevPipeline",
            project_version="3.0.0"
        )
        
        # État du système
        self.system_status: str = "initializing"
        self.last_health_check: Optional[datetime] = None
        self.start_time = datetime.now()
        
        # Registre des types d'agents
        self.agent_classes = {
            "architect": ArchitectAgent,
            "smart_contract": SmartContractAgent,
            "tester": TesterAgent,
            # Les autres agents utiliseront BaseAgent par défaut
        }
    
    # --------------------------------------------------------------------------
    # INITIALISATION ET CHARGEMENT
    # --------------------------------------------------------------------------
    
    def load_configuration(self) -> bool:
        """Charge la configuration depuis le fichier YAML"""
        try:
            logger.info(f"Chargement de la configuration depuis {self.config_path}")
            
            if not os.path.exists(self.config_path):
                logger.error(f"Fichier de configuration non trouvé: {self.config_path}")
                return False
            
            with open(self.config_path, 'r', encoding='utf-8') as file:
                self.project_config = yaml.safe_load(file)
            
            logger.info(f"Configuration chargée: {self.project_config.get('project_name', 'Unknown')} v{self.project_config.get('version', '1.0.0')}")
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors du chargement de la configuration: {e}")
            logger.error(traceback.format_exc())
            return False
    
    def parse_agents_configuration(self) -> bool:
        """Parse la configuration des agents depuis le fichier YAML"""
        try:
            # Charger les agents principaux
            required_agents = self.project_config.get('required_agents', [])
            
            for agent_data in required_agents:
                agent_info = AgentInfo(
                    name=agent_data['name'],
                    display_name=agent_data.get('display_name', agent_data['name']),
                    specialization=agent_data.get('specialization', 'default'),
                    config_path=agent_data.get('config', ''),
                    agent_type=agent_data.get('agent_type', 'main_agent'),
                    enabled=agent_data.get('enabled', True),
                    instantiate=agent_data.get('instantiate', True),
                    dependencies=agent_data.get('dependencies', []),
                    initialization_order=agent_data.get('initialization_order', 999),
                    mandatory=agent_data.get('mandatory', True),
                    purpose=agent_data.get('purpose', '')
                )
                
                self.agents[agent_data['name']] = agent_info
                logger.info(f"Agent configuré: {agent_data['name']} ({agent_info.agent_type})")
            
            # Charger les sous-agents
            specialized_sub_agents = self.project_config.get('specialized_sub_agents', {})
            
            for category, subagents_list in specialized_sub_agents.items():
                parent_agent = category.replace('_subagents', '')
                
                for subagent_data in subagents_list:
                    agent_info = AgentInfo(
                        name=subagent_data['name'],
                        display_name=subagent_data.get('type', subagent_data['name']),
                        specialization=subagent_data.get('type', 'specialized'),
                        config_path=subagent_data.get('config', ''),
                        agent_type='sub_agent',
                        enabled=subagent_data.get('enabled', True),
                        instantiate=False,  # Instanciés à la demande
                        dependencies=subagent_data.get('dependencies', []),
                        initialization_order=999,
                        parent=parent_agent
                    )
                    
                    self.agents[subagent_data['name']] = agent_info
                    logger.info(f"Sous-agent configuré: {subagent_data['name']} (parent: {parent_agent})")
            
            logger.info(f"Total agents configurés: {len(self.agents)}")
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors du parsing de la configuration des agents: {e}")
            logger.error(traceback.format_exc())
            return False
    
    def load_agent_module(self, agent_name: str) -> Optional[Any]:
        """Charge dynamiquement un module d'agent"""
        agent_info = self.agents.get(agent_name)
        if not agent_info:
            logger.error(f"Agent {agent_name} non trouvé dans la configuration")
            return None
        
        try:
            # Chercher le fichier de l'agent
            agent_dir = os.path.dirname(agent_info.config_path)
            agent_file = os.path.join(agent_dir, f"{agent_name}.py")
            
            # Si le fichier n'existe pas, chercher dans d'autres emplacements
            if not os.path.exists(agent_file):
                possible_paths = [
                    agent_file,
                    f"agents/{agent_name}/{agent_name}.py",
                    f"agents/{agent_name}.py",
                    f"../agents/{agent_name}/{agent_name}.py"
                ]
                
                for path in possible_paths:
                    if os.path.exists(path):
                        agent_file = path
                        break
                else:
                    logger.warning(f"Fichier d'agent non trouvé pour {agent_name}, utilisation de la classe par défaut")
                    return None
            
            # Charger le module
            spec = importlib.util.spec_from_file_location(f"agents.{agent_name}", agent_file)
            if spec is None:
                logger.warning(f"Impossible de charger le module pour {agent_name}")
                return None
            
            module = importlib.util.module_from_spec(spec)
            sys.modules[spec.name] = module
            
            try:
                spec.loader.exec_module(module)
                logger.info(f"Module chargé pour l'agent {agent_name}")
                return module
            except Exception as e:
                logger.error(f"Erreur lors de l'exécution du module {agent_name}: {e}")
                return None
                
        except Exception as e:
            logger.error(f"Erreur lors du chargement du module {agent_name}: {e}")
            return None
    
    def create_agent_instance(self, agent_name: str) -> Optional[Any]:
        """Crée une instance d'agent"""
        agent_info = self.agents.get(agent_name)
        if not agent_info:
            logger.error(f"Agent {agent_name} non trouvé")
            return None
        
        if agent_info.agent_type == "abstract_base":
            logger.warning(f"L'agent {agent_name} est abstrait et ne doit pas être instancié")
            return None
        
        try:
            # Chercher une classe d'agent spécifique
            agent_class = None
            
            # 1. Chercher dans les classes prédéfinies
            if agent_name in self.agent_classes:
                agent_class = self.agent_classes[agent_name]
            else:
                # 2. Chercher dans le module chargé
                module = self.load_agent_module(agent_name)
                if module:
                    # Chercher une classe avec un nom correspondant
                    for attr_name in dir(module):
                        attr = getattr(module, attr_name)
                        if (inspect.isclass(attr) and 
                            attr_name.lower().endswith('agent') and
                            attr_name != 'BaseAgent' and
                            hasattr(attr, 'execute')):
                            agent_class = attr
                            break
            
            # 3. Utiliser BaseAgent par défaut
            if agent_class is None:
                agent_class = BaseAgent
            
            # Créer l'instance
            agent_instance = agent_class(agent_name, agent_info)
            agent_info.instance = agent_instance
            agent_info.status = AgentStatus.READY
            agent_info.last_health_check = datetime.now()
            
            # Charger les capacités depuis task_mapping
            task_mapping = self.project_config.get('task_mapping', {})
            agent_info.capabilities = [
                task for task, agents in task_mapping.items() 
                if agent_name in agents or "*" in agents
            ]
            
            logger.info(f"Instance créée pour l'agent {agent_name} ({agent_class.__name__}) avec {len(agent_info.capabilities)} capacités")
            return agent_instance
            
        except Exception as e:
            logger.error(f"Erreur lors de la création de l'instance pour {agent_name}: {e}")
            logger.error(traceback.format_exc())
            agent_info.status = AgentStatus.ERROR
            return None
    
    async def initialize_agents(self) -> bool:
        """Initialise tous les agents selon l'ordre de dépendances"""
        logger.info("Initialisation des agents...")
        
        # Trier les agents par ordre d'initialisation et dépendances
        agents_to_initialize = self.get_sorted_agents_by_dependencies()
        
        initialization_results = []
        for agent_name in agents_to_initialize:
            agent_info = self.agents.get(agent_name)
            if not agent_info:
                logger.warning(f"Agent {agent_name} non trouvé, ignoré")
                initialization_results.append((agent_name, False, "Non trouvé"))
                continue
            
            if not agent_info.enabled:
                logger.info(f"Agent {agent_name} désactivé, ignoré")
                agent_info.status = AgentStatus.DISABLED
                initialization_results.append((agent_name, True, "Désactivé"))
                continue
            
            if not agent_info.instantiate:
                logger.info(f"Agent {agent_name} non instanciable, ignoré")
                initialization_results.append((agent_name, True, "Non instanciable"))
                continue
            
            if agent_info.status == AgentStatus.READY:
                logger.info(f"Agent {agent_name} déjà initialisé")
                initialization_results.append((agent_name, True, "Déjà initialisé"))
                continue
            
            logger.info(f"Initialisation de l'agent: {agent_name} (ordre: {agent_info.initialization_order})")
            
            agent_info.status = AgentStatus.LOADING
            agent_instance = self.create_agent_instance(agent_name)
            
            if agent_instance:
                self.agent_instances[agent_name] = agent_instance
                
                # Vérification de santé
                try:
                    health_result = await agent_instance.health_check()
                    if health_result.get('status') == 'healthy':
                        logger.info(f"✓ Agent {agent_name} initialisé avec succès")
                        initialization_results.append((agent_name, True, "Succès"))
                        self.project_context.agents_available.append(agent_name)
                    else:
                        logger.warning(f"Agent {agent_name} en état douteux: {health_result}")
                        initialization_results.append((agent_name, False, f"État douteux: {health_result.get('status')}"))
                except Exception as e:
                    logger.error(f"Échec du health check pour {agent_name}: {e}")
                    initialization_results.append((agent_name, False, f"Health check échoué: {e}"))
            else:
                logger.error(f"Échec de l'initialisation de l'agent {agent_name}")
                initialization_results.append((agent_name, False, "Échec de création"))
                if agent_info.mandatory:
                    logger.critical(f"Agent obligatoire {agent_name} non initialisé")
        
        # Afficher le résumé
        successful = sum(1 for _, success, _ in initialization_results if success)
        total = len(initialization_results)
        
        logger.info(f"Initialisation terminée: {successful}/{total} agents initialisés avec succès")
        
        if successful == 0 and total > 0:
            logger.error("Aucun agent n'a pu être initialisé")
            return False
        
        return True
    
    def get_sorted_agents_by_dependencies(self) -> List[str]:
        """Retourne les agents triés par dépendances (tri topologique)"""
        # Créer un graphe des dépendances
        graph = {name: set(info.dependencies) for name, info in self.agents.items()}
        
        # Tri topologique
        visited = set()
        temp = set()
        result = []
        
        def visit(node):
            if node in temp:
                raise Exception(f"Dépendance circulaire détectée impliquant {node}")
            if node not in visited:
                temp.add(node)
                for neighbor in graph.get(node, set()):
                    if neighbor in self.agents:  # Ne visiter que les agents existants
                        visit(neighbor)
                temp.remove(node)
                visited.add(node)
                result.append(node)
        
        # Visiter tous les agents qui doivent être instanciés
        for agent_name, agent_info in self.agents.items():
            if agent_info.enabled and agent_info.instantiate and agent_name not in visited:
                try:
                    visit(agent_name)
                except Exception as e:
                    logger.error(f"Erreur lors du tri des dépendances: {e}")
        
        return result
    
    # --------------------------------------------------------------------------
    # GESTION DES TÂCHES ET WORKFLOWS
    # --------------------------------------------------------------------------
    
    def find_agents_for_task(self, task_name: str) -> List[str]:
        """Trouve les agents capables d'exécuter une tâche"""
        task_mapping = self.project_config.get('task_mapping', {})
        agents = task_mapping.get(task_name, [])
        
        if "*" in agents:
            # Tous les agents peuvent exécuter cette tâche
            return [name for name, info in self.agents.items() 
                   if info.enabled and info.status == AgentStatus.READY]
        
        # Filtrer les agents disponibles
        available_agents = []
        for agent_name in agents:
            agent_info = self.agents.get(agent_name)
            if agent_info and agent_info.enabled and agent_info.status == AgentStatus.READY:
                available_agents.append(agent_name)
        
        return available_agents
    
    async def execute_task(self, task_name: str, parameters: Dict[str, Any] = None, 
                          preferred_agent: Optional[str] = None, 
                          timeout: int = 300) -> Dict[str, Any]:
        """Exécute une tâche avec l'agent approprié"""
        logger.info(f"Exécution de la tâche: {task_name}")
        
        # Trouver les agents capables
        capable_agents = self.find_agents_for_task(task_name)
        
        if not capable_agents:
            return {
                "status": "failed",
                "error": f"Aucun agent capable d'exécuter la tâche: {task_name}",
                "task": task_name,
                "timestamp": datetime.now().isoformat(),
                "available_agents": list(self.agent_instances.keys())
            }
        
        # Choisir l'agent
        selected_agent = None
        if preferred_agent and preferred_agent in capable_agents:
            selected_agent = preferred_agent
            logger.info(f"Utilisation de l'agent préféré: {selected_agent}")
        else:
            # Choisir l'agent avec le moins de tâches en cours (simplifié)
            selected_agent = capable_agents[0]
            logger.info(f"Utilisation de l'agent: {selected_agent}")
        
        # Exécuter la tâche avec timeout
        agent_instance = self.agent_instances.get(selected_agent)
        if not agent_instance:
            return {
                "status": "failed",
                "error": f"Agent {selected_agent} non disponible",
                "task": task_name,
                "capable_agents": capable_agents
            }
        
        try:
            parameters = parameters or {}
            
            # Exécuter avec timeout
            task_coro = agent_instance.execute(task_name, **parameters)
            result = await asyncio.wait_for(task_coro, timeout=timeout)
            
            # Mettre à jour le contexte
            self.project_context.last_update = datetime.now()
            if selected_agent in self.project_context.agents_available:
                self.project_context.agents_busy.append(selected_agent)
                # Retirer après un délai simulé
                await asyncio.sleep(0.1)
                if selected_agent in self.project_context.agents_busy:
                    self.project_context.agents_busy.remove(selected_agent)
            
            return result
            
        except asyncio.TimeoutError:
            error_msg = f"Timeout lors de l'exécution de {task_name} par {selected_agent}"
            logger.error(error_msg)
            return {
                "status": "failed",
                "error": error_msg,
                "task": task_name,
                "agent": selected_agent,
                "timeout": timeout,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Erreur lors de l'exécution de {task_name} par {selected_agent}: {e}")
            logger.error(traceback.format_exc())
            return {
                "status": "failed",
                "error": str(e),
                "task": task_name,
                "agent": selected_agent,
                "traceback": traceback.format_exc(),
                "timestamp": datetime.now().isoformat()
            }
    
    async def execute_workflow(self, workflow_name: str, 
                              parameters: Dict[str, Any] = None) -> Dict[str, Any]:
        """Exécute un workflow défini dans la configuration"""
        workflows = self.project_config.get('workflow_configurations', {})
        workflow = workflows.get(workflow_name)
        
        if not workflow:
            return {
                "status": "failed",
                "error": f"Workflow '{workflow_name}' non trouvé"
            }
        
        execution_id = str(uuid.uuid4())[:8]
        execution = WorkflowExecution(
            execution_id=execution_id,
            workflow_name=workflow_name,
            start_time=datetime.now(),
            status=WorkflowStatus.RUNNING
        )
        
        self.active_workflows[execution_id] = execution
        self.project_context.active_workflows.append(execution_id)
        
        logger.info(f"Début du workflow {workflow_name} (ID: {execution_id})")
        
        try:
            # Récupérer la configuration du workflow
            agents_needed = workflow.get('agents', [])
            use_subagents = workflow.get('use_subagents', False)
            subagents_needed = workflow.get('subagents', [])
            sequential = workflow.get('sequential', True)
            steps = workflow.get('steps', [])
            timeout = workflow.get('timeout', 300)
            expected_result = workflow.get('expected_result', '')
            
            # Vérifier la disponibilité des agents
            missing_agents = []
            for agent_name in agents_needed:
                if agent_name not in self.agent_instances:
                    missing_agents.append(agent_name)
            
            if missing_agents:
                error_msg = f"Agents manquants: {missing_agents}"
                execution.errors.append(error_msg)
                execution.status = WorkflowStatus.FAILED
                execution.end_time = datetime.now()
                
                return {
                    "status": "failed",
                    "error": error_msg,
                    "execution_id": execution_id
                }
            
            # Exécuter les étapes
            results = {}
            execution_steps = steps if steps else ['initialization', 'execution', 'validation']
            
            for step in execution_steps:
                execution.current_task = step
                logger.info(f"Exécution de l'étape: {step}")
                
                # Déterminer la tâche à exécuter pour cette étape
                task_to_execute = self.map_step_to_task(step, workflow)
                
                if task_to_execute:
                    task_result = await self.execute_task(task_to_execute, parameters)
                    
                    # Enregistrer dans le log d'exécution
                    execution.execution_log.append({
                        "step": step,
                        "task": task_to_execute,
                        "result": task_result,
                        "timestamp": datetime.now().isoformat()
                    })
                    
                    if task_result.get('status') == 'success':
                        execution.tasks_completed.append(step)
                        results[step] = task_result
                        logger.info(f"✓ Étape {step} terminée avec succès")
                    else:
                        execution.tasks_failed.append(step)
                        results[step] = task_result
                        execution.errors.append(f"Étape {step} échouée: {task_result.get('error')}")
                        logger.error(f"✗ Étape {step} échouée: {task_result.get('error')}")
                        
                        # Gestion d'erreur selon la configuration
                        if workflow.get('critical', True):
                            execution.status = WorkflowStatus.FAILED
                            break
                else:
                    # Aucune tâche spécifique pour cette étape
                    execution.tasks_completed.append(step)
                    results[step] = {"status": "skipped", "reason": "No specific task"}
                    logger.info(f"→ Étape {step} ignorée (pas de tâche spécifique)")
            
            # Finaliser l'exécution
            execution.end_time = datetime.now()
            execution.results = results
            execution.duration = (execution.end_time - execution.start_time).total_seconds()
            
            if execution.status == WorkflowStatus.RUNNING:
                if execution.tasks_failed:
                    execution.status = WorkflowStatus.COMPLETED
                    execution.warnings.append("Workflow terminé avec des erreurs")
                else:
                    execution.status = WorkflowStatus.COMPLETED
            
            # Mettre à jour le contexte
            self.project_context.active_workflows.remove(execution_id)
            self.project_context.completed_workflows.append(execution_id)
            self.project_context.last_update = datetime.now()
            
            logger.info(f"Workflow {workflow_name} terminé: {execution.status.value}")
            logger.info(f"Durée: {execution.duration:.2f} secondes")
            logger.info(f"Tâches: {len(execution.tasks_completed)} réussies, {len(execution.tasks_failed)} échouées")
            
            return {
                "status": "success",
                "execution_id": execution_id,
                "workflow_name": workflow_name,
                "workflow_status": execution.status.value,
                "start_time": execution.start_time.isoformat(),
                "end_time": execution.end_time.isoformat(),
                "duration_seconds": execution.duration,
                "tasks_completed": len(execution.tasks_completed),
                "tasks_failed": len(execution.tasks_failed),
                "results": results,
                "errors": execution.errors,
                "warnings": execution.warnings
            }
            
        except Exception as e:
            logger.error(f"Erreur lors de l'exécution du workflow {workflow_name}: {e}")
            logger.error(traceback.format_exc())
            
            execution.status = WorkflowStatus.FAILED
            execution.end_time = datetime.now()
            execution.errors.append(str(e))
            
            # Mettre à jour le contexte
            if execution_id in self.project_context.active_workflows:
                self.project_context.active_workflows.remove(execution_id)
            
            return {
                "status": "failed",
                "error": str(e),
                "execution_id": execution_id,
                "traceback": traceback.format_exc()
            }
    
    def map_step_to_task(self, step: str, workflow: Dict[str, Any]) -> Optional[str]:
        """Mappe une étape de workflow à une tâche spécifique"""
        # Mapping simple - dans un vrai système, ce serait configurable
        mapping = {
            "initialization": "validate_config",
            "architecture_design": "system_architecture",
            "contract_development": "develop_contract",
            "frontend_integration": "dapp_development",
            "testing": "security_audit",
            "deployment": "deploy_contract",
            "security_audit": "security_audit",
            "documentation": "generate_code"
        }
        
        return mapping.get(step)
    
    # --------------------------------------------------------------------------
    # GESTION DES SPRINTS
    # --------------------------------------------------------------------------
    
    async def execute_sprint(self, sprint_input: SprintInput) -> SprintOutput:
        """Exécute un sprint complet de développement"""
        logger.info(f"\n{'='*60}")
        logger.info(f"DÉBUT DU SPRINT {sprint_input.sprint_number}: {sprint_input.title}")
        logger.info(f"{'='*60}")
        
        # Initialiser l'output du sprint
        sprint_output = SprintOutput(
            sprint_id=sprint_input.sprint_id,
            sprint_number=sprint_input.sprint_number,
            status=SprintStatus.IN_PROGRESS,
            start_date=sprint_input.start_date,
            end_date=sprint_input.end_date
        )
        
        sprint_results = {}
        
        try:
            # PHASE 1: PLANIFICATION ET ARCHITECTURE
            logger.info("\n[PHASE 1] Planification et architecture")
            
            # 1.1 Architecture système
            arch_result = await self.execute_task(
                "system_architecture",
                {
                    "requirements": sprint_input.user_stories,
                    "constraints": sprint_input.technical_constraints,
                    "objectives": sprint_input.objectives,
                    "sprint_number": sprint_input.sprint_number
                },
                preferred_agent="architect",
                timeout=600
            )
            
            sprint_results["architecture"] = arch_result
            
            if arch_result.get('status') != 'success':
                sprint_output.status = SprintStatus.BLOCKED
                sprint_output.retrospective_notes = f"Échec de l'architecture: {arch_result.get('error')}"
                return sprint_output
            
            # 1.2 Stack technique
            tech_result = await self.execute_task(
                "select_tech_stack",
                {
                    "architecture": arch_result.get('result', {}),
                    "requirements": sprint_input.technical_constraints,
                    "previous_sprint": sprint_input.previous_sprint_output
                },
                preferred_agent="architect"
            )
            
            sprint_results["tech_stack"] = tech_result
            
            # PHASE 2: DÉVELOPPEMENT SMART CONTRACTS
            logger.info("\n[PHASE 2] Développement smart contracts")
            
            contract_results = []
            for user_story in sprint_input.user_stories:
                if user_story.get('type') in ['smart_contract', 'contract', 'blockchain']:
                    logger.info(f"  Développement du contrat: {user_story.get('name', 'Unnamed')}")
                    
                    contract_result = await self.execute_task(
                        "develop_contract",
                        {
                            "user_story": user_story,
                            "architecture": arch_result.get('result', {}),
                            "tech_stack": tech_result.get('result', {}),
                            "acceptance_criteria": sprint_input.acceptance_criteria.get(user_story.get('id', ''), [])
                        },
                        preferred_agent="smart_contract",
                        timeout=900
                    )
                    
                    contract_results.append(contract_result)
                    
                    if contract_result.get('status') == 'success':
                        sprint_output.features_completed.append({
                            "id": user_story.get('id'),
                            "name": user_story.get('name'),
                            "type": "smart_contract",
                            "result": contract_result,
                            "completion_date": datetime.now().isoformat()
                        })
                        
                        # Ajouter les fichiers générés
                        generated_files = contract_result.get('result', {}).get('generated_files', [])
                        if generated_files:
                            sprint_output.generated_files.extend(generated_files)
                        
                        logger.info(f"  ✓ Contrat {user_story.get('name')} développé avec succès")
                    else:
                        sprint_output.features_blocked.append({
                            "id": user_story.get('id'),
                            "name": user_story.get('name'),
                            "type": "smart_contract",
                            "error": contract_result.get('error'),
                            "blocked_date": datetime.now().isoformat()
                        })
                        logger.error(f"  ✗ Échec du contrat {user_story.get('name')}: {contract_result.get('error')}")
            
            sprint_results["contracts"] = contract_results
            
            # PHASE 3: AUDIT DE SÉCURITÉ
            logger.info("\n[PHASE 3] Audit de sécurité")
            
            if contract_results:
                security_result = await self.execute_task(
                    "security_audit",
                    {
                        "contracts": [r.get('result', {}) for r in contract_results if r.get('status') == 'success'],
                        "requirements": sprint_input.acceptance_criteria,
                        "security_requirements": sprint_input.technical_constraints.get('security', {})
                    },
                    preferred_agent="tester",
                    timeout=1200
                )
                
                sprint_results["security_audit"] = security_result
                
                if security_result.get('status') == 'success':
                    vulnerabilities = security_result.get('result', {}).get('vulnerabilities', [])
                    sprint_output.bugs_identified.extend(vulnerabilities)
                    sprint_output.security_metrics = security_result.get('result', {}).get('metrics', {})
                    
                    logger.info(f"  Audit de sécurité terminé: {len(vulnerabilities)} vulnérabilités trouvées")
                else:
                    sprint_output.warnings.append(f"Audit de sécurité échoué: {security_result.get('error')}")
                    logger.warning(f"  Audit de sécurité échoué: {security_result.get('error')}")
            
            # PHASE 4: DÉVELOPPEMENT FRONTEND/DAPP
            logger.info("\n[PHASE 4] Développement frontend/DApp")
            
            frontend_results = []
            for user_story in sprint_input.user_stories:
                if user_story.get('type') in ['frontend', 'ui', 'dapp', 'web3']:
                    logger.info(f"  Développement frontend: {user_story.get('name', 'Unnamed')}")
                    
                    frontend_result = await self.execute_task(
                        "dapp_development",
                        {
                            "user_story": user_story,
                            "contracts": [r.get('result', {}) for r in contract_results if r.get('status') == 'success'],
                            "design_constraints": sprint_input.technical_constraints.get('ui', {}),
                            "tech_stack": tech_result.get('result', {})
                        },
                        preferred_agent="frontend_web3",
                        timeout=600
                    )
                    
                    frontend_results.append(frontend_result)
                    
                    if frontend_result.get('status') == 'success':
                        sprint_output.features_completed.append({
                            "id": user_story.get('id'),
                            "name": user_story.get('name'),
                            "type": "frontend",
                            "result": frontend_result,
                            "completion_date": datetime.now().isoformat()
                        })
                        
                        # Ajouter les fichiers générés
                        generated_files = frontend_result.get('result', {}).get('generated_files', [])
                        if generated_files:
                            sprint_output.generated_files.extend(generated_files)
                        
                        logger.info(f"  ✓ Frontend {user_story.get('name')} développé avec succès")
                    else:
                        sprint_output.features_in_progress.append({
                            "id": user_story.get('id'),
                            "name": user_story.get('name'),
                            "type": "frontend",
                            "status": "blocked",
                            "error": frontend_result.get('error'),
                            "last_update": datetime.now().isoformat()
                        })
                        logger.warning(f"  ⚠ Frontend {user_story.get('name')} bloqué: {frontend_result.get('error')}")
            
            sprint_results["frontend"] = frontend_results
            
            # PHASE 5: TESTS D'INTÉGRATION
            logger.info("\n[PHASE 5] Tests d'intégration")
            
            integration_result = await self.execute_task(
                "integration_testing",
                {
                    "contracts": [r.get('result', {}) for r in contract_results if r.get('status') == 'success'],
                    "frontend": [r.get('result', {}) for r in frontend_results if r.get('status') == 'success'],
                    "acceptance_criteria": sprint_input.acceptance_criteria,
                    "user_stories": sprint_input.user_stories
                },
                preferred_agent="tester",
                timeout=900
            )
            
            sprint_results["integration_tests"] = integration_result
            
            if integration_result.get('status') == 'success':
                test_metrics = integration_result.get('result', {}).get('metrics', {})
                sprint_output.test_metrics.update(test_metrics)
                
                # Identifier les bugs
                bugs = integration_result.get('result', {}).get('bugs', [])
                sprint_output.bugs_identified.extend(bugs)
                
                logger.info(f"  Tests d'intégration terminés: {test_metrics.get('tests_passed', 0)}/{test_metrics.get('tests_total', 0)} tests passés")
            else:
                sprint_output.warnings.append(f"Tests d'intégration échoués: {integration_result.get('error')}")
                logger.warning(f"  ⚠ Tests d'intégration échoués: {integration_result.get('error')}")
            
            # PHASE 6: DÉPLOIEMENT
            logger.info("\n[PHASE 6] Déploiement")
            
            successful_contracts = [r.get('result', {}) for r in contract_results if r.get('status') == 'success']
            if successful_contracts:
                deployment_result = await self.execute_task(
                    "deploy_contract",
                    {
                        "contracts": successful_contracts,
                        "environment": "staging",
                        "network": sprint_input.technical_constraints.get('blockchain_network', 'sepolia')
                    },
                    preferred_agent="smart_contract",
                    timeout=1200
                )
                
                sprint_results["deployment"] = deployment_result
                
                if deployment_result.get('status') == 'success':
                    sprint_output.deployment_status = "staging"
                    artifacts = deployment_result.get('result', {}).get('artifacts', [])
                    sprint_output.deployment_artifacts.extend(artifacts)
                    
                    logger.info(f"  Déploiement réussi: {len(artifacts)} artefacts déployés")
                else:
                    sprint_output.warnings.append(f"Déploiement échoué: {deployment_result.get('error')}")
                    logger.warning(f"  ⚠ Déploiement échoué: {deployment_result.get('error')}")
            
            # PHASE 7: DOCUMENTATION
            logger.info("\n[PHASE 7] Documentation")
            
            doc_result = await self.execute_task(
                "generate_code",
                {
                    "type": "documentation",
                    "features": sprint_output.features_completed,
                    "contracts": [r.get('result', {}) for r in contract_results if r.get('status') == 'success'],
                    "sprint_info": {
                        "number": sprint_input.sprint_number,
                        "title": sprint_input.title,
                        "objectives": sprint_input.objectives
                    }
                },
                preferred_agent="coder",
                timeout=300
            )
            
            if doc_result.get('status') == 'success':
                docs = doc_result.get('result', {}).get('documents', [])
                sprint_output.documentation_generated = docs
                logger.info(f"  Documentation générée: {len(docs)} documents")
            
            # PHASE 8: ÉVALUATION DU SPRINT
            logger.info("\n[PHASE 8] Évaluation du sprint")
            
            # Calculer les objectifs atteints
            for objective in sprint_input.objectives:
                # Logique simplifiée d'évaluation
                objective_lower = objective.lower()
                achieved = False
                
                # Vérifier dans les fonctionnalités complétées
                for feature in sprint_output.features_completed:
                    if objective_lower in feature.get('name', '').lower() or \
                       objective_lower in feature.get('type', '').lower():
                        achieved = True
                        break
                
                if achieved:
                    sprint_output.objectives_achieved.append(objective)
                else:
                    sprint_output.objectives_pending.append(objective)
            
            # Calculer la vélocité
            total_stories = len(sprint_input.user_stories)
            completed_stories = len(sprint_output.features_completed)
            sprint_output.sprint_velocity = (completed_stories / total_stories * 100) if total_stories > 0 else 0
            
            # Générer les notes de rétrospective
            sprint_output.retrospective_notes = self.generate_retrospective_notes(sprint_output)
            
            # Générer les recommandations
            sprint_output.recommendations_next_sprint = self.generate_recommendations(sprint_output)
            
            # Calculer les scores
            sprint_output.quality_score = self.calculate_quality_score(sprint_output)
            sprint_output.team_satisfaction = self.calculate_satisfaction_score(sprint_output)
            
            # Finaliser le sprint
            sprint_output.actual_end_date = datetime.now()
            sprint_output.status = SprintStatus.COMPLETED
            
            # Sauvegarder le résultat
            self.sprints[sprint_input.sprint_id] = sprint_output
            
            # Afficher le résumé
            logger.info(f"\n{'='*60}")
            logger.info(f"FIN DU SPRINT {sprint_input.sprint_number}")
            logger.info(f"{'='*60}")
            logger.info(f"Objectifs atteints: {len(sprint_output.objectives_achieved)}/{len(sprint_input.objectives)}")
            logger.info(f"Fonctionnalités: {completed_stories}/{total_stories} complétées")
            logger.info(f"Vélocité: {sprint_output.sprint_velocity:.1f}%")
            logger.info(f"Bugs: {len(sprint_output.bugs_identified)} identifiés, {len(sprint_output.bugs_resolved)} résolus")
            logger.info(f"Qualité: {sprint_output.quality_score}/5")
            
            return sprint_output
            
        except Exception as e:
            logger.error(f"\n✗ ERREUR LORS DE L'EXÉCUTION DU SPRINT: {e}")
            logger.error(traceback.format_exc())
            
            sprint_output.status = SprintStatus.BLOCKED
            sprint_output.actual_end_date = datetime.now()
            sprint_output.retrospective_notes = f"Erreur système: {str(e)}\n\nRésultats partiels:\n{json.dumps(sprint_results, indent=2, default=str)}"
            
            return sprint_output
    
    def generate_retrospective_notes(self, sprint_output: SprintOutput) -> str:
        """Génère des notes de rétrospective basées sur les résultats du sprint"""
        notes = []
        
        # Points positifs
        if sprint_output.features_completed:
            notes.append("## ✅ Points positifs")
            notes.append(f"- {len(sprint_output.features_completed)} fonctionnalités développées avec succès")
            
            feature_types = {}
            for feature in sprint_output.features_completed:
                ftype = feature.get('type', 'unknown')
                feature_types[ftype] = feature_types.get(ftype, 0) + 1
            
            for ftype, count in feature_types.items():
                notes.append(f"  - {count} {ftype}")
        
        if sprint_output.objectives_achieved:
            notes.append(f"- {len(sprint_output.objectives_achieved)} objectifs atteints:")
            for obj in sprint_output.objectives_achieved[:5]:  # Limiter à 5
                notes.append(f"  - {obj}")
        
        if sprint_output.bugs_resolved:
            notes.append(f"- {len(sprint_output.bugs_resolved)} bugs résolus")
        
        # Points d'amélioration
        improvement_points = []
        
        if sprint_output.features_blocked:
            improvement_points.append(f"{len(sprint_output.features_blocked)} fonctionnalités bloquées")
        
        if sprint_output.bugs_open:
            improvement_points.append(f"{len(sprint_output.bugs_open)} bugs non résolus")
        
        if sprint_output.objectives_pending:
            improvement_points.append(f"{len(sprint_output.objectives_pending)} objectifs non atteints")
        
        if improvement_points:
            notes.append("\n## ⚠ Points d'amélioration")
            for point in improvement_points:
                notes.append(f"- {point}")
        
        # Recommandations techniques
        notes.append("\n## 🔧 Recommandations techniques")
        
        if sprint_output.sprint_velocity < 60:
            notes.append("- Revoir l'estimation des tâches (vélocité faible)")
        
        if len(sprint_output.bugs_identified) > 10:
            notes.append("- Améliorer les tests unitaires et d'intégration")
        
        if sprint_output.quality_score < 3:
            notes.append("- Augmenter le focus sur la qualité du code")
        
        if not sprint_output.documentation_generated:
            notes.append("- Inclure la documentation dans les critères d'acceptation")
        
        return "\n".join(notes)
    
    def generate_recommendations(self, sprint_output: SprintOutput) -> List[str]:
        """Génère des recommandations pour le prochain sprint"""
        recommendations = []
        
        if sprint_output.features_blocked:
            recommendations.append(f"Prioriser les {len(sprint_output.features_blocked)} fonctionnalités bloquées")
        
        if sprint_output.bugs_open:
            recommendations.append(f"Dédier du temps au bug fixing ({len(sprint_output.bugs_open)} bugs ouverts)")
        
        if sprint_output.sprint_velocity < 70:
            recommendations.append("Réduire la charge du prochain sprint pour améliorer la qualité")
        
        if not sprint_output.documentation_generated:
            recommendations.append("Inclure la documentation dans les critères d'acceptation")
        
        if sprint_output.quality_score < 3:
            recommendations.append("Augmenter les revues de code et les tests")
        
        return recommendations
    
    def calculate_quality_score(self, sprint_output: SprintOutput) -> int:
        """Calcule un score de qualité pour le sprint"""
        score = 5  # Score de base
        
        # Pénalités
        if len(sprint_output.bugs_identified) > 10:
            score -= 1
        if len(sprint_output.features_blocked) > 2:
            score -= 1
        if sprint_output.sprint_velocity < 50:
            score -= 1
        if not sprint_output.documentation_generated:
            score -= 1
        
        # Bonus
        if len(sprint_output.bugs_resolved) > len(sprint_output.bugs_identified) * 0.8:
            score += 1
        if sprint_output.sprint_velocity > 90:
            score += 1
        
        return max(1, min(5, score))
    
    def calculate_satisfaction_score(self, sprint_output: SprintOutput) -> int:
        """Calcule un score de satisfaction pour le sprint"""
        score = 3  # Score neutre
        
        # Facteurs positifs
        if len(sprint_output.objectives_achieved) > len(sprint_output.objectives_pending):
            score += 1
        if sprint_output.sprint_velocity > 70:
            score += 1
        if sprint_output.quality_score >= 4:
            score += 1
        
        # Facteurs négatifs
        if len(sprint_output.features_blocked) > 3:
            score -= 1
        if len(sprint_output.bugs_open) > 5:
            score -= 1
        
        return max(1, min(5, score))
    
    # --------------------------------------------------------------------------
    # MONITORING ET RAPPORTS
    # --------------------------------------------------------------------------
    
    async def health_check_all_agents(self) -> Dict[str, Any]:
        """Vérifie la santé de tous les agents"""
        logger.info("Vérification de santé des agents...")
        
        health_results = {}
        for agent_name, agent_instance in self.agent_instances.items():
            try:
                health = await agent_instance.health_check()
                health_results[agent_name] = health
                
                # Mettre à jour le statut de l'agent
                agent_info = self.agents.get(agent_name)
                if agent_info:
                    if health.get('status') == 'healthy':
                        agent_info.status = AgentStatus.READY
                    else:
                        agent_info.status = AgentStatus.ERROR
                    agent_info.last_health_check = datetime.now()
                
                logger.debug(f"  {agent_name}: {health.get('status', 'unknown')}")
                
            except Exception as e:
                logger.error(f"Erreur de health check pour {agent_name}: {e}")
                health_results[agent_name] = {"status": "error", "error": str(e)}
                
                agent_info = self.agents.get(agent_name)
                if agent_info:
                    agent_info.status = AgentStatus.ERROR
        
        # Résumé
        healthy_count = sum(1 for result in health_results.values() 
                          if result.get('status') == 'healthy')
        total_count = len(health_results)
        
        self.last_health_check = datetime.now()
        
        logger.info(f"Résumé santé: {healthy_count}/{total_count} agents en bonne santé")
        
        return {
            "timestamp": datetime.now().isoformat(),
            "healthy_agents": healthy_count,
            "total_agents": total_count,
            "health_percentage": (healthy_count / total_count * 100) if total_count > 0 else 0,
            "results": health_results
        }
    
    def get_system_status_report(self) -> Dict[str, Any]:
        """Génère un rapport d'état du système"""
        uptime = datetime.now() - self.start_time
        
        return {
            "timestamp": datetime.now().isoformat(),
            "system_status": self.system_status,
            "uptime_seconds": uptime.total_seconds(),
            "uptime_human": str(uptime).split('.')[0],
            "total_agents_configured": len(self.agents),
            "total_agents_instantiated": len(self.agent_instances),
            "active_workflows": len(self.active_workflows),
            "sprints_completed": len([s for s in self.sprints.values() 
                                     if s.status == SprintStatus.COMPLETED]),
            "sprints_in_progress": len([s for s in self.sprints.values() 
                                       if s.status == SprintStatus.IN_PROGRESS]),
            "last_health_check": self.last_health_check.isoformat() if self.last_health_check else None,
            "project_context": asdict(self.project_context),
            "agents_by_status": {
                status.value: len([a for a in self.agents.values() 
                                 if a.status == status])
                for status in AgentStatus
            }
        }
    
    def get_sprint_report(self, sprint_id: str) -> Optional[Dict[str, Any]]:
        """Génère un rapport détaillé pour un sprint"""
        sprint_output = self.sprints.get(sprint_id)
        if not sprint_output:
            return None
        
        duration = None
        if sprint_output.actual_end_date:
            duration = (sprint_output.actual_end_date - sprint_output.start_date).total_seconds()
        
        return {
            "sprint_id": sprint_output.sprint_id,
            "sprint_number": sprint_output.sprint_number,
            "title": f"Sprint {sprint_output.sprint_number}",
            "status": sprint_output.status.value,
            "start_date": sprint_output.start_date.isoformat(),
            "end_date": sprint_output.end_date.isoformat(),
            "actual_end_date": sprint_output.actual_end_date.isoformat() if sprint_output.actual_end_date else None,
            "duration_seconds": duration,
            "duration_days": duration / 86400 if duration else None,
            
            # Objectifs
            "objectives_achieved": sprint_output.objectives_achieved,
            "objectives_pending": sprint_output.objectives_pending,
            "objectives_achievement_rate": len(sprint_output.objectives_achieved) / (len(sprint_output.objectives_achieved) + len(sprint_output.objectives_pending)) * 100 if (len(sprint_output.objectives_achieved) + len(sprint_output.objectives_pending)) > 0 else 0,
            
            # Fonctionnalités
            "features_completed_count": len(sprint_output.features_completed),
            "features_in_progress_count": len(sprint_output.features_in_progress),
            "features_blocked_count": len(sprint_output.features_blocked),
            
            # Bugs
            "bugs_identified_count": len(sprint_output.bugs_identified),
            "bugs_resolved_count": len(sprint_output.bugs_resolved),
            "bugs_open_count": len(sprint_output.bugs_open),
            "bug_resolution_rate": len(sprint_output.bugs_resolved) / len(sprint_output.bugs_identified) * 100 if len(sprint_output.bugs_identified) > 0 else 100,
            
            # Métriques
            "sprint_velocity": sprint_output.sprint_velocity,
            "quality_score": sprint_output.quality_score,
            "team_satisfaction": sprint_output.team_satisfaction,
            
            # Déploiement
            "deployment_status": sprint_output.deployment_status,
            "deployment_artifacts_count": len(sprint_output.deployment_artifacts),
            
            # Documentation
            "documentation_generated_count": len(sprint_output.documentation_generated),
            
            # Recommandations
            "recommendations_count": len(sprint_output.recommendations_next_sprint),
            "recommendations": sprint_output.recommendations_next_sprint,
            
            # Fichiers
            "generated_files_count": len(sprint_output.generated_files),
            
            # Résumé
            "success_summary": self.generate_sprint_summary(sprint_output)
        }
    
    def generate_sprint_summary(self, sprint_output: SprintOutput) -> str:
        """Génère un résumé textuel du sprint"""
        summary_parts = []
        
        if sprint_output.status == SprintStatus.COMPLETED:
            summary_parts.append(f"Sprint {sprint_output.sprint_number} terminé avec succès.")
        elif sprint_output.status == SprintStatus.BLOCKED:
            summary_parts.append(f"Sprint {sprint_output.sprint_number} bloqué.")
        else:
            summary_parts.append(f"Sprint {sprint_output.sprint_number} en cours.")
        
        if sprint_output.objectives_achieved:
            summary_parts.append(f"{len(sprint_output.objectives_achieved)} objectifs atteints.")
        
        if sprint_output.features_completed:
            summary_parts.append(f"{len(sprint_output.features_completed)} fonctionnalités développées.")
        
        if sprint_output.bugs_identified:
            summary_parts.append(f"{len(sprint_output.bugs_identified)} bugs identifiés, {len(sprint_output.bugs_resolved)} résolus.")
        
        if sprint_output.sprint_velocity:
            summary_parts.append(f"Vélocité: {sprint_output.sprint_velocity:.1f}%.")
        
        return " ".join(summary_parts)
    
    # --------------------------------------------------------------------------
    # INTERFACE UTILISATEUR ET UTILITAIRES
    # --------------------------------------------------------------------------
    
    def list_available_agents(self) -> List[Dict[str, Any]]:
        """Liste tous les agents disponibles"""
        agents_list = []
        
        for agent_name, agent_info in self.agents.items():
            if agent_info.enabled:
                agents_list.append({
                    "name": agent_name,
                    "display_name": agent_info.display_name,
                    "type": agent_info.agent_type,
                    "specialization": agent_info.specialization,
                    "status": agent_info.status.value,
                    "instantiated": agent_name in self.agent_instances,
                    "capabilities": agent_info.capabilities,
                    "parent": agent_info.parent,
                    "purpose": agent_info.purpose
                })
        
        return sorted(agents_list, key=lambda x: (x['type'], x['name']))
    
    def list_available_tasks(self) -> Dict[str, List[str]]:
        """Liste toutes les tâches disponibles et les agents capables"""
        task_mapping = self.project_config.get('task_mapping', {})
        available_tasks = {}
        
        for task, agents in task_mapping.items():
            # Filtrer les agents disponibles
            available_agents = []
            for agent_name in agents:
                if agent_name == "*":
                    # Tous les agents disponibles
                    available_agents.extend([name for name, info in self.agents.items() 
                                           if info.enabled and info.status == AgentStatus.READY])
                elif agent_name in self.agents:
                    agent_info = self.agents[agent_name]
                    if agent_info.enabled and agent_info.status == AgentStatus.READY:
                        available_agents.append(agent_name)
            
            if available_agents:
                available_tasks[task] = list(set(available_agents))  # Dédupliquer
        
        return available_tasks
    
    def create_example_sprint(self, sprint_number: int = 1) -> SprintInput:
        """Crée un exemple de sprint pour les tests"""
        return SprintInput(
            sprint_id=f"sprint_{sprint_number}_{str(uuid.uuid4())[:8]}",
            sprint_number=sprint_number,
            title=f"Développement Token ERC20 - Sprint {sprint_number}",
            description="Création d'un token ERC20 sécurisé avec interface Web3 et tests complets",
            objectives=[
                "Smart contract ERC20 fonctionnel et sécurisé",
                "Interface utilisateur pour interagir avec le token",
                "Tests de sécurité et d'intégration effectués",
                "Documentation technique générée"
            ],
            user_stories=[
                {
                    "id": "US001",
                    "name": "Token ERC20 Standard",
                    "type": "smart_contract",
                    "description": "Implémenter un token ERC20 avec les fonctions standard",
                    "priority": "high",
                    "story_points": 5,
                    "acceptance_criteria": [
                        "Fonctions transfer, approve, transferFrom implémentées",
                        "Événements Transfer et Approval émis",
                        "Conforme au standard OpenZeppelin ERC20"
                    ],
                    "technical_notes": "Utiliser OpenZeppelin pour la sécurité"
                },
                {
                    "id": "US002",
                    "name": "Fonctions Mint/Burn",
                    "type": "smart_contract",
                    "description": "Ajouter des fonctions pour créer et détruire des tokens",
                    "priority": "medium",
                    "story_points": 3,
                    "acceptance_criteria": [
                        "Fonction mint avec contrôle d'accès",
                        "Fonction burn pour détruire des tokens",
                        "Événements Mint et Burn émis"
                    ],
                    "technical_notes": "Restreindre mint à l'owner du contrat"
                },
                {
                    "id": "US003",
                    "name": "Interface Web3 DApp",
                    "type": "dapp",
                    "description": "Interface utilisateur pour interagir avec le token",
                    "priority": "high",
                    "story_points": 8,
                    "acceptance_criteria": [
                        "Connexion avec MetaMask",
                        "Affichage du balance de tokens",
                        "Formulaire pour transferer des tokens",
                        "Interface responsive et moderne"
                    ],
                    "technical_notes": "Utiliser React + Ethers.js"
                },
                {
                    "id": "US004",
                    "name": "Tests de Sécurité",
                    "type": "testing",
                    "description": "Tests de sécurité complets pour le smart contract",
                    "priority": "critical",
                    "story_points": 5,
                    "acceptance_criteria": [
                        "Tests pour prévenir les reentrancy attacks",
                        "Tests pour les overflows/underflows",
                        "Audit avec outils automatisés (Slither)",
                        "Rapport de sécurité généré"
                    ],
                    "technical_notes": "Utiliser Hardhat pour les tests"
                }
            ],
            acceptance_criteria={
                "US001": ["Tests unitaires passants à 100%", "Gas usage optimisé"],
                "US002": ["Contrôle d'accès fonctionnel", "Événements correctement émis"],
                "US003": ["Connexion wallet fonctionnelle", "Interface utilisable sur mobile"],
                "US004": ["Aucune vulnérabilité critique", "Rapport d'audit généré"]
            },
            technical_constraints={
                "blockchain": "Ethereum",
                "testnet": "Sepolia",
                "smart_contract_language": "Solidity >=0.8.0",
                "frontend_framework": "React 18+",
                "web3_library": "Ethers.js v6",
                "security": "OpenZeppelin Contracts",
                "testing": "Hardhat + Waffle",
                "ui": {
                    "responsive": True,
                    "design_system": "Material-UI",
                    "browser_support": "Chrome, Firefox, Safari"
                }
            },
            priority_features=["US001", "US003", "US004"],
            start_date=datetime.now(),
            end_date=datetime.now() + timedelta(days=14)
        )

# --------------------------------------------------------------------------
# POINT D'ENTRÉE PRINCIPAL
# --------------------------------------------------------------------------

async def main():
    """Fonction principale de l'orchestrateur"""
    orchestrator = SmartContractOrchestrator()
    
    logger.info("=" * 70)
    logger.info("SMART CONTRACT DEVELOPMENT PIPELINE - ORCHESTRATOR v3.0")
    logger.info("=" * 70)
    
    try:
        # 1. Charger la configuration
        logger.info("\n1. 📁 Chargement de la configuration...")
        if not orchestrator.load_configuration():
            logger.error("❌ Échec du chargement de la configuration")
            return None
        
        logger.info(f"   Projet: {orchestrator.project_config.get('project_name')}")
        logger.info(f"   Version: {orchestrator.project_config.get('version')}")
        
        # 2. Parser la configuration des agents
        logger.info("\n2. 🤖 Analyse de la configuration des agents...")
        if not orchestrator.parse_agents_configuration():
            logger.error("❌ Échec de l'analyse des agents")
            return None
        
        logger.info(f"   Agents configurés: {len(orchestrator.agents)}")
        
        # 3. Initialiser les agents
        logger.info("\n3. ⚡ Initialisation des agents...")
        if not await orchestrator.initialize_agents():
            logger.error("❌ Échec de l'initialisation des agents")
            return None
        
        logger.info(f"   Agents initialisés: {len(orchestrator.agent_instances)}")
        
        # 4. Vérification de santé
        logger.info("\n4. 🩺 Vérification de santé initiale...")
        health_report = await orchestrator.health_check_all_agents()
        healthy_pct = health_report['health_percentage']
        
        if healthy_pct >= 80:
            logger.info(f"   ✅ Santé: {healthy_pct:.1f}% ({health_report['healthy_agents']}/{health_report['total_agents']} agents)")
        elif healthy_pct >= 50:
            logger.warning(f"   ⚠ Santé: {healthy_pct:.1f}% ({health_report['healthy_agents']}/{health_report['total_agents']} agents)")
        else:
            logger.error(f"   ❌ Santé: {healthy_pct:.1f}% ({health_report['healthy_agents']}/{health_report['total_agents']} agents)")
        
        # 5. Exécuter un workflow de test
        logger.info("\n5. 🔄 Exécution d'un workflow de test...")
        test_result = await orchestrator.execute_workflow("test")
        
        if test_result.get('status') == 'success':
            logger.info(f"   ✅ Test réussi: {test_result.get('workflow_status')}")
        else:
            logger.warning(f"   ⚠ Test avec problèmes: {test_result.get('error', 'Unknown error')}")
        
        # 6. Afficher le statut du système
        logger.info("\n6. 📊 Statut du système:")
        system_status = orchestrator.get_system_status_report()
        
        logger.info(f"   Uptime: {system_status['uptime_human']}")
        logger.info(f"   Agents: {system_status['total_agents_instantiated']}/{system_status['total_agents_configured']} instanciés")
        logger.info(f"   Workflows actifs: {len(system_status['active_workflows'])}")
        logger.info(f"   Sprints terminés: {system_status['sprints_completed']}")
        
        # 7. Lister les agents disponibles
        logger.info("\n7. 📋 Agents disponibles:")
        agents_list = orchestrator.list_available_agents()
        
        for agent in agents_list[:10]:  # Afficher les 10 premiers
            status_icon = "✅" if agent['status'] == 'ready' else "⚡" if agent['status'] == 'loading' else "❌"
            logger.info(f"   {status_icon} {agent['name']:20} ({agent['type']:12}) - {agent['status']}")
        
        if len(agents_list) > 10:
            logger.info(f"   ... et {len(agents_list) - 10} autres agents")
        
        # 8. Tâches disponibles
        logger.info("\n8. 🛠️ Tâches disponibles:")
        available_tasks = orchestrator.list_available_tasks()
        task_count = len(available_tasks)
        
        logger.info(f"   {task_count} tâches disponibles")
        for task, agents in list(available_tasks.items())[:5]:  # 5 premières tâches
            logger.info(f"   • {task}: {len(agents)} agents")
        
        if task_count > 5:
            logger.info(f"   ... et {task_count - 5} autres tâches")
        
        # 9. Exemple de sprint
        logger.info("\n9. 🚀 Exemple de sprint prêt à l'exécution:")
        example_sprint = orchestrator.create_example_sprint(1)
        
        logger.info(f"   Titre: {example_sprint.title}")
        logger.info(f"   Durée: 14 jours")
        logger.info(f"   User Stories: {len(example_sprint.user_stories)}")
        logger.info(f"   Objectifs: {len(example_sprint.objectives)}")
        
        # 10. Interface utilisateur
        logger.info("\n" + "=" * 70)
        logger.info("🏁 ORCHESTRATEUR PRÊT")
        logger.info("=" * 70)
        logger.info("\nCommandes disponibles:")
        logger.info("  • orchestrator.execute_sprint(sprint_input) - Exécuter un sprint")
        logger.info("  • orchestrator.execute_workflow('workflow_name') - Exécuter un workflow")
        logger.info("  • orchestrator.execute_task('task_name', params) - Exécuter une tâche")
        logger.info("  • orchestrator.health_check_all_agents() - Vérifier la santé des agents")
        logger.info("  • orchestrator.get_system_status_report() - Obtenir le statut du système")
        logger.info("\nExemple:")
        logger.info("  sprint_output = await orchestrator.execute_sprint(example_sprint)")
        logger.info("  print(f'Sprint terminé: {sprint_output.status}')")
        
        return orchestrator
        
    except Exception as e:
        logger.error(f"\n❌ ERREUR CRITIQUE DANS L'ORCHESTRATEUR: {e}")
        logger.error(traceback.format_exc())
        return None

async def interactive_mode():
    """Mode interactif pour tester l'orchestrateur"""
    orchestrator = await main()
    
    if not orchestrator:
        logger.error("Impossible de démarrer l'orchestrateur")
        return
    
    try:
        while True:
            print("\n" + "=" * 50)
            print("MENU INTERACTIF - SmartContractDevPipeline")
            print("=" * 50)
            print("1. Exécuter un sprint exemple")
            print("2. Vérifier la santé des agents")
            print("3. Afficher le statut du système")
            print("4. Lister les agents disponibles")
            print("5. Exécuter un workflow spécifique")
            print("6. Quitter")
            
            choice = input("\nVotre choix (1-6): ").strip()
            
            if choice == "1":
                # Exécuter un sprint exemple
                sprint_input = orchestrator.create_example_sprint(
                    len(orchestrator.sprints) + 1
                )
                
                print(f"\n🎯 Exécution du sprint {sprint_input.sprint_number}...")
                print(f"Titre: {sprint_input.title}")
                
                sprint_output = await orchestrator.execute_sprint(sprint_input)
                
                print(f"\n📊 Résultat du sprint:")
                print(f"  Statut: {sprint_output.status.value}")
                print(f"  Objectifs atteints: {len(sprint_output.objectives_achieved)}/{len(sprint_input.objectives)}")
                print(f"  Fonctionnalités: {len(sprint_output.features_completed)} complétées")
                print(f"  Vélocité: {sprint_output.sprint_velocity:.1f}%")
                print(f"  Qualité: {sprint_output.quality_score}/5")
                
                # Demander si on veut voir le rapport détaillé
                if input("\nVoir le rapport détaillé? (o/n): ").lower() == 'o':
                    report = orchestrator.get_sprint_report(sprint_output.sprint_id)
                    if report:
                        print("\n📋 Rapport détaillé:")
                        print(f"  ID: {report['sprint_id']}")
                        print(f"  Durée: {report['duration_days']:.1f} jours")
                        print(f"  Taux d'objectifs: {report['objectives_achievement_rate']:.1f}%")
                        print(f"  Taux de bugs: {report['bug_resolution_rate']:.1f}%")
                        print(f"  Recommandations: {len(report['recommendations'])}")
                        
            elif choice == "2":
                # Vérifier la santé
                print("\n🩺 Vérification de santé...")
                health_report = await orchestrator.health_check_all_agents()
                
                print(f"Agents sains: {health_report['healthy_agents']}/{health_report['total_agents']}")
                print(f"Pourcentage: {health_report['health_percentage']:.1f}%")
                
            elif choice == "3":
                # Statut du système
                print("\n📊 Statut du système:")
                status = orchestrator.get_system_status_report()
                
                print(f"Uptime: {status['uptime_human']}")
                print(f"Agents: {status['total_agents_instantiated']}/{status['total_agents_configured']}")
                print(f"Sprints terminés: {status['sprints_completed']}")
                print(f"Workflows actifs: {len(status['active_workflows'])}")
                
                # Statut des agents
                print("\nStatut des agents:")
                for status_name, count in status['agents_by_status'].items():
                    if count > 0:
                        print(f"  {status_name}: {count}")
                        
            elif choice == "4":
                # Lister les agents
                print("\n🤖 Agents disponibles:")
                agents = orchestrator.list_available_agents()
                
                for agent in agents:
                    status_icon = {
                        'ready': '✅',
                        'loading': '⚡',
                        'error': '❌',
                        'disabled': '🚫',
                        'not_loaded': '⭕'
                    }.get(agent['status'], '❓')
                    
                    print(f"  {status_icon} {agent['name']:20} - {agent['display_name']}")
                    print(f"     Type: {agent['type']}, Statut: {agent['status']}")
                    print(f"     Capacités: {len(agent['capabilities'])}")
                    
            elif choice == "5":
                # Exécuter un workflow
                workflows = orchestrator.project_config.get('workflow_configurations', {})
                
                if workflows:
                    print("\n🔄 Workflows disponibles:")
                    for i, (name, config) in enumerate(workflows.items(), 1):
                        print(f"  {i}. {name}: {config.get('name', 'Sans nom')}")
                    
                    workflow_choice = input("\nNuméro du workflow (ou nom): ").strip()
                    
                    try:
                        if workflow_choice.isdigit():
                            workflow_idx = int(workflow_choice) - 1
                            workflow_name = list(workflows.keys())[workflow_idx]
                        else:
                            workflow_name = workflow_choice
                        
                        if workflow_name in workflows:
                            print(f"\nExécution du workflow: {workflow_name}")
                            result = await orchestrator.execute_workflow(workflow_name)
                            
                            if result.get('status') == 'success':
                                print(f"✅ Workflow terminé: {result.get('workflow_status')}")
                                print(f"   Durée: {result.get('duration_seconds', 0):.1f}s")
                                print(f"   Tâches: {result.get('tasks_completed', 0)} réussies")
                            else:
                                print(f"❌ Échec du workflow: {result.get('error')}")
                        else:
                            print(f"❌ Workflow '{workflow_name}' non trouvé")
                    except (ValueError, IndexError):
                        print("❌ Choix invalide")
                else:
                    print("❌ Aucun workflow configuré")
                    
            elif choice == "6":
                print("\n👋 Au revoir!")
                break
                
            else:
                print("❌ Choix invalide, veuillez choisir 1-6")
                
            input("\nAppuyez sur Entrée pour continuer...")
            
    except KeyboardInterrupt:
        print("\n\n👋 Arrêt demandé par l'utilisateur")
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Orchestrateur SmartContractDevPipeline")
    parser.add_argument("--interactive", action="store_true", help="Mode interactif")
    parser.add_argument("--config", default="project_config.yaml", help="Chemin du fichier de configuration")
    parser.add_argument("--test", action="store_true", help="Mode test rapide")
    
    args = parser.parse_args()
    
    if args.interactive:
        asyncio.run(interactive_mode())
    elif args.test:
        # Mode test rapide
        async def quick_test():
            orchestrator = SmartContractOrchestrator(args.config)
            
            print("Test rapide de l'orchestrateur...")
            
            if orchestrator.load_configuration() and orchestrator.parse_agents_configuration():
                print("✓ Configuration chargée")
                
                if await orchestrator.initialize_agents():
                    print(f"✓ {len(orchestrator.agent_instances)} agents initialisés")
                    
                    health = await orchestrator.health_check_all_agents()
                    print(f"✓ Santé: {health['health_percentage']:.1f}%")
                    
                    # Tester une tâche simple
                    result = await orchestrator.execute_task("validate_config")
                    print(f"✓ Tâche test: {result.get('status')}")
                    
                    return True
            
            print("✗ Test échoué")
            return False
        
        success = asyncio.run(quick_test())
        sys.exit(0 if success else 1)
    else:
        # Mode normal
        try:
            orchestrator = asyncio.run(main())
            if orchestrator:
                print("\n" + "=" * 70)
                print("Orchestrateur démarré avec succès!")
                print("Utilisez --interactive pour le mode interactif")
                print("=" * 70)
                
                # Garder le programme en vie
                try:
                    asyncio.get_event_loop().run_forever()
                except KeyboardInterrupt:
                    print("\n\n👋 Arrêt de l'orchestrateur")
        except KeyboardInterrupt:
            print("\n\n👋 Arrêt demandé par l'utilisateur")
        except Exception as e:
            print(f"\n❌ Erreur: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)
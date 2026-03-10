"""
Architect Agent - Agent responsable de la conception de l'architecture des systèmes
Version: 1.2.0 (ALIGNÉ SUR CODER)
Auteur: PoolSync DeFi
Date: 2026-03-05
"""

import os
import sys
import yaml
import json
import logging
import asyncio
from pathlib import Path
from typing import Dict, List, Any, Optional, Union, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum
from datetime import datetime
import hashlib
import uuid

logger = logging.getLogger(__name__)

# Ajouter le chemin du projet au PYTHONPATH
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from agents.base_agent.base_agent import BaseAgent, AgentStatus, Message, MessageType


# -----------------------------------------------------------------------------
# CLASSES DE DONNÉES SPÉCIFIQUES À L'ARCHITECT
# -----------------------------------------------------------------------------

class ArchitectureType(Enum):
    """Types d'architectures supportés"""
    MICROSERVICES = "microservices"
    MONOLITH = "monolith"
    SERVERLESS = "serverless"
    EVENT_DRIVEN = "event_driven"
    LAYERED = "layered"
    HEXAGONAL = "hexagonal"
    CQRS = "cqrs"
    EVENT_SOURCING = "event_sourcing"


class ComponentType(Enum):
    """Types de composants dans l'architecture"""
    API_GATEWAY = "api_gateway"
    SERVICE = "service"
    DATABASE = "database"
    CACHE = "cache"
    MESSAGE_BROKER = "message_broker"
    AUTHENTICATION = "authentication"
    MONITORING = "monitoring"
    LOGGING = "logging"
    STORAGE = "storage"
    FRONTEND = "frontend"
    SMART_CONTRACT = "smart_contract"


class TechnologyStack(Enum):
    """Piles technologiques supportées"""
    PYTHON_FASTAPI = "python_fastapi"
    NODE_EXPRESS = "node_express"
    REACT_FRONTEND = "react_frontend"
    POSTGRESQL = "postgresql"
    MONGODB = "mongodb"
    REDIS = "redis"
    RABBITMQ = "rabbitmq"
    KAFKA = "kafka"
    DOCKER = "docker"
    KUBERNETES = "kubernetes"
    SOLIDITY_HARDFHAT = "solidity_hardhat"
    RUST_ANCHOR = "rust_anchor"
    ETHEREUM = "ethereum"
    POLYGON = "polygon"
    ARBITRUM = "arbitrum"


@dataclass
class ComponentSpec:
    """Spécifications d'un composant"""
    name: str
    component_type: ComponentType
    description: str
    technology: TechnologyStack
    dependencies: List[str] = field(default_factory=list)
    endpoints: List[Dict[str, Any]] = field(default_factory=list)
    database_schemas: List[Dict[str, Any]] = field(default_factory=list)
    environment_vars: Dict[str, str] = field(default_factory=dict)
    resource_requirements: Dict[str, Any] = field(default_factory=dict)
    security_requirements: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertit en dictionnaire"""
        return {
            "name": self.name,
            "component_type": self.component_type.value,
            "description": self.description,
            "technology": self.technology.value,
            "dependencies": self.dependencies,
            "endpoints": self.endpoints,
            "database_schemas": self.database_schemas,
            "environment_vars": self.environment_vars,
            "resource_requirements": self.resource_requirements,
            "security_requirements": self.security_requirements
        }


@dataclass
class DeploymentSpec:
    """Spécifications de déploiement"""
    environment: str  # dev, staging, prod
    cloud_provider: str = "aws"
    region: str = "us-east-1"
    scaling_config: Dict[str, Any] = field(default_factory=dict)
    networking: Dict[str, Any] = field(default_factory=dict)
    monitoring: Dict[str, Any] = field(default_factory=dict)
    backup_config: Dict[str, Any] = field(default_factory=dict)
    disaster_recovery: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertit en dictionnaire"""
        return asdict(self)


@dataclass
class ArchitectureDesign:
    """Conception complète de l'architecture"""
    project_name: str
    architecture_type: ArchitectureType
    description: str
    components: List[ComponentSpec] = field(default_factory=list)
    deployment_specs: List[DeploymentSpec] = field(default_factory=list)
    design_patterns: List[str] = field(default_factory=list)
    constraints: Dict[str, Any] = field(default_factory=dict)
    assumptions: List[str] = field(default_factory=list)
    risks: List[Dict[str, str]] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    version: str = "1.0.0"
    design_id: str = field(default_factory=lambda: f"design_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertit en dictionnaire"""
        return {
            "design_id": self.design_id,
            "project_name": self.project_name,
            "architecture_type": self.architecture_type.value,
            "description": self.description,
            "components": [comp.to_dict() for comp in self.components],
            "deployment_specs": [dep.to_dict() for dep in self.deployment_specs],
            "design_patterns": self.design_patterns,
            "constraints": self.constraints,
            "assumptions": self.assumptions,
            "risks": self.risks,
            "created_at": self.created_at.isoformat(),
            "version": self.version
        }


# -----------------------------------------------------------------------------
# CLASSE ARCHITECT AGENT (CORRIGÉE ET ALIGNÉE)
# -----------------------------------------------------------------------------

class ArchitectAgent(BaseAgent):
    """
    Agent responsable de la conception de l'architecture des systèmes.
    Analyse les exigences et produit des conceptions d'architecture détaillées.
    """

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialise l'agent Architect.

        Args:
            config_path: Chemin vers le fichier de configuration YAML
        """
        # Déterminer le chemin de configuration
        if config_path is None:
            config_path = str(project_root / "agents" / "architect" / "config.yaml")

        # Initialiser l'agent de base
        super().__init__(config_path)

        # État spécifique à l'Architect
        self._designs: Dict[str, ArchitectureDesign] = {}
        self._templates: Dict[str, Any] = {}
        self._patterns_library: Dict[str, Any] = {}
        
        # Sous-agents
        self._sub_agents: Dict[str, Any] = {}

        # Charger les templates et patterns
        self._load_templates()
        self._load_patterns()

        self._logger.info(f"Agent Architect initialisé avec la configuration de {config_path}")

    async def initialize(self) -> bool:
        """
        Initialise l'agent Architect.
        """
        return await super().initialize()

    async def _initialize_components(self) -> bool:
        """
        Initialise les composants spécifiques de l'agent Architect.

        Returns:
            True si l'initialisation a réussi
        """
        try:
            self._logger.info("Initialisation des composants de l'agent Architect...")

            # Charger les configurations avancées
            self._load_advanced_configs()

            # Initialiser le cache des designs
            self._designs = {}

            # Initialiser les sous-agents
            await self._initialize_sub_agents()

            # Vérifier les outils nécessaires
            if not self._check_required_tools():
                self._logger.warning("Certains outils recommandés ne sont pas disponibles")

            self._logger.info("Composants de l'agent Architect initialisés avec succès")
            return True

        except Exception as e:
            self._logger.error(f"Erreur lors de l'initialisation des composants: {e}")
            return False

    async def _initialize_sub_agents(self):
        """Initialise les sous-agents spécialisés"""
        try:
            # Import des sous-agents si disponibles
            try:
                from .sous_agents import (
                    CloudArchitectSubAgent,
                    BlockchainArchitectSubAgent,
                    MicroservicesArchitectSubAgent
                )
                
                self._sub_agents = {
                    "cloud": CloudArchitectSubAgent(),
                    "blockchain": BlockchainArchitectSubAgent(),
                    "microservices": MicroservicesArchitectSubAgent()
                }
                self._logger.info(f"Sous-agents initialisés: {list(self._sub_agents.keys())}")
            except ImportError as e:
                self._logger.debug(f"Aucun sous-agent trouvé: {e}")
                self._sub_agents = {}
                
        except Exception as e:
            self._logger.error(f"Erreur lors de l'initialisation des sous-agents: {e}")
            self._sub_agents = {}

    # -------------------------------------------------------------------------
    # MÉTHODES D'INFORMATION ET DE SANTÉ (AJOUTÉES)
    # -------------------------------------------------------------------------

    async def health_check(self) -> Dict[str, Any]:
        """Vérifie la santé de l'agent."""
        base_health = await super().health_check()
        
        return {
            **base_health,
            "agent": self.name,
            "display_name": self._display_name,
            "status": self._status.value,
            "ready": self._status == AgentStatus.READY,
            "designs_count": len(self._designs),
            "templates_loaded": len(self._templates),
            "patterns_loaded": len(self._patterns_library),
            "sub_agents": list(self._sub_agents.keys()),
            "timestamp": datetime.now().isoformat()
        }

    def get_agent_info(self) -> Dict[str, Any]:
        """Retourne les informations de l'agent."""
        agent_config = self._agent_config.get('agent', {})
        capabilities = agent_config.get('capabilities', [])
        
        if capabilities and isinstance(capabilities[0], dict):
            capabilities = [cap["name"] for cap in capabilities]

        return {
            "id": self.name,
            "name": "ArchitectAgent",
            "display_name": self._display_name,
            "version": agent_config.get('version', '3.0.0'),
            "description": agent_config.get('description', 'Agent de conception d\'architecture'),
            "status": self._status.value,
            "capabilities": capabilities,
            "features": {
                "templates": list(self._templates.keys()),
                "patterns": len(self._patterns_library),
                "sub_agents": list(self._sub_agents.keys()),
                "architecture_types": [t.value for t in ArchitectureType]
            },
            "stats": {
                "designs_created": len(self._designs)
            }
        }

    # -------------------------------------------------------------------------
    # MÉTHODES PRIVÉES D'INITIALISATION (inchangées)
    # -------------------------------------------------------------------------

    def _load_templates(self):
        """Charge les templates d'architecture"""
        templates_dir = project_root / "agents" / "architect" / "templates"
        
        if templates_dir.exists():
            self._logger.info(f"Chargement des templates depuis {templates_dir}")
            
            self._templates = {
                "microservices": self._get_microservices_template(),
                "monolith": self._get_monolith_template(),
                "serverless": self._get_serverless_template(),
                "event_driven": self._get_event_driven_template()
            }
        else:
            self._logger.warning("Répertoire des templates non trouvé, utilisation des templates par défaut")
            self._templates = self._get_default_templates()

    def _load_patterns(self):
        """Charge les patterns d'architecture"""
        patterns_file = project_root / "agents" / "architect" / "patterns.yaml"
        
        if patterns_file.exists():
            try:
                with open(patterns_file, 'r', encoding='utf-8') as f:
                    self._patterns_library = yaml.safe_load(f)
                self._logger.info(f"Patterns chargés depuis {patterns_file}")
            except Exception as e:
                self._logger.error(f"Erreur lors du chargement des patterns: {e}")
                self._patterns_library = self._get_default_patterns()
        else:
            self._logger.warning("Fichier des patterns non trouvé, utilisation des patterns par défaut")
            self._patterns_library = self._get_default_patterns()

    def _load_advanced_configs(self):
        """Charge les configurations avancées"""
        pass

    def _check_required_tools(self) -> bool:
        """Vérifie la disponibilité des outils nécessaires"""
        return True

    # -------------------------------------------------------------------------
    # MÉTHODES PUBLIQUES PRINCIPALES (inchangées)
    # -------------------------------------------------------------------------

    async def design_architecture(self, requirements: Dict[str, Any]) -> Dict[str, Any]:
        """
        Conçoit une architecture basée sur les exigences.
        """
        try:
            self._logger.info("Démarrage de la conception de l'architecture...")
            
            validation_result = self.validate_requirements(requirements)
            if not validation_result["valid"]:
                return {
                    "success": False,
                    "error": "Exigences invalides",
                    "validation_errors": validation_result["errors"]
                }
            
            analysis = self._analyze_requirements(requirements)
            arch_type = self._select_architecture_type(analysis)
            design = self._create_design(analysis, arch_type, requirements)
            documentation = self._generate_documentation(design)
            
            self._designs[design.design_id] = design
            
            result = {
                "success": True,
                "design_id": design.design_id,
                "architecture": design.to_dict(),
                "documentation": documentation,
                "analysis": analysis,
                "created_at": design.created_at.isoformat()
            }
            
            self._logger.info(f"Architecture conçue avec succès: {design.design_id}")
            return result
            
        except Exception as e:
            self._logger.error(f"Erreur lors de la conception de l'architecture: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def validate_requirements(self, requirements: Dict[str, Any]) -> Dict[str, Any]:
        """
        Valide les exigences d'architecture.
        """
        errors = []
        warnings = []
        
        if not requirements:
            errors.append("Aucune exigence fournie")
            return {"valid": False, "errors": errors, "warnings": warnings}
        
        required_fields = ["project_name", "description", "functional_requirements"]
        for field in required_fields:
            if field not in requirements:
                errors.append(f"Champ obligatoire manquant: {field}")
        
        func_reqs = requirements.get("functional_requirements", [])
        if not isinstance(func_reqs, list) or len(func_reqs) == 0:
            errors.append("Aucune exigence fonctionnelle spécifiée")
        
        constraints = requirements.get("technical_constraints", {})
        if constraints:
            if "programming_languages" in constraints:
                langs = constraints["programming_languages"]
                if not isinstance(langs, list) or len(langs) == 0:
                    warnings.append("Aucun langage de programmation spécifié")
        
        scale = requirements.get("expected_scale", {})
        if not scale:
            warnings.append("Échelle attendue non spécifiée")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }

    async def review_design(self, design_id: str, feedback: Dict[str, Any]) -> Dict[str, Any]:
        """
        Révision d'une conception d'architecture.
        """
        try:
            self._logger.info(f"Révision de la conception {design_id}...")
            
            design = self.get_design(design_id)
            if not design:
                return {
                    "success": False,
                    "error": f"Conception non trouvée: {design_id}"
                }
            
            analysis = self._analyze_feedback(feedback, design)
            
            if analysis.get("needs_revision", False):
                revised_design = self._revise_design(design, analysis["suggestions"])
                self._designs[design_id] = revised_design
                design = revised_design
            
            result = {
                "success": True,
                "design_id": design_id,
                "review_comments": analysis.get("comments", []),
                "suggestions_applied": analysis.get("suggestions_applied", []),
                "revision_needed": analysis.get("needs_revision", False),
                "updated_design": design.to_dict() if analysis.get("needs_revision", False) else None
            }
            
            self._logger.info(f"Révision terminée pour {design_id}")
            return result
            
        except Exception as e:
            self._logger.error(f"Erreur lors de la révision de la conception: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def get_design(self, design_id: str) -> Optional[Dict[str, Any]]:
        """
        Récupère une conception d'architecture.
        """
        design = self._designs.get(design_id)
        if design:
            return design.to_dict()
        return None

    def list_designs(self) -> List[Dict[str, Any]]:
        """
        Liste toutes les conceptions disponibles.
        """
        return [
            {
                "design_id": design_id,
                "project_name": design.project_name,
                "architecture_type": design.architecture_type.value,
                "created_at": design.created_at.isoformat(),
                "version": design.version
            }
            for design_id, design in self._designs.items()
        ]

    # -------------------------------------------------------------------------
    # MÉTHODES D'ANALYSE ET DE CONCEPTION (inchangées)
    # -------------------------------------------------------------------------

    def _analyze_requirements(self, requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Analyse les exigences pour extraire les informations clés"""
        analysis = {
            "project_scope": requirements.get("project_name", "Unnamed Project"),
            "description": requirements.get("description", ""),
            "functional_reqs_count": len(requirements.get("functional_requirements", [])),
            "non_functional_reqs": requirements.get("non_functional_requirements", {}),
            "technical_constraints": requirements.get("technical_constraints", {}),
            "business_constraints": requirements.get("business_constraints", {}),
            "expected_scale": requirements.get("expected_scale", {}),
            "security_requirements": requirements.get("security_requirements", []),
            "compliance_requirements": requirements.get("compliance_requirements", [])
        }
        
        complexity_score = self._calculate_complexity_score(requirements)
        analysis["complexity_score"] = complexity_score
        analysis["complexity_level"] = self._get_complexity_level(complexity_score)
        
        perf_requirements = requirements.get("non_functional_requirements", {}).get("performance", {})
        analysis["performance_requirements"] = perf_requirements
        
        availability = requirements.get("non_functional_requirements", {}).get("availability", "99.9%")
        analysis["availability_requirement"] = availability
        
        return analysis

    def _calculate_complexity_score(self, requirements: Dict[str, Any]) -> int:
        """Calcule un score de complexité basé sur les exigences"""
        score = 0
        
        func_reqs = requirements.get("functional_requirements", [])
        score += min(len(func_reqs) // 5, 10)
        
        constraints = requirements.get("technical_constraints", {})
        if constraints:
            score += 5
        
        security_reqs = requirements.get("security_requirements", [])
        score += min(len(security_reqs) // 2, 10)
        
        scale = requirements.get("expected_scale", {})
        if scale.get("expected_users", 0) > 10000:
            score += 5
        if scale.get("expected_transactions", 0) > 1000:
            score += 5
        
        integrations = requirements.get("external_integrations", [])
        score += min(len(integrations), 10)
        
        return min(score, 100)

    def _get_complexity_level(self, score: int) -> str:
        """Détermine le niveau de complexité basé sur le score"""
        if score < 20:
            return "simple"
        elif score < 50:
            return "moderate"
        elif score < 80:
            return "complex"
        else:
            return "highly_complex"

    def _select_architecture_type(self, analysis: Dict[str, Any]) -> ArchitectureType:
        """Sélectionne le type d'architecture approprié"""
        complexity = analysis.get("complexity_level", "moderate")
        scale = analysis.get("expected_scale", {})
        users = scale.get("expected_users", 1000)
        
        if complexity == "simple" and users < 5000:
            return ArchitectureType.MONOLITH
        elif complexity == "moderate" or users > 5000:
            return ArchitectureType.MICROSERVICES
        elif complexity in ["complex", "highly_complex"]:
            if analysis.get("performance_requirements", {}).get("event_processing", False):
                return ArchitectureType.EVENT_DRIVEN
            else:
                return ArchitectureType.MICROSERVICES
        return ArchitectureType.MICROSERVICES

    async def split_spec_into_fragments(self, global_spec: Dict, strategy: str = "largeur_dabord") -> Dict[str, List[Dict]]:
        """
        Découpe une spécification globale en fragments individuels pour chaque instance de coder.py
        """
        self._logger.info(f"🔪 Découpage de la spécification en fragments...")
        
        fragments = {
            "by_domain": {},
            "by_priority": [],
            "by_complexity": [],
            "dependencies": {},
            "metadata": {
                "total_fragments": 0,
                "estimated_sprints": 0,
                "parallel_possible": True
            }
        }
        
        for fragment in global_spec.get("fragments", []):
            domain = fragment.get("domain", "unknown")
            
            fragment["coder_config"] = {
                "max_iterations": 3,
                "validation_level": "comprehensive",
                "generate_tests": True,
                "generate_docs": True
            }
            
            if domain not in fragments["by_domain"]:
                fragments["by_domain"][domain] = []
            fragments["by_domain"][domain].append(fragment)
            
            complexity = fragment.get("complexity", 5)
            fragments["by_complexity"].append((complexity, fragment))
            
            deps = []
            for dep in global_spec.get("dependencies", []):
                if dep["from"] == fragment["id"]:
                    deps.append(dep["to"])
            if deps:
                fragments["dependencies"][fragment["id"]] = deps
        
        fragments["by_complexity"].sort(key=lambda x: x[0])
        fragments["metadata"]["total_fragments"] = len(global_spec.get("fragments", []))
        fragments["metadata"]["estimated_sprints"] = self._estimate_sprints(fragments, strategy)
        
        base_dir = Path(f"./specs/fragments/{global_spec.get('project', 'unknown')}")
        base_dir.mkdir(parents=True, exist_ok=True)
        
        for fragment in global_spec.get("fragments", []):
            frag_file = base_dir / f"{fragment['id']}.json"
            with open(frag_file, 'w', encoding='utf-8') as f:
                json.dump(fragment, f, indent=2)
            self._logger.debug(f"  ✅ Fragment sauvegardé: {frag_file}")
        
        index_file = base_dir / "_index.json"
        with open(index_file, 'w', encoding='utf-8') as f:
            json.dump({
                "project": global_spec.get("project", "unknown"),
                "fragments": [f["id"] for f in global_spec.get("fragments", [])],
                "dependencies": fragments["dependencies"],
                "metadata": fragments["metadata"]
            }, f, indent=2)
        
        self._logger.info(f"✅ Découpage terminé: {fragments['metadata']['total_fragments']} fragments")
        return fragments

    def _estimate_sprints(self, fragments: Dict, strategy: str) -> int:
        """Estime le nombre de sprints nécessaires"""
        if strategy == "largeur_dabord":
            return max(len(f) for f in fragments["by_domain"].values())
        else:
            return sum(len(f) for f in fragments["by_domain"].values())

    def _create_design(self, analysis: Dict[str, Any], arch_type: ArchitectureType,
                      requirements: Dict[str, Any]) -> ArchitectureDesign:
        """Crée une conception d'architecture complète"""
        design = ArchitectureDesign(
            project_name=analysis["project_scope"],
            architecture_type=arch_type,
            description=analysis["description"],
            design_patterns=self._select_design_patterns(analysis, arch_type),
            constraints=requirements.get("technical_constraints", {}),
            assumptions=self._extract_assumptions(requirements),
            risks=self._identify_risks(analysis)
        )
        
        design.components = self._design_components(analysis, arch_type, requirements)
        design.deployment_specs = self._create_deployment_specs(analysis, arch_type)
        
        return design

    def _select_design_patterns(self, analysis: Dict[str, Any], arch_type: ArchitectureType) -> List[str]:
        """Sélectionne les patterns de conception appropriés"""
        patterns = []
        
        if arch_type == ArchitectureType.MICROSERVICES:
            patterns.extend(["API Gateway", "Service Discovery", "Circuit Breaker"])
        if arch_type == ArchitectureType.EVENT_DRIVEN:
            patterns.extend(["Event Sourcing", "CQRS", "Event Carried State Transfer"])
        if analysis.get("performance_requirements", {}).get("caching_required", False):
            patterns.append("Cache-Aside")
        if analysis.get("security_requirements"):
            patterns.append("Zero Trust")
        if analysis.get("expected_scale", {}).get("expected_users", 0) > 100000:
            patterns.extend(["Sharding", "Load Balancing"])
        
        return patterns

    def _extract_assumptions(self, requirements: Dict[str, Any]) -> List[str]:
        """Extrait les hypothèses des exigences"""
        assumptions = requirements.get("assumptions", [])
        default_assumptions = [
            "L'équipe de développement a les compétences nécessaires",
            "Les ressources budgétaires sont suffisantes",
            "Les délais sont réalistes"
        ]
        return assumptions + default_assumptions

    def _identify_risks(self, analysis: Dict[str, Any]) -> List[Dict[str, str]]:
        """Identifie les risques potentiels"""
        risks = []
        
        complexity = analysis.get("complexity_level", "moderate")
        if complexity in ["complex", "highly_complex"]:
            risks.append({
                "risk": "Complexité technique élevée",
                "impact": "Délais de développement prolongés",
                "mitigation": "Revues de code fréquentes et tests approfondis"
            })
        
        perf_reqs = analysis.get("performance_requirements", {})
        if perf_reqs.get("response_time", 1000) < 100:
            risks.append({
                "risk": "Exigences de performance strictes",
                "impact": "Difficulté à atteindre les objectifs de performance",
                "mitigation": "Tests de performance précoces et optimisation continue"
            })
        
        if analysis.get("security_requirements"):
            risks.append({
                "risk": "Exigences de sécurité élevées",
                "impact": "Vulnérabilités potentielles",
                "mitigation": "Revues de sécurité et tests de pénétration"
            })
        
        return risks

    def _design_components(self, analysis: Dict[str, Any], arch_type: ArchitectureType,
                          requirements: Dict[str, Any]) -> List[ComponentSpec]:
        """Conçoit les composants du système"""
        components = []
        
        api_gateway = ComponentSpec(
            name="api-gateway",
            component_type=ComponentType.API_GATEWAY,
            description="Point d'entrée unique pour toutes les requêtes API",
            technology=TechnologyStack.PYTHON_FASTAPI,
            endpoints=[{"path": "/api/v1/*", "method": "ALL", "description": "Route toutes les requêtes API"}],
            security_requirements=["JWT Authentication", "Rate Limiting", "CORS"]
        )
        components.append(api_gateway)
        
        func_reqs = requirements.get("functional_requirements", [])
        for i, req in enumerate(func_reqs[:10]):
            service_name = f"service-{i+1}"
            component = ComponentSpec(
                name=service_name,
                component_type=ComponentType.SERVICE,
                description=f"Implémente: {req.get('description', 'Fonctionnalité non décrite')}",
                technology=TechnologyStack.PYTHON_FASTAPI,
                dependencies=["api-gateway"],
                endpoints=[{"path": f"/api/v1/{service_name}", "method": "GET", "description": f"Endpoint pour {service_name}"}]
            )
            components.append(component)
        
        if analysis.get("technical_constraints", {}).get("database_type") == "postgresql":
            db_component = ComponentSpec(
                name="postgres-db",
                component_type=ComponentType.DATABASE,
                description="Base de données relationnelle principale",
                technology=TechnologyStack.POSTGRESQL,
                database_schemas=[{
                    "name": "public",
                    "tables": [{
                        "name": "users",
                        "columns": [
                            {"name": "id", "type": "uuid", "primary_key": True},
                            {"name": "email", "type": "varchar(255)", "unique": True},
                            {"name": "created_at", "type": "timestamp"}
                        ]
                    }]
                }]
            )
            components.append(db_component)
        
        auth_component = ComponentSpec(
            name="auth-service",
            component_type=ComponentType.AUTHENTICATION,
            description="Service d'authentification et d'autorisation",
            technology=TechnologyStack.PYTHON_FASTAPI,
            dependencies=["api-gateway"],
            endpoints=[
                {"path": "/api/v1/auth/login", "method": "POST", "description": "Authentification des utilisateurs"},
                {"path": "/api/v1/auth/register", "method": "POST", "description": "Enregistrement des nouveaux utilisateurs"}
            ]
        )
        components.append(auth_component)
        
        monitoring_component = ComponentSpec(
            name="monitoring-service",
            component_type=ComponentType.MONITORING,
            description="Surveillance des performances et de la santé du système",
            technology=TechnologyStack.PYTHON_FASTAPI,
            dependencies=["api-gateway"],
            environment_vars={"PROMETHEUS_PORT": "9090", "GRAFANA_PORT": "3000"}
        )
        components.append(monitoring_component)
        
        return components

    def _create_deployment_specs(self, analysis: Dict[str, Any],
                                arch_type: ArchitectureType) -> List[DeploymentSpec]:
        """Crée les spécifications de déploiement"""
        specs = []
        
        dev_spec = DeploymentSpec(
            environment="dev",
            cloud_provider="docker",
            scaling_config={"min_instances": 1, "max_instances": 2, "auto_scaling": False},
            networking={"subnet": "192.168.1.0/24", "public_access": False},
            monitoring={"enabled": True, "tools": ["docker logs", "basic metrics"]}
        )
        specs.append(dev_spec)
        
        prod_spec = DeploymentSpec(
            environment="prod",
            cloud_provider="aws",
            region="us-east-1",
            scaling_config={"min_instances": 3, "max_instances": 10, "auto_scaling": True,
                           "cpu_threshold": 70, "memory_threshold": 80},
            networking={"vpc": "vpc-123456", "subnets": ["subnet-a", "subnet-b", "subnet-c"],
                       "load_balancer": "application", "cdn": True},
            monitoring={"enabled": True, "tools": ["CloudWatch", "Prometheus", "Grafana", "New Relic"],
                       "alerts": ["pagerduty", "slack"]},
            backup_config={"enabled": True, "frequency": "daily", "retention_days": 30},
            disaster_recovery={"strategy": "multi-az", "rto": "4 hours", "rpo": "1 hour"}
        )
        specs.append(prod_spec)
        
        return specs

    def _generate_documentation(self, design: ArchitectureDesign) -> Dict[str, Any]:
        """Génère la documentation de l'architecture"""
        return {
            "overview": {
                "title": f"Architecture Documentation - {design.project_name}",
                "version": design.version,
                "last_updated": datetime.now().isoformat(),
                "author": "Architect Agent"
            },
            "architecture_decisions": [{
                "decision": f"Utilisation de l'architecture {design.architecture_type.value}",
                "context": "Basé sur l'analyse des exigences et de la complexité",
                "consequences": "Meilleure scalabilité et maintenabilité"
            }],
            "component_documentation": [{
                "name": comp.name,
                "type": comp.component_type.value,
                "responsibilities": comp.description,
                "interfaces": comp.endpoints,
                "dependencies": comp.dependencies
            } for comp in design.components],
            "deployment_guide": {
                "prerequisites": ["Docker", "Kubernetes CLI", "AWS CLI"],
                "steps": [
                    "1. Cloner le référentiel",
                    "2. Configurer les variables d'environnement",
                    "3. Construire les images Docker",
                    "4. Déployer sur Kubernetes"
                ]
            },
            "operational_guidelines": {
                "monitoring": "Surveiller les métriques de performance et les logs",
                "scaling": "Ajuster le nombre de réplicas en fonction de la charge",
                "backup": "Sauvegarder les bases de données quotidiennement"
            }
        }

    def _analyze_feedback(self, feedback: Dict[str, Any], design: ArchitectureDesign) -> Dict[str, Any]:
        """Analyse le feedback pour déterminer les actions nécessaires"""
        comments = feedback.get("comments", [])
        suggestions = feedback.get("suggestions", [])
        
        analysis = {
            "comments": comments,
            "suggestions": suggestions,
            "needs_revision": len(suggestions) > 0,
            "suggestions_applied": []
        }
        
        for suggestion in suggestions:
            if "simplifier" in suggestion.lower():
                analysis["suggestions_applied"].append("Simplification de l'architecture")
            elif "performance" in suggestion.lower():
                analysis["suggestions_applied"].append("Optimisation des performances")
            elif "sécurité" in suggestion.lower() or "security" in suggestion.lower():
                analysis["suggestions_applied"].append("Renforcement de la sécurité")
        
        return analysis

    def _revise_design(self, design: ArchitectureDesign, suggestions: List[str]) -> ArchitectureDesign:
        """Révision d'une conception basée sur les suggestions"""
        revised = ArchitectureDesign(
            project_name=design.project_name,
            architecture_type=design.architecture_type,
            description=design.description,
            components=design.components.copy(),
            deployment_specs=design.deployment_specs.copy(),
            design_patterns=design.design_patterns.copy(),
            constraints=design.constraints.copy(),
            assumptions=design.assumptions.copy(),
            risks=design.risks.copy(),
            created_at=design.created_at,
            version=f"{design.version}.1"
        )
        
        for suggestion in suggestions:
            if "simplifier" in suggestion.lower():
                if len(revised.components) > 10:
                    revised.components = revised.components[:10]
            if "performance" in suggestion.lower():
                has_cache = any(c.component_type == ComponentType.CACHE for c in revised.components)
                if not has_cache:
                    cache_component = ComponentSpec(
                        name="redis-cache",
                        component_type=ComponentType.CACHE,
                        description="Cache Redis pour améliorer les performances",
                        technology=TechnologyStack.REDIS
                    )
                    revised.components.append(cache_component)
        
        return revised

    # -------------------------------------------------------------------------
    # TEMPLATES PAR DÉFAUT (inchangés)
    # -------------------------------------------------------------------------

    def _get_default_templates(self) -> Dict[str, Any]:
        """Retourne les templates d'architecture par défaut"""
        return {
            "microservices": {
                "description": "Architecture microservices avec API Gateway",
                "components": ["api-gateway", "service-registry", "config-server"],
                "patterns": ["Circuit Breaker", "Service Discovery", "API Gateway"]
            },
            "monolith": {
                "description": "Architecture monolithique traditionnelle",
                "components": ["web-server", "application", "database"],
                "patterns": ["Layered Architecture", "Repository Pattern"]
            },
            "serverless": {
                "description": "Architecture serverless avec fonctions asynchrones",
                "components": ["api-gateway", "lambda-functions", "event-bridge"],
                "patterns": ["Function as a Service", "Event-Driven"]
            },
            "event_driven": {
                "description": "Architecture pilotée par les événements",
                "components": ["message-broker", "event-processors", "event-store"],
                "patterns": ["Event Sourcing", "CQRS", "Event Carried State Transfer"]
            }
        }

    def _get_microservices_template(self) -> Dict[str, Any]:
        """Template pour architecture microservices"""
        return {
            "name": "microservices",
            "description": "Architecture microservices pour applications complexes et scalables",
            "use_cases": [
                "Grandes équipes de développement",
                "Applications nécessitant une échelle indépendante des composants",
                "Systèmes avec des stacks technologiques hétérogènes"
            ],
            "components": [
                {
                    "type": "api_gateway",
                    "mandatory": True,
                    "technologies": ["Python/FastAPI", "Node.js/Express", "Spring Cloud Gateway"]
                },
                {
                    "type": "service_registry",
                    "mandatory": True,
                    "technologies": ["Consul", "Eureka", "Zookeeper"]
                },
                {
                    "type": "config_server",
                    "mandatory": True,
                    "technologies": ["Spring Cloud Config", "HashiCorp Consul"]
                }
            ],
            "best_practices": [
                "Définir des contrats d'API clairs",
                "Implémenter le circuit breaker pattern",
                "Utiliser la découverte de service",
                "Séparer les bases de données par service"
            ]
        }

    def _get_monolith_template(self) -> Dict[str, Any]:
        """Template pour architecture monolithique"""
        return {
            "name": "monolith",
            "description": "Architecture monolithique simple et facile à déployer",
            "use_cases": [
                "Petites à moyennes applications",
                "Équipes de développement réduites",
                "Prototypage rapide",
                "Applications avec faible complexité"
            ],
            "components": [
                {
                    "type": "web_server",
                    "mandatory": True,
                    "technologies": ["Nginx", "Apache", "IIS"]
                },
                {
                    "type": "application",
                    "mandatory": True,
                    "technologies": ["Django", "Spring Boot", "Ruby on Rails", "Laravel"]
                },
                {
                    "type": "database",
                    "mandatory": True,
                    "technologies": ["PostgreSQL", "MySQL", "MongoDB"]
                }
            ],
            "best_practices": [
                "Organiser le code en modules",
                "Utiliser des migrations de base de données",
                "Implémenter le caching",
                "Séparer les couches (présentation, logique, données)"
            ]
        }

    def _get_serverless_template(self) -> Dict[str, Any]:
        """Template pour architecture serverless"""
        return {
            "name": "serverless",
            "description": "Architecture serverless pour réduire les coûts d'infrastructure",
            "use_cases": [
                "Applications avec charge variable",
                "Traitement par lots (batch processing)",
                "API avec faible traffic",
                "Automatisation de workflows"
            ],
            "components": [
                {
                    "type": "api_gateway",
                    "mandatory": True,
                    "technologies": ["AWS API Gateway", "Azure API Management", "Google Cloud Endpoints"]
                },
                {
                    "type": "functions",
                    "mandatory": True,
                    "technologies": ["AWS Lambda", "Azure Functions", "Google Cloud Functions"]
                },
                {
                    "type": "event_sources",
                    "mandatory": False,
                    "technologies": ["S3", "DynamoDB Streams", "EventBridge", "Pub/Sub"]
                }
            ],
            "best_practices": [
                "Garder les fonctions stateless",
                "Optimiser la taille des packages",
                "Utiliser le cold start mitigation",
                "Implémenter les retries et les dead letter queues"
            ]
        }

    def _get_event_driven_template(self) -> Dict[str, Any]:
        """Template pour architecture event-driven"""
        return {
            "name": "event_driven",
            "description": "Architecture pilotée par les événements pour systèmes découplés",
            "use_cases": [
                "Systèmes en temps réel",
                "Traitement de flux de données",
                "Applications avec haute disponibilité",
                "Intégration de systèmes hétérogènes"
            ],
            "components": [
                {
                    "type": "message_broker",
                    "mandatory": True,
                    "technologies": ["Apache Kafka", "RabbitMQ", "AWS SQS", "Azure Service Bus"]
                },
                {
                    "type": "event_processors",
                    "mandatory": True,
                    "technologies": ["Python", "Java", "Go", "Node.js"]
                },
                {
                    "type": "event_store",
                    "mandatory": False,
                    "technologies": ["EventStoreDB", "MongoDB", "Cassandra"]
                }
            ],
            "best_practices": [
                "Définir des schémas d'événements clairs",
                "Implémenter l'idempotence",
                "Utiliser le pattern outbox",
                "Surveiller les latences et les backlogs"
            ]
        }

    def _get_default_patterns(self) -> Dict[str, Any]:
        """Retourne les patterns d'architecture par défaut"""
        return {
            "microservices_patterns": [
                {
                    "name": "API Gateway",
                    "description": "Point d'entrée unique pour toutes les requêtes client",
                    "use_case": "Routage, authentification, limitation de débit"
                },
                {
                    "name": "Circuit Breaker",
                    "description": "Empêche les appels à des services défaillants",
                    "use_case": "Tolérance aux pannes et résilience"
                },
                {
                    "name": "Service Discovery",
                    "description": "Découverte dynamique des instances de service",
                    "use_case": "Environnements avec scaling automatique"
                }
            ],
            "data_patterns": [
                {
                    "name": "CQRS",
                    "description": "Séparation des modèles de lecture et d'écriture",
                    "use_case": "Applications avec modèles de lecture/écriture différents"
                },
                {
                    "name": "Event Sourcing",
                    "description": "Stockage des événements plutôt que de l'état",
                    "use_case": "Audit trail, récupération d'état"
                },
                {
                    "name": "SAGA",
                    "description": "Gestion des transactions distribuées",
                    "use_case": "Orchestration de workflows entre services"
                }
            ],
            "deployment_patterns": [
                {
                    "name": "Blue-Green Deployment",
                    "description": "Déploiement sans interruption de service",
                    "use_case": "Mises à jour critiques avec zéro temps d'arrêt"
                },
                {
                    "name": "Canary Release",
                    "description": "Déploiement progressif à un sous-ensemble d'utilisateurs",
                    "use_case": "Tests en production et réduction des risques"
                }
            ]
        }

    # -------------------------------------------------------------------------
    # GESTION DES MESSAGES (ALIGNÉE SUR CODER)
    # -------------------------------------------------------------------------

    async def _handle_custom_message(self, message: Message) -> Optional[Message]:
        """
        Gère les messages personnalisés pour l'agent Architect.
        """
        try:
            message_type = message.message_type

            handlers = {
                "design_architecture": self._handle_design_architecture,
                "review_design": self._handle_review_design,
                "get_design": self._handle_get_design,
                "validate_requirements": self._handle_validate_requirements,
                "split_spec": self._handle_split_spec,
            }

            if message_type in handlers:
                return await handlers[message_type](message)

            self._logger.warning(f"Type de message non reconnu: {message_type}")
            return None

        except Exception as e:
            self._logger.error(f"Erreur lors du traitement du message personnalisé: {e}")
            return Message(
                sender=self.name,
                recipient=message.sender,
                content={"error": str(e)},
                message_type="error",
                correlation_id=message.message_id
            )

    async def _handle_design_architecture(self, message: Message) -> Message:
        requirements = message.content.get("requirements", {})
        result = await self.design_architecture(requirements)
        return Message(
            sender=self.name,
            recipient=message.sender,
            content={"design_result": result},
            message_type="design_result",
            correlation_id=message.message_id
        )

    async def _handle_review_design(self, message: Message) -> Message:
        design_id = message.content.get("design_id", "")
        feedback = message.content.get("feedback", {})
        result = await self.review_design(design_id, feedback)
        return Message(
            sender=self.name,
            recipient=message.sender,
            content={"review_result": result},
            message_type="review_result",
            correlation_id=message.message_id
        )

    async def _handle_get_design(self, message: Message) -> Message:
        design_id = message.content.get("design_id", "")
        design = self.get_design(design_id)
        return Message(
            sender=self.name,
            recipient=message.sender,
            content={"design": design},
            message_type="design_response",
            correlation_id=message.message_id
        )

    async def _handle_validate_requirements(self, message: Message) -> Message:
        requirements = message.content.get("requirements", {})
        result = self.validate_requirements(requirements)
        return Message(
            sender=self.name,
            recipient=message.sender,
            content={"validation_result": result},
            message_type="validation_response",
            correlation_id=message.message_id
        )

    async def _handle_split_spec(self, message: Message) -> Message:
        global_spec = message.content.get("spec", {})
        strategy = message.content.get("strategy", "largeur_dabord")
        result = await self.split_spec_into_fragments(global_spec, strategy)
        return Message(
            sender=self.name,
            recipient=message.sender,
            content={"fragments": result},
            message_type="split_spec_result",
            correlation_id=message.message_id
        )


# -----------------------------------------------------------------------------
# FONCTION FACTORY
# -----------------------------------------------------------------------------

def create_architect_agent(config_path: Optional[str] = None) -> ArchitectAgent:
    """Crée une instance de l'agent Architect"""
    return ArchitectAgent(config_path)


# -----------------------------------------------------------------------------
# POINT D'ENTRÉE POUR LES TESTS (CORRIGÉ)
# -----------------------------------------------------------------------------

async def test_architect_agent():
    """Teste l'agent Architect"""
    print("🧪 Test de l'agent Architect...")

    agent = ArchitectAgent()

    print(f"  Création: {agent}")
    print(f"  Nom: {agent.name}")
    print(f"  Statut: {agent.status}")

    success = await agent.initialize()
    print(f"  Initialisation: {'✅' if success else '❌'}")

    if success:
        requirements = {
            "project_name": "Test E-Commerce Platform",
            "description": "Plateforme e-commerce avec catalogue, panier et paiement",
            "functional_requirements": [
                {"id": "FR1", "description": "Gestion des utilisateurs et authentification"},
                {"id": "FR2", "description": "Catalogue de produits avec recherche et filtres"},
                {"id": "FR3", "description": "Panier d'achat et gestion des commandes"},
                {"id": "FR4", "description": "Système de paiement sécurisé"},
                {"id": "FR5", "description": "Gestion des stocks en temps réel"}
            ],
            "non_functional_requirements": {
                "performance": {"response_time": "200ms p95", "throughput": "1000 req/s"},
                "availability": "99.99%",
                "scalability": "Horizontal scaling support"
            },
            "technical_constraints": {
                "programming_languages": ["Python", "JavaScript"],
                "database_type": "postgresql"
            },
            "expected_scale": {"expected_users": 100000, "expected_transactions": 10000}
        }

        result = await agent.design_architecture(requirements)

        if result["success"]:
            design_id = result["design_id"]
            print(f"  Conception créée: {design_id}")
            print(f"  Type d'architecture: {result['architecture']['architecture_type']}")
            print(f"  Nombre de composants: {len(result['architecture']['components'])}")

            designs = agent.list_designs()
            print(f"  Conceptions disponibles: {len(designs)}")
        else:
            print(f"  ❌ Échec de la conception: {result.get('error', 'Erreur inconnue')}")

    health = await agent.health_check()
    print(f"  Santé: {health['status']}")

    await agent.shutdown()
    print(f"  Statut final: {agent.status}")

    print("✅ Test ArchitectAgent terminé")


if __name__ == "__main__":
    asyncio.run(test_architect_agent())
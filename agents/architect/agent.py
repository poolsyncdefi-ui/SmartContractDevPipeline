"""
Architect Agent - Agent responsable de la conception de l'architecture des systèmes
Version: 4.0.0 (CORRIGÉE - ALIGNEMENT COMPLET AVEC BASEAGENT)
Auteur: PoolSync DeFi
Date: 2026-03-24
"""

import os
import sys
import yaml
import json
import logging
import asyncio
import time
import hashlib
from pathlib import Path
from typing import Dict, List, Any, Optional, Union, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)

# Ajouter le chemin du projet au PYTHONPATH
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from agents.base_agent.base_agent import BaseAgent, AgentStatus, Message, MessageType, AgentCapability


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
class ArchitectureDecision:
    """Architecture Decision Record (ADR)"""
    title: str
    status: str
    context: str
    decision: str
    consequences: List[str] = field(default_factory=list)
    alternatives_considered: List[Dict[str, str]] = field(default_factory=list)
    trade_offs: List[str] = field(default_factory=list)
    risks: List[Dict[str, str]] = field(default_factory=list)
    mitigations: List[str] = field(default_factory=list)
    compliance_impact: Optional[str] = None
    cost_impact: Optional[str] = None
    reviewers: List[str] = field(default_factory=list)
    approval_date: Optional[str] = None
    decision_id: str = field(default_factory=lambda: f"ADR_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "decision_id": self.decision_id,
            "title": self.title,
            "status": self.status,
            "context": self.context,
            "decision": self.decision,
            "consequences": self.consequences,
            "alternatives_considered": self.alternatives_considered,
            "trade_offs": self.trade_offs,
            "risks": self.risks,
            "mitigations": self.mitigations,
            "compliance_impact": self.compliance_impact,
            "cost_impact": self.cost_impact,
            "reviewers": self.reviewers,
            "approval_date": self.approval_date,
            "created_at": self.created_at.isoformat()
        }


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
    decisions: List[ArchitectureDecision] = field(default_factory=list)
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
            "decisions": [dec.to_dict() for dec in self.decisions],
            "created_at": self.created_at.isoformat(),
            "version": self.version
        }


# -----------------------------------------------------------------------------
# CLASSE DE CACHE LRU
# -----------------------------------------------------------------------------

class LRUCache:
    """Cache LRU simple pour les designs et patterns"""
    
    def __init__(self, max_size: int = 500, ttl_seconds: int = 3600):
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self._cache: Dict[str, Any] = {}
        self._order: List[str] = []
        self._timestamps: Dict[str, datetime] = {}
    
    def get(self, key: str) -> Optional[Any]:
        if key not in self._cache:
            return None
        
        # Vérifier TTL
        if key in self._timestamps:
            age = (datetime.now() - self._timestamps[key]).total_seconds()
            if age > self.ttl_seconds:
                self._pop(key)
                return None
        
        # Mettre à jour l'ordre (LRU)
        if key in self._order:
            self._order.remove(key)
        self._order.append(key)
        
        return self._cache[key]
    
    def set(self, key: str, value: Any):
        if key in self._cache:
            if key in self._order:
                self._order.remove(key)
        else:
            if len(self._cache) >= self.max_size:
                oldest = self._order.pop(0)
                self._pop(oldest)
        
        self._cache[key] = value
        self._order.append(key)
        self._timestamps[key] = datetime.now()
    
    def _pop(self, key: str):
        if key in self._cache:
            del self._cache[key]
        if key in self._timestamps:
            del self._timestamps[key]
        if key in self._order:
            self._order.remove(key)
    
    def clear(self):
        self._cache.clear()
        self._order.clear()
        self._timestamps.clear()
    
    def size(self) -> int:
        return len(self._cache)


# -----------------------------------------------------------------------------
# CLASSE ARCHITECT AGENT (VERSION 4.0.0 CORRIGÉE)
# -----------------------------------------------------------------------------

class ArchitectAgent(BaseAgent):
    """
    Agent responsable de la conception de l'architecture des systèmes.
    Version optimisée avec configuration renforcée, cache, métriques et délégation.
    """

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialise l'agent Architect avec configuration renforcée.
        """
        # Appeler le constructeur de BaseAgent
        super().__init__(config_path)
        
        # Redéfinir les attributs (BaseAgent les a initialisés avec des valeurs par défaut)
        self._name = "ArchitectAgent"
        self._display_name = "🏛️ Agent Architecte Système"
        self._description = "Agent responsable de la conception de l'architecture des systèmes"
        self._version = "4.0.0"
        
        # État spécifique à l'Architect
        self._designs: Dict[str, ArchitectureDesign] = {}
        self._templates: Dict[str, Any] = {}
        self._patterns_library: Dict[str, Any] = {}
        
        # Sous-agents
        self._sub_agents: Dict[str, Any] = {}
        self._domain_agents: Dict[str, Any] = {}
        
        # Domain mapping
        self._domain_mapping: Dict[str, str] = {}
        
        # Configuration anti-hallucination (chargée depuis le YAML)
        self._anti_hallucination_config: Dict[str, Any] = {}
        self._confidence_threshold: float = 0.85
        self._strict_mode: bool = False
        
        # Configuration performance
        self._performance_config: Dict[str, Any] = {}
        self._max_concurrent_designs: int = 5
        self._max_concurrent_delegations: int = 10
        self._design_semaphore: Optional[asyncio.Semaphore] = None
        self._delegation_semaphore: Optional[asyncio.Semaphore] = None
        
        # Cache
        self._cache_enabled: bool = True
        self._design_cache: Optional[LRUCache] = None
        
        # Métriques de performance (complémentaires à celles de BaseAgent)
        self._architect_metrics: Dict[str, Any] = {
            "designs_created": 0,
            "designs_cached": 0,
            "delegations_successful": 0,
            "delegations_failed": 0,
            "validation_failures": 0,
            "avg_design_time_ms": 0,
            "total_design_time_ms": 0,
            "adr_generated": 0,
            "conflicts_resolved": 0
        }
        
        # Statistiques des circuits (fallback)
        self._circuit_stats: Dict[str, Dict[str, Any]] = {}
        
        # Charger les templates et patterns
        self._load_templates()
        self._load_patterns()
        
        # Charger la configuration renforcée
        self._load_and_validate_config()
        
        self._logger.info(f"Agent Architect v{self._version} initialisé avec {self._max_concurrent_designs} designs concurrents max")

    # -------------------------------------------------------------------------
    # SURCHARGES DES MÉTHODES DE BASEAGENT
    # -------------------------------------------------------------------------

    async def _initialize_components(self) -> bool:
        """
        Initialise les composants spécifiques de l'agent Architect.
        Cette méthode est appelée par BaseAgent.initialize()
        """
        try:
            self._logger.info("Initialisation des composants de l'agent Architect v4.0.0...")

            # Charger le mapping des domaines depuis la config
            self._domain_mapping = self._agent_config.get('domain_mapping', {})

            # Initialiser les sémaphores
            self._design_semaphore = asyncio.Semaphore(self._max_concurrent_designs)
            self._delegation_semaphore = asyncio.Semaphore(self._max_concurrent_delegations)

            # Initialiser le cache
            if self._cache_enabled:
                caching_config = self._agent_config.get('caching', {})
                max_cache_size = caching_config.get('max_size', 500)
                cache_ttl = caching_config.get('ttl_seconds', 3600)
                self._design_cache = LRUCache(max_size=max_cache_size, ttl_seconds=cache_ttl)

            # Ajouter les capacités depuis la config
            capabilities_list = self._agent_config.get('agent', {}).get('capabilities', [])
            for cap in capabilities_list:
                if isinstance(cap, dict):
                    self.add_capability(AgentCapability(
                        name=cap.get('name', 'unknown'),
                        description=cap.get('description', ''),
                        version=cap.get('version', '1.0.0')
                    ))

            # Initialiser les sous-agents
            await self._initialize_sub_agents()

            self._logger.info("Composants de l'agent Architect initialisés avec succès")
            return True

        except Exception as e:
            self._logger.error(f"Erreur lors de l'initialisation des composants: {e}")
            return False

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
                "record_call_result": self._handle_record_call_result,
                "check_service_circuit": self._handle_check_service_circuit,
                "delegate_to_domain": self._handle_delegate_to_domain,
                "delegate_multi_domain": self._handle_delegate_multi_domain,
                "resolve_conflicts": self._handle_resolve_conflicts,
                "create_adr": self._handle_create_adr,
                "get_architect_metrics": self._handle_get_metrics,
            }

            if message_type in handlers:
                return await handlers[message_type](message)

            self._logger.warning(f"Type de message non reconnu: {message_type}")
            return None

        except Exception as e:
            self._logger.error(f"Erreur lors du traitement du message: {e}")
            return Message(
                sender=self._name,
                recipient=message.sender,
                content={"error": str(e)},
                message_type=MessageType.ERROR.value,
                correlation_id=message.message_id
            )

    # -------------------------------------------------------------------------
    # MÉTHODES D'INITIALISATION INTERNES
    # -------------------------------------------------------------------------

    def _load_and_validate_config(self):
        """Charge et valide la configuration renforcée"""
        try:
            # Charger la configuration anti-hallucination
            self._anti_hallucination_config = self._agent_config.get('anti_hallucination', {})
            self._confidence_threshold = self._anti_hallucination_config.get('confidence_threshold', 0.85)
            self._strict_mode = self._anti_hallucination_config.get('strict_mode', False)
            
            # Charger la configuration performance
            self._performance_config = self._agent_config.get('performance', {})
            self._max_concurrent_designs = self._performance_config.get('max_concurrent_designs', 5)
            self._max_concurrent_delegations = self._performance_config.get('max_concurrent_delegations', 10)
            
            # Charger la configuration cache
            caching_config = self._agent_config.get('caching', {})
            self._cache_enabled = caching_config.get('enabled', True)
            
            # =============================================================
            # CORRECTION 1 : Assurer la présence des champs obligatoires
            # pour la validation de BaseAgent
            # =============================================================
            if 'agent' not in self._agent_config:
                self._agent_config['agent'] = {}
            
            agent_section = self._agent_config['agent']
            
            if 'name' not in agent_section:
                agent_section['name'] = self._name
                self._logger.debug(f"Champ 'agent.name' ajouté: {self._name}")
            
            if 'version' not in agent_section:
                agent_section['version'] = self._version
                self._logger.debug(f"Champ 'agent.version' ajouté: {self._version}")
            
            # =============================================================
            # CORRECTION 2 : Charger les capacités depuis la configuration
            # =============================================================
            capabilities_list = self._agent_config.get('capabilities', [])
            if capabilities_list:
                loaded_count = 0
                for cap in capabilities_list:
                    if isinstance(cap, dict):
                        self.add_capability(AgentCapability(
                            name=cap.get('name', 'unknown'),
                            description=cap.get('description', ''),
                            version=cap.get('version', '1.0.0')
                        ))
                        loaded_count += 1
                self._logger.info(f"✅ {loaded_count} capacités chargées depuis la configuration")
            else:
                # Optionnel : ajouter des capacités par défaut si aucune n'est définie
                default_capabilities = [
                    "DESIGN_SYSTEM_ARCHITECTURE",
                    "DESIGN_MICROSERVICES",
                    "DESIGN_CLOUD_INFRASTRUCTURE",
                    "DELEGATE_TO_DOMAIN"
                ]
                for cap_name in default_capabilities:
                    self.add_capability(AgentCapability(
                        name=cap_name,
                        description=f"Capacité {cap_name}",
                        version="1.0.0"
                    ))
                self._logger.info(f"✅ {len(default_capabilities)} capacités par défaut ajoutées")
            
            # Vérifier les sections critiques
            required_sections = ['anti_hallucination', 'validation_rules', 'performance']
            for section in required_sections:
                if section not in self._agent_config:
                    self._logger.debug(f"Section {section} non trouvée dans la configuration")
            
            # Vérifier les alertes
            alerting_config = self._agent_config.get('alerting', {})
            if alerting_config.get('enabled'):
                self._logger.info("Alerting activé")
            
            self._logger.info("Configuration validée avec succès")
            
        except Exception as e:
            self._logger.error(f"Erreur lors de la validation de la configuration: {e}")

    async def _initialize_sub_agents(self):
        """
        Initialise les sous-agents spécialisés.
        """
        try:
            # -----------------------------------------------------------------
            # 1. SOUS-AGENTS ARCHITECTURAUX (spécialisations techniques)
            # -----------------------------------------------------------------
            try:
                from agents.architect.sous_agents import (
                    CloudArchitectSubAgent,
                    BlockchainArchitectSubAgent,
                    MicroservicesArchitectSubAgent,
                    BackendArchitectSubAgent,
                    BankingSpecialistSubAgent
                )
                
                # Vérifier que les classes existent avant de les instancier
                if CloudArchitectSubAgent:
                    self._domain_agents["cloud"] = CloudArchitectSubAgent()
                    self._sub_agents["cloud"] = self._domain_agents["cloud"]
                    self._logger.info("✅ CloudArchitectSubAgent chargé")
                
                if BlockchainArchitectSubAgent:
                    self._domain_agents["blockchain"] = BlockchainArchitectSubAgent()
                    self._sub_agents["blockchain"] = self._domain_agents["blockchain"]
                    self._logger.info("✅ BlockchainArchitectSubAgent chargé")
                
                if MicroservicesArchitectSubAgent:
                    self._domain_agents["microservices"] = MicroservicesArchitectSubAgent()
                    self._sub_agents["microservices"] = self._domain_agents["microservices"]
                    self._logger.info("✅ MicroservicesArchitectSubAgent chargé")
                
                if BackendArchitectSubAgent:
                    self._domain_agents["backend"] = BackendArchitectSubAgent()
                    self._sub_agents["backend"] = self._domain_agents["backend"]
                    self._logger.info("✅ BackendArchitectSubAgent chargé")
                
                if BankingSpecialistSubAgent:
                    self._domain_agents["banking"] = BankingSpecialistSubAgent()
                    self._sub_agents["banking"] = self._domain_agents["banking"]
                    self._logger.info("✅ BankingSpecialistSubAgent chargé")
                
            except ImportError as e:
                self._logger.debug(f"Sous-agents architecturaux non trouvés: {e}")
            
            # -----------------------------------------------------------------
            # 2. CIRCUIT BREAKER (optionnel - pour résilience)
            # -----------------------------------------------------------------
            try:
                from agents.communication.sous_agents.circuit_breaker.agent import CircuitBreakerSubAgent
                self._sub_agents["circuit_breaker"] = CircuitBreakerSubAgent()
                self._logger.info("✅ Circuit Breaker SubAgent chargé (service de résilience)")
            except ImportError as e:
                self._logger.debug(f"Circuit Breaker SubAgent non disponible (optionnel): {e}")
                self._sub_agents["circuit_breaker"] = None
            
            # -----------------------------------------------------------------
            # 3. INITIALISATION DES SOUS-AGENTS
            # -----------------------------------------------------------------
            for agent_id, agent in self._sub_agents.items():
                if agent and hasattr(agent, 'initialize'):
                    try:
                        await agent.initialize()
                        self._logger.debug(f"Sous-agent {agent_id} initialisé")
                    except Exception as e:
                        self._logger.error(f"Erreur initialisation {agent_id}: {e}")
            
            self._logger.info(f"✅ {len(self._sub_agents)} sous-agents initialisés ({len(self._domain_agents)} métier)")
                        
        except Exception as e:
            self._logger.error(f"Erreur lors de l'initialisation des sous-agents: {e}")
            self._sub_agents = {}
            self._domain_agents = {}
        
    # -------------------------------------------------------------------------
    # MÉTHODES DE CHARGEMENT DES TEMPLATES ET PATTERNS
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

    # -------------------------------------------------------------------------
    # MÉTHODES DE VALIDATION
    # -------------------------------------------------------------------------

    def validate_requirements(self, requirements: Dict[str, Any]) -> Dict[str, Any]:
        """
        Valide les exigences d'architecture.
        """
        errors = []
        warnings = []
        
        if not requirements:
            errors.append("Aucune exigence fournie")
            return {"valid": False, "errors": errors, "warnings": warnings}
        
        # Validation de base
        required_fields = ["project_name", "description", "functional_requirements"]
        for field in required_fields:
            if field not in requirements:
                errors.append(f"Champ obligatoire manquant: {field}")
        
        func_reqs = requirements.get("functional_requirements", [])
        if not isinstance(func_reqs, list) or len(func_reqs) == 0:
            errors.append("Aucune exigence fonctionnelle spécifiée")
        
        # Validation renforcée avec les règles de configuration
        validation_rules = self._agent_config.get('validation_rules', [])
        
        for rule in validation_rules:
            rule_name = rule.get('name')
            severity = rule.get('severity')
            
            if rule_name == "scalability_proven":
                scale = requirements.get("expected_scale", {})
                if not scale.get("expected_users") and not scale.get("expected_transactions"):
                    msg = "Scalabilité non documentée - prévoir une analyse de charge"
                    if severity == "critical":
                        errors.append(msg)
                        self._architect_metrics["validation_failures"] += 1
                    else:
                        warnings.append(msg)
            
            elif rule_name == "disaster_recovery_defined":
                dr_plan = requirements.get("disaster_recovery", {})
                if not dr_plan.get("rto") or not dr_plan.get("rpo"):
                    errors.append("Plan de reprise d'activité (RTO/RPO) non défini")
                    self._architect_metrics["validation_failures"] += 1
            
            elif rule_name == "security_requirements_met":
                security_reqs = requirements.get("security_requirements", [])
                if not security_reqs:
                    errors.append("Exigences de sécurité non spécifiées")
                    self._architect_metrics["validation_failures"] += 1
        
        # Vérifier les hypothèses manquantes
        assumptions = requirements.get("assumptions", [])
        if not assumptions:
            warnings.append("Aucune hypothèse documentée - risque de malentendus")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }

    # -------------------------------------------------------------------------
    # MÉTHODES DE CONCEPTION PRINCIPALES
    # -------------------------------------------------------------------------

    async def design_architecture(self, requirements: Dict[str, Any]) -> Dict[str, Any]:
        """
        Conçoit une architecture basée sur les exigences.
        """
        start_time = time.time()
        
        try:
            # Vérifier le cache
            cache_key = hashlib.md5(json.dumps(requirements, sort_keys=True).encode()).hexdigest()
            if self._cache_enabled and self._design_cache:
                cached = self._design_cache.get(cache_key)
                if cached:
                    self._architect_metrics["designs_cached"] += 1
                    self._logger.debug(f"Design récupéré du cache: {cache_key}")
                    return cached
            
            self._logger.info("Démarrage de la conception de l'architecture...")
            
            # Validation
            validation_result = self.validate_requirements(requirements)
            if not validation_result["valid"]:
                return {
                    "success": False,
                    "error": "Exigences invalides",
                    "validation_errors": validation_result["errors"]
                }
            
            # Analyse et conception
            analysis = self._analyze_requirements(requirements)
            arch_type = self._select_architecture_type(analysis)
            design = self._create_design(analysis, arch_type, requirements)
            
            # Documentation
            documentation = self._generate_documentation(design)
            
            # Stockage
            self._designs[design.design_id] = design
            self._architect_metrics["designs_created"] += 1
            
            # Mise en cache
            result = {
                "success": True,
                "design_id": design.design_id,
                "architecture": design.to_dict(),
                "documentation": documentation,
                "analysis": analysis,
                "created_at": design.created_at.isoformat()
            }
            
            if self._cache_enabled and self._design_cache:
                self._design_cache.set(cache_key, result)
            
            execution_time = (time.time() - start_time) * 1000
            self._architect_metrics["total_design_time_ms"] += execution_time
            self._architect_metrics["avg_design_time_ms"] = (
                self._architect_metrics["total_design_time_ms"] / 
                self._architect_metrics["designs_created"]
            )
            
            self._logger.info(f"Architecture conçue avec succès: {design.design_id} ({execution_time:.0f}ms)")
            
            return result
                
        except Exception as e:
            self._logger.error(f"Erreur lors de la conception de l'architecture: {e}")
            return {
                "success": False,
                "error": str(e)
            }

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
        """Détermine le niveau de complexité"""
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
                "author": "Architect Agent v4.0"
            },
            "component_documentation": [{
                "name": comp.name,
                "type": comp.component_type.value,
                "responsibilities": comp.description,
                "interfaces": comp.endpoints,
                "dependencies": comp.dependencies
            } for comp in design.components]
        }

    async def split_spec_into_fragments(self, global_spec: Dict, strategy: str = "largeur_dabord") -> Dict[str, Any]:
        """Découpe une spécification globale en fragments"""
        self._logger.info(f"🔪 Découpage de la spécification en fragments...")
        
        fragments = {
            "by_domain": {},
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
        
        self._logger.info(f"✅ Découpage terminé: {fragments['metadata']['total_fragments']} fragments")
        return fragments

    def _estimate_sprints(self, fragments: Dict, strategy: str) -> int:
        """Estime le nombre de sprints nécessaires"""
        if strategy == "largeur_dabord":
            return max(len(f) for f in fragments["by_domain"].values()) if fragments["by_domain"] else 0
        else:
            return sum(len(f) for f in fragments["by_domain"].values())

    # -------------------------------------------------------------------------
    # MÉTHODES DE DÉLÉGATION ET RÉSILIENCE
    # -------------------------------------------------------------------------

    async def delegate_to_domain(self, domain: str, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Délègue une tâche à un sous-agent métier.
        """
        start_time = datetime.now()
        
        agent = self._domain_agents.get(domain)
        if not agent:
            self._architect_metrics["delegations_failed"] += 1
            return {
                "success": False,
                "error": f"Sous-agent pour le domaine '{domain}' non trouvé",
                "available_domains": list(self._domain_agents.keys())
            }
        
        # Vérifier le circuit breaker
        circuit_check = await self.check_service_circuit(f"{domain}_{action}")
        if not circuit_check.get("allowed", True):
            self._architect_metrics["delegations_failed"] += 1
            return {
                "success": False,
                "error": f"Circuit ouvert pour {domain}_{action}",
                "circuit_state": circuit_check.get("state")
            }
        
        try:
            if hasattr(agent, action):
                result = await getattr(agent, action)(**params) if asyncio.iscoroutinefunction(getattr(agent, action)) else getattr(agent, action)(**params)
                
                await self.record_call_result(f"{domain}_{action}", True)
                self._architect_metrics["delegations_successful"] += 1
                
                execution_time = (datetime.now() - start_time).total_seconds() * 1000
                
                return {
                    "success": True,
                    "domain": domain,
                    "action": action,
                    "result": result,
                    "execution_time_ms": execution_time
                }
            else:
                await self.record_call_result(f"{domain}_{action}", False, f"Action '{action}' non trouvée")
                self._architect_metrics["delegations_failed"] += 1
                
                return {
                    "success": False,
                    "error": f"Action '{action}' non trouvée",
                    "available_actions": [m for m in dir(agent) if not m.startswith('_') and callable(getattr(agent, m))]
                }
                
        except Exception as e:
            await self.record_call_result(f"{domain}_{action}", False, str(e))
            self._architect_metrics["delegations_failed"] += 1
            return {
                "success": False,
                "error": str(e),
                "domain": domain,
                "action": action
            }

    async def record_call_result(self, service_name: str, success: bool, error: Optional[str] = None) -> Dict[str, Any]:
        """Enregistre le résultat d'un appel vers un service."""
        cb = self._sub_agents.get("circuit_breaker")
        if not cb:
            # Fallback local
            if service_name not in self._circuit_stats:
                self._circuit_stats[service_name] = {
                    "success_count": 0,
                    "failure_count": 0
                }
            if success:
                self._circuit_stats[service_name]["success_count"] += 1
            else:
                self._circuit_stats[service_name]["failure_count"] += 1
            return {"success": True, "recorded_locally": True}
        
        if success:
            return await cb.record_success(service_name)
        else:
            return await cb.record_failure(service_name, error)

    async def check_service_circuit(self, service_name: str) -> Dict[str, Any]:
        """Vérifie si un service est accessible selon le circuit breaker."""
        cb = self._sub_agents.get("circuit_breaker")
        if not cb:
            return {"allowed": True, "circuit_available": False}
        
        result = await cb.check_circuit(service_name)
        return {
            "allowed": result.get("allowed", True),
            "state": result.get("state"),
            "failure_rate": result.get("failure_rate")
        }

    # -------------------------------------------------------------------------
    # MÉTHODES DE RÉCUPÉRATION
    # -------------------------------------------------------------------------

    def get_design(self, design_id: str) -> Optional[Dict[str, Any]]:
        """Récupère une conception d'architecture"""
        design = self._designs.get(design_id)
        if design:
            return design.to_dict()
        return None

    def list_designs(self) -> List[Dict[str, Any]]:
        """Liste toutes les conceptions disponibles"""
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

    def get_architect_metrics(self) -> Dict[str, Any]:
        """Retourne les métriques spécifiques de l'architecte"""
        return {
            **self._architect_metrics,
            "designs_count": len(self._designs),
            "cache_size": self._design_cache.size() if self._design_cache else 0,
            "cache_enabled": self._cache_enabled,
            "sub_agents_count": len(self._sub_agents),
            "domain_agents_count": len(self._domain_agents)
        }

    # -------------------------------------------------------------------------
    # MÉTHODES DE NETTOYAGE
    # -------------------------------------------------------------------------

    async def _cleanup(self):
        """Nettoie les ressources spécifiques de l'agent"""
        self._logger.info("Nettoyage des ressources de l'ArchitectAgent...")
        
        # Nettoyer le cache
        if self._design_cache:
            self._design_cache.clear()
        
        # Arrêter les sous-agents
        for agent_id, agent in self._sub_agents.items():
            if agent and hasattr(agent, 'shutdown'):
                try:
                    await agent.shutdown()
                except Exception as e:
                    self._logger.error(f"Erreur arrêt {agent_id}: {e}")
        
        await super()._cleanup()

    # -------------------------------------------------------------------------
    # TEMPLATES PAR DÉFAUT
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
        return {
            "name": "microservices",
            "description": "Architecture microservices pour applications complexes et scalables",
            "use_cases": ["Grandes équipes", "Échelle indépendante", "Stacks hétérogènes"],
            "components": [
                {"type": "api_gateway", "mandatory": True},
                {"type": "service_registry", "mandatory": True}
            ],
            "best_practices": [
                "Définir des contrats d'API clairs",
                "Implémenter le circuit breaker pattern",
                "Utiliser la découverte de service"
            ]
        }

    def _get_monolith_template(self) -> Dict[str, Any]:
        return {
            "name": "monolith",
            "description": "Architecture monolithique simple et facile à déployer",
            "use_cases": ["Petites applications", "Équipes réduites", "Prototypage rapide"],
            "components": [
                {"type": "web_server", "mandatory": True},
                {"type": "application", "mandatory": True},
                {"type": "database", "mandatory": True}
            ],
            "best_practices": [
                "Organiser le code en modules",
                "Utiliser des migrations de base de données",
                "Implémenter le caching"
            ]
        }

    def _get_serverless_template(self) -> Dict[str, Any]:
        return {
            "name": "serverless",
            "description": "Architecture serverless pour réduire les coûts d'infrastructure",
            "use_cases": ["Charge variable", "Traitement par lots", "API faible traffic"],
            "components": [
                {"type": "api_gateway", "mandatory": True},
                {"type": "functions", "mandatory": True}
            ],
            "best_practices": [
                "Garder les fonctions stateless",
                "Optimiser la taille des packages"
            ]
        }

    def _get_event_driven_template(self) -> Dict[str, Any]:
        return {
            "name": "event_driven",
            "description": "Architecture pilotée par les événements",
            "use_cases": ["Systèmes temps réel", "Flux de données", "Haute disponibilité"],
            "components": [
                {"type": "message_broker", "mandatory": True},
                {"type": "event_processors", "mandatory": True}
            ],
            "best_practices": [
                "Définir des schémas d'événements clairs",
                "Implémenter l'idempotence",
                "Utiliser le pattern outbox"
            ]
        }

    def _get_default_patterns(self) -> Dict[str, Any]:
        return {
            "microservices_patterns": [
                {"name": "API Gateway", "description": "Point d'entrée unique"},
                {"name": "Circuit Breaker", "description": "Protection contre les défaillances"},
                {"name": "Service Discovery", "description": "Découverte dynamique"}
            ],
            "data_patterns": [
                {"name": "CQRS", "description": "Séparation lecture/écriture"},
                {"name": "Event Sourcing", "description": "Stockage des événements"}
            ]
        }

    # -------------------------------------------------------------------------
    # HANDLERS DE MESSAGES
    # -------------------------------------------------------------------------

    async def _handle_design_architecture(self, message: Message) -> Message:
        requirements = message.content.get("requirements", {})
        result = await self.design_architecture(requirements)
        return Message(
            sender=self._name,
            recipient=message.sender,
            content={"design_result": result},
            message_type=MessageType.RESPONSE.value,
            correlation_id=message.message_id
        )

    async def _handle_review_design(self, message: Message) -> Message:
        design_id = message.content.get("design_id", "")
        design = self.get_design(design_id)
        return Message(
            sender=self._name,
            recipient=message.sender,
            content={"design": design, "reviewed": True},
            message_type=MessageType.RESPONSE.value,
            correlation_id=message.message_id
        )

    async def _handle_get_design(self, message: Message) -> Message:
        design_id = message.content.get("design_id", "")
        design = self.get_design(design_id)
        return Message(
            sender=self._name,
            recipient=message.sender,
            content={"design": design},
            message_type=MessageType.RESPONSE.value,
            correlation_id=message.message_id
        )

    async def _handle_validate_requirements(self, message: Message) -> Message:
        requirements = message.content.get("requirements", {})
        result = self.validate_requirements(requirements)
        return Message(
            sender=self._name,
            recipient=message.sender,
            content={"validation_result": result},
            message_type=MessageType.RESPONSE.value,
            correlation_id=message.message_id
        )

    async def _handle_split_spec(self, message: Message) -> Message:
        global_spec = message.content.get("spec", {})
        strategy = message.content.get("strategy", "largeur_dabord")
        result = await self.split_spec_into_fragments(global_spec, strategy)
        return Message(
            sender=self._name,
            recipient=message.sender,
            content={"fragments": result},
            message_type=MessageType.RESPONSE.value,
            correlation_id=message.message_id
        )

    async def _handle_record_call_result(self, message: Message) -> Message:
        service_name = message.content.get("service_name", "")
        success = message.content.get("success", False)
        error = message.content.get("error")
        result = await self.record_call_result(service_name, success, error)
        return Message(
            sender=self._name,
            recipient=message.sender,
            content={"result": result},
            message_type=MessageType.RESPONSE.value,
            correlation_id=message.message_id
        )

    async def _handle_check_service_circuit(self, message: Message) -> Message:
        service_name = message.content.get("service_name", "")
        result = await self.check_service_circuit(service_name)
        return Message(
            sender=self._name,
            recipient=message.sender,
            content={"circuit_status": result},
            message_type=MessageType.RESPONSE.value,
            correlation_id=message.message_id
        )

    async def _handle_delegate_to_domain(self, message: Message) -> Message:
        domain = message.content.get("domain", "")
        action = message.content.get("action", "")
        params = message.content.get("params", {})
        result = await self.delegate_to_domain(domain, action, params)
        return Message(
            sender=self._name,
            recipient=message.sender,
            content={"delegation_result": result},
            message_type=MessageType.RESPONSE.value,
            correlation_id=message.message_id
        )

    async def _handle_delegate_multi_domain(self, message: Message) -> Message:
        tasks = message.content.get("tasks", [])
        results = {}
        for task in tasks:
            domain = task.get("domain")
            action = task.get("action")
            params = task.get("params", {})
            if domain and action:
                results[f"{domain}_{action}"] = await self.delegate_to_domain(domain, action, params)
        return Message(
            sender=self._name,
            recipient=message.sender,
            content={"multi_delegation_results": results},
            message_type=MessageType.RESPONSE.value,
            correlation_id=message.message_id
        )

    async def _handle_resolve_conflicts(self, message: Message) -> Message:
        designs = message.content.get("designs", [])
        # Résolution simple: fusionner les designs
        merged = {}
        for design in designs:
            merged.update(design)
        return Message(
            sender=self._name,
            recipient=message.sender,
            content={"resolved": True, "merged_design": merged},
            message_type=MessageType.RESPONSE.value,
            correlation_id=message.message_id
        )

    async def _handle_create_adr(self, message: Message) -> Message:
        adr_data = message.content.get("adr_data", {})
        adr = ArchitectureDecision(**adr_data)
        self._architect_metrics["adr_generated"] += 1
        return Message(
            sender=self._name,
            recipient=message.sender,
            content={"adr": adr.to_dict()},
            message_type=MessageType.RESPONSE.value,
            correlation_id=message.message_id
        )

    async def _handle_get_metrics(self, message: Message) -> Message:
        return Message(
            sender=self._name,
            recipient=message.sender,
            content={"metrics": self.get_architect_metrics()},
            message_type=MessageType.RESPONSE.value,
            correlation_id=message.message_id
        )


# -----------------------------------------------------------------------------
# FONCTION FACTORY
# -----------------------------------------------------------------------------

def create_architect_agent(config_path: Optional[str] = None) -> ArchitectAgent:
    """Crée une instance de l'agent Architect"""
    return ArchitectAgent(config_path)


# -----------------------------------------------------------------------------
# POINT D'ENTRÉE POUR LES TESTS
# -----------------------------------------------------------------------------

async def test_architect_agent():
    """Teste l'agent Architect v4.0.0"""
    print("🧪 Test de l'agent Architect v4.0.0...")

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
                {"id": "FR1", "description": "Gestion des utilisateurs"},
                {"id": "FR2", "description": "Catalogue de produits"},
                {"id": "FR3", "description": "Panier d'achat"},
                {"id": "FR4", "description": "Système de paiement"},
                {"id": "FR5", "description": "Gestion des stocks"}
            ],
            "non_functional_requirements": {
                "performance": {"response_time": "200ms"},
                "availability": "99.99%"
            },
            "technical_constraints": {
                "programming_languages": ["Python"],
                "database_type": "postgresql"
            },
            "expected_scale": {"expected_users": 100000},
            "security_requirements": ["authentication", "encryption"],
            "disaster_recovery": {"rto": "4 hours", "rpo": "1 hour"}
        }

        result = await agent.design_architecture(requirements)

        if result["success"]:
            design_id = result["design_id"]
            print(f"  Conception créée: {design_id}")
            print(f"  Type d'architecture: {result['architecture']['architecture_type']}")

            designs = agent.list_designs()
            print(f"  Conceptions disponibles: {len(designs)}")
        else:
            print(f"  ❌ Échec de la conception: {result.get('error', 'Erreur inconnue')}")

    print(f"\n  Statut final: {agent.status}")
    await agent.shutdown()
    print(f"  Statut après arrêt: {agent.status}")

    print("\n✅ Test ArchitectAgent v4.0.0 terminé")


if __name__ == "__main__":
    asyncio.run(test_architect_agent())
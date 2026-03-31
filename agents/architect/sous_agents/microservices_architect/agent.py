"""
Microservices Architect SubAgent - Spécialiste en architecture microservices
Version: 2.0.0 (ALIGNÉ SUR CIRCUIT BREAKER)

Expert en conception d'architectures microservices, patterns de résilience,
orchestration, service discovery, et gestion des transactions distribuées.
"""

import logging
import sys
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
from enum import Enum
from dataclasses import dataclass, field

# Configuration des imports
current_dir = Path(__file__).parent.absolute()
project_root = current_dir.parent.parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from agents.sous_agents.base_subagent import BaseSubAgent
from agents.base_agent.base_agent import Message, MessageType, AgentCapability

logger = logging.getLogger(__name__)


# ============================================================================
# ÉNUMS ET CLASSES DE DONNÉES
# ============================================================================

class ServicePattern(Enum):
    """Patterns d'architecture microservices"""
    API_GATEWAY = "api_gateway"
    SERVICE_REGISTRY = "service_registry"
    CIRCUIT_BREAKER = "circuit_breaker"
    SAGA = "saga"
    CQRS = "cqrs"
    EVENT_SOURCING = "event_sourcing"
    BULKHEAD = "bulkhead"
    SIDE_CAR = "side_car"
    STRANGER_PATTERN = "stranger_pattern"


class CommunicationProtocol(Enum):
    """Protocoles de communication inter-services"""
    HTTP_REST = "http_rest"
    GRPC = "grpc"
    GRAPHQL = "graphql"
    MESSAGE_QUEUE = "message_queue"
    EVENT_BUS = "event_bus"
    WEBSOCKET = "websocket"


@dataclass
class MicroserviceSpec:
    """Spécifications d'un microservice"""
    name: str
    description: str
    responsibilities: List[str]
    dependencies: List[str] = field(default_factory=list)
    exposed_apis: List[Dict[str, Any]] = field(default_factory=list)
    database: Optional[str] = None
    database_type: str = "postgresql"
    scalability: Dict[str, Any] = field(default_factory=dict)
    patterns: List[ServicePattern] = field(default_factory=list)
    communication_protocols: List[CommunicationProtocol] = field(default_factory=list)
    data_consistency: str = "eventual"  # eventual, strong
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "responsibilities": self.responsibilities,
            "dependencies": self.dependencies,
            "exposed_apis": self.exposed_apis,
            "database": self.database,
            "database_type": self.database_type,
            "scalability": self.scalability,
            "patterns": [p.value for p in self.patterns],
            "communication_protocols": [p.value for p in self.communication_protocols],
            "data_consistency": self.data_consistency
        }


@dataclass
class ServiceMesh:
    """Configuration du service mesh"""
    enabled: bool = True
    service_discovery: str = "consul"  # consul, eureka, kubernetes
    load_balancing: str = "round_robin"
    circuit_breaker_enabled: bool = True
    retry_policy: Dict[str, Any] = field(default_factory=dict)
    timeout_seconds: int = 30
    observability: Dict[str, bool] = field(default_factory=lambda: {
        "metrics": True,
        "tracing": True,
        "logging": True
    })


@dataclass
class MicroservicesArchitecture:
    """Conception d'architecture microservices"""
    design_id: str
    name: str
    description: str
    version: str = "1.0.0"
    services: List[MicroserviceSpec] = field(default_factory=list)
    service_mesh: ServiceMesh = field(default_factory=ServiceMesh)
    api_gateway: Dict[str, Any] = field(default_factory=dict)
    event_bus: Optional[Dict[str, Any]] = None
    database_per_service: bool = True
    container_platform: str = "kubernetes"
    ci_cd_pipeline: Dict[str, Any] = field(default_factory=dict)
    monitoring: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "design_id": self.design_id,
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "services": [s.to_dict() for s in self.services],
            "service_mesh": {
                "enabled": self.service_mesh.enabled,
                "service_discovery": self.service_mesh.service_discovery,
                "load_balancing": self.service_mesh.load_balancing,
                "circuit_breaker_enabled": self.service_mesh.circuit_breaker_enabled,
                "timeout_seconds": self.service_mesh.timeout_seconds
            },
            "api_gateway": self.api_gateway,
            "event_bus": self.event_bus,
            "database_per_service": self.database_per_service,
            "container_platform": self.container_platform,
            "created_at": self.created_at.isoformat()
        }


# ============================================================================
# SOUS-AGENT PRINCIPAL
# ============================================================================

class MicroservicesArchitectSubAgent(BaseSubAgent):
    """
    Sous-agent spécialisé en architecture microservices.
    
    Expert en conception d'architectures microservices, patterns de résilience,
    service discovery, orchestration, et gestion des transactions distribuées.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialise le sous-agent Microservices Architect.
        """
        if config_path is None:
            config_path = str(current_dir / "config.yaml")
        
        # Appel au parent (BaseSubAgent)
        super().__init__(config_path)
        
        # Métadonnées
        self._subagent_display_name = "🔧 Expert Microservices Architecture"
        self._subagent_description = "Sous-agent spécialisé en conception d'architecture microservices"
        self._subagent_version = "2.0.0"
        self._subagent_category = "microservices"
        self._subagent_capabilities = [
            "microservices.design",
            "microservices.service_discovery",
            "microservices.circuit_breaker",
            "microservices.saga",
            "microservices.resilience"
        ]
        
        # État spécifique
        self._designs: Dict[str, MicroservicesArchitecture] = {}
        self._templates: Dict[str, Any] = {}
        self._patterns_library: Dict[str, Any] = {}
        
        # Patterns de résilience
        self._resilience_patterns = [
            "Circuit Breaker", "Retry", "Timeout", "Bulkhead",
            "Rate Limiter", "Fallback", "Health Check"
        ]
        
        # Métriques spécifiques
        self._microservices_metrics = {
            "designs_created": 0,
            "services_designed": 0,
            "patterns_applied": 0
        }
        
        # Configuration
        self._microservices_config = self._config.get('microservices', {}) if self._config else {}
        
        # Charger les templates
        self._load_templates()
        self._load_patterns()
        
        # Charger les capacités depuis la configuration
        self._load_capabilities_from_config()
        
        logger.info(f"✅ {self._subagent_display_name} v{self._subagent_version} initialisé")
    
    # ========================================================================
    # IMPLÉMENTATION DES MÉTHODES ABSTRACTES (BaseSubAgent)
    # ========================================================================
    
    async def _initialize_subagent_components(self) -> bool:
        """Initialise les composants spécifiques"""
        logger.info("Initialisation des composants Microservices Architect...")
        self._designs = {}
        logger.info("✅ Composants Microservices Architect initialisés")
        return True
    
    async def _initialize_components(self) -> bool:
        """
        Implémentation requise par BaseAgent.
        Délègue à _initialize_subagent_components.
        """
        return await self._initialize_subagent_components()
    
    def _get_capability_handlers(self) -> Dict[str, Any]:
        """Retourne les handlers spécifiques"""
        return {
            "microservices.design": self._handle_design,
            "microservices.service_discovery": self._handle_service_discovery,
            "microservices.circuit_breaker": self._handle_circuit_breaker,
            "microservices.saga": self._handle_saga,
            "microservices.resilience": self._handle_resilience,
        }
    
    def _load_capabilities_from_config(self):
        """Charge les capacités depuis la configuration"""
        caps = self._config.get('capabilities', [])
        for cap in caps:
            if isinstance(cap, dict):
                self.add_capability(AgentCapability(
                    name=cap.get('name', 'unknown'),
                    description=cap.get('description', ''),
                    version=cap.get('version', '1.0.0')
                ))
        if caps:
            self._logger.info(f"✅ {len(caps)} capacités chargées depuis la configuration")
    
    # ========================================================================
    # HANDLERS DE CAPACITÉS
    # ========================================================================
    
    async def _handle_design(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handler pour la conception d'architecture microservices"""
        requirements = params.get("requirements", {})
        return await self.design_microservices_architecture(requirements)
    
    async def _handle_service_discovery(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handler pour la configuration du service discovery"""
        return await self.configure_service_discovery(params)
    
    async def _handle_circuit_breaker(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handler pour la configuration du circuit breaker"""
        return await self.configure_circuit_breaker(params)
    
    async def _handle_saga(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handler pour la conception de transactions Saga"""
        requirements = params.get("requirements", {})
        return await self.design_saga_pattern(requirements)
    
    async def _handle_resilience(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handler pour la conception de la résilience"""
        return await self.design_resilience_strategy(params)
    
    # ========================================================================
    # MÉTHODES DE CHARGEMENT
    # ========================================================================
    
    def _load_templates(self):
        """Charge les templates de microservices"""
        templates_dir = current_dir / "templates"
        
        if templates_dir.exists():
            self._logger.info(f"Chargement des templates depuis {templates_dir}")
            for template_file in templates_dir.glob("*.yaml"):
                try:
                    import yaml
                    with open(template_file, 'r', encoding='utf-8') as f:
                        template = yaml.safe_load(f)
                        template_name = template_file.stem
                        self._templates[template_name] = template
                except Exception as e:
                    self._logger.error(f"Erreur chargement template {template_file}: {e}")
        else:
            self._logger.warning("Répertoire des templates non trouvé")
            self._templates = self._get_default_templates()
    
    def _load_patterns(self):
        """Charge les patterns d'architecture microservices"""
        patterns_file = current_dir / "patterns.yaml"
        
        if patterns_file.exists():
            try:
                import yaml
                with open(patterns_file, 'r', encoding='utf-8') as f:
                    self._patterns_library = yaml.safe_load(f)
                self._logger.info(f"Patterns chargés depuis {patterns_file}")
            except Exception as e:
                self._logger.error(f"Erreur chargement patterns: {e}")
                self._patterns_library = self._get_default_patterns()
        else:
            self._logger.warning("Fichier des patterns non trouvé")
            self._patterns_library = self._get_default_patterns()
    
    def _get_default_templates(self) -> Dict[str, Any]:
        """Retourne les templates par défaut"""
        return {
            "ecommerce": {
                "name": "E-commerce Microservices",
                "services": [
                    "user-service", "product-service", "order-service",
                    "payment-service", "inventory-service", "notification-service"
                ],
                "patterns": ["API Gateway", "Circuit Breaker", "SAGA"]
            },
            "banking": {
                "name": "Banking Microservices",
                "services": [
                    "account-service", "transaction-service", "customer-service",
                    "fraud-detection", "notification-service"
                ],
                "patterns": ["CQRS", "Event Sourcing", "Circuit Breaker"]
            }
        }
    
    def _get_default_patterns(self) -> Dict[str, Any]:
        """Retourne les patterns par défaut"""
        return {
            "resilience_patterns": [
                {"name": "Circuit Breaker", "description": "Protection contre les défaillances en cascade"},
                {"name": "Retry", "description": "Réessai automatique avec backoff"},
                {"name": "Timeout", "description": "Limite de temps d'exécution"},
                {"name": "Bulkhead", "description": "Isolation des ressources"},
                {"name": "Rate Limiter", "description": "Limitation du débit"}
            ],
            "communication_patterns": [
                {"name": "API Gateway", "description": "Point d'entrée unique"},
                {"name": "Service Discovery", "description": "Découverte dynamique"},
                {"name": "Event-Driven", "description": "Communication asynchrone"}
            ]
        }
    
    # ========================================================================
    # MÉTHODES PUBLIQUES PRINCIPALES
    # ========================================================================
    
    async def design_microservices_architecture(self, requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Conçoit une architecture microservices complète."""
        try:
            design_id = f"microservices_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # Créer les services
            services = self._create_services(requirements)
            
            # Configurer le service mesh
            service_mesh = ServiceMesh(
                enabled=requirements.get("service_mesh_enabled", True),
                service_discovery=requirements.get("service_discovery", "consul"),
                load_balancing=requirements.get("load_balancing", "round_robin"),
                circuit_breaker_enabled=requirements.get("circuit_breaker_enabled", True),
                timeout_seconds=requirements.get("timeout_seconds", 30)
            )
            
            # Configurer l'API Gateway
            api_gateway = {
                "type": requirements.get("api_gateway_type", "kong"),
                "rate_limiting": requirements.get("rate_limiting", True),
                "authentication": requirements.get("authentication", "jwt")
            }
            
            design = MicroservicesArchitecture(
                design_id=design_id,
                name=requirements.get("name", "Microservices Architecture"),
                description=requirements.get("description", ""),
                services=services,
                service_mesh=service_mesh,
                api_gateway=api_gateway,
                database_per_service=requirements.get("database_per_service", True),
                container_platform=requirements.get("container_platform", "kubernetes")
            )
            
            self._designs[design_id] = design
            self._microservices_metrics["designs_created"] += 1
            self._microservices_metrics["services_designed"] += len(services)
            
            return {
                "success": True,
                "design": design.to_dict(),
                "design_id": design_id,
                "services_count": len(services)
            }
            
        except Exception as e:
            logger.error(f"Erreur conception microservices: {e}")
            return {"success": False, "error": str(e)}
    
    async def configure_service_discovery(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Configure le service discovery."""
        discovery_type = config.get("type", "consul")
        
        configurations = {
            "consul": {
                "port": 8500,
                "health_check_interval": "10s",
                "deregister_critical_service_after": "30s"
            },
            "eureka": {
                "port": 8761,
                "heartbeat_interval": "30s",
                "lease_expiration": "90s"
            },
            "kubernetes": {
                "dns": "cluster.local",
                "namespace": "default"
            }
        }
        
        return {
            "success": True,
            "service_discovery": discovery_type,
            "configuration": configurations.get(discovery_type, configurations["consul"])
        }
    
    async def configure_circuit_breaker(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Configure le circuit breaker."""
        self._microservices_metrics["patterns_applied"] += 1
        
        return {
            "success": True,
            "circuit_breaker": {
                "enabled": config.get("enabled", True),
                "failure_threshold": config.get("failure_threshold", 5),
                "timeout_seconds": config.get("timeout_seconds", 30),
                "half_open_timeout": config.get("half_open_timeout", 10),
                "success_threshold": config.get("success_threshold", 2)
            }
        }
    
    async def design_saga_pattern(self, requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Conçoit un pattern Saga pour transactions distribuées."""
        saga_type = requirements.get("type", "choreography")
        
        saga_design = {
            "type": saga_type,
            "steps": requirements.get("steps", []),
            "compensation": requirements.get("compensation", []),
            "coordinator": "saga_coordinator" if saga_type == "orchestration" else None
        }
        
        return {
            "success": True,
            "saga_design": saga_design,
            "recommendations": [
                "Use idempotent operations",
                "Implement compensation logic for each step",
                "Log all saga state changes"
            ]
        }
    
    async def design_resilience_strategy(self, requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Conçoit une stratégie de résilience."""
        patterns = requirements.get("patterns", self._resilience_patterns)
        
        return {
            "success": True,
            "resilience_strategy": {
                "patterns": patterns,
                "retry_policy": {
                    "max_attempts": 3,
                    "backoff": "exponential",
                    "initial_delay_ms": 100
                },
                "timeout_default": 30,
                "bulkhead": {
                    "max_concurrent": 10,
                    "max_wait": 100
                }
            }
        }
    
    # ========================================================================
    # MÉTHODES PRIVÉES
    # ========================================================================
    
    def _create_services(self, requirements: Dict[str, Any]) -> List[MicroserviceSpec]:
        """Crée les microservices à partir des exigences."""
        services = []
        
        service_names = requirements.get("services", ["user", "order", "product"])
        
        for name in service_names:
            service = MicroserviceSpec(
                name=f"{name}-service",
                description=f"Service de gestion des {name}",
                responsibilities=[f"Gérer les {name}", f"CRUD des {name}"],
                database=f"{name}_db",
                scalability={"min_replicas": 2, "max_replicas": 10, "target_cpu": 70},
                patterns=[ServicePattern.API_GATEWAY, ServicePattern.CIRCUIT_BREAKER],
                communication_protocols=[CommunicationProtocol.HTTP_REST]
            )
            services.append(service)
        
        return services
    
    # ========================================================================
    # MÉTHODES DE RÉCUPÉRATION
    # ========================================================================
    
    def get_design(self, design_id: str) -> Optional[Dict[str, Any]]:
        """Récupère une conception d'architecture microservices"""
        design = self._designs.get(design_id)
        return design.to_dict() if design else None
    
    def list_designs(self) -> List[Dict[str, Any]]:
        """Liste toutes les conceptions disponibles"""
        return [
            {
                "design_id": design.design_id,
                "name": design.name,
                "services_count": len(design.services),
                "created_at": design.created_at.isoformat()
            }
            for design in self._designs.values()
        ]
    
    def get_metrics(self) -> Dict[str, Any]:
        """Retourne les métriques du sous-agent"""
        return {
            **self._microservices_metrics,
            "designs_count": len(self._designs),
            "resilience_patterns": self._resilience_patterns
        }
    
    # ========================================================================
    # NETTOYAGE
    # ========================================================================
    
    async def _cleanup(self):
        """Nettoie les ressources du sous-agent"""
        logger.info("Nettoyage des ressources Microservices Architect...")
        self._designs.clear()
        await super()._cleanup()


# ============================================================================
# FONCTION D'USINE
# ============================================================================

def create_microservices_architect_subagent(config_path: Optional[str] = None) -> MicroservicesArchitectSubAgent:
    """Crée une instance du sous-agent Microservices Architect"""
    return MicroservicesArchitectSubAgent(config_path)
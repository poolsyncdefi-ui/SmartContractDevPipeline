"""
Backend Architect SubAgent - Spécialiste en architecture backend
Version: 2.0.0 (ALIGNÉ SUR BLOCKCHAIN ARCHITECT)

Expert en conception d'architectures backend robustes, scalables et performantes.
Spécialisations : API REST, GraphQL, microservices, serverless, bases de données,
caching, message brokers, et patterns d'intégration.
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

class APIType(Enum):
    """Types d'API supportés"""
    REST = "rest"
    GRAPHQL = "graphql"
    GRPC = "grpc"
    WEBSOCKET = "websocket"
    WEBHOOK = "webhook"


class DatabaseType(Enum):
    """Types de bases de données supportées"""
    POSTGRESQL = "postgresql"
    MYSQL = "mysql"
    MONGODB = "mongodb"
    COUCHDB = "couchdb"
    DYNAMODB = "dynamodb"
    CASSANDRA = "cassandra"
    REDIS = "redis"
    ELASTICSEARCH = "elasticsearch"


class CacheStrategy(Enum):
    """Stratégies de cache"""
    CACHE_ASIDE = "cache_aside"
    READ_THROUGH = "read_through"
    WRITE_THROUGH = "write_through"
    WRITE_BEHIND = "write_behind"
    REFRESH_AHEAD = "refresh_ahead"


class MessageBrokerType(Enum):
    """Types de message brokers"""
    RABBITMQ = "rabbitmq"
    KAFKA = "kafka"
    REDIS_PUBSUB = "redis_pubsub"
    AWS_SQS = "aws_sqs"
    AZURE_SERVICE_BUS = "azure_service_bus"
    GOOGLE_PUBSUB = "google_pubsub"


@dataclass
class APIEndpoint:
    """Spécifications d'un endpoint API"""
    path: str
    method: str  # GET, POST, PUT, DELETE, PATCH
    description: str
    request_schema: Optional[Dict[str, Any]] = None
    response_schema: Optional[Dict[str, Any]] = None
    authentication_required: bool = True
    rate_limit_per_minute: int = 100
    timeout_seconds: int = 30
    tags: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "path": self.path,
            "method": self.method,
            "description": self.description,
            "request_schema": self.request_schema,
            "response_schema": self.response_schema,
            "authentication_required": self.authentication_required,
            "rate_limit_per_minute": self.rate_limit_per_minute,
            "timeout_seconds": self.timeout_seconds,
            "tags": self.tags
        }


@dataclass
class DatabaseSpec:
    """Spécifications d'une base de données"""
    name: str
    db_type: DatabaseType
    purpose: str
    expected_connections: int = 10
    expected_storage_gb: float = 100
    replication_enabled: bool = True
    backup_frequency: str = "daily"  # daily, hourly, weekly
    retention_days: int = 30
    indexing_strategy: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "db_type": self.db_type.value,
            "purpose": self.purpose,
            "expected_connections": self.expected_connections,
            "expected_storage_gb": self.expected_storage_gb,
            "replication_enabled": self.replication_enabled,
            "backup_frequency": self.backup_frequency,
            "retention_days": self.retention_days,
            "indexing_strategy": self.indexing_strategy
        }


@dataclass
class CacheConfig:
    """Configuration du cache"""
    strategy: CacheStrategy
    ttl_seconds: int = 300
    max_size_mb: int = 1024
    eviction_policy: str = "lru"  # lru, lfu, fifo
    distributed: bool = False
    redis_config: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "strategy": self.strategy.value,
            "ttl_seconds": self.ttl_seconds,
            "max_size_mb": self.max_size_mb,
            "eviction_policy": self.eviction_policy,
            "distributed": self.distributed,
            "redis_config": self.redis_config
        }


@dataclass
class MessageQueueSpec:
    """Spécifications d'une file de messages"""
    name: str
    broker_type: MessageBrokerType
    purpose: str
    max_retries: int = 3
    dead_letter_queue_enabled: bool = True
    message_ttl_seconds: int = 604800  # 7 jours
    consumer_count: int = 2
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "broker_type": self.broker_type.value,
            "purpose": self.purpose,
            "max_retries": self.max_retries,
            "dead_letter_queue_enabled": self.dead_letter_queue_enabled,
            "message_ttl_seconds": self.message_ttl_seconds,
            "consumer_count": self.consumer_count
        }


@dataclass
class BackendArchitecture:
    """Conception d'architecture backend complète"""
    design_id: str
    name: str
    description: str
    version: str = "1.0.0"
    api_type: APIType = APIType.REST
    endpoints: List[APIEndpoint] = field(default_factory=list)
    databases: List[DatabaseSpec] = field(default_factory=list)
    cache_config: Optional[CacheConfig] = None
    message_queues: List[MessageQueueSpec] = field(default_factory=list)
    authentication_method: str = "jwt"  # jwt, oauth2, api_key, none
    rate_limiting_enabled: bool = True
    logging_enabled: bool = True
    monitoring_enabled: bool = True
    tracing_enabled: bool = False
    containerization: str = "docker"  # docker, none
    orchestration: str = "kubernetes"  # kubernetes, docker-compose, none
    expected_requests_per_second: int = 1000
    sla_percent: float = 99.9
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "design_id": self.design_id,
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "api_type": self.api_type.value,
            "endpoints": [e.to_dict() for e in self.endpoints],
            "databases": [d.to_dict() for d in self.databases],
            "cache_config": self.cache_config.to_dict() if self.cache_config else None,
            "message_queues": [q.to_dict() for q in self.message_queues],
            "authentication_method": self.authentication_method,
            "rate_limiting_enabled": self.rate_limiting_enabled,
            "logging_enabled": self.logging_enabled,
            "monitoring_enabled": self.monitoring_enabled,
            "tracing_enabled": self.tracing_enabled,
            "containerization": self.containerization,
            "orchestration": self.orchestration,
            "expected_requests_per_second": self.expected_requests_per_second,
            "sla_percent": self.sla_percent,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }


# ============================================================================
# SOUS-AGENT PRINCIPAL
# ============================================================================

class BackendArchitectSubAgent(BaseSubAgent):
    """
    Sous-agent spécialisé en architecture backend.
    
    Expert en conception d'architectures backend robustes, scalables et performantes.
    Spécialisations : API REST, GraphQL, microservices, serverless, bases de données,
    caching, message brokers, et patterns d'intégration.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialise le sous-agent Backend Architect.
        """
        if config_path is None:
            config_path = str(current_dir / "config.yaml")
        
        # Appel au parent (BaseSubAgent)
        super().__init__(config_path)
        
        # Métadonnées
        self._subagent_display_name = "⚙️ Expert Backend Architecture"
        self._subagent_description = "Sous-agent spécialisé en conception d'architecture backend"
        self._subagent_version = "2.0.0"
        self._subagent_category = "backend"
        self._subagent_capabilities = [
            "backend.design_architecture",
            "backend.design_api",
            "backend.design_database",
            "backend.design_cache",
            "backend.design_message_queue",
            "backend.optimize_performance",
            "backend.scalability_analysis"
        ]
        
        # État spécifique
        self._designs: Dict[str, BackendArchitecture] = {}
        self._templates: Dict[str, Any] = {}
        self._patterns_library: Dict[str, Any] = {}
        
        # Patterns backend
        self._backend_patterns = [
            "Repository Pattern", "Unit of Work", "Dependency Injection",
            "CQRS", "Event Sourcing", "SAGA", "Strangler Fig",
            "Circuit Breaker", "Bulkhead", "Retry with Backoff"
        ]
        
        # Métriques spécifiques
        self._backend_metrics = {
            "designs_created": 0,
            "api_endpoints_designed": 0,
            "databases_designed": 0,
            "message_queues_designed": 0
        }
        
        # Configuration
        self._backend_config = self._config.get('backend', {}) if self._config else {}
        
        # Charger les templates
        self._load_templates()
        self._load_patterns()
        
        # =============================================================
        # CHARGER LES CAPACITÉS DEPUIS LA CONFIGURATION
        # =============================================================
        self._load_capabilities_from_config()
        
        logger.info(f"✅ {self._subagent_display_name} v{self._subagent_version} initialisé")
    
    # ========================================================================
    # IMPLÉMENTATION DES MÉTHODES ABSTRACTES (BaseSubAgent)
    # ========================================================================
    
    async def _initialize_subagent_components(self) -> bool:
        """Initialise les composants spécifiques"""
        logger.info("Initialisation des composants Backend Architect...")
        
        # Initialiser les designs
        self._designs = {}
        
        logger.info("✅ Composants Backend Architect initialisés")
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
            "backend.design_architecture": self._handle_design_architecture,
            "backend.design_api": self._handle_design_api,
            "backend.design_database": self._handle_design_database,
            "backend.design_cache": self._handle_design_cache,
            "backend.design_message_queue": self._handle_design_message_queue,
            "backend.optimize_performance": self._handle_optimize_performance,
            "backend.scalability_analysis": self._handle_scalability_analysis,
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
    
    async def _handle_design_architecture(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handler pour la conception d'architecture backend"""
        requirements = params.get("requirements", {})
        return await self.design_backend_architecture(requirements)
    
    async def _handle_design_api(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handler pour la conception d'API"""
        requirements = params.get("requirements", {})
        return await self.design_api(requirements)
    
    async def _handle_design_database(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handler pour la conception de base de données"""
        requirements = params.get("requirements", {})
        return await self.design_database(requirements)
    
    async def _handle_design_cache(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handler pour la conception de cache"""
        requirements = params.get("requirements", {})
        return await self.design_cache(requirements)
    
    async def _handle_design_message_queue(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handler pour la conception de file de messages"""
        requirements = params.get("requirements", {})
        return await self.design_message_queue(requirements)
    
    async def _handle_optimize_performance(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handler pour l'optimisation des performances"""
        current_config = params.get("current_config", {})
        return await self.optimize_performance(current_config)
    
    async def _handle_scalability_analysis(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handler pour l'analyse de scalabilité"""
        requirements = params.get("requirements", {})
        return await self.analyze_scalability(requirements)
    
    # ========================================================================
    # MÉTHODES DE CHARGEMENT
    # ========================================================================
    
    def _load_templates(self):
        """Charge les templates d'architecture backend"""
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
        """Charge les patterns d'architecture backend"""
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
            "ecommerce_backend": {
                "name": "E-commerce Backend",
                "api_type": "rest",
                "databases": [
                    {"name": "user_db", "type": "postgresql", "purpose": "User data"},
                    {"name": "product_db", "type": "postgresql", "purpose": "Product catalog"},
                    {"name": "order_db", "type": "postgresql", "purpose": "Orders"},
                    {"name": "cache", "type": "redis", "purpose": "Session & product cache"}
                ],
                "message_queues": [
                    {"name": "order_processing", "broker": "rabbitmq", "purpose": "Async order processing"}
                ]
            },
            "social_media_backend": {
                "name": "Social Media Backend",
                "api_type": "graphql",
                "databases": [
                    {"name": "user_db", "type": "postgresql", "purpose": "User profiles"},
                    {"name": "post_db", "type": "mongodb", "purpose": "Posts and comments"},
                    {"name": "feed_cache", "type": "redis", "purpose": "User feeds"}
                ],
                "message_queues": [
                    {"name": "notification_queue", "broker": "kafka", "purpose": "Notifications"},
                    {"name": "feed_generation", "broker": "kafka", "purpose": "Feed updates"}
                ]
            }
        }
    
    def _get_default_patterns(self) -> Dict[str, Any]:
        """Retourne les patterns par défaut"""
        return {
            "api_patterns": [
                {"name": "RESTful", "description": "Resource-based API design"},
                {"name": "GraphQL", "description": "Query language for APIs"},
                {"name": "gRPC", "description": "High-performance RPC framework"}
            ],
            "database_patterns": [
                {"name": "CQRS", "description": "Separate read and write models"},
                {"name": "Event Sourcing", "description": "Store state changes as events"},
                {"name": "Repository Pattern", "description": "Abstract data access"}
            ],
            "caching_patterns": [
                {"name": "Cache-Aside", "description": "Application manages cache"},
                {"name": "Read-Through", "description": "Cache manages loading"},
                {"name": "Write-Through", "description": "Write to cache and DB"}
            ]
        }
    
    # ========================================================================
    # MÉTHODES PUBLIQUES PRINCIPALES
    # ========================================================================
    
    async def design_backend_architecture(self, requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Conçoit une architecture backend complète."""
        try:
            design_id = f"backend_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # Déterminer le type d'API
            api_type_str = requirements.get("api_type", "rest")
            api_type = APIType.REST
            for at in APIType:
                if at.value == api_type_str.lower():
                    api_type = at
                    break
            
            # Créer les endpoints
            endpoints = self._create_endpoints(requirements, api_type)
            
            # Créer les bases de données
            databases = self._create_databases(requirements)
            
            # Configurer le cache
            cache_config = None
            if requirements.get("cache_enabled", True):
                cache_config = CacheConfig(
                    strategy=CacheStrategy.CACHE_ASIDE,
                    ttl_seconds=requirements.get("cache_ttl", 300),
                    distributed=requirements.get("distributed_cache", False)
                )
            
            # Créer les files de messages
            message_queues = self._create_message_queues(requirements)
            
            design = BackendArchitecture(
                design_id=design_id,
                name=requirements.get("name", "Backend Architecture"),
                description=requirements.get("description", ""),
                api_type=api_type,
                endpoints=endpoints,
                databases=databases,
                cache_config=cache_config,
                message_queues=message_queues,
                authentication_method=requirements.get("authentication", "jwt"),
                rate_limiting_enabled=requirements.get("rate_limiting", True),
                expected_requests_per_second=requirements.get("expected_rps", 1000),
                sla_percent=requirements.get("sla", 99.9)
            )
            
            self._designs[design_id] = design
            self._backend_metrics["designs_created"] += 1
            self._backend_metrics["api_endpoints_designed"] += len(endpoints)
            self._backend_metrics["databases_designed"] += len(databases)
            self._backend_metrics["message_queues_designed"] += len(message_queues)
            
            return {
                "success": True,
                "design": design.to_dict(),
                "design_id": design_id,
                "summary": {
                    "endpoints_count": len(endpoints),
                    "databases_count": len(databases),
                    "message_queues_count": len(message_queues),
                    "cache_enabled": cache_config is not None
                }
            }
            
        except Exception as e:
            logger.error(f"Erreur conception backend: {e}")
            return {"success": False, "error": str(e)}
    
    async def design_api(self, requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Conçoit une API spécifique."""
        try:
            api_type_str = requirements.get("api_type", "rest")
            api_type = APIType.REST
            for at in APIType:
                if at.value == api_type_str.lower():
                    api_type = at
                    break
            
            endpoints = self._create_endpoints(requirements, api_type)
            
            recommendations = []
            if api_type == APIType.REST:
                recommendations = [
                    "Use resource naming conventions (plural nouns)",
                    "Implement proper HTTP status codes",
                    "Add pagination for list endpoints",
                    "Use versioning in URL (/api/v1/)"
                ]
            elif api_type == APIType.GRAPHQL:
                recommendations = [
                    "Design schema-first approach",
                    "Implement DataLoader for N+1 problem",
                    "Add query complexity analysis",
                    "Use persisted queries for production"
                ]
            elif api_type == APIType.GRPC:
                recommendations = [
                    "Define proto files with clear contracts",
                    "Implement interceptors for auth/logging",
                    "Use load balancing with gRPC",
                    "Enable reflection for debugging"
                ]
            
            return {
                "success": True,
                "api_design": {
                    "type": api_type.value,
                    "endpoints": [e.to_dict() for e in endpoints],
                    "recommendations": recommendations
                }
            }
            
        except Exception as e:
            logger.error(f"Erreur conception API: {e}")
            return {"success": False, "error": str(e)}
    
    async def design_database(self, requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Conçoit une base de données spécifique."""
        try:
            db_type_str = requirements.get("db_type", "postgresql")
            db_type = DatabaseType.POSTGRESQL
            for dt in DatabaseType:
                if dt.value == db_type_str.lower():
                    db_type = dt
                    break
            
            db_spec = DatabaseSpec(
                name=requirements.get("name", "main_db"),
                db_type=db_type,
                purpose=requirements.get("purpose", "Main application data"),
                expected_connections=requirements.get("expected_connections", 10),
                expected_storage_gb=requirements.get("expected_storage_gb", 100),
                replication_enabled=requirements.get("replication", True),
                backup_frequency=requirements.get("backup_frequency", "daily"),
                retention_days=requirements.get("retention_days", 30),
                indexing_strategy=requirements.get("indexing_strategy", [])
            )
            
            # Recommandations spécifiques au type de base de données
            recommendations = []
            if db_type == DatabaseType.POSTGRESQL:
                recommendations = [
                    "Use connection pooling (pgBouncer)",
                    "Implement read replicas for queries",
                    "Use partitioning for large tables",
                    "Regular VACUUM and ANALYZE"
                ]
            elif db_type == DatabaseType.MONGODB:
                recommendations = [
                    "Design schema based on query patterns",
                    "Use sharding for horizontal scaling",
                    "Implement proper indexing strategy",
                    "Use aggregation pipelines for complex queries"
                ]
            elif db_type == DatabaseType.REDIS:
                recommendations = [
                    "Use appropriate data structures",
                    "Implement key expiration policies",
                    "Use Redis Cluster for high availability",
                    "Monitor memory usage"
                ]
            
            return {
                "success": True,
                "database": db_spec.to_dict(),
                "recommendations": recommendations
            }
            
        except Exception as e:
            logger.error(f"Erreur conception base de données: {e}")
            return {"success": False, "error": str(e)}
    
    async def design_cache(self, requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Conçoit une stratégie de cache."""
        try:
            strategy_str = requirements.get("strategy", "cache_aside")
            strategy = CacheStrategy.CACHE_ASIDE
            for cs in CacheStrategy:
                if cs.value == strategy_str.lower():
                    strategy = cs
                    break
            
            cache_config = CacheConfig(
                strategy=strategy,
                ttl_seconds=requirements.get("ttl_seconds", 300),
                max_size_mb=requirements.get("max_size_mb", 1024),
                eviction_policy=requirements.get("eviction_policy", "lru"),
                distributed=requirements.get("distributed", False),
                redis_config=requirements.get("redis_config")
            )
            
            # Recommandations par stratégie
            recommendations = {
                CacheStrategy.CACHE_ASIDE: [
                    "Handle cache misses by loading from database",
                    "Implement cache invalidation on updates",
                    "Use consistent hashing for distributed cache"
                ],
                CacheStrategy.READ_THROUGH: [
                    "Cache library handles loading automatically",
                    "Configure cache loader functions",
                    "Monitor cache hit rates"
                ],
                CacheStrategy.WRITE_THROUGH: [
                    "Write to cache and database synchronously",
                    "Use for write-heavy workloads",
                    "Consider performance impact"
                ]
            }
            
            return {
                "success": True,
                "cache_config": cache_config.to_dict(),
                "recommendations": recommendations.get(strategy, [])
            }
            
        except Exception as e:
            logger.error(f"Erreur conception cache: {e}")
            return {"success": False, "error": str(e)}
    
    async def design_message_queue(self, requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Conçoit une file de messages."""
        try:
            broker_str = requirements.get("broker_type", "rabbitmq")
            broker_type = MessageBrokerType.RABBITMQ
            for bt in MessageBrokerType:
                if bt.value == broker_str.lower():
                    broker_type = bt
                    break
            
            queue_spec = MessageQueueSpec(
                name=requirements.get("name", "default_queue"),
                broker_type=broker_type,
                purpose=requirements.get("purpose", "Async task processing"),
                max_retries=requirements.get("max_retries", 3),
                dead_letter_queue_enabled=requirements.get("dead_letter_queue", True),
                message_ttl_seconds=requirements.get("message_ttl_seconds", 604800),
                consumer_count=requirements.get("consumer_count", 2)
            )
            
            # Recommandations par broker
            recommendations = {
                MessageBrokerType.RABBITMQ: [
                    "Use exchanges for routing (direct, topic, fanout)",
                    "Implement consumer acknowledgments",
                    "Monitor queue length and consumer lag"
                ],
                MessageBrokerType.KAFKA: [
                    "Configure appropriate partition count",
                    "Set retention policy based on use case",
                    "Use consumer groups for parallel processing"
                ]
            }
            
            return {
                "success": True,
                "message_queue": queue_spec.to_dict(),
                "recommendations": recommendations.get(broker_type, [
                    "Implement dead letter queue for failed messages",
                    "Add monitoring and alerting",
                    "Use idempotent consumers"
                ])
            }
            
        except Exception as e:
            logger.error(f"Erreur conception message queue: {e}")
            return {"success": False, "error": str(e)}
    
    async def optimize_performance(self, current_config: Dict[str, Any]) -> Dict[str, Any]:
        """Optimise les performances du backend."""
        try:
            optimizations = []
            estimated_improvements = {}
            
            # Vérifier la mise en cache
            if not current_config.get("cache_enabled", False):
                optimizations.append({
                    "area": "caching",
                    "suggestion": "Implement Redis cache for frequent queries",
                    "estimated_improvement": "40-60% latency reduction"
                })
                estimated_improvements["latency_reduction"] = 50
            
            # Vérifier l'indexation des bases de données
            if not current_config.get("indexing_complete", False):
                optimizations.append({
                    "area": "database",
                    "suggestion": "Add proper indexes on frequently queried columns",
                    "estimated_improvement": "70-90% query time reduction"
                })
            
            # Vérifier les requêtes N+1
            if current_config.get("has_n_plus_one", False):
                optimizations.append({
                    "area": "database",
                    "suggestion": "Use eager loading to prevent N+1 queries",
                    "estimated_improvement": "50-80% response time improvement"
                })
            
            # Vérifier la compression
            if not current_config.get("compression_enabled", False):
                optimizations.append({
                    "area": "network",
                    "suggestion": "Enable gzip/brotli compression for API responses",
                    "estimated_improvement": "60-80% bandwidth reduction"
                })
            
            # Vérifier la pagination
            if current_config.get("unbounded_queries", False):
                optimizations.append({
                    "area": "api",
                    "suggestion": "Implement pagination for list endpoints",
                    "estimated_improvement": "Prevents timeouts and memory issues"
                })
            
            return {
                "success": True,
                "optimizations": optimizations,
                "estimated_improvements": estimated_improvements,
                "summary": f"{len(optimizations)} optimizations identified"
            }
            
        except Exception as e:
            logger.error(f"Erreur optimisation performance: {e}")
            return {"success": False, "error": str(e)}
    
    async def analyze_scalability(self, requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Analyse la scalabilité du backend."""
        try:
            current_rps = requirements.get("current_rps", 100)
            target_rps = requirements.get("target_rps", 1000)
            current_instances = requirements.get("current_instances", 1)
            
            # Calculer les besoins
            instances_needed = (target_rps / current_rps) * current_instances
            horizontal_scale_needed = instances_needed > current_instances * 1.5
            
            # Vérifier les goulots d'étranglement
            bottlenecks = []
            if requirements.get("database_single_instance", False):
                bottlenecks.append({
                    "component": "Database",
                    "issue": "Single instance cannot handle high concurrency",
                    "solution": "Implement read replicas or database sharding"
                })
            
            if requirements.get("monolithic_architecture", False):
                bottlenecks.append({
                    "component": "Application",
                    "issue": "Monolith cannot scale individual components",
                    "solution": "Migrate to microservices for critical paths"
                })
            
            if not requirements.get("cache_enabled", False):
                bottlenecks.append({
                    "component": "Data Access",
                    "issue": "High database load under increased traffic",
                    "solution": "Implement caching layer (Redis)"
                })
            
            recommendations = []
            if horizontal_scale_needed:
                recommendations.append(
                    f"Scale horizontally to {max(2, int(instances_needed))} instances"
                )
            
            if bottlenecks:
                recommendations.append("Address identified bottlenecks before scaling")
            
            return {
                "success": True,
                "scalability_analysis": {
                    "current_capacity_rps": current_rps,
                    "target_capacity_rps": target_rps,
                    "instances_needed": max(1, int(instances_needed)),
                    "horizontal_scaling_required": horizontal_scale_needed,
                    "bottlenecks": bottlenecks,
                    "recommendations": recommendations,
                    "scalability_score": self._calculate_scalability_score(requirements)
                }
            }
            
        except Exception as e:
            logger.error(f"Erreur analyse scalabilité: {e}")
            return {"success": False, "error": str(e)}
    
    # ========================================================================
    # MÉTHODES PRIVÉES
    # ========================================================================
    
    def _create_endpoints(self, requirements: Dict[str, Any], 
                          api_type: APIType) -> List[APIEndpoint]:
        """Crée les endpoints API selon les exigences."""
        endpoints = []
        
        if api_type == APIType.REST:
            # Endpoints CRUD par défaut
            resources = requirements.get("resources", ["users", "products", "orders"])
            for resource in resources:
                endpoints.append(APIEndpoint(
                    path=f"/api/v1/{resource}",
                    method="GET",
                    description=f"List {resource}",
                    rate_limit_per_minute=1000
                ))
                endpoints.append(APIEndpoint(
                    path=f"/api/v1/{resource}/{{id}}",
                    method="GET",
                    description=f"Get {resource} by ID",
                    rate_limit_per_minute=1000
                ))
                endpoints.append(APIEndpoint(
                    path=f"/api/v1/{resource}",
                    method="POST",
                    description=f"Create {resource}",
                    rate_limit_per_minute=100
                ))
                endpoints.append(APIEndpoint(
                    path=f"/api/v1/{resource}/{{id}}",
                    method="PUT",
                    description=f"Update {resource}",
                    rate_limit_per_minute=100
                ))
                endpoints.append(APIEndpoint(
                    path=f"/api/v1/{resource}/{{id}}",
                    method="DELETE",
                    description=f"Delete {resource}",
                    rate_limit_per_minute=50
                ))
        
        elif api_type == APIType.GRAPHQL:
            endpoints.append(APIEndpoint(
                path="/graphql",
                method="POST",
                description="GraphQL endpoint",
                rate_limit_per_minute=500
            ))
        
        elif api_type == APIType.GRPC:
            endpoints.append(APIEndpoint(
                path="service.proto",
                method="gRPC",
                description="gRPC service definition",
                rate_limit_per_minute=5000
            ))
        
        return endpoints
    
    def _create_databases(self, requirements: Dict[str, Any]) -> List[DatabaseSpec]:
        """Crée les bases de données selon les exigences."""
        databases = []
        
        # Base de données principale
        databases.append(DatabaseSpec(
            name="primary_db",
            db_type=DatabaseType.POSTGRESQL,
            purpose="Main application data",
            expected_connections=requirements.get("expected_connections", 20),
            expected_storage_gb=requirements.get("expected_storage_gb", 100)
        ))
        
        # Cache Redis si requis
        if requirements.get("cache_enabled", True):
            databases.append(DatabaseSpec(
                name="cache",
                db_type=DatabaseType.REDIS,
                purpose="Application cache",
                expected_connections=100,
                expected_storage_gb=10,
                replication_enabled=False
            ))
        
        # Base de données de recherche si requis
        if requirements.get("search_enabled", False):
            databases.append(DatabaseSpec(
                name="search_db",
                db_type=DatabaseType.ELASTICSEARCH,
                purpose="Search and analytics",
                expected_connections=10,
                expected_storage_gb=200
            ))
        
        return databases
    
    def _create_message_queues(self, requirements: Dict[str, Any]) -> List[MessageQueueSpec]:
        """Crée les files de messages selon les exigences."""
        queues = []
        
        if requirements.get("async_processing", False):
            queues.append(MessageQueueSpec(
                name="async_tasks",
                broker_type=MessageBrokerType.RABBITMQ,
                purpose="Async task processing",
                max_retries=3
            ))
        
        if requirements.get("event_driven", False):
            queues.append(MessageQueueSpec(
                name="events",
                broker_type=MessageBrokerType.KAFKA,
                purpose="Event streaming",
                max_retries=5
            ))
        
        if requirements.get("notifications", False):
            queues.append(MessageQueueSpec(
                name="notifications",
                broker_type=MessageBrokerType.RABBITMQ,
                purpose="Notification delivery",
                max_retries=5
            ))
        
        return queues
    
    def _calculate_scalability_score(self, requirements: Dict[str, Any]) -> int:
        """Calcule un score de scalabilité."""
        score = 100
        
        if requirements.get("database_single_instance", False):
            score -= 20
        if requirements.get("monolithic_architecture", False):
            score -= 15
        if not requirements.get("cache_enabled", False):
            score -= 15
        if not requirements.get("horizontal_scaling_possible", False):
            score -= 20
        if requirements.get("stateful_services", False):
            score -= 10
        
        return max(0, score)
    
    # ========================================================================
    # MÉTHODES DE RÉCUPÉRATION
    # ========================================================================
    
    def get_design(self, design_id: str) -> Optional[Dict[str, Any]]:
        """Récupère une conception d'architecture backend"""
        design = self._designs.get(design_id)
        return design.to_dict() if design else None
    
    def list_designs(self) -> List[Dict[str, Any]]:
        """Liste toutes les conceptions disponibles"""
        return [
            {
                "design_id": design.design_id,
                "name": design.name,
                "api_type": design.api_type.value,
                "endpoints_count": len(design.endpoints),
                "databases_count": len(design.databases),
                "created_at": design.created_at.isoformat()
            }
            for design in self._designs.values()
        ]
    
    def get_metrics(self) -> Dict[str, Any]:
        """Retourne les métriques du sous-agent"""
        return {
            **self._backend_metrics,
            "designs_count": len(self._designs),
            "backend_patterns": self._backend_patterns
        }
    
    # ========================================================================
    # NETTOYAGE
    # ========================================================================
    
    async def _cleanup(self):
        """Nettoie les ressources du sous-agent"""
        logger.info("Nettoyage des ressources Backend Architect...")
        self._designs.clear()
        await super()._cleanup()


# ============================================================================
# FONCTION D'USINE
# ============================================================================

def create_backend_architect_subagent(config_path: Optional[str] = None) -> BackendArchitectSubAgent:
    """Crée une instance du sous-agent Backend Architect"""
    return BackendArchitectSubAgent(config_path)
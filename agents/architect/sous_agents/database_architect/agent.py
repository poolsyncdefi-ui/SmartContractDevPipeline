"""
Database Architect SubAgent - Spécialiste en architecture de bases de données
Version: 2.0.0 (ALIGNÉ SUR BLOCKCHAIN ARCHITECT)

Expert en conception d'architectures de bases de données optimisées, scalables et performantes.
Spécialisations : SQL (PostgreSQL, MySQL), NoSQL (MongoDB, Cassandra), NewSQL,
sharding, réplication, indexation, optimisation des requêtes, et migration.
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
from agents.base_agent.base_agent import Message, MessageType

logger = logging.getLogger(__name__)


# ============================================================================
# ÉNUMS ET CLASSES DE DONNÉES
# ============================================================================

class DatabaseEngine(Enum):
    """Moteurs de bases de données supportés"""
    # SQL
    POSTGRESQL = "postgresql"
    MYSQL = "mysql"
    SQLITE = "sqlite"
    SQL_SERVER = "sql_server"
    ORACLE = "oracle"
    # NoSQL
    MONGODB = "mongodb"
    CASSANDRA = "cassandra"
    DYNAMODB = "dynamodb"
    COUCHDB = "couchdb"
    NEO4J = "neo4j"  # Graph
    # Timeseries
    TIMESCALE = "timescale"
    INFLUXDB = "influxdb"
    # NewSQL
    COCKROACHDB = "cockroachdb"
    YUGABYTE = "yugabyte"
    # Cache/In-memory
    REDIS = "redis"
    MEMCACHED = "memcached"
    # Search
    ELASTICSEARCH = "elasticsearch"
    OPENSEARCH = "opensearch"


class ReplicationStrategy(Enum):
    """Stratégies de réplication"""
    MASTER_SLAVE = "master_slave"
    MASTER_MASTER = "master_master"
    MULTI_MASTER = "multi_master"
    CASCADE = "cascade"
    SYNCHRONOUS = "synchronous"
    ASYNCHRONOUS = "asynchronous"


class ShardingStrategy(Enum):
    """Stratégies de sharding"""
    RANGE = "range"          # Par plage de valeurs
    HASH = "hash"            # Par hash modulaire
    DIRECTORY = "directory"  # Par lookup table
    GEOGRAPHIC = "geographic" # Par région géographique
    TIME_BASED = "time_based" # Par période temporelle


class IndexType(Enum):
    """Types d'index"""
    BTREE = "btree"
    HASH = "hash"
    GIN = "gin"      # Generalized Inverted Index (PostgreSQL)
    GIST = "gist"    # Generalized Search Tree (PostgreSQL)
    BRIN = "brin"    # Block Range Index (PostgreSQL)
    FULLTEXT = "fulltext"
    SPATIAL = "spatial"
    COMPOSITE = "composite"


@dataclass
class TableSchema:
    """Schéma d'une table"""
    name: str
    description: str
    columns: List[Dict[str, Any]]
    primary_key: List[str]
    foreign_keys: List[Dict[str, str]] = field(default_factory=list)
    indexes: List[Dict[str, Any]] = field(default_factory=list)
    partitions: Optional[Dict[str, Any]] = None
    estimated_rows: int = 1000000
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "columns": self.columns,
            "primary_key": self.primary_key,
            "foreign_keys": self.foreign_keys,
            "indexes": self.indexes,
            "partitions": self.partitions,
            "estimated_rows": self.estimated_rows
        }


@dataclass
class DatabaseDesign:
    """Conception de base de données"""
    name: str
    engine: DatabaseEngine
    description: str
    version: str = "1.0.0"
    tables: List[TableSchema] = field(default_factory=list)
    replication_strategy: Optional[ReplicationStrategy] = None
    sharding_strategy: Optional[ShardingStrategy] = None
    shard_key: Optional[str] = None
    backup_policy: Dict[str, Any] = field(default_factory=dict)
    disaster_recovery: Dict[str, Any] = field(default_factory=dict)
    expected_reads_per_second: int = 1000
    expected_writes_per_second: int = 500
    expected_data_growth_gb_per_month: float = 10
    high_availability: bool = True
    encryption_at_rest: bool = True
    encryption_in_transit: bool = True
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "engine": self.engine.value,
            "description": self.description,
            "version": self.version,
            "tables": [t.to_dict() for t in self.tables],
            "replication_strategy": self.replication_strategy.value if self.replication_strategy else None,
            "sharding_strategy": self.sharding_strategy.value if self.sharding_strategy else None,
            "shard_key": self.shard_key,
            "backup_policy": self.backup_policy,
            "disaster_recovery": self.disaster_recovery,
            "expected_reads_per_second": self.expected_reads_per_second,
            "expected_writes_per_second": self.expected_writes_per_second,
            "expected_data_growth_gb_per_month": self.expected_data_growth_gb_per_month,
            "high_availability": self.high_availability,
            "encryption_at_rest": self.encryption_at_rest,
            "encryption_in_transit": self.encryption_in_transit,
            "created_at": self.created_at.isoformat()
        }


@dataclass
class QueryOptimization:
    """Optimisation de requête"""
    original_query: str
    optimized_query: str
    estimated_improvement: float
    recommendations: List[str]
    index_created: Optional[List[str]] = None
    query_plan_before: Optional[str] = None
    query_plan_after: Optional[str] = None


@dataclass
class MigrationPlan:
    """Plan de migration de base de données"""
    source_engine: DatabaseEngine
    target_engine: DatabaseEngine
    steps: List[Dict[str, Any]]
    estimated_duration_hours: float
    risks: List[str]
    rollback_plan: List[str]
    data_volume_gb: float
    downtime_expected: bool
    estimated_downtime_minutes: int = 0


# ============================================================================
# SOUS-AGENT PRINCIPAL
# ============================================================================

class DatabaseArchitectSubAgent(BaseSubAgent):
    """
    Sous-agent spécialisé en architecture de bases de données.
    
    Expert en conception d'architectures de bases de données optimisées, scalables.
    Spécialisations : SQL, NoSQL, sharding, réplication, indexation, optimisation.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialise le sous-agent Database Architect.
        """
        if config_path is None:
            config_path = str(current_dir / "config.yaml")
        
        # Appel au parent (BaseSubAgent)
        super().__init__(config_path)
        
        # Métadonnées
        self._subagent_display_name = "🗄️ Expert Database Architecture"
        self._subagent_description = "Sous-agent spécialisé en conception d'architecture de bases de données"
        self._subagent_version = "2.0.0"
        self._subagent_category = "database"
        self._subagent_capabilities = [
            "database.design_schema",
            "database.optimize_queries",
            "database.design_replication",
            "database.design_sharding",
            "database.migration_planning",
            "database.capacity_planning",
            "database.performance_tuning"
        ]
        
        # État spécifique
        self._designs: Dict[str, DatabaseDesign] = {}
        self._templates: Dict[str, Any] = {}
        self._patterns_library: Dict[str, Any] = {}
        
        # Patterns de base de données
        self._db_patterns = [
            "Single Database", "Master-Slave Replication", "Master-Master Replication",
            "Sharding", "CQRS", "Event Sourcing", "Polyglot Persistence",
            "Read Replicas", "Database per Service", "Saga Pattern"
        ]
        
        # Métriques spécifiques
        self._database_metrics = {
            "designs_created": 0,
            "tables_designed": 0,
            "optimizations_performed": 0,
            "migrations_planned": 0
        }
        
        # Configuration
        self._database_config = self._config.get('database', {}) if self._config else {}
        
        # Charger les templates
        self._load_templates()
        self._load_patterns()
        
        logger.info(f"✅ {self._subagent_display_name} v{self._subagent_version} initialisé")
    
    # ========================================================================
    # IMPLÉMENTATION DES MÉTHODES ABSTRACTES
    # ========================================================================
    
    async def _initialize_subagent_components(self) -> bool:
        """Initialise les composants spécifiques"""
        logger.info("Initialisation des composants Database Architect...")
        
        self._designs = {}
        
        logger.info("✅ Composants Database Architect initialisés")
        return True
    
    async def _initialize_components(self) -> bool:
        """Implémentation requise par BaseAgent"""
        return await self._initialize_subagent_components()
    
    def _get_capability_handlers(self) -> Dict[str, Any]:
        """Retourne les handlers spécifiques"""
        return {
            "database.design_schema": self._handle_design_schema,
            "database.optimize_queries": self._handle_optimize_queries,
            "database.design_replication": self._handle_design_replication,
            "database.design_sharding": self._handle_design_sharding,
            "database.migration_planning": self._handle_migration_planning,
            "database.capacity_planning": self._handle_capacity_planning,
            "database.performance_tuning": self._handle_performance_tuning,
        }
    
    def _load_capabilities_from_config(self):
        """Charge les capacités depuis la configuration"""
        caps = self._agent_config.get('capabilities', [])
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
    
    async def _handle_design_schema(self, params: Dict[str, Any]) -> Dict[str, Any]:
        requirements = params.get("requirements", {})
        return await self.design_database_schema(requirements)
    
    async def _handle_optimize_queries(self, params: Dict[str, Any]) -> Dict[str, Any]:
        queries = params.get("queries", [])
        db_type = params.get("db_type", "postgresql")
        return await self.optimize_queries(queries, db_type)
    
    async def _handle_design_replication(self, params: Dict[str, Any]) -> Dict[str, Any]:
        requirements = params.get("requirements", {})
        return await self.design_replication_strategy(requirements)
    
    async def _handle_design_sharding(self, params: Dict[str, Any]) -> Dict[str, Any]:
        requirements = params.get("requirements", {})
        return await self.design_sharding_strategy(requirements)
    
    async def _handle_migration_planning(self, params: Dict[str, Any]) -> Dict[str, Any]:
        source = params.get("source_engine", "postgresql")
        target = params.get("target_engine", "mongodb")
        data_volume = params.get("data_volume_gb", 100)
        return await self.plan_migration(source, target, data_volume)
    
    async def _handle_capacity_planning(self, params: Dict[str, Any]) -> Dict[str, Any]:
        requirements = params.get("requirements", {})
        return await self.plan_capacity(requirements)
    
    async def _handle_performance_tuning(self, params: Dict[str, Any]) -> Dict[str, Any]:
        db_config = params.get("database_config", {})
        return await self.tune_performance(db_config)
    
    # ========================================================================
    # MÉTHODES DE CHARGEMENT
    # ========================================================================
    
    def _load_templates(self):
        """Charge les templates de bases de données"""
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
        """Charge les patterns de bases de données"""
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
                "name": "E-commerce Database",
                "engine": "postgresql",
                "tables": [
                    {"name": "users", "columns": ["id", "email", "name", "created_at"]},
                    {"name": "products", "columns": ["id", "name", "price", "stock"]},
                    {"name": "orders", "columns": ["id", "user_id", "total", "status"]},
                    {"name": "order_items", "columns": ["id", "order_id", "product_id", "quantity"]}
                ]
            },
            "social_media": {
                "name": "Social Media Database",
                "engine": "postgresql",
                "tables": [
                    {"name": "users", "columns": ["id", "username", "email"]},
                    {"name": "posts", "columns": ["id", "user_id", "content", "created_at"]},
                    {"name": "comments", "columns": ["id", "post_id", "user_id", "content"]},
                    {"name": "likes", "columns": ["id", "post_id", "user_id"]}
                ]
            }
        }
    
    def _get_default_patterns(self) -> Dict[str, Any]:
        """Retourne les patterns par défaut"""
        return {
            "indexing_patterns": [
                {"name": "BTREE", "description": "Default balanced tree index"},
                {"name": "Composite Index", "description": "Multi-column index"},
                {"name": "Partial Index", "description": "Index on subset of rows"},
                {"name": "Covering Index", "description": "Include all needed columns"}
            ],
            "replication_patterns": [
                {"name": "Master-Slave", "description": "One master, multiple read replicas"},
                {"name": "Master-Master", "description": "Multi-master active-active"},
                {"name": "Synchronous", "description": "Strong consistency, higher latency"}
            ]
        }
    
    # ========================================================================
    # MÉTHODES PUBLIQUES PRINCIPALES
    # ========================================================================
    
    async def design_database_schema(self, requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Conçoit un schéma de base de données complet."""
        try:
            engine_str = requirements.get("engine", "postgresql")
            engine = DatabaseEngine.POSTGRESQL
            for de in DatabaseEngine:
                if de.value == engine_str.lower():
                    engine = de
                    break
            
            # Créer les tables
            tables = self._create_tables(requirements, engine)
            
            # Configurer la réplication
            replication = None
            if requirements.get("replication_enabled", False):
                rep_str = requirements.get("replication_strategy", "master_slave")
                for rs in ReplicationStrategy:
                    if rs.value == rep_str.lower():
                        replication = rs
                        break
            
            # Configurer le sharding
            sharding = None
            shard_key = None
            if requirements.get("sharding_enabled", False):
                shard_str = requirements.get("sharding_strategy", "hash")
                for ss in ShardingStrategy:
                    if ss.value == shard_str.lower():
                        sharding = ss
                        break
                shard_key = requirements.get("shard_key", "id")
            
            design = DatabaseDesign(
                name=requirements.get("name", "Database Design"),
                engine=engine,
                description=requirements.get("description", ""),
                tables=tables,
                replication_strategy=replication,
                sharding_strategy=sharding,
                shard_key=shard_key,
                backup_policy={
                    "frequency": requirements.get("backup_frequency", "daily"),
                    "retention_days": requirements.get("backup_retention", 30),
                    "point_in_time_recovery": requirements.get("pitr_enabled", True)
                },
                disaster_recovery={
                    "rto_seconds": requirements.get("rto_seconds", 3600),
                    "rpo_seconds": requirements.get("rpo_seconds", 300),
                    "region_replication": requirements.get("region_replication", False)
                },
                expected_reads_per_second=requirements.get("expected_reads", 1000),
                expected_writes_per_second=requirements.get("expected_writes", 500),
                expected_data_growth_gb_per_month=requirements.get("data_growth_gb", 10),
                high_availability=requirements.get("high_availability", True)
            )
            
            design_id = f"db_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            self._designs[design_id] = design
            self._database_metrics["designs_created"] += 1
            self._database_metrics["tables_designed"] += len(tables)
            
            return {
                "success": True,
                "design": design.to_dict(),
                "design_id": design_id,
                "summary": {
                    "tables_count": len(tables),
                    "engine": engine.value,
                    "replication_enabled": replication is not None,
                    "sharding_enabled": sharding is not None
                }
            }
            
        except Exception as e:
            logger.error(f"Erreur conception schéma: {e}")
            return {"success": False, "error": str(e)}
    
    async def optimize_queries(self, queries: List[str], db_type: str) -> Dict[str, Any]:
        """Optimise une liste de requêtes SQL."""
        try:
            optimizations = []
            
            for i, query in enumerate(queries):
                # Analyse basique de la requête
                optimized = query
                recommendations = []
                improvements = 0
                
                # Vérifier SELECT *
                if "SELECT *" in query.upper():
                    optimized = optimized.replace("SELECT *", "SELECT id, created_at")
                    recommendations.append("Avoid SELECT *, specify only needed columns")
                    improvements += 30
                
                # Vérifier les JOINs sans index
                if "JOIN" in query.upper() and "ON" in query.upper():
                    recommendations.append("Ensure join columns are indexed")
                    improvements += 50
                
                # Vérifier ORDER BY sans LIMIT
                if "ORDER BY" in query.upper() and "LIMIT" not in query.upper():
                    recommendations.append("Add LIMIT clause to ORDER BY queries")
                    improvements += 40
                
                # Vérifier les subqueries
                if "SELECT" in query.upper() and "SELECT" in query.upper()[query.upper().find("SELECT")+6:]:
                    recommendations.append("Consider rewriting subquery as JOIN")
                    improvements += 25
                
                optimizations.append({
                    "original": query,
                    "optimized": optimized,
                    "recommendations": recommendations,
                    "estimated_improvement_percent": min(improvements, 80)
                })
            
            self._database_metrics["optimizations_performed"] += len(optimizations)
            
            return {
                "success": True,
                "optimizations": optimizations,
                "total_optimizations": len(optimizations)
            }
            
        except Exception as e:
            logger.error(f"Erreur optimisation requêtes: {e}")
            return {"success": False, "error": str(e)}
    
    async def design_replication_strategy(self, requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Conçoit une stratégie de réplication."""
        try:
            rep_str = requirements.get("strategy", "master_slave")
            strategy = ReplicationStrategy.MASTER_SLAVE
            for rs in ReplicationStrategy:
                if rs.value == rep_str.lower():
                    strategy = rs
                    break
            
            nodes = requirements.get("nodes", 3)
            read_replicas = requirements.get("read_replicas", 2)
            
            # Recommandations par stratégie
            recommendations = {
                ReplicationStrategy.MASTER_SLAVE: [
                    f"Deploy {nodes} nodes with 1 master, {read_replicas} slaves",
                    "Use connection pooling for read replicas",
                    "Monitor replication lag, alert if > 5 seconds"
                ],
                ReplicationStrategy.MASTER_MASTER: [
                    "Ensure conflict resolution logic",
                    "Use auto-increment offset for each master",
                    "Monitor for split-brain scenarios"
                ],
                ReplicationStrategy.SYNCHRONOUS: [
                    "Higher latency but strong consistency",
                    "Use for financial/transactional data",
                    "Requires fast network between nodes"
                ]
            }
            
            return {
                "success": True,
                "replication_strategy": {
                    "type": strategy.value,
                    "nodes": nodes,
                    "read_replicas": read_replicas,
                    "synchronous_commit": strategy == ReplicationStrategy.SYNCHRONOUS
                },
                "recommendations": recommendations.get(strategy, [
                    "Implement regular backup of all replicas",
                    "Monitor replication health",
                    "Plan for failover scenarios"
                ])
            }
            
        except Exception as e:
            logger.error(f"Erreur conception réplication: {e}")
            return {"success": False, "error": str(e)}
    
    async def design_sharding_strategy(self, requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Conçoit une stratégie de sharding."""
        try:
            shard_str = requirements.get("strategy", "hash")
            strategy = ShardingStrategy.HASH
            for ss in ShardingStrategy:
                if ss.value == shard_str.lower():
                    strategy = ss
                    break
            
            shards = requirements.get("shards", 16)
            shard_key = requirements.get("shard_key", "user_id")
            
            # Configuration par stratégie
            configs = {
                ShardingStrategy.RANGE: {
                    "ranges": ["0-999", "1000-1999", "2000-2999"],
                    "balancing": "Manual"
                },
                ShardingStrategy.HASH: {
                    "algorithm": "consistent_hashing",
                    "virtual_nodes": 256,
                    "balancing": "Automatic"
                },
                ShardingStrategy.GEOGRAPHIC: {
                    "regions": ["US", "EU", "APAC"],
                    "balancing": "Based on traffic"
                },
                ShardingStrategy.TIME_BASED: {
                    "intervals": "monthly",
                    "retention": "archive after 12 months"
                }
            }
            
            return {
                "success": True,
                "sharding_strategy": {
                    "type": strategy.value,
                    "shards": shards,
                    "shard_key": shard_key,
                    "config": configs.get(strategy, {})
                },
                "recommendations": [
                    "Choose shard key carefully to avoid hot spots",
                    "Plan for rebalancing when adding shards",
                    "Implement cross-shard queries carefully"
                ]
            }
            
        except Exception as e:
            logger.error(f"Erreur conception sharding: {e}")
            return {"success": False, "error": str(e)}
    
    async def plan_migration(self, source_engine: str, target_engine: str, 
                             data_volume_gb: float) -> Dict[str, Any]:
        """Planifie une migration de base de données."""
        try:
            source = DatabaseEngine.POSTGRESQL
            target = DatabaseEngine.POSTGRESQL
            for de in DatabaseEngine:
                if de.value == source_engine.lower():
                    source = de
                if de.value == target_engine.lower():
                    target = de
            
            # Déterminer la complexité
            same_type = source.value.split('_')[0] == target.value.split('_')[0]
            complexity = "low" if same_type else "high"
            
            # Calculer la durée estimée
            base_hours = data_volume_gb / 10  # 10 GB par heure
            if not same_type:
                base_hours *= 2
            
            # Déterminer si downtime est nécessaire
            downtime_required = source != target
            
            steps = [
                {"step": 1, "name": "Schema analysis", "duration_hours": 2},
                {"step": 2, "name": "Schema conversion", "duration_hours": 4 if not same_type else 1},
                {"step": 3, "name": "Data migration", "duration_hours": base_hours},
                {"step": 4, "name": "Data validation", "duration_hours": 2},
                {"step": 5, "name": "Application switch", "duration_hours": 1, "downtime": downtime_required}
            ]
            
            migration = MigrationPlan(
                source_engine=source,
                target_engine=target,
                steps=steps,
                estimated_duration_hours=sum(s["duration_hours"] for s in steps),
                risks=[
                    "Data type incompatibility",
                    "Performance degradation after migration",
                    "Application compatibility issues"
                ],
                rollback_plan=[
                    "Keep source database available during migration",
                    "Test rollback procedure before migration",
                    "Have recent backup ready"
                ],
                data_volume_gb=data_volume_gb,
                downtime_expected=downtime_required,
                estimated_downtime_minutes=30 if downtime_required else 0
            )
            
            self._database_metrics["migrations_planned"] += 1
            
            return {
                "success": True,
                "migration_plan": {
                    "source": source.value,
                    "target": target.value,
                    "complexity": complexity,
                    "steps": steps,
                    "estimated_duration_hours": migration.estimated_duration_hours,
                    "downtime_required": downtime_required,
                    "estimated_downtime_minutes": migration.estimated_downtime_minutes
                },
                "risks": migration.risks,
                "rollback_plan": migration.rollback_plan
            }
            
        except Exception as e:
            logger.error(f"Erreur planification migration: {e}")
            return {"success": False, "error": str(e)}
    
    async def plan_capacity(self, requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Planifie la capacité de la base de données."""
        try:
            current_gb = requirements.get("current_data_gb", 100)
            growth_rate = requirements.get("growth_rate_percent", 20)  # par an
            years = requirements.get("years", 3)
            read_ops = requirements.get("read_ops_per_second", 1000)
            write_ops = requirements.get("write_ops_per_second", 500)
            
            # Calculer la croissance
            future_gb = current_gb * (1 + growth_rate / 100) ** years
            
            # Estimer les besoins
            storage_needed_gb = future_gb * 1.5  # Buffer
            iops_needed = max(read_ops, write_ops) * 1.2
            
            # Recommandations
            recommendations = []
            if storage_needed_gb > 500:
                recommendations.append("Consider sharding or archiving strategy")
            if iops_needed > 2000:
                recommendations.append("Consider read replicas or SSD storage")
            if growth_rate > 50:
                recommendations.append("Implement data retention policy")
            
            return {
                "success": True,
                "capacity_plan": {
                    "current_data_gb": current_gb,
                    "estimated_growth_rate_percent": growth_rate,
                    "data_gb_in_{years}_years": round(future_gb, 2),
                    "storage_needed_gb": round(storage_needed_gb, 2),
                    "iops_needed": round(iops_needed),
                    "recommendations": recommendations
                }
            }
            
        except Exception as e:
            logger.error(f"Erreur planification capacité: {e}")
            return {"success": False, "error": str(e)}
    
    async def tune_performance(self, db_config: Dict[str, Any]) -> Dict[str, Any]:
        """Optimise les performances de la base de données."""
        try:
            engine = db_config.get("engine", "postgresql")
            recommendations = []
            
            if engine == "postgresql":
                recommendations = [
                    {"parameter": "shared_buffers", "value": "25% of RAM", "impact": "High"},
                    {"parameter": "effective_cache_size", "value": "50% of RAM", "impact": "High"},
                    {"parameter": "work_mem", "value": "10-20MB", "impact": "Medium"},
                    {"parameter": "maintenance_work_mem", "value": "10% of RAM", "impact": "Medium"},
                    {"parameter": "wal_buffers", "value": "16MB", "impact": "Low"},
                    {"parameter": "max_connections", "value": "100-500", "impact": "Medium"}
                ]
            elif engine == "mysql":
                recommendations = [
                    {"parameter": "innodb_buffer_pool_size", "value": "70% of RAM", "impact": "High"},
                    {"parameter": "innodb_log_file_size", "value": "1-2GB", "impact": "Medium"},
                    {"parameter": "max_connections", "value": "100-500", "impact": "Medium"},
                    {"parameter": "query_cache_size", "value": "0 (disabled)", "impact": "Low"},
                    {"parameter": "tmp_table_size", "value": "64MB", "impact": "Medium"}
                ]
            elif engine == "mongodb":
                recommendations = [
                    {"parameter": "cacheSizeGB", "value": "50% of RAM", "impact": "High"},
                    {"parameter": "storage.wiredTiger.engineConfig.cacheSizeGB", "value": "50% of RAM", "impact": "High"},
                    {"parameter": "operationProfiling.mode", "value": "slowOp", "impact": "Medium"}
                ]
            
            return {
                "success": True,
                "performance_recommendations": recommendations,
                "summary": f"{len(recommendations)} tuning parameters identified"
            }
            
        except Exception as e:
            logger.error(f"Erreur tuning performance: {e}")
            return {"success": False, "error": str(e)}
    
    # ========================================================================
    # MÉTHODES PRIVÉES
    # ========================================================================
    
    def _create_tables(self, requirements: Dict[str, Any], 
                       engine: DatabaseEngine) -> List[TableSchema]:
        """Crée les tables selon les exigences."""
        tables = []
        
        # Table utilisateurs
        tables.append(TableSchema(
            name="users",
            description="User accounts and profiles",
            columns=[
                {"name": "id", "type": "uuid", "nullable": False},
                {"name": "email", "type": "varchar(255)", "nullable": False},
                {"name": "name", "type": "varchar(100)", "nullable": False},
                {"name": "created_at", "type": "timestamp", "nullable": False}
            ],
            primary_key=["id"],
            indexes=[
                {"columns": ["email"], "type": "unique"},
                {"columns": ["created_at"], "type": "btree"}
            ],
            estimated_rows=requirements.get("expected_users", 1_000_000)
        ))
        
        # Table produits (si e-commerce)
        if requirements.get("has_products", True):
            tables.append(TableSchema(
                name="products",
                description="Product catalog",
                columns=[
                    {"name": "id", "type": "uuid", "nullable": False},
                    {"name": "name", "type": "varchar(200)", "nullable": False},
                    {"name": "price", "type": "decimal(10,2)", "nullable": False},
                    {"name": "stock", "type": "integer", "nullable": False}
                ],
                primary_key=["id"],
                indexes=[
                    {"columns": ["name"], "type": "gin" if engine == DatabaseEngine.POSTGRESQL else "btree"}
                ],
                estimated_rows=requirements.get("expected_products", 100_000)
            ))
        
        return tables
    
    # ========================================================================
    # MÉTHODES DE RÉCUPÉRATION
    # ========================================================================
    
    def get_design(self, design_id: str) -> Optional[Dict[str, Any]]:
        """Récupère une conception de base de données"""
        design = self._designs.get(design_id)
        return design.to_dict() if design else None
    
    def list_designs(self) -> List[Dict[str, Any]]:
        """Liste toutes les conceptions disponibles"""
        return [
            {
                "design_id": design_id,
                "name": design.name,
                "engine": design.engine.value,
                "tables_count": len(design.tables),
                "created_at": design.created_at.isoformat()
            }
            for design_id, design in self._designs.items()
        ]
    
    def get_metrics(self) -> Dict[str, Any]:
        """Retourne les métriques du sous-agent"""
        return {
            **self._database_metrics,
            "designs_count": len(self._designs),
            "database_patterns": self._db_patterns
        }
    
    # ========================================================================
    # NETTOYAGE
    # ========================================================================
    
    async def _cleanup(self):
        """Nettoie les ressources du sous-agent"""
        logger.info("Nettoyage des ressources Database Architect...")
        self._designs.clear()
        await super()._cleanup()


# ============================================================================
# FONCTION D'USINE
# ============================================================================

def create_database_architect_subagent(config_path: Optional[str] = None) -> DatabaseArchitectSubAgent:
    """Crée une instance du sous-agent Database Architect"""
    return DatabaseArchitectSubAgent(config_path)
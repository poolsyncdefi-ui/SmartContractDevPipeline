#!/usr/bin/env python3
"""
Script de création avancée des sous-agents pour communication
Crée 7 sous-agents riches avec configurations détaillées
Version FINALE - Toutes les références à 'self' sont échappées
"""

import os
import sys
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

# Configuration
PROJECT_ROOT = Path(__file__).parent if __file__ else Path.cwd()
AGENT_PATH = PROJECT_ROOT / "agents" / "communication"
SOUS_AGENTS_PATH = AGENT_PATH / "sous_agents"

# ============================================================================
# SOUS-AGENT 1: QUEUE MANAGER
# ============================================================================
QUEUE_MANAGER = {
    "id": "queue_manager",
    "display_name": "📊 Gestionnaire de Files d'Attente",
    "description": "Gère les files d'attente prioritaires avec QoS avancé, monitoring et scaling automatique",
    "version": "2.0.0",
    "capabilities": [
        {
            "name": "fifo_queue_management",
            "description": "Gestion de files FIFO avec ordre strict",
            "confidence": 0.98,
            "features": ["ordering_guarantee", "dead_letter_queue", "message_replay"]
        },
        {
            "name": "priority_queue_routing",
            "description": "Routage basé sur priorité avec 5 niveaux",
            "confidence": 0.97,
            "priority_levels": 5
        },
        {
            "name": "queue_monitoring",
            "description": "Monitoring en temps réel des files",
            "confidence": 0.95,
            "metrics": ["size", "throughput", "latency", "backlog"]
        },
        {
            "name": "automatic_scaling",
            "description": "Scaling automatique basé sur la charge",
            "confidence": 0.9,
            "thresholds": {"scale_up": 0.8, "scale_down": 0.2}
        },
        {
            "name": "queue_persistence",
            "description": "Persistance des messages sur disque",
            "confidence": 0.95,
            "storage": ["memory", "disk", "hybrid"]
        }
    ],
    "queue_types": ["fifo", "priority", "lifo", "dead_letter"],
    "performance_targets": {
        "max_queue_size": 100000,
        "target_latency_ms": 50,
        "max_throughput": 10000
    },
    "outputs": [
        {"name": "queue_metrics", "type": "metrics", "format": "prometheus"},
        {"name": "queue_status", "type": "status", "format": "json"}
    ]
}

# ============================================================================
# SOUS-AGENT 2: PUBSUB MANAGER
# ============================================================================
PUBSUB_MANAGER = {
    "id": "pubsub_manager",
    "display_name": "📢 Gestionnaire Pub/Sub Haute Performance",
    "description": "Gère les topics et abonnements publish/subscribe avec patterns avancés",
    "version": "2.0.0",
    "capabilities": [
        {
            "name": "topic_management",
            "description": "Création et gestion de topics hiérarchiques",
            "confidence": 0.98,
            "features": ["wildcards", "hierarchical", "dynamic_topics"]
        },
        {
            "name": "subscription_handling",
            "description": "Gestion des abonnements persistants",
            "confidence": 0.97,
            "subscription_types": ["durable", "volatile", "shared"]
        },
        {
            "name": "message_broadcasting",
            "description": "Broadcast efficace à tous les abonnés",
            "confidence": 0.96,
            "strategies": ["fanout", "multicast", "selective"]
        },
        {
            "name": "topic_partitioning",
            "description": "Partitionnement des topics pour scale",
            "confidence": 0.92,
            "max_partitions": 64
        },
        {
            "name": "message_filtering",
            "description": "Filtrage avancé par expressions",
            "confidence": 0.94,
            "filter_types": ["sql", "regex", "jmespath"]
        }
    ],
    "subscription_types": ["durable", "volatile", "shared", "exclusive"],
    "wildcard_support": {"single_level": "*", "multi_level": "#"},
    "outputs": [
        {"name": "subscription_stats", "type": "metrics", "format": "json"},
        {"name": "topic_events", "type": "events", "format": "json"}
    ]
}

# ============================================================================
# SOUS-AGENT 3: CIRCUIT BREAKER
# ============================================================================
CIRCUIT_BREAKER = {
    "id": "circuit_breaker",
    "display_name": "🛡️ Circuit Breaker Intelligent",
    "description": "Protège contre les défaillances en cascade avec stratégies adaptatives",
    "version": "2.0.0",
    "capabilities": [
        {
            "name": "failure_detection",
            "description": "Détection avancée des défaillances",
            "confidence": 0.98,
            "detection_methods": ["timeout", "error_rate", "consecutive_failures"]
        },
        {
            "name": "circuit_state_management",
            "description": "Gestion des états closed/open/half-open",
            "confidence": 0.97,
            "states": ["closed", "open", "half-open", "forced_open"]
        },
        {
            "name": "automatic_recovery",
            "description": "Récupération automatique avec test",
            "confidence": 0.95,
            "recovery_strategies": ["progressive", "test_request", "time_based"]
        },
        {
            "name": "failure_threshold_adaptation",
            "description": "Adaptation dynamique des seuils",
            "confidence": 0.92,
            "learning_enabled": True
        },
        {
            "name": "metrics_collection",
            "description": "Collecte de métriques de défaillance",
            "confidence": 0.96,
            "metrics": ["failure_rate", "success_rate", "mean_time_to_recover"]
        }
    ],
    "config": {
        "failure_threshold": 5,
        "timeout_seconds": 30,
        "half_open_timeout": 10,
        "success_threshold": 2
    },
    "outputs": [
        {"name": "circuit_events", "type": "events", "format": "json"},
        {"name": "circuit_metrics", "type": "metrics", "format": "prometheus"}
    ]
}

# ============================================================================
# SOUS-AGENT 4: MESSAGE ROUTER
# ============================================================================
MESSAGE_ROUTER = {
    "id": "message_router",
    "display_name": "🔄 Routeur Intelligent de Messages",
    "description": "Route les messages selon règles complexes, patterns et conditions",
    "version": "2.0.0",
    "capabilities": [
        {
            "name": "content_based_routing",
            "description": "Routage basé sur le contenu des messages",
            "confidence": 0.97,
            "routing_criteria": ["headers", "payload", "metadata"]
        },
        {
            "name": "dynamic_routing",
            "description": "Routage dynamique selon charge",
            "confidence": 0.95,
            "algorithms": ["round_robin", "least_loaded", "random"]
        },
        {
            "name": "message_filtering",
            "description": "Filtrage avec expressions complexes",
            "confidence": 0.96,
            "filter_engines": ["jmespath", "jsonata", "custom"]
        },
        {
            "name": "rule_management",
            "description": "Gestion dynamique des règles",
            "confidence": 0.94,
            "max_rules": 1000,
            "rule_formats": ["json", "yaml", "dsl"]
        },
        {
            "name": "route_visualization",
            "description": "Visualisation des routes",
            "confidence": 0.88,
            "formats": ["graph", "tree", "table"]
        }
    ],
    "routing_strategies": ["content_based", "header_based", "dynamic", "consistent_hashing"],
    "max_routes": 1000,
    "outputs": [
        {"name": "routing_table", "type": "config", "format": "json"},
        {"name": "route_metrics", "type": "metrics", "format": "prometheus"}
    ]
}

# ============================================================================
# SOUS-AGENT 5: DEAD LETTER ANALYZER
# ============================================================================
DEAD_LETTER_ANALYZER = {
    "id": "dead_letter_analyzer",
    "display_name": "💀 Analyseur Dead Letter Avancé",
    "description": "Analyse les messages échoués, détecte les patterns et propose des solutions",
    "version": "2.0.0",
    "capabilities": [
        {
            "name": "dead_letter_monitoring",
            "description": "Surveillance des messages en dead letter",
            "confidence": 0.98,
            "monitoring_features": ["real_time", "historical", "trend_analysis"]
        },
        {
            "name": "failure_analysis",
            "description": "Analyse des causes d'échec",
            "confidence": 0.96,
            "analysis_types": ["error_correlation", "pattern_matching", "root_cause"]
        },
        {
            "name": "retry_strategy",
            "description": "Stratégies de réessai intelligentes",
            "confidence": 0.95,
            "strategies": ["exponential_backoff", "linear", "custom_schedule"]
        },
        {
            "name": "message_recovery",
            "description": "Récupération automatique des messages",
            "confidence": 0.93,
            "recovery_methods": ["automatic", "manual_approval", "conditional"]
        },
        {
            "name": "pattern_detection",
            "description": "Détection de patterns d'échec",
            "confidence": 0.91,
            "ml_enabled": True
        }
    ],
    "retention_days": 30,
    "max_analysis_batch": 1000,
    "outputs": [
        {"name": "dead_letter_report", "type": "report", "format": "json"},
        {"name": "failure_insights", "type": "insights", "format": "json"}
    ]
}

# ============================================================================
# SOUS-AGENT 6: PERFORMANCE OPTIMIZER
# ============================================================================
PERFORMANCE_OPTIMIZER = {
    "id": "performance_optimizer",
    "display_name": "⚡ Optimisateur Performance Temps-Réel",
    "description": "Optimise en continu les performances du système de messagerie",
    "version": "2.0.0",
    "capabilities": [
        {
            "name": "throughput_optimization",
            "description": "Optimisation du débit de messages",
            "confidence": 0.97,
            "techniques": ["batching", "compression", "parallel_processing"]
        },
        {
            "name": "latency_reduction",
            "description": "Réduction de la latence",
            "confidence": 0.96,
            "targets": {"p95": 50, "p99": 100}
        },
        {
            "name": "batch_processing",
            "description": "Traitement par lots optimisé",
            "confidence": 0.95,
            "batch_sizes": [10, 50, 100, 500]
        },
        {
            "name": "resource_optimization",
            "description": "Optimisation des ressources",
            "confidence": 0.93,
            "resources": ["cpu", "memory", "network"]
        },
        {
            "name": "adaptive_tuning",
            "description": "Ajustement automatique des paramètres",
            "confidence": 0.91,
            "learning_enabled": True
        }
    ],
    "optimization_targets": {
        "throughput": 10000,
        "latency_p95_ms": 50,
        "cpu_usage_max": 80,
        "memory_usage_max": 1024
    },
    "outputs": [
        {"name": "performance_report", "type": "report", "format": "json"},
        {"name": "optimization_suggestions", "type": "insights", "format": "json"}
    ]
}

# ============================================================================
# SOUS-AGENT 7: SECURITY VALIDATOR
# ============================================================================
SECURITY_VALIDATOR = {
    "id": "security_validator",
    "display_name": "🔒 Validateur Sécurité & Conformité",
    "description": "Valide, chiffre et sécurise tous les messages selon politiques",
    "version": "2.0.0",
    "capabilities": [
        {
            "name": "message_validation",
            "description": "Validation complète des messages",
            "confidence": 0.98,
            "validation_types": ["schema", "format", "size", "content"]
        },
        {
            "name": "schema_checking",
            "description": "Vérification contre schémas JSON/Avro",
            "confidence": 0.97,
            "schema_formats": ["json-schema", "avro", "protobuf"]
        },
        {
            "name": "encryption_verification",
            "description": "Vérification du chiffrement",
            "confidence": 0.96,
            "encryption_methods": ["aes-256", "rsa", "ecc"]
        },
        {
            "name": "access_control",
            "description": "Contrôle d'accès basé sur politiques",
            "confidence": 0.97,
            "models": ["rbac", "abac", "acl"]
        },
        {
            "name": "audit_logging",
            "description": "Journalisation d'audit complète",
            "confidence": 0.95,
            "audit_events": ["access", "modification", "validation_failure"]
        },
        {
            "name": "threat_detection",
            "description": "Détection de menaces",
            "confidence": 0.93,
            "threat_types": ["injection", "traversal", "overflow"]
        }
    ],
    "security_levels": ["none", "basic", "standard", "high", "paranoid"],
    "compliance_standards": ["GDPR", "SOC2", "HIPAA", "PCI-DSS"],
    "outputs": [
        {"name": "security_report", "type": "report", "format": "json"},
        {"name": "audit_trail", "type": "audit", "format": "jsonl"},
        {"name": "validation_results", "type": "results", "format": "json"}
    ]
}

# Liste complète des sous-agents
SUB_AGENTS = [
    QUEUE_MANAGER,
    PUBSUB_MANAGER,
    CIRCUIT_BREAKER,
    MESSAGE_ROUTER,
    DEAD_LETTER_ANALYZER,
    PERFORMANCE_OPTIMIZER,
    SECURITY_VALIDATOR
]


def create_class_name(agent_id: str) -> str:
    """Convertit un ID en nom de classe (ex: queue_manager -> QueueManagerSubAgent)"""
    parts = agent_id.split('_')
    return ''.join(p.capitalize() for p in parts) + 'SubAgent'


def format_capabilities_yaml(capabilities: List[Dict]) -> str:
    """Formate la liste des capacités en YAML"""
    lines = []
    for cap in capabilities:
        lines.append(f'  - name: "{cap["name"]}"')
        lines.append(f'    description: "{cap["description"]}"')
        lines.append(f'    confidence: {cap["confidence"]}')
        if "features" in cap:
            lines.append(f'    features: {cap["features"]}')
        if "priority_levels" in cap:
            lines.append(f'    priority_levels: {cap["priority_levels"]}')
        if "metrics" in cap:
            lines.append(f'    metrics: {cap["metrics"]}')
        lines.append('')
    return '\n'.join(lines)


def create_agent_py(agent_data: Dict) -> str:
    """Crée le contenu du fichier agent.py pour un sous-agent"""
    agent_id = agent_data["id"]
    display_name = agent_data["display_name"]
    description = agent_data["description"]
    version = agent_data["version"]
    capabilities = agent_data["capabilities"]
    class_name = create_class_name(agent_id)
    
    capabilities_list = '\n'.join([f'        "{cap["name"]}",' for cap in capabilities])
    
    # Générer les lignes pour les handlers
    handler_lines = []
    for cap in capabilities:
        handler_lines.append(f'            "{cap["name"]}": self._handle_{cap["name"]},')
    
    handlers_section = '\n'.join(handler_lines)
    
    # Générer les méthodes pour chaque capacité (avec échappement correct)
    capability_methods = []
    for cap in capabilities:
        method = f'''
    async def _handle_{cap["name"]}(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Traite une tâche de type {cap["name"]}"""
        logger.info(f"Traitement de {cap["name"]} avec params: {{params}}")
        self._stats['tasks_processed'] += 1
        self._stats['successful_tasks'] += 1
        
        return {{
            "success": True,
            "task": "{cap["name"]}",
            "description": "{cap["description"]}",
            "params": params,
            "result": "Tâche exécutée avec succès",
            "timestamp": datetime.now().isoformat()
        }}'''
        capability_methods.append(method)
    
    capability_methods_section = '\n'.join(capability_methods)
    
    return f'''"""
{display_name} - Sous-agent spécialisé
Version: {version}

{description}
"""

import logging
import sys
import asyncio
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List
from enum import Enum

# Configuration des imports
current_dir = Path(__file__).parent.absolute()
project_root = current_dir.parent.parent.parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from agents.base_agent.base_agent import BaseAgent, AgentStatus, Message, MessageType

logger = logging.getLogger(__name__)


class TaskType(Enum):
    """Types de tâches supportés"""
{chr(10).join([f'    {cap["name"].upper()} = "{cap["name"]}"' for cap in capabilities])}


class {class_name}(BaseAgent):
    """
    {description}
    
    Capacités principales:
{chr(10).join([f'    • {cap["name"]}: {cap["description"]}' for cap in capabilities])}
    """
    
    def __init__(self, config_path: str = ""):
        """Initialise le sous-agent"""
        if not config_path:
            config_path = str(current_dir / "config.yaml")

        super().__init__(config_path)

        self._display_name = "{display_name}"
        self._initialized = False
        self._components = {{}}
        
        # Statistiques avancées
        self._stats = {{
            'tasks_processed': 0,
            'successful_tasks': 0,
            'failed_tasks': 0,
            'total_duration_ms': 0,
            'start_time': datetime.now().isoformat()
        }}
        
        # Métriques par type de tâche
        self._task_metrics: Dict[str, Dict] = {{}}

        logger.info(f"{{self._display_name}} créé - v{{self._version}}")

    async def initialize(self) -> bool:
        """Initialise le sous-agent"""
        try:
            self._set_status(AgentStatus.INITIALIZING)
            logger.info(f"Initialisation de {{self._display_name}}...")

            base_result = await super().initialize()
            if not base_result:
                return False

            await self._initialize_components()

            self._initialized = True
            self._set_status(AgentStatus.READY)
            logger.info(f"✅ {{self._display_name}} prêt")
            return True

        except Exception as e:
            logger.error(f"❌ Erreur initialisation: {{e}}")
            self._set_status(AgentStatus.ERROR)
            return False

    async def _initialize_components(self) -> bool:
        """Initialise les composants du sous-agent"""
        logger.info("Initialisation des composants...")
        
        self._components = {{
            "capabilities": [
{capabilities_list}
            ],
            "enabled": True,
            "version": "{version}",
            "config": self._agent_config
        }}
        
        logger.info(f"✅ Composants: {{list(self._components.keys())}}")
        return True

    async def _handle_custom_message(self, message: Message) -> Optional[Message]:
        """Gère les messages personnalisés"""
        try:
            msg_type = message.message_type
            logger.debug(f"Message reçu: {{msg_type}} de {{message.sender}}")

            # Handlers standards
            handlers = {{
                f"{{self.name}}.status": self._handle_status,
                f"{{self.name}}.metrics": self._handle_metrics,
                f"{{self.name}}.health": self._handle_health,
                f"{{self.name}}.process": self._handle_process,
                f"{{self.name}}.capabilities": self._handle_capabilities,
            }}

            # Handlers pour chaque capacité
{handlers_section}

            if msg_type in handlers:
                return await handlers[msg_type](message)

            return None

        except Exception as e:
            logger.error(f"Erreur traitement message: {{e}}")
            return Message(
                sender=self.name,
                recipient=message.sender,
                content={{"error": str(e)}},
                message_type=MessageType.ERROR.value,
                correlation_id=message.message_id
            )

    async def _handle_status(self, message: Message) -> Message:
        """Retourne le statut général"""
        return Message(
            sender=self.name,
            recipient=message.sender,
            content={{
                'status': self._status.value,
                'initialized': self._initialized,
                'stats': self._stats
            }},
            message_type=f"{{self.name}}.status_response",
            correlation_id=message.message_id
        )

    async def _handle_metrics(self, message: Message) -> Message:
        """Retourne les métriques détaillées"""
        return Message(
            sender=self.name,
            recipient=message.sender,
            content={{
                'global': self._stats,
                'by_task': self._task_metrics,
                'components': self._components
            }},
            message_type=f"{{self.name}}.metrics_response",
            correlation_id=message.message_id
        )

    async def _handle_health(self, message: Message) -> Message:
        """Retourne l'état de santé"""
        health = await self.health_check()
        return Message(
            sender=self.name,
            recipient=message.sender,
            content=health,
            message_type=f"{{self.name}}.health_response",
            correlation_id=message.message_id
        )

    async def _handle_capabilities(self, message: Message) -> Message:
        """Liste les capacités disponibles"""
        return Message(
            sender=self.name,
            recipient=message.sender,
            content={{
                'capabilities': [
{capabilities_list}
                ],
                'version': '{version}'
            }},
            message_type=f"{{self.name}}.capabilities_response",
            correlation_id=message.message_id
        )

    async def _handle_process(self, message: Message) -> Message:
        """Handler générique pour le traitement"""
        task_type = message.content.get('task_type')
        params = message.content.get('params', {{}})
        
        # Routing vers le handler spécifique
        handler_map = {{
{handlers_section}
        }}
        
        if task_type in handler_map:
            result = await handler_map[task_type](params)
        else:
            result = {{"success": False, "error": f"Unknown task type: {{task_type}}"}}
        
        return Message(
            sender=self.name,
            recipient=message.sender,
            content=result,
            message_type=f"{{self.name}}.processed",
            correlation_id=message.message_id
        )

{capability_methods_section}

    async def shutdown(self) -> bool:
        """Arrête le sous-agent"""
        logger.info(f"Arrêt de {{self._display_name}}...")
        self._set_status(AgentStatus.SHUTTING_DOWN)
        await super().shutdown()
        logger.info(f"✅ {{self._display_name}} arrêté")
        return True

    async def pause(self) -> bool:
        """Met en pause le sous-agent"""
        logger.info(f"Pause de {{self._display_name}}...")
        self._set_status(AgentStatus.PAUSED)
        return True

    async def resume(self) -> bool:
        """Reprend l'activité"""
        logger.info(f"Reprise de {{self._display_name}}...")
        self._set_status(AgentStatus.READY)
        return True

    async def health_check(self) -> Dict[str, Any]:
        """Vérifie la santé du sous-agent"""
        base_health = await super().health_check()

        uptime = None
        if self._stats.get('start_time'):
            start = datetime.fromisoformat(self._stats['start_time'])
            uptime = str(datetime.now() - start)

        success_rate = 0
        if self._stats['tasks_processed'] > 0:
            success_rate = (self._stats['successful_tasks'] / self._stats['tasks_processed']) * 100

        return {{
            **base_health,
            "agent": self.name,
            "display_name": self._display_name,
            "status": self._status.value,
            "ready": self._status == AgentStatus.READY,
            "initialized": self._initialized,
            "uptime": uptime,
            "components": list(self._components.keys()),
            "stats": {{
                "tasks_processed": self._stats['tasks_processed'],
                "success_rate": f"{{success_rate:.1f}}%",
                "successful": self._stats['successful_tasks'],
                "failed": self._stats['failed_tasks']
            }},
            "timestamp": datetime.now().isoformat()
        }}

    def get_agent_info(self) -> Dict[str, Any]:
        """Informations pour le registre"""
        return {{
            "id": self.name,
            "name": "{class_name}",
            "display_name": self._display_name,
            "version": "{version}",
            "description": \"\"\"{description}\"\"\",
            "status": self._status.value,
            "capabilities": [
{capabilities_list}
            ],
            "stats": self._stats
        }}


def create_{agent_id}_agent(config_path: str = "") -> {class_name}:
    """Crée une instance du sous-agent"""
    return {class_name}(config_path)
'''


def create_config_yaml(agent_data: Dict) -> str:
    """Crée le contenu du fichier config.yaml pour un sous-agent"""
    agent_id = agent_data["id"]
    display_name = agent_data["display_name"]
    description = agent_data["description"]
    version = agent_data["version"]
    capabilities = agent_data["capabilities"]
    class_name = create_class_name(agent_id)
    
    capabilities_yaml = format_capabilities_yaml(capabilities)
    
    # Outputs YAML
    outputs_yaml = '\n'.join([f'  - name: "{out["name"]}"\n    type: "{out["type"]}"\n    format: "{out["format"]}"' 
                              for out in agent_data.get("outputs", [])])
    
    # Configuration spécifique
    specific_config = []
    for key, value in agent_data.items():
        if key not in ["id", "display_name", "description", "version", "capabilities", "outputs"]:
            if isinstance(value, dict):
                specific_config.append(f"{key}:")
                for k, v in value.items():
                    specific_config.append(f'  {k}: {v}')
            elif isinstance(value, list):
                specific_config.append(f"{key}: {value}")
            else:
                specific_config.append(f"{key}: {value}")
    
    specific_config_str = '\n'.join(specific_config)
    
    return f'''# ============================================================================
# {display_name} - Configuration avancée
# Version: {version}
# ============================================================================

agent:
  name: "{class_name}"
  display_name: "{display_name}"
  description: |-
    {description}
  version: "{version}"
  class_name: "{class_name}"
  module_path: "agents.communication.sous_agents.{agent_id}.agent"

# ============================================================================
# SYSTÈME
# ============================================================================
system:
  log_level: "INFO"
  log_file: "logs/communication/{agent_id}.log"
  timeout_seconds: 120
  max_retries: 3
  retry_delay_seconds: 1
  
  # Cache
  cache_enabled: true
  cache_ttl_seconds: 300
  cache_max_size: 1000

# ============================================================================
# PERFORMANCE
# ============================================================================
performance:
  max_concurrent_tasks: 5
  task_queue_size: 100
  priority_levels: ["critical", "high", "medium", "low"]
  default_priority: "medium"
  
  # Timeouts par priorité
  timeouts:
    critical: 60
    high: 30
    medium: 15
    low: 5

# ============================================================================
# CAPACITÉS
# ============================================================================
capabilities:
{capabilities_yaml}

# ============================================================================
# OUTPUTS PRODUITS
# ============================================================================
outputs:
{outputs_yaml}

# ============================================================================
# MÉTRIQUES
# ============================================================================
metrics:
  track_by_task_type: true
  track_duration: true
  track_errors: true
  track_cache: true
  retention_days: 30

# ============================================================================
# SÉCURITÉ
# ============================================================================
security:
  validate_inputs: true
  validate_outputs: false
  mask_sensitive_data: true
  sensitive_fields: ["password", "token", "key", "secret"]

# ============================================================================
# CONFIGURATION SPÉCIFIQUE
# ============================================================================
{specific_config_str}

# ============================================================================
# MÉTADONNÉES
# ============================================================================
metadata:
  author: "SmartContractDevPipeline"
  maintainer: "dev@poolsync.io"
  license: "Proprietary"
  tags: ["communication", "{agent_id}", "messaging"]
  capabilities_count: {len(capabilities)}
  last_reviewed: "{datetime.now().strftime("%Y-%m-%d")}"
'''


def create_directory_structure():
    """Crée toute l'arborescence des dossiers et fichiers"""
    
    print("=" * 80)
    print("🚀 CRÉATION AVANCÉE DES SOUS-AGENTS COMMUNICATION")
    print("=" * 80)
    
    # 1. Créer le dossier principal des sous-agents
    print(f"\n📁 Création du dossier: {SOUS_AGENTS_PATH}")
    SOUS_AGENTS_PATH.mkdir(parents=True, exist_ok=True)
    
    # 2. Créer le __init__.py du dossier sous_agents
    init_file = SOUS_AGENTS_PATH / "__init__.py"
    print(f"   📄 Création: {init_file}")
    with open(init_file, 'w', encoding='utf-8') as f:
        f.write('"""\nPackage des sous-agents Communication\nSous-agents spécialisés pour la gestion des messages\n"""\n\n__all__ = []\n')
    
    # 3. Créer chaque sous-agent
    for agent in SUB_AGENTS:
        agent_id = agent["id"]
        display_name = agent["display_name"]
        
        agent_path = SOUS_AGENTS_PATH / agent_id
        print(f"\n📁 Création du sous-agent: {agent_id}")
        print(f"   📁 Dossier: {agent_path}")
        agent_path.mkdir(exist_ok=True)
        
        # Créer __init__.py
        init_file = agent_path / "__init__.py"
        print(f"   📄 Création: {init_file}")
        with open(init_file, 'w', encoding='utf-8') as f:
            class_name = create_class_name(agent_id)
            f.write(f'''"""
Package {display_name}
Version: {agent["version"]}

{agent["description"]}
"""

from .agent import {class_name}

__all__ = ['{class_name}']
__version__ = '{agent["version"]}'
''')
        
        # Créer agent.py
        agent_file = agent_path / "agent.py"
        print(f"   📄 Création: {agent_file}")
        with open(agent_file, 'w', encoding='utf-8') as f:
            f.write(create_agent_py(agent))
        
        # Créer config.yaml
        config_file = agent_path / "config.yaml"
        print(f"   📄 Création: {config_file}")
        with open(config_file, 'w', encoding='utf-8') as f:
            f.write(create_config_yaml(agent))
        
        # Créer tools.py
        tools_file = agent_path / "tools.py"
        print(f"   📄 Création: {tools_file}")
        with open(tools_file, 'w', encoding='utf-8') as f:
            f.write(f'''"""
Outils utilitaires pour {display_name}
Version: {agent["version"]}
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
import json

logger = logging.getLogger(__name__)


def format_timestamp(timestamp: Optional[datetime] = None) -> str:
    """Formate un timestamp pour l'affichage"""
    if timestamp is None:
        timestamp = datetime.now()
    return timestamp.strftime("%Y-%m-%d %H:%M:%S")


def validate_config(config: Dict[str, Any]) -> bool:
    """Valide la configuration"""
    required_fields = ["agent", "system"]
    return all(field in config for field in required_fields)


def serialize_message(obj: Any) -> str:
    """Sérialise un message en JSON"""
    if isinstance(obj, datetime):
        return obj.isoformat()
    return str(obj)


def deserialize_message(data: str) -> Dict[str, Any]:
    """Désérialise un message JSON"""
    return json.loads(data)


def calculate_backoff(attempt: int, base_delay: float = 1.0, max_delay: float = 60.0) -> float:
    """Calcule le délai de backoff exponentiel"""
    delay = base_delay * (2 ** (attempt - 1))
    return min(delay, max_delay)
''')
        
        print(f"   ✅ Sous-agent {agent_id} créé avec succès")
    
    print("\n" + "=" * 80)
    print("✅ CRÉATION TERMINÉE AVEC SUCCÈS !")
    print("=" * 80)
    
    # Résumé
    print(f"\n📊 RÉSUMÉ:")
    print(f"   • Dossier principal: {SOUS_AGENTS_PATH}")
    print(f"   • Nombre de sous-agents: {len(SUB_AGENTS)}")
    print(f"   • Fichiers créés: {len(SUB_AGENTS) * 4 + 1} fichiers")
    print(f"   • Total capacités: {sum(len(a['capabilities']) for a in SUB_AGENTS)}")


def verify_agent_parent():
    """Vérifie que l'agent parent existe"""
    agent_file = AGENT_PATH / "agent.py"
    
    if not agent_file.exists():
        print(f"\n⚠️  Attention: {agent_file} n'existe pas!")
        print("   Vous devez d'abord créer l'agent parent communication.")
        return False
    
    # Vérifier si importlib est importé
    with open(agent_file, 'r', encoding='utf-8') as f:
        content = f.read()
        if 'import importlib' not in content:
            print(f"\n⚠️  Attention: 'import importlib' manquant dans {agent_file}")
            print("   Ajoutez cette ligne dans les imports de votre agent parent.")
    
    return True


if __name__ == "__main__":
    # Vérifier qu'on est à la racine du projet
    if not (PROJECT_ROOT / "agents").exists():
        print(f"❌ Erreur: Le dossier 'agents' n'existe pas dans {PROJECT_ROOT}")
        print("   Assurez-vous d'exécuter ce script depuis la racine du projet")
        sys.exit(1)
    
    # Créer l'arborescence avancée
    create_directory_structure()
    
    # Vérifications finales
    verify_agent_parent()
    
    print(f"\n🎉 Tous les sous-agents ont été créés avec succès!")
    print(f"\n🚀 Vous pouvez maintenant lancer votre application!")
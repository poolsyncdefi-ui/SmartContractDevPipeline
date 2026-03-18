#!/usr/bin/env python3
"""
Documenter Agent - Système de documentation professionnelle
Gestion de la documentation technique, diagrammes, API, README avec qualité et validation
Version: 2.2.0 (ALIGNÉ SUR COMMUNICATION AGENT)
"""

import logging
import os
import sys
import json
import asyncio
import time
import traceback
import importlib
import shutil
from pathlib import Path
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Any, Optional, Union, Set, Callable
from collections import defaultdict, deque
from dataclasses import dataclass, field
from uuid import uuid4

# ============================================================================
# CONFIGURATION DES IMPORTS - Chemin absolu
# ============================================================================

current_dir = Path(__file__).parent.absolute()
project_root = current_dir.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from agents.base_agent.base_agent import BaseAgent, AgentStatus, Message, MessageType

logger = logging.getLogger(__name__)


# ============================================================================
# ÉNUMS ET STRUCTURES DE DONNÉES
# ============================================================================

class DocFormat(Enum):
    """Formats de documentation supportés"""
    MARKDOWN = "markdown"
    HTML = "html"
    PDF = "pdf"
    OPENAPI = "openapi"
    SITE = "site"
    ASCII_DOC = "asciidoc"


class DocType(Enum):
    """Types de documentation"""
    API = "api"
    USER_GUIDE = "user_guide"
    DEVELOPER_GUIDE = "developer_guide"
    DEPLOYMENT_GUIDE = "deployment_guide"
    ARCHITECTURE = "architecture"
    CONTRACT = "contract"
    README = "readme"
    CHANGELOG = "changelog"
    TUTORIAL = "tutorial"
    GLOSSARY = "glossary"


class DiagramType(Enum):
    """Types de diagrammes supportés"""
    CLASS = "class"
    SEQUENCE = "sequence"
    FLOWCHART = "flowchart"
    STATE = "state"
    ENTITY_RELATIONSHIP = "entity_relationship"
    C4_CONTEXT = "c4_context"
    C4_CONTAINER = "c4_container"
    C4_COMPONENT = "c4_component"
    DEPENDENCY = "dependency"
    INHERITANCE = "inheritance"


class DocStatus(Enum):
    """Statuts de génération de documentation"""
    PENDING = "pending"
    GENERATING = "generating"
    COMPLETED = "completed"
    FAILED = "failed"
    VALIDATING = "validating"
    VALIDATED = "validated"
    REJECTED = "rejected"


class QualityLevel(Enum):
    """Niveaux de qualité de documentation"""
    DRAFT = "draft"           # Brouillon, à revoir
    STANDARD = "standard"      # Qualité standard
    PROFESSIONAL = "professional"  # Qualité professionnelle
    EXCELLENT = "excellent"    # Excellence documentaire


@dataclass
class DocRequest:
    """Requête de génération de documentation"""
    id: str = field(default_factory=lambda: str(uuid4()))
    doc_type: DocType = DocType.CONTRACT
    format: DocFormat = DocFormat.MARKDOWN
    source_path: Optional[str] = None
    source_content: Optional[Any] = None
    output_path: Optional[str] = None
    options: Dict[str, Any] = field(default_factory=dict)
    quality_level: QualityLevel = QualityLevel.PROFESSIONAL
    status: DocStatus = DocStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    requester: str = ""
    correlation_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convertit en dictionnaire"""
        return {
            "id": self.id,
            "doc_type": self.doc_type.value,
            "format": self.format.value,
            "source_path": self.source_path,
            "output_path": self.output_path,
            "options": self.options,
            "quality_level": self.quality_level.value,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "requester": self.requester,
            "correlation_id": self.correlation_id,
            "metadata": self.metadata
        }


@dataclass
class DocSection:
    """Section de documentation"""
    id: str
    title: str
    level: int
    content: str
    diagrams: List[str] = field(default_factory=list)
    examples: List[str] = field(default_factory=list)
    references: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DocPackage:
    """Package complet de documentation"""
    id: str = field(default_factory=lambda: str(uuid4()))
    title: str = ""
    description: str = ""
    version: str = "1.0.0"
    sections: List[DocSection] = field(default_factory=list)
    diagrams: Dict[str, str] = field(default_factory=dict)  # name -> content
    glossary: Dict[str, str] = field(default_factory=dict)  # term -> definition
    metadata: Dict[str, Any] = field(default_factory=dict)
    generated_at: datetime = field(default_factory=datetime.now)
    
    def add_section(self, section: DocSection):
        """Ajoute une section"""
        self.sections.append(section)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertit en dictionnaire"""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "version": self.version,
            "sections": [
                {
                    "id": s.id,
                    "title": s.title,
                    "level": s.level,
                    "diagrams": s.diagrams,
                    "examples": s.examples,
                    "references": s.references
                }
                for s in self.sections
            ],
            "diagrams": self.diagrams,
            "glossary": self.glossary,
            "metadata": self.metadata,
            "generated_at": self.generated_at.isoformat()
        }


# ============================================================================
# GESTIONNAIRE DE QUALITÉ
# ============================================================================

class QualityManager:
    """Gestionnaire de qualité de documentation"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self._quality_metrics = config.get('quality_metrics', {})
        self._validation_rules = config.get('validation_rules', [])
        
    async def validate_document(self, doc_package: DocPackage, 
                               quality_level: QualityLevel) -> Dict[str, Any]:
        """Valide un document selon les critères de qualité"""
        results = {
            "valid": True,
            "score": 0,
            "checks": [],
            "warnings": [],
            "errors": []
        }
        
        # Vérifier la présence des sections requises
        required_sections = self.config.get('documenter', {}).get('documentation_validation', {}).get('required_sections', [])
        present_sections = [s.id for s in doc_package.sections]
        
        for required in required_sections:
            if required not in present_sections:
                results["warnings"].append(f"Section requise manquante: {required}")
                results["valid"] = False
        
        # Vérifier les exemples
        if self.config.get('documenter', {}).get('documentation_validation', {}).get('require_examples', False):
            has_examples = any(len(s.examples) > 0 for s in doc_package.sections)
            if not has_examples:
                results["warnings"].append("Aucun exemple trouvé dans la documentation")
        
        # Vérifier les diagrammes
        if self.config.get('documenter', {}).get('documentation_validation', {}).get('require_diagrams', False):
            if not doc_package.diagrams:
                results["warnings"].append("Aucun diagramme trouvé dans la documentation")
        
        # Calculer le score de qualité
        total_checks = len(required_sections) + 2  # + exemples et diagrammes
        passed_checks = len(required_sections) - len([w for w in results["warnings"] if "Section" in w])
        
        if self.config.get('documenter', {}).get('documentation_validation', {}).get('require_examples', False):
            total_checks += 1
            if has_examples:
                passed_checks += 1
        
        if self.config.get('documenter', {}).get('documentation_validation', {}).get('require_diagrams', False):
            total_checks += 1
            if doc_package.diagrams:
                passed_checks += 1
        
        results["score"] = (passed_checks / max(1, total_checks)) * 100
        
        # Seuil selon niveau de qualité
        thresholds = {
            QualityLevel.DRAFT: 50,
            QualityLevel.STANDARD: 70,
            QualityLevel.PROFESSIONAL: 85,
            QualityLevel.EXCELLENT: 95
        }
        
        threshold = thresholds.get(quality_level, 70)
        if results["score"] < threshold:
            results["valid"] = False
            results["errors"].append(f"Score {results['score']:.1f}% < seuil {threshold}% pour {quality_level.value}")
        
        return results


# ============================================================================
# AGENT PRINCIPAL - DOCUMENTER (ALIGNÉ SUR COMMUNICATION)
# ============================================================================

class DocumenterAgent(BaseAgent):
    """
    Agent de documentation professionnelle
    Gère la génération de documentation technique avec qualité et validation
    Version 2.2 - Alignée sur l'architecture des agents
    """

    def __init__(self, config_path: Optional[str] = None):
        """Initialise l'agent de documentation"""
        if config_path is None:
            config_path = str(project_root / "agents" / "documenter" / "config.yaml")

        # Appel au constructeur parent
        super().__init__(config_path)

        # Configuration spécifique
        agent_config = self._agent_config.get('agent', {})
        self._display_name = agent_config.get('display_name', '📚 Documenter Agent')
        
        # Récupérer la configuration spécifique
        self._doc_config = self._agent_config.get('documenter', {})
        
        # Configuration des chemins
        self._output_path = Path(self._doc_config.get('output_path', './docs'))
        self._temp_path = Path(self._doc_config.get('temp_path', './agents/documenter/temp'))
        self._templates_path = Path(self._doc_config.get('templates_path', './agents/documenter/templates'))
        
        # Configuration LLM
        self._llm_config = self._agent_config.get('llm_config', {})
        
        # Configuration Mermaid
        self._mermaid_config = self._doc_config.get('mermaid', {})
        
        # Configuration des formats supportés
        self._output_formats = self._doc_config.get('output_formats', [])
        
        # Performance targets
        self._perf_targets = self._doc_config.get('performance_targets', {})

        # État interne
        self._requests: Dict[str, DocRequest] = {}  # id -> request
        self._packages: Dict[str, DocPackage] = {}  # id -> package
        
        # Sous-agents
        self._sub_agents: Dict[str, Any] = {}
        self._components: Dict[str, Any] = {}
        self._initialized = False
        
        # Tâches de fond
        self._processor_task: Optional[asyncio.Task] = None
        self._cleanup_task_obj: Optional[asyncio.Task] = None
        self._quality_manager = QualityManager(self._agent_config)

        # Statistiques internes
        self._stats = {
            "docs_generated": 0,
            "docs_failed": 0,
            "docs_validated": 0,
            "diagrams_generated": 0,
            "sections_generated": 0,
            "quality_scores": [],
            "average_quality_score": 0,
            "by_format": defaultdict(int),
            "by_type": defaultdict(int),
            "processing_time_total": 0,
            "processing_time_avg": 0,
            "uptime_start": datetime.now().isoformat()
        }

        # Créer les répertoires nécessaires
        self._create_directories()
        
        self._logger.info("📚 Documenter Agent créé")

    def _create_directories(self):
        """Crée les répertoires nécessaires"""
        for dir_path in [self._output_path, self._temp_path, self._templates_path]:
            dir_path.mkdir(parents=True, exist_ok=True)
        self._logger.debug(f"✅ Répertoires créés: output={self._output_path}, temp={self._temp_path}")

    # ============================================================================
    # CYCLE DE VIE (ALIGNÉ SUR COMMUNICATION)
    # ============================================================================

    async def initialize(self) -> bool:
        """Initialise l'agent"""
        try:
            self._set_status(AgentStatus.INITIALIZING)
            self._logger.info("📚 Initialisation du Documenter Agent...")

            # Appeler l'initialisation du parent
            base_result = await super().initialize()
            if not base_result:
                return False

            # Initialiser les composants
            await self._initialize_components()

            # Initialiser les sous-agents
            await self._initialize_sub_agents()

            # Démarrer les tâches de fond
            self._start_background_tasks()

            self._initialized = True
            self._set_status(AgentStatus.READY)
            self._logger.info("✅ Documenter Agent prêt")
            return True

        except Exception as e:
            self._logger.error(f"❌ Erreur initialisation: {e}")
            self._logger.error(traceback.format_exc())
            self._set_status(AgentStatus.ERROR)
            return False

    async def _initialize_components(self) -> bool:
        """
        Initialise les composants spécifiques.
        Appelé par BaseAgent.initialize().
        """
        try:
            self._logger.info("Initialisation des composants Documenter...")
            
            self._components = {
                "formats": [f.get('name') for f in self._output_formats],
                "diagram_types": [dt.value for dt in DiagramType],
                "llm_enabled": self._llm_config.get('enabled', True),
                "mermaid_enabled": self._mermaid_config.get('enabled', True),
                "quality_validation": self._doc_config.get('quality_metrics', {}).get('enabled', True),
                "sub_agents_count": len(self._sub_agents)
            }

            self._logger.info(f"✅ Composants: {list(self._components.keys())}")
            return True

        except Exception as e:
            self._logger.error(f"Erreur composants: {e}")
            return False

    async def _initialize_sub_agents(self):
        """
        Initialise les sous-agents spécialisés de manière robuste
        """
        self._sub_agents = {}

        try:
            # Lire la config des sous-agents
            sub_agent_configs = self._agent_config.get('subAgents', [])
            
            if not sub_agent_configs:
                # Sous-agents par défaut
                sub_agent_configs = [
                    {"id": "doc_generator", "enabled": True},
                    {"id": "diagram_generator", "enabled": True},
                    {"id": "api_doc_specialist", "enabled": True},
                    {"id": "readme_specialist", "enabled": True},
                    {"id": "contract_analyzer", "enabled": True},
                    {"id": "html_generator", "enabled": True},
                    {"id": "markdown_generator", "enabled": True},
                ]

            for config in sub_agent_configs:
                agent_id = config.get('id')
                
                if not config.get('enabled', True):
                    continue

                try:
                    # Essayer différents chemins possibles
                    module_name = f"agents.documenter.sous_agents.{agent_id}.agent"
                    
                    # Vérifier si le fichier existe
                    module_path = Path(__file__).parent / "sous_agents" / agent_id / "agent.py"
                    if not module_path.exists():
                        self._logger.debug(f"  ℹ️ Sous-agent {agent_id} non développé (fichier manquant)")
                        continue

                    module = importlib.import_module(module_name)
                    
                    class_name = self._get_sub_agent_class_name(agent_id)
                    agent_class = getattr(module, class_name, None)
                    
                    if agent_class:
                        config_path = config.get('config_path', 
                            str(Path(__file__).parent / "sous_agents" / agent_id / "config.yaml"))
                        sub_agent = agent_class(config_path)
                        self._sub_agents[agent_id] = sub_agent
                        self._logger.info(f"  ✓ Sous-agent {agent_id} initialisé")
                    else:
                        self._logger.debug(f"  ℹ️ Classe {class_name} non trouvée pour {agent_id}")

                except ImportError as e:
                    self._logger.debug(f"  ℹ️ Sous-agent {agent_id} non disponible: {e}")
                except Exception as e:
                    self._logger.warning(f"  ⚠️ Erreur initialisation {agent_id}: {e}")

        except Exception as e:
            self._logger.error(f"❌ Erreur globale initialisation sous-agents: {e}")

        self._logger.info(f"✅ Sous-agents chargés: {len(self._sub_agents)}")

    def _get_sub_agent_class_name(self, agent_id: str) -> str:
        """Convertit un ID de sous-agent en nom de classe"""
        parts = agent_id.split('_')
        return ''.join(p.capitalize() for p in parts) + 'SubAgent'

    def _start_background_tasks(self):
        """Démarre les tâches de fond"""
        loop = asyncio.get_event_loop()
        self._processor_task = loop.create_task(self._doc_processor())
        self._cleanup_task_obj = loop.create_task(self._cleanup_worker())
        self._logger.debug("🔄 Tâches de fond démarrées")

    async def _cleanup_worker(self):
        """Nettoie périodiquement les fichiers temporaires"""
        interval = 3600  # 1 heure
        
        self._logger.info("🧹 Tâche de nettoyage démarrée")
        while self._status == AgentStatus.READY:
            try:
                await asyncio.sleep(interval)
                
                # Nettoyer les fichiers temporaires de plus de 7 jours
                if self._temp_path.exists():
                    cutoff = datetime.now() - timedelta(days=7)
                    for temp_file in self._temp_path.glob("*"):
                        try:
                            mtime = datetime.fromtimestamp(temp_file.stat().st_mtime)
                            if mtime < cutoff:
                                if temp_file.is_file():
                                    temp_file.unlink()
                                else:
                                    shutil.rmtree(temp_file)
                                self._logger.debug(f"🧹 Nettoyé: {temp_file}")
                        except Exception as e:
                            self._logger.warning(f"Erreur nettoyage {temp_file}: {e}")
                
                # Nettoyer les vieilles requêtes
                old_requests = []
                now = datetime.now()
                for req_id, req in self._requests.items():
                    if (now - req.created_at).days > 30:
                        old_requests.append(req_id)
                
                for req_id in old_requests:
                    self._requests.pop(req_id, None)
                
                if old_requests:
                    self._logger.debug(f"🧹 Nettoyé {len(old_requests)} vieilles requêtes")
                    
            except asyncio.CancelledError:
                self._logger.info("🛑 Tâche de nettoyage arrêtée")
                break
            except Exception as e:
                self._logger.error(f"Erreur dans cleanup_worker: {e}")

    async def shutdown(self) -> bool:
        """Arrête l'agent proprement"""
        self._logger.info("Arrêt de l'agent Documenter...")
        self._set_status(AgentStatus.SHUTTING_DOWN)

        # Annuler les tâches de fond
        for task in [self._processor_task, self._cleanup_task_obj]:
            if task and not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass

        # Arrêter les sous-agents
        for agent_name, agent_instance in self._sub_agents.items():
            try:
                await agent_instance.shutdown()
                self._logger.debug(f"  ✓ Sous-agent {agent_name} arrêté")
            except Exception as e:
                self._logger.warning(f"  ⚠️ Erreur arrêt sous-agent {agent_name}: {e}")

        # Sauvegarder les statistiques
        await self._save_stats()

        # Appeler la méthode parent
        await super().shutdown()

        self._logger.info("✅ Agent Documenter arrêté")
        return True

    async def pause(self) -> bool:
        """Met l'agent en pause"""
        self._logger.info("Pause de l'agent Documenter...")

        # Mettre en pause les sous-agents
        for agent_name, agent_instance in self._sub_agents.items():
            try:
                await agent_instance.pause()
            except Exception as e:
                self._logger.warning(f"⚠️ Erreur pause sous-agent {agent_name}: {e}")

        self._set_status(AgentStatus.PAUSED)
        return True

    async def resume(self) -> bool:
        """Reprend l'activité"""
        self._logger.info("Reprise de l'agent Documenter...")

        # Reprendre les sous-agents
        for agent_name, agent_instance in self._sub_agents.items():
            try:
                await agent_instance.resume()
            except Exception as e:
                self._logger.warning(f"⚠️ Erreur reprise sous-agent {agent_name}: {e}")

        self._set_status(AgentStatus.READY)
        return True

    async def _save_stats(self):
        """Sauvegarde les statistiques"""
        try:
            stats_file = Path("./reports") / "documenter" / f"stats_{datetime.now().strftime('%Y%m%d')}.json"
            stats_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Calculer les moyennes
            if self._stats["quality_scores"]:
                self._stats["average_quality_score"] = sum(self._stats["quality_scores"]) / len(self._stats["quality_scores"])
            
            with open(stats_file, 'w', encoding='utf-8') as f:
                json.dump({
                    "stats": dict(self._stats),
                    "sub_agents": list(self._sub_agents.keys()),
                    "components": self._components,
                    "timestamp": datetime.now().isoformat()
                }, f, indent=2, default=str)
            self._logger.info(f"✅ Statistiques sauvegardées dans {stats_file}")
        except Exception as e:
            self._logger.warning(f"⚠️ Impossible de sauvegarder: {e}")

    # ============================================================================
    # MÉTHODES DE SANTÉ ET D'INFORMATION (ALIGNÉES SUR COMMUNICATION)
    # ============================================================================

    # ============================================================================
    # MÉTHODES DE SANTÉ ET D'INFORMATION
    # ============================================================================

    async def health_check(self) -> Dict[str, Any]:
        """Vérifie la santé de l'agent"""
        # Calculer l'uptime
        uptime = None
        if self._stats.get('uptime_start'):
            start = datetime.fromisoformat(self._stats['uptime_start'])
            uptime = str(datetime.now() - start)

        # Vérifier la santé des sous-agents
        sub_agents_health = {}
        for agent_name, agent_instance in self._sub_agents.items():
            try:
                if hasattr(agent_instance, 'health_check'):
                    health = await agent_instance.health_check()
                    sub_agents_health[agent_name] = {
                        "status": health.get("status", "unknown"),
                        "ready": health.get("ready", False)
                    }
                else:
                    sub_agents_health[agent_name] = {"status": "unknown", "error": "No health_check method"}
            except Exception as e:
                sub_agents_health[agent_name] = {"status": "error", "error": str(e)}

        try:
            stats = await self.get_stats()
            
            health_status = "healthy"
            issues = []
            
            if stats["docs_failed"] > 10:
                issues.append(f"Taux d'échec élevé: {stats['docs_failed']} échecs")
                health_status = "degraded"
            
            if stats.get("average_quality_score", 0) < 70:
                issues.append(f"Score qualité bas: {stats.get('average_quality_score', 0):.1f}%")
                health_status = "degraded"
            
            # Vérifier si des sous-agents sont en erreur
            for sub_name, sub_health in sub_agents_health.items():
                if sub_health.get("status") == "error":
                    issues.append(f"Sous-agent {sub_name} en erreur")
                    health_status = "degraded"
            
            documenter_specific = {
                "docs_generated": stats["docs_generated"],
                "docs_failed": stats["docs_failed"],
                "average_quality": stats.get("average_quality_score", 0),
                "sub_agents": len(self._sub_agents),
                "sub_agents_health": sub_agents_health,
                "formats": list(stats.get("by_format", {}).keys()),
                "health_status": health_status,
                "issues": issues
            }
            
        except Exception as e:
            self._logger.error(f"Erreur dans health_check: {e}")
            documenter_specific = {"error": str(e)}
            health_status = "degraded"
            issues = [f"Erreur lors de la vérification: {e}"]
        
        return {
            "agent": self.name,
            "display_name": self._display_name,
            "status": self._status.value if hasattr(self._status, 'value') else str(self._status),
            "ready": self._status == AgentStatus.READY,
            "initialized": self._initialized,
            "uptime": uptime,
            "health_status": health_status,
            "issues": issues,
            "documenter_specific": documenter_specific,
            "timestamp": datetime.now().isoformat()
        }

    def get_agent_info(self) -> Dict[str, Any]:
        """Informations de l'agent pour le registre"""
        agent_config = self._agent_config.get('agent', {})
        capabilities = agent_config.get('capabilities', [])
        
        if capabilities and isinstance(capabilities[0], dict):
            capabilities = [cap.get('name') for cap in capabilities if cap.get('name')]

        return {
            "id": self.name,
            "name": "DocumenterAgent",
            "display_name": self._display_name,
            "version": agent_config.get('version', '2.2.0'),
            "description": agent_config.get('description', 'Agent de documentation professionnelle'),
            "status": self._status.value if hasattr(self._status, 'value') else str(self._status),
            "capabilities": capabilities,
            "features": {
                "formats": [f.get('name') for f in self._output_formats],
                "diagram_types": [dt.value for dt in DiagramType],
                "llm_enabled": self._llm_config.get('enabled', True),
                "quality_validation": self._doc_config.get('quality_metrics', {}).get('enabled', True),
                "sub_agents": list(self._sub_agents.keys())
            },
            "stats": {
                "docs_generated": self._stats["docs_generated"],
                "average_quality": round(self._stats.get("average_quality_score", 0), 2),
                "sub_agents": len(self._sub_agents)
            }
        }

    async def get_sub_agents_status(self) -> Dict[str, Any]:
        """Retourne le statut de tous les sous-agents"""
        status = {}
        for agent_name, agent_instance in self._sub_agents.items():
            try:
                health = await agent_instance.health_check()
                status[agent_name] = {
                    "status": health.get("status", "unknown"),
                    "agent_info": agent_instance.get_agent_info() if hasattr(agent_instance, 'get_agent_info') else {}
                }
            except Exception as e:
                status[agent_name] = {
                    "status": "error",
                    "error": str(e)
                }

        return {
            "total_sub_agents": len(self._sub_agents),
            "sub_agents": status
        }

    async def delegate_to_sub_agent(self, task_type: str, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Délègue une tâche à un sous-agent approprié.

        Args:
            task_type: Type de tâche à déléguer
            task_data: Données de la tâche

        Returns:
            Résultat de l'exécution par le sous-agent
        """
        # Mapping des types de tâches vers les sous-agents
        sub_agent_mapping = {
            "contract": "contract_analyzer",
            "diagram": "diagram_generator",
            "api": "api_doc_specialist",
            "readme": "readme_specialist",
            "html": "html_generator",
            "markdown": "markdown_generator",
            "doc": "doc_generator"
        }

        for pattern, agent_name in sub_agent_mapping.items():
            if task_type.startswith(pattern):
                if agent_name in self._sub_agents:
                    self._logger.info(f"➡️ Délégation de la tâche {task_type} au sous-agent {agent_name}")
                    # Créer un message pour le sous-agent
                    msg = Message(
                        sender=self.name,
                        recipient=agent_name,
                        content=task_data,
                        message_type=f"documenter.{task_type}",
                        correlation_id=f"delegate_{datetime.now().timestamp()}"
                    )
                    
                    # Vérifier si le sous-agent a une méthode handle_message
                    if hasattr(self._sub_agents[agent_name], 'handle_message'):
                        return await self._sub_agents[agent_name].handle_message(msg)
                    elif hasattr(self._sub_agents[agent_name], 'process'):
                        # Fallback vers une méthode process
                        return await self._sub_agents[agent_name].process(task_data)
                    else:
                        return {"success": False, "error": f"Sous-agent {agent_name} ne supporte pas le traitement"}

        # Fallback: utiliser l'agent principal
        self._logger.info(f"ℹ️ Aucun sous-agent trouvé pour {task_type}, utilisation de l'agent principal")
        
        # Exécuter la tâche localement selon le type
        if task_type == "generate_contract_doc":
            return await self.generate_contract_documentation(
                task_data.get("source_path"),
                task_data.get("format", "html")
            )
        elif task_type == "generate_readme":
            return await self.generate_readme(task_data)
        elif task_type == "generate_api_doc":
            return await self.generate_api_documentation(task_data)
        else:
            return {"success": False, "error": f"Type de tâche non supporté: {task_type}"}

    # ============================================================================
    # API PUBLIQUE - MÉTHODES SPÉCIFIQUES
    # ============================================================================

    async def generate_documentation(self,
                                     doc_type: Union[DocType, str],
                                     source: Union[str, Dict[str, Any]],
                                     output_format: Union[DocFormat, str] = DocFormat.MARKDOWN,
                                     options: Optional[Dict[str, Any]] = None,
                                     quality_level: Union[QualityLevel, str] = QualityLevel.PROFESSIONAL,
                                     **kwargs) -> Dict[str, Any]:
        """
        Génère de la documentation (méthode générique)
        
        Args:
            doc_type: Type de documentation
            source: Source (chemin de fichier ou contenu)
            output_format: Format de sortie
            options: Options de génération
            quality_level: Niveau de qualité souhaité
            **kwargs: Paramètres supplémentaires
            
        Returns:
            Résultat de la génération
        """
        self._logger.info(f"📄 Génération documentation: {doc_type} -> {output_format}")
        
        # Convertir les énumérations si nécessaire
        if isinstance(doc_type, str):
            try:
                doc_type = DocType(doc_type)
            except ValueError:
                doc_type = DocType.CONTRACT
        
        if isinstance(output_format, str):
            try:
                output_format = DocFormat(output_format)
            except ValueError:
                output_format = DocFormat.MARKDOWN
        
        if isinstance(quality_level, str):
            try:
                quality_level = QualityLevel(quality_level)
            except ValueError:
                quality_level = QualityLevel.PROFESSIONAL
        
        # Créer la requête
        request = DocRequest(
            doc_type=doc_type,
            format=output_format,
            quality_level=quality_level,
            options=options or {},
            requester=kwargs.get('requester', self.name),
            correlation_id=kwargs.get('correlation_id'),
            metadata=kwargs.get('metadata', {})
        )
        
        if isinstance(source, str) and os.path.exists(source):
            request.source_path = source
        else:
            request.source_content = source
        
        self._requests[request.id] = request
        
        # Traiter selon le type
        try:
            if doc_type == DocType.CONTRACT:
                result = await self._generate_contract_doc(request)
            elif doc_type == DocType.README:
                result = await self._generate_readme_doc(request)
            elif doc_type == DocType.API:
                result = await self._generate_api_doc(request)
            elif doc_type == DocType.ARCHITECTURE:
                result = await self._generate_architecture_doc(request)
            elif doc_type == DocType.USER_GUIDE:
                result = await self._generate_user_guide(request)
            elif doc_type == DocType.DEVELOPER_GUIDE:
                result = await self._generate_developer_guide(request)
            elif doc_type == DocType.DEPLOYMENT_GUIDE:
                result = await self._generate_deployment_guide(request)
            else:
                result = await self._generate_generic_doc(request)
            
            # Mettre à jour les statistiques
            self._stats["docs_generated"] += 1
            self._stats["by_format"][output_format.value] = self._stats["by_format"].get(output_format.value, 0) + 1
            self._stats["by_type"][doc_type.value] = self._stats["by_type"].get(doc_type.value, 0) + 1
            
            request.status = DocStatus.COMPLETED
            request.completed_at = datetime.now()
            
            return {
                "success": True,
                "request_id": request.id,
                "doc_type": doc_type.value,
                "format": output_format.value,
                "output_path": result.get("output_path"),
                "sections": result.get("sections", 0),
                "diagrams": result.get("diagrams", 0),
                "quality_score": result.get("quality_score"),
                "validation": result.get("validation")
            }
            
        except Exception as e:
            self._logger.error(f"❌ Erreur génération: {e}")
            request.status = DocStatus.FAILED
            self._stats["docs_failed"] += 1
            return {
                "success": False,
                "request_id": request.id,
                "error": str(e),
                "traceback": traceback.format_exc()
            }

    async def generate_contract_documentation(self, 
                                             contract_path: str,
                                             output_format: str = "html",
                                             options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Génère la documentation d'un contrat (méthode spécifique pour rétrocompatibilité)"""
        return await self.generate_documentation(
            doc_type=DocType.CONTRACT,
            source=contract_path,
            output_format=output_format,
            options=options
        )

    async def generate_readme(self, project_info: Dict[str, Any]) -> Dict[str, Any]:
        """Génère un README"""
        return await self.generate_documentation(
            doc_type=DocType.README,
            source=project_info,
            output_format=DocFormat.MARKDOWN
        )

    async def generate_api_documentation(self, api_spec: Dict[str, Any]) -> Dict[str, Any]:
        """Génère une documentation API"""
        return await self.generate_documentation(
            doc_type=DocType.API,
            source=api_spec,
            output_format=DocFormat.OPENAPI
        )

    # ============================================================================
    # MÉTHODES INTERNES DE GÉNÉRATION
    # ============================================================================

    async def _generate_contract_doc(self, request: DocRequest) -> Dict[str, Any]:
        """Génère la documentation d'un contrat"""
        self._logger.info(f"📄 Génération documentation contrat: {request.source_path}")
        
        # Étape 1: Analyser le contrat
        analyzer = self._sub_agents.get("contract_analyzer")
        if not analyzer:
            return {"success": False, "error": "Analyseur non disponible"}
        
        contract_info = await analyzer.analyze_contract(request.source_path)
        
        # Étape 2: Générer les diagrammes
        diagrams = {}
        diagram_agent = self._sub_agents.get("diagram_generator")
        if diagram_agent and request.options.get('generate_diagrams', True):
            diagram_result = await diagram_agent.generate_diagrams(contract_info)
            diagrams = diagram_result.get('diagrams', {})
            self._stats["diagrams_generated"] += len(diagrams)
        
        # Étape 3: Construire le package de documentation
        doc_package = await self._build_doc_package(contract_info, diagrams, request)
        
        # Étape 4: Valider la qualité
        validation = await self._quality_manager.validate_document(doc_package, request.quality_level)
        self._stats["docs_validated"] += 1
        self._stats["quality_scores"].append(validation["score"])
        
        # Étape 5: Générer selon le format
        output_path = await self._render_document(doc_package, request.format, request.options)
        
        # Sauvegarder le package
        self._packages[doc_package.id] = doc_package
        
        return {
            "success": True,
            "output_path": str(output_path) if output_path else None,
            "sections": len(doc_package.sections),
            "diagrams": len(diagrams),
            "quality_score": validation["score"],
            "validation": validation
        }

    async def _generate_readme_doc(self, request: DocRequest) -> Dict[str, Any]:
        """Génère un README"""
        readme_agent = self._sub_agents.get("readme_specialist")
        if readme_agent:
            result = await readme_agent.generate_readme(request.source_content)
            return result
        return {"success": False, "error": "README specialist not available"}

    async def _generate_api_doc(self, request: DocRequest) -> Dict[str, Any]:
        """Génère une documentation API"""
        api_agent = self._sub_agents.get("api_doc_specialist")
        if api_agent:
            result = await api_agent.generate_api_doc(request.source_content)
            return result
        return {"success": False, "error": "API doc specialist not available"}

    async def _generate_architecture_doc(self, request: DocRequest) -> Dict[str, Any]:
        """Génère une documentation d'architecture"""
        # TODO: Implémenter
        return {"success": False, "error": "Architecture doc not implemented"}

    async def _generate_user_guide(self, request: DocRequest) -> Dict[str, Any]:
        """Génère un guide utilisateur"""
        # TODO: Implémenter
        return {"success": False, "error": "User guide not implemented"}

    async def _generate_developer_guide(self, request: DocRequest) -> Dict[str, Any]:
        """Génère un guide développeur"""
        # TODO: Implémenter
        return {"success": False, "error": "Developer guide not implemented"}

    async def _generate_deployment_guide(self, request: DocRequest) -> Dict[str, Any]:
        """Génère un guide de déploiement"""
        # TODO: Implémenter
        return {"success": False, "error": "Deployment guide not implemented"}

    async def _generate_generic_doc(self, request: DocRequest) -> Dict[str, Any]:
        """Génère une documentation générique"""
        doc_agent = self._sub_agents.get("doc_generator")
        if doc_agent:
            result = await doc_agent.generate_documentation(request.source_content, request.options)
            return result
        return {"success": False, "error": "Doc generator not available"}

    async def _build_doc_package(self, contract_info: Dict[str, Any],
                                diagrams: Dict[str, str],
                                request: DocRequest) -> DocPackage:
        """Construit le package de documentation"""
        package = DocPackage(
            title=f"Documentation: {contract_info.get('name', 'Contract')}",
            description=contract_info.get('description', ''),
            version=contract_info.get('version', '1.0.0'),
            diagrams=diagrams,
            metadata={
                "source": request.source_path,
                "generated_by": self.name,
                "quality_level": request.quality_level.value
            }
        )
        
        # Ajouter les sections
        sections = [
            DocSection(
                id="overview",
                title="📋 Overview",
                level=1,
                content=self._generate_overview_content(contract_info),
                examples=contract_info.get('examples', [])
            ),
            DocSection(
                id="functions",
                title="⚙️ Functions",
                level=1,
                content=self._generate_functions_content(contract_info),
                diagrams=["inheritance"] if "inheritance" in diagrams else []
            ),
            DocSection(
                id="events",
                title="📢 Events",
                level=1,
                content=self._generate_events_content(contract_info)
            ),
        ]
        
        if contract_info.get("modifiers"):
            sections.append(
                DocSection(
                    id="modifiers",
                    title="🔒 Modifiers",
                    level=1,
                    content=self._generate_modifiers_content(contract_info)
                )
            )
        
        if contract_info.get("security"):
            sections.append(
                DocSection(
                    id="security",
                    title="🛡️ Security",
                    level=1,
                    content=self._generate_security_content(contract_info)
                )
            )
        
        for section in sections:
            package.add_section(section)
        
        self._stats["sections_generated"] += len(sections)
        
        return package

    async def _render_document(self, package: DocPackage, 
                              format: DocFormat, 
                              options: Dict[str, Any]) -> Optional[Path]:
        """Rend le document dans le format demandé"""
        
        if format == DocFormat.HTML:
            html_agent = self._sub_agents.get("html_generator")
            if html_agent:
                html_content = await html_agent.generate_html(package)
                output_path = self._output_path / f"{package.id}.html"
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(html_content)
                return output_path
                
        elif format == DocFormat.MARKDOWN:
            md_agent = self._sub_agents.get("markdown_generator")
            if md_agent:
                md_content = await md_agent.generate_markdown(package)
                output_path = self._output_path / f"{package.id}.md"
                with open(output_path, 'w', encoding='utf-8') as f:
                    if isinstance(md_content, dict):
                        f.write(json.dumps(md_content, indent=2))
                    else:
                        f.write(str(md_content))
                return output_path
                
        elif format == DocFormat.SITE:
            # Génération d'un site complet
            # TODO: Implémenter
            pass
            
        return None

    # Méthodes de génération de contenu
    def _generate_overview_content(self, info: Dict) -> str:
        """Génère le contenu de la section overview"""
        lines = []
        lines.append(f"# {info.get('name', 'Contract')}")
        lines.append("")
        lines.append(info.get('description', 'No description provided.'))
        lines.append("")
        lines.append(f"**License:** {info.get('license', 'MIT')}")
        lines.append(f"**Version:** {info.get('version', '1.0.0')}")
        if info.get('author'):
            lines.append(f"**Author:** {info.get('author')}")
        return "\n".join(lines)

    def _generate_functions_content(self, info: Dict) -> str:
        """Génère le contenu de la section functions"""
        lines = ["## Functions", ""]
        for func in info.get('functions', []):
            lines.append(f"### `{func.get('name')}`")
            lines.append("")
            if func.get('description'):
                lines.append(func.get('description'))
                lines.append("")
            if func.get('params'):
                lines.append("**Parameters:**")
                for param in func.get('params', []):
                    lines.append(f"- `{param.get('name')}`: {param.get('type')} - {param.get('description', '')}")
                lines.append("")
            if func.get('returns'):
                lines.append(f"**Returns:** `{func.get('returns')}`")
                lines.append("")
            if func.get('visibility'):
                lines.append(f"**Visibility:** `{func.get('visibility')}`")
                lines.append("")
            lines.append("---")
            lines.append("")
        return "\n".join(lines)

    def _generate_events_content(self, info: Dict) -> str:
        """Génère le contenu de la section events"""
        lines = ["## Events", ""]
        for event in info.get('events', []):
            lines.append(f"### `{event.get('name')}`")
            lines.append("")
            if event.get('description'):
                lines.append(event.get('description'))
                lines.append("")
            if event.get('params'):
                lines.append("**Parameters:**")
                for param in event.get('params', []):
                    lines.append(f"- `{param.get('name')}`: {param.get('type')} - {param.get('description', '')}")
                lines.append("")
            lines.append("---")
            lines.append("")
        return "\n".join(lines)

    def _generate_modifiers_content(self, info: Dict) -> str:
        """Génère le contenu de la section modifiers"""
        lines = ["## Modifiers", ""]
        for mod in info.get('modifiers', []):
            lines.append(f"### `{mod.get('name')}`")
            lines.append("")
            if mod.get('description'):
                lines.append(mod.get('description'))
                lines.append("")
            lines.append("---")
            lines.append("")
        return "\n".join(lines)

    def _generate_security_content(self, info: Dict) -> str:
        """Génère le contenu de la section security"""
        lines = ["## Security Considerations", ""]
        for sec in info.get('security', []):
            lines.append(f"### {sec.get('title', 'Security')}")
            lines.append("")
            lines.append(sec.get('description', ''))
            lines.append("")
            if sec.get('recommendations'):
                lines.append("**Recommendations:**")
                for rec in sec.get('recommendations', []):
                    lines.append(f"- {rec}")
                lines.append("")
        return "\n".join(lines)

    # ============================================================================
    # TÂCHES DE FOND
    # ============================================================================

    async def _doc_processor(self):
        """Tâche de traitement des requêtes de documentation"""
        self._logger.info("🔄 Processeur de documentation démarré")
        
        while self._status == AgentStatus.READY:
            try:
                # Traiter les requêtes en attente
                pending_requests = [r for r in self._requests.values() 
                                   if r.status == DocStatus.PENDING]
                
                for req in pending_requests[:5]:  # Traiter 5 à la fois
                    req.status = DocStatus.GENERATING
                    # Le traitement réel est fait dans les méthodes appelées
                
                await asyncio.sleep(1)
                    
            except asyncio.CancelledError:
                self._logger.info("🛑 Processeur de documentation arrêté")
                break
            except Exception as e:
                self._logger.error(f"Erreur dans le processeur: {e}")
                await asyncio.sleep(5)

    # ============================================================================
    # STATISTIQUES ET MONITORING
    # ============================================================================

    async def get_stats(self) -> Dict[str, Any]:
        """Retourne les statistiques de documentation"""
        stats = dict(self._stats)
        
        # Convertir les defaultdict en dict
        stats["by_format"] = dict(stats["by_format"])
        stats["by_type"] = dict(stats["by_type"])
        
        # Calculer la moyenne
        if stats["quality_scores"]:
            stats["average_quality_score"] = sum(stats["quality_scores"]) / len(stats["quality_scores"])
        
        # Statistiques supplémentaires
        stats["pending_requests"] = len([r for r in self._requests.values() 
                                        if r.status == DocStatus.PENDING])
        stats["total_requests"] = len(self._requests)
        stats["packages_generated"] = len(self._packages)
        stats["sub_agents_count"] = len(self._sub_agents)
        
        return stats

    # ============================================================================
    # GESTION DES MESSAGES (hérités de BaseAgent)
    # ============================================================================

    async def _handle_custom_message(self, message: Message) -> Optional[Message]:
        """Gère les messages personnalisés"""
        try:
            msg_type = message.message_type
            self._logger.debug(f"Message personnalisé reçu: {msg_type} de {message.sender}")

            # D'abord, essayer de déléguer à un sous-agent
            if message.content and "sub_agent" in message.content:
                sub_agent_id = message.content.get("sub_agent")
                if sub_agent_id in self._sub_agents:
                    result = await self._sub_agents[sub_agent_id].handle_message(message)
                    return result

            # Handlers standards
            handlers = {
                "documenter.generate": self._handle_generate_request,
                "documenter.generate_contract": self._handle_generate_contract,
                "documenter.generate_readme": self._handle_generate_readme,
                "documenter.generate_api": self._handle_generate_api,
                "documenter.stats": self._handle_stats_request,
                "documenter.health": self._handle_health_request,
                "documenter.sub_agents_status": self._handle_sub_agents_status,
                "documenter.pause": self._handle_pause,
                "documenter.resume": self._handle_resume,
                "documenter.shutdown": self._handle_shutdown,
            }

            if msg_type in handlers:
                return await handlers[msg_type](message)

            self._logger.warning(f"Aucun handler pour le type: {msg_type}")
            return None

        except Exception as e:
            self._logger.error(f"Erreur traitement message: {e}")
            return Message(
                sender=self.name,
                recipient=message.sender,
                content={"error": str(e), "traceback": traceback.format_exc()},
                message_type=MessageType.ERROR.value,
                correlation_id=message.message_id
            )

    async def _handle_generate_request(self, message: Message) -> Message:
        """Gère une requête de génération générique"""
        content = message.content
        result = await self.generate_documentation(
            doc_type=content.get("doc_type", "contract"),
            source=content.get("source"),
            output_format=content.get("format", "markdown"),
            options=content.get("options", {}),
            quality_level=content.get("quality_level", "professional"),
            requester=message.sender,
            correlation_id=message.message_id,
            metadata=content.get("metadata", {})
        )
        return Message(
            sender=self.name,
            recipient=message.sender,
            content=result,
            message_type="documenter.generate_response",
            correlation_id=message.message_id
        )

    async def _handle_generate_contract(self, message: Message) -> Message:
        """Gère la génération de documentation contrat"""
        content = message.content
        result = await self.generate_contract_documentation(
            contract_path=content.get("contract_path"),
            output_format=content.get("format", "html"),
            options=content.get("options")
        )
        return Message(
            sender=self.name,
            recipient=message.sender,
            content=result,
            message_type="documenter.generate_contract_response",
            correlation_id=message.message_id
        )

    async def _handle_generate_readme(self, message: Message) -> Message:
        """Gère la génération de README"""
        result = await self.generate_readme(message.content)
        return Message(
            sender=self.name,
            recipient=message.sender,
            content=result,
            message_type="documenter.generate_readme_response",
            correlation_id=message.message_id
        )

    async def _handle_generate_api(self, message: Message) -> Message:
        """Gère la génération de documentation API"""
        result = await self.generate_api_documentation(message.content)
        return Message(
            sender=self.name,
            recipient=message.sender,
            content=result,
            message_type="documenter.generate_api_response",
            correlation_id=message.message_id
        )

    async def _handle_stats_request(self, message: Message) -> Message:
        """Gère la demande de statistiques"""
        stats = await self.get_stats()
        return Message(
            sender=self.name,
            recipient=message.sender,
            content=stats,
            message_type="documenter.stats_response",
            correlation_id=message.message_id
        )

    async def _handle_health_request(self, message: Message) -> Message:
        """Gère la demande de santé"""
        health = await self.health_check()
        return Message(
            sender=self.name,
            recipient=message.sender,
            content=health,
            message_type="documenter.health_response",
            correlation_id=message.message_id
        )

    async def _handle_sub_agents_status(self, message: Message) -> Message:
        """Gère la récupération du statut des sous-agents"""
        status = await self.get_sub_agents_status()
        return Message(
            sender=self.name,
            recipient=message.sender,
            content=status,
            message_type="documenter.sub_agents_status_response",
            correlation_id=message.message_id
        )

    async def _handle_pause(self, message: Message) -> Message:
        """Gère la pause"""
        await self.pause()
        return Message(
            sender=self.name,
            recipient=message.sender,
            content={"status": "paused"},
            message_type="documenter.status_update",
            correlation_id=message.message_id
        )

    async def _handle_resume(self, message: Message) -> Message:
        """Gère la reprise"""
        await self.resume()
        return Message(
            sender=self.name,
            recipient=message.sender,
            content={"status": "resumed"},
            message_type="documenter.status_update",
            correlation_id=message.message_id
        )

    async def _handle_shutdown(self, message: Message) -> Message:
        """Gère l'arrêt"""
        await self.shutdown()
        return Message(
            sender=self.name,
            recipient=message.sender,
            content={"status": "shutdown"},
            message_type="documenter.status_update",
            correlation_id=message.message_id
        )


# ============================================================================
# FONCTIONS D'USINE
# ============================================================================

def create_documenter_agent(config_path: Optional[str] = None) -> DocumenterAgent:
    """Crée une instance de l'agent documenter"""
    return DocumenterAgent(config_path)


def get_agent_class():
    """Retourne la classe de l'agent pour le registre"""
    return DocumenterAgent


# ============================================================================
# POINT D'ENTRÉE POUR EXÉCUTION DIRECTE
# ============================================================================

if __name__ == "__main__":
    async def main():
        print("📚 TEST DOCUMENTER AGENT")
        print("="*60)
        
        agent = DocumenterAgent()
        await agent.initialize()
        
        agent_info = agent.get_agent_info()
        print(f"✅ Agent: {agent_info['name']} v{agent_info['version']}")
        print(f"✅ Statut: {agent_info['status']}")
        print(f"✅ Formats: {agent_info['features']['formats']}")
        print(f"✅ Sous-agents: {agent_info['features']['sub_agents']}")
        
        # Test simple
        print(f"\n📄 Test génération...")
        
        # Créer un contrat factice pour le test
        test_contract = {
            "name": "TestContract",
            "description": "A test contract for documentation",
            "version": "1.0.0",
            "license": "MIT",
            "functions": [
                {
                    "name": "transfer",
                    "description": "Transfer tokens to another address",
                    "params": [
                        {"name": "to", "type": "address", "description": "Recipient address"},
                        {"name": "amount", "type": "uint256", "description": "Amount to transfer"}
                    ],
                    "returns": "bool",
                    "visibility": "public"
                }
            ],
            "events": [
                {
                    "name": "Transfer",
                    "description": "Emitted when tokens are transferred",
                    "params": [
                        {"name": "from", "type": "address", "description": "Sender address"},
                        {"name": "to", "type": "address", "description": "Recipient address"},
                        {"name": "value", "type": "uint256", "description": "Amount transferred"}
                    ]
                }
            ]
        }
        
        # Sauvegarder temporairement
        test_file = agent._temp_path / "test_contract.json"
        with open(test_file, 'w') as f:
            json.dump(test_contract, f)
        
        # Tester la génération
        result = await agent.generate_contract_documentation(
            contract_path=str(test_file),
            output_format="markdown"
        )
        print(f"✅ Résultat: {result}")
        
        # Statistiques
        stats = await agent.get_stats()
        print(f"\n📊 Statistiques:")
        print(f"  Documents générés: {stats['docs_generated']}")
        print(f"  Sections générées: {stats['sections_generated']}")
        print(f"  Diagrammes générés: {stats['diagrams_generated']}")
        print(f"  Score qualité: {stats['average_quality_score']:.1f}%")
        
        health = await agent.health_check()
        print(f"\n❤️  Health: {health['status']}")
        
        print("\n" + "="*60)
        print("✅ DOCUMENTER AGENT OPÉRATIONNEL")
        print("="*60)
        
        await agent.shutdown()
    
    asyncio.run(main())
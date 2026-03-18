#!/usr/bin/env python3
"""
DocGenerator SubAgent - Générateur de documentation générale
Version: 2.2.0 (ALIGNÉ SUR COMMUNICATION)
"""

import os
import sys
import json
import asyncio
import time
import traceback
from collections import defaultdict
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from enum import Enum
from dataclasses import dataclass, field
from uuid import uuid4

project_root = Path(__file__).parent.parent.parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from agents.sous_agents.base_subagent import BaseSubAgent
from agents.base_agent.base_agent import Message, MessageType


class DocType(Enum):
    """Types de documents supportés"""
    GENERAL = "general"
    TECHNICAL = "technical"
    API = "api"
    USER_GUIDE = "user_guide"


class ProcessingStatus(Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class GenerationTask:
    id: str = field(default_factory=lambda: str(uuid4()))
    doc_type: DocType = DocType.GENERAL
    content: Any = None
    format: str = "markdown"
    options: Dict[str, Any] = field(default_factory=dict)
    status: ProcessingStatus = ProcessingStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    output_path: Optional[str] = None
    requester: str = ""
    correlation_id: Optional[str] = None


class DocGeneratorSubAgent(BaseSubAgent):
    """
    Sous-agent spécialisé dans la génération de documentation générale
    Version 2.2 - Aligné sur l'architecture Communication
    """

    def __init__(self, config_path: Optional[str] = None):
        super().__init__(config_path)
        
        subagent_config = self._config.get('subagent', {})
        self._display_name = subagent_config.get('display_name', '📄 Générateur de Documentation')
        
        self._tasks: Dict[str, GenerationTask] = {}
        self._initialized = False
        
        # Templates disponibles
        self._templates = self._load_templates()
        
        self._stats = {
            "documents_generated": 0,
            "documents_failed": 0,
            "formats_used": defaultdict(int),
            "processing_time_total": 0,
            "processing_time_avg": 0,
            "uptime_start": datetime.now().isoformat()
        }
        
        self._logger.info(f"{self._display_name} créé")

    def _load_templates(self) -> Dict[str, str]:
        """Charge les templates disponibles"""
        templates_path = Path(__file__).parent / "templates"
        templates = {}
        if templates_path.exists():
            for template_file in templates_path.glob("*.md"):
                try:
                    with open(template_file, 'r', encoding='utf-8') as f:
                        templates[template_file.stem] = f.read()
                except Exception as e:
                    self._logger.warning(f"Impossible de charger {template_file}: {e}")
        return templates

    async def _initialize_subagent_components(self) -> bool:
        try:
            self._logger.info("Initialisation des composants DocGenerator...")
            
            self._components = {
                "version": "2.2.0",
                "templates": list(self._templates.keys()),
                "supported_formats": ["markdown", "html", "text"],
                "max_document_size_mb": 10
            }

            self._logger.info(f"✅ Composants: {list(self._components.keys())}")
            return True
        except Exception as e:
            self._logger.error(f"Erreur composants: {e}")
            return False

    async def _initialize_components(self) -> bool:
        return await self._initialize_subagent_components()

    def _get_capability_handlers(self) -> Dict[str, str]:
        return {
            "generate_documentation": "handle_generate_documentation",
            "generate_from_template": "handle_generate_from_template",
            "validate_document": "handle_validate_document",
            "get_templates": "handle_get_templates",
            "format_document": "handle_format_document"
        }

    def _get_features(self) -> Dict[str, Any]:
        return {
            "templates_available": list(self._templates.keys()),
            "formats": ["markdown", "html", "text"],
            "max_size_mb": 10,
            "supports_custom_templates": True,
            "validation_enabled": True
        }

    async def initialize(self) -> bool:
        try:
            self._logger.info(f"Initialisation de {self._display_name}...")
            
            base_result = await super().initialize()
            if not base_result:
                return False

            self._initialized = True
            self._logger.info(f"✅ {self._display_name} prêt")
            return True
        except Exception as e:
            self._logger.error(f"❌ Erreur initialisation: {e}")
            return False

    async def shutdown(self) -> bool:
        self._logger.info(f"Arrêt de {self._display_name}...")
        await self._save_stats()
        
        # Appeler super().shutdown() mais ignorer son retour
        try:
            await super().shutdown()
        except Exception:
            pass  # Ignorer toute erreur
        
        return True

    async def _save_stats(self):
        try:
            stats_file = Path("./reports") / "documenter" / "doc_generator" / f"stats_{datetime.now().strftime('%Y%m%d')}.json"
            stats_file.parent.mkdir(parents=True, exist_ok=True)
            with open(stats_file, 'w', encoding='utf-8') as f:
                json.dump({
                    "stats": dict(self._stats),
                    "components": self._components,
                    "timestamp": datetime.now().isoformat()
                }, f, indent=2, default=str)
        except Exception as e:
            self._logger.warning(f"⚠️ Impossible de sauvegarder: {e}")

    async def health_check(self) -> Dict[str, Any]:
        uptime = None
        if self._stats.get('uptime_start'):
            start = datetime.fromisoformat(self._stats['uptime_start'])
            uptime = str(datetime.now() - start)

        success_rate = 0
        total = self._stats["documents_generated"] + self._stats["documents_failed"]
        if total > 0:
            success_rate = (self._stats["documents_generated"] / total) * 100

        return {
            "status": self._status,
            "ready": self._initialized,
            "display_name": self._display_name,
            "uptime": uptime,
            "stats": {
                "documents_generated": self._stats["documents_generated"],
                "documents_failed": self._stats["documents_failed"],
                "success_rate": round(success_rate, 2),
                "formats_used": dict(self._stats["formats_used"]),
                "processing_time_avg": round(self._stats["processing_time_avg"], 3)
            },
            "components": self._components,
            "timestamp": datetime.now().isoformat()
        }

    def get_agent_info(self) -> Dict[str, Any]:
        return {
            "id": "DocGeneratorSubAgent",
            "name": self._display_name,
            "version": "2.2.0",
            "status": self._status,
            "capabilities": list(self._get_capability_handlers().keys()),
            "features": self._get_features(),
            "stats": {
                "documents_generated": self._stats["documents_generated"],
                "success_rate": round(
                    (self._stats["documents_generated"] / max(1, self._stats["documents_generated"] + self._stats["documents_failed"])) * 100, 2
                )
            }
        }

    async def get_stats(self) -> Dict[str, Any]:
        return {
            **self._stats,
            "pending_tasks": len([t for t in self._tasks.values() if t.status == ProcessingStatus.PENDING]),
            "total_tasks": len(self._tasks),
            "templates_count": len(self._templates)
        }

    # ============================================================================
    # HANDLERS PRINCIPAUX
    # ============================================================================

    async def generate_documentation(self, content: Any, format: str = "markdown", options: Dict = None) -> Dict[str, Any]:
        """Génère de la documentation"""
        start_time = time.time()
        
        try:
            options = options or {}
            
            # Appliquer le template si spécifié
            if options.get("template") and options["template"] in self._templates:
                template = self._templates[options["template"]]
                result = template.replace("{{content}}", str(content))
            else:
                # Génération basique
                if format == "markdown":
                    result = self._generate_markdown(content, options)
                elif format == "html":
                    result = self._generate_html(content, options)
                else:
                    result = str(content)
            
            # Mettre à jour les stats
            processing_time = time.time() - start_time
            self._stats["documents_generated"] += 1
            self._stats["formats_used"][format] += 1
            self._stats["processing_time_total"] += processing_time
            self._stats["processing_time_avg"] = self._stats["processing_time_total"] / self._stats["documents_generated"]
            
            return {
                "success": True,
                "content": result,
                "format": format,
                "size": len(result),
                "processing_time": processing_time
            }
            
        except Exception as e:
            self._stats["documents_failed"] += 1
            return {
                "success": False,
                "error": str(e)
            }

    def _generate_markdown(self, content: Any, options: Dict) -> str:
        """Génère du contenu Markdown"""
        lines = []
        
        if options.get("title"):
            lines.append(f"# {options['title']}")
            lines.append("")
        
        if isinstance(content, dict):
            for key, value in content.items():
                lines.append(f"## {key}")
                lines.append("")
                lines.append(str(value))
                lines.append("")
        else:
            lines.append(str(content))
        
        return "\n".join(lines)

    def _generate_html(self, content: Any, options: Dict) -> str:
        """Génère du contenu HTML"""
        title = options.get("title", "Documentation")
        body = str(content).replace("\n", "<br>")
        
        return f"""<!DOCTYPE html>
<html>
<head>
    <title>{title}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }}
        h1 {{ color: #333; }}
    </style>
</head>
<body>
    <h1>{title}</h1>
    <div>{body}</div>
</body>
</html>"""

    async def generate_from_template(self, template_name: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Génère un document à partir d'un template"""
        if template_name not in self._templates:
            return {"success": False, "error": f"Template '{template_name}' non trouvé"}
        
        template = self._templates[template_name]
        result = template
        for key, value in data.items():
            result = result.replace(f"{{{{{key}}}}}", str(value))
        
        return {
            "success": True,
            "content": result,
            "template": template_name
        }

    async def validate_document(self, content: str, rules: Dict = None) -> Dict[str, Any]:
        """Valide un document"""
        rules = rules or {}
        issues = []
        
        # Vérifications basiques
        if rules.get("min_length") and len(content) < rules["min_length"]:
            issues.append(f"Longueur minimale: {len(content)} < {rules['min_length']}")
        
        if rules.get("max_length") and len(content) > rules["max_length"]:
            issues.append(f"Longueur maximale: {len(content)} > {rules['max_length']}")
        
        if rules.get("required_sections"):
            for section in rules["required_sections"]:
                if f"#{section}" not in content and section.lower() not in content.lower():
                    issues.append(f"Section requise manquante: {section}")
        
        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "length": len(content)
        }

    async def handle_generate_documentation(self, message: Message) -> Message:
        """Handler pour generate_documentation"""
        content = message.content
        result = await self.generate_documentation(
            content.get("data"),
            content.get("format", "markdown"),
            content.get("options", {})
        )
        return Message(
            sender=self.__class__.__name__,
            recipient=message.sender,
            content=result,
            message_type="doc_generated",
            correlation_id=message.message_id
        )

    async def handle_generate_from_template(self, message: Message) -> Message:
        """Handler pour generate_from_template"""
        content = message.content
        result = await self.generate_from_template(
            content.get("template"),
            content.get("data", {})
        )
        return Message(
            sender=self.__class__.__name__,
            recipient=message.sender,
            content=result,
            message_type="template_generated",
            correlation_id=message.message_id
        )

    async def handle_validate_document(self, message: Message) -> Message:
        """Handler pour validate_document"""
        content = message.content
        result = await self.validate_document(
            content.get("content", ""),
            content.get("rules", {})
        )
        return Message(
            sender=self.__class__.__name__,
            recipient=message.sender,
            content=result,
            message_type="doc_validated",
            correlation_id=message.message_id
        )

    async def handle_get_templates(self, message: Message) -> Message:
        """Handler pour get_templates"""
        return Message(
            sender=self.__class__.__name__,
            recipient=message.sender,
            content={
                "templates": list(self._templates.keys()),
                "count": len(self._templates)
            },
            message_type="templates_list",
            correlation_id=message.message_id
        )

    async def handle_format_document(self, message: Message) -> Message:
        """Handler pour format_document"""
        content = message.content
        # Réutiliser generate_documentation
        result = await self.generate_documentation(
            content.get("content"),
            content.get("format", "markdown"),
            {"title": content.get("title")}
        )
        return Message(
            sender=self.__class__.__name__,
            recipient=message.sender,
            content=result,
            message_type="doc_formatted",
            correlation_id=message.message_id
        )

    async def handle_message(self, message: Message) -> Optional[Message]:
        """Point d'entrée principal pour les messages"""
        start_time = time.time()
        
        try:
            msg_type = message.message_type
            self._logger.debug(f"📨 Message reçu: {msg_type}")

            handlers = self._get_capability_handlers()
            
            if msg_type in handlers:
                handler_name = handlers[msg_type]
                handler = getattr(self, handler_name, None)
                
                if handler:
                    return await handler(message)
                else:
                    return Message(
                        sender=self.__class__.__name__,
                        recipient=message.sender,
                        content={"error": f"Handler {handler_name} non implémenté"},
                        message_type=MessageType.ERROR.value,
                        correlation_id=message.message_id
                    )
            else:
                return Message(
                    sender=self.__class__.__name__,
                    recipient=message.sender,
                    content={"error": f"Type non supporté: {msg_type}"},
                    message_type=MessageType.ERROR.value,
                    correlation_id=message.message_id
                )

        except Exception as e:
            self._logger.error(f"❌ Erreur: {e}")
            return Message(
                sender=self.__class__.__name__,
                recipient=message.sender,
                content={"error": str(e)},
                message_type=MessageType.ERROR.value,
                correlation_id=message.message_id
            )
#!/usr/bin/env python3
"""
MarkdownGenerator SubAgent - Générateur Markdown
Version: 2.2.0 (ALIGNÉ SUR COMMUNICATION)
"""

import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
import time
import json
import re

project_root = Path(__file__).parent.parent.parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from agents.sous_agents.base_subagent import BaseSubAgent
from agents.base_agent.base_agent import Message, MessageType


class MarkdownGeneratorSubAgent(BaseSubAgent):
    """
    Sous-agent spécialisé dans la génération de documentation Markdown
    Version 2.2 - Aligné sur l'architecture Communication
    """

    def __init__(self, config_path: Optional[str] = None):
        super().__init__(config_path)
        
        subagent_config = self._config.get('subagent', {})
        self._display_name = subagent_config.get('display_name', '📝 Générateur Markdown')
        
        self._initialized = False
        self._docs_generated = 0
        self._docs_failed = 0
        
        self._templates = self._load_templates()
        self._styles = self._load_styles()
        
        self._stats = {
            "docs_generated": 0,
            "docs_failed": 0,
            "by_style": {},
            "processing_time_total": 0,
            "processing_time_avg": 0,
            "uptime_start": datetime.now().isoformat()
        }
        
        self._logger.info(f"{self._display_name} créé")

    def _load_templates(self) -> Dict[str, str]:
        """Charge les templates Markdown"""
        return {
            "basic": """# {title}

{description}

{content}

---
*Généré le {date}*
""",
            "documentation": """# {title}

{description}

## Table des matières
{toc}

## Documentation

{content}

---
**Version:** {version}  
**Dernière mise à jour:** {date}
""",
            "api": """# {title} - API Reference

{description}

## Base URL
`{base_url}`

## Endpoints
{endpoints}

## Models
{models}

---
**Version:** {version}
"""
        }

    def _load_styles(self) -> Dict[str, Dict[str, str]]:
        """Charge les styles de formatage"""
        return {
            "clean": {
                "heading1": "# {text}",
                "heading2": "## {text}",
                "heading3": "### {text}",
                "code_block": "```{language}\n{code}\n```",
                "inline_code": "`{code}`",
                "bold": "**{text}**",
                "italic": "*{text}*",
                "list_item": "- {text}",
                "table_separator": "|---"
            },
            "github": {
                "heading1": "# {text}",
                "heading2": "## {text}",
                "heading3": "### {text}",
                "code_block": "```{language}\n{code}\n```",
                "inline_code": "`{code}`",
                "bold": "**{text}**",
                "italic": "*{text}*",
                "list_item": "- {text}",
                "task_item": "- [ ] {text}",
                "table_separator": "| ---"
            },
            "extended": {
                "heading1": "# {text}",
                "heading2": "## {text}",
                "heading3": "### {text}",
                "heading4": "#### {text}",
                "code_block": "```{language}\n{code}\n```",
                "inline_code": "`{code}`",
                "bold": "**{text}**",
                "italic": "*{text}*",
                "list_item": "- {text}",
                "numbered_item": "1. {text}",
                "quote": "> {text}",
                "hr": "---",
                "table_separator": "| ---"
            }
        }

    async def _initialize_subagent_components(self) -> bool:
        try:
            self._components = {
                "version": "2.2.0",
                "templates": list(self._templates.keys()),
                "styles": list(self._styles.keys()),
                "supports_mermaid": True,
                "supports_tables": True,
                "supports_toc": True
            }
            return True
        except Exception as e:
            self._logger.error(f"Erreur composants: {e}")
            return False

    async def _initialize_components(self) -> bool:
        return await self._initialize_subagent_components()

    def _get_capability_handlers(self) -> Dict[str, str]:
        return {
            "generate_markdown": "handle_generate_markdown",
            "generate_from_package": "handle_generate_from_package",
            "generate_toc": "handle_generate_toc",
            "generate_tables": "handle_generate_tables",
            "embed_diagrams": "handle_embed_diagrams",
            "convert_to_html": "handle_convert_to_html",
            "get_templates": "handle_get_templates",
            "get_styles": "handle_get_styles"
        }

    def _get_features(self) -> Dict[str, Any]:
        return {
            "templates": list(self._templates.keys()),
            "styles": list(self._styles.keys()),
            "supports_mermaid": True,
            "supports_tables": True,
            "supports_toc": True,
            "supports_code_blocks": True,
            "max_sections": 50
        }

    async def generate_markdown(self, content: Any, template: str = "basic", style: str = "github") -> Dict[str, Any]:
        """Génère du Markdown à partir de contenu"""
        start_time = time.time()
        
        try:
            if template not in self._templates:
                template = "basic"
            
            template_str = self._templates[template]
            style_config = self._styles.get(style, self._styles["github"])
            
            # Traiter le contenu selon son type
            if isinstance(content, dict):
                markdown_content = self._dict_to_markdown(content, style_config)
            elif isinstance(content, list):
                markdown_content = self._list_to_markdown(content, style_config)
            else:
                markdown_content = str(content)
            
            data = {
                "title": "Documentation",
                "description": "",
                "content": markdown_content,
                "toc": "",
                "date": datetime.now().strftime("%d/%m/%Y"),
                "version": "1.0.0",
                "base_url": "https://api.example.com",
                "endpoints": "",
                "models": ""
            }
            
            # Générer la table des matières si demandée
            if template == "documentation":
                sections = self._extract_sections(markdown_content)
                toc_result = await self.generate_toc(sections)
                if toc_result["success"]:
                    data["toc"] = toc_result["toc"]
            
            markdown = template_str.format(**data)
            
            processing_time = time.time() - start_time
            self._docs_generated += 1
            self._stats["docs_generated"] += 1
            self._stats["by_style"][style] = self._stats["by_style"].get(style, 0) + 1
            self._stats["processing_time_total"] += processing_time
            self._stats["processing_time_avg"] = self._stats["processing_time_total"] / self._stats["docs_generated"]
            
            return {
                "success": True,
                "markdown": markdown,
                "template": template,
                "style": style,
                "size": len(markdown),
                "processing_time": processing_time
            }
            
        except Exception as e:
            self._docs_failed += 1
            self._stats["docs_failed"] += 1
            return {"success": False, "error": str(e)}

    def _dict_to_markdown(self, data: Dict, style: Dict, level: int = 1) -> str:
        """Convertit un dictionnaire en Markdown"""
        lines = []
        
        for key, value in data.items():
            # Titre pour la clé
            heading = style[f"heading{min(level, 3)}"].format(text=str(key).replace('_', ' ').title())
            lines.append(heading)
            lines.append("")
            
            # Valeur
            if isinstance(value, dict):
                lines.append(self._dict_to_markdown(value, style, level + 1))
            elif isinstance(value, list):
                lines.append(self._list_to_markdown(value, style))
            else:
                lines.append(str(value))
                lines.append("")
        
        return "\n".join(lines)

    def _list_to_markdown(self, items: List, style: Dict) -> str:
        """Convertit une liste en Markdown"""
        lines = []
        
        for item in items:
            if isinstance(item, dict):
                lines.append(self._dict_to_markdown(item, style))
            elif isinstance(item, list):
                lines.append(self._list_to_markdown(item, style))
            else:
                lines.append(style["list_item"].format(text=str(item)))
        
        return "\n".join(lines)

    async def generate_from_package(self, package: Any, style: str = "github") -> Dict[str, Any]:
        """Génère du Markdown à partir d'un package de documentation"""
        try:
            style_config = self._styles.get(style, self._styles["github"])
            lines = []
            
            # Titre principal
            title = getattr(package, 'title', 'Documentation')
            lines.append(style_config["heading1"].format(text=title))
            lines.append("")
            
            # Description
            description = getattr(package, 'description', '')
            if description:
                lines.append(description)
                lines.append("")
            
            # Sections
            if hasattr(package, 'sections'):
                for section in package.sections:
                    section_title = getattr(section, 'title', 'Section')
                    level = getattr(section, 'level', 1)
                    content = getattr(section, 'content', '')
                    
                    heading = style_config[f"heading{min(level, 3)}"].format(text=section_title)
                    lines.append(heading)
                    lines.append("")
                    lines.append(content)
                    lines.append("")
            
            # Diagrammes
            if hasattr(package, 'diagrams') and package.diagrams:
                lines.append(style_config["heading2"].format(text="Diagrammes"))
                lines.append("")
                for name, diagram in package.diagrams.items():
                    lines.append(style_config["heading3"].format(text=name))
                    lines.append("")
                    lines.append(style_config["code_block"].format(language="mermaid", code=diagram))
                    lines.append("")
            
            markdown = "\n".join(lines)
            
            return {
                "success": True,
                "markdown": markdown,
                "sections": len(getattr(package, 'sections', [])),
                "diagrams": len(getattr(package, 'diagrams', {}))
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def generate_toc(self, sections: List[str]) -> Dict[str, Any]:
        """Génère une table des matières"""
        try:
            toc_lines = ["## Table des matières", ""]
            
            for section in sections:
                # Créer un anchor
                anchor = section.lower()
                anchor = re.sub(r'[^\w\s-]', '', anchor)
                anchor = re.sub(r'[-\s]+', '-', anchor)
                
                toc_lines.append(f"- [{section}](#{anchor})")
            
            return {
                "success": True,
                "toc": "\n".join(toc_lines),
                "sections": len(sections)
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _extract_sections(self, markdown: str) -> List[str]:
        """Extrait les sections d'un document Markdown"""
        sections = []
        lines = markdown.split('\n')
        
        for line in lines:
            if line.startswith('## '):
                section = line[3:].strip()
                sections.append(section)
        
        return sections

    async def generate_tables(self, data: List[List[str]], headers: List[str] = None) -> Dict[str, Any]:
        """Génère un tableau Markdown"""
        try:
            if not data:
                return {"success": False, "error": "Données vides"}
            
            lines = []
            
            # En-têtes
            if headers:
                lines.append("| " + " | ".join(headers) + " |")
                lines.append("|" + "|".join([" --- " for _ in headers]) + "|")
            
            # Données
            for row in data:
                lines.append("| " + " | ".join(str(cell) for cell in row) + " |")
            
            return {
                "success": True,
                "table": "\n".join(lines),
                "rows": len(data),
                "columns": len(headers) if headers else len(data[0]) if data else 0
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def embed_diagrams(self, markdown: str, diagrams: Dict[str, str]) -> Dict[str, Any]:
        """Intègre des diagrammes dans du Markdown existant"""
        try:
            lines = markdown.split('\n')
            result_lines = []
            diagrams_added = 0
            
            for line in lines:
                result_lines.append(line)
                
                # Chercher un marqueur pour insérer les diagrammes
                if line.startswith('## Diagrammes') or line == '<!-- diagrams -->':
                    for name, diagram in diagrams.items():
                        result_lines.append("")
                        result_lines.append(f"### {name}")
                        result_lines.append("")
                        result_lines.append("```mermaid")
                        result_lines.append(diagram)
                        result_lines.append("```")
                        result_lines.append("")
                        diagrams_added += 1
            
            if diagrams_added == 0 and diagrams:
                # Ajouter à la fin si pas de marqueur
                result_lines.append("")
                result_lines.append("## Diagrammes")
                result_lines.append("")
                for name, diagram in diagrams.items():
                    result_lines.append(f"### {name}")
                    result_lines.append("")
                    result_lines.append("```mermaid")
                    result_lines.append(diagram)
                    result_lines.append("```")
                    result_lines.append("")
                    diagrams_added += 1
            
            return {
                "success": True,
                "markdown": "\n".join(result_lines),
                "diagrams_added": diagrams_added
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def convert_to_html(self, markdown: str) -> Dict[str, Any]:
        """Convertit du Markdown en HTML basique"""
        try:
            html_lines = []
            in_code_block = False
            
            for line in markdown.split('\n'):
                if line.startswith('```'):
                    in_code_block = not in_code_block
                    if in_code_block:
                        html_lines.append('<pre><code>')
                    else:
                        html_lines.append('</code></pre>')
                elif in_code_block:
                    html_lines.append(line)
                elif line.startswith('# '):
                    html_lines.append(f'<h1>{line[2:]}</h1>')
                elif line.startswith('## '):
                    html_lines.append(f'<h2>{line[3:]}</h2>')
                elif line.startswith('### '):
                    html_lines.append(f'<h3>{line[4:]}</h3>')
                elif line.startswith('- '):
                    html_lines.append(f'<li>{line[2:]}</li>')
                elif line.strip() == '':
                    html_lines.append('<br>')
                else:
                    html_lines.append(f'<p>{line}</p>')
            
            return {
                "success": True,
                "html": "\n".join(html_lines),
                "lines": len(markdown.split('\n'))
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def handle_generate_markdown(self, message: Message) -> Message:
        content = message.content
        result = await self.generate_markdown(
            content.get("content"),
            content.get("template", "basic"),
            content.get("style", "github")
        )
        return Message(
            sender=self.__class__.__name__,
            recipient=message.sender,
            content=result,
            message_type="markdown_generated",
            correlation_id=message.message_id
        )

    async def handle_generate_from_package(self, message: Message) -> Message:
        content = message.content
        result = await self.generate_from_package(
            content.get("package"),
            content.get("style", "github")
        )
        return Message(
            sender=self.__class__.__name__,
            recipient=message.sender,
            content=result,
            message_type="markdown_from_package",
            correlation_id=message.message_id
        )

    async def handle_generate_toc(self, message: Message) -> Message:
        result = await self.generate_toc(message.content.get("sections", []))
        return Message(
            sender=self.__class__.__name__,
            recipient=message.sender,
            content=result,
            message_type="toc_generated",
            correlation_id=message.message_id
        )

    async def handle_generate_tables(self, message: Message) -> Message:
        content = message.content
        result = await self.generate_tables(
            content.get("data", []),
            content.get("headers")
        )
        return Message(
            sender=self.__class__.__name__,
            recipient=message.sender,
            content=result,
            message_type="tables_generated",
            correlation_id=message.message_id
        )

    async def handle_embed_diagrams(self, message: Message) -> Message:
        content = message.content
        result = await self.embed_diagrams(
            content.get("markdown", ""),
            content.get("diagrams", {})
        )
        return Message(
            sender=self.__class__.__name__,
            recipient=message.sender,
            content=result,
            message_type="diagrams_embedded",
            correlation_id=message.message_id
        )

    async def handle_convert_to_html(self, message: Message) -> Message:
        result = await self.convert_to_html(message.content.get("markdown", ""))
        return Message(
            sender=self.__class__.__name__,
            recipient=message.sender,
            content=result,
            message_type="html_converted",
            correlation_id=message.message_id
        )

    async def handle_get_templates(self, message: Message) -> Message:
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

    async def handle_get_styles(self, message: Message) -> Message:
        return Message(
            sender=self.__class__.__name__,
            recipient=message.sender,
            content={
                "styles": list(self._styles.keys()),
                "count": len(self._styles)
            },
            message_type="styles_list",
            correlation_id=message.message_id
        )

    async def handle_message(self, message: Message) -> Optional[Message]:
        try:
            msg_type = message.message_type
            handlers = self._get_capability_handlers()
            
            if msg_type in handlers:
                handler = getattr(self, handlers[msg_type], None)
                if handler:
                    return await handler(message)
            
            return Message(
                sender=self.__class__.__name__,
                recipient=message.sender,
                content={"error": f"Type non supporté: {msg_type}"},
                message_type=MessageType.ERROR.value,
                correlation_id=message.message_id
            )
        except Exception as e:
            return Message(
                sender=self.__class__.__name__,
                recipient=message.sender,
                content={"error": str(e)},
                message_type=MessageType.ERROR.value,
                correlation_id=message.message_id
            )

    async def health_check(self) -> Dict[str, Any]:
        uptime = None
        if self._stats.get('uptime_start'):
            start = datetime.fromisoformat(self._stats['uptime_start'])
            uptime = str(datetime.now() - start)

        success_rate = 0
        total = self._stats["docs_generated"] + self._stats["docs_failed"]
        if total > 0:
            success_rate = (self._stats["docs_generated"] / total) * 100

        return {
            "status": self._status,
            "ready": self._initialized,
            "display_name": self._display_name,
            "uptime": uptime,
            "stats": {
                "docs_generated": self._stats["docs_generated"],
                "docs_failed": self._stats["docs_failed"],
                "by_style": self._stats["by_style"],
                "success_rate": round(success_rate, 2),
                "processing_time_avg": round(self._stats["processing_time_avg"], 3)
            },
            "components": self._components,
            "timestamp": datetime.now().isoformat()
        }

    def get_agent_info(self) -> Dict[str, Any]:
        return {
            "id": "MarkdownGeneratorSubAgent",
            "name": self._display_name,
            "version": "2.2.0",
            "status": self._status,
            "capabilities": list(self._get_capability_handlers().keys()),
            "features": self._get_features(),
            "stats": {
                "docs_generated": self._stats["docs_generated"],
                "templates_available": len(self._templates),
                "success_rate": round(
                    (self._stats["docs_generated"] / max(1, self._stats["docs_generated"] + self._stats["docs_failed"])) * 100, 2
                )
            }
        }

    async def get_stats(self) -> Dict[str, Any]:
        return self._stats

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
            stats_file = Path("./reports") / "documenter" / "markdown_generator" / f"stats_{datetime.now().strftime('%Y%m%d')}.json"
            stats_file.parent.mkdir(parents=True, exist_ok=True)
            with open(stats_file, 'w', encoding='utf-8') as f:
                json.dump(self._stats, f, indent=2, default=str)
        except Exception as e:
            self._logger.warning(f"Impossible de sauvegarder: {e}")
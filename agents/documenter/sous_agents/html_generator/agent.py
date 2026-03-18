#!/usr/bin/env python3
"""
HtmlGenerator SubAgent - Générateur HTML
Version: 2.2.0 (ALIGNÉ SUR COMMUNICATION)
"""

import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
import time
import json
import html

project_root = Path(__file__).parent.parent.parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from agents.sous_agents.base_subagent import BaseSubAgent
from agents.base_agent.base_agent import Message, MessageType


class HtmlGeneratorSubAgent(BaseSubAgent):
    """
    Sous-agent spécialisé dans la génération de documentation HTML
    Version 2.2 - Aligné sur l'architecture Communication
    """

    def __init__(self, config_path: Optional[str] = None):
        super().__init__(config_path)
        
        subagent_config = self._config.get('subagent', {})
        self._display_name = subagent_config.get('display_name', '🌐 Générateur HTML')
        
        self._initialized = False
        self._pages_generated = 0
        self._pages_failed = 0
        
        self._templates = self._load_templates()
        self._themes = self._load_themes()
        
        self._stats = {
            "pages_generated": 0,
            "pages_failed": 0,
            "by_theme": {},
            "processing_time_total": 0,
            "processing_time_avg": 0,
            "uptime_start": datetime.now().isoformat()
        }
        
        self._logger.info(f"{self._display_name} créé")

    def _load_templates(self) -> Dict[str, str]:
        """Charge les templates HTML"""
        return {
            "basic": """<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; margin: 0; padding: 20px; }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        h1, h2, h3 {{ color: #333; }}
        pre {{ background: #f4f4f4; padding: 10px; border-radius: 5px; overflow-x: auto; }}
        code {{ font-family: 'Courier New', monospace; }}
        .diagram {{ margin: 20px 0; padding: 10px; background: #f9f9f9; border-left: 3px solid #00ff88; }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>{title}</h1>
            <p>{description}</p>
        </header>
        <main>
            {content}
        </main>
        <footer>
            <p>Généré le {date} par {generator}</p>
        </footer>
    </div>
</body>
</html>""",
            "dark": """<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; margin: 0; padding: 20px; background: #1a1a1a; color: #e0e0e0; }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        h1, h2, h3 {{ color: #00ff88; }}
        pre {{ background: #2d2d2d; padding: 10px; border-radius: 5px; overflow-x: auto; color: #e0e0e0; }}
        code {{ font-family: 'Courier New', monospace; color: #ff9f00; }}
        .diagram {{ margin: 20px 0; padding: 10px; background: #2d2d2d; border-left: 3px solid #00ff88; }}
        a {{ color: #00ff88; }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>{title}</h1>
            <p>{description}</p>
        </header>
        <main>
            {content}
        </main>
        <footer>
            <p>Généré le {date} par {generator}</p>
        </footer>
    </div>
</body>
</html>""",
            "professional": """<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6; color: #333; }}
        .navbar {{ background: #2c3e50; color: white; padding: 1rem; position: sticky; top: 0; }}
        .navbar a {{ color: white; text-decoration: none; margin-right: 1rem; }}
        .container {{ max-width: 1200px; margin: 2rem auto; padding: 0 2rem; }}
        h1 {{ color: #2c3e50; border-bottom: 2px solid #00ff88; padding-bottom: 0.5rem; }}
        h2 {{ color: #34495e; margin-top: 2rem; }}
        pre {{ background: #f8f9fa; padding: 1rem; border-radius: 5px; border-left: 3px solid #00ff88; overflow-x: auto; }}
        code {{ font-family: 'Courier New', monospace; }}
        .diagram {{ margin: 2rem 0; padding: 1rem; background: #f8f9fa; border-radius: 5px; }}
        .card {{ background: white; border-radius: 5px; padding: 1.5rem; margin-bottom: 1.5rem; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        footer {{ background: #2c3e50; color: white; text-align: center; padding: 1rem; margin-top: 2rem; }}
    </style>
</head>
<body>
    <nav class="navbar">
        <div class="container">
            <a href="#home">Accueil</a>
            <a href="#api">API</a>
            <a href="#diagrams">Diagrammes</a>
            <a href="#examples">Exemples</a>
        </div>
    </nav>
    <div class="container">
        <header>
            <h1>{title}</h1>
            <p>{description}</p>
        </header>
        <main>
            {content}
        </main>
    </div>
    <footer>
        <p>Généré le {date} par {generator}</p>
    </footer>
</body>
</html>"""
        }

    def _load_themes(self) -> Dict[str, Dict[str, str]]:
        """Charge les thèmes disponibles"""
        return {
            "light": {
                "bg": "#ffffff",
                "text": "#333333",
                "code_bg": "#f4f4f4",
                "accent": "#00ff88"
            },
            "dark": {
                "bg": "#1a1a1a",
                "text": "#e0e0e0",
                "code_bg": "#2d2d2d",
                "accent": "#00ff88"
            },
            "blue": {
                "bg": "#f0f8ff",
                "text": "#003366",
                "code_bg": "#e6f0ff",
                "accent": "#0066cc"
            }
        }

    async def _initialize_subagent_components(self) -> bool:
        try:
            self._components = {
                "version": "2.2.0",
                "templates": list(self._templates.keys()),
                "themes": list(self._themes.keys()),
                "supports_mermaid": True,
                "supports_responsive": True
            }
            return True
        except Exception as e:
            self._logger.error(f"Erreur composants: {e}")
            return False

    async def _initialize_components(self) -> bool:
        return await self._initialize_subagent_components()

    def _get_capability_handlers(self) -> Dict[str, str]:
        return {
            "generate_html": "handle_generate_html",
            "generate_site": "handle_generate_site",
            "generate_from_markdown": "handle_generate_from_markdown",
            "embed_diagrams": "handle_embed_diagrams",
            "get_templates": "handle_get_templates",
            "get_themes": "handle_get_themes"
        }

    def _get_features(self) -> Dict[str, Any]:
        return {
            "templates": list(self._templates.keys()),
            "themes": list(self._themes.keys()),
            "supports_mermaid": True,
            "supports_responsive": True,
            "supports_navigation": True,
            "max_file_size_mb": 50
        }

    async def generate_html(self, package: Any, template: str = "professional", theme: str = "light") -> Dict[str, Any]:
        """Génère du HTML à partir d'un package de documentation"""
        start_time = time.time()
        
        try:
            if template not in self._templates:
                template = "professional"
            
            template_str = self._templates[template]
            
            # Convertir le contenu en HTML
            content_html = self._convert_to_html(package)
            
            # Ajouter les diagrammes
            if hasattr(package, 'diagrams') and package.diagrams:
                content_html += self._render_diagrams(package.diagrams)
            
            data = {
                "title": getattr(package, 'title', 'Documentation'),
                "description": getattr(package, 'description', ''),
                "content": content_html,
                "date": datetime.now().strftime("%d/%m/%Y %H:%M"),
                "generator": "HtmlGeneratorSubAgent"
            }
            
            html_content = template_str.format(**data)
            
            processing_time = time.time() - start_time
            self._pages_generated += 1
            self._stats["pages_generated"] += 1
            self._stats["by_theme"][theme] = self._stats["by_theme"].get(theme, 0) + 1
            self._stats["processing_time_total"] += processing_time
            self._stats["processing_time_avg"] = self._stats["processing_time_total"] / self._stats["pages_generated"]
            
            return {
                "success": True,
                "html": html_content,
                "template": template,
                "theme": theme,
                "size": len(html_content),
                "processing_time": processing_time
            }
            
        except Exception as e:
            self._pages_failed += 1
            self._stats["pages_failed"] += 1
            return {"success": False, "error": str(e)}

    def _convert_to_html(self, package: Any) -> str:
        """Convertit le contenu du package en HTML"""
        html_parts = []
        
        if hasattr(package, 'sections'):
            for section in package.sections:
                level = getattr(section, 'level', 1)
                title = getattr(section, 'title', 'Section')
                content = getattr(section, 'content', '')
                
                # Échapper le HTML
                content = html.escape(content)
                # Convertir les retours à la ligne en <br>
                content = content.replace('\n', '<br>')
                
                html_parts.append(f"<h{level}>{title}</h{level}>")
                html_parts.append(f"<div class='section'>{content}</div>")
        
        return "\n".join(html_parts)

    def _render_diagrams(self, diagrams: Dict[str, str]) -> str:
        """Rend les diagrammes en HTML"""
        html_parts = ["<h2>Diagrammes</h2>"]
        
        for name, diagram in diagrams.items():
            # Échapper le diagramme pour l'affichage
            diagram_escaped = html.escape(diagram)
            html_parts.append(f"""
            <div class="diagram">
                <h3>{name}</h3>
                <pre>{diagram_escaped}</pre>
            </div>
            """)
        
        return "\n".join(html_parts)

    async def generate_site(self, packages: List[Any], template: str = "professional") -> Dict[str, Any]:
        """Génère un site complet de documentation"""
        start_time = time.time()
        
        try:
            pages = []
            for i, package in enumerate(packages):
                result = await self.generate_html(package, template)
                if result["success"]:
                    pages.append({
                        "index": i,
                        "title": getattr(package, 'title', f'Page {i}'),
                        "html": result["html"]
                    })
            
            # Générer la page d'accueil avec navigation
            index_html = self._generate_index(pages, template)
            
            processing_time = time.time() - start_time
            
            return {
                "success": True,
                "pages": pages,
                "index": index_html,
                "count": len(pages),
                "processing_time": processing_time
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _generate_index(self, pages: List[Dict], template: str) -> str:
        """Génère la page d'accueil du site"""
        nav_links = []
        for page in pages:
            nav_links.append(f'<li><a href="page_{page["index"]}.html">{page["title"]}</a></li>')
        
        nav_html = "<ul>" + "\n".join(nav_links) + "</ul>"
        
        data = {
            "title": "Documentation - Accueil",
            "description": "Site de documentation généré automatiquement",
            "content": f"<h1>Documentation</h1>\n{nav_html}",
            "date": datetime.now().strftime("%d/%m/%Y %H:%M"),
            "generator": "HtmlGeneratorSubAgent"
        }
        
        template_str = self._templates.get(template, self._templates["professional"])
        return template_str.format(**data)

    async def generate_from_markdown(self, markdown: str, template: str = "professional") -> Dict[str, Any]:
        """Génère du HTML à partir de Markdown"""
        try:
            # Conversion basique Markdown -> HTML
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
                    html_lines.append(html.escape(line))
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
            
            content = "\n".join(html_lines)
            
            data = {
                "title": "Documentation Markdown",
                "description": "Converti depuis Markdown",
                "content": content,
                "date": datetime.now().strftime("%d/%m/%Y %H:%M"),
                "generator": "HtmlGeneratorSubAgent"
            }
            
            template_str = self._templates.get(template, self._templates["professional"])
            html_content = template_str.format(**data)
            
            return {
                "success": True,
                "html": html_content,
                "lines": len(markdown.split('\n'))
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def embed_diagrams(self, html_content: str, diagrams: Dict[str, str]) -> Dict[str, Any]:
        """Intègre des diagrammes dans du HTML existant"""
        try:
            # Chercher l'emplacement pour insérer les diagrammes
            if "</main>" in html_content:
                parts = html_content.split("</main>")
                diagrams_html = self._render_diagrams(diagrams)
                new_html = parts[0] + diagrams_html + "</main>" + parts[1]
            elif "</body>" in html_content:
                parts = html_content.split("</body>")
                diagrams_html = self._render_diagrams(diagrams)
                new_html = parts[0] + diagrams_html + "</body>" + parts[1]
            else:
                new_html = html_content + self._render_diagrams(diagrams)
            
            return {
                "success": True,
                "html": new_html,
                "diagrams_added": len(diagrams)
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def handle_generate_html(self, message: Message) -> Message:
        content = message.content
        result = await self.generate_html(
            content.get("package"),
            content.get("template", "professional"),
            content.get("theme", "light")
        )
        return Message(
            sender=self.__class__.__name__,
            recipient=message.sender,
            content=result,
            message_type="html_generated",
            correlation_id=message.message_id
        )

    async def handle_generate_site(self, message: Message) -> Message:
        content = message.content
        result = await self.generate_site(
            content.get("packages", []),
            content.get("template", "professional")
        )
        return Message(
            sender=self.__class__.__name__,
            recipient=message.sender,
            content=result,
            message_type="site_generated",
            correlation_id=message.message_id
        )

    async def handle_generate_from_markdown(self, message: Message) -> Message:
        content = message.content
        result = await self.generate_from_markdown(
            content.get("markdown", ""),
            content.get("template", "professional")
        )
        return Message(
            sender=self.__class__.__name__,
            recipient=message.sender,
            content=result,
            message_type="html_from_markdown",
            correlation_id=message.message_id
        )

    async def handle_embed_diagrams(self, message: Message) -> Message:
        content = message.content
        result = await self.embed_diagrams(
            content.get("html", ""),
            content.get("diagrams", {})
        )
        return Message(
            sender=self.__class__.__name__,
            recipient=message.sender,
            content=result,
            message_type="diagrams_embedded",
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

    async def handle_get_themes(self, message: Message) -> Message:
        return Message(
            sender=self.__class__.__name__,
            recipient=message.sender,
            content={
                "themes": list(self._themes.keys()),
                "count": len(self._themes)
            },
            message_type="themes_list",
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
        total = self._stats["pages_generated"] + self._stats["pages_failed"]
        if total > 0:
            success_rate = (self._stats["pages_generated"] / total) * 100

        return {
            "status": self._status,
            "ready": self._initialized,
            "display_name": self._display_name,
            "uptime": uptime,
            "stats": {
                "pages_generated": self._stats["pages_generated"],
                "pages_failed": self._stats["pages_failed"],
                "by_theme": self._stats["by_theme"],
                "success_rate": round(success_rate, 2),
                "processing_time_avg": round(self._stats["processing_time_avg"], 3)
            },
            "components": self._components,
            "timestamp": datetime.now().isoformat()
        }

    def get_agent_info(self) -> Dict[str, Any]:
        return {
            "id": "HtmlGeneratorSubAgent",
            "name": self._display_name,
            "version": "2.2.0",
            "status": self._status,
            "capabilities": list(self._get_capability_handlers().keys()),
            "features": self._get_features(),
            "stats": {
                "pages_generated": self._stats["pages_generated"],
                "templates_available": len(self._templates),
                "success_rate": round(
                    (self._stats["pages_generated"] / max(1, self._stats["pages_generated"] + self._stats["pages_failed"])) * 100, 2
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
            stats_file = Path("./reports") / "documenter" / "html_generator" / f"stats_{datetime.now().strftime('%Y%m%d')}.json"
            stats_file.parent.mkdir(parents=True, exist_ok=True)
            with open(stats_file, 'w', encoding='utf-8') as f:
                json.dump(self._stats, f, indent=2, default=str)
        except Exception as e:
            self._logger.warning(f"Impossible de sauvegarder: {e}")
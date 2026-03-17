#!/usr/bin/env python3
"""
Doc Generator SubAgent - Générateur de documentation générale
Version: 2.0.0

Génère de la documentation technique à partir de spécifications.
"""

import logging
import sys
import asyncio
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List

# Configuration des imports
current_dir = Path(__file__).parent.absolute()
project_root = current_dir.parent.parent.parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from agents.sous_agents.base_subagent import BaseSubAgent

logger = logging.getLogger(__name__)


class DocGeneratorSubAgent(BaseSubAgent):
    """
    Sous-agent spécialisé en génération de documentation technique.
    Gère la création de documentation à partir de spécifications.
    """

    def __init__(self, config_path: Optional[str] = None):
        super().__init__(config_path)

        self._subagent_display_name = "📄 Générateur de Documentation"
        self._subagent_description = "Génération de documentation technique générale"
        self._subagent_version = "2.0.0"
        self._subagent_category = "documentation"
        self._subagent_capabilities = [
            "doc.generate",
            "doc.generate_from_spec",
            "doc.generate_technical_spec",
            "doc.generate_architecture_doc"
        ]

        self._doc_config = self._agent_config.get('doc_generator', {})
        self._formats = self._doc_config.get('formats', ['markdown', 'html'])

        logger.info(f"✅ {self._subagent_display_name} initialisé (v{self._subagent_version})")

    async def _initialize_subagent_components(self) -> bool:
        """Initialise les composants spécifiques."""
        logger.info("Initialisation des composants Doc Generator...")
        return True

    async def _initialize_components(self) -> bool:
        """Implémentation requise par BaseSubAgent."""
        return await self._initialize_subagent_components()

    async def generate_doc(self, project_name: str, content: Dict[str, Any], format: str = "markdown") -> Dict[str, Any]:
        """Génère une documentation à partir du contenu."""
        logger.info(f"📄 Génération de documentation pour {project_name}")

        doc_id = f"doc_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        doc = {
            "id": doc_id,
            "project": project_name,
            "title": content.get('title', project_name),
            "version": content.get('version', '1.0.0'),
            "date": datetime.now().isoformat(),
            "sections": self._build_sections(content.get('sections', []))
        }

        if format == "markdown":
            output = self._generate_markdown(doc)
        elif format == "html":
            output = self._generate_html(doc)
        else:
            output = json.dumps(doc, indent=2)

        return {
            'success': True,
            'doc_id': doc_id,
            'format': format,
            'content': output,
            'sections_count': len(doc['sections'])
        }

    def _build_sections(self, sections_config: List[Dict]) -> List[Dict]:
        sections = []
        for config in sections_config:
            sections.append({
                "title": config.get('title', 'Untitled'),
                "level": config.get('level', 1),
                "content": config.get('content', ''),
                "subsections": self._build_sections(config.get('subsections', []))
            })
        return sections

    def _generate_markdown(self, doc: Dict) -> str:
        lines = []
        lines.append(f"# {doc['title']}\n")
        lines.append(f"*Version {doc['version']} - {doc['date']}*\n")
        lines.append("---\n")

        for section in doc['sections']:
            lines.append(self._render_section_markdown(section))

        return "\n".join(lines)

    def _render_section_markdown(self, section: Dict, level: int = 1) -> str:
        content = []
        content.append(f"{'#' * level} {section['title']}\n")
        content.append(f"{section['content']}\n")

        for subsection in section['subsections']:
            content.append(self._render_section_markdown(subsection, level + 1))

        return "\n".join(content)

    def _generate_html(self, doc: Dict) -> str:
        html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>{doc['title']}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }}
        h1 {{ color: #333; border-bottom: 2px solid #333; }}
        h2 {{ color: #666; margin-top: 30px; }}
        .metadata {{ background: #f5f5f5; padding: 10px; border-radius: 5px; }}
    </style>
</head>
<body>
    <h1>{doc['title']}</h1>
    <div class="metadata">
        <p><strong>Version:</strong> {doc['version']}</p>
        <p><strong>Date:</strong> {doc['date']}</p>
    </div>
"""
        for section in doc['sections']:
            html += self._render_section_html(section)

        html += "</body></html>"
        return html

    def _render_section_html(self, section: Dict, level: int = 1) -> str:
        html = f"<h{level}>{section['title']}</h{level}>\n"
        html += f"<div>{section['content']}</div>\n"

        for subsection in section['subsections']:
            html += self._render_section_html(subsection, level + 1)

        return html

    async def generate_from_spec(self, spec: Dict[str, Any], format: str = "markdown") -> Dict[str, Any]:
        return await self.generate_doc(spec.get('name', 'Unnamed'), spec, format)

    def _get_capability_handlers(self) -> Dict[str, Any]:
        return {
            "doc.generate": self._handle_generate,
            "doc.generate_from_spec": self._handle_generate_from_spec,
            "doc.generate_technical_spec": self._handle_generate_technical_spec,
            "doc.generate_architecture_doc": self._handle_generate_architecture_doc,
        }

    async def _handle_generate(self, params: Dict[str, Any]) -> Dict[str, Any]:
        return await self.generate_doc(
            project_name=params.get('project_name', 'Unnamed'),
            content=params.get('content', {}),
            format=params.get('format', 'markdown')
        )

    async def _handle_generate_from_spec(self, params: Dict[str, Any]) -> Dict[str, Any]:
        return await self.generate_from_spec(
            spec=params.get('spec', {}),
            format=params.get('format', 'markdown')
        )

    async def _handle_generate_technical_spec(self, params: Dict[str, Any]) -> Dict[str, Any]:
        content = {
            "title": f"{params.get('component', {}).get('name', 'Component')} - Technical Specification",
            "sections": [
                {"title": "Overview", "content": params.get('component', {}).get('description', 'Technical overview.')},
                {"title": "Architecture", "content": "Architecture description."},
                {"title": "Interfaces", "content": "API specifications."}
            ]
        }
        return await self.generate_doc(params.get('component', {}).get('name', 'Component'), content, params.get('format', 'markdown'))


# ============================================================================
# FONCTIONS D'EXPORT
# ============================================================================

def get_agent_class():
    return DocGeneratorSubAgent
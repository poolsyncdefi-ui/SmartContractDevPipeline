#!/usr/bin/env python3
"""
Diagram Generator SubAgent - Générateur de diagrammes
Version: 2.0.0

Génère des diagrammes d'architecture, séquences, classes avec Mermaid et PlantUML.
"""

import logging
import sys
import asyncio
import json
import subprocess
import tempfile
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


class DiagramGeneratorSubAgent(BaseSubAgent):
    """
    Sous-agent spécialisé en génération de diagrammes.
    Gère la création de diagrammes Mermaid, PlantUML, etc.
    """

    def __init__(self, config_path: Optional[str] = None):
        super().__init__(config_path)

        self._subagent_display_name = "📊 Générateur de Diagrammes"
        self._subagent_description = "Génération de diagrammes d'architecture et de séquence"
        self._subagent_version = "2.0.0"
        self._subagent_category = "documentation"
        self._subagent_capabilities = [
            "diagram.generate_architecture",
            "diagram.generate_sequence",
            "diagram.generate_class",
            "diagram.generate_flowchart",
            "diagram.generate_er"
        ]

        self._diagram_config = self._agent_config.get('diagram_generator', {})
        self._default_type = self._diagram_config.get('default_type', 'mermaid')
        self._mermaid_available = self._check_mermaid_available()
        self._plantuml_available = self._check_plantuml_available()

        logger.info(f"✅ {self._subagent_display_name} initialisé (v{self._subagent_version})")

    def _check_mermaid_available(self) -> bool:
        """Vérifie si Mermaid CLI est disponible."""
        try:
            result = subprocess.run(['mmdc', '--version'], capture_output=True, text=True, timeout=2)
            return result.returncode == 0
        except:
            return False

    def _check_plantuml_available(self) -> bool:
        """Vérifie si PlantUML est disponible."""
        try:
            result = subprocess.run(['plantuml', '-version'], capture_output=True, text=True, timeout=2)
            return result.returncode == 0
        except:
            return False

    async def _initialize_subagent_components(self) -> bool:
        """Initialise les composants spécifiques."""
        logger.info("Initialisation des composants Diagram Generator...")
        logger.info(f"  Mermaid: {'✅' if self._mermaid_available else '❌'} (mode simulation)")
        logger.info(f"  PlantUML: {'✅' if self._plantuml_available else '❌'} (mode simulation)")
        return True

    async def _initialize_components(self) -> bool:
        """Implémentation requise par BaseSubAgent."""
        return await self._initialize_subagent_components()

    async def generate_architecture_diagram(self, components: List[Dict[str, Any]], 
                                           diagram_type: str = "mermaid") -> Dict[str, Any]:
        """Génère un diagramme d'architecture."""
        logger.info(f"📊 Génération de diagramme d'architecture ({diagram_type})")

        if diagram_type == "mermaid":
            diagram = self._generate_mermaid_architecture(components)
        elif diagram_type == "plantuml":
            diagram = self._generate_plantuml_architecture(components)
        else:
            diagram = self._generate_text_architecture(components)

        diagram_id = f"diag_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        return {
            'success': True,
            'diagram_id': diagram_id,
            'diagram_type': diagram_type,
            'diagram': diagram,
            'components_count': len(components),
            'mode': 'simulation' if not self._mermaid_available else 'real'
        }

    def _generate_mermaid_architecture(self, components: List[Dict]) -> str:
        """Génère un diagramme d'architecture Mermaid."""
        lines = ["graph TD"]
        
        for i, comp in enumerate(components):
            node_id = comp.get('id', f"comp{i}")
            node_name = comp.get('name', f"Component {i}")
            lines.append(f"    {node_id}[{node_name}]")

            # Ajouter les relations
            for dep in comp.get('dependencies', []):
                lines.append(f"    {node_id} --> {dep}")

        return "\n".join(lines)

    def _generate_plantuml_architecture(self, components: List[Dict]) -> str:
        """Génère un diagramme d'architecture PlantUML."""
        lines = ["@startuml", "skinparam componentStyle rectangle"]
        
        for comp in components:
            comp_name = comp.get('name', 'Unknown')
            lines.append(f"component {comp_name} {{")
            lines.append("}")

        lines.append("@enduml")
        return "\n".join(lines)

    def _generate_text_architecture(self, components: List[Dict]) -> str:
        """Génère une représentation textuelle simple."""
        lines = ["ARCHITECTURE DIAGRAM", "=" * 50]
        
        for comp in components:
            lines.append(f"\n• {comp.get('name', 'Component')}")
            if 'description' in comp:
                lines.append(f"  {comp['description']}")
            if 'dependencies' in comp:
                lines.append(f"  → Depends on: {', '.join(comp['dependencies'])}")

        return "\n".join(lines)

    async def generate_sequence_diagram(self, interactions: List[Dict[str, Any]],
                                       diagram_type: str = "mermaid") -> Dict[str, Any]:
        """Génère un diagramme de séquence."""
        if diagram_type == "mermaid":
            lines = ["sequenceDiagram"]
            for interaction in interactions:
                from_ = interaction.get('from', 'Actor')
                to_ = interaction.get('to', 'System')
                action = interaction.get('action', 'call')
                lines.append(f"    {from_}->>{to_}: {action}")
            diagram = "\n".join(lines)
        else:
            diagram = "Sequence diagram placeholder"

        return {
            'success': True,
            'diagram': diagram,
            'interactions_count': len(interactions)
        }

    async def generate_class_diagram(self, classes: List[Dict[str, Any]],
                                    diagram_type: str = "mermaid") -> Dict[str, Any]:
        """Génère un diagramme de classes."""
        if diagram_type == "mermaid":
            lines = ["classDiagram"]
            for cls in classes:
                class_name = cls.get('name', 'Class')
                lines.append(f"    class {class_name} {{")
                for attr in cls.get('attributes', []):
                    lines.append(f"        +{attr}")
                for method in cls.get('methods', []):
                    lines.append(f"        +{method}()")
                lines.append("    }")
            diagram = "\n".join(lines)
        else:
            diagram = "Class diagram placeholder"

        return {
            'success': True,
            'diagram': diagram,
            'classes_count': len(classes)
        }

    async def generate_flowchart(self, nodes: List[Dict[str, Any]],
                                diagram_type: str = "mermaid") -> Dict[str, Any]:
        """Génère un organigramme."""
        if diagram_type == "mermaid":
            lines = ["flowchart TD"]
            for node in nodes:
                node_id = node.get('id', 'node')
                node_text = node.get('text', 'Step')
                lines.append(f"    {node_id}[{node_text}]")
                
                if 'next' in node:
                    lines.append(f"    {node_id} --> {node['next']}")
            diagram = "\n".join(lines)
        else:
            diagram = "Flowchart placeholder"

        return {
            'success': True,
            'diagram': diagram,
            'nodes_count': len(nodes)
        }

    async def generate_er_diagram(self, entities: List[Dict[str, Any]],
                                 diagram_type: str = "mermaid") -> Dict[str, Any]:
        """Génère un diagramme entité-relation."""
        if diagram_type == "mermaid":
            lines = ["erDiagram"]
            for entity in entities:
                entity_name = entity.get('name', 'Entity')
                lines.append(f"    {entity_name} {{")
                for attr in entity.get('attributes', []):
                    lines.append(f"        {attr}")
                lines.append("    }")
                
                for rel in entity.get('relationships', []):
                    lines.append(f"    {entity_name} ||--o{{ {rel} : has")
            diagram = "\n".join(lines)
        else:
            diagram = "ER diagram placeholder"

        return {
            'success': True,
            'diagram': diagram,
            'entities_count': len(entities)
        }

    def _get_capability_handlers(self) -> Dict[str, Any]:
        return {
            "diagram.generate_architecture": self._handle_generate_architecture,
            "diagram.generate_sequence": self._handle_generate_sequence,
            "diagram.generate_class": self._handle_generate_class,
            "diagram.generate_flowchart": self._handle_generate_flowchart,
            "diagram.generate_er": self._handle_generate_er,
        }

    async def _handle_generate_architecture(self, params: Dict[str, Any]) -> Dict[str, Any]:
        return await self.generate_architecture_diagram(
            components=params.get('components', []),
            diagram_type=params.get('diagram_type', self._default_type)
        )

    async def _handle_generate_sequence(self, params: Dict[str, Any]) -> Dict[str, Any]:
        return await self.generate_sequence_diagram(
            interactions=params.get('interactions', []),
            diagram_type=params.get('diagram_type', self._default_type)
        )

    async def _handle_generate_class(self, params: Dict[str, Any]) -> Dict[str, Any]:
        return await self.generate_class_diagram(
            classes=params.get('classes', []),
            diagram_type=params.get('diagram_type', self._default_type)
        )

    async def _handle_generate_flowchart(self, params: Dict[str, Any]) -> Dict[str, Any]:
        return await self.generate_flowchart(
            nodes=params.get('nodes', []),
            diagram_type=params.get('diagram_type', self._default_type)
        )

    async def _handle_generate_er(self, params: Dict[str, Any]) -> Dict[str, Any]:
        return await self.generate_er_diagram(
            entities=params.get('entities', []),
            diagram_type=params.get('diagram_type', self._default_type)
        )


# ============================================================================
# FONCTIONS D'EXPORT
# ============================================================================

def get_agent_class():
    return DiagramGeneratorSubAgent
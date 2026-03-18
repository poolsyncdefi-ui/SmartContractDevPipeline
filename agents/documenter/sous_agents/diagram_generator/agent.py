#!/usr/bin/env python3
"""
DiagramGenerator SubAgent - Générateur de diagrammes
Version: 2.2.0 (ALIGNÉ SUR COMMUNICATION)
"""

import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
import time
import json
from enum import Enum

project_root = Path(__file__).parent.parent.parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from agents.sous_agents.base_subagent import BaseSubAgent
from agents.base_agent.base_agent import Message, MessageType


class DiagramType(Enum):
    INHERITANCE = "inheritance"
    DEPENDENCY = "dependency"
    WORKFLOW = "workflow"
    SEQUENCE = "sequence"
    CLASS = "class"
    STATE = "state"


class DiagramGeneratorSubAgent(BaseSubAgent):
    """
    Sous-agent spécialisé dans la génération de diagrammes Mermaid
    Version 2.2 - Aligné sur l'architecture Communication
    """

    def __init__(self, config_path: Optional[str] = None):
        super().__init__(config_path)
        
        subagent_config = self._config.get('subagent', {})
        self._display_name = subagent_config.get('display_name', '📊 Générateur de Diagrammes')
        
        self._initialized = False
        self._diagrams_generated = 0
        self._diagrams_failed = 0
        
        self._stats = {
            "diagrams_generated": 0,
            "diagrams_failed": 0,
            "by_type": {},
            "processing_time_total": 0,
            "processing_time_avg": 0,
            "uptime_start": datetime.now().isoformat()
        }
        
        self._logger.info(f"{self._display_name} créé")

    async def _initialize_subagent_components(self) -> bool:
        try:
            self._components = {
                "version": "2.2.0",
                "diagram_types": [dt.value for dt in DiagramType],
                "supports_mermaid": True,
                "max_nodes": 100
            }
            return True
        except Exception as e:
            self._logger.error(f"Erreur composants: {e}")
            return False

    async def _initialize_components(self) -> bool:
        return await self._initialize_subagent_components()

    def _get_capability_handlers(self) -> Dict[str, str]:
        return {
            "generate_diagrams": "handle_generate_diagrams",
            "generate_inheritance": "handle_generate_inheritance",
            "generate_dependencies": "handle_generate_dependencies",
            "generate_workflow": "handle_generate_workflow",
            "generate_sequence": "handle_generate_sequence",
            "validate_diagram": "handle_validate_diagram"
        }

    def _get_features(self) -> Dict[str, Any]:
        return {
            "diagram_types": [dt.value for dt in DiagramType],
            "syntax": "mermaid",
            "max_nodes": 100,
            "themes": ["default", "dark", "forest"],
            "export_formats": ["svg", "png", "markdown"]
        }

    async def generate_diagrams(self, contract_info: Dict[str, Any], types: List[str] = None) -> Dict[str, Any]:
        """Génère des diagrammes à partir des informations du contrat"""
        start_time = time.time()
        
        try:
            types = types or [dt.value for dt in DiagramType]
            diagrams = {}
            
            if "inheritance" in types and contract_info.get("inheritance"):
                diagrams["inheritance"] = self._generate_inheritance_diagram(contract_info)
            
            if "dependency" in types and contract_info.get("dependencies"):
                diagrams["dependencies"] = self._generate_dependencies_diagram(contract_info)
            
            if "workflow" in types and contract_info.get("functions"):
                diagrams["workflow"] = self._generate_workflow_diagram(contract_info)
            
            if "sequence" in types and contract_info.get("functions"):
                diagrams["sequence"] = self._generate_sequence_diagram(contract_info)
            
            if "class" in types:
                diagrams["class"] = self._generate_class_diagram(contract_info)
            
            processing_time = time.time() - start_time
            self._diagrams_generated += len(diagrams)
            self._stats["diagrams_generated"] += len(diagrams)
            self._stats["processing_time_total"] += processing_time
            self._stats["processing_time_avg"] = self._stats["processing_time_total"] / max(1, self._stats["diagrams_generated"])
            
            for diagram_type in diagrams.keys():
                self._stats["by_type"][diagram_type] = self._stats["by_type"].get(diagram_type, 0) + 1
            
            return {
                "success": True,
                "diagrams": diagrams,
                "count": len(diagrams),
                "types": list(diagrams.keys()),
                "processing_time": processing_time
            }
            
        except Exception as e:
            self._diagrams_failed += 1
            self._stats["diagrams_failed"] += 1
            return {
                "success": False,
                "error": str(e)
            }

    def _generate_inheritance_diagram(self, info: Dict) -> str:
        """Génère un diagramme d'héritage"""
        lines = ["```mermaid", "classDiagram"]
        main = info.get('name', 'Contract')
        
        lines.append(f"  class {main} {{")
        for func in info.get('functions', [])[:5]:
            lines.append(f"    +{func.get('name')}()")
        lines.append("  }")
        
        for parent in info.get('inheritance', []):
            lines.append(f"  {main} --|> {parent}")
        
        lines.append("```")
        return "\n".join(lines)

    def _generate_dependencies_diagram(self, info: Dict) -> str:
        """Génère un diagramme de dépendances"""
        lines = ["```mermaid", "graph TD"]
        main = info.get('name', 'Contract')
        lines.append(f"  {main}[{main}]")
        
        for i, dep in enumerate(info.get('dependencies', [])[:10]):
            dep_id = f"dep{i}"
            lines.append(f"  {dep_id}[{dep}]")
            lines.append(f"  {main} --> {dep_id}")
        
        lines.append("```")
        return "\n".join(lines)

    def _generate_workflow_diagram(self, info: Dict) -> str:
        """Génère un diagramme de workflow"""
        lines = ["```mermaid", "stateDiagram-v2"]
        lines.append("  [*] --> Idle")
        
        for func in info.get('functions', [])[:8]:
            name = func.get('name', 'function')
            lines.append(f"  Idle --> {name}")
            lines.append(f"  {name} --> Idle")
        
        lines.append("```")
        return "\n".join(lines)

    def _generate_sequence_diagram(self, info: Dict) -> str:
        """Génère un diagramme de séquence"""
        lines = ["```mermaid", "sequenceDiagram"]
        lines.append("  participant User")
        lines.append("  participant Contract")
        
        for func in info.get('functions', [])[:5]:
            name = func.get('name', 'function')
            lines.append(f"  User->>Contract: {name}()")
            lines.append(f"  Contract-->>User: result")
        
        lines.append("```")
        return "\n".join(lines)

    def _generate_class_diagram(self, info: Dict) -> str:
        """Génère un diagramme de classes"""
        lines = ["```mermaid", "classDiagram"]
        main = info.get('name', 'Contract')
        
        lines.append(f"  class {main} {{")
        for func in info.get('functions', []):
            params = ", ".join([p.get('type', '') for p in func.get('params', [])])
            lines.append(f"    +{func.get('name')}({params}) {func.get('returns', 'void')}")
        lines.append("  }")
        
        lines.append("```")
        return "\n".join(lines)

    async def validate_diagram(self, diagram: str) -> Dict[str, Any]:
        """Valide la syntaxe d'un diagramme"""
        issues = []
        
        if not diagram.startswith("```mermaid"):
            issues.append("Le diagramme doit commencer par ```mermaid")
        
        if "classDiagram" in diagram:
            if "class" not in diagram:
                issues.append("Diagramme de classe sans classe")
        
        lines = diagram.split("\n")
        if len(lines) > 100:
            issues.append(f"Diagramme trop long: {len(lines)} lignes > 100")
        
        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "line_count": len(lines)
        }

    async def handle_generate_diagrams(self, message: Message) -> Message:
        content = message.content
        result = await self.generate_diagrams(
            content.get("contract_info", {}),
            content.get("types")
        )
        return Message(
            sender=self.__class__.__name__,
            recipient=message.sender,
            content=result,
            message_type="diagrams_generated",
            correlation_id=message.message_id
        )

    async def handle_generate_inheritance(self, message: Message) -> Message:
        diagram = self._generate_inheritance_diagram(message.content)
        return Message(
            sender=self.__class__.__name__,
            recipient=message.sender,
            content={"diagram": diagram, "type": "inheritance"},
            message_type="diagram_generated",
            correlation_id=message.message_id
        )

    async def handle_generate_dependencies(self, message: Message) -> Message:
        diagram = self._generate_dependencies_diagram(message.content)
        return Message(
            sender=self.__class__.__name__,
            recipient=message.sender,
            content={"diagram": diagram, "type": "dependencies"},
            message_type="diagram_generated",
            correlation_id=message.message_id
        )

    async def handle_generate_workflow(self, message: Message) -> Message:
        diagram = self._generate_workflow_diagram(message.content)
        return Message(
            sender=self.__class__.__name__,
            recipient=message.sender,
            content={"diagram": diagram, "type": "workflow"},
            message_type="diagram_generated",
            correlation_id=message.message_id
        )

    async def handle_generate_sequence(self, message: Message) -> Message:
        diagram = self._generate_sequence_diagram(message.content)
        return Message(
            sender=self.__class__.__name__,
            recipient=message.sender,
            content={"diagram": diagram, "type": "sequence"},
            message_type="diagram_generated",
            correlation_id=message.message_id
        )

    async def handle_validate_diagram(self, message: Message) -> Message:
        result = await self.validate_diagram(message.content.get("diagram", ""))
        return Message(
            sender=self.__class__.__name__,
            recipient=message.sender,
            content=result,
            message_type="diagram_validated",
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
        return {
            "status": self._status,
            "ready": self._initialized,
            "display_name": self._display_name,
            "stats": {
                "diagrams_generated": self._stats["diagrams_generated"],
                "diagrams_failed": self._stats["diagrams_failed"],
                "by_type": self._stats["by_type"]
            },
            "timestamp": datetime.now().isoformat()
        }

    def get_agent_info(self) -> Dict[str, Any]:
        return {
            "id": "DiagramGeneratorSubAgent",
            "name": self._display_name,
            "version": "2.2.0",
            "status": self._status,
            "capabilities": list(self._get_capability_handlers().keys()),
            "features": self._get_features(),
            "stats": {
                "diagrams_generated": self._stats["diagrams_generated"],
                "success_rate": round(
                    (self._stats["diagrams_generated"] / max(1, self._stats["diagrams_generated"] + self._stats["diagrams_failed"])) * 100, 2
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
            stats_file = Path("./reports") / "documenter" / "diagram_generator" / f"stats_{datetime.now().strftime('%Y%m%d')}.json"
            stats_file.parent.mkdir(parents=True, exist_ok=True)
            with open(stats_file, 'w') as f:
                json.dump(self._stats, f, indent=2, default=str)
        except Exception as e:
            self._logger.warning(f"Impossible de sauvegarder: {e}")
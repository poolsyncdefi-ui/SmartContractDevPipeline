"""
Outils utilitaires pour 📊 Générateur de Diagrammes
Version: 2.0.0 (ALIGNÉ SUR COMMUNICATION)
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
    """Valide la configuration du sous-agent"""
    required_fields = ["agent", "system", "diagram_generator"]
    return all(field in config for field in required_fields)


def serialize_diagram(obj: Any) -> str:
    """Sérialise un diagramme en JSON"""
    if isinstance(obj, datetime):
        return obj.isoformat()
    return str(obj)


def deserialize_diagram(data: str) -> Dict[str, Any]:
    """Désérialise un diagramme JSON"""
    return json.loads(data)


def calculate_backoff(attempt: int, base_delay: float = 1.0, max_delay: float = 60.0) -> float:
    """Calcule le délai de backoff exponentiel"""
    delay = base_delay * (2 ** (attempt - 1))
    return min(delay, max_delay)


def detect_diagram_type(content: str) -> str:
    """Détecte le type de diagramme à partir du contenu"""
    if content.startswith("@startuml"):
        return "plantuml"
    if "graph TD" in content or "flowchart" in content:
        return "mermaid"
    return "unknown"


def merge_diagrams(base: str, overlay: str) -> str:
    """Fusionne deux diagrammes"""
    if "```mermaid" in base and "```mermaid" in overlay:
        # Extraire le contenu Mermaid
        base_content = base.split("```mermaid")[1].split("```")[0].strip()
        overlay_content = overlay.split("```mermaid")[1].split("```")[0].strip()
        return f"```mermaid\n{base_content}\n{overlay_content}\n```"
    return overlay


def generate_node_id(prefix: str = "node") -> str:
    """Génère un ID de nœud unique"""
    import hashlib
    import time
    unique = f"{prefix}_{time.time()}"
    return hashlib.md5(unique.encode()).hexdigest()[:8]


def validate_mermaid_syntax(diagram: str) -> bool:
    """Valide basiquement la syntaxe Mermaid"""
    if not diagram:
        return False
    
    # Vérifications simples
    lines = diagram.strip().split('\n')
    first_line = lines[0].strip()
    
    if not any(first_line.startswith(t) for t in ["graph", "flowchart", "sequenceDiagram", "classDiagram", "stateDiagram", "erDiagram", "gantt", "pie"]):
        return False
    
    return True


def escape_mermaid_text(text: str) -> str:
    """Échappe les caractères spéciaux pour Mermaid"""
    special_chars = ['[', ']', '{', '}', '(', ')', '#', '.', '"', "'"]
    for char in special_chars:
        text = text.replace(char, f'\\{char}')
    return text
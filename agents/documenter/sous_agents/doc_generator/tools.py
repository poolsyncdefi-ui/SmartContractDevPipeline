"""
Outils utilitaires pour 📄 Générateur de Documentation
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
    required_fields = ["agent", "system", "doc_generator"]
    return all(field in config for field in required_fields)


def serialize_doc(obj: Any) -> str:
    """Sérialise un document en JSON"""
    if isinstance(obj, datetime):
        return obj.isoformat()
    return str(obj)


def deserialize_doc(data: str) -> Dict[str, Any]:
    """Désérialise un document JSON"""
    return json.loads(data)


def calculate_backoff(attempt: int, base_delay: float = 1.0, max_delay: float = 60.0) -> float:
    """Calcule le délai de backoff exponentiel"""
    delay = base_delay * (2 ** (attempt - 1))
    return min(delay, max_delay)


def generate_anchor(text: str) -> str:
    """Génère une ancre à partir d'un texte"""
    anchor = text.lower()
    anchor = ''.join(c if c.isalnum() else '-' for c in anchor)
    anchor = '-'.join(filter(None, anchor.split('-')))
    return anchor


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """Tronque un texte à une longueur maximale"""
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix


def merge_sections(base_sections: List[Dict], override_sections: List[Dict]) -> List[Dict]:
    """Fusionne deux listes de sections"""
    result = base_sections.copy()
    
    for section in override_sections:
        title = section.get('title')
        found = False
        for i, existing in enumerate(result):
            if existing.get('title') == title:
                result[i] = {**existing, **section}
                found = True
                break
        if not found:
            result.append(section)
    
    return result
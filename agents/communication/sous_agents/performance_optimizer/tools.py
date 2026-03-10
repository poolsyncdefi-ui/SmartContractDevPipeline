"""
Outils utilitaires pour ⚡ Optimisateur Performance Temps-Réel
Version: 2.0.0
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

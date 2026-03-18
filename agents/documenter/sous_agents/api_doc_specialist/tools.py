"""
Outils utilitaires pour 🔌 Spécialiste Documentation API
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
    required_fields = ["agent", "system", "api_doc_specialist"]
    return all(field in config for field in required_fields)


def serialize_api_spec(obj: Any) -> str:
    """Sérialise une spécification API en JSON"""
    if isinstance(obj, datetime):
        return obj.isoformat()
    return str(obj)


def deserialize_api_spec(data: str) -> Dict[str, Any]:
    """Désérialise une spécification API JSON"""
    return json.loads(data)


def calculate_backoff(attempt: int, base_delay: float = 1.0, max_delay: float = 60.0) -> float:
    """Calcule le délai de backoff exponentiel"""
    delay = base_delay * (2 ** (attempt - 1))
    return min(delay, max_delay)


def normalize_path(path: str) -> str:
    """Normalise un chemin d'API"""
    if not path.startswith('/'):
        path = '/' + path
    # Supprimer les slashs multiples
    import re
    path = re.sub('/+', '/', path)
    return path


def extract_path_parameters(path: str) -> List[str]:
    """Extrait les paramètres de chemin d'une URL"""
    import re
    return re.findall(r'{([^}]+)}', path)


def generate_operation_id(method: str, path: str) -> str:
    """Génère un operationId pour OpenAPI"""
    path_parts = path.strip('/').replace('{', '').replace('}', '').split('/')
    operation = method.lower()
    name = '_'.join(path_parts) if path_parts else 'root'
    return f"{operation}{name.capitalize()}"


def merge_openapi_specs(base: Dict, overlay: Dict) -> Dict:
    """Fusionne deux spécifications OpenAPI"""
    result = base.copy()
    
    if 'paths' in overlay:
        if 'paths' not in result:
            result['paths'] = {}
        result['paths'].update(overlay['paths'])
    
    if 'components' in overlay:
        if 'components' not in result:
            result['components'] = {}
        for comp_type, comps in overlay['components'].items():
            if comp_type not in result['components']:
                result['components'][comp_type] = {}
            result['components'][comp_type].update(comps)
    
    return result


def validate_email(email: str) -> bool:
    """Valide un format d'email"""
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def validate_url(url: str) -> bool:
    """Valide un format d'URL"""
    import re
    pattern = r'^https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+[^\s]*$'
    return bool(re.match(pattern, url))
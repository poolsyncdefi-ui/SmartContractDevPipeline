"""
Outils utilitaires pour 📖 Spécialiste README
Version: 2.0.0 (ALIGNÉ SUR COMMUNICATION)
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
import json
import re

logger = logging.getLogger(__name__)


def format_timestamp(timestamp: Optional[datetime] = None) -> str:
    """Formate un timestamp pour l'affichage"""
    if timestamp is None:
        timestamp = datetime.now()
    return timestamp.strftime("%Y-%m-%d %H:%M:%S")


def validate_config(config: Dict[str, Any]) -> bool:
    """Valide la configuration du sous-agent"""
    required_fields = ["agent", "system", "readme_specialist"]
    return all(field in config for field in required_fields)


def serialize_readme(obj: Any) -> str:
    """Sérialise un README en JSON"""
    if isinstance(obj, datetime):
        return obj.isoformat()
    return str(obj)


def deserialize_readme(data: str) -> Dict[str, Any]:
    """Désérialise un README JSON"""
    return json.loads(data)


def calculate_backoff(attempt: int, base_delay: float = 1.0, max_delay: float = 60.0) -> float:
    """Calcule le délai de backoff exponentiel"""
    delay = base_delay * (2 ** (attempt - 1))
    return min(delay, max_delay)


def extract_project_name_from_repo(url: str) -> str:
    """Extrait le nom du projet à partir d'une URL de repository"""
    match = re.search(r'/([^/]+?)(?:\.git)?$', url)
    if match:
        return match.group(1)
    return "project"


def format_badge_url(badge_type: str, value: str, color: str = "blue") -> str:
    """Formate une URL de badge shields.io"""
    return f"https://img.shields.io/badge/{badge_type}-{value}-{color}.svg"


def detect_project_type_from_files(files: List[str]) -> str:
    """Détecte le type de projet à partir de la liste des fichiers"""
    file_set = set(files)
    
    if "setup.py" in file_set or "requirements.txt" in file_set:
        return "python"
    elif "package.json" in file_set:
        if "next.config.js" in file_set or "next.config.ts" in file_set:
            return "nextjs"
        return "node"
    elif "Cargo.toml" in file_set:
        return "rust"
    elif "go.mod" in file_set:
        return "go"
    elif "pom.xml" in file_set or "build.gradle" in file_set:
        return "java"
    elif "hardhat.config.js" in file_set or "foundry.toml" in file_set:
        return "solidity"
    
    return "generic"


def generate_anchor(text: str) -> str:
    """Génère une ancre à partir d'un titre"""
    anchor = text.lower()
    anchor = re.sub(r'[^\w\s-]', '', anchor)
    anchor = re.sub(r'[-\s]+', '-', anchor)
    return anchor


def merge_readmes(base: str, overlay: str) -> str:
    """Fusionne deux README (overlay remplace les sections existantes)"""
    # Simple implémentation: le overlay remplace le base
    return overlay if overlay else base


def validate_readme(readme: str) -> Dict[str, Any]:
    """Valide un README"""
    issues = []
    
    lines = readme.split('\n')
    
    # Vérifier la présence d'un titre
    if not any(line.startswith('# ') for line in lines):
        issues.append("Missing main title (# Title)")
    
    # Vérifier la présence de sections communes
    required_sections = ["## Installation", "## Usage", "## License"]
    for section in required_sections:
        if not any(section in line for line in lines):
            issues.append(f"Missing section: {section}")
    
    return {
        "valid": len(issues) == 0,
        "issues": issues,
        "line_count": len(lines),
        "section_count": sum(1 for line in lines if line.startswith('## '))
    }
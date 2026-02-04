"""
Package agents.base_agent - Classe de base pour tous les agents
"""

from .agent import BaseAgent, AgentUtils

__version__ = "1.0.0"
__author__ = "SmartContractDevPipeline Team"
__license__ = "MIT"

__all__ = [
    "BaseAgent",
    "AgentUtils"
]

# Exports pour compatibilité
BaseAgent = BaseAgent
AgentUtils = AgentUtils

# Informations sur le package
PACKAGE_INFO = {
    "name": "base_agent",
    "version": __version__,
    "description": "Classe de base pour tous les agents du pipeline SmartContractDevPipeline",
    "author": __author__,
    "license": __license__,
    "dependencies": ["pyyaml>=6.0", "typing-extensions>=4.0"],
    "python_version": ">=3.8"
}

# Vérification des dépendances au chargement
def _check_dependencies():
    """Vérifie les dépendances requises"""
    import sys
    
    # Vérification version Python
    if sys.version_info < (3, 8):
        raise RuntimeError(f"Python 3.8 ou supérieur requis (version actuelle: {sys.version})")
    
    # Vérification des packages
    missing_packages = []
    try:
        import yaml
    except ImportError:
        missing_packages.append("pyyaml")
    
    try:
        from typing import get_origin
    except ImportError:
        missing_packages.append("typing-extensions")
    
    if missing_packages:
        raise ImportError(
            f"Packages manquants: {', '.join(missing_packages)}. "
            f"Installez-les avec: pip install {' '.join(missing_packages)}"
        )
    
    return True

# Exécuter la vérification
_dependencies_checked = False
if not _dependencies_checked:
    _check_dependencies()
    _dependencies_checked = True

# Configuration par défaut
DEFAULT_CONFIG = {
    "agent": {
        "name": "BaseAgent",
        "version": "1.0.0",
        "type": "abstract_base"
    },
    "capabilities": [
        "health_check",
        "execute_tasks",
        "load_configuration"
    ]
}

# Utilitaires d'import
def create_base_agent(config_path: str = None, **kwargs):
    """
    Crée une instance de BaseAgent avec la configuration fournie
    
    Args:
        config_path: Chemin vers le fichier de configuration YAML
        **kwargs: Arguments supplémentaires pour le constructeur
    
    Returns:
        Instance de BaseAgent
    """
    return BaseAgent(config_path=config_path, **kwargs)

def get_agent_info() -> dict:
    """
    Retourne les informations sur le package base_agent
    
    Returns:
        Dict avec les informations du package
    """
    return PACKAGE_INFO.copy()
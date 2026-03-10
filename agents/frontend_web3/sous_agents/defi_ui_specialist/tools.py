"""
Outils utilitaires pour 📊 Spécialiste Interfaces DeFi Avancées
Version: 2.0.0
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

logger = logging.getLogger(__name__)


def format_timestamp(timestamp: Optional[datetime] = None) -> str:
    """Formate un timestamp pour l'affichage"""
    if timestamp is None:
        timestamp = datetime.now()
    return timestamp.strftime("%Y-%m-%d %H:%M:%S")

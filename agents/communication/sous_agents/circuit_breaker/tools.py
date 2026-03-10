"""
Outils utilitaires pour Circuit Breaker SubAgent
"""

import logging
import time
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import json

logger = logging.getLogger(__name__)


def calculate_backoff(attempt: int, base_delay: float = 1.0, max_delay: float = 60.0) -> float:
    """
    Calcule le délai de backoff exponentiel pour les tentatives
    
    Args:
        attempt: Numéro de tentative (1, 2, 3...)
        base_delay: Délai de base en secondes
        max_delay: Délai maximum en secondes
    
    Returns:
        Délai à attendre en secondes
    """
    delay = base_delay * (2 ** (attempt - 1))
    return min(delay, max_delay)


def format_circuit_state(state: str) -> str:
    """
    Formate un état de circuit pour affichage
    
    Args:
        state: État du circuit (closed, open, half_open, etc.)
    
    Returns:
        État formaté avec emoji
    """
    emojis = {
        "closed": "🟢 FERMÉ",
        "open": "🔴 OUVERT",
        "half_open": "🟡 MI-OUVERT",
        "half-open": "🟡 MI-OUVERT",
        "forced_open": "⚫ FORCÉ",
        "forced-open": "⚫ FORCÉ",
        "disabled": "⚪ DÉSACTIVÉ"
    }
    return emojis.get(state.lower(), f"❓ {state}")


def analyze_circuit_health(stats: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analyse la santé d'un circuit à partir de ses statistiques
    
    Args:
        stats: Statistiques du circuit
    
    Returns:
        Analyse de santé avec recommandations
    """
    health_score = 100
    issues = []
    recommendations = []
    
    failure_rate = stats.get("failure_rate", 0)
    consecutive_failures = stats.get("consecutive_failures", 0)
    state = stats.get("state", "unknown")
    
    # Évaluer le taux d'échec
    if failure_rate > 50:
        health_score -= 30
        issues.append(f"Taux d'échec critique: {failure_rate}%")
        recommendations.append("Vérifier le service cible immédiatement")
    elif failure_rate > 20:
        health_score -= 15
        issues.append(f"Taux d'échec élevé: {failure_rate}%")
        recommendations.append("Surveiller le service cible")
    
    # Évaluer les échecs consécutifs
    if consecutive_failures > 10:
        health_score -= 25
        issues.append(f"Échecs consécutifs: {consecutive_failures}")
        recommendations.append("Circuit devrait être ouvert")
    elif consecutive_failures > 5:
        health_score -= 10
        issues.append(f"Échecs consécutifs: {consecutive_failures}")
    
    # Évaluer l'état
    if state == "open":
        health_score -= 20
        recommendations.append("Vérifier la récupération du service")
    elif state == "half_open":
        health_score -= 5
        recommendations.append("Tests de reprise en cours")
    
    return {
        "health_score": max(0, health_score),
        "status": "CRITICAL" if health_score < 50 else "WARNING" if health_score < 80 else "HEALTHY",
        "issues": issues,
        "recommendations": recommendations[:3]  # Top 3 recommandations
    }


def serialize_circuit_data(data: Dict[str, Any]) -> str:
    """
    Sérialise les données d'un circuit pour persistance
    
    Args:
        data: Données du circuit
    
    Returns:
        JSON string
    """
    def json_serializer(obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        if isinstance(obj, timedelta):
            return obj.total_seconds()
        raise TypeError(f"Type {type(obj)} non sérialisable")
    
    return json.dumps(data, default=json_serializer, indent=2)


def deserialize_circuit_data(json_str: str) -> Dict[str, Any]:
    """
    Désérialise les données d'un circuit
    
    Args:
        json_str: JSON string
    
    Returns:
        Données du circuit
    """
    return json.loads(json_str)


def merge_circuit_configs(base_config: Dict, override_config: Dict) -> Dict:
    """
    Fusionne deux configurations de circuit (base + override)
    
    Args:
        base_config: Configuration de base
        override_config: Configuration à surcharger
    
    Returns:
        Configuration fusionnée
    """
    result = base_config.copy()
    
    for key, value in override_config.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = merge_circuit_configs(result[key], value)
        else:
            result[key] = value
    
    return result


def calculate_recovery_time(stats: Dict[str, Any]) -> Optional[float]:
    """
    Calcule le temps estimé de récupération
    
    Args:
        stats: Statistiques du circuit
    
    Returns:
        Temps estimé en secondes, ou None si non disponible
    """
    if stats.get("state") != "open":
        return None
    
    opened_at = stats.get("opened_at")
    if not opened_at:
        return None
    
    try:
        if isinstance(opened_at, str):
            opened_at = datetime.fromisoformat(opened_at)
        
        timeout = stats.get("timeout_seconds", 30)
        elapsed = (datetime.now() - opened_at).total_seconds()
        
        return max(0, timeout - elapsed)
    except:
        return None
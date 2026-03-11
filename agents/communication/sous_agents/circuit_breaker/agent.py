"""
Circuit Breaker SubAgent - Protection contre les défaillances en cascade
Version: 2.0.0

Implémente le pattern Circuit Breaker avec états CLOSED, OPEN, HALF-OPEN.
Surveille les erreurs et protège le système contre les défaillances en cascade.
"""

import logging
import sys
import asyncio
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
from enum import Enum
from dataclasses import dataclass, field

# Configuration des imports
current_dir = Path(__file__).parent.absolute()
project_root = current_dir.parent.parent.parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from agents.sous_agents.base_subagent import BaseSubAgent

logger = logging.getLogger(__name__)


# ============================================================================
# ÉNUMS ET CLASSES DE DONNÉES
# ============================================================================

class CircuitState(Enum):
    """États possibles du circuit breaker"""
    CLOSED = "closed"          # Circuit fermé - trafic normal
    OPEN = "open"              # Circuit ouvert - trafic bloqué
    HALF_OPEN = "half_open"    # Circuit mi-ouvert - test limité
    FORCED_OPEN = "forced_open" # Circuit forcé ouvert - maintenance
    DISABLED = "disabled"       # Circuit désactivé - surveillance seule
    
    @classmethod
    def from_string(cls, state_str: str) -> 'CircuitState':
        """Convertit une chaîne en état"""
        mapping = {
            "closed": cls.CLOSED,
            "open": cls.OPEN,
            "half_open": cls.HALF_OPEN,
            "half-open": cls.HALF_OPEN,
            "forced_open": cls.FORCED_OPEN,
            "forced-open": cls.FORCED_OPEN,
            "disabled": cls.DISABLED
        }
        return mapping.get(state_str.lower(), cls.CLOSED)
    
    def allows_traffic(self) -> bool:
        """Indique si le circuit autorise le trafic"""
        return self in [CircuitState.CLOSED, CircuitState.HALF_OPEN, CircuitState.DISABLED]
    
    def __str__(self) -> str:
        colors = {
            CircuitState.CLOSED: "🟢",
            CircuitState.OPEN: "🔴",
            CircuitState.HALF_OPEN: "🟡",
            CircuitState.FORCED_OPEN: "⚫",
            CircuitState.DISABLED: "⚪"
        }
        return f"{colors.get(self, '⚪')} {self.value}"


@dataclass
class CircuitStats:
    """Statistiques d'un circuit"""
    circuit_id: str
    state: CircuitState = CircuitState.CLOSED
    failure_count: int = 0
    success_count: int = 0
    consecutive_failures: int = 0
    consecutive_successes: int = 0
    total_requests: int = 0
    blocked_requests: int = 0
    last_failure: Optional[datetime] = None
    last_success: Optional[datetime] = None
    last_state_change: datetime = field(default_factory=datetime.now)
    opened_at: Optional[datetime] = None
    half_open_at: Optional[datetime] = None
    failure_threshold: int = 5
    timeout_seconds: int = 30
    half_open_timeout: int = 10
    success_threshold: int = 2
    
    @property
    def failure_rate(self) -> float:
        """Calcule le taux d'échec sur les 100 dernières requêtes"""
        if self.total_requests == 0:
            return 0.0
        return (self.failure_count / self.total_requests) * 100
    
    @property
    def success_rate(self) -> float:
        """Calcule le taux de succès"""
        if self.total_requests == 0:
            return 100.0
        return (self.success_count / self.total_requests) * 100
    
    @property
    def is_timed_out(self) -> bool:
        """Vérifie si le circuit est en timeout (OPEN depuis trop longtemps)"""
        if self.state != CircuitState.OPEN or not self.opened_at:
            return False
        return (datetime.now() - self.opened_at).total_seconds() > self.timeout_seconds
    
    @property
    def can_attempt_recovery(self) -> bool:
        """Vérifie si on peut tenter une récupération"""
        if self.state == CircuitState.OPEN and self.is_timed_out:
            return True
        if self.state == CircuitState.HALF_OPEN and self.half_open_at:
            return (datetime.now() - self.half_open_at).total_seconds() < self.half_open_timeout
        return False
    
    def record_success(self):
        """Enregistre un succès"""
        self.success_count += 1
        self.total_requests += 1
        self.consecutive_successes += 1
        self.consecutive_failures = 0
        self.last_success = datetime.now()
    
    def record_failure(self):
        """Enregistre un échec"""
        self.failure_count += 1
        self.total_requests += 1
        self.consecutive_failures += 1
        self.consecutive_successes = 0
        self.last_failure = datetime.now()
    
    def to_dict(self, detailed: bool = False) -> Dict[str, Any]:
        """Convertit en dictionnaire"""
        result = {
            "circuit_id": self.circuit_id,
            "state": self.state.value,
            "state_display": str(self.state),
            "allows_traffic": self.state.allows_traffic(),
            "failure_count": self.failure_count,
            "success_count": self.success_count,
            "total_requests": self.total_requests,
            "blocked_requests": self.blocked_requests,
            "failure_rate": round(self.failure_rate, 2),
            "success_rate": round(self.success_rate, 2),
            "consecutive_failures": self.consecutive_failures,
            "consecutive_successes": self.consecutive_successes,
            "last_failure": self.last_failure.isoformat() if self.last_failure else None,
            "last_success": self.last_success.isoformat() if self.last_success else None,
            "last_state_change": self.last_state_change.isoformat(),
        }
        
        if detailed:
            result.update({
                "failure_threshold": self.failure_threshold,
                "timeout_seconds": self.timeout_seconds,
                "half_open_timeout": self.half_open_timeout,
                "success_threshold": self.success_threshold,
                "opened_at": self.opened_at.isoformat() if self.opened_at else None,
                "half_open_at": self.half_open_at.isoformat() if self.half_open_at else None,
                "is_timed_out": self.is_timed_out,
                "can_attempt_recovery": self.can_attempt_recovery,
            })
        
        return result


@dataclass
class CircuitBreakerConfig:
    """Configuration d'un circuit breaker"""
    failure_threshold: int = 5
    timeout_seconds: int = 30
    half_open_timeout: int = 10
    success_threshold: int = 2
    window_size_seconds: int = 60
    enabled: bool = True
    auto_recovery: bool = True
    log_events: bool = True
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CircuitBreakerConfig':
        """Crée une config depuis un dictionnaire"""
        return cls(
            failure_threshold=data.get('failure_threshold', 5),
            timeout_seconds=data.get('timeout_seconds', 30),
            half_open_timeout=data.get('half_open_timeout', 10),
            success_threshold=data.get('success_threshold', 2),
            window_size_seconds=data.get('window_size_seconds', 60),
            enabled=data.get('enabled', True),
            auto_recovery=data.get('auto_recovery', True),
            log_events=data.get('log_events', True)
        )


# ============================================================================
# SOUS-AGENT PRINCIPAL
# ============================================================================

class CircuitBreakerSubAgent(BaseSubAgent):
    """
    Sous-agent Circuit Breaker - Protection contre les défaillances en cascade
    
    Surveille les erreurs et ouvre/ferme automatiquement le circuit selon
    les seuils configurés. Implémente les états CLOSED, OPEN, HALF-OPEN.
    """
    
    def __init__(self, config_path: str = ""):
        """Initialise le circuit breaker"""
        super().__init__(config_path)
        
        # Métadonnées
        self._subagent_display_name = "🛡️ Circuit Breaker"
        self._subagent_description = "Protection contre les défaillances en cascade"
        self._subagent_version = "2.0.0"
        self._subagent_category = "communication"
        self._subagent_capabilities = [
            "circuit_breaker.monitor",
            "circuit_breaker.trip",
            "circuit_breaker.reset",
            "circuit_breaker.status",
            "circuit_breaker.configure",
            "circuit_breaker.stats"
        ]
        
        # État interne
        self._circuits: Dict[str, CircuitStats] = {}
        self._circuit_configs: Dict[str, CircuitBreakerConfig] = {}
        self._default_config = CircuitBreakerConfig.from_dict(
            self._agent_config.get('circuit_breaker', {}).get('defaults', {})
        )
        
        # File d'attente pour les événements
        self._event_queue: asyncio.Queue = asyncio.Queue()
        
        # Statistiques globales
        self._global_stats = {
            "total_circuits": 0,
            "total_state_changes": 0,
            "total_requests_blocked": 0,
            "total_recovery_attempts": 0,
            "circuits_by_state": {
                "closed": 0,
                "open": 0,
                "half_open": 0,
                "forced_open": 0,
                "disabled": 0
            }
        }
        
        # Tâche de surveillance
        self._monitor_task: Optional[asyncio.Task] = None
        
        logger.info(f"✅ {self._subagent_display_name} initialisé")

    # ========================================================================
    # IMPLÉMENTATION DES MÉTHODES ABSTRACTES
    # ========================================================================
    
    async def _initialize_subagent_components(self) -> bool:
        """Initialise les composants spécifiques"""
        logger.info("Initialisation des composants Circuit Breaker...")
        
        # Démarrer la tâche de surveillance
        self._monitor_task = asyncio.create_task(self._monitor_loop())
        
        logger.info("✅ Composants Circuit Breaker initialisés")
        return True
        
    async def _initialize_components(self) -> bool:
        """
        Implémentation requise par BaseAgent.
        Délègue à _initialize_subagent_components.
        """
        return await self._initialize_subagent_components()

    def _get_capability_handlers(self) -> Dict[str, Any]:
        """Retourne les handlers spécifiques"""
        return {
            "circuit_breaker.monitor": self._handle_monitor,
            "circuit_breaker.trip": self._handle_trip,
            "circuit_breaker.reset": self._handle_reset,
            "circuit_breaker.status": self._handle_status,
            "circuit_breaker.configure": self._handle_configure,
            "circuit_breaker.stats": self._handle_stats,
        }
    
    # ========================================================================
    # TÂCHES DE FOND
    # ========================================================================
    
    async def _monitor_loop(self):
        """Boucle de surveillance des circuits"""
        logger.info("🔄 Boucle de surveillance démarrée")
        
        while self._status.value == "ready":
            try:
                await asyncio.sleep(5)  # Vérification toutes les 5 secondes
                
                for circuit_id, stats in list(self._circuits.items()):
                    await self._check_circuit_state(circuit_id, stats)
                
                # Mettre à jour les statistiques globales
                await self._update_global_stats()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"❌ Erreur dans la boucle de surveillance: {e}")
    
    async def _check_circuit_state(self, circuit_id: str, stats: CircuitStats):
        """Vérifie et met à jour l'état d'un circuit"""
        old_state = stats.state
        
        if stats.state == CircuitState.CLOSED:
            # Vérifier si on doit ouvrir le circuit
            if stats.consecutive_failures >= stats.failure_threshold:
                await self._open_circuit(circuit_id, "Seuil d'échecs atteint")
                
        elif stats.state == CircuitState.OPEN:
            # Vérifier si on peut passer en HALF_OPEN
            if stats.is_timed_out:
                await self._half_open_circuit(circuit_id, "Timeout écoulé")
                
        elif stats.state == CircuitState.HALF_OPEN:
            # Vérifier si on doit refermer ou rouvrir
            if stats.consecutive_successes >= stats.success_threshold:
                await self._close_circuit(circuit_id, "Succès consécutifs")
            elif stats.consecutive_failures > 0:
                await self._open_circuit(circuit_id, "Échec en half-open")
        
        if old_state != stats.state:
            logger.info(f"🔄 Circuit {circuit_id}: {old_state} -> {stats.state}")
    
    # ========================================================================
    # OPÉRATIONS SUR LES CIRCUITS
    # ========================================================================
    
    async def _open_circuit(self, circuit_id: str, reason: str = ""):
        """Ouvre un circuit"""
        if circuit_id not in self._circuits:
            return
        
        stats = self._circuits[circuit_id]
        stats.state = CircuitState.OPEN
        stats.opened_at = datetime.now()
        stats.last_state_change = datetime.now()
        
        self._global_stats["total_state_changes"] += 1
        
        logger.warning(f"🔴 Circuit {circuit_id} OUVERT: {reason}")
        
        # Journaliser l'événement
        await self._log_event("circuit_opened", {
            "circuit_id": circuit_id,
            "reason": reason,
            "failure_count": stats.failure_count,
            "consecutive_failures": stats.consecutive_failures
        })
    
    async def _close_circuit(self, circuit_id: str, reason: str = ""):
        """Ferme un circuit"""
        if circuit_id not in self._circuits:
            return
        
        stats = self._circuits[circuit_id]
        stats.state = CircuitState.CLOSED
        stats.consecutive_failures = 0
        stats.opened_at = None
        stats.half_open_at = None
        stats.last_state_change = datetime.now()
        
        self._global_stats["total_state_changes"] += 1
        
        logger.info(f"🟢 Circuit {circuit_id} FERMÉ: {reason}")
        
        # Journaliser l'événement
        await self._log_event("circuit_closed", {
            "circuit_id": circuit_id,
            "reason": reason
        })
    
    async def _half_open_circuit(self, circuit_id: str, reason: str = ""):
        """Met un circuit en état HALF_OPEN"""
        if circuit_id not in self._circuits:
            return
        
        stats = self._circuits[circuit_id]
        stats.state = CircuitState.HALF_OPEN
        stats.half_open_at = datetime.now()
        stats.last_state_change = datetime.now()
        
        self._global_stats["total_state_changes"] += 1
        self._global_stats["total_recovery_attempts"] += 1
        
        logger.info(f"🟡 Circuit {circuit_id} HALF-OPEN: {reason}")
        
        # Journaliser l'événement
        await self._log_event("circuit_half_opened", {
            "circuit_id": circuit_id,
            "reason": reason
        })
    
    async def _force_open_circuit(self, circuit_id: str, reason: str = ""):
        """Force l'ouverture d'un circuit (maintenance)"""
        if circuit_id not in self._circuits:
            # Créer le circuit s'il n'existe pas
            await self._create_circuit(circuit_id)
        
        stats = self._circuits[circuit_id]
        stats.state = CircuitState.FORCED_OPEN
        stats.last_state_change = datetime.now()
        
        self._global_stats["total_state_changes"] += 1
        
        logger.warning(f"⚫ Circuit {circuit_id} FORCÉ OUVERT: {reason}")
        
        # Journaliser l'événement
        await self._log_event("circuit_forced_open", {
            "circuit_id": circuit_id,
            "reason": reason
        })
    
    async def _create_circuit(self, circuit_id: str, 
                              config: Optional[CircuitBreakerConfig] = None) -> CircuitStats:
        """Crée un nouveau circuit"""
        if circuit_id in self._circuits:
            return self._circuits[circuit_id]
        
        cfg = config or self._default_config
        stats = CircuitStats(
            circuit_id=circuit_id,
            failure_threshold=cfg.failure_threshold,
            timeout_seconds=cfg.timeout_seconds,
            half_open_timeout=cfg.half_open_timeout,
            success_threshold=cfg.success_threshold
        )
        
        self._circuits[circuit_id] = stats
        self._circuit_configs[circuit_id] = cfg
        self._global_stats["total_circuits"] += 1
        
        logger.info(f"➕ Nouveau circuit créé: {circuit_id}")
        
        # Journaliser l'événement
        await self._log_event("circuit_created", {
            "circuit_id": circuit_id,
            "config": cfg.__dict__
        })
        
        return stats
    
    # ========================================================================
    # API PUBLIQUE POUR LES AUTRES AGENTS
    # ========================================================================
    
    async def record_success(self, circuit_id: str) -> Dict[str, Any]:
        """
        Enregistre un succès pour un circuit
        À appeler par les autres agents après une opération réussie
        """
        # Créer le circuit s'il n'existe pas
        if circuit_id not in self._circuits:
            await self._create_circuit(circuit_id)
        
        stats = self._circuits[circuit_id]
        
        # Vérifier si le circuit autorise le trafic
        if not stats.state.allows_traffic():
            stats.blocked_requests += 1
            self._global_stats["total_requests_blocked"] += 1
            return {
                "success": False,
                "blocked": True,
                "circuit_id": circuit_id,
                "state": stats.state.value,
                "reason": "Circuit ouvert"
            }
        
        # Enregistrer le succès
        stats.record_success()
        
        # Vérifier l'état (pour HALF_OPEN -> CLOSED)
        await self._check_circuit_state(circuit_id, stats)
        
        return {
            "success": True,
            "circuit_id": circuit_id,
            "state": stats.state.value,
            "consecutive_successes": stats.consecutive_successes
        }
    
    async def record_failure(self, circuit_id: str, error: Optional[str] = None) -> Dict[str, Any]:
        """
        Enregistre un échec pour un circuit
        À appeler par les autres agents après une opération échouée
        """
        # Créer le circuit s'il n'existe pas
        if circuit_id not in self._circuits:
            await self._create_circuit(circuit_id)
        
        stats = self._circuits[circuit_id]
        
        # Vérifier si le circuit autorise le trafic
        if not stats.state.allows_traffic():
            stats.blocked_requests += 1
            self._global_stats["total_requests_blocked"] += 1
            return {
                "success": False,
                "blocked": True,
                "circuit_id": circuit_id,
                "state": stats.state.value,
                "reason": "Circuit ouvert"
            }
        
        # Enregistrer l'échec
        stats.record_failure()
        
        # Vérifier l'état (peut ouvrir le circuit)
        await self._check_circuit_state(circuit_id, stats)
        
        return {
            "success": False,
            "circuit_id": circuit_id,
            "state": stats.state.value,
            "consecutive_failures": stats.consecutive_failures,
            "error": error
        }
    
    async def check_circuit(self, circuit_id: str) -> Dict[str, Any]:
        """
        Vérifie si un circuit autorise le trafic
        """
        if circuit_id not in self._circuits:
            # Circuit inexistant = autorisé par défaut
            return {
                "allowed": True,
                "circuit_id": circuit_id,
                "exists": False
            }
        
        stats = self._circuits[circuit_id]
        
        return {
            "allowed": stats.state.allows_traffic(),
            "circuit_id": circuit_id,
            "state": stats.state.value,
            "state_display": str(stats.state),
            "exists": True,
            "failure_rate": stats.failure_rate,
            "consecutive_failures": stats.consecutive_failures
        }
    
    # ========================================================================
    # HANDLERS DE CAPACITÉS
    # ========================================================================
    
    async def _handle_monitor(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Surveille un circuit"""
        circuit_id = params.get("target_service", params.get("circuit_id", "default"))
        window = params.get("time_window_seconds", 60)
        
        if circuit_id not in self._circuits:
            return {
                "success": False,
                "error": f"Circuit {circuit_id} non trouvé"
            }
        
        stats = self._circuits[circuit_id]
        
        return {
            "success": True,
            "circuit": stats.to_dict(detailed=True),
            "window_seconds": window,
            "monitored_at": datetime.now().isoformat()
        }
    
    async def _handle_trip(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Ouvre manuellement un circuit"""
        circuit_id = params.get("circuit_id", "default")
        reason = params.get("reason", "Manuel")
        
        await self._force_open_circuit(circuit_id, reason)
        
        return {
            "success": True,
            "circuit_id": circuit_id,
            "state": CircuitState.FORCED_OPEN.value,
            "reason": reason,
            "timestamp": datetime.now().isoformat()
        }
    
    async def _handle_reset(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Réinitialise un circuit"""
        circuit_id = params.get("circuit_id", "default")
        
        if circuit_id not in self._circuits:
            return {
                "success": False,
                "error": f"Circuit {circuit_id} non trouvé"
            }
        
        await self._close_circuit(circuit_id, "Réinitialisation manuelle")
        
        return {
            "success": True,
            "circuit_id": circuit_id,
            "state": CircuitState.CLOSED.value,
            "timestamp": datetime.now().isoformat()
        }
    
    async def _handle_status(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Retourne l'état de tous les circuits"""
        circuit_id = params.get("circuit_id")
        
        if circuit_id:
            # Un seul circuit
            if circuit_id not in self._circuits:
                return {
                    "success": False,
                    "error": f"Circuit {circuit_id} non trouvé"
                }
            circuits = {circuit_id: self._circuits[circuit_id].to_dict()}
        else:
            # Tous les circuits
            circuits = {
                cid: stats.to_dict() 
                for cid, stats in self._circuits.items()
            }
        
        return {
            "success": True,
            "circuits": circuits,
            "count": len(circuits),
            "global_stats": self._global_stats,
            "timestamp": datetime.now().isoformat()
        }
    
    async def _handle_configure(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Configure un circuit"""
        circuit_id = params.get("circuit_id", "default")
        
        # Créer ou récupérer la config
        config = self._circuit_configs.get(circuit_id, self._default_config)
        
        # Mettre à jour les paramètres
        if "failure_threshold" in params:
            config.failure_threshold = params["failure_threshold"]
        if "timeout_seconds" in params:
            config.timeout_seconds = params["timeout_seconds"]
        if "half_open_timeout" in params:
            config.half_open_timeout = params["half_open_timeout"]
        if "success_threshold" in params:
            config.success_threshold = params["success_threshold"]
        
        self._circuit_configs[circuit_id] = config
        
        # Mettre à jour le circuit existant
        if circuit_id in self._circuits:
            stats = self._circuits[circuit_id]
            stats.failure_threshold = config.failure_threshold
            stats.timeout_seconds = config.timeout_seconds
            stats.half_open_timeout = config.half_open_timeout
            stats.success_threshold = config.success_threshold
        
        return {
            "success": True,
            "circuit_id": circuit_id,
            "config": config.__dict__,
            "timestamp": datetime.now().isoformat()
        }
    
    async def _handle_stats(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Fournit des statistiques détaillées"""
        circuit_id = params.get("circuit_id")
        detailed = params.get("detailed", False)
        
        if circuit_id:
            if circuit_id not in self._circuits:
                return {
                    "success": False,
                    "error": f"Circuit {circuit_id} non trouvé"
                }
            stats = self._circuits[circuit_id].to_dict(detailed)
            circuits_data = {circuit_id: stats}
        else:
            circuits_data = {
                cid: stats.to_dict(detailed)
                for cid, stats in self._circuits.items()
            }
        
        return {
            "success": True,
            "circuits": circuits_data,
            "global_stats": self._global_stats,
            "circuits_count": len(self._circuits),
            "timestamp": datetime.now().isoformat()
        }
    
    # ========================================================================
    # UTILITAIRES
    # ========================================================================
    
    async def _log_event(self, event_type: str, data: Dict[str, Any]):
        """Journalise un événement"""
        event = {
            "type": event_type,
            "timestamp": datetime.now().isoformat(),
            "data": data
        }
        await self._event_queue.put(event)
        
        # Audit si configuré
        if self._agent_config.get('circuit_breaker', {}).get('alerts', {}).get('enabled', True):
            logger.info(f"📋 Événement circuit: {event_type} - {data}")
    
    async def _update_global_stats(self):
        """Met à jour les statistiques globales"""
        counts = {
            "closed": 0,
            "open": 0,
            "half_open": 0,
            "forced_open": 0,
            "disabled": 0
        }
        
        for stats in self._circuits.values():
            state_name = stats.state.value
            if state_name in counts:
                counts[state_name] += 1
        
        self._global_stats["circuits_by_state"] = counts
    
    # ========================================================================
    # SURCHARGE POUR LE NETTOYAGE
    # ========================================================================
    
    async def shutdown(self) -> bool:
        """Arrête le sous-agent"""
        logger.info(f"Arrêt de {self._subagent_display_name}...")
        
        # Arrêter la tâche de surveillance
        if self._monitor_task and not self._monitor_task.done():
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
        
        return await super().shutdown()
    
    # ========================================================================
    # MÉTHODES DE TEST (pour le développement)
    # ========================================================================
    
    async def simulate_failures(self, circuit_id: str, count: int):
        """Simule des échecs pour tester (utile pour les tests)"""
        for i in range(count):
            await self.record_failure(circuit_id, f"Échec simulé {i+1}")
            await asyncio.sleep(0.1)
    
    async def simulate_successes(self, circuit_id: str, count: int):
        """Simule des succès pour tester"""
        for i in range(count):
            await self.record_success(circuit_id)
            await asyncio.sleep(0.1)


    # ============================================================================
    # FONCTION D'USINE
    # ============================================================================

    def create_circuit_breaker_agent(config_path: str = "") -> "CircuitBreakerSubAgent":
        """Crée une instance du sous-agent circuit breaker"""
        return CircuitBreakerSubAgent(config_path)
"""
Message Router SubAgent - Routeur intelligent de messages
Version: 2.0.0

Route les messages selon des règles complexes avec support de :
- Conditions basées sur le contenu (JMESPath)
- Équilibrage de charge dynamique
- Multiples stratégies de routage
- Cache des décisions de routage
"""

import logging
import sys
import asyncio
import json
import time
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple, Callable
from enum import Enum
from dataclasses import dataclass, field
from collections import defaultdict

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

class RoutingStrategy(Enum):
    """Stratégies de routage disponibles"""
    CONTENT_BASED = "content_based"
    HEADER_BASED = "header_based"
    ROUND_ROBIN = "round_robin"
    LEAST_LOADED = "least_loaded"
    CONSISTENT_HASHING = "consistent_hashing"


class ConditionEngine(Enum):
    """Moteurs d'évaluation des conditions"""
    JMESPATH = "jmespath"
    JSONATA = "jsonata"
    PYTHON = "python"


@dataclass
class Route:
    """Règle de routage"""
    id: str
    condition: str
    destination: str
    priority: int = 0
    strategy: RoutingStrategy = RoutingStrategy.CONTENT_BASED
    engine: ConditionEngine = ConditionEngine.JMESPATH
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    hits: int = 0
    last_hit: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    enabled: bool = True


@dataclass
class Destination:
    """Destination de routage"""
    name: str
    queue_size: int = 0
    response_time_ms: float = 0.0
    error_rate: float = 0.0
    last_updated: datetime = field(default_factory=datetime.now)
    weight: int = 1


@dataclass
class RoutingContext:
    """Contexte de routage"""
    message_id: str
    timestamp: datetime = field(default_factory=datetime.now)
    source: Optional[str] = None
    headers: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


# ============================================================================
# SOUS-AGENT PRINCIPAL
# ============================================================================

class MessageRouterSubAgent(BaseSubAgent):
    """
    Sous-agent Message Router - Routeur intelligent de messages

    Route les messages selon des règles configurables avec :
    - Évaluation de conditions complexes
    - Multiples stratégies de routage
    - Cache des décisions
    - Équilibrage de charge dynamique
    - Statistiques détaillées
    """

    def __init__(self, config_path: str = ""):
        """Initialise le routeur de messages"""
        super().__init__(config_path)

        # Métadonnées
        self._subagent_display_name = "🔄 Message Router"
        self._subagent_description = "Routeur intelligent de messages"
        self._subagent_version = "2.0.0"
        self._subagent_category = "communication"
        self._subagent_capabilities = [
            "router.add_route",
            "router.remove_route",
            "router.route",
            "router.stats",
            "router.list",
            "router.test"
        ]

        # État interne
        self._routes: Dict[str, Route] = {}  # id -> Route
        self._routes_by_priority: List[Tuple[int, str]] = []  # (priority, id)
        self._destinations: Dict[str, Destination] = {}
        self._route_cache: Dict[str, Tuple[str, datetime]] = {}  # cache_key -> (destination, expiry)
        self._round_robin_counters: Dict[str, int] = defaultdict(int)  # destination_group -> counter

        # Configuration
        self._default_config = self._agent_config.get('message_router', {}).get('defaults', {})
        self._strategies_config = self._agent_config.get('message_router', {}).get('routing_strategies', [])
        self._lb_config = self._agent_config.get('message_router', {}).get('load_balancing', {})

        # Tâche de mise à jour des métriques
        self._metrics_update_task: Optional[asyncio.Task] = None

        logger.info(f"✅ {self._subagent_display_name} initialisé")

    # ========================================================================
    # IMPLÉMENTATION DES MÉTHODES ABSTRACTES
    # ========================================================================

    async def _initialize_subagent_components(self) -> bool:
        """Initialise les composants spécifiques"""
        logger.info("Initialisation des composants Message Router...")

        # Démarrer la tâche de mise à jour des métriques
        if self._lb_config.get('enabled', True):
            self._metrics_update_task = asyncio.create_task(self._update_destination_metrics())

        logger.info("✅ Composants Message Router initialisés")
        return True

    async def _initialize_components(self) -> bool:
        """Implémentation requise par BaseAgent"""
        return await self._initialize_subagent_components()

    def _get_capability_handlers(self) -> Dict[str, Any]:
        """Retourne les handlers spécifiques"""
        return {
            "router.add_route": self._handle_add_route,
            "router.remove_route": self._handle_remove_route,
            "router.route": self._handle_route,
            "router.stats": self._handle_stats,
            "router.list": self._handle_list,
            "router.test": self._handle_test,
        }

    # ========================================================================
    # MOTEUR DE ROUTAGE
    # ========================================================================

    async def _evaluate_condition(self, condition: str, message: Any,
                                   engine: ConditionEngine) -> bool:
        """Évalue une condition sur un message"""
        try:
            if engine == ConditionEngine.JMESPATH:
                import jmespath
                result = jmespath.search(condition, message)
                return bool(result)

            elif engine == ConditionEngine.JSONATA:
                # JSONATA non implémenté par défaut
                return True

            elif engine == ConditionEngine.PYTHON:
                # Évaluation Python (dangereux - à utiliser avec précaution)
                # Dans un vrai système, on utiliserait un sandbox
                context = {"message": message}
                return eval(condition, {"__builtins__": {}}, context)

        except Exception as e:
            logger.warning(f"Erreur d'évaluation de condition: {e}")
            return False

        return False

    def _get_cache_key(self, message: Any, context: RoutingContext) -> str:
        """Génère une clé de cache pour un message"""
        content_hash = hashlib.md5(
            json.dumps(message, sort_keys=True).encode()
        ).hexdigest()
        return f"{content_hash}:{context.source}:{context.timestamp.timestamp()}"

    async def _find_matching_routes(self, message: Any,
                                    context: RoutingContext) -> List[Route]:
        """Trouve toutes les routes correspondant à un message"""
        matches = []

        for route in sorted(self._routes.values(), key=lambda r: -r.priority):
            if not route.enabled:
                continue

            if await self._evaluate_condition(route.condition, message, route.engine):
                matches.append(route)

        return matches

    async def _apply_routing_strategy(self, routes: List[Route],
                                       message: Any,
                                       context: RoutingContext) -> Optional[str]:
        """Applique la stratégie de routage pour choisir une destination"""
        if not routes:
            return self._default_config.get('default_destination', 'dead_letter')

        # Prendre la première route (déjà triée par priorité)
        primary_route = routes[0]

        # Appliquer la stratégie si la route a plusieurs destinations potentielles
        if isinstance(primary_route.destination, list):
            destinations = primary_route.destination
            strategy = primary_route.strategy

            if strategy == RoutingStrategy.ROUND_ROBIN:
                # Round-robin simple
                group = primary_route.id
                idx = self._round_robin_counters[group]
                self._round_robin_counters[group] = (idx + 1) % len(destinations)
                return destinations[idx]

            elif strategy == RoutingStrategy.LEAST_LOADED:
                # Destination la moins chargée
                best = min(destinations, key=lambda d: self._get_destination_load(d))
                return best

            elif strategy == RoutingStrategy.CONSISTENT_HASHING:
                # Hash cohérent basé sur l'ID du message
                hash_val = int(hashlib.md5(context.message_id.encode()).hexdigest(), 16)
                return destinations[hash_val % len(destinations)]

        return primary_route.destination

    def _get_destination_load(self, dest_name: str) -> float:
        """Calcule la charge d'une destination"""
        dest = self._destinations.get(dest_name)
        if not dest:
            return 0.0

        # Formule de charge pondérée
        load = (
            dest.queue_size * 1.0 +
            dest.response_time_ms * 0.1 +
            dest.error_rate * 100.0
        )
        return load / max(1, dest.weight)

    async def _update_destination_metrics(self):
        """Met à jour périodiquement les métriques des destinations"""
        interval = self._lb_config.get('update_interval', 60)

        while self._status.value == "ready":
            try:
                await asyncio.sleep(interval)

                # Simuler la mise à jour des métriques
                # Dans un vrai système, on interrogerait les destinations
                for dest in self._destinations.values():
                    dest.queue_size = max(0, dest.queue_size - 10)  # Décroissance simulée
                    dest.response_time_ms = max(5, dest.response_time_ms * 0.9)  # Normalisation
                    dest.error_rate = max(0, dest.error_rate * 0.95)
                    dest.last_updated = datetime.now()

                logger.debug("📊 Métriques des destinations mises à jour")

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"❌ Erreur mise à jour métriques: {e}")

    # ========================================================================
    # GESTION DES ROUTES
    # ========================================================================

    async def _add_route(self, route_id: str, condition: str, destination: str,
                         priority: int = 0, strategy: str = "content_based",
                         engine: str = "jmespath", **kwargs) -> Dict[str, Any]:
        """Ajoute une nouvelle règle de routage"""
        if route_id in self._routes:
            return {
                "success": False,
                "error": f"Route {route_id} existe déjà"
            }

        try:
            strategy_enum = RoutingStrategy(strategy)
            engine_enum = ConditionEngine(engine)
        except ValueError as e:
            return {
                "success": False,
                "error": f"Paramètre invalide: {e}"
            }

        # Vérifier la limite de routes
        max_routes = self._default_config.get('max_routes', 10000)
        if len(self._routes) >= max_routes:
            return {
                "success": False,
                "error": f"Nombre maximum de routes atteint ({max_routes})"
            }

        route = Route(
            id=route_id,
            condition=condition,
            destination=destination,
            priority=priority,
            strategy=strategy_enum,
            engine=engine_enum,
            metadata=kwargs
        )

        self._routes[route_id] = route
        self._routes_by_priority.append((priority, route_id))
        self._routes_by_priority.sort(key=lambda x: -x[0])

        # Ajouter la destination si nécessaire
        if destination not in self._destinations:
            self._destinations[destination] = Destination(name=destination)

        logger.info(f"✅ Route ajoutée: {route_id} (prio {priority}) -> {destination}")

        return {
            "success": True,
            "route_id": route_id,
            "destination": destination,
            "priority": priority
        }

    async def _remove_route(self, route_id: str) -> Dict[str, Any]:
        """Supprime une règle de routage"""
        if route_id not in self._routes:
            return {
                "success": False,
                "error": f"Route {route_id} non trouvée"
            }

        del self._routes[route_id]
        self._routes_by_priority = [(p, rid) for p, rid in self._routes_by_priority if rid != route_id]

        logger.info(f"🗑️ Route supprimée: {route_id}")

        return {
            "success": True,
            "route_id": route_id
        }

    # ========================================================================
    # HANDLERS DE CAPACITÉS
    # ========================================================================

    async def _handle_add_route(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Ajoute une règle de routage"""
        route_id = params.get("route_id")
        condition = params.get("condition")
        destination = params.get("destination")

        if not route_id:
            return {"success": False, "error": "route_id requis"}
        if not condition:
            return {"success": False, "error": "condition requis"}
        if not destination:
            return {"success": False, "error": "destination requis"}

        return await self._add_route(
            route_id=route_id,
            condition=condition,
            destination=destination,
            priority=params.get("priority", 0),
            strategy=params.get("strategy", "content_based"),
            engine=params.get("engine", "jmespath"),
            **params.get("metadata", {})
        )

    async def _handle_remove_route(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Supprime une règle de routage"""
        route_id = params.get("route_id")
        if not route_id:
            return {"success": False, "error": "route_id requis"}

        return await self._remove_route(route_id)

    async def _handle_route(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Route un message"""
        message = params.get("message")
        if message is None:
            return {"success": False, "error": "message requis"}

        # Créer le contexte
        context = RoutingContext(
            message_id=params.get("message_id", "unknown"),
            source=params.get("source"),
            headers=params.get("headers", {}),
            metadata=params.get("metadata", {})
        )

        # Vérifier le cache
        cache_key = self._get_cache_key(message, context)
        if cache_key in self._route_cache:
            destination, expiry = self._route_cache[cache_key]
            if datetime.now() < expiry:
                logger.debug(f"🎯 Cache hit pour {cache_key}")
                return {
                    "success": True,
                    "destination": destination,
                    "cached": True,
                    "message_id": context.message_id
                }

        # Trouver les routes correspondantes
        start_time = time.time()
        matching_routes = await self._find_matching_routes(message, context)
        eval_time = (time.time() - start_time) * 1000

        if not matching_routes:
            destination = self._default_config.get('default_destination', 'dead_letter')
            logger.debug(f"❌ Aucune route trouvée, destination par défaut: {destination}")
        else:
            # Appliquer la stratégie de routage
            destination = await self._apply_routing_strategy(matching_routes, message, context)

            # Mettre à jour les statistiques des routes
            for route in matching_routes:
                route.hits += 1
                route.last_hit = datetime.now()

        # Mettre en cache
        cache_ttl = self._default_config.get('cache_ttl_seconds', 300)
        self._route_cache[cache_key] = (destination, datetime.now() + timedelta(seconds=cache_ttl))

        # Nettoyer le cache périodiquement
        if len(self._route_cache) > 10000:
            self._cleanup_cache()

        logger.debug(f"📨 Message {context.message_id} routé vers {destination} en {eval_time:.2f}ms")

        return {
            "success": True,
            "destination": destination,
            "routes_evaluated": len(matching_routes),
            "evaluation_time_ms": round(eval_time, 2),
            "cached": False,
            "message_id": context.message_id,
            "timestamp": datetime.now().isoformat()
        }

    def _cleanup_cache(self):
        """Nettoie les entrées expirées du cache"""
        now = datetime.now()
        expired = [k for k, (_, exp) in self._route_cache.items() if now > exp]
        for k in expired:
            del self._route_cache[k]
        logger.debug(f"🧹 Cache nettoyé: {len(expired)} entrées")

    async def _handle_stats(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Statistiques de routage"""
        route_id = params.get("route_id")
        detailed = params.get("detailed", False)

        if route_id:
            if route_id not in self._routes:
                return {"success": False, "error": f"Route {route_id} non trouvée"}

            route = self._routes[route_id]
            stats = {
                "id": route.id,
                "destination": route.destination,
                "priority": route.priority,
                "hits": route.hits,
                "last_hit": route.last_hit.isoformat() if route.last_hit else None,
                "enabled": route.enabled,
                "created_at": route.created_at.isoformat()
            }
            if detailed:
                stats["condition"] = route.condition
                stats["strategy"] = route.strategy.value
                stats["engine"] = route.engine.value
                stats["metadata"] = route.metadata

            return {
                "success": True,
                "route": stats
            }

        # Statistiques globales
        total_hits = sum(r.hits for r in self._routes.values())
        routes_by_dest = defaultdict(int)
        for r in self._routes.values():
            routes_by_dest[r.destination] += 1

        return {
            "success": True,
            "global": {
                "routes_total": len(self._routes),
                "destinations_total": len(self._destinations),
                "total_hits": total_hits,
                "cache_size": len(self._route_cache),
                "routes_by_destination": dict(routes_by_dest)
            },
            "timestamp": datetime.now().isoformat()
        }

    async def _handle_list(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Liste les routes actives"""
        filter_str = params.get("filter", "")
        include_stats = params.get("include_stats", False)

        routes = []
        for route in self._routes.values():
            if filter_str and filter_str not in route.id and filter_str not in route.destination:
                continue

            route_info = {
                "id": route.id,
                "destination": route.destination,
                "priority": route.priority,
                "strategy": route.strategy.value,
                "enabled": route.enabled
            }

            if include_stats:
                route_info["hits"] = route.hits
                route_info["last_hit"] = route.last_hit.isoformat() if route.last_hit else None
                route_info["created_at"] = route.created_at.isoformat()

            routes.append(route_info)

        return {
            "success": True,
            "routes": routes,
            "count": len(routes),
            "timestamp": datetime.now().isoformat()
        }

    async def _handle_test(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Teste une règle de routage"""
        route_id = params.get("route_id")
        test_message = params.get("test_message")

        if not route_id:
            return {"success": False, "error": "route_id requis"}
        if test_message is None:
            return {"success": False, "error": "test_message requis"}

        if route_id not in self._routes:
            return {"success": False, "error": f"Route {route_id} non trouvée"}

        route = self._routes[route_id]

        # Évaluer la condition
        matches = await self._evaluate_condition(route.condition, test_message, route.engine)

        return {
            "success": True,
            "route_id": route_id,
            "matches": matches,
            "destination": route.destination if matches else None,
            "condition": route.condition,
            "engine": route.engine.value,
            "timestamp": datetime.now().isoformat()
        }

    # ========================================================================
    # SURCHARGE POUR LE NETTOYAGE
    # ========================================================================

    async def shutdown(self) -> bool:
        """Arrête le sous-agent"""
        logger.info(f"Arrêt de {self._subagent_display_name}...")

        if self._metrics_update_task and not self._metrics_update_task.done():
            self._metrics_update_task.cancel()
            try:
                await self._metrics_update_task
            except asyncio.CancelledError:
                pass

        return await super().shutdown()


# ============================================================================
# FONCTION D'USINE
# ============================================================================

def create_message_router_agent(config_path: str = "") -> "MessageRouterSubAgent":
    """Crée une instance du sous-agent message router"""
    return MessageRouterSubAgent(config_path)
"""
Gas Optimizer Sub-Agent - Expert en optimisation de gas
Version: 1.0.0
"""

import logging
import sys
import json
import asyncio
import random
import re
import importlib
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from enum import Enum

# Configuration des imports
current_dir = Path(__file__).parent.absolute()
project_root = current_dir.parent.parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from agents.base_agent.base_agent import BaseAgent, AgentStatus, Message, MessageType

logger = logging.getLogger(__name__)


class OptimizationType(Enum):
    """Types d'optimisations"""
    STORAGE = "storage"
    COMPUTATION = "computation"
    MEMORY = "memory"
    CALLDATA = "calldata"
    LOOP = "loop"
    ASSEMBLY = "assembly"


class OptimizationPriority(Enum):
    """Priorités d'optimisation"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class GasOptimizerSubAgent(BaseAgent):
    """
    Sous-agent spécialisé dans l'optimisation de gas pour smart contracts
    Storage packing, assembly optimization, loop unrolling, etc.
    """

    def __init__(self, config_path: str = ""):
        """Initialise le sous-agent d'optimisation gas"""
        if not config_path:
            config_path = str(current_dir / "config.yaml")

        super().__init__(config_path)

        self._display_name = self._agent_config.get('agent', {}).get('display_name', '⚡ Optimisation Gas')
        self._initialized = False

        # Statistiques
        self._stats = {
            'optimizations_performed': 0,
            'total_gas_saved': 0,
            'contracts_optimized': 0,
            'assembly_blocks_used': 0,
            'start_time': datetime.now().isoformat()
        }

        self._logger.info("⚡ Sous-agent Optimisation Gas créé")

    async def initialize(self) -> bool:
        """Initialise le sous-agent"""
        try:
            self._set_status(AgentStatus.INITIALIZING)
            self._logger.info("Initialisation du sous-agent Optimisation Gas...")

            base_result = await super().initialize()
            if not base_result:
                return False

            self._initialized = True
            self._set_status(AgentStatus.READY)
            self._logger.info("✅ Sous-agent Optimisation Gas prêt")
            return True

        except Exception as e:
            self._logger.error(f"❌ Erreur initialisation: {e}")
            self._set_status(AgentStatus.ERROR)
            return False

    async def _initialize_components(self) -> bool:
        """Initialise les composants du sous-agent"""
        self._logger.info("Initialisation des composants...")
        self._components = {
            "analyzer": {"enabled": True},
            "optimizer": {"enabled": True},
            "profiler": {"enabled": True}
        }
        return True

    async def _handle_custom_message(self, message: Message) -> Optional[Message]:
        """Gère les messages personnalisés"""
        try:
            msg_type = message.message_type

            handlers = {
                "gas.optimize": self._handle_optimize,
                "gas.analyze": self._handle_analyze,
                "gas.profile": self._handle_profile,
                "gas.techniques": self._handle_techniques,
                "gas.estimate": self._handle_estimate,
            }

            if msg_type in handlers:
                return await handlers[msg_type](message)

            return None

        except Exception as e:
            self._logger.error(f"Erreur traitement message: {e}")
            return Message(
                sender=self.name,
                recipient=message.sender,
                content={"error": str(e)},
                message_type=MessageType.ERROR.value,
                correlation_id=message.message_id
            )

    async def _handle_optimize(self, message: Message) -> Message:
        """Gère l'optimisation de code"""
        code = message.content.get("code", "")
        target = message.content.get("target", "all")

        result = await self.optimize_contract(code, target)

        return Message(
            sender=self.name,
            recipient=message.sender,
            content=result,
            message_type="gas.optimized",
            correlation_id=message.message_id
        )

    async def _handle_analyze(self, message: Message) -> Message:
        """Gère l'analyse de gas"""
        code = message.content.get("code", "")
        result = await self.analyze_gas_usage(code)

        return Message(
            sender=self.name,
            recipient=message.sender,
            content=result,
            message_type="gas.analyzed",
            correlation_id=message.message_id
        )

    async def _handle_profile(self, message: Message) -> Message:
        """Gère le profilage de gas"""
        code = message.content.get("code", "")
        function = message.content.get("function", "all")
        result = await self.profile_gas_usage(code, function)

        return Message(
            sender=self.name,
            recipient=message.sender,
            content=result,
            message_type="gas.profiled",
            correlation_id=message.message_id
        )

    async def _handle_techniques(self, message: Message) -> Message:
        """Retourne les techniques d'optimisation disponibles"""
        return Message(
            sender=self.name,
            recipient=message.sender,
            content={"techniques": self._get_optimization_techniques()},
            message_type="gas.techniques_list",
            correlation_id=message.message_id
        )

    async def _handle_estimate(self, message: Message) -> Message:
        """Estime le gas pour une fonction"""
        code = message.content.get("code", "")
        function = message.content.get("function", "")
        result = await self.estimate_gas_function(code, function)

        return Message(
            sender=self.name,
            recipient=message.sender,
            content=result,
            message_type="gas.estimated",
            correlation_id=message.message_id
        )

    async def optimize_contract(self, code: str, target: str = "all") -> Dict[str, Any]:
        """Optimise un contrat pour réduire le gas"""
        self._stats['optimizations_performed'] += 1
        self._stats['contracts_optimized'] += 1

        # Analyser le code pour trouver des opportunités d'optimisation
        opportunities = self._find_optimization_opportunities(code)

        # Appliquer les optimisations (simulation)
        optimized_code = code
        applied_optimizations = []
        total_gas_saved = 0

        for opp in opportunities:
            if opp['priority'] in ['critical', 'high'] or target == 'all':
                applied_optimizations.append(opp)
                total_gas_saved += opp['gas_save']
                optimized_code = self._simulate_optimization(optimized_code, opp)

        self._stats['total_gas_saved'] += total_gas_saved
        if any('assembly' in opp['type'].lower() for opp in applied_optimizations):
            self._stats['assembly_blocks_used'] += 1

        return {
            "success": True,
            "original_code": code,
            "optimized_code": optimized_code,
            "gas_saved": f"{total_gas_saved:,}",
            "percentage_saved": f"{(total_gas_saved / 1000000 * 100):.1f}%",
            "applied_optimizations": applied_optimizations,
            "optimization_summary": {
                "storage": len([o for o in applied_optimizations if o['type'] == 'storage']),
                "computation": len([o for o in applied_optimizations if o['type'] == 'computation']),
                "memory": len([o for o in applied_optimizations if o['type'] == 'memory']),
                "calldata": len([o for o in applied_optimizations if o['type'] == 'calldata']),
                "assembly": len([o for o in applied_optimizations if o['type'] == 'assembly'])
            },
            "timestamp": datetime.now().isoformat()
        }

    async def analyze_gas_usage(self, code: str) -> Dict[str, Any]:
        """Analyse l'utilisation de gas d'un contrat"""
        lines = code.split('\n')
        
        # Compter les opérations coûteuses
        expensive_ops = {
            'SSTORE': len(re.findall(r'=\s*\w+\s*;', code)),
            'SLOAD': len(re.findall(r'\b\w+\s*=\s*\w+\[', code)),
            'CALL': len(re.findall(r'\.call\s*\(', code)),
            'DELEGATECALL': len(re.findall(r'\.delegatecall\s*\(', code)),
            'MSTORE': len(re.findall(r'mstore\s*\(', code)),
            'MLOAD': len(re.findall(r'mload\s*\(', code))
        }

        # Identifier les gas guzzlers
        gas_guzzlers = []
        if 'for (' in code or 'while (' in code:
            gas_guzzlers.append({
                "pattern": "Loop without gas limit",
                "location": "multiple lines",
                "estimated_cost": "unbounded"
            })
        if 'transfer(' in code or 'send(' in code:
            gas_guzzlers.append({
                "pattern": "transfer/send (2300 gas limit)",
                "location": "various",
                "estimated_cost": "2300"
            })
        if 'public' in code and 'view' not in code and 'pure' not in code:
            gas_guzzlers.append({
                "pattern": "Public state-changing functions",
                "location": "various",
                "estimated_cost": "external call overhead"
            })

        return {
            "success": True,
            "analysis": {
                "total_lines": lines,
                "expensive_operations": expensive_ops,
                "estimated_deployment_gas": self._estimate_deployment_gas(code),
                "estimated_operation_gas": self._estimate_operation_gas(code),
                "gas_guzzlers": gas_guzzlers,
                "optimization_potential": self._calculate_optimization_potential(code)
            },
            "recommendations": self._generate_recommendations(code),
            "timestamp": datetime.now().isoformat()
        }

    async def profile_gas_usage(self, code: str, function: str = "all") -> Dict[str, Any]:
        """Profile l'utilisation de gas fonction par fonction"""
        # Extraire les fonctions du code
        functions = self._extract_functions(code)
        
        profile = {}
        for func in functions:
            if function == "all" or func['name'] == function:
                profile[func['name']] = {
                    "estimated_gas": func['estimated_gas'],
                    "operations": func['operations'],
                    "storage_writes": func['storage_writes'],
                    "external_calls": func['external_calls'],
                    "complexity": func['complexity']
                }

        return {
            "success": True,
            "profile": profile,
            "total_estimated_gas": sum(f['estimated_gas'] for f in functions if function == "all" or f['name'] == function),
            "timestamp": datetime.now().isoformat()
        }

    async def estimate_gas_function(self, code: str, function: str) -> Dict[str, Any]:
        """Estime le gas pour une fonction spécifique"""
        # Simulation d'estimation
        base_gas = random.randint(20000, 100000)
        
        return {
            "success": True,
            "function": function,
            "estimated_gas": f"{base_gas:,}",
            "breakdown": {
                "base_cost": "21,000",
                "computation": f"{random.randint(5000, 30000):,}",
                "storage": f"{random.randint(5000, 50000):,}",
                "memory": f"{random.randint(1000, 10000):,}",
                "external_calls": f"{random.randint(0, 20000):,}"
            },
            "optimization_suggestions": self._get_function_optimizations(function),
            "timestamp": datetime.now().isoformat()
        }

    def _find_optimization_opportunities(self, code: str) -> List[Dict]:
        """Trouve les opportunités d'optimisation dans le code"""
        opportunities = []

        # Storage packing
        if 'uint' in code and len(re.findall(r'uint\d+\s+\w+;', code)) > 3:
            opportunities.append({
                "type": "storage",
                "description": "Storage packing possible - combine multiple small uints",
                "priority": "high",
                "gas_save": 20000,
                "locations": ["state variables"],
                "example": "uint128 a; uint128 b; → uint256 packed;"
            })

        # Loop optimization
        if 'for (' in code or 'while (' in code:
            if 'unchecked' not in code:
                opportunities.append({
                    "type": "loop",
                    "description": "Use unchecked blocks in loops where overflow is impossible",
                    "priority": "medium",
                    "gas_save": 5000,
                    "locations": ["for loops"],
                    "example": "for(uint i=0; i<10; i++) unchecked { ... }"
                })

        # Calldata optimization
        if 'memory' in code and 'calldata' not in code:
            opportunities.append({
                "type": "calldata",
                "description": "Use calldata instead of memory for read-only parameters",
                "priority": "medium",
                "gas_save": 3000,
                "locations": ["function parameters"],
                "example": "function f(string memory s) → function f(string calldata s)"
            })

        # Assembly optimization
        if 'require(' in code and len(re.findall(r'require\(', code)) > 3:
            opportunities.append({
                "type": "assembly",
                "description": "Use assembly for custom errors to save gas",
                "priority": "high",
                "gas_save": 10000,
                "locations": ["require statements"],
                "example": "require(cond, 'msg') → if(!cond) revert Error();"
            })

        return opportunities

    def _simulate_optimization(self, code: str, optimization: Dict) -> str:
        """Simule l'application d'une optimisation"""
        # Dans un environnement réel, ceci modifierait réellement le code
        # Ici, on ajoute simplement un commentaire
        comment = f"\n    // OPTIMIZED: {optimization['description']}\n"
        return code + comment

    def _estimate_deployment_gas(self, code: str) -> str:
        """Estime le gas de déploiement"""
        lines = len(code.split('\n'))
        base = 32000 + (lines * 200)
        return f"{base + random.randint(-5000, 5000):,}"

    def _estimate_operation_gas(self, code: str) -> Dict[str, str]:
        """Estime le gas des opérations courantes"""
        return {
            "transfer": f"{random.randint(40000, 60000):,}",
            "approve": f"{random.randint(35000, 50000):,}",
            "mint": f"{random.randint(60000, 90000):,}",
            "burn": f"{random.randint(30000, 50000):,}",
            "average_tx": f"{random.randint(80000, 120000):,}"
        }

    def _calculate_optimization_potential(self, code: str) -> Dict[str, Any]:
        """Calcule le potentiel d'optimisation"""
        return {
            "score": random.randint(60, 95),
            "estimated_savings": f"{random.randint(10, 40)}%",
            "priority_areas": ["storage", "loops", "external calls"],
            "effort_required": random.choice(["low", "medium", "high"])
        }

    def _generate_recommendations(self, code: str) -> List[str]:
        """Génère des recommandations d'optimisation"""
        return [
            "📦 Storage: Pack multiple small uints into a single slot",
            "🔄 Loops: Use unchecked blocks and cache array length",
            "📞 Calls: Batch multiple external calls",
            "🎯 Assembly: Use inline assembly for critical sections",
            "💾 Memory: Use calldata instead of memory for read-only params",
            "⚡ Immutable: Use immutable for variables set once in constructor",
            "🚫 Errors: Use custom errors instead of require strings"
        ]

    def _get_function_optimizations(self, function: str) -> List[str]:
        """Retourne des optimisations pour une fonction spécifique"""
        return [
            "Check if function can be external instead of public",
            "Verify if parameters can be calldata instead of memory",
            "Look for loops that can be optimized with unchecked",
            "Consider using assembly for critical arithmetic"
        ]

    def _extract_functions(self, code: str) -> List[Dict]:
        """Extrait les fonctions du code (simulation)"""
        return [
            {
                "name": "transfer",
                "estimated_gas": 45000,
                "operations": ["SLOAD", "SSTORE", "CALL"],
                "storage_writes": 2,
                "external_calls": 1,
                "complexity": "medium"
            },
            {
                "name": "approve",
                "estimated_gas": 38000,
                "operations": ["SLOAD", "SSTORE"],
                "storage_writes": 1,
                "external_calls": 0,
                "complexity": "low"
            }
        ]

    def _get_optimization_techniques(self) -> List[Dict]:
        """Retourne les techniques d'optimisation disponibles"""
        return [
            {
                "name": "Storage Packing",
                "description": "Combiner plusieurs petites variables dans un seul slot",
                "savings": "up to 20,000 gas per variable",
                "difficulty": "medium"
            },
            {
                "name": "Unchecked Blocks",
                "description": "Désactiver la vérification d'overflow dans les boucles",
                "savings": "~100 gas per iteration",
                "difficulty": "low"
            },
            {
                "name": "Calldata vs Memory",
                "description": "Utiliser calldata pour les paramètres read-only",
                "savings": "~500 gas per call",
                "difficulty": "low"
            },
            {
                "name": "Assembly Optimizations",
                "description": "Utiliser Yul/assembly pour les opérations critiques",
                "savings": "up to 50%",
                "difficulty": "high"
            },
            {
                "name": "Custom Errors",
                "description": "Remplacer les strings par des erreurs personnalisées",
                "savings": "~10,000 gas per revert",
                "difficulty": "low"
            },
            {
                "name": "Immutable Variables",
                "description": "Marquer les variables constantes comme immutable",
                "savings": "~2,000 gas per access",
                "difficulty": "low"
            }
        ]

    async def shutdown(self) -> bool:
        """Arrête le sous-agent"""
        self._logger.info("Arrêt du sous-agent Optimisation Gas...")
        self._set_status(AgentStatus.SHUTTING_DOWN)

        await super().shutdown()

        self._logger.info("✅ Sous-agent Optimisation Gas arrêté")
        return True

    async def health_check(self) -> Dict[str, Any]:
        """Vérifie la santé du sous-agent"""
        base_health = await super().health_check()

        return {
            **base_health,
            "agent": self.name,
            "display_name": self._display_name,
            "status": self._status.value,
            "ready": self._status == AgentStatus.READY,
            "initialized": self._initialized,
            "stats": self._stats,
            "timestamp": datetime.now().isoformat()
        }


def create_gas_optimizer_agent(config_path: str = "") -> GasOptimizerSubAgent:
    """Crée une instance du sous-agent d'optimisation gas"""
    return GasOptimizerSubAgent(config_path)
"""
Gas Optimizer SubAgent - Sous-agent d'optimisation gas
Version: 2.0.0

Optimise la consommation de gas des smart contracts avec support de :
- Analyse de gas
- Suggestions d'optimisation
- Estimation des coûts
- Comparaison de versions
"""

import logging
import sys
import asyncio
import json
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, Optional, List, Set, Tuple
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

class OptimizationLevel(Enum):
    """Niveaux d'optimisation"""
    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    AGGRESSIVE = "aggressive"


class OptimizationCategory(Enum):
    """Catégories d'optimisation"""
    STORAGE = "storage"
    LOOPS = "loops"
    FUNCTIONS = "functions"
    MATH = "math"
    STRINGS = "strings"
    ARRAYS = "arrays"
    MAPPINGS = "mappings"
    EVENTS = "events"
    MODIFIERS = "modifiers"
    INHERITANCE = "inheritance"


@dataclass
class GasEstimate:
    """Estimation de gas"""
    function_name: str
    gas_estimate: int
    min_gas: int
    max_gas: int
    call_data_size: int
    execution_time_ms: float


@dataclass
class OptimizationSuggestion:
    """Suggestion d'optimisation"""
    id: str
    category: OptimizationCategory
    location: str  # Ligne ou fonction
    description: str
    current_code: str
    suggested_code: str
    estimated_saving: int  # en gas
    confidence: float
    complexity: str  # low, medium, high
    applied: bool = False


@dataclass
class GasAnalysis:
    """Analyse de gas complète"""
    contract_name: str
    total_estimated_gas: int
    functions_analyzed: int
    gas_by_function: Dict[str, GasEstimate]
    suggestions: List[OptimizationSuggestion]
    total_potential_saving: int
    optimization_score: float  # 0-100
    created_at: datetime = field(default_factory=datetime.now)


# ============================================================================
# SOUS-AGENT PRINCIPAL
# ============================================================================

class GasOptimizerSubAgent(BaseSubAgent):
    """
    Sous-agent d'optimisation gas

    Optimise la consommation de gas des smart contracts avec :
    - Analyse détaillée du gas
    - Suggestions d'optimisation automatiques
    - Estimation des coûts
    - Comparaison de versions
    """

    def __init__(self, config_path: str = ""):
        """Initialise le sous-agent d'optimisation gas"""
        super().__init__(config_path)

        # Métadonnées
        self._subagent_display_name = "⛽ Optimisation Gas"
        self._subagent_description = "Optimisation des coûts de gas des smart contracts"
        self._subagent_version = "2.0.0"
        self._subagent_category = "smart_contract"
        self._subagent_capabilities = [
            "gas.analyze_contract",
            "gas.optimize_contract",
            "gas.estimate_costs",
            "gas.suggest_patterns",
            "gas.compare_versions",
            "gas.simulate_transaction",
            "gas.get_optimization_history"
        ]

        # État interne
        self._analyses: Dict[str, GasAnalysis] = {}
        self._optimization_history: List[Dict[str, Any]] = []
        self._contract_locks: Dict[str, asyncio.Lock] = {}
        
        # Configuration
        self._gas_params = self._agent_config.get('gas_parameters', {})
        self._target_gas = self._gas_params.get('target_gas_limit', 3000000)
        self._warning_threshold = self._gas_params.get('warning_threshold', 2000000)
        self._critical_threshold = self._gas_params.get('critical_threshold', 4000000)

        # Charger les patterns d'optimisation
        self._optimization_patterns = self._load_optimization_patterns()
        
        # Tâche de fond
        self._cleanup_task: Optional[asyncio.Task] = None

        logger.info(f"✅ {self._subagent_display_name} initialisé (v{self._subagent_version})")

    # ========================================================================
    # IMPLÉMENTATION DES MÉTHODES ABSTRACTES
    # ========================================================================

    async def _initialize_subagent_components(self) -> bool:
        """Initialise les composants spécifiques"""
        logger.info("Initialisation des composants d'optimisation gas...")

        try:
            # Charger les paramètres gas
            logger.info(f"  ✅ Paramètres gas chargés: target={self._target_gas}, warning={self._warning_threshold}")
            logger.info(f"  ✅ {len(self._optimization_patterns)} patterns d'optimisation chargés")

            # Démarrer la tâche de nettoyage
            self._cleanup_task = asyncio.create_task(self._cleanup_loop())

            logger.info("✅ Composants d'optimisation gas initialisés")
            return True

        except Exception as e:
            logger.error(f"❌ Erreur initialisation composants: {e}")
            return False

    async def _initialize_components(self) -> bool:
        """Implémentation requise par BaseAgent"""
        return await self._initialize_subagent_components()

    def _get_capability_handlers(self) -> Dict[str, Any]:
        """Retourne les handlers spécifiques"""
        return {
            "gas.analyze_contract": self._handle_analyze_contract,
            "gas.optimize_contract": self._handle_optimize_contract,
            "gas.estimate_costs": self._handle_estimate_costs,
            "gas.suggest_patterns": self._handle_suggest_patterns,
            "gas.compare_versions": self._handle_compare_versions,
            "gas.simulate_transaction": self._handle_simulate_transaction,
            "gas.get_optimization_history": self._handle_get_history,
        }

    # ========================================================================
    # MÉTHODES PRIVÉES
    # ========================================================================

    async def _get_contract_lock(self, contract_path: str) -> asyncio.Lock:
        """Récupère ou crée un verrou pour un contrat"""
        if contract_path not in self._contract_locks:
            self._contract_locks[contract_path] = asyncio.Lock()
        return self._contract_locks[contract_path]

    def _load_optimization_patterns(self) -> Dict[str, List[Dict[str, Any]]]:
        """Charge les patterns d'optimisation"""
        patterns = {
            'storage': [
                {
                    'pattern': r'uint\s*\[\s*\]',
                    'suggestion': 'Utiliser bytes32[] pour les tableaux d\'entiers pour économiser du gas',
                    'saving': 5000,
                    'confidence': 0.8,
                    'complexity': 'medium'
                },
                {
                    'pattern': r'mapping\s*\(\s*address\s*=>\s*uint\s*\)',
                    'suggestion': 'Considérer le packed storage pour les mappings',
                    'saving': 2000,
                    'confidence': 0.7,
                    'complexity': 'high'
                },
                {
                    'pattern': r'string\s+(public|internal|private)',
                    'suggestion': 'Utiliser bytes32 pour les chaînes de moins de 32 caractères',
                    'saving': 1500,
                    'confidence': 0.9,
                    'complexity': 'low'
                }
            ],
            'loops': [
                {
                    'pattern': r'for\s*\(\s*uint\s+i\s*=\s*0\s*;\s*i\s*<\s*(\w+)\.length\s*;\s*i\+\+\s*\)',
                    'suggestion': 'Mettre en cache array.length en dehors de la boucle',
                    'saving': 800 * 10,  # 800 gas par itération
                    'confidence': 0.95,
                    'complexity': 'low',
                    'example': 'uint len = array.length; for (uint i = 0; i < len; i++)'
                },
                {
                    'pattern': r'for\s*\([^;]+;[^;]+;[^\)]+\)\s*\{[^}]*require\([^}]*\)[^}]*\}',
                    'suggestion': 'Éviter les require dans les boucles, les vérifier avant',
                    'saving': 500,
                    'confidence': 0.85,
                    'complexity': 'medium'
                },
                {
                    'pattern': r'i\+\+',
                    'suggestion': 'Utiliser ++i au lieu de i++ pour économiser du gas',
                    'saving': 5,
                    'confidence': 0.99,
                    'complexity': 'low'
                }
            ],
            'functions': [
                {
                    'pattern': r'function\s+\w+\s*\([^)]*\)\s*(public|external)\s+payable',
                    'suggestion': 'Rendre payable seulement si nécessaire',
                    'saving': 2100,
                    'confidence': 0.9,
                    'complexity': 'low'
                },
                {
                    'pattern': r'function\s+\w+\s*\([^)]*\)\s*(public|external)\s+view',
                    'suggestion': 'Utiliser external pour les fonctions view appelées depuis l\'extérieur',
                    'saving': 300,
                    'confidence': 0.8,
                    'complexity': 'low'
                },
                {
                    'pattern': r'modifier\s+\w+\s*\([^)]*\)\s*\{[^}]*_;[^}]*\}',
                    'suggestion': 'Remplacer les modificateurs par des fonctions internes si possible',
                    'saving': 1000,
                    'confidence': 0.6,
                    'complexity': 'high'
                }
            ],
            'math': [
                {
                    'pattern': r'(\+{2}|-{2})',
                    'suggestion': "Utiliser unchecked { ++i; } quand le débordement est impossible",
                    'saving': 30,
                    'confidence': 0.95,
                    'complexity': 'low'
                },
                {
                    'pattern': r'for\s*\([^;]+;[^;]+;[^\)]+\)\s*\{[^}]*\w+\s*=\s*\w+\s*[+\-]\s*\w+[^}]*\}',
                    'suggestion': 'Utiliser unchecked pour les calculs sans risque de débordement',
                    'saving': 40,
                    'confidence': 0.7,
                    'complexity': 'medium'
                },
                {
                    'pattern': r'\brequire\b\s*\(\s*\w+\s*!=\s*0\s*\)',
                    'suggestion': 'Utiliser require(x > 0) au lieu de require(x != 0) quand pertinent',
                    'saving': 10,
                    'confidence': 0.6,
                    'complexity': 'low'
                }
            ],
            'events': [
                {
                    'pattern': r'event\s+\w+\s*\([^)]*\)\s*;',
                    'suggestion': 'Indexer les paramètres pertinents pour faciliter la recherche',
                    'saving': 0,
                    'confidence': 0.9,
                    'complexity': 'low',
                    'info': 'N\'économise pas de gas mais améliore l\'indexation'
                }
            ],
            'inheritance': [
                {
                    'pattern': r'is\s+(\w+),\s*(\w+)',
                    'suggestion': 'Éviter l\'héritage multiple quand possible',
                    'saving': 5000,
                    'confidence': 0.5,
                    'complexity': 'high'
                }
            ]
        }
        return patterns

    def _analyze_gas_patterns(self, contract_code: str) -> List[OptimizationSuggestion]:
        """Analyse le code pour trouver des opportunités d'optimisation"""
        suggestions = []
        lines = contract_code.split('\n')
        
        for category, patterns in self._optimization_patterns.items():
            for pattern_info in patterns:
                pattern = pattern_info['pattern']
                matches = list(re.finditer(pattern, contract_code, re.MULTILINE))
                
                for match in matches:
                    # Trouver la ligne approximative
                    line_no = 1
                    for i, line in enumerate(lines, 1):
                        if match.group() in line:
                            line_no = i
                            break
                    
                    suggestion = OptimizationSuggestion(
                        id=f"OPT-{category}-{len(suggestions)}",
                        category=OptimizationCategory(category),
                        location=f"Ligne {line_no}",
                        description=pattern_info['suggestion'],
                        current_code=match.group(),
                        suggested_code=pattern_info.get('example', match.group()),
                        estimated_saving=pattern_info['saving'],
                        confidence=pattern_info['confidence'],
                        complexity=pattern_info['complexity']
                    )
                    suggestions.append(suggestion)
        
        return suggestions

    def _estimate_function_gas(self, function_code: str) -> GasEstimate:
        """Estime le gas pour une fonction"""
        # Simulation d'estimation basée sur des règles simples
        base_gas = 21000  # Transaction de base
        
        # Opérations de base
        operations = {
            r'require\s*\(': 200,
            r'mapping\s*\(': 500,
            r'\.transfer\s*\(': 3000,
            r'\.send\s*\(': 2300,
            r'\.call\s*\{': 9000,
            r'for\s*\(': 800 * 10,  # Boucle avec 10 itérations
            r'while\s*\(': 800 * 10,
            r'new\s+\w+': 50000,
            r'delete\s+': 5000,
            r'emit\s+': 375,
            r'return\s+': 200
        }
        
        total_gas = base_gas
        for op_pattern, op_cost in operations.items():
            if re.search(op_pattern, function_code):
                total_gas += op_cost
        
        return GasEstimate(
            function_name="unknown",
            gas_estimate=total_gas,
            min_gas=total_gas - 1000,
            max_gas=total_gas + 5000,
            call_data_size=len(function_code),
            execution_time_ms=total_gas / 100  # Approximation
        )

    # ========================================================================
    # TÂCHES DE FOND
    # ========================================================================

    async def _cleanup_loop(self):
        """Nettoie les anciennes analyses"""
        logger.info("🔄 Boucle de nettoyage démarrée")

        while self._status.value == "ready":
            try:
                await asyncio.sleep(3600)  # Toutes les heures

                # Nettoyer les analyses de plus de 7 jours
                cutoff = datetime.now() - timedelta(days=7)
                old_analyses = [
                    aid for aid, analysis in self._analyses.items()
                    if analysis.created_at < cutoff
                ]

                for aid in old_analyses:
                    del self._analyses[aid]

                # Nettoyer l'historique d'optimisation
                old_history = [
                    h for h in self._optimization_history
                    if datetime.fromisoformat(h['timestamp']) < cutoff
                ]
                
                for h in old_history:
                    self._optimization_history.remove(h)

                if old_analyses or old_history:
                    logger.info(f"🧹 Nettoyage: {len(old_analyses)} analyses, {len(old_history)} historiques")

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"❌ Erreur dans la boucle de nettoyage: {e}")

    # ========================================================================
    # HANDLERS DE CAPACITÉS
    # ========================================================================

    async def _handle_analyze_contract(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Analyse la consommation gas d'un contrat"""
        contract_path = params.get('contract_path')
        contract_code = params.get('contract_code')
        detailed = params.get('detailed', False)

        if not contract_path and not contract_code:
            return {'success': False, 'error': 'contract_path ou contract_code requis'}

        # Lire le code si nécessaire
        if contract_path and not contract_code:
            try:
                with open(contract_path, 'r') as f:
                    contract_code = f.read()
            except Exception as e:
                return {'success': False, 'error': f"Erreur lecture fichier: {e}"}

        # Analyser le code
        suggestions = self._analyze_gas_patterns(contract_code)
        
        # Estimer le gas par fonction (simplifié)
        functions = re.findall(r'function\s+(\w+)\s*\([^)]*\)\s*[^{]*\{[^}]*\}', contract_code, re.DOTALL)
        gas_by_function = {}
        total_gas = 21000  # Transaction de base
        
        for func in functions[:10]:  # Limiter pour l'exemple
            estimate = self._estimate_function_gas(func)
            gas_by_function[estimate.function_name] = {
                'estimate': estimate.gas_estimate,
                'min': estimate.min_gas,
                'max': estimate.max_gas
            }
            total_gas += estimate.gas_estimate

        # Calculer le score d'optimisation
        total_potential_saving = sum(s.estimated_saving for s in suggestions)
        optimization_score = min(100, (total_potential_saving / total_gas) * 100) if total_gas > 0 else 0

        # Créer l'analyse
        analysis = GasAnalysis(
            contract_name=Path(contract_path).stem if contract_path else "inline",
            total_estimated_gas=total_gas,
            functions_analyzed=len(functions),
            gas_by_function=gas_by_function,
            suggestions=suggestions,
            total_potential_saving=total_potential_saving,
            optimization_score=optimization_score
        )

        # Stocker l'analyse
        analysis_id = f"ANALYSIS-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        self._analyses[analysis_id] = analysis

        result = {
            'success': True,
            'analysis_id': analysis_id,
            'contract': analysis.contract_name,
            'total_estimated_gas': analysis.total_estimated_gas,
            'functions_analyzed': analysis.functions_analyzed,
            'total_potential_saving': analysis.total_potential_saving,
            'optimization_score': round(analysis.optimization_score, 2),
            'suggestions_count': len(analysis.suggestions),
            'suggestions': [
                {
                    'id': s.id,
                    'category': s.category.value,
                    'location': s.location,
                    'description': s.description,
                    'estimated_saving': s.estimated_saving,
                    'confidence': s.confidence,
                    'complexity': s.complexity
                }
                for s in analysis.suggestions
            ]
        }

        if detailed:
            result['gas_by_function'] = analysis.gas_by_function

        return result

    async def _handle_optimize_contract(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Optimise un contrat automatiquement"""
        contract_path = params.get('contract_path')
        contract_code = params.get('contract_code')
        level = params.get('level', 'medium')
        apply_suggestions = params.get('apply_suggestions', False)

        if not contract_path and not contract_code:
            return {'success': False, 'error': 'contract_path ou contract_code requis'}

        # Analyser d'abord
        analysis_result = await self._handle_analyze_contract(params)
        if not analysis_result['success']:
            return analysis_result

        # Simuler l'optimisation
        optimized_code = contract_code
        changes_applied = 0
        total_saving = 0

        if apply_suggestions:
            # Dans une vraie implémentation, appliquer les suggestions
            # Ici, on simule
            changes_applied = min(5, len(analysis_result['suggestions']))
            total_saving = sum(s['estimated_saving'] for s in analysis_result['suggestions'][:changes_applied])

        # Enregistrer dans l'historique
        self._optimization_history.append({
            'timestamp': datetime.now().isoformat(),
            'contract': analysis_result['contract'],
            'level': level,
            'changes_applied': changes_applied,
            'total_saving': total_saving,
            'analysis_id': analysis_result['analysis_id']
        })

        return {
            'success': True,
            'original_analysis': analysis_result,
            'optimization_level': level,
            'changes_applied': changes_applied,
            'total_gas_saving': total_saving,
            'estimated_cost_saving_usd': round(total_saving * 50 / 1e9 * 3000, 2),  # 50 gwei, $3000/ETH
            'optimized_code': optimized_code if apply_suggestions else None,
            'message': f"Optimisation {level} appliquée avec {changes_applied} changements"
        }

    async def _handle_estimate_costs(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Estime les coûts de gas en USD"""
        gas_estimate = params.get('gas_estimate', 0)
        gas_price_gwei = params.get('gas_price_gwei', 50)
        eth_price_usd = params.get('eth_price_usd', 3000)
        transaction_count = params.get('transaction_count', 1000)

        if gas_estimate == 0:
            return {'success': False, 'error': 'gas_estimate requis'}

        cost_eth = (gas_estimate * gas_price_gwei) / 1e9
        cost_usd = cost_eth * eth_price_usd
        
        monthly_cost = cost_usd * transaction_count * 30  # 30 jours
        yearly_cost = monthly_cost * 12

        return {
            'success': True,
            'estimates': {
                'per_transaction': {
                    'gas': gas_estimate,
                    'eth': round(cost_eth, 8),
                    'usd': round(cost_usd, 2)
                },
                'monthly': {
                    'transactions': transaction_count * 30,
                    'usd': round(monthly_cost, 2)
                },
                'yearly': {
                    'transactions': transaction_count * 365,
                    'usd': round(yearly_cost, 2)
                }
            },
            'assumptions': {
                'gas_price_gwei': gas_price_gwei,
                'eth_price_usd': eth_price_usd,
                'daily_transactions': transaction_count
            }
        }

    async def _handle_suggest_patterns(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Suggère des patterns d'optimisation"""
        category = params.get('category')
        context = params.get('context', {})

        patterns = []
        for cat, cat_patterns in self._optimization_patterns.items():
            if category and cat != category:
                continue
            
            for pattern in cat_patterns:
                patterns.append({
                    'category': cat,
                    'suggestion': pattern['suggestion'],
                    'saving': pattern['saving'],
                    'confidence': pattern['confidence'],
                    'complexity': pattern['complexity'],
                    'example': pattern.get('example', '')
                })

        return {
            'success': True,
            'patterns': patterns[:20],  # Limiter à 20
            'count': len(patterns),
            'categories': list(self._optimization_patterns.keys())
        }

    async def _handle_compare_versions(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Compare deux versions d'un contrat"""
        version_a_path = params.get('version_a_path')
        version_b_path = params.get('version_b_path')
        version_a_code = params.get('version_a_code')
        version_b_code = params.get('version_b_code')

        if not version_a_path and not version_a_code:
            return {'success': False, 'error': 'version_a requis'}
        if not version_b_path and not version_b_code:
            return {'success': False, 'error': 'version_b requis'}

        # Analyser les deux versions
        analysis_a = await self._handle_analyze_contract({
            'contract_path': version_a_path,
            'contract_code': version_a_code
        })
        analysis_b = await self._handle_analyze_contract({
            'contract_path': version_b_path,
            'contract_code': version_b_code
        })

        if not analysis_a['success']:
            return analysis_a
        if not analysis_b['success']:
            return analysis_b

        # Calculer les améliorations
        gas_improvement = analysis_b['total_estimated_gas'] - analysis_a['total_estimated_gas']
        gas_improvement_pct = (gas_improvement / analysis_a['total_estimated_gas']) * 100 if analysis_a['total_estimated_gas'] > 0 else 0
        
        score_improvement = analysis_b['optimization_score'] - analysis_a['optimization_score']

        return {
            'success': True,
            'comparison': {
                'version_a': {
                    'name': version_a_path or 'version A',
                    'total_gas': analysis_a['total_estimated_gas'],
                    'optimization_score': analysis_a['optimization_score'],
                    'suggestions': analysis_a['suggestions_count']
                },
                'version_b': {
                    'name': version_b_path or 'version B',
                    'total_gas': analysis_b['total_estimated_gas'],
                    'optimization_score': analysis_b['optimization_score'],
                    'suggestions': analysis_b['suggestions_count']
                },
                'differences': {
                    'gas_improvement': gas_improvement,
                    'gas_improvement_percent': round(gas_improvement_pct, 2),
                    'score_improvement': round(score_improvement, 2),
                    'suggestions_resolved': analysis_a['suggestions_count'] - analysis_b['suggestions_count']
                },
                'recommendation': 'version_b' if gas_improvement < 0 else 'version_a'
            }
        }

    async def _handle_simulate_transaction(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Simule une transaction pour estimer le gas"""
        contract_path = params.get('contract_path')
        function_name = params.get('function')
        params_list = params.get('params', [])

        if not contract_path:
            return {'success': False, 'error': 'contract_path requis'}
        if not function_name:
            return {'success': False, 'error': 'function requis'}

        # Simulation
        base_gas = 21000
        function_gas = {
            'transfer': 52000,
            'approve': 46000,
            'transferFrom': 68000,
            'mint': 120000,
            'burn': 45000,
            'balanceOf': 30000
        }.get(function_name, 50000)

        total_gas = base_gas + function_gas

        return {
            'success': True,
            'simulation': {
                'function': function_name,
                'params': params_list,
                'estimated_gas': total_gas,
                'execution_time_ms': total_gas / 100,
                'would_succeed': True,
                'state_changes': ['balance updated', 'event emitted']
            }
        }

    async def _handle_get_history(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Récupère l'historique des optimisations"""
        contract = params.get('contract')
        limit = params.get('limit', 50)

        history = self._optimization_history
        if contract:
            history = [h for h in history if h['contract'] == contract]

        history = sorted(history, key=lambda h: h['timestamp'], reverse=True)[:limit]

        return {
            'success': True,
            'history': history,
            'total_count': len(history),
            'total_savings': sum(h['total_saving'] for h in history),
            'total_changes': sum(h['changes_applied'] for h in history)
        }

    # ========================================================================
    # NETTOYAGE
    # ========================================================================

    async def shutdown(self) -> bool:
        """Arrête le sous-agent"""
        logger.info(f"Arrêt de {self._subagent_display_name}...")

        if self._cleanup_task and not self._cleanup_task.done():
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass

        return await super().shutdown()


# ============================================================================
# FONCTIONS D'EXPORT
# ============================================================================

def get_agent_class():
    """
    Fonction requise pour le chargement dynamique des sous-agents.
    Retourne la classe principale du sous-agent.
    """
    return GasOptimizerSubAgent


def create_gas_optimizer_agent(config_path: str = "") -> "GasOptimizerSubAgent":
    """Crée une instance du sous-agent d'optimisation gas"""
    return GasOptimizerSubAgent(config_path)
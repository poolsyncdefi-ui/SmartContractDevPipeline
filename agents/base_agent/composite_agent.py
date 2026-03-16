#!/usr/bin/env python3
"""
Composite Agent - Classe de base pour tous les agents composites
Version: 1.0.0

Permet à un agent de contenir et d'orchestrer d'autres agents (spécialistes)
tout en présentant une interface unifiée vers l'extérieur.
"""

import asyncio
import logging
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional, Union, Callable, Awaitable
from pathlib import Path
import traceback

from agents.base_agent.base_agent import BaseAgent, AgentStatus
from agents.sous_agents.base_subagent import BaseSubAgent

logger = logging.getLogger(__name__)


class OrchestrationStrategy:
    """Constantes pour les stratégies d'orchestration"""
    PARALLEL = "parallel"
    SEQUENTIAL = "sequential"
    PIPELINE = "pipeline"
    ADAPTIVE = "adaptive"
    CONSENSUS = "consensus"
    WEIGHTED = "weighted"


class CompositeAgent(BaseAgent):
    """
    Agent capable de contenir et d'orchestrer d'autres agents.
    
    Un agent composite :
    - Contient des agents spécialistes
    - Orchestre leur exécution selon différentes stratégies
    - Agrège leurs résultats
    - Présente une interface unifiée
    
    Attributes:
        composite_id (str): Identifiant unique du composite
        specialists (Dict[str, BaseAgent]): Dictionnaire des agents spécialistes
        capability_mapping (Dict[str, str]): Mapping capacité -> ID du spécialiste
        orchestration_strategy (str): Stratégie d'orchestration par défaut
        _instance_registry (Dict[str, BaseAgent]): Registre global des instances
        _specialist_health (Dict[str, Dict]): État de santé des spécialistes
        _orchestration_history (List[Dict]): Historique des orchestrations
    """

    def __init__(self, config_path: str = "", composite_id: Optional[str] = None):
        """
        Initialise l'agent composite.

        Args:
            config_path: Chemin vers le fichier de configuration
            composite_id: Identifiant unique du composite (généré si None)
        """
        super().__init__(config_path)

        # Identifiants
        self.composite_id = composite_id or f"composite_{uuid.uuid4().hex[:8]}"
        
        # Attributs composites
        self._is_composite = True
        self.specialists: Dict[str, BaseAgent] = {}
        self.capability_mapping: Dict[str, str] = {}
        self.orchestration_strategy = OrchestrationStrategy.PARALLEL
        
        # Registre et métriques
        self._instance_registry: Dict[str, BaseAgent] = {}
        self._specialist_health: Dict[str, Dict] = {}
        self._orchestration_history: List[Dict] = []
        
        # Configuration composite
        self._composite_config = self._agent_config.get('composite_mode', {})
        self._strategies_config = self._composite_config.get('strategies', {})
        self._specialists_config = self._agent_config.get('composite_specialists', {})
        
        # Verrous pour la synchronisation
        self._specialist_locks: Dict[str, asyncio.Lock] = {}
        self._registry_lock = asyncio.Lock()
        
        logger.info(f"🏗️ Agent composite créé: {self.composite_id} (v{self._version})")

    # ========================================================================
    # INITIALISATION
    # ========================================================================

    async def _initialize_components(self) -> bool:
        """
        Initialise les composants spécifiques du composite.
        Appelé par BaseAgent.initialize().
        """
        try:
            logger.info(f"Initialisation des composants composites pour {self.composite_id}...")

            # Charger la stratégie d'orchestration
            self.orchestration_strategy = self._composite_config.get(
                'default_strategy', OrchestrationStrategy.PARALLEL
            )
            
            # Initialiser les spécialistes
            await self._initialize_specialists()
            
            # Initialiser les verrous
            for specialist_id in self.specialists:
                self._specialist_locks[specialist_id] = asyncio.Lock()
            
            logger.info(f"✅ Composants composites initialisés: {len(self.specialists)} spécialistes")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erreur initialisation composants composites: {e}")
            logger.error(traceback.format_exc())
            return False

    async def _initialize_specialists(self) -> bool:
        """
        Initialise les agents spécialistes selon la configuration.
        
        Returns:
            True si au moins un spécialiste a été initialisé
        """
        logger.info(f"Initialisation des spécialistes pour {self.composite_id}...")

        if not self._specialists_config:
            logger.warning("⚠️ Aucune configuration de spécialistes trouvée")
            return False

        for specialist_id, config in self._specialists_config.items():
            try:
                # Récupérer la classe du spécialiste
                class_path = config.get('class')
                if not class_path:
                    logger.warning(f"  ⚠️ {specialist_id}: 'class' non spécifié")
                    continue

                # Import dynamique de la classe
                module_path, class_name = class_path.rsplit('.', 1)
                module = __import__(module_path, fromlist=[class_name])
                specialist_class = getattr(module, class_name)

                # Chemin de configuration
                config_path = config.get('config', '')
                
                # Créer l'instance
                specialist = specialist_class(config_path)
                
                # Enregistrer auprès du composite
                if hasattr(specialist, 'register_with_composite'):
                    role = config.get('role', specialist_id)
                    await specialist.register_with_composite(self.composite_id, role)
                
                # Définir le parent composite
                if hasattr(specialist, 'set_parent_composite'):
                    specialist.set_parent_composite(self)
                
                # Stocker le spécialiste
                self.specialists[specialist_id] = specialist
                
                # Mapper les capacités
                capabilities = config.get('capabilities', [])
                weight = config.get('weight', 1.0)
                
                for cap in capabilities:
                    self.capability_mapping[cap] = specialist_id
                
                # Enregistrer dans le registre global
                await self._register_instance(specialist, specialist_id)
                
                # Initialiser l'état de santé
                self._specialist_health[specialist_id] = {
                    'status': 'initialized',
                    'weight': weight,
                    'last_used': None,
                    'success_count': 0,
                    'error_count': 0
                }
                
                logger.info(f"  ✓ Spécialiste {specialist_id} initialisé ({class_name})")
                
            except Exception as e:
                logger.error(f"  ❌ Erreur initialisation spécialiste {specialist_id}: {e}")
                logger.debug(traceback.format_exc())

        logger.info(f"✅ {len(self.specialists)} spécialistes initialisés")
        return len(self.specialists) > 0

    async def _register_instance(self, agent: BaseAgent, agent_id: str):
        """
        Enregistre une instance d'agent dans le registre global.
        
        Args:
            agent: Instance de l'agent
            agent_id: Identifiant unique
        """
        async with self._registry_lock:
            instance_key = f"{self.composite_id}:{agent_id}"
            self._instance_registry[instance_key] = agent

    # ========================================================================
    # GESTION DES SPÉCIALISTES
    # ========================================================================

    def get_specialist(self, capability: str, context: Optional[Dict] = None) -> Optional[BaseAgent]:
        """
        Récupère le spécialiste approprié pour une capacité.
        
        Args:
            capability: Capacité recherchée
            context: Contexte pour le routage contextuel
            
        Returns:
            Agent spécialiste ou None
        """
        # Routage direct par mapping
        specialist_id = self.capability_mapping.get(capability)
        
        # Routage contextuel si demandé
        if context and self.orchestration_strategy == OrchestrationStrategy.ADAPTIVE:
            specialist_id = self._route_by_context(capability, context)
        
        if specialist_id and specialist_id in self.specialists:
            specialist = self.specialists[specialist_id]
            self._update_health(specialist_id, 'accessed')
            return specialist
        
        # Recherche par capacité déclarée
        for sid, specialist in self.specialists.items():
            if hasattr(specialist, 'can_handle') and specialist.can_handle(capability, context):
                self.capability_mapping[capability] = sid
                self._update_health(sid, 'accessed')
                return specialist
        
        logger.warning(f"⚠️ Aucun spécialiste trouvé pour la capacité: {capability}")
        return None

    def _route_by_context(self, capability: str, context: Dict) -> Optional[str]:
        """
        Routage contextuel - sélectionne le meilleur spécialiste selon le contexte.
        
        Args:
            capability: Capacité recherchée
            context: Contexte (charge, disponibilité, performance)
            
        Returns:
            ID du spécialiste sélectionné
        """
        candidates = []
        
        for sid, health in self._specialist_health.items():
            # Vérifier si le spécialiste peut gérer cette capacité
            if sid in self.capability_mapping.values() or capability in dir(self.specialists[sid]):
                # Calculer un score basé sur le contexte
                score = health.get('weight', 1.0)
                
                # Pénaliser si récemment utilisé
                if health.get('last_used'):
                    time_since_used = (datetime.now() - health['last_used']).total_seconds()
                    if time_since_used < 60:  # Moins d'une minute
                        score *= 0.8
                
                # Pénaliser si beaucoup d'erreurs
                error_rate = health.get('error_count', 0) / max(1, health.get('success_count', 1) + health.get('error_count', 0))
                score *= (1 - error_rate)
                
                candidates.append((score, sid))
        
        if candidates:
            # Retourner le meilleur candidat
            candidates.sort(reverse=True)
            return candidates[0][1]
        
        return None

    def _update_health(self, specialist_id: str, action: str, success: bool = True):
        """
        Met à jour l'état de santé d'un spécialiste.
        
        Args:
            specialist_id: ID du spécialiste
            action: Action effectuée
            success: Succès de l'action
        """
        if specialist_id in self._specialist_health:
            health = self._specialist_health[specialist_id]
            health['last_used'] = datetime.now()
            
            if action == 'execute':
                if success:
                    health['success_count'] += 1
                else:
                    health['error_count'] += 1

    async def add_specialist(self, agent: BaseAgent, capabilities: List[str], 
                             role: str = "default", weight: float = 1.0) -> bool:
        """
        Ajoute dynamiquement un spécialiste.
        
        Args:
            agent: Instance de l'agent à ajouter
            capabilities: Liste des capacités de l'agent
            role: Rôle du spécialiste
            weight: Poids pour le routage contextuel
            
        Returns:
            True si l'ajout a réussi
        """
        specialist_id = f"{role}_{len(self.specialists)}"
        
        try:
            # Enregistrer auprès du composite
            if hasattr(agent, 'register_with_composite'):
                await agent.register_with_composite(self.composite_id, role)
            
            # Définir le parent composite
            if hasattr(agent, 'set_parent_composite'):
                agent.set_parent_composite(self)
            
            # Stocker le spécialiste
            self.specialists[specialist_id] = agent
            
            # Mapper les capacités
            for cap in capabilities:
                self.capability_mapping[cap] = specialist_id
            
            # Initialiser l'état de santé
            self._specialist_health[specialist_id] = {
                'status': 'added',
                'weight': weight,
                'last_used': None,
                'success_count': 0,
                'error_count': 0
            }
            
            # Initialiser un verrou
            self._specialist_locks[specialist_id] = asyncio.Lock()
            
            logger.info(f"✅ Spécialiste {specialist_id} ajouté dynamiquement")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erreur ajout spécialiste: {e}")
            return False

    async def remove_specialist(self, specialist_id: str) -> bool:
        """
        Retire dynamiquement un spécialiste.
        
        Args:
            specialist_id: ID du spécialiste à retirer
            
        Returns:
            True si le retrait a réussi
        """
        if specialist_id not in self.specialists:
            logger.warning(f"⚠️ Spécialiste {specialist_id} non trouvé")
            return False
        
        try:
            # Arrêter le spécialiste
            specialist = self.specialists[specialist_id]
            await specialist.shutdown()
            
            # Retirer des structures de données
            del self.specialists[specialist_id]
            
            # Retirer du mapping des capacités
            caps_to_remove = [cap for cap, sid in self.capability_mapping.items() if sid == specialist_id]
            for cap in caps_to_remove:
                del self.capability_mapping[cap]
            
            # Retirer de l'état de santé
            if specialist_id in self._specialist_health:
                del self._specialist_health[specialist_id]
            
            # Retirer le verrou
            if specialist_id in self._specialist_locks:
                del self._specialist_locks[specialist_id]
            
            logger.info(f"✅ Spécialiste {specialist_id} retiré")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erreur retrait spécialiste: {e}")
            return False

    # ========================================================================
    # ORCHESTRATION
    # ========================================================================

    async def execute_composite(self, task: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Méthode principale d'exécution composite.
        
        Args:
            task: Tâche à exécuter
            context: Contexte d'exécution
            
        Returns:
            Résultat de l'exécution composite
        """
        start_time = datetime.now()
        self._logger.info(f"🎯 Exécution composite: {task}")
        
        try:
            # Déterminer la stratégie d'orchestration
            strategy = context.get('strategy', self.orchestration_strategy)
            
            # Analyser la tâche
            task_analysis = await self._analyze_task(task, context)
            
            # Récupérer les spécialistes nécessaires
            specialists_needed = task_analysis.get('specialists', [])
            specialist_instances = []
            for spec_id in specialists_needed:
                specialist = self.get_specialist(spec_id, context)
                if specialist:
                    specialist_instances.append((spec_id, specialist))
                else:
                    self._logger.warning(f"⚠️ Spécialiste {spec_id} non disponible")
            
            if not specialist_instances:
                return {
                    'success': False,
                    'error': f'Aucun spécialiste disponible pour la tâche: {task}',
                    'task': task,
                    'timestamp': datetime.now().isoformat()
                }
            
            # Orchestrer selon la stratégie
            if strategy == OrchestrationStrategy.PARALLEL:
                result = await self._orchestrate_parallel(task, context, specialist_instances)
            elif strategy == OrchestrationStrategy.SEQUENTIAL:
                result = await self._orchestrate_sequential(task, context, specialist_instances)
            elif strategy == OrchestrationStrategy.PIPELINE:
                result = await self._orchestrate_pipeline(task, context, specialist_instances)
            elif strategy == OrchestrationStrategy.CONSENSUS:
                result = await self._orchestrate_consensus(task, context, specialist_instances)
            elif strategy == OrchestrationStrategy.WEIGHTED:
                result = await self._orchestrate_weighted(task, context, specialist_instances)
            else:
                result = await self._orchestrate_parallel(task, context, specialist_instances)
            
            # Ajouter des métadonnées
            duration = (datetime.now() - start_time).total_seconds() * 1000
            result['metadata'] = {
                'composite_id': self.composite_id,
                'task': task,
                'strategy': strategy,
                'duration_ms': duration,
                'specialists_used': [s[0] for s in specialist_instances],
                'timestamp': datetime.now().isoformat()
            }
            
            # Enregistrer dans l'historique
            self._orchestration_history.append({
                'task': task,
                'strategy': strategy,
                'success': result.get('success', False),
                'duration_ms': duration,
                'specialists': [s[0] for s in specialist_instances],
                'timestamp': datetime.now().isoformat()
            })
            
            return result
            
        except Exception as e:
            self._logger.error(f"❌ Erreur exécution composite: {e}")
            self._logger.error(traceback.format_exc())
            return {
                'success': False,
                'error': str(e),
                'traceback': traceback.format_exc(),
                'task': task,
                'timestamp': datetime.now().isoformat()
            }

    async def _analyze_task(self, task: str, context: Dict) -> Dict[str, Any]:
        """
        Analyse une tâche pour déterminer les spécialistes nécessaires.
        
        Args:
            task: Tâche à analyser
            context: Contexte d'exécution
            
        Returns:
            Analyse de la tâche
        """
        # Par défaut, décomposer la tâche en sous-tâches
        subtasks = context.get('subtasks', [task])
        
        # Déterminer les spécialistes pour chaque sous-tâche
        specialists_needed = []
        for subtask in subtasks:
            # Chercher un spécialiste capable de gérer cette sous-tâche
            for sid, specialist in self.specialists.items():
                if hasattr(specialist, 'can_handle_subtask'):
                    confidence = await specialist.can_handle_subtask(subtask, context)
                    if confidence > 0.7:
                        specialists_needed.append(sid)
                        break
        
        return {
            'subtasks': subtasks,
            'specialists': specialists_needed or list(self.specialists.keys()),
            'complexity': context.get('complexity', 'medium'),
            'priority': context.get('priority', 'normal')
        }

    async def _orchestrate_parallel(self, task: str, context: Dict, 
                                    specialists: List[tuple]) -> Dict[str, Any]:
        """
        Exécute des tâches en parallèle.
        
        Args:
            task: Tâche principale
            context: Contexte
            specialists: Liste des (id, instance) de spécialistes
            
        Returns:
            Résultats agrégés
        """
        self._logger.info(f"⚡ Orchestration parallèle avec {len(specialists)} spécialistes")
        
        # Créer les tâches
        tasks = []
        for spec_id, specialist in specialists:
            subtask = context.get(f'subtask_{spec_id}', task)
            tasks.append(self._execute_with_lock(spec_id, specialist, subtask, context))
        
        # Exécuter en parallèle
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Traiter les résultats
        processed_results = []
        for i, (spec_id, _) in enumerate(specialists):
            result = results[i]
            if isinstance(result, Exception):
                self._logger.error(f"❌ Erreur spécialiste {spec_id}: {result}")
                self._update_health(spec_id, 'execute', success=False)
                processed_results.append({
                    'specialist': spec_id,
                    'success': False,
                    'error': str(result)
                })
            else:
                self._update_health(spec_id, 'execute', success=True)
                processed_results.append({
                    'specialist': spec_id,
                    'success': True,
                    'result': result
                })
        
        return {
            'success': all(r['success'] for r in processed_results),
            'results': processed_results,
            'strategy': 'parallel'
        }

    async def _orchestrate_sequential(self, task: str, context: Dict,
                                      specialists: List[tuple]) -> Dict[str, Any]:
        """
        Exécute des tâches en séquence.
        
        Args:
            task: Tâche principale
            context: Contexte
            specialists: Liste des (id, instance) de spécialistes
            
        Returns:
            Résultat final
        """
        self._logger.info(f"➡️ Orchestration séquentielle avec {len(specialists)} spécialistes")
        
        current_data = context.get('initial_data', {})
        stop_on_failure = context.get('stop_on_failure', True)
        
        for i, (spec_id, specialist) in enumerate(specialists):
            self._logger.info(f"  Étape {i+1}/{len(specialists)}: {spec_id}")
            
            try:
                # Exécuter avec verrou
                result = await self._execute_with_lock(
                    spec_id, specialist, 
                    context.get(f'step_{i}', task),
                    {**context, 'previous_data': current_data}
                )
                
                if result.get('success', False):
                    current_data = result.get('data', current_data)
                    self._update_health(spec_id, 'execute', success=True)
                else:
                    self._update_health(spec_id, 'execute', success=False)
                    if stop_on_failure:
                        return {
                            'success': False,
                            'error': f"Échec à l'étape {spec_id}",
                            'step': i,
                            'result': result,
                            'strategy': 'sequential'
                        }
            
            except Exception as e:
                self._logger.error(f"❌ Erreur à l'étape {spec_id}: {e}")
                self._update_health(spec_id, 'execute', success=False)
                if stop_on_failure:
                    return {
                        'success': False,
                        'error': str(e),
                        'step': i,
                        'traceback': traceback.format_exc(),
                        'strategy': 'sequential'
                    }
        
        return {
            'success': True,
            'data': current_data,
            'strategy': 'sequential'
        }

    async def _orchestrate_pipeline(self, task: str, context: Dict,
                                    specialists: List[tuple]) -> Dict[str, Any]:
        """
        Exécute un pipeline de traitement (chaque étape transforme les données).
        
        Args:
            task: Tâche principale
            context: Contexte
            specialists: Liste des (id, instance) de spécialistes
            
        Returns:
            Données transformées
        """
        self._logger.info(f"🔧 Orchestration pipeline avec {len(specialists)} étapes")
        
        data = context.get('initial_data', {})
        
        for spec_id, specialist in specialists:
            self._logger.info(f"  Pipeline étape: {spec_id}")
            
            try:
                result = await self._execute_with_lock(
                    spec_id, specialist,
                    context.get('pipeline_task', 'process'),
                    {**context, 'input_data': data}
                )
                
                if result.get('success', False):
                    data = result.get('output_data', result.get('data', data))
                    self._update_health(spec_id, 'execute', success=True)
                else:
                    self._update_health(spec_id, 'execute', success=False)
                    return {
                        'success': False,
                        'error': f"Pipeline failed at {spec_id}",
                        'data': data,
                        'strategy': 'pipeline'
                    }
            
            except Exception as e:
                self._logger.error(f"❌ Erreur pipeline {spec_id}: {e}")
                self._update_health(spec_id, 'execute', success=False)
                return {
                    'success': False,
                    'error': str(e),
                    'data': data,
                    'strategy': 'pipeline'
                }
        
        return {
            'success': True,
            'data': data,
            'strategy': 'pipeline'
        }

    async def _orchestrate_consensus(self, task: str, context: Dict,
                                     specialists: List[tuple]) -> Dict[str, Any]:
        """
        Exécute plusieurs spécialistes et cherche un consensus.
        
        Args:
            task: Tâche principale
            context: Contexte
            specialists: Liste des (id, instance) de spécialistes
            
        Returns:
            Résultat par consensus
        """
        self._logger.info(f"🤝 Orchestration par consensus avec {len(specialists)} spécialistes")
        
        # Exécuter tous en parallèle
        tasks = []
        for spec_id, specialist in specialists:
            tasks.append(self._execute_with_lock(spec_id, specialist, task, context))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Analyser les résultats
        valid_results = []
        for i, (spec_id, _) in enumerate(specialists):
            result = results[i]
            if not isinstance(result, Exception) and result.get('success', False):
                valid_results.append({
                    'specialist': spec_id,
                    'result': result
                })
                self._update_health(spec_id, 'execute', success=True)
            else:
                self._update_health(spec_id, 'execute', success=False)
        
        # Chercher un consensus (majorité)
        if valid_results:
            # Version simplifiée: prendre le premier résultat
            # Dans une vraie implémentation, comparer les résultats
            return {
                'success': True,
                'consensus': valid_results[0]['result'],
                'participants': len(valid_results),
                'total': len(specialists),
                'strategy': 'consensus'
            }
        
        return {
            'success': False,
            'error': 'Aucun consensus atteint',
            'strategy': 'consensus'
        }

    async def _orchestrate_weighted(self, task: str, context: Dict,
                                    specialists: List[tuple]) -> Dict[str, Any]:
        """
        Exécute des spécialistes avec pondération.
        
        Args:
            task: Tâche principale
            context: Contexte
            specialists: Liste des (id, instance) de spécialistes
            
        Returns:
            Résultat pondéré
        """
        self._logger.info(f"⚖️ Orchestration pondérée avec {len(specialists)} spécialistes")
        
        # Exécuter tous en parallèle
        tasks = []
        for spec_id, specialist in specialists:
            tasks.append(self._execute_with_lock(spec_id, specialist, task, context))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Pondérer les résultats
        weighted_results = []
        total_weight = 0
        
        for i, (spec_id, _) in enumerate(specialists):
            weight = self._specialist_health.get(spec_id, {}).get('weight', 1.0)
            result = results[i]
            
            if not isinstance(result, Exception) and result.get('success', False):
                weighted_results.append({
                    'specialist': spec_id,
                    'weight': weight,
                    'result': result
                })
                total_weight += weight
                self._update_health(spec_id, 'execute', success=True)
            else:
                self._update_health(spec_id, 'execute', success=False)
        
        if weighted_results:
            # Sélectionner le résultat avec le poids le plus élevé
            weighted_results.sort(key=lambda x: x['weight'], reverse=True)
            return {
                'success': True,
                'result': weighted_results[0]['result'],
                'selected_specialist': weighted_results[0]['specialist'],
                'weight': weighted_results[0]['weight'],
                'participants': len(weighted_results),
                'strategy': 'weighted'
            }
        
        return {
            'success': False,
            'error': 'Aucun résultat pondéré disponible',
            'strategy': 'weighted'
        }

    async def _execute_with_lock(self, spec_id: str, specialist: BaseAgent,
                                  task: str, context: Dict) -> Dict[str, Any]:
        """
        Exécute une tâche avec verrouillage pour éviter les conflits.
        
        Args:
            spec_id: ID du spécialiste
            specialist: Instance du spécialiste
            task: Tâche à exécuter
            context: Contexte
            
        Returns:
            Résultat de l'exécution
        """
        lock = self._specialist_locks.get(spec_id)
        if lock:
            async with lock:
                if hasattr(specialist, 'execute_composite'):
                    return await specialist.execute_composite(task, context)
                elif hasattr(specialist, 'execute'):
                    return await specialist.execute(task, context)
                else:
                    return {'success': False, 'error': 'Specialist has no execute method'}
        else:
            if hasattr(specialist, 'execute_composite'):
                return await specialist.execute_composite(task, context)
            elif hasattr(specialist, 'execute'):
                return await specialist.execute(task, context)
            else:
                return {'success': False, 'error': 'Specialist has no execute method'}

    # ========================================================================
    # MÉTHODES DE GESTION D'ÉTAT
    # ========================================================================

    async def shutdown(self) -> bool:
        """
        Arrête le composite et tous ses spécialistes.
        
        Returns:
            True si l'arrêt a réussi
        """
        self._logger.info(f"Arrêt du composite {self.composite_id}...")
        self._set_status(AgentStatus.SHUTTING_DOWN)

        # Arrêter les spécialistes
        for spec_id, specialist in self.specialists.items():
            try:
                await specialist.shutdown()
                self._logger.info(f"  ✓ Spécialiste {spec_id} arrêté")
            except Exception as e:
                self._logger.warning(f"  ⚠️ Erreur arrêt spécialiste {spec_id}: {e}")

        # Sauvegarder l'historique
        await self._save_orchestration_history()

        # Appeler la méthode parent
        await super().shutdown()

        self._logger.info(f"✅ Composite {self.composite_id} arrêté")
        return True

    async def pause(self) -> bool:
        """Met le composite en pause (y compris les spécialistes)."""
        self._logger.info(f"Pause du composite {self.composite_id}...")

        # Mettre en pause les spécialistes
        for spec_id, specialist in self.specialists.items():
            try:
                await specialist.pause()
            except Exception as e:
                self._logger.warning(f"⚠️ Erreur pause spécialiste {spec_id}: {e}")

        self._set_status(AgentStatus.PAUSED)
        return True

    async def resume(self) -> bool:
        """Reprend l'activité du composite."""
        self._logger.info(f"Reprise du composite {self.composite_id}...")

        # Reprendre les spécialistes
        for spec_id, specialist in self.specialists.items():
            try:
                await specialist.resume()
            except Exception as e:
                self._logger.warning(f"⚠️ Erreur reprise spécialiste {spec_id}: {e}")

        self._set_status(AgentStatus.READY)
        return True

    async def _save_orchestration_history(self):
        """Sauvegarde l'historique des orchestrations."""
        try:
            history_file = Path(f"./reports/orchestration/{self.composite_id}_history.json")
            history_file.parent.mkdir(parents=True, exist_ok=True)
            
            import json
            with open(history_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'composite_id': self.composite_id,
                    'history': self._orchestration_history[-1000:],  # Garder les 1000 derniers
                    'total_operations': len(self._orchestration_history),
                    'specialists': list(self.specialists.keys()),
                    'timestamp': datetime.now().isoformat()
                }, f, indent=2, ensure_ascii=False)
            
            self._logger.info(f"✅ Historique sauvegardé: {history_file}")
        except Exception as e:
            self._logger.warning(f"⚠️ Erreur sauvegarde historique: {e}")

    # ========================================================================
    # MÉTHODES D'INFORMATION
    # ========================================================================

    async def get_composite_info(self) -> Dict[str, Any]:
        """
        Retourne les informations sur le composite.
        
        Returns:
            Dictionnaire d'informations
        """
        base_info = await super().get_agent_info() if hasattr(super(), 'get_agent_info') else {}
        
        specialist_info = {}
        for spec_id, specialist in self.specialists.items():
            try:
                if hasattr(specialist, 'get_agent_info'):
                    specialist_info[spec_id] = await specialist.get_agent_info()
                else:
                    specialist_info[spec_id] = {'name': specialist.name if hasattr(specialist, 'name') else spec_id}
            except:
                specialist_info[spec_id] = {'status': 'error'}
        
        return {
            **base_info,
            'composite_id': self.composite_id,
            'composite_type': 'CompositeAgent',
            'specialists_count': len(self.specialists),
            'specialists': specialist_info,
            'orchestration_strategy': self.orchestration_strategy,
            'capabilities': list(self.capability_mapping.keys()),
            'orchestration_stats': {
                'total_operations': len(self._orchestration_history),
                'success_rate': self._calculate_success_rate(),
                'avg_duration_ms': self._calculate_avg_duration()
            },
            'health': self._specialist_health,
            'timestamp': datetime.now().isoformat()
        }

    def _calculate_success_rate(self) -> float:
        """Calcule le taux de succès des orchestrations."""
        if not self._orchestration_history:
            return 1.0
        successes = sum(1 for op in self._orchestration_history if op.get('success', False))
        return successes / len(self._orchestration_history)

    def _calculate_avg_duration(self) -> float:
        """Calcule la durée moyenne des orchestrations."""
        if not self._orchestration_history:
            return 0.0
        durations = [op.get('duration_ms', 0) for op in self._orchestration_history]
        return sum(durations) / len(durations)

    async def health_check(self) -> Dict[str, Any]:
        """Vérifie la santé du composite et de ses spécialistes."""
        base_health = await super().health_check()
        
        specialists_health = {}
        all_healthy = True
        
        for spec_id, specialist in self.specialists.items():
            try:
                if hasattr(specialist, 'health_check'):
                    health = await specialist.health_check()
                    specialists_health[spec_id] = health
                    if health.get('status') != 'healthy':
                        all_healthy = False
                else:
                    specialists_health[spec_id] = {'status': 'unknown'}
            except Exception as e:
                specialists_health[spec_id] = {'status': 'error', 'error': str(e)}
                all_healthy = False
        
        return {
            **base_health,
            'composite_id': self.composite_id,
            'status': 'healthy' if all_healthy else 'degraded',
            'specialists_count': len(self.specialists),
            'specialists_health': specialists_health,
            'orchestration_stats': {
                'total_operations': len(self._orchestration_history),
                'success_rate': self._calculate_success_rate()
            },
            'timestamp': datetime.now().isoformat()
        }


# ============================================================================
# FONCTIONS D'USINE
# ============================================================================

def create_composite_agent(config_path: str = "", composite_id: Optional[str] = None) -> CompositeAgent:
    """Crée une instance d'agent composite."""
    return CompositeAgent(config_path, composite_id)


def get_agent_class():
    """Retourne la classe principale pour le chargement dynamique."""
    return CompositeAgent
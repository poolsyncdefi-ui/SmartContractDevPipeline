# orchestrator/orchestrator.py
import asyncio
import os
import sys
import yaml
import json
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("SmartContractOrchestrator")

class AgentStatus(Enum):
    """Statut d'un agent."""
    UNINITIALIZED = "uninitialized"
    INITIALIZING = "initializing"
    READY = "ready"
    BUSY = "busy"
    ERROR = "error"
    DISABLED = "disabled"

@dataclass
class AgentInfo:
    """Informations sur un agent."""
    name: str
    display_name: str
    specialization: str
    config_path: str
    agent_type: str  # main_agent, sous_agent, abstract_base
    enabled: bool
    instantiate: bool
    dependencies: List[str]
    initialization_order: int
    parent: Optional[str]
    status: AgentStatus = AgentStatus.UNINITIALIZED
    instance: Any = None
    capabilities: List[str] = field(default_factory=list)
    last_health_check: Optional[datetime] = None
    mandatory: bool = True
    purpose: str = ""

class SmartContractOrchestrator:
    """Orchestrateur principal pour la pipeline de développement de smart contracts."""
    
    def __init__(self, config_path: str = "project_config.yaml"):
        """Initialiser l'orchestrateur.
        
        Args:
            config_path: Chemin vers le fichier de configuration
        """
        self.config_path = config_path
        self.config = None
        self.agents: Dict[str, AgentInfo] = {}
        self.agent_instances = {}
        self.task_results = []
        self.initialized = False
        self.logger = logging.getLogger(self.__class__.__name__)
        
    def load_configuration(self) -> bool:
        """Charger la configuration depuis le fichier YAML.
        
        Returns:
            True si la configuration a été chargée avec succès
        """
        try:
            if not os.path.exists(self.config_path):
                self.logger.error(f"Fichier de configuration non trouvé: {self.config_path}")
                return False
            
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self.config = yaml.safe_load(f)
            
            if not self.config:
                self.logger.error("Configuration vide")
                return False
            
            self.logger.info(f"Configuration chargée: {self.config.get('project_name', 'Unknown')} v{self.config.get('version', '1.0.0')}")
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur lors du chargement de la configuration: {e}")
            return False
    
    def _load_agent_config(self, agent_name: str, agent_info: dict) -> Dict[str, Any]:
        """Charger la configuration d'un agent.
        
        Args:
            agent_name: Nom de l'agent
            agent_info: Informations sur l'agent
            
        Returns:
            Configuration de l'agent
        """
        try:
            config_path = agent_info.get("config_path")
            if not config_path or not os.path.exists(config_path):
                self.logger.warning(f"Fichier de configuration non trouvé pour {agent_name}")
                return {}
            
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            # Extraire les capacités
            capabilities = config.get("agent", {}).get("capabilities", [])
            capability_names = [cap.get("name") for cap in capabilities if isinstance(cap, dict) and "name" in cap]
            
            self.logger.info(f"Agent {agent_name}: configuration chargée ({len(capability_names)} capacités)")
            
            return config
            
        except Exception as e:
            self.logger.error(f"Erreur lors du chargement de la configuration pour {agent_name}: {e}")
            return {}
    
    def _create_agent_instance(self, agent_name: str, agent_info: AgentInfo) -> Any:
        """Créer une instance d'un agent.
        
        Args:
            agent_name: Nom de l'agent
            agent_info: Informations sur l'agent
            
        Returns:
            Instance de l'agent ou None en cas d'erreur
        """
        try:
            config_path = agent_info.config_path
            
            # Vérifier si le fichier d'agent existe
            agent_file = config_path.replace("config.yaml", "agent.py")
            if not os.path.exists(agent_file):
                self.logger.warning(f"Fichier d'agent non trouvé pour {agent_name}, utilisation de la classe par défaut")
                # Pour le moment, retourner une instance de BaseAgent
                from agents.base_agent import BaseAgent
                return BaseAgent(config_path)
            
            # Charger dynamiquement le module de l'agent
            agent_dir = os.path.dirname(config_path)
            agent_module_name = os.path.basename(agent_dir)
            
            # Ajouter le répertoire parent au chemin Python
            parent_dir = os.path.dirname(agent_dir)
            if parent_dir not in sys.path:
                sys.path.insert(0, parent_dir)
            
            try:
                # Importer le module de l'agent
                agent_module = __import__(f"agents.{agent_module_name}.agent", fromlist=[f"{agent_module_name.capitalize()}Agent"])
                
                # Trouver la classe de l'agent (nommée selon la convention: NomAgent)
                agent_class_name = f"{agent_module_name.capitalize()}Agent"
                if hasattr(agent_module, agent_class_name):
                    agent_class = getattr(agent_module, agent_class_name)
                    
                    # Créer l'instance
                    instance = agent_class(config_path)
                    
                    # Charger les capacités depuis la config
                    agent_config = self._load_agent_config(agent_name, {"config_path": config_path})
                    capabilities = agent_config.get("agent", {}).get("capabilities", [])
                    capability_names = [cap.get("name") for cap in capabilities if isinstance(cap, dict) and "name" in cap]
                    
                    # Mettre à jour les capacités de l'agent
                    if capability_names:
                        instance.capabilities = capability_names
                    
                    self.logger.info(f"Instance créée pour l'agent {agent_name} ({agent_class.__name__}) avec {len(instance.capabilities)} capacités")
                    return instance
                else:
                    self.logger.warning(f"Classe {agent_class_name} non trouvée pour {agent_name}")
                    from agents.base_agent import BaseAgent
                    return BaseAgent(config_path)
                    
            except ImportError as e:
                self.logger.warning(f"Impossible d'importer l'agent {agent_name}: {e}")
                from agents.base_agent import BaseAgent
                return BaseAgent(config_path)
                
        except Exception as e:
            self.logger.error(f"Erreur lors de la création de l'instance pour {agent_name}: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    async def initialize_agents(self) -> bool:
        """Initialiser tous les agents.
        
        Returns:
            True si tous les agents ont été initialisés avec succès
        """
        if not self.config:
            self.logger.error("Configuration non chargée")
            return False
        
        self.logger.info("Initialisation des agents...")
        
        agents_config = self.config.get("agents", {})
        if not agents_config:
            self.logger.error("Aucun agent configuré")
            return False
        
        # Créer les objets AgentInfo pour tous les agents
        for agent_name, agent_config in agents_config.items():
            agent_info = AgentInfo(
                name=agent_name,
                display_name=agent_config.get("display_name", agent_name),
                specialization=agent_config.get("specialization", ""),
                config_path=agent_config.get("config_path", f"agents/{agent_name}/config.yaml"),
                agent_type=agent_config.get("agent_type", "main_agent"),
                enabled=agent_config.get("enabled", True),
                instantiate=agent_config.get("instantiate", True),
                dependencies=agent_config.get("dependencies", []),
                initialization_order=agent_config.get("initialization_order", 999),
                parent=agent_config.get("parent"),
                purpose=agent_config.get("purpose", "")
            )
            
            # Vérifier si l'agent doit être instancié
            if agent_name == "base_agent" and agent_config.get("agent_type") == "abstract_base":
                agent_info.instantiate = False
                self.logger.info(f"Agent {agent_name} non instanciable, ignoré")
            
            self.agents[agent_name] = agent_info
            
            # Charger la configuration de l'agent
            self._load_agent_config(agent_name, {"config_path": agent_info.config_path})
        
        # Trier les agents par ordre d'initialisation
        sorted_agents = sorted(
            [agent for agent in self.agents.values() if agent.instantiate],
            key=lambda x: x.initialization_order
        )
        
        # Initialiser les agents dans l'ordre
        initialized_count = 0
        for agent_info in sorted_agents:
            try:
                self.logger.info(f"Initialisation de l'agent: {agent_info.name} (ordre: {agent_info.initialization_order})")
                
                # Vérifier les dépendances
                deps_ready = all(
                    dep in self.agents and 
                    self.agents[dep].status == AgentStatus.READY 
                    for dep in agent_info.dependencies
                )
                
                if not deps_ready and agent_info.dependencies:
                    self.logger.warning(f"Dépendances non satisfaites pour {agent_info.name}: {agent_info.dependencies}")
                    continue
                
                # Créer l'instance de l'agent
                agent_info.status = AgentStatus.INITIALIZING
                instance = self._create_agent_instance(agent_info.name, agent_info)
                
                if instance:
                    agent_info.instance = instance
                    agent_info.status = AgentStatus.READY
                    
                    # Récupérer les capacités de l'instance
                    if hasattr(instance, 'capabilities'):
                        agent_info.capabilities = instance.capabilities
                    
                    self.logger.info(f"✓ Agent {agent_info.name} initialisé avec succès")
                    initialized_count += 1
                else:
                    agent_info.status = AgentStatus.ERROR
                    self.logger.error(f"Échec de l'initialisation de l'agent {agent_info.name}")
                    
            except Exception as e:
                agent_info.status = AgentStatus.ERROR
                self.logger.error(f"Erreur lors de l'initialisation de l'agent {agent_info.name}: {e}")
                import traceback
                traceback.print_exc()
        
        # Compter les sous-agents
        sous_agents_count = sum(1 for agent in self.agents.values() if agent.parent)
        total_agents = len(self.agents) + sous_agents_count
        
        self.logger.info(f"Initialisation terminée: {initialized_count}/{len(sorted_agents)} agents initialisés avec succès")
        self.logger.info(f"Total agents configurés: {total_agents}")
        
        self.initialized = initialized_count > 0
        return self.initialized
    
    async def check_health(self) -> Dict[str, Any]:
        """Vérifier la santé de tous les agents.
        
        Returns:
            Dictionnaire avec le statut de santé
        """
        self.logger.info("Vérification de santé des agents...")
        
        healthy = 0
        total = 0
        
        for agent_name, agent_info in self.agents.items():
            if agent_info.instantiate and agent_info.enabled:
                total += 1
                
                if agent_info.status == AgentStatus.READY:
                    # Vérifier la santé de l'instance
                    if agent_info.instance and hasattr(agent_info.instance, 'health_check'):
                        try:
                            health_result = agent_info.instance.health_check()
                            if health_result and health_result.get("status") == "healthy":
                                healthy += 1
                                agent_info.last_health_check = datetime.now()
                            else:
                                agent_info.status = AgentStatus.ERROR
                        except Exception as e:
                            self.logger.error(f"Erreur lors du health check pour {agent_name}: {e}")
                            agent_info.status = AgentStatus.ERROR
                    else:
                        # Si pas de méthode health_check, considérer comme healthy
                        healthy += 1
                        agent_info.last_health_check = datetime.now()
                elif agent_info.status == AgentStatus.ERROR:
                    self.logger.warning(f"Agent {agent_name} en état d'erreur")
                else:
                    self.logger.warning(f"Agent {agent_name} non prêt: {agent_info.status}")
        
        health_percentage = (healthy / total * 100) if total > 0 else 0
        
        self.logger.info(f"Résumé santé: {healthy}/{total} agents en bonne santé")
        
        return {
            "healthy": healthy,
            "total": total,
            "percentage": health_percentage,
            "timestamp": datetime.now().isoformat()
        }
    
    def execute_task(self, agent_name: str, task_name: str, **kwargs):
        """Exécuter une tâche avec un agent spécifique.
        
        Args:
            agent_name: Nom de l'agent
            task_name: Nom de la tâche/capacité
            **kwargs: Arguments supplémentaires
            
        Returns:
            Résultat de l'exécution ou None en cas d'erreur
        """
        print(f"\n" + "="*80)
        print(f"DEBUG execute_task - ENTRÉE")
        print(f"  agent_name: {agent_name}")
        print(f"  task_name: {task_name}")
        
        if agent_name not in self.agents:
            print(f"  ERREUR: Agent {agent_name} non trouvé dans self.agents!")
            return None
        
        agent_info = self.agents[agent_name]
        print(f"  AgentInfo trouvé: {agent_info.name}")
        print(f"  Agent instance: {agent_info.instance}")
        
        # Obtenir l'instance réelle de l'agent
        agent = agent_info.instance
        if agent is None:
            print(f"  ERREUR: L'agent {agent_name} n'a pas d'instance!")
            return None
        
        print(f"  Agent instance type: {type(agent)}")
        print(f"  Agent capabilities: {agent.capabilities}")
        
        # Vérifier si l'agent supporte cette tâche
        if task_name not in agent.capabilities:
            print(f"  Tâche {task_name} non supportée par l'agent {agent_name}. Capacités: {agent.capabilities}")
            return None
        
        print(f"  ✅ Tâche supportée, exécution...")
        
        try:
            # Préparation des arguments
            execution_args = {
                "task_name": task_name,
                "task_data": kwargs.get("task_data", {}),
                "context": kwargs.get("context", {}),
                "orchestrator": self
            }
            
            # Exécution de la tâche
            start_time = time.time()
            result = agent.execute_capability(task_name, **execution_args)
            execution_time = time.time() - start_time
            
            # Journalisation des résultats
            if hasattr(self, 'logger'):
                self.logger.info(f"Tâche {task_name} exécutée par {agent_name} en {execution_time:.2f}s")
            else:
                print(f"Tâche {task_name} exécutée par {agent_name} en {execution_time:.2f}s")
            
            # Stockage des résultats
            if result is not None:
                self.task_results.append({
                    "task": task_name,
                    "agent": agent_name,
                    "result": result,
                    "execution_time": execution_time,
                    "timestamp": datetime.now().isoformat()
                })
            
            print(f"  ✅ Résultat: {result}")
            return result
            
        except Exception as e:
            print(f"  ❌ Erreur lors de l'exécution: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    async def execute_workflow(self, workflow_name: str, workflow_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Exécuter un workflow complet.
        
        Args:
            workflow_name: Nom du workflow
            workflow_data: Données du workflow
            
        Returns:
            Résultats du workflow
        """
        if not self.initialized:
            self.logger.error("Orchestrateur non initialisé")
            return {"status": "error", "message": "Orchestrateur non initialisé"}
        
        self.logger.info(f"Exécution du workflow: {workflow_name}")
        
        workflows = self.config.get("workflows", {})
        if workflow_name not in workflows:
            self.logger.error(f"Workflow {workflow_name} non trouvé")
            return {"status": "error", "message": f"Workflow {workflow_name} non trouvé"}
        
        workflow = workflows[workflow_name]
        steps = workflow.get("steps", [])
        
        results = {
            "workflow": workflow_name,
            "start_time": datetime.now().isoformat(),
            "steps": [],
            "overall_status": "success"
        }
        
        for step in steps:
            step_name = step.get("name", f"step_{len(results['steps'])}")
            agent_name = step.get("agent")
            task_name = step.get("task")
            step_data = step.get("data", {})
            
            if not agent_name or not task_name:
                self.logger.warning(f"Step {step_name} ignoré: agent ou task manquant")
                continue
            
            self.logger.info(f"Exécution du step {step_name}: {agent_name}.{task_name}")
            
            step_result = {
                "step": step_name,
                "agent": agent_name,
                "task": task_name,
                "start_time": datetime.now().isoformat()
            }
            
            try:
                # Exécuter la tâche
                task_result = self.execute_task(agent_name, task_name, task_data=step_data, context=workflow_data)
                
                step_result["end_time"] = datetime.now().isoformat()
                step_result["result"] = task_result
                
                if task_result is None:
                    step_result["status"] = "failed"
                    results["overall_status"] = "partial_failure"
                    self.logger.warning(f"Step {step_name} échoué")
                else:
                    step_result["status"] = "success"
                    self.logger.info(f"Step {step_name} terminé avec succès")
                    
            except Exception as e:
                step_result["end_time"] = datetime.now().isoformat()
                step_result["status"] = "error"
                step_result["error"] = str(e)
                results["overall_status"] = "failure"
                self.logger.error(f"Erreur lors du step {step_name}: {e}")
            
            results["steps"].append(step_result)
        
        results["end_time"] = datetime.now().isoformat()
        
        self.logger.info(f"Workflow {workflow_name} terminé avec statut: {results['overall_status']}")
        
        return results
    
    def get_agent_status(self, agent_name: str = None) -> Dict[str, Any]:
        """Obtenir le statut d'un agent ou de tous les agents.
        
        Args:
            agent_name: Nom de l'agent (None pour tous les agents)
            
        Returns:
            Statut de(s) l'agent(s)
        """
        if agent_name:
            if agent_name not in self.agents:
                return {"error": f"Agent {agent_name} non trouvé"}
            
            agent_info = self.agents[agent_name]
            return {
                "name": agent_info.name,
                "display_name": agent_info.display_name,
                "status": agent_info.status.value,
                "capabilities": agent_info.capabilities,
                "last_health_check": agent_info.last_health_check.isoformat() if agent_info.last_health_check else None,
                "initialization_order": agent_info.initialization_order,
                "dependencies": agent_info.dependencies,
                "purpose": agent_info.purpose
            }
        else:
            return {
                "total_agents": len(self.agents),
                "initialized_agents": sum(1 for a in self.agents.values() if a.status == AgentStatus.READY),
                "agents": {
                    name: {
                        "display_name": info.display_name,
                        "status": info.status.value,
                        "capabilities": info.capabilities,
                        "initialization_order": info.initialization_order
                    }
                    for name, info in self.agents.items()
                }
            }
    
    async def shutdown(self):
        """Arrêter l'orchestrateur et tous les agents."""
        self.logger.info("Arrêt de l'orchestrateur...")
        
        for agent_name, agent_info in self.agents.items():
            if agent_info.instance and hasattr(agent_info.instance, 'cleanup'):
                try:
                    await agent_info.instance.cleanup()
                    self.logger.info(f"Agent {agent_name} nettoyé")
                except Exception as e:
                    self.logger.error(f"Erreur lors du nettoyage de l'agent {agent_name}: {e}")
        
        self.initialized = False
        self.logger.info("Orchestrateur arrêté")

# Test rapide
async def quick_test():
    """Test rapide de l'orchestrateur."""
    print("Test rapide de l'orchestrateur...")
    
    try:
        # Initialiser l'orchestrateur
        orchestrator = SmartContractOrchestrator()
        
        # Charger la configuration
        if not orchestrator.load_configuration():
            print("✗ Échec du chargement de la configuration")
            return False
        
        print("✓ Configuration chargée")
        
        # Initialiser les agents
        success = await orchestrator.initialize_agents()
        if not success:
            print("✗ Échec de l'initialisation des agents")
            return False
        
        print(f"✓ {len([a for a in orchestrator.agents.values() if a.status == AgentStatus.READY])} agents initialisés")
        
        # Vérifier la santé des agents
        health = await orchestrator.check_health()
        health_percentage = (health["healthy"] / health["total"]) * 100 if health["total"] > 0 else 0
        print(f"✓ Santé: {health_percentage:.1f}%")
        
        # Exécuter une tâche de test
        print("Exécution de la tâche: validate_config")
        
        # CORRECTION: Ajouter "architect" comme premier argument
        result = orchestrator.execute_task("architect", "validate_config")
        
        if result is None:
            print("✓ Tâche test: failed")
            return False
        
        print(f"✓ Tâche test: success - {result}")
        return True
        
    except Exception as e:
        print(f"✗ Erreur lors du test: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Orchestrateur de pipeline de développement de smart contracts")
    parser.add_argument("--test", action="store_true", help="Exécuter le test rapide")
    parser.add_argument("--workflow", type=str, help="Exécuter un workflow spécifique")
    parser.add_argument("--config", type=str, default="project_config.yaml", help="Chemin vers le fichier de configuration")
    
    args = parser.parse_args()
    
    if args.test:
        success = asyncio.run(quick_test())
        sys.exit(0 if success else 1)
    elif args.workflow:
        orchestrator = SmartContractOrchestrator(args.config)
        
        if orchestrator.load_configuration():
            asyncio.run(orchestrator.initialize_agents())
            result = asyncio.run(orchestrator.execute_workflow(args.workflow))
            print(json.dumps(result, indent=2, default=str))
        else:
            print("Échec du chargement de la configuration")
            sys.exit(1)
    else:
        print("Usage: python orchestrator.py --test | --workflow <workflow_name>")
        sys.exit(1)
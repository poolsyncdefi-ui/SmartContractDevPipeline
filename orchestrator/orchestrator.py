"""
Orchestrateur principal du pipeline de développement
Coordinate les agents et sous-agents
"""
import asyncio
import yaml
from typing import Dict, List, Any
from pathlib import Path
import logging

class Orchestrator:
    def __init__(self, config_path: str = "config.yaml"):
        self.config_path = config_path
        self.config = self.load_config()
        self.agents = {}
        self.logger = logging.getLogger(__name__)
        self.initialized = False
    
    def load_config(self) -> Dict[str, Any]:
        """Charge la configuration depuis le fichier YAML"""
        try:
            with open(self.config_path, 'r') as f:
                return yaml.safe_load(f) or {}
        except FileNotFoundError:
            return {"agents": {}, "workflow": {}}
    
    async def initialize_agents(self):
        """Initialise tous les agents du pipeline"""
        if self.initialized:
            return
        
        self.logger.info("Initialisation des agents...")
        
        # Dynamiquement importer les agents basés sur la config
        agents_to_load = self.config.get("agents", {})
        
        for agent_name, agent_config in agents_to_load.items():
            if agent_config.get("enabled", True):
                try:
                    # Construction du chemin d'import
                    module_path = agent_config.get("module", f"agents.{agent_name}.agent")
                    agent_class_name = agent_config.get("class", f"{agent_name.capitalize()}Agent")
                    
                    # Import dynamique
                    module = __import__(module_path, fromlist=[agent_class_name])
                    agent_class = getattr(module, agent_class_name)
                    
                    # Instanciation
                    agent_instance = agent_class(agent_config.get("config_path", ""))
                    self.agents[agent_name] = agent_instance
                    
                    self.logger.info(f"✅ Agent {agent_name} initialisé")
                    
                except Exception as e:
                    self.logger.error(f"❌ Erreur lors de l'initialisation de {agent_name}: {e}")
        
        self.initialized = True
        self.logger.info(f"✅ {len(self.agents)} agents initialisés")
    
    async def execute_workflow(self, workflow_name: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Exécute un workflow prédéfini"""
        self.logger.info(f"Exécution du workflow: {workflow_name}")
        
        if not self.initialized:
            await self.initialize_agents()
        
        workflow = self.config.get("workflow", {}).get(workflow_name, {})
        steps = workflow.get("steps", [])
        
        results = {}
        current_data = input_data.copy()
        
        for step in steps:
            agent_name = step.get("agent")
            task = step.get("task")
            parameters = step.get("parameters", {})
            
            if agent_name in self.agents:
                try:
                    self.logger.info(f"  → Étape: {agent_name}.{task}")
                    
                    # Fusionner les paramètres
                    task_data = {**parameters, **current_data}
                    
                    # Exécuter la tâche
                    result = await self.agents[agent_name].execute(task_data, {})
                    
                    # Mettre à jour les données pour les étapes suivantes
                    if result.get("success"):
                        current_data.update(result.get("output", {}))
                        results[step.get("id", task)] = result
                    else:
                        self.logger.error(f"Échec de l'étape {task}")
                        break
                        
                except Exception as e:
                    self.logger.error(f"Erreur dans l'étape {task}: {e}")
                    break
        
        return {
            "workflow": workflow_name,
            "success": len(results) == len(steps),
            "results": results,
            "output_data": current_data
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Vérifie la santé de tous les agents"""
        health_status = {"orchestrator": "healthy", "agents": {}}
        
        for agent_name, agent_instance in self.agents.items():
            try:
                health = await agent_instance.health_check()
                health_status["agents"][agent_name] = health
            except Exception as e:
                health_status["agents"][agent_name] = {
                    "status": "error",
                    "error": str(e)
                }
        
        return health_status

# Point d'entrée principal
async def main():
    orchestrator = Orchestrator()
    await orchestrator.initialize_agents()
    
    # Exemple d'exécution
    health = await orchestrator.health_check()
    print(f"État du système: {health}")

if __name__ == "__main__":
    asyncio.run(main())

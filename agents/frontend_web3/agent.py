"""
Agent Frontend_web3 - Agent principal
"""
from typing import Dict, Any, List
import yaml
import logging
from base_agent import BaseAgent

class Frontend_web3Agent(BaseAgent):
    """Agent spécialisé en Frontend Web3"""
    
    def __init__(self, config_path: str):
        super().__init__(config_path)
        self.specialization = "frontend_web3"
        self.sub_agents = {}
        self._initialize_sub_agents()
        self.logger.info(f"Agent {self.agent_id} initialisé")
    
    def _initialize_sub_agents(self):
        """Initialise les sous-agents spécialisés"""
        try:
            from .sous_agents import *
            
            sub_agent_configs = self.config.get("sub_agents", {})
            
            for sub_agent_name, agent_config in sub_agent_configs.items():
                if agent_config.get("enabled", True):
                    agent_class_name = f"{sub_agent_name.capitalize().replace('_', '')}SubAgent"
                    agent_class = globals().get(agent_class_name)
                    
                    if agent_class:
                        sub_agent = agent_class(agent_config.get("config_path", ""))
                        self.sub_agents[sub_agent_name] = sub_agent
                        self.logger.info(f"Sous-agent {sub_agent_name} initialisé")
                    else:
                        self.logger.warning(f"Classe non trouvée pour {sub_agent_name}")
        
        except ImportError as e:
            self.logger.error(f"Erreur lors de l'import des sous-agents: {e}")
        except Exception as e:
            self.logger.error(f"Erreur lors de l'initialisation des sous-agents: {e}")
    
    async def execute(self, task_data: Dict[str, Any], workflow_context: Dict[str, Any]) -> Dict[str, Any]:
        """Exécute une tâche"""
        task_type = task_data.get("task_type", "unknown")
        
        # Vérifier si on doit déléguer à un sous-agent
        sub_agent_mapping = self.config.get("sub_agent_mapping", {})
        
        for pattern, agent_name in sub_agent_mapping.items():
            if task_type.startswith(pattern):
                if agent_name in self.sub_agents:
                    self.logger.info(f"Délégation au sous-agent {agent_name}")
                    return await self.sub_agents[agent_name].execute(task_data, workflow_context)
        
        # Exécuter localement
        self.logger.info(f"Exécution de la tâche {task_type}")
        
        # Implémentation spécifique à l'agent
        result = await self._execute_frontend_web3(task_data, workflow_context)
        
        return {
            "success": True,
            "agent": "frontend_web3",
            "task": task_type,
            "result": result,
            "sub_agents_used": list(self.sub_agents.keys())
        }
    
    async def _execute_frontend_web3(self, task_data: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Méthode spécifique à implémenter par chaque agent"""
        # À implémenter selon la spécialisation
        return {
            "message": f"Tâche exécutée par l'agent frontend_web3",
            "input_data": task_data,
            "context": context
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Vérifie la santé de l'agent et de ses sous-agents"""
        status = {
            "agent": "frontend_web3",
            "status": "healthy",
            "sub_agents": {}
        }
        
        for sub_agent_name, sub_agent in self.sub_agents.items():
            try:
                sub_health = await sub_agent.health_check()
                status["sub_agents"][sub_agent_name] = sub_health
            except Exception as e:
                status["sub_agents"][sub_agent_name] = {
                    "status": "error",
                    "error": str(e)
                }
        
        return status

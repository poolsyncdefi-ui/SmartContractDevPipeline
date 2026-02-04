#!/usr/bin/env python3
"""
Script de déploiement complet pour SmartContractDevPipeline
Déploie l'orchestrateur, les agents principaux et leurs sous-agents.
Date: 2026-02-03
Auteur: SmartContractDevPipeline
"""
import os
import sys
import yaml
import asyncio
import subprocess
from pathlib import Path
from typing import Dict, List, Any
import logging

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class AgentDeployer:
    """Classe principale pour déployer tous les composants du pipeline"""
    
    def __init__(self, project_root: str = None):
        """Initialise le déployeur avec le chemin du projet"""
        if project_root:
            self.project_root = os.path.abspath(project_root)
        else:
            # Utiliser le dossier courant
            self.project_root = os.path.abspath(".")
        self.agents_path = os.path.join(self.project_root, "agents")
        self.orchestrator_path = os.path.join(self.project_root, "orchestrator")
        
        # Structure des agents (identique à votre PS1)
        self.agent_structure = {
            "architect": [
                {"name": "cloud_architect", "type": "Cloud Architecture"},
                {"name": "blockchain_architect", "type": "Blockchain Architecture"},
                {"name": "microservices_architect", "type": "Microservices Architecture"},
            ],
            "coder": [
                {"name": "backend_coder", "type": "Backend Development"},
                {"name": "frontend_coder", "type": "Frontend Development"},
                {"name": "devops_coder", "type": "DevOps"},
            ],
            "smart_contract": [
                {"name": "solidity_expert", "type": "Solidity Development"},
                {"name": "security_expert", "type": "Smart Contract Security"},
                {"name": "gas_optimizer", "type": "Gas Optimization"},
                {"name": "formal_verification", "type": "Formal Verification"},
            ],
            "frontend_web3": [
                {"name": "react_expert", "type": "React/Next.js"},
                {"name": "web3_integration", "type": "Web3 Integration"},
                {"name": "ui_ux_expert", "type": "UI/UX Design"},
            ],
            "tester": [
                {"name": "unit_tester", "type": "Unit Testing"},
                {"name": "integration_tester", "type": "Integration Testing"},
                {"name": "e2e_tester", "type": "E2E Testing"},
                {"name": "fuzzing_expert", "type": "Fuzzing"},
            ]
        }
    
    def check_existing_deployment(self) -> Dict[str, bool]:
        """Vérifie quels composants sont déjà déployés"""
        status = {
            "orchestrator": False,
            "main_agents": {},
            "sub_agents": {}
        }
        
        # Vérifier l'orchestrateur
        orchestrator_files = ["orchestrator.py", "config.yaml", "requirements.txt"]
        if os.path.exists(self.orchestrator_path):
            status["orchestrator"] = all(
                os.path.exists(os.path.join(self.orchestrator_path, f))
                for f in orchestrator_files
            )
        
        # Vérifier les agents principaux
        for agent in self.agent_structure.keys():
            agent_dir = os.path.join(self.agents_path, agent)
            if os.path.exists(agent_dir):
                main_files = ["agent.py", "config.yaml", "__init__.py"]
                status["main_agents"][agent] = all(
                    os.path.exists(os.path.join(agent_dir, f))
                    for f in main_files
                )
            
            # Vérifier les sous-agents
            for sub_agent in self.agent_structure[agent]:
                sub_agent_dir = os.path.join(agent_dir, "sous_agents", sub_agent["name"])
                if os.path.exists(sub_agent_dir):
                    sub_files = ["config.yaml", "agent.py", "tools.py", "__init__.py"]
                    key = f"{agent}/{sub_agent['name']}"
                    status["sub_agents"][key] = all(
                        os.path.exists(os.path.join(sub_agent_dir, f))
                        for f in sub_files
                    )
        
        return status
    
    def create_orchestrator(self) -> bool:
        """Crée et configure l'orchestrateur s'il n'existe pas"""
        logger.info("🔧 Configuration de l'orchestrateur...")
        
        # Créer le dossier
        os.makedirs(self.orchestrator_path, exist_ok=True)
        
        # Fichier orchestrateur.py
        orchestrator_py = '''"""
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
'''
        
        # Fichier config.yaml pour l'orchestrateur
        orchestrator_config = '''# Configuration de l'orchestrateur
orchestrator:
  name: "SmartContractDevPipeline"
  version: "1.0.0"
  log_level: "INFO"

# Configuration des agents
agents:
  architect:
    enabled: true
    module: "agents.architect.agent"
    class: "ArchitectAgent"
    config_path: "agents/architect/config.yaml"
    priority: 1
    
  coder:
    enabled: true
    module: "agents.coder.agent"
    class: "CoderAgent"
    config_path: "agents/coder/config.yaml"
    priority: 2
    
  smart_contract:
    enabled: true
    module: "agents.smart_contract.agent"
    class: "SmartContractAgent"
    config_path: "agents/smart_contract/config.yaml"
    priority: 3
    
  frontend_web3:
    enabled: true
    module: "agents.frontend_web3.agent"
    class: "FrontendWeb3Agent"
    config_path: "agents/frontend_web3/config.yaml"
    priority: 4
    
  tester:
    enabled: true
    module: "agents.tester.agent"
    class: "TesterAgent"
    config_path: "agents/tester/config.yaml"
    priority: 5

# Définition des workflows
workflow:
  full_pipeline:
    name: "Pipeline complet de développement"
    description: "Workflow complet du développement d'un smart contract"
    steps:
      - id: "architecture"
        agent: "architect"
        task: "design_architecture"
        parameters:
          project_type: "smart_contract"
          complexity: "medium"
      
      - id: "backend_dev"
        agent: "coder"
        task: "develop_backend"
        parameters:
          language: "python"
          framework: "fastapi"
      
      - id: "smart_contract_dev"
        agent: "smart_contract"
        task: "develop_contract"
        parameters:
          blockchain: "ethereum"
          standard: "ERC20"
      
      - id: "frontend_dev"
        agent: "frontend_web3"
        task: "develop_frontend"
        parameters:
          framework: "nextjs"
          web3_library: "ethers"
      
      - id: "testing"
        agent: "tester"
        task: "run_full_tests"
        parameters:
          test_types: ["unit", "integration", "e2e"]
'''
        
        # Fichier requirements.txt
        requirements = '''# Dépendances de l'orchestrateur
aiohttp>=3.9.0
PyYAML>=6.0
asyncio>=3.4.3
pydantic>=2.5.0
python-dotenv>=1.0.0
web3>=6.0.0
'''
        
        # Créer les fichiers
        files_to_create = {
            "orchestrator.py": orchestrator_py,
            "config.yaml": orchestrator_config,
            "requirements.txt": requirements,
            "__init__.py": "# Orchestrator package\n"
        }
        
        try:
            for filename, content in files_to_create.items():
                filepath = os.path.join(self.orchestrator_path, filename)
                if not os.path.exists(filepath):
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(content)
                    logger.info(f"  ✅ {filename} créé")
                else:
                    logger.info(f"  ⏭️ {filename} existe déjà")
            
            return True
        except Exception as e:
            logger.error(f"❌ Erreur lors de la création de l'orchestrateur: {e}")
            return False
    
    def create_main_agent(self, agent_name: str) -> bool:
        """Crée un agent principal s'il n'existe pas"""
        agent_dir = os.path.join(self.agents_path, agent_name)
        os.makedirs(agent_dir, exist_ok=True)
        
        # Fichier agent.py pour l'agent principal
        agent_py = f'''"""
Agent {agent_name.capitalize()} - Agent principal
"""
from typing import Dict, Any, List
import yaml
import logging
from base_agent import BaseAgent

class {agent_name.capitalize()}Agent(BaseAgent):
    """Agent spécialisé en {agent_name.replace('_', ' ').title()}"""
    
    def __init__(self, config_path: str):
        super().__init__(config_path)
        self.specialization = "{agent_name}"
        self.sub_agents = {{}}
        self._initialize_sub_agents()
        self.logger.info(f"Agent {{self.agent_id}} initialisé")
    
    def _initialize_sub_agents(self):
        """Initialise les sous-agents spécialisés"""
        try:
            from .sous_agents import *
            
            sub_agent_configs = self.config.get("sub_agents", {{}})
            
            for sub_agent_name, agent_config in sub_agent_configs.items():
                if agent_config.get("enabled", True):
                    agent_class_name = f"{{sub_agent_name.capitalize().replace('_', '')}}SubAgent"
                    agent_class = globals().get(agent_class_name)
                    
                    if agent_class:
                        sub_agent = agent_class(agent_config.get("config_path", ""))
                        self.sub_agents[sub_agent_name] = sub_agent
                        self.logger.info(f"Sous-agent {{sub_agent_name}} initialisé")
                    else:
                        self.logger.warning(f"Classe non trouvée pour {{sub_agent_name}}")
        
        except ImportError as e:
            self.logger.error(f"Erreur lors de l'import des sous-agents: {{e}}")
        except Exception as e:
            self.logger.error(f"Erreur lors de l'initialisation des sous-agents: {{e}}")
    
    async def execute(self, task_data: Dict[str, Any], workflow_context: Dict[str, Any]) -> Dict[str, Any]:
        """Exécute une tâche"""
        task_type = task_data.get("task_type", "unknown")
        
        # Vérifier si on doit déléguer à un sous-agent
        sub_agent_mapping = self.config.get("sub_agent_mapping", {{}})
        
        for pattern, agent_name in sub_agent_mapping.items():
            if task_type.startswith(pattern):
                if agent_name in self.sub_agents:
                    self.logger.info(f"Délégation au sous-agent {{agent_name}}")
                    return await self.sub_agents[agent_name].execute(task_data, workflow_context)
        
        # Exécuter localement
        self.logger.info(f"Exécution de la tâche {{task_type}}")
        
        # Implémentation spécifique à l'agent
        result = await self._execute_{agent_name}(task_data, workflow_context)
        
        return {{
            "success": True,
            "agent": "{agent_name}",
            "task": task_type,
            "result": result,
            "sub_agents_used": list(self.sub_agents.keys())
        }}
    
    async def _execute_{agent_name}(self, task_data: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Méthode spécifique à implémenter par chaque agent"""
        # À implémenter selon la spécialisation
        return {{
            "message": f"Tâche exécutée par l'agent {agent_name}",
            "input_data": task_data,
            "context": context
        }}
    
    async def health_check(self) -> Dict[str, Any]:
        """Vérifie la santé de l'agent et de ses sous-agents"""
        status = {{
            "agent": "{agent_name}",
            "status": "healthy",
            "sub_agents": {{}}
        }}
        
        for sub_agent_name, sub_agent in self.sub_agents.items():
            try:
                sub_health = await sub_agent.health_check()
                status["sub_agents"][sub_agent_name] = sub_health
            except Exception as e:
                status["sub_agents"][sub_agent_name] = {{
                    "status": "error",
                    "error": str(e)
                }}
        
        return status
'''
        
        # Fichier config.yaml pour l'agent principal
        config_yaml = f'''# Configuration de l'agent {agent_name}
agent:
  id: "{agent_name}_01"
  name: "{agent_name.capitalize()} Agent"
  version: "1.0.0"
  description: "Agent spécialisé en {agent_name.replace('_', ' ').title()}"
  
  capabilities:
    - "task_execution"
    - "sub_agent_management"
    - "health_monitoring"
  
  parameters:
    max_concurrent_tasks: 5
    timeout_seconds: 300
    retry_attempts: 3

# Sous-agents (à adapter selon l'agent)
sub_agents:{self._generate_sub_agent_config(agent_name)}

# Mapping des tâches vers les sous-agents
sub_agent_mapping:{self._generate_sub_agent_mapping(agent_name)}

logging:
  level: "INFO"
  file: "logs/{agent_name}.log"
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

api:
  enabled: true
  port: {self._get_agent_port(agent_name)}
  endpoints:
    - "/execute"
    - "/health"
    - "/status"
'''
        
        # Fichiers à créer
        files_to_create = {
            "agent.py": agent_py,
            "config.yaml": config_yaml,
            "__init__.py": f"# {agent_name.capitalize()} Agent package\n",
            "tools.py": f"# Outils pour l'agent {agent_name}\n\nclass {agent_name.capitalize()}Tools:\n    pass\n"
        }
        
        try:
            for filename, content in files_to_create.items():
                filepath = os.path.join(agent_dir, filename)
                if not os.path.exists(filepath):
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(content)
                    logger.info(f"  ✅ {agent_name}/{filename} créé")
            
            return True
        except Exception as e:
            logger.error(f"❌ Erreur lors de la création de l'agent {agent_name}: {e}")
            return False
    
    def _generate_sub_agent_config(self, parent_agent: str) -> str:
        """Génère la configuration YAML pour les sous-agents"""
        if parent_agent not in self.agent_structure:
            return ""
        
        config_lines = []
        for sub_agent in self.agent_structure[parent_agent]:
            config_lines.append(f'''
  {sub_agent["name"]}:
    enabled: true
    config_path: "agents/{parent_agent}/sous_agents/{sub_agent['name']}/config.yaml"
    specialization: "{sub_agent['type']}"
    priority: 1''')
        
        return "".join(config_lines)
    
    def _generate_sub_agent_mapping(self, parent_agent: str) -> str:
        """Génère le mapping des tâches pour les sous-agents"""
        mappings = {
            "architect": '''
  "cloud_": "cloud_architect"
  "aws_": "cloud_architect"
  "azure_": "cloud_architect"
  "gcp_": "cloud_architect"
  "blockchain_": "blockchain_architect"
  "web3_": "blockchain_architect"
  "smart_contract_": "blockchain_architect"
  "microservices_": "microservices_architect"
  "service_": "microservices_architect"
  "api_": "microservices_architect"''',
            
            "coder": '''
  "backend_": "backend_coder"
  "server_": "backend_coder"
  "api_": "backend_coder"
  "frontend_": "frontend_coder"
  "ui_": "frontend_coder"
  "react_": "frontend_coder"
  "devops_": "devops_coder"
  "deploy_": "devops_coder"
  "ci_cd_": "devops_coder"''',
            
            "smart_contract": '''
  "solidity_": "solidity_expert"
  "contract_": "solidity_expert"
  "security_": "security_expert"
  "audit_": "security_expert"
  "gas_": "gas_optimizer"
  "optimize_": "gas_optimizer"
  "formal_": "formal_verification"
  "verify_": "formal_verification"''',
            
            "frontend_web3": '''
  "react_": "react_expert"
  "nextjs_": "react_expert"
  "web3_": "web3_integration"
  "wallet_": "web3_integration"
  "ui_": "ui_ux_expert"
  "ux_": "ui_ux_expert"
  "design_": "ui_ux_expert"''',
            
            "tester": '''
  "unit_": "unit_tester"
  "test_unit": "unit_tester"
  "integration_": "integration_tester"
  "test_integration": "integration_tester"
  "e2e_": "e2e_tester"
  "end_to_end": "e2e_tester"
  "fuzz_": "fuzzing_expert"
  "fuzzing_": "fuzzing_expert"'''
        }
        
        return mappings.get(parent_agent, "")
    
    def _get_agent_port(self, agent_name: str) -> int:
        """Retourne un port unique pour chaque agent"""
        port_mapping = {
            "architect": 8001,
            "coder": 8002,
            "smart_contract": 8003,
            "frontend_web3": 8004,
            "tester": 8005,
            "orchestrator": 8000
        }
        return port_mapping.get(agent_name, 8080)
    
    def create_sub_agents(self, parent_agent: str) -> bool:
        """Crée les sous-agents pour un agent parent"""
        if parent_agent not in self.agent_structure:
            return False
        
        logger.info(f"  📁 Création des sous-agents pour {parent_agent}...")
        
        for sub_agent_info in self.agent_structure[parent_agent]:
            sub_agent_name = sub_agent_info["name"]
            sub_agent_dir = os.path.join(
                self.agents_path, 
                parent_agent, 
                "sous_agents", 
                sub_agent_name
            )
            
            # Créer le dossier
            os.makedirs(sub_agent_dir, exist_ok=True)
            
            # Nom de classe formaté
            class_name = sub_agent_name.replace("_", " ").title().replace(" ", "")
            
            # Fichier agent.py pour le sous-agent
            sub_agent_py = f'''"""
Sous-agent {sub_agent_info['type']}
Spécialisation: {sub_agent_info['type']}
"""
from typing import Dict, Any
import yaml
import logging

class {class_name}SubAgent:
    """Sous-agent spécialisé en {sub_agent_info['type']}"""
    
    def __init__(self, config_path: str = ""):
        self.config_path = config_path
        self.config = self._load_config()
        self.logger = logging.getLogger(__name__)
        self.agent_id = f"{sub_agent_name}_sub_01"
        
        self.logger.info(f"Sous-agent {{self.agent_id}} initialisé")
    
    def _load_config(self) -> Dict[str, Any]:
        """Charge la configuration"""
        if self.config_path and os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r') as f:
                    return yaml.safe_load(f)
            except Exception as e:
                self.logger.error(f"Erreur de chargement config: {{e}}")
        
        # Configuration par défaut
        return {{
            "agent": {{
                "name": "{sub_agent_info['type']}",
                "specialization": "{sub_agent_info['type']}",
                "version": "1.0.0"
            }},
            "capabilities": ["task_execution", "specialized_operation"]
        }}
    
    async def execute(self, task_data: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Exécute une tâche spécialisée"""
        task_type = task_data.get("task_type", "unknown")
        
        self.logger.info(f"Exécution de la tâche {{task_type}}")
        
        # Implémentation spécifique au sous-agent
        result = await self._execute_specialized(task_data, context)
        
        return {{
            "success": True,
            "sub_agent": "{sub_agent_name}",
            "task": task_type,
            "result": result,
            "specialization": "{sub_agent_info['type']}"
        }}
    
    async def _execute_specialized(self, task_data: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Méthode spécialisée à implémenter"""
        # À implémenter selon la spécialisation
        return {{
            "message": "Tâche exécutée par le sous-agent spécialisé",
            "specialization": "{sub_agent_info['type']}",
            "input": task_data
        }}
    
    async def health_check(self) -> Dict[str, Any]:
        """Vérifie la santé du sous-agent"""
        return {{
            "agent": "{sub_agent_name}",
            "status": "healthy",
            "type": "sub_agent",
            "specialization": "{sub_agent_info['type']}",
            "config_loaded": bool(self.config)
        }}
    
    def get_agent_info(self) -> Dict[str, Any]:
        """Retourne les informations du sous-agent"""
        return {{
            "id": self.agent_id,
            "name": "{sub_agent_info['type']}",
            "type": "sub_agent",
            "parent": "{parent_agent}",
            "specialization": "{sub_agent_info['type']}",
            "version": "1.0.0"
        }}
'''
            
            # Fichier config.yaml pour le sous-agent
            sub_config_yaml = f'''# Configuration du sous-agent {sub_agent_name}
sub_agent:
  id: "{sub_agent_name}_01"
  name: "{sub_agent_info['type']}"
  parent: "{parent_agent}"
  specialization: "{sub_agent_info['type']}"
  version: "1.0.0"

capabilities:
  - "specialized_task_execution"
  - "domain_expertise"

parameters:
  timeout_seconds: 60
  max_retries: 2

logging:
  level: "INFO"
'''
            
            # Fichiers à créer
            sub_files = {
                "agent.py": sub_agent_py,
                "config.yaml": sub_config_yaml,
                "tools.py": f"# Outils pour {sub_agent_info['type']}\n",
                "__init__.py": f"# {class_name}SubAgent package\n"
            }
            
            try:
                for filename, content in sub_files.items():
                    filepath = os.path.join(sub_agent_dir, filename)
                    if not os.path.exists(filepath):
                        with open(filepath, 'w', encoding='utf-8') as f:
                            f.write(content)
                
                logger.info(f"    ✅ {parent_agent}/{sub_agent_name}")
                
            except Exception as e:
                logger.error(f"    ❌ Erreur avec {sub_agent_name}: {e}")
                return False
        
        return True
    
    def create_init_files(self):
        """Crée les fichiers __init__.py pour l'importation"""
        logger.info("📄 Création des fichiers d'import...")
        
        # Fichier __init__.py principal
        main_init = os.path.join(self.agents_path, "__init__.py")
        with open(main_init, 'w', encoding='utf-8') as f:
            f.write('''# Package agents
from .architect.agent import ArchitectAgent
from .coder.agent import CoderAgent
from .smart_contract.agent import SmartContractAgent
from .frontend_web3.agent import FrontendWeb3Agent
from .tester.agent import TesterAgent

__all__ = [
    "ArchitectAgent",
    "CoderAgent",
    "SmartContractAgent",
    "FrontendWeb3Agent",
    "TesterAgent"
]
''')
        
        # Fichiers __init__.py pour les sous-agents de chaque parent
        for parent_agent in self.agent_structure.keys():
            init_dir = os.path.join(self.agents_path, parent_agent, "sous_agents")
            init_file = os.path.join(init_dir, "__init__.py")
            
            # Générer les imports dynamiquement
            imports = ["# Import des sous-agents\n"]
            all_list = []
            
            for sub_agent in self.agent_structure[parent_agent]:
                class_name = sub_agent["name"].replace("_", " ").title().replace(" ", "") + "SubAgent"
                imports.append(f"from .{sub_agent['name']}.agent import {class_name}")
                all_list.append(f'"{class_name}"')
            
            imports.append(f"\n__all__ = [{', '.join(all_list)}]")
            
            with open(init_file, 'w', encoding='utf-8') as f:
                f.write("\n".join(imports))
            
            logger.info(f"  ✅ {parent_agent}/sous_agents/__init__.py")
    
    def create_base_agent(self):
        """Crée la classe BaseAgent si elle n'existe pas"""
        base_agent_path = os.path.join(self.project_root, "base_agent.py")
        
        if not os.path.exists(base_agent_path):
            base_agent_code = '''"""
Classe de base pour tous les agents
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import yaml
import logging
import uuid
from datetime import datetime

class BaseAgent(ABC):
    """Classe abstraite de base pour tous les agents"""
    
    def __init__(self, config_path: str = ""):
        self.config_path = config_path
        self.config = self._load_config()
        self.agent_id = f"{self.__class__.__name__.lower()}_{uuid.uuid4().hex[:8]}"
        self.logger = logging.getLogger(self.__class__.__name__)
        self.created_at = datetime.now()
        self.last_activity = datetime.now()
        
        self.logger.info(f"Agent {self.agent_id} initialisé")
    
    def _load_config(self) -> Dict[str, Any]:
        """Charge la configuration depuis un fichier YAML"""
        if self.config_path and os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r') as f:
                    return yaml.safe_load(f) or {}
            except Exception as e:
                self.logger.error(f"Erreur de chargement de la config: {e}")
        
        # Configuration par défaut
        return {
            "agent": {
                "name": self.__class__.__name__,
                "version": "1.0.0"
            },
            "logging": {
                "level": "INFO"
            }
        }
    
    @abstractmethod
    async def execute(self, task_data: Dict[str, Any], workflow_context: Dict[str, Any]) -> Dict[str, Any]:
        """Méthode abstraite pour exécuter une tâche"""
        pass
    
    async def health_check(self) -> Dict[str, Any]:
        """Vérifie la santé de l'agent"""
        return {
            "agent_id": self.agent_id,
            "status": "healthy",
            "uptime": str(datetime.now() - self.created_at),
            "last_activity": self.last_activity.isoformat(),
            "config_loaded": bool(self.config)
        }
    
    def get_agent_info(self) -> Dict[str, Any]:
        """Retourne les informations de l'agent"""
        return {
            "id": self.agent_id,
            "name": self.config.get("agent", {}).get("name", self.__class__.__name__),
            "class": self.__class__.__name__,
            "created_at": self.created_at.isoformat(),
            "config_path": self.config_path
        }
    
    def update_activity(self):
        """Met à jour le timestamp de la dernière activité"""
        self.last_activity = datetime.now()
    
    async def validate_input(self, task_data: Dict[str, Any]) -> bool:
        """Valide les données d'entrée"""
        required_fields = self.config.get("required_fields", [])
        
        for field in required_fields:
            if field not in task_data:
                self.logger.error(f"Champ requis manquant: {field}")
                return False
        
        return True
'''
            
            with open(base_agent_path, 'w', encoding='utf-8') as f:
                f.write(base_agent_code)
            
            logger.info("✅ base_agent.py créé")
    
    def create_requirements_file(self):
        """Crée le fichier requirements.txt global"""
        requirements_path = os.path.join(self.project_root, "requirements.txt")
        
        requirements = '''# Dépendances du projet SmartContractDevPipeline

# Core
python>=3.9
PyYAML>=6.0
pydantic>=2.5.0
python-dotenv>=1.0.0

# Async
aiohttp>=3.9.0
asyncio>=3.4.3

# Web3 & Blockchain
web3>=6.0.0
eth-account>=0.11.0
eth-typing>=3.0.0
cryptography>=41.0.0

# Development
black>=23.0.0
pytest>=7.0.0
pytest-asyncio>=0.21.0
mypy>=1.0.0

# API
fastapi>=0.104.0
uvicorn>=0.24.0
httpx>=0.25.0

# Utils
jinja2>=3.1.0
markdown>=3.5.0
rich>=13.0.0
'''
        
        with open(requirements_path, 'w', encoding='utf-8') as f:
            f.write(requirements)
        
        logger.info("✅ requirements.txt créé")
    
    def create_docker_compose(self):
        """Crée un docker-compose.yml pour déployer tous les agents"""
        docker_path = os.path.join(self.project_root, "docker-compose.yml")
        
        docker_compose = '''version: '3.8'

services:
  orchestrator:
    build: 
      context: .
      dockerfile: Dockerfile
    container_name: smartcontract-orchestrator
    ports:
      - "8000:8000"
    volumes:
      - ./orchestrator:/app/orchestrator
      - ./agents:/app/agents
      - ./logs:/app/logs
    environment:
      - LOG_LEVEL=INFO
      - ENVIRONMENT=production
    command: python orchestrator/orchestrator.py
    restart: unless-stopped
    networks:
      - agent-network

  architect:
    build:
      context: .
      dockerfile: Dockerfile.agent
    container_name: agent-architect
    ports:
      - "8001:8001"
    volumes:
      - ./agents/architect:/app/agent
      - ./logs:/app/logs
    environment:
      - AGENT_TYPE=architect
      - PARENT_ORCHESTRATOR=http://orchestrator:8000
    depends_on:
      - orchestrator
    restart: unless-stopped
    networks:
      - agent-network

  coder:
    build:
      context: .
      dockerfile: Dockerfile.agent
    container_name: agent-coder
    ports:
      - "8002:8002"
    volumes:
      - ./agents/coder:/app/agent
      - ./logs:/app/logs
    environment:
      - AGENT_TYPE=coder
      - PARENT_ORCHESTRATOR=http://orchestrator:8000
    depends_on:
      - orchestrator
    restart: unless-stopped
    networks:
      - agent-network

  smart_contract:
    build:
      context: .
      dockerfile: Dockerfile.agent
    container_name: agent-smart-contract
    ports:
      - "8003:8003"
    volumes:
      - ./agents/smart_contract:/app/agent
      - ./logs:/app/logs
    environment:
      - AGENT_TYPE=smart_contract
      - PARENT_ORCHESTRATOR=http://orchestrator:8000
    depends_on:
      - orchestrator
    restart: unless-stopped
    networks:
      - agent-network

  frontend_web3:
    build:
      context: .
      dockerfile: Dockerfile.agent
    container_name: agent-frontend-web3
    ports:
      - "8004:8004"
    volumes:
      - ./agents/frontend_web3:/app/agent
      - ./logs:/app/logs
    environment:
      - AGENT_TYPE=frontend_web3
      - PARENT_ORCHESTRATOR=http://orchestrator:8000
    depends_on:
      - orchestrator
    restart: unless-stopped
    networks:
      - agent-network

  tester:
    build:
      context: .
      dockerfile: Dockerfile.agent
    container_name: agent-tester
    ports:
      - "8005:8005"
    volumes:
      - ./agents/tester:/app/agent
      - ./logs:/app/logs
    environment:
      - AGENT_TYPE=tester
      - PARENT_ORCHESTRATOR=http://orchestrator:8000
    depends_on:
      - orchestrator
    restart: unless-stopped
    networks:
      - agent-network

networks:
  agent-network:
    driver: bridge

volumes:
  agent-data:
    driver: local
'''
        
        with open(docker_path, 'w', encoding='utf-8') as f:
            f.write(docker_compose)
        
        logger.info("✅ docker-compose.yml créé")
    
    # CORRECTION BUG PRINCIPAL : Méthode create_readme simplifiée
    def create_readme(self):
        """Crée un fichier README.md avec des instructions"""
        readme_path = os.path.join(self.project_root, "README.md")
        
        # Construction simple sans f-string multiligne complexe
        project_name = os.path.basename(self.project_root)
        
        content = f"# SmartContractDevPipeline\n\n"
        content += f"Pipeline de développement automatisé pour smart contracts avec agents IA.\n\n"
        content += f"## 📁 Structure du projet\n\n"
        content += f"```\n"
        content += f"{project_name}/\n"
        content += f"├── agents/                    # Agents principaux\n"
        content += f"│   ├── architect/            # Agent architecte\n"
        content += f"│   │   ├── sous_agents/      # Sous-agents spécialisés\n"
        content += f"│   │   │   ├── cloud_architect/\n"
        content += f"│   │   │   ├── blockchain_architect/\n"
        content += f"│   │   │   └── microservices_architect/\n"
        content += f"│   │   ├── agent.py         # Agent principal\n"
        content += f"│   │   └── config.yaml      # Configuration\n"
        content += f"│   ├── coder/               # Agent développeur\n"
        content += f"│   ├── smart_contract/      # Agent smart contract\n"
        content += f"│   ├── frontend_web3/       # Agent frontend Web3\n"
        content += f"│   └── tester/              # Agent testeur\n"
        content += f"├── orchestrator/            # Orchestrateur principal\n"
        content += f"│   ├── orchestrator.py      # Code de l'orchestrateur\n"
        content += f"│   └── config.yaml         # Configuration globale\n"
        content += f"├── base_agent.py           # Classe de base pour tous les agents\n"
        content += f"├── requirements.txt        # Dépendances Python\n"
        content += f"├── docker-compose.yml      # Déploiement Docker\n"
        content += f"└── README.md              # Ce fichier\n"
        content += f"```\n\n"
        content += f"## 🚀 Démarrage rapide\n\n"
        content += f"### 1. Installation des dépendances\n\n"
        content += f"```bash\n"
        content += f"pip install -r requirements.txt\n"
        content += f"```\n\n"
        content += f"### 2. Déploiement des agents\n\n"
        content += f"```bash\n"
        content += f"python deploy_pipeline.py\n"
        content += f"```\n\n"
        content += f"Options disponibles:\n"
        content += f"- `--path /chemin/vers/projet` : Chemin personnalisé du projet\n"
        content += f"- `--force` : Forcer le redéploiement complet\n"
        content += f"- `--verbose` : Mode détaillé\n\n"
        content += f"### 3. Tester l'orchestrateur\n\n"
        content += f"```bash\n"
        content += f"cd orchestrator\n"
        content += f"python orchestrator.py --test\n"
        content += f"```\n\n"
        content += f"### 4. Exécuter un workflow\n\n"
        content += f"```bash\n"
        content += f"python orchestrator.py --workflow full_pipeline\n"
        content += f"```\n\n"
        content += f"## 🔧 Agents et sous-agents\n\n"
        content += f"### Architecte (3 sous-agents)\n"
        content += f"- Cloud Architect\n"
        content += f"- Blockchain Architect\n"
        content += f"- Microservices Architect\n\n"
        content += f"### Développeur (3 sous-agents)\n"
        content += f"- Backend Developer\n"
        content += f"- Frontend Developer\n"
        content += f"- DevOps Engineer\n\n"
        content += f"### Smart Contract (4 sous-agents)\n"
        content += f"- Solidity Expert\n"
        content += f"- Security Expert\n"
        content += f"- Gas Optimizer\n"
        content += f"- Formal Verification\n\n"
        content += f"### Frontend Web3 (3 sous-agents)\n"
        content += f"- React/Next.js Expert\n"
        content += f"- Web3 Integration\n"
        content += f"- UI/UX Designer\n\n"
        content += f"### Testeur (4 sous-agents)\n"
        content += f"- Unit Tester\n"
        content += f"- Integration Tester\n"
        content += f"- E2E Tester\n"
        content += f"- Fuzzing Expert\n\n"
        content += f"## 🐛 Dépannage\n\n"
        content += f"### Problèmes d'import\n"
        content += f"```bash\n"
        content += f"export PYTHONPATH=\"$PYTHONPATH:{self.project_root}\"\n"
        content += f"```\n\n"
        content += f"Ou exécuter depuis la racine du projet:\n"
        content += f"```bash\n"
        content += f"cd {self.project_root}\n"
        content += f"python deploy_pipeline.py\n"
        content += f"```\n\n"
        content += f"## 📝 Personnalisation\n\n"
        content += f"1. Modifier les configurations dans `agents/*/config.yaml`\n"
        content += f"2. Ajouter de nouveaux sous-agents dans `deploy_pipeline.py`\n"
        content += f"3. Créer de nouveaux workflows dans `orchestrator/config.yaml`\n\n"
        content += f"## 📄 Licence\n\n"
        content += f"Projet SmartContractDevPipeline - Usage interne\n"
        
        try:
            with open(readme_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            logger.info("✅ README.md créé")
            return True
        except Exception as e:
            logger.error(f"❌ Erreur lors de la création du README: {e}")
            return False
    
    async def deploy_all(self, force_redeploy: bool = False) -> Dict[str, Any]:
        """Déploie tous les composants du pipeline"""
        logger.info("🚀 Déploiement du SmartContractDevPipeline")
        logger.info(f"📂 Chemin du projet: {self.project_root}")
        
        # Vérifier l'état actuel
        deployment_status = self.check_existing_deployment()
        
        if not force_redeploy:
            logger.info("🔍 Vérification des composants existants...")
            
            # Afficher le statut
            for component, status in deployment_status.items():
                if isinstance(status, dict):
                    for sub, sub_status in status.items():
                        if sub_status:
                            logger.info(f"  ✅ {component}/{sub} déjà déployé")
                elif status:
                    logger.info(f"  ✅ {component} déjà déployé")
        
        # Créer la structure de base
        os.makedirs(self.project_root, exist_ok=True)
        os.makedirs(self.agents_path, exist_ok=True)
        os.makedirs(self.orchestrator_path, exist_ok=True)
        
        results = {
            "orchestrator": False,
            "main_agents": {},
            "sub_agents": {},
            "base_files": False
        }
        
        # 1. Créer la classe BaseAgent
        self.create_base_agent()
        results["base_files"] = True
        
        # 2. Créer l'orchestrateur (seulement si pas déjà fait ou force)
        if not deployment_status["orchestrator"] or force_redeploy:
            results["orchestrator"] = self.create_orchestrator()
        else:
            results["orchestrator"] = True
            logger.info("⏭️ Orchestrateur déjà déployé")
        
        # 3. Créer les agents principaux
        logger.info("\n👥 Déploiement des agents principaux...")
        for agent_name in self.agent_structure.keys():
            if not deployment_status["main_agents"].get(agent_name, False) or force_redeploy:
                success = self.create_main_agent(agent_name)
                results["main_agents"][agent_name] = success
                
                # Créer les sous-agents
                if success:
                    sub_success = self.create_sub_agents(agent_name)
                    results["sub_agents"][agent_name] = sub_success
            else:
                results["main_agents"][agent_name] = True
                results["sub_agents"][agent_name] = True
                logger.info(f"⏭️ Agent {agent_name} déjà déployé")
        
        # 4. Créer les fichiers d'import
        self.create_init_files()
        
        # 5. Créer le fichier requirements global
        self.create_requirements_file()
        
        # 6. Optionnel: créer docker-compose
        self.create_docker_compose()
        
        # 7. Créer README (CORRIGÉ)
        self.create_readme()
        
        # Résumé
        logger.info("\n" + "="*50)
        logger.info("📊 RÉSUMÉ DU DÉPLOIEMENT")
        logger.info("="*50)
        
        total_main = sum(1 for v in results["main_agents"].values() if v)
        total_sub = sum(1 for v in results["sub_agents"].values() if v)
        
        logger.info(f"Orchestrateur: {'✅' if results['orchestrator'] else '❌'}")
        logger.info(f"Agents principaux: {total_main}/{len(self.agent_structure)}")
        logger.info(f"Groupes de sous-agents: {total_sub}/{len(self.agent_structure)}")
        
        # Calculer le nombre total de sous-agents
        total_sub_agents = sum(len(subs) for subs in self.agent_structure.values())
        logger.info(f"Sous-agents individuels: {total_sub_agents} créés")
        
        logger.info(f"\n📁 Structure créée dans: {self.project_root}")
        logger.info("🎉 Déploiement terminé!")
        
        # Instructions
        logger.info("\n" + "="*50)
        logger.info("📋 PROCHAINES ÉTAPES")
        logger.info("="*50)
        logger.info("1. Installer les dépendances:")
        logger.info("   pip install -r requirements.txt")
        logger.info("\n2. Tester l'orchestrateur:")
        logger.info("   cd orchestrator && python orchestrator.py")
        logger.info("\n3. Démarrer avec Docker (optionnel):")
        logger.info("   docker-compose up -d")
        logger.info("\n4. Vérifier la santé:")
        logger.info("   curl http://localhost:8000/health")
        
        return results


# Point d'entrée principal
async def main():
    """Fonction principale"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Déploiement du SmartContractDevPipeline")
    parser.add_argument("--path", "-p", type=str, default=None,
                       help="Chemin du projet (défaut: ~/Projects/SmartContractPipeline)")
    parser.add_argument("--force", "-f", action="store_true",
                       help="Forcer le redéploiement même si les composants existent")
    parser.add_argument("--verbose", "-v", action="store_true",
                       help="Mode verbeux")
    
    args = parser.parse_args()
    
    # Configurer le logging
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Créer et exécuter le déployeur
    deployer = AgentDeployer(args.path)
    
    try:
        await deployer.deploy_all(force_redeploy=args.force)
    except KeyboardInterrupt:
        logger.info("\n⚠️  Déploiement interrompu par l'utilisateur")
    except Exception as e:
        logger.error(f"❌ Erreur lors du déploiement: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
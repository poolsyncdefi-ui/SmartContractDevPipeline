#!/usr/bin/env python3
"""
Script de génération automatique des classes d'agents manquantes
Version corrigée - bug des f-strings résolu
"""

import os
import sys
from pathlib import Path

# Configuration
ROOT_DIR = Path("D:/Web3Projects\SmartContractDevPipeline")
AGENTS_DIR = ROOT_DIR / "agents"

# Mapping des noms de dossiers vers les noms de classes et descriptions
AGENT_CLASSES = {
    # Agents principaux
    'architect': {
        'class_name': 'ArchitectAgent',
        'description': 'Agent responsable de la conception architecturale complète',
        'version': '3.0.0'
    },
    'coder': {
        'class_name': 'CoderAgent',
        'description': 'Agent responsable du développement complet du code',
        'version': '2.2.0'
    },
    'communication': {
        'class_name': 'CommunicationAgent',
        'description': 'Agent gérant la communication inter-agents',
        'version': '1.0.0'
    },
    'database': {
        'class_name': 'DatabaseAgent',
        'description': 'Agent spécialisé dans la conception de bases de données',
        'version': '1.0.0'
    },
    'documenter': {
        'class_name': 'DocumenterAgent',
        'description': 'Agent de documentation technique',
        'version': '2.2.0'
    },
    'formal_verification': {
        'class_name': 'FormalVerificationAgent',
        'description': 'Agent de vérification formelle des propriétés',
        'version': '1.0.0'
    },
    'frontend_web3': {
        'class_name': 'FrontendWeb3Agent',
        'description': 'Agent de développement frontend Web3',
        'version': '2.2.0'
    },
    'fuzzing_simulation': {
        'class_name': 'FuzzingSimulationAgent',
        'description': 'Agent de tests de sécurité par fuzzing',
        'version': '1.0.0'
    },
    'learning': {
        'class_name': 'LearningAgent',
        'description': 'Agent d\'apprentissage automatique',
        'version': '1.0.0'
    },
    'monitoring': {
        'class_name': 'MonitoringAgent',
        'description': 'Agent de surveillance et monitoring',
        'version': '1.0.0'
    },
    'orchestrator': {
        'class_name': 'OrchestratorAgent',
        'description': 'Agent d\'orchestration des workflows',
        'version': '2.2.0'
    },
    'registry': {
        'class_name': 'RegistryAgent',
        'description': 'Agent de gestion du registre',
        'version': '2.0.0'
    },
    'smart_contract': {
        'class_name': 'SmartContractAgent',
        'description': 'Agent expert en contrats intelligents',
        'version': '2.2.0'
    },
    'storage': {
        'class_name': 'StorageAgent',
        'description': 'Agent de gestion des données',
        'version': '1.0.0'
    },
    'tester': {
        'class_name': 'TesterAgent',
        'description': 'Agent de tests et assurance qualité',
        'version': '2.2.0'
    },
    
    # Sous-agents Architect
    'blockchain_architect': {
        'class_name': 'BlockchainArchitectSubAgent',
        'description': 'Sous-agent spécialisé en architecture blockchain',
        'parent': 'architect',
        'version': '1.0.0'
    },
    'cloud_architect': {
        'class_name': 'CloudArchitectSubAgent',
        'description': 'Sous-agent spécialisé en architecture cloud',
        'parent': 'architect',
        'version': '1.0.0'
    },
    'microservices_architect': {
        'class_name': 'MicroservicesArchitectSubAgent',
        'description': 'Sous-agent spécialisé en microservices',
        'parent': 'architect',
        'version': '1.0.0'
    },
    
    # Sous-agents Coder
    'backend_coder': {
        'class_name': 'BackendCoderSubAgent',
        'description': 'Sous-agent spécialisé en développement backend',
        'parent': 'coder',
        'version': '1.0.0'
    },
    'devops_coder': {
        'class_name': 'DevopsCoderSubAgent',
        'description': 'Sous-agent spécialisé en DevOps',
        'parent': 'coder',
        'version': '1.0.0'
    },
    'frontend_coder': {
        'class_name': 'FrontendCoderSubAgent',
        'description': 'Sous-agent spécialisé en développement frontend',
        'parent': 'coder',
        'version': '1.0.0'
    },
    
    # Sous-agents Frontend Web3
    'react_expert': {
        'class_name': 'ReactExpertSubAgent',
        'description': 'Sous-agent expert en React',
        'parent': 'frontend_web3',
        'version': '1.0.0'
    },
    'ui_ux_expert': {
        'class_name': 'UiUxExpertSubAgent',
        'description': 'Sous-agent expert en UI/UX',
        'parent': 'frontend_web3',
        'version': '1.0.0'
    },
    'web3_integration': {
        'class_name': 'Web3IntegrationSubAgent',
        'description': 'Sous-agent expert en intégration Web3',
        'parent': 'frontend_web3',
        'version': '1.0.0'
    },
    
    # Sous-agents Smart Contract
    'formal_verification': {
        'class_name': 'FormalVerificationSubAgent',
        'description': 'Sous-agent spécialisé en vérification formelle',
        'parent': 'smart_contract',
        'version': '1.0.0'
    },
    'gas_optimizer': {
        'class_name': 'GasOptimizerSubAgent',
        'description': 'Sous-agent spécialisé en optimisation gas',
        'parent': 'smart_contract',
        'version': '1.0.0'
    },
    'security_expert': {
        'class_name': 'SecurityExpertSubAgent',
        'description': 'Sous-agent expert en sécurité',
        'parent': 'smart_contract',
        'version': '1.0.0'
    },
    'solidity_expert': {
        'class_name': 'SolidityExpertSubAgent',
        'description': 'Sous-agent expert en Solidity',
        'parent': 'smart_contract',
        'version': '1.0.0'
    },
    
    # Sous-agents Tester
    'e2e_tester': {
        'class_name': 'E2ETesterSubAgent',
        'description': 'Sous-agent spécialisé en tests E2E',
        'parent': 'tester',
        'version': '1.0.0'
    },
    'fuzzing_expert': {
        'class_name': 'FuzzingExpertSubAgent',
        'description': 'Sous-agent expert en fuzzing',
        'parent': 'tester',
        'version': '1.0.0'
    },
    'integration_tester': {
        'class_name': 'IntegrationTesterSubAgent',
        'description': 'Sous-agent spécialisé en tests d\'intégration',
        'parent': 'tester',
        'version': '1.0.0'
    },
    'unit_tester': {
        'class_name': 'UnitTesterSubAgent',
        'description': 'Sous-agent spécialisé en tests unitaires',
        'parent': 'tester',
        'version': '1.0.0'
    }
}

def get_agent_base_template(class_name, description, version="1.0.0"):
    """Génère le template pour un agent principal."""
    return f'''"""
{description}
Version {version}
"""

import os
import sys
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from agents.base_agent.base_agent import BaseAgent, AgentStatus

logger = logging.getLogger(__name__)

class {class_name}(BaseAgent):
    """
    {description}
    """
    
    def __init__(self, config_path: str = None):
        """
        Initialise l'agent.
        
        Args:
            config_path: Chemin vers le fichier de configuration
        """
        if config_path is None:
            config_path = os.path.join(os.path.dirname(__file__), "config.yaml")
        
        super().__init__(config_path)
        self.logger = logging.getLogger(f"agent.{class_name}")
        self.logger.info(f"Agent {class_name} créé (config: {{config_path}})")
        self.version = "{version}"
    
    async def _initialize_components(self):
        """Initialise les composants spécifiques à l'agent."""
        self.logger.info(f"Initialisation des composants de {class_name}...")
        return True
    
    async def _handle_custom_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """
        Gère les messages personnalisés.
        
        Args:
            message: Message reçu
            
        Returns:
            Réponse au message
        """
        msg_type = message.get("type", "unknown")
        self.logger.info(f"Message reçu: {{msg_type}}")
        return {{"status": "received", "type": msg_type}}
    
    async def execute(self, task_data: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Exécute une tâche.
        
        Args:
            task_data: Données de la tâche
            context: Contexte d'exécution
            
        Returns:
            Résultat de l'exécution
        """
        self.logger.info(f"Exécution de la tâche: {{task_data.get('task_type', 'unknown')}}")
        return {{
            "status": "success",
            "agent": self.name,
            "result": {{"message": "Tâche exécutée avec succès"}},
            "timestamp": datetime.now().isoformat()
        }}
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Vérifie la santé de l'agent.
        
        Returns:
            Rapport de santé
        """
        return {{
            "agent": self.name,
            "status": "healthy",
            "version": self.version,
            "timestamp": datetime.now().isoformat()
        }}
    
    def get_agent_info(self) -> Dict[str, Any]:
        """
        Retourne les informations de l'agent.
        
        Returns:
            Informations de l'agent
        """
        return {{
            "id": self.name,
            "name": "{class_name}",
            "version": self.version,
            "status": self._status.value if hasattr(self._status, 'value') else str(self._status)
        }}
'''

def get_subagent_template(class_name, description, parent, version="1.0.0"):
    """Génère le template pour un sous-agent."""
    return f'''"""
{description}
Sous-agent de {parent}
Version {version}
"""

import os
import sys
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from agents.base_agent.base_agent import BaseAgent, AgentStatus

logger = logging.getLogger(__name__)

class {class_name}(BaseAgent):
    """
    {description}
    """
    
    def __init__(self, config_path: str = None):
        """
        Initialise le sous-agent.
        
        Args:
            config_path: Chemin vers le fichier de configuration
        """
        if config_path is None:
            config_path = os.path.join(os.path.dirname(__file__), "config.yaml")
        
        super().__init__(config_path)
        self.logger = logging.getLogger(f"agent.{class_name}")
        self.logger.info(f"Sous-agent {class_name} créé")
        self.version = "{version}"
        self.parent = "{parent}"
        self.specialization = class_name.replace('SubAgent', '').replace('Agent', '')
    
    async def _initialize_components(self):
        """Initialise les composants spécifiques."""
        self.logger.info(f"Initialisation des composants de {class_name}...")
        return True
    
    async def _handle_custom_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """
        Gère les messages personnalisés.
        
        Args:
            message: Message reçu
            
        Returns:
            Réponse au message
        """
        msg_type = message.get("type", "unknown")
        self.logger.info(f"Message reçu: {{msg_type}}")
        
        result = await self._execute_specialized(message)
        
        return {{
            "status": "success",
            "agent": self.name,
            "specialization": self.specialization,
            "result": result,
            "timestamp": datetime.now().isoformat()
        }}
    
    async def _execute_specialized(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """
        Exécute une tâche spécialisée.
        
        Args:
            message: Message avec les données de la tâche
            
        Returns:
            Résultat de l'exécution
        """
        return {{"message": "Tâche exécutée par le sous-agent spécialisé"}}
    
    async def execute(self, task_data: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Exécute une tâche.
        
        Args:
            task_data: Données de la tâche
            context: Contexte d'exécution
            
        Returns:
            Résultat de l'exécution
        """
        self.logger.info(f"Exécution de la tâche spécialisée: {{task_data.get('task_type', 'unknown')}}")
        return {{
            "status": "success",
            "agent": self.name,
            "specialization": self.specialization,
            "result": {{"message": "Tâche exécutée avec succès"}},
            "timestamp": datetime.now().isoformat()
        }}
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Vérifie la santé du sous-agent.
        
        Returns:
            Rapport de santé
        """
        return {{
            "agent": self.name,
            "status": "healthy",
            "type": "sub_agent",
            "specialization": self.specialization,
            "version": self.version,
            "timestamp": datetime.now().isoformat()
        }}
    
    def get_agent_info(self) -> Dict[str, Any]:
        """
        Retourne les informations du sous-agent.
        
        Returns:
            Informations du sous-agent
        """
        return {{
            "id": self.name,
            "name": "{class_name}",
            "type": "sub_agent",
            "parent": self.parent,
            "specialization": self.specialization,
            "version": self.version,
            "status": self._status.value if hasattr(self._status, 'value') else str(self._status)
        }}
'''

def create_agent_file(agent_dir: Path, agent_info: dict):
    """Crée le fichier agent.py pour un agent donné."""
    agent_path = agent_dir / "agent.py"
    
    # Ne pas écraser si le fichier existe déjà et n'est pas vide
    if agent_path.exists() and agent_path.stat().st_size > 100:
        print(f"  ⏭️  {agent_dir.name} existe déjà - ignoré")
        return
    
    print(f"  ✨ Création de {agent_dir.name}/agent.py")
    
    if 'parent' in agent_info:
        # C'est un sous-agent
        content = get_subagent_template(
            agent_info['class_name'],
            agent_info['description'],
            agent_info['parent'],
            agent_info.get('version', '1.0.0')
        )
    else:
        # C'est un agent principal
        content = get_agent_base_template(
            agent_info['class_name'],
            agent_info['description'],
            agent_info.get('version', '1.0.0')
        )
    
    with open(agent_path, 'w', encoding='utf-8') as f:
        f.write(content)

def main():
    """Parcourt tous les dossiers d'agents et crée les fichiers manquants."""
    print("\n" + "="*70)
    print("🚀 GÉNÉRATION AUTOMATIQUE DES CLASSES D'AGENTS - VERSION CORRIGÉE")
    print("="*70)
    
    if not AGENTS_DIR.exists():
        print(f"❌ Dossier agents introuvable: {AGENTS_DIR}")
        return
    
    print(f"\n📂 Scan du dossier: {AGENTS_DIR}")
    
    created = 0
    skipped = 0
    not_found = 0
    
    # Créer les agents principaux
    for agent_name, agent_info in AGENT_CLASSES.items():
        # Chercher le dossier correspondant
        found = False
        for agent_dir in AGENTS_DIR.iterdir():
            if agent_dir.is_dir() and agent_dir.name == agent_name:
                create_agent_file(agent_dir, agent_info)
                created += 1
                found = True
                break
        
        if not found:
            # Chercher dans les sous-dossiers
            for agent_dir in AGENTS_DIR.rglob(agent_name):
                if agent_dir.is_dir():
                    create_agent_file(agent_dir, agent_info)
                    created += 1
                    found = True
                    break
        
        if not found:
            print(f"  ❌ Dossier {agent_name} non trouvé")
            not_found += 1
    
    print("\n" + "="*70)
    print(f"✅ Fichiers créés: {created}")
    print(f"⏭️  Fichiers ignorés: {skipped}")
    print(f"❌ Dossiers non trouvés: {not_found}")
    print("="*70)

if __name__ == "__main__":
    main()
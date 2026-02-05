#!/usr/bin/env python3
"""
Script de correction automatique des agents
"""
import os
import re

def fix_agent_file(filepath, agent_class_name):
    """Corrige un fichier agent.py"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 1. Corriger les imports
    old_import = """import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from base_agent import BaseAgent"""
    
    new_import = """import os
import sys

# Correction du chemin pour importer base_agent
current_dir = os.path.dirname(os.path.abspath(__file__))
agents_root = os.path.dirname(current_dir)  # Remonte à agents/

# Ajouter agents/ au path si pas déjà présent
if agents_root not in sys.path:
    sys.path.insert(0, agents_root)

from base_agent.agent import BaseAgent"""
    
    if old_import in content:
        content = content.replace(old_import, new_import)
        print(f"  ✅ Imports corrigés dans {os.path.basename(filepath)}")
    
    # 2. Corriger le constructeur pour passer le nom de l'agent
    constructor_pattern = r'def __init__\(self, config_path: str = None\):'
    replacement = f'def __init__(self, config_path: str = None):\n        super().__init__(config_path, "{agent_class_name}")'
    
    if re.search(constructor_pattern, content):
        content = re.sub(constructor_pattern, replacement, content)
        print(f"  ✅ Constructeur corrigé pour {agent_class_name}")
    
    # Sauvegarder
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    
    return content

def main():
    print("🔧 CORRECTION AUTOMATIQUE DES AGENTS")
    print("=" * 50)
    
    # Agents à corriger
    agents = [
        ("agents/architect/agent.py", "ArchitectAgent"),
        ("agents/coder/agent.py", "CoderAgent"),
        ("agents/smart_contract/agent.py", "SmartContractAgent"),
        ("agents/frontend_web3/agent.py", "FrontendWeb3Agent"),
        ("agents/tester/agent.py", "TesterAgent")
    ]
    
    # 1. Créer agents/base_agent/__init__.py
    init_file = "agents/base_agent/__init__.py"
    if not os.path.exists(init_file):
        os.makedirs(os.path.dirname(init_file), exist_ok=True)
        with open(init_file, 'w') as f:
            f.write('from .agent import BaseAgent, AgentUtils\n\n__all__ = ["BaseAgent", "AgentUtils"]')
        print(f"✅ Créé: {init_file}")
    
    # 2. Corriger base_agent/agent.py
    base_agent_file = "agents/base_agent/agent.py"
    if os.path.exists(base_agent_file):
        with open(base_agent_file, 'r') as f:
            content = f.read()
        
        # Corriger l'ordre d'initialisation
        old_init = """def __init__(self, config_path: Optional[str] = None, agent_name: Optional[str] = None):
    self.config = {}
    self.name = agent_name or self.__class__.__name__
    self.agent_type = self._get_agent_type()
    self.logger = logging.getLogger(self.name)"""
        
        new_init = """def __init__(self, config_path: Optional[str] = None, agent_name: Optional[str] = None):
    # D'ABORD déterminer le nom
    if agent_name:
        self.name = agent_name
    else:
        self.name = self.__class__.__name__
    
    # MAINTENANT initialiser le logger
    self.logger = logging.getLogger(self.name)
    
    # Puis le reste
    self.config = {}
    self.agent_type = self._get_agent_type()"""
        
        if old_init in content:
            content = content.replace(old_init, new_init)
            with open(base_agent_file, 'w') as f:
                f.write(content)
            print(f"✅ BaseAgent corrigé")
    
    # 3. Corriger les 5 agents principaux
    for filepath, class_name in agents:
        if os.path.exists(filepath):
            fix_agent_file(filepath, class_name)
        else:
            print(f"⚠️  Fichier non trouvé: {filepath}")
    
    print("\n" + "=" * 50)
    print("✅ CORRECTIONS APPLIQUÉES")
    print("\nProchaines étapes:")
    print("1. Testez avec: python orchestrator/orchestrator.py --test")
    print("2. Si erreur persistante, vérifiez le chemin Python")
    print("3. Exécutez depuis SmartContractDevPipeline/")

if __name__ == "__main__":
    main()
# setup_agents.py
"""
Script de configuration initiale pour les agents
"""

import os
import sys
from pathlib import Path

def create_init_files():
    """Crée les fichiers __init__.py manquants"""
    project_root = Path(__file__).parent
    
    # Structure des agents
    agents_structure = {
        "agents": [
            "base_agent",
            "architect", 
            "coder",
            "tester",
            "smart_contract",
            "registry",
            "formal_verification",
            "fuzzing_simulation",
            "documenter",
            "frontend_web3",
            "communication",
            "storage",
            "monitoring",
            "learning",
            "workflow"
        ]
    }
    
    # Contenu minimal des __init__.py
    init_content = '''"""
{agent_name} Agent Package
"""
'''

    for agent_dir in agents_structure["agents"]:
        agent_path = project_root / "agents" / agent_dir
        init_file = agent_path / "__init__.py"
        
        # Créer le répertoire s'il n'existe pas
        agent_path.mkdir(parents=True, exist_ok=True)
        
        # Créer le __init__.py s'il n'existe pas
        if not init_file.exists():
            content = init_content.format(agent_name=agent_dir.replace('_', ' ').title())
            init_file.write_text(content)
            print(f"✅ Créé: {init_file.relative_to(project_root)}")
    
    # Créer le __init__.py racine des agents
    agents_root = project_root / "agents" / "__init__.py"
    if not agents_root.exists():
        agents_root.write_text('''"""
Agents Package - Tous les agents du système
"""

__version__ = "2.2.0"
''')
        print(f"✅ Créé: {agents_root.relative_to(project_root)}")

def check_structure():
    """Vérifie la structure des agents"""
    project_root = Path(__file__).parent
    required = [
        "agents/base_agent/base_agent.py",
        "agents/base_agent/config.yaml",
        "agents/architect/architect.py", 
        "agents/architect/config.yaml",
        "agents/coder/coder.py",
        "agents/coder/config.yaml"
    ]
    
    print("🔍 Vérification de la structure...")
    
    for path in required:
        full_path = project_root / path
        if full_path.exists():
            print(f"✅ {path}")
        else:
            print(f"❌ {path} - MANQUANT")
    
    # Vérifier les __init__.py
    print("\n🔍 Vérification des packages...")
    for agent_dir in ["base_agent", "architect", "coder"]:
        init_file = project_root / "agents" / agent_dir / "__init__.py"
        if init_file.exists():
            print(f"✅ agents/{agent_dir}/__init__.py")
        else:
            print(f"❌ agents/{agent_dir}/__init__.py - MANQUANT")

def main():
    """Fonction principale"""
    print("🛠️  CONFIGURATION DES AGENTS")
    print("="*40)
    
    create_init_files()
    print()
    check_structure()
    
    print("\n" + "="*40)
    print("📋 PROCHAINES ÉTAPES:")
    print("1. Exécuter: python setup_agents.py")
    print("2. Exécuter: python test_all_agents.py")
    print("3. Vérifier que tous les agents s'initialisent")
    print("="*40)

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
Script pour ajouter AgentStatus dans les imports
"""

import os
import re
from pathlib import Path

ROOT_DIR = Path("D:/Web3Projects/SmartContractDevPipeline")
AGENTS_DIR = ROOT_DIR / "agents"

def fix_agent_file(file_path: Path):
    """Ajoute AgentStatus dans les imports."""
    print(f"\n📝 Traitement de: {file_path.relative_to(ROOT_DIR)}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Remplacer l'import de BaseAgent seul par BaseAgent, AgentStatus
    content = content.replace(
        'from agents.base_agent.base_agent import BaseAgent',
        'from agents.base_agent.base_agent import BaseAgent, AgentStatus'
    )
    
    # Sauvegarder
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("  ✅ AgentStatus ajouté")

def main():
    print("\n" + "="*70)
    print("🔧 CORRECTION DES IMPORTS AGENTSTATUS")
    print("="*70)
    
    # Trouver tous les fichiers agent.py
    agent_files = list(AGENTS_DIR.rglob("agent.py"))
    print(f"📊 {len(agent_files)} fichiers trouvés\n")
    
    for file_path in agent_files:
        fix_agent_file(file_path)
    
    print("\n" + "="*70)
    print("✅ CORRECTION TERMINÉE")
    print("="*70)

if __name__ == "__main__":
    main()
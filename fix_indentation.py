#!/usr/bin/env python3
"""
Script pour corriger précisément l'indentation des fichiers agent.py
"""

import re
from pathlib import Path

SOUS_AGENTS_PATH = Path("agents/communication/sous_agents")

SUB_AGENTS = [
    "circuit_breaker",
    "dead_letter_analyzer",
    "message_router",
    "performance_optimizer",
    "pubsub_manager",
    "queue_manager",
    "security_validator"
]

def fix_indentation(content: str) -> str:
    """Corrige l'indentation dans le contenu du fichier"""
    
    # Pattern pour trouver la section handlers avec la mauvaise indentation
    pattern = r'(handlers = \{.*?\n)(.*?)(?=\n        \})'
    
    def replacer(match):
        start = match.group(1)
        middle = match.group(2)
        
        # Remplacer l'indentation incorrecte
        lines = middle.split('\n')
        corrected_lines = []
        for line in lines:
            if line.strip():
                # Compter les espaces actuels
                current_indent = len(line) - len(line.lstrip())
                # Si l'indentation est de 4, la passer à 8
                if current_indent == 4:
                    line = '        ' + line.lstrip()
                corrected_lines.append(line)
        
        return start + '\n'.join(corrected_lines)
    
    # Appliquer la correction
    content = re.sub(pattern, replacer, content, flags=re.DOTALL)
    
    return content

def fix_file(file_path: Path) -> bool:
    """Corrige un fichier"""
    print(f"\n🔧 Correction de {file_path}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Sauvegarder l'original
    backup = file_path.with_suffix('.py.bak2')
    with open(backup, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"  ✅ Backup créé: {backup}")
    
    # Corriger l'indentation
    new_content = fix_indentation(content)
    
    if new_content != content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"  ✅ Indentation corrigée")
        return True
    else:
        print(f"  ℹ️ Aucune modification nécessaire")
        return False

def main():
    print("=" * 60)
    print("🔧 CORRECTION PRÉCISE DE L'INDENTATION")
    print("=" * 60)
    
    fixed_count = 0
    
    for agent_id in SUB_AGENTS:
        agent_file = SOUS_AGENTS_PATH / agent_id / "agent.py"
        if agent_file.exists():
            if fix_file(agent_file):
                fixed_count += 1
    
    print("\n" + "=" * 60)
    print(f"✅ Correction terminée: {fixed_count} fichiers corrigés")
    print("=" * 60)
    print("\n📋 Prochaines étapes:")
    print("   1. Relancez python diagnose_communication.py")
    print("   2. Les sous-agents devraient maintenant s'importer")

if __name__ == "__main__":
    main()
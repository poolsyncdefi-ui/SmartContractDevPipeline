# fix_subagents_annotations.py
"""
Script pour corriger les annotations de type dans les sous-agents communication
"""

import re
from pathlib import Path

# Chemin vers les sous-agents
subagents_path = Path("agents/communication/sous_agents")

# Parcourir tous les sous-agents
for agent_dir in subagents_path.iterdir():
    if agent_dir.is_dir():
        agent_file = agent_dir / "agent.py"
        if agent_file.exists():
            print(f"🔧 Correction de {agent_file}")
            
            # Lire le contenu
            with open(agent_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Remplacer les annotations problématiques
            # Version originale avec l'erreur
            original = "self._task_metrics: Dict[str, Dict] = {}"
            # Version corrigée
            corrected = "self._task_metrics = {}"
            
            if original in content:
                content = content.replace(original, corrected)
                print(f"  ✅ Annotation corrigée dans {agent_file}")
                
                # Écrire le fichier corrigé
                with open(agent_file, 'w', encoding='utf-8') as f:
                    f.write(content)
            else:
                print(f"  ℹ️ Annotation non trouvée dans {agent_file}")

print("\n✅ Corrections terminées !")
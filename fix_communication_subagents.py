#!/usr/bin/env python3
"""
Script de correction des sous-agents communication
Corrige les erreurs d'annotation de type et autres problèmes
"""

import re
from pathlib import Path

# Configuration
SOUS_AGENTS_PATH = Path("agents/communication/sous_agents")

# Liste des sous-agents à corriger
SUB_AGENTS = [
    "queue_manager",
    "pubsub_manager", 
    "circuit_breaker",
    "message_router",
    "dead_letter_analyzer",
    "performance_optimizer",
    "security_validator"
]

def fix_agent_file(agent_file: Path) -> bool:
    """Corrige les erreurs dans un fichier agent.py"""
    print(f"\n🔧 Analyse de {agent_file}")
    
    with open(agent_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    modified = False
    
    # 1. Corriger l'annotation de type problématique
    # Remplacer "self._task_metrics: Dict[str, Dict] = {}" par "self._task_metrics = {}"
    pattern1 = r'self\._task_metrics: Dict\[str, Dict\] = \{\}'
    replacement1 = 'self._task_metrics = {}'
    
    if re.search(pattern1, content):
        content = re.sub(pattern1, replacement1, content)
        print(f"  ✅ Annotation de type corrigée")
        modified = True
    
    # 2. Vérifier que le logger est correctement défini
    if "logger = logging.getLogger(__name__)" not in content:
        print(f"  ⚠️ Logger manquant - à vérifier")
    
    # 3. Vérifier que la méthode __init__ a bien les doubles accolades
    # (c'est déjà bon normalement)
    
    if modified:
        # Sauvegarder le fichier corrigé
        with open(agent_file, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"  ✅ Fichier mis à jour")
        return True
    else:
        print(f"  ℹ️ Aucune correction nécessaire")
        return False

def main():
    print("=" * 60)
    print("🔧 CORRECTION DES SOUS-AGENTS COMMUNICATION")
    print("=" * 60)
    
    if not SOUS_AGENTS_PATH.exists():
        print(f"❌ Dossier {SOUS_AGENTS_PATH} introuvable")
        return
    
    fixed_count = 0
    error_count = 0
    
    for agent_id in SUB_AGENTS:
        agent_dir = SOUS_AGENTS_PATH / agent_id
        agent_file = agent_dir / "agent.py"
        
        if not agent_file.exists():
            print(f"\n⚠️ Fichier non trouvé: {agent_file}")
            error_count += 1
            continue
        
        try:
            if fix_agent_file(agent_file):
                fixed_count += 1
        except Exception as e:
            print(f"❌ Erreur lors de la correction de {agent_id}: {e}")
            error_count += 1
    
    print("\n" + "=" * 60)
    print(f"✅ CORRECTION TERMINÉE")
    print(f"   • Fichiers corrigés: {fixed_count}")
    print(f"   • Erreurs: {error_count}")
    print("=" * 60)

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
Script de correction automatique des fichiers agent.py
Version 4.0 - Approche simplifiée
"""

import os
import re
import shutil
import logging
from pathlib import Path
from datetime import datetime

# Configuration
ROOT_DIR = Path("D:/Web3Projects/SmartContractDevPipeline")
AGENTS_DIR = ROOT_DIR / "agents"

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger("fix_agent")

def backup_file(file_path: Path) -> bool:
    """Crée une sauvegarde."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = file_path.with_suffix(f'.py.{timestamp}.bak')
    shutil.copy2(file_path, backup_path)
    logger.info(f"  ✅ Backup créé: {backup_path.name}")
    return True

def fix_agent_file(file_path: Path) -> bool:
    """Corrige un fichier agent.py de façon simple."""
    logger.info(f"\n📝 Traitement de: {file_path.relative_to(ROOT_DIR)}")
    
    # Lire le contenu
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Créer une sauvegarde
    backup_file(file_path)
    
    # 1. CORRECTION DES IMPORTS
    # Remplacer les imports relatifs/incorrects
    content = re.sub(
        r'from\s+\.\.?base_agent\s+import\s+BaseAgent',
        'from agents.base_agent.base_agent import BaseAgent',
        content
    )
    content = re.sub(
        r'from\s+base_agent\s+import\s+BaseAgent',
        'from agents.base_agent.base_agent import BaseAgent',
        content
    )
    content = re.sub(
        r'from\s+\.base_agent\s+import\s+BaseAgent',
        'from agents.base_agent.base_agent import BaseAgent',
        content
    )
    
    # Ajouter AgentStatus si nécessaire
    if 'AgentStatus' not in content and 'BaseAgent' in content:
        content = content.replace(
            'from agents.base_agent.base_agent import BaseAgent',
            'from agents.base_agent.base_agent import BaseAgent, AgentStatus'
        )
    
    # 2. AJOUTER LES IMPORTS MANQUANTS
    imports_to_add = []
    if 'import os' not in content:
        imports_to_add.append('import os')
    if 'import sys' not in content:
        imports_to_add.append('import sys')
    if 'import logging' not in content:
        imports_to_add.append('import logging')
    if 'from typing import' not in content:
        imports_to_add.append('from typing import Dict, Any, List, Optional')
    if 'from datetime import datetime' not in content:
        imports_to_add.append('from datetime import datetime')
    
    if imports_to_add:
        # Ajouter après les imports existants
        import_section = '\n'.join(imports_to_add) + '\n\n'
        content = import_section + content
    
    # 3. CORRECTION DE L'HÉRITAGE
    # Vérifier si la classe hérite de BaseAgent
    class_match = re.search(r'class\s+(\w+)\s*(?:\(.*?\))?\s*:', content)
    if class_match:
        class_name = class_match.group(1)
        if 'BaseAgent' not in class_match.group(0):
            # Ajouter l'héritage
            content = content.replace(
                f'class {class_name}:',
                f'class {class_name}(BaseAgent):'
            )
    
    # 4. AJOUTER LES MÉTHODES REQUISES SI ELLES MANQUENT
    if 'async def _initialize_components' not in content:
        # Ajouter après la classe
        methods = '''
    async def _initialize_components(self):
        """Initialise les composants spécifiques."""
        self.logger.info(f"Initialisation des composants de {class_name}...")
        return True
'''
        # Insérer après le __init__
        if '__init__' in content:
            content = content.replace('__init__', '__init__' + methods)
    
    if 'async def _handle_custom_message' not in content:
        method = '''
    async def _handle_custom_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Gère les messages personnalisés."""
        msg_type = message.get("type", "unknown")
        self.logger.info(f"Message reçu: {msg_type}")
        return {"status": "received", "type": msg_type}
'''
        content += method
    
    if 'async def health_check' not in content:
        method = '''
    async def health_check(self) -> Dict[str, Any]:
        """Vérifie la santé de l'agent."""
        return {
            "agent": self.name,
            "status": "healthy",
            "timestamp": datetime.now().isoformat()
        }
'''
        content += method
    
    if 'def get_agent_info' not in content:
        method = '''
    def get_agent_info(self) -> Dict[str, Any]:
        """Retourne les informations de l'agent."""
        return {
            "id": self.name,
            "name": "{class_name}",
            "version": getattr(self, 'version', '1.0.0'),
            "status": self._status.value if hasattr(self._status, 'value') else str(self._status)
        }
'''.format(class_name=class_name)
        content += method
    
    # 5. AJOUTER LE LOGGER SI NÉCESSAIRE
    if 'logger = logging.getLogger' not in content:
        content = content.replace(
            'import logging',
            'import logging\n\nlogger = logging.getLogger(__name__)'
        )
    
    # Sauvegarder
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    logger.info(f"  ✅ Fichier corrigé avec succès")
    return True

def main():
    print("\n" + "="*70)
    print("🔧 SCRIPT DE CORRECTION SIMPLIFIÉ - VERSION 4.0")
    print("="*70)
    
    if not AGENTS_DIR.exists():
        logger.error(f"❌ Dossier agents introuvable: {AGENTS_DIR}")
        return
    
    # Trouver tous les fichiers agent.py (sauf base_agent)
    agent_files = []
    for file_path in AGENTS_DIR.rglob("agent.py"):
        if "base_agent" not in str(file_path):
            agent_files.append(file_path)
    
    logger.info(f"📊 {len(agent_files)} fichiers agent.py à traiter\n")
    
    success = 0
    failed = 0
    
    for file_path in agent_files:
        try:
            if fix_agent_file(file_path):
                success += 1
        except Exception as e:
            logger.error(f"❌ Erreur sur {file_path.name}: {e}")
            failed += 1
    
    print("\n" + "="*70)
    print(f"✅ Fichiers corrigés: {success}")
    print(f"❌ Fichiers en échec: {failed}")
    print("="*70)

if __name__ == "__main__":
    main()
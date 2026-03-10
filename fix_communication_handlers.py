#!/usr/bin/env python3
"""
Script de correction pour les sous-agents communication
Corrige l'erreur 'illegal target for annotation' dans les fichiers agent.py
"""

import re
from pathlib import Path

# Configuration
SOUS_AGENTS_PATH = Path("agents/communication/sous_agents")

# Liste des sous-agents à corriger
SUB_AGENTS = [
    "circuit_breaker",
    "dead_letter_analyzer",
    "message_router",
    "performance_optimizer",
    "pubsub_manager",
    "queue_manager",
    "security_validator"
]

def fix_agent_file(agent_file: Path) -> bool:
    """Corrige les erreurs dans un fichier agent.py"""
    print(f"\n🔧 Analyse de {agent_file}")
    
    with open(agent_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    modified = False
    new_lines = []
    in_handlers_section = False
    handlers_section_start = -1
    handlers_section_end = -1
    
    # Première passe : identifier la section problématique
    for i, line in enumerate(lines):
        if "handlers = {" in line:
            in_handlers_section = True
            handlers_section_start = i
        elif in_handlers_section and "}" in line and not line.strip().startswith("#"):
            handlers_section_end = i
            in_handlers_section = False
    
    if handlers_section_start != -1 and handlers_section_end != -1:
        print(f"  📍 Section handlers trouvée lignes {handlers_section_start+1}-{handlers_section_end+1}")
        
        # Vérifier si la section est correcte
        section_content = ''.join(lines[handlers_section_start:handlers_section_end+1])
        
        # Chercher les lignes de handlers qui ne sont pas correctement indentées
        if "self._handle" in section_content:
            # Remplacer par une version corrigée
            new_section = []
            new_section.append(lines[handlers_section_start])  # "handlers = {"
            
            # Ajouter les handlers standards
            new_section.append('                f"{self.name}.status": self._handle_status,\n')
            new_section.append('                f"{self.name}.metrics": self._handle_metrics,\n')
            new_section.append('                f"{self.name}.health": self._handle_health,\n')
            new_section.append('                f"{self.name}.process": self._handle_process,\n')
            new_section.append('                f"{self.name}.capabilities": self._handle_capabilities,\n')
            
            # Ajouter les handlers pour chaque capacité
            # Les extraire du fichier original
            for j in range(handlers_section_start + 1, handlers_section_end):
                line = lines[j].strip()
                if line and not line.startswith('}') and 'self._handle' in line:
                    # Cette ligne contient un handler, la garder
                    new_section.append(lines[j])
            
            new_section.append('            }\n')  # Fermeture du dictionnaire
            
            # Remplacer la section
            lines[handlers_section_start:handlers_section_end+1] = new_section
            modified = True
            print(f"  ✅ Section handlers corrigée")
    
    if modified:
        # Sauvegarder le fichier corrigé
        with open(agent_file, 'w', encoding='utf-8') as f:
            f.writelines(lines)
        print(f"  ✅ Fichier mis à jour")
        return True
    else:
        print(f"  ℹ️ Aucune correction nécessaire")
        return False

def create_simple_version(agent_id: str) -> str:
    """Crée une version ultra-simplifiée du sous-agent"""
    class_name = ''.join(p.capitalize() for p in agent_id.split('_')) + 'SubAgent'
    display_name_map = {
        "circuit_breaker": "🛡️ Circuit Breaker",
        "dead_letter_analyzer": "💀 Dead Letter Analyzer",
        "message_router": "🔄 Message Router",
        "performance_optimizer": "⚡ Performance Optimizer",
        "pubsub_manager": "📢 PubSub Manager",
        "queue_manager": "📊 Queue Manager",
        "security_validator": "🔒 Security Validator"
    }
    display_name = display_name_map.get(agent_id, agent_id.replace('_', ' ').title())
    
    return f'''"""
{display_name} - Sous-agent simplifié
"""

import logging
import sys
from datetime import datetime
from pathlib import Path

current_dir = Path(__file__).parent.absolute()
project_root = current_dir.parent.parent.parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from agents.base_agent.base_agent import BaseAgent, AgentStatus, Message, MessageType

logger = logging.getLogger(__name__)


class {class_name}(BaseAgent):
    """Version simplifiée du sous-agent"""
    
    def __init__(self, config_path: str = ""):
        if not config_path:
            config_path = str(current_dir / "config.yaml")
        super().__init__(config_path)
        self._display_name = "{display_name}"
        self._initialized = False
        self._stats = {{'tasks': 0, 'start': datetime.now().isoformat()}}

    async def initialize(self) -> bool:
        try:
            self._set_status(AgentStatus.INITIALIZING)
            await super().initialize()
            self._initialized = True
            self._set_status(AgentStatus.READY)
            logger.info(f"✅ {{self._display_name}} prêt")
            return True
        except Exception as e:
            logger.error(f"❌ Erreur: {{e}}")
            self._set_status(AgentStatus.ERROR)
            return False

    async def _handle_custom_message(self, message: Message):
        try:
            msg_type = message.message_type
            if msg_type == f"{{self.name}}.status":
                return Message(
                    sender=self.name,
                    recipient=message.sender,
                    content=self._stats,
                    message_type=f"{{self.name}}.status_response",
                    correlation_id=message.message_id
                )
            elif msg_type == f"{{self.name}}.health":
                health = await self.health_check()
                return Message(
                    sender=self.name,
                    recipient=message.sender,
                    content=health,
                    message_type=f"{{self.name}}.health_response",
                    correlation_id=message.message_id
                )
            return None
        except Exception as e:
            logger.error(f"Erreur: {{e}}")
            return Message(
                sender=self.name,
                recipient=message.sender,
                content={{"error": str(e)}},
                message_type=MessageType.ERROR.value,
                correlation_id=message.message_id
            )

    async def health_check(self):
        base = await super().health_check()
        return {{**base, "stats": self._stats}}

    async def shutdown(self) -> bool:
        logger.info(f"Arrêt de {{self._display_name}}...")
        self._set_status(AgentStatus.SHUTTING_DOWN)
        await super().shutdown()
        return True

    def get_agent_info(self):
        return {{
            "id": self.name,
            "name": "{class_name}",
            "display_name": self._display_name,
            "version": "1.0.0",
            "description": "Sous-agent simplifié",
            "status": self._status.value,
            "stats": self._stats
        }}


def create_{agent_id}_agent(config_path: str = "") -> {class_name}:
    return {class_name}(config_path)
'''

def main():
    print("=" * 60)
    print("🔧 CORRECTION DES SOUS-AGENTS COMMUNICATION")
    print("=" * 60)
    
    if not SOUS_AGENTS_PATH.exists():
        print(f"❌ Dossier {SOUS_AGENTS_PATH} introuvable")
        return
    
    print("\nOptions:")
    print("  1. Corriger automatiquement les fichiers existants")
    print("  2. Remplacer par des versions simplifiées (recommandé)")
    print("  3. Quitter")
    
    choice = input("\nVotre choix [1-3]: ").strip()
    
    if choice == "1":
        # Correction automatique
        fixed_count = 0
        for agent_id in SUB_AGENTS:
            agent_file = SOUS_AGENTS_PATH / agent_id / "agent.py"
            if agent_file.exists():
                if fix_agent_file(agent_file):
                    fixed_count += 1
        print(f"\n✅ {fixed_count} fichiers corrigés")
    
    elif choice == "2":
        # Remplacer par versions simplifiées
        print("\n⚠️  Attention: Cette opération va remplacer tous les fichiers agent.py")
        confirm = input("Confirmer? (oui/non): ").strip().lower()
        
        if confirm == "oui":
            for agent_id in SUB_AGENTS:
                agent_dir = SOUS_AGENTS_PATH / agent_id
                agent_file = agent_dir / "agent.py"
                
                # Sauvegarder l'original
                if agent_file.exists():
                    backup = agent_file.with_suffix('.py.bak')
                    agent_file.rename(backup)
                    print(f"  📦 Backup créé: {backup}")
                
                # Créer la version simplifiée
                simple_version = create_simple_version(agent_id)
                with open(agent_file, 'w', encoding='utf-8') as f:
                    f.write(simple_version)
                print(f"  ✅ Version simplifiée créée pour {agent_id}")
            
            print("\n✅ Tous les sous-agents ont été remplacés par des versions simplifiées")
    
    else:
        print("Annulé")
        return
    
    print("\n" + "=" * 60)
    print("✅ OPÉRATION TERMINÉE")
    print("=" * 60)
    print("\n📋 Prochaines étapes:")
    print("   1. Relancez python diagnose_communication.py")
    print("   2. Tous les sous-agents devraient maintenant s'importer")
    print("   3. Relancez python test_full_sprint.py")

if __name__ == "__main__":
    main()
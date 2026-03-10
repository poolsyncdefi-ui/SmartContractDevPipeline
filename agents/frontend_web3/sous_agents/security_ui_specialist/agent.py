"""
🛡️ Spécialiste Sécurité UI Avancée - Sous-agent spécialisé
Version: 2.0.0

Expert en sécurité des interfaces Web3
"""

import logging
import sys
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

# Configuration des imports
current_dir = Path(__file__).parent.absolute()
project_root = current_dir.parent.parent.parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from agents.base_agent.base_agent import BaseAgent, AgentStatus, Message, MessageType

logger = logging.getLogger(__name__)


class SecurityUiSpecialistSubAgent(BaseAgent):
    """
    Expert en sécurité des interfaces Web3
    """
    
    def __init__(self, config_path: str = ""):
        """Initialise le sous-agent"""
        if not config_path:
            config_path = str(current_dir / "config.yaml")

        super().__init__(config_path)

        self._display_name = "🛡️ Spécialiste Sécurité UI Avancée"
        self._initialized = False
        self._components = {}
        
        # Statistiques
        self._stats = {
            'tasks_processed': 0,
            'components_generated': 0,
            'start_time': datetime.now().isoformat()
        }

        logger.info(f"{self._display_name} créé - v{self._version}")

    async def initialize(self) -> bool:
        """Initialise le sous-agent"""
        try:
            self._set_status(AgentStatus.INITIALIZING)
            logger.info(f"Initialisation de {self._display_name}...")

            base_result = await super().initialize()
            if not base_result:
                return False

            await self._initialize_components()

            self._initialized = True
            self._set_status(AgentStatus.READY)
            logger.info(f"✅ {self._display_name} prêt")
            return True

        except Exception as e:
            logger.error(f"❌ Erreur initialisation: {e}")
            self._set_status(AgentStatus.ERROR)
            return False

    async def _initialize_components(self) -> bool:
        """Initialise les composants du sous-agent"""
        logger.info("Initialisation des composants...")
        
        self._components = {
            "capabilities": [
        "transaction_security",
        "phishing_protection",
        "wallet_security",
        "smart_contract_verification",
        "approval_management",
            ],
            "enabled": True,
            "version": "2.0.0"
        }
        
        logger.info(f"✅ Composants: {list(self._components.keys())}")
        return True

    async def _handle_custom_message(self, message: Message) -> Optional[Message]:
        """Gère les messages personnalisés"""
        try:
            msg_type = message.message_type
            logger.debug(f"Message reçu: {msg_type} de {message.sender}")

            handlers = {
                f"{self.name}.status": self._handle_status,
                f"{self.name}.metrics": self._handle_metrics,
                f"{self.name}.health": self._handle_health,
            }

            if msg_type in handlers:
                return await handlers[msg_type](message)

            return None

        except Exception as e:
            logger.error(f"Erreur traitement message: {e}")
            return Message(
                sender=self.name,
                recipient=message.sender,
                content={"error": str(e)},
                message_type=MessageType.ERROR.value,
                correlation_id=message.message_id
            )

    async def _handle_status(self, message: Message) -> Message:
        """Retourne le statut général"""
        return Message(
            sender=self.name,
            recipient=message.sender,
            content={
                'status': self._status.value,
                'initialized': self._initialized,
                'stats': self._stats
            },
            message_type=f"{self.name}.status_response",
            correlation_id=message.message_id
        )

    async def _handle_metrics(self, message: Message) -> Message:
        """Retourne les métriques"""
        return Message(
            sender=self.name,
            recipient=message.sender,
            content=self._stats,
            message_type=f"{self.name}.metrics_response",
            correlation_id=message.message_id
        )

    async def _handle_health(self, message: Message) -> Message:
        """Retourne l'état de santé"""
        health = await self.health_check()
        return Message(
            sender=self.name,
            recipient=message.sender,
            content=health,
            message_type=f"{self.name}.health_response",
            correlation_id=message.message_id
        )

    async def shutdown(self) -> bool:
        """Arrête le sous-agent"""
        logger.info(f"Arrêt de {self._display_name}...")
        self._set_status(AgentStatus.SHUTTING_DOWN)
        await super().shutdown()
        logger.info(f"✅ {self._display_name} arrêté")
        return True

    async def pause(self) -> bool:
        """Met en pause le sous-agent"""
        logger.info(f"Pause de {self._display_name}...")
        self._set_status(AgentStatus.PAUSED)
        return True

    async def resume(self) -> bool:
        """Reprend l'activité"""
        logger.info(f"Reprise de {self._display_name}...")
        self._set_status(AgentStatus.READY)
        return True

    async def health_check(self) -> Dict[str, Any]:
        """Vérifie la santé du sous-agent"""
        base_health = await super().health_check()

        uptime = None
        if self._stats.get('start_time'):
            start = datetime.fromisoformat(self._stats['start_time'])
            uptime = str(datetime.now() - start)

        return {
            **base_health,
            "agent": self.name,
            "display_name": self._display_name,
            "status": self._status.value,
            "ready": self._status == AgentStatus.READY,
            "initialized": self._initialized,
            "uptime": uptime,
            "components": list(self._components.keys()),
            "stats": self._stats,
            "timestamp": datetime.now().isoformat()
        }

    def get_agent_info(self) -> Dict[str, Any]:
        """Informations pour le registre"""
        return {
            "id": self.name,
            "name": "SecurityUiSpecialistSubAgent",
            "display_name": self._display_name,
            "version": "2.0.0",
            "description": """Expert en sécurité des interfaces Web3""",
            "status": self._status.value,
            "capabilities": [
        "transaction_security",
        "phishing_protection",
        "wallet_security",
        "smart_contract_verification",
        "approval_management",
            ],
            "stats": self._stats
        }


def create_security_ui_specialist_agent(config_path: str = "") -> SecurityUiSpecialistSubAgent:
    """Crée une instance du sous-agent"""
    return SecurityUiSpecialistSubAgent(config_path)

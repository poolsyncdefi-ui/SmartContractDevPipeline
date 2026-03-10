#!/usr/bin/env python3
"""
Script de création avancée de l'arborescence des sous-agents pour frontend_web3
Crée des sous-agents riches en fonctionnalités avec configuration complète
Version FINALE - Sans référence à 'self' dans les templates
"""

import os
import sys
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional

# Configuration
PROJECT_ROOT = Path(__file__).parent if __file__ else Path.cwd()
AGENT_PATH = PROJECT_ROOT / "agents" / "frontend_web3"
SOUS_AGENTS_PATH = AGENT_PATH / "sous_agents"

# ============================================================================
# SOUS-AGENT 1: REACT EXPERT
# ============================================================================
REACT_EXPERT = {
    "id": "react_expert",
    "display_name": "⚛️ Expert React/Next.js Avancé",
    "description": "Expert en développement React 18+, Next.js 14+, hooks personnalisés, patterns avancés et optimisation de composants",
    "version": "2.0.0",
    "capabilities": [
        {
            "name": "react_component_generation_advanced",
            "description": "Génération de composants React avec patterns avancés",
            "confidence": 0.95
        },
        {
            "name": "nextjs_app_router_master",
            "description": "Maîtrise du App Router Next.js 14+",
            "confidence": 0.98
        },
        {
            "name": "react_hook_generator_advanced",
            "description": "Génération de hooks personnalisés complexes",
            "confidence": 0.95
        },
        {
            "name": "performance_optimization_react",
            "description": "Optimisation des performances React",
            "confidence": 0.9
        },
        {
            "name": "state_management_master",
            "description": "Maîtrise des solutions de state management",
            "confidence": 0.92
        }
    ],
    "technologies": {
        "frameworks": ["Next.js 14+", "React 18+", "Vite"],
        "state_management": ["Zustand", "Redux Toolkit", "Jotai"]
    },
    "outputs": [
        {"name": "react_component_library", "type": "code", "format": "typescript"},
        {"name": "nextjs_application", "type": "code", "format": "typescript"}
    ]
}

# ============================================================================
# SOUS-AGENT 2: WEB3 INTEGRATION EXPERT
# ============================================================================
WEB3_INTEGRATION = {
    "id": "web3_integration",
    "display_name": "🔗 Expert Intégration Web3 Avancé",
    "description": "Expert en intégration blockchain avec wagmi, viem, ethers.js, support multi-chaînes",
    "version": "2.0.0",
    "capabilities": [
        {
            "name": "wallet_connection_advanced",
            "description": "Connexion wallet multi-chaînes",
            "confidence": 0.98
        },
        {
            "name": "contract_interaction_master",
            "description": "Interaction avancée avec smart contracts",
            "confidence": 0.96
        },
        {
            "name": "transaction_management",
            "description": "Gestion complète des transactions",
            "confidence": 0.95
        },
        {
            "name": "multi_chain_support",
            "description": "Support de multiples blockchains",
            "confidence": 0.94
        },
        {
            "name": "abi_management",
            "description": "Gestion avancée des ABI",
            "confidence": 0.92
        }
    ],
    "technologies": {
        "libraries": ["wagmi", "viem", "ethers.js v6"],
        "wallets": ["RainbowKit", "WalletConnect v2", "Web3Modal"],
        "chains": ["Ethereum", "Polygon", "Arbitrum", "Optimism"]
    },
    "outputs": [
        {"name": "wallet_connection_system", "type": "code", "format": "typescript"},
        {"name": "contract_interaction_hooks", "type": "code", "format": "typescript"}
    ]
}

# ============================================================================
# SOUS-AGENT 3: UI/UX EXPERT
# ============================================================================
UI_UX_EXPERT = {
    "id": "ui_ux_expert",
    "display_name": "🎨 Expert UI/UX Design Système",
    "description": "Expert en design system, composants accessibles, animations fluides",
    "version": "2.0.0",
    "capabilities": [
        {
            "name": "design_system_creation",
            "description": "Création de design systems complets",
            "confidence": 0.96
        },
        {
            "name": "responsive_design_advanced",
            "description": "Design responsive avancé",
            "confidence": 0.98
        },
        {
            "name": "animation_orchestration",
            "description": "Orchestration d'animations complexes",
            "confidence": 0.9
        },
        {
            "name": "accessibility_compliance",
            "description": "Conformité WCAG 2.1 AA/AAA",
            "confidence": 0.95
        },
        {
            "name": "dark_mode_system",
            "description": "Système complet de dark/light mode",
            "confidence": 0.94
        }
    ],
    "technologies": {
        "frameworks": ["Tailwind CSS", "Chakra UI", "Radix UI"],
        "animations": ["Framer Motion", "GSAP", "React Spring"],
        "charts": ["Recharts", "D3.js"]
    },
    "outputs": [
        {"name": "design_system", "type": "code", "format": "typescript"},
        {"name": "accessible_component_library", "type": "code", "format": "typescript"}
    ]
}

# ============================================================================
# SOUS-AGENT 4: DEFI UI SPECIALIST
# ============================================================================
DEFI_UI_SPECIALIST = {
    "id": "defi_ui_specialist",
    "display_name": "📊 Spécialiste Interfaces DeFi Avancées",
    "description": "Spécialiste des interfaces DeFi complexes (swap, lending, staking)",
    "version": "2.0.0",
    "capabilities": [
        {
            "name": "swap_interface_advanced",
            "description": "Interface DEX avancée",
            "confidence": 0.97
        },
        {
            "name": "lending_interface_complete",
            "description": "Interface lending/borrowing complète",
            "confidence": 0.96
        },
        {
            "name": "staking_interface_advanced",
            "description": "Interface staking avancée",
            "confidence": 0.95
        },
        {
            "name": "vault_interface",
            "description": "Interface vaults/yield optimizers",
            "confidence": 0.93
        },
        {
            "name": "defi_dashboard_comprehensive",
            "description": "Dashboard DeFi complet",
            "confidence": 0.95
        }
    ],
    "protocols": ["Uniswap V3", "Aave V3", "Compound V3"],
    "outputs": [
        {"name": "dex_interface", "type": "code", "format": "typescript"},
        {"name": "lending_dashboard", "type": "code", "format": "typescript"}
    ]
}

# ============================================================================
# SOUS-AGENT 5: NFT UI SPECIALIST
# ============================================================================
NFT_UI_SPECIALIST = {
    "id": "nft_ui_specialist",
    "display_name": "🖼️ Spécialiste Interfaces NFT Premium",
    "description": "Spécialiste des interfaces NFT (mint, gallery, marketplace)",
    "version": "2.0.0",
    "capabilities": [
        {
            "name": "mint_page_advanced",
            "description": "Page de mint NFT avancée",
            "confidence": 0.98
        },
        {
            "name": "nft_gallery_pro",
            "description": "Galerie NFT professionnelle",
            "confidence": 0.97
        },
        {
            "name": "marketplace_interface",
            "description": "Interface marketplace complète",
            "confidence": 0.96
        },
        {
            "name": "nft_detail_view",
            "description": "Vue détaillée NFT",
            "confidence": 0.95
        },
        {
            "name": "nft_auction_house",
            "description": "Système d'enchères NFT",
            "confidence": 0.92
        }
    ],
    "standards": ["ERC721", "ERC1155", "ERC2981"],
    "outputs": [
        {"name": "nft_mint_page", "type": "code", "format": "typescript"},
        {"name": "nft_marketplace", "type": "code", "format": "typescript"}
    ]
}

# ============================================================================
# SOUS-AGENT 6: PERFORMANCE OPTIMIZER
# ============================================================================
PERFORMANCE_OPTIMIZER = {
    "id": "performance_optimizer",
    "display_name": "⚡ Optimisateur Performance Web3",
    "description": "Expert en optimisation des performances Web3",
    "version": "2.0.0",
    "capabilities": [
        {
            "name": "bundle_optimization",
            "description": "Optimisation de la taille du bundle",
            "confidence": 0.95
        },
        {
            "name": "core_web_vitals",
            "description": "Optimisation Core Web Vitals",
            "confidence": 0.96
        },
        {
            "name": "caching_strategy",
            "description": "Stratégies de caching avancées",
            "confidence": 0.94
        },
        {
            "name": "image_optimization",
            "description": "Optimisation des images",
            "confidence": 0.93
        },
        {
            "name": "web3_performance",
            "description": "Optimisation des appels Web3",
            "confidence": 0.92
        }
    ],
    "metrics": ["LCP < 2.5s", "FID < 100ms", "CLS < 0.1"],
    "outputs": [
        {"name": "performance_report", "type": "report", "format": "json"},
        {"name": "optimization_config", "type": "config", "format": "json"}
    ]
}

# ============================================================================
# SOUS-AGENT 7: SECURITY UI SPECIALIST
# ============================================================================
SECURITY_UI_SPECIALIST = {
    "id": "security_ui_specialist",
    "display_name": "🛡️ Spécialiste Sécurité UI Avancée",
    "description": "Expert en sécurité des interfaces Web3",
    "version": "2.0.0",
    "capabilities": [
        {
            "name": "transaction_security",
            "description": "Validation de transactions",
            "confidence": 0.98
        },
        {
            "name": "phishing_protection",
            "description": "Protection anti-phishing",
            "confidence": 0.97
        },
        {
            "name": "wallet_security",
            "description": "Sécurité wallet",
            "confidence": 0.96
        },
        {
            "name": "smart_contract_verification",
            "description": "Vérification des smart contracts",
            "confidence": 0.95
        },
        {
            "name": "approval_management",
            "description": "Gestion des approvals",
            "confidence": 0.94
        }
    ],
    "standards": ["EIP-712", "EIP-2612", "EIP-1271"],
    "outputs": [
        {"name": "security_configuration", "type": "config", "format": "json"},
        {"name": "transaction_guard", "type": "code", "format": "typescript"}
    ]
}

# Liste complète des sous-agents
SUB_AGENTS = [
    REACT_EXPERT,
    WEB3_INTEGRATION,
    UI_UX_EXPERT,
    DEFI_UI_SPECIALIST,
    NFT_UI_SPECIALIST,
    PERFORMANCE_OPTIMIZER,
    SECURITY_UI_SPECIALIST
]

# ============================================================================
# FONCTIONS DE GÉNÉRATION
# ============================================================================

def create_agent_py(agent_data: Dict) -> str:
    """Crée le contenu du fichier agent.py pour un sous-agent"""
    agent_id = agent_data["id"]
    display_name = agent_data["display_name"]
    description = agent_data["description"]
    version = agent_data["version"]
    class_name = ''.join(p.capitalize() for p in agent_id.split('_')) + 'SubAgent'
    
    capabilities_list = '\n'.join([f'        "{cap["name"]}",' for cap in agent_data["capabilities"]])
    
    return f'''"""
{display_name} - Sous-agent spécialisé
Version: {version}

{description}
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


class {class_name}(BaseAgent):
    """
    {description}
    """
    
    def __init__(self, config_path: str = ""):
        """Initialise le sous-agent"""
        if not config_path:
            config_path = str(current_dir / "config.yaml")

        super().__init__(config_path)

        self._display_name = "{display_name}"
        self._initialized = False
        self._components = {{}}
        
        # Statistiques
        self._stats = {{
            'tasks_processed': 0,
            'components_generated': 0,
            'start_time': datetime.now().isoformat()
        }}

        logger.info(f"{{self._display_name}} créé - v{{self._version}}")

    async def initialize(self) -> bool:
        """Initialise le sous-agent"""
        try:
            self._set_status(AgentStatus.INITIALIZING)
            logger.info(f"Initialisation de {{self._display_name}}...")

            base_result = await super().initialize()
            if not base_result:
                return False

            await self._initialize_components()

            self._initialized = True
            self._set_status(AgentStatus.READY)
            logger.info(f"✅ {{self._display_name}} prêt")
            return True

        except Exception as e:
            logger.error(f"❌ Erreur initialisation: {{e}}")
            self._set_status(AgentStatus.ERROR)
            return False

    async def _initialize_components(self) -> bool:
        """Initialise les composants du sous-agent"""
        logger.info("Initialisation des composants...")
        
        self._components = {{
            "capabilities": [
{capabilities_list}
            ],
            "enabled": True,
            "version": "{version}"
        }}
        
        logger.info(f"✅ Composants: {{list(self._components.keys())}}")
        return True

    async def _handle_custom_message(self, message: Message) -> Optional[Message]:
        """Gère les messages personnalisés"""
        try:
            msg_type = message.message_type
            logger.debug(f"Message reçu: {{msg_type}} de {{message.sender}}")

            handlers = {{
                f"{{self.name}}.status": self._handle_status,
                f"{{self.name}}.metrics": self._handle_metrics,
                f"{{self.name}}.health": self._handle_health,
            }}

            if msg_type in handlers:
                return await handlers[msg_type](message)

            return None

        except Exception as e:
            logger.error(f"Erreur traitement message: {{e}}")
            return Message(
                sender=self.name,
                recipient=message.sender,
                content={{"error": str(e)}},
                message_type=MessageType.ERROR.value,
                correlation_id=message.message_id
            )

    async def _handle_status(self, message: Message) -> Message:
        """Retourne le statut général"""
        return Message(
            sender=self.name,
            recipient=message.sender,
            content={{
                'status': self._status.value,
                'initialized': self._initialized,
                'stats': self._stats
            }},
            message_type=f"{{self.name}}.status_response",
            correlation_id=message.message_id
        )

    async def _handle_metrics(self, message: Message) -> Message:
        """Retourne les métriques"""
        return Message(
            sender=self.name,
            recipient=message.sender,
            content=self._stats,
            message_type=f"{{self.name}}.metrics_response",
            correlation_id=message.message_id
        )

    async def _handle_health(self, message: Message) -> Message:
        """Retourne l'état de santé"""
        health = await self.health_check()
        return Message(
            sender=self.name,
            recipient=message.sender,
            content=health,
            message_type=f"{{self.name}}.health_response",
            correlation_id=message.message_id
        )

    async def shutdown(self) -> bool:
        """Arrête le sous-agent"""
        logger.info(f"Arrêt de {{self._display_name}}...")
        self._set_status(AgentStatus.SHUTTING_DOWN)
        await super().shutdown()
        logger.info(f"✅ {{self._display_name}} arrêté")
        return True

    async def pause(self) -> bool:
        """Met en pause le sous-agent"""
        logger.info(f"Pause de {{self._display_name}}...")
        self._set_status(AgentStatus.PAUSED)
        return True

    async def resume(self) -> bool:
        """Reprend l'activité"""
        logger.info(f"Reprise de {{self._display_name}}...")
        self._set_status(AgentStatus.READY)
        return True

    async def health_check(self) -> Dict[str, Any]:
        """Vérifie la santé du sous-agent"""
        base_health = await super().health_check()

        uptime = None
        if self._stats.get('start_time'):
            start = datetime.fromisoformat(self._stats['start_time'])
            uptime = str(datetime.now() - start)

        return {{
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
        }}

    def get_agent_info(self) -> Dict[str, Any]:
        """Informations pour le registre"""
        return {{
            "id": self.name,
            "name": "{class_name}",
            "display_name": self._display_name,
            "version": "{version}",
            "description": \"\"\"{description}\"\"\",
            "status": self._status.value,
            "capabilities": [
{capabilities_list}
            ],
            "stats": self._stats
        }}


def create_{agent_id}_agent(config_path: str = "") -> {class_name}:
    """Crée une instance du sous-agent"""
    return {class_name}(config_path)
'''


def create_config_yaml(agent_data: Dict) -> str:
    """Crée le contenu du fichier config.yaml pour un sous-agent"""
    agent_id = agent_data["id"]
    display_name = agent_data["display_name"]
    description = agent_data["description"]
    version = agent_data["version"]
    class_name = ''.join(p.capitalize() for p in agent_id.split('_')) + 'SubAgent'
    
    capabilities_yaml = '\n'.join([f'  - name: "{cap["name"]}"' for cap in agent_data["capabilities"]])
    
    # Technologies
    tech_items = []
    for cat, items in agent_data.get("technologies", {}).items():
        for item in items:
            tech_items.append(item)
    technologies_yaml = '\n'.join([f'    - "{tech}"' for tech in tech_items[:3]])  # Limiter à 3 pour lisibilité
    
    # Outputs
    outputs_yaml = '\n'.join([f'  - name: "{out["name"]}"' for out in agent_data.get("outputs", [])])
    
    return f'''# ============================================================================
# {display_name} - Configuration
# Version: {version}
# ============================================================================

agent:
  name: "{class_name}"
  display_name: "{display_name}"
  description: |-
    {description}
  version: "{version}"
  class_name: "{class_name}"
  module_path: "agents.frontend_web3.sous_agents.{agent_id}.agent"

# ============================================================================
# SYSTÈME
# ============================================================================
system:
  log_level: "INFO"
  timeout_seconds: 60
  max_retries: 2

# ============================================================================
# CAPACITÉS
# ============================================================================
capabilities:
{capabilities_yaml}

# ============================================================================
# TECHNOLOGIES SUPPORTÉES
# ============================================================================
technologies:
  supported:
{technologies_yaml}

# ============================================================================
# OUTPUTS PRODUITS
# ============================================================================
outputs:
{outputs_yaml}

# ============================================================================
# MÉTADONNÉES
# ============================================================================
metadata:
  author: "SmartContractDevPipeline"
  maintainer: "dev@poolsync.io"
  license: "Proprietary"
  capabilities_count: {len(agent_data["capabilities"])}
  last_reviewed: "{datetime.now().strftime("%Y-%m-%d")}"
'''


def create_directory_structure():
    """Crée toute l'arborescence des dossiers et fichiers"""
    
    print("=" * 80)
    print("🚀 CRÉATION AVANCÉE DES SOUS-AGENTS FRONTEND_WEB3")
    print("=" * 80)
    
    # 1. Créer le dossier principal des sous-agents
    print(f"\n📁 Création du dossier: {SOUS_AGENTS_PATH}")
    SOUS_AGENTS_PATH.mkdir(parents=True, exist_ok=True)
    
    # 2. Créer le __init__.py du dossier sous_agents
    init_file = SOUS_AGENTS_PATH / "__init__.py"
    print(f"   📄 Création: {init_file}")
    with open(init_file, 'w', encoding='utf-8') as f:
        f.write('"""\nPackage des sous-agents Frontend Web3\nSous-agents spécialisés pour le développement d\'interfaces Web3\n"""\n\n__all__ = []\n')
    
    # 3. Créer chaque sous-agent
    for agent in SUB_AGENTS:
        agent_id = agent["id"]
        display_name = agent["display_name"]
        
        agent_path = SOUS_AGENTS_PATH / agent_id
        print(f"\n📁 Création du sous-agent: {agent_id}")
        print(f"   📁 Dossier: {agent_path}")
        agent_path.mkdir(exist_ok=True)
        
        # Créer __init__.py
        init_file = agent_path / "__init__.py"
        print(f"   📄 Création: {init_file}")
        with open(init_file, 'w', encoding='utf-8') as f:
            class_name = ''.join(p.capitalize() for p in agent_id.split('_')) + 'SubAgent'
            f.write(f'''"""
Package {display_name}
Version: {agent["version"]}

{agent["description"]}
"""

from .agent import {class_name}

__all__ = ['{class_name}']
__version__ = '{agent["version"]}'
''')
        
        # Créer agent.py
        agent_file = agent_path / "agent.py"
        print(f"   📄 Création: {agent_file}")
        with open(agent_file, 'w', encoding='utf-8') as f:
            f.write(create_agent_py(agent))
        
        # Créer config.yaml
        config_file = agent_path / "config.yaml"
        print(f"   📄 Création: {config_file}")
        with open(config_file, 'w', encoding='utf-8') as f:
            f.write(create_config_yaml(agent))
        
        # Créer tools.py
        tools_file = agent_path / "tools.py"
        print(f"   📄 Création: {tools_file}")
        with open(tools_file, 'w', encoding='utf-8') as f:
            f.write(f'''"""
Outils utilitaires pour {display_name}
Version: {agent["version"]}
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

logger = logging.getLogger(__name__)


def format_timestamp(timestamp: Optional[datetime] = None) -> str:
    """Formate un timestamp pour l'affichage"""
    if timestamp is None:
        timestamp = datetime.now()
    return timestamp.strftime("%Y-%m-%d %H:%M:%S")
''')
        
        print(f"   ✅ Sous-agent {agent_id} créé avec succès")
    
    print("\n" + "=" * 80)
    print("✅ CRÉATION TERMINÉE AVEC SUCCÈS !")
    print("=" * 80)
    
    # Résumé
    print(f"\n📊 RÉSUMÉ:")
    print(f"   • Dossier principal: {SOUS_AGENTS_PATH}")
    print(f"   • Nombre de sous-agents: {len(SUB_AGENTS)}")
    print(f"   • Fichiers créés: {len(SUB_AGENTS) * 4 + 1} fichiers")


def verify_agent_parent():
    """Vérifie que l'agent parent existe"""
    agent_file = AGENT_PATH / "agent.py"
    
    if not agent_file.exists():
        print(f"\n⚠️  Attention: {agent_file} n'existe pas!")
        print("   Vous devez d'abord créer l'agent parent frontend_web3.")
        return False
    
    return True


if __name__ == "__main__":
    # Vérifier qu'on est à la racine du projet
    if not (PROJECT_ROOT / "agents").exists():
        print(f"❌ Erreur: Le dossier 'agents' n'existe pas dans {PROJECT_ROOT}")
        print("   Assurez-vous d'exécuter ce script depuis la racine du projet")
        sys.exit(1)
    
    # Créer l'arborescence
    create_directory_structure()
    
    # Vérifications finales
    verify_agent_parent()
    
    print(f"\n🎉 Tous les sous-agents ont été créés avec succès!")
    print(f"\n🚀 Vous pouvez maintenant lancer votre application!")
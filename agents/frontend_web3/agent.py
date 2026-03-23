"""
Frontend Web3 Agent - Agent de génération d'interfaces Web3
Version: 2.5.0 (ALIGNÉ SUR ARCHITECT/CODER/LEARNING/SMARTCONTRACT)
"""

import logging
import os
import sys
import json
import yaml
import asyncio
import subprocess
import re
import traceback
import importlib  # AJOUT IMPORTANT
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, field, asdict

logger = logging.getLogger(__name__)

# ============================================================================
# CONFIGURATION DES IMPORTS - Chemin absolu
# ============================================================================

project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from agents.base_agent.base_agent import BaseAgent, AgentStatus, Message, MessageType


# ============================================================================
# ÉNUMS
# ============================================================================

class FrameworkType(Enum):
    """Frameworks frontend supportés"""
    REACT = "react"
    NEXTJS = "nextjs"
    VUE = "vue"
    HTML = "html"


class ComponentType(Enum):
    """Types de composants à générer"""
    # Composants existants
    MINT_PAGE = "mint_page"
    DASHBOARD = "dashboard"
    MARKETPLACE = "marketplace"
    STAKING = "staking_page"
    GOVERNANCE = "governance_page"
    NFT_GALLERY = "nft_gallery"
    TOKEN_TRANSFER = "token_transfer"
    SWAP = "swap_page"
    BRIDGE = "bridge_page"
    ANALYTICS = "analytics_dashboard"
    PROFILE = "profile_page"
    AUCTION = "auction_house"
    LENDING = "lending_page"
    MULTISIG = "multisig_wallet"
    AIRDROP = "airdrop_page"
    CUSTOM = "custom"
    
    # Banking Core 2.0
    BANKING_DASHBOARD_2_0 = "banking_dashboard_2_0"
    VIRTUAL_CARDS = "virtual_cards"
    SAVINGS_PODS = "savings_pods"
    ROUND_UP_SAVINGS = "round_up_savings"
    SPENDING_INSIGHTS = "spending_insights"
    BUDGET_FORECAST = "budget_forecast"
    BILL_SPLITTING = "bill_splitting"
    DIRECT_DEBIT = "direct_debit"
    
    # Lending 2.0
    LENDING_MARKETPLACE_2_0 = "lending_marketplace_2_0"
    COLLATERAL_MANAGEMENT = "collateral_management"
    LIQUIDATION_GUARD = "liquidation_guard"
    YIELD_OPTIMIZER = "yield_optimizer"
    LOAN_BUILDER = "loan_builder"
    CREDIT_SCORING = "credit_scoring"
    NFT_LENDING = "nft_lending"
    
    # Web3 Innovations
    GASLESS_INTERFACE = "gasless_interface"
    SOCIAL_RECOVERY = "social_recovery"
    PASSKEY_AUTH = "passkey_auth"
    DEFI_COMPOSER = "defi_composer"
    CROSS_CHAIN_SWAP = "cross_chain_swap"
    SESSION_KEYS = "session_keys"
    
    # UX 2.0
    VOICE_COMMANDS = "voice_commands"
    GESTURE_NAVIGATION = "gesture_navigation"
    HAPTIC_FEEDBACK = "haptic_feedback"
    BIOMETRIC_CONFIRM = "biometric_confirm"


class Web3Library(Enum):
    """Bibliothèques Web3 supportées"""
    ETHERS = "ethers"
    WEB3JS = "web3.js"
    VIEM = "viem"
    WAGMI = "wagmi"


# ============================================================================
# CLASSES DE DONNÉES
# ============================================================================

@dataclass
class FrontendProject:
    """Projet frontend généré"""
    id: str
    name: str
    framework: FrameworkType
    components: List[Dict] = field(default_factory=list)
    contracts: List[Dict] = field(default_factory=list)
    output_path: Optional[str] = None
    deploy_url: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    theme: str = "dark"
    
    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d['framework'] = self.framework.value
        d['created_at'] = self.created_at.isoformat()
        return d
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FrontendProject':
        """Crée une instance depuis un dictionnaire"""
        data = data.copy()
        data['framework'] = FrameworkType(data['framework'])
        data['created_at'] = datetime.fromisoformat(data['created_at'])
        return cls(**data)


@dataclass
class ContractABI:
    """ABI d'un contrat intelligent"""
    name: str
    abi: List[Dict]
    path: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# ============================================================================
# AGENT PRINCIPAL - FRONTEND WEB3 (ALIGNÉ)
# ============================================================================

class FrontendWeb3Agent(BaseAgent):
    """
    Agent de génération d'interfaces Web3
    Crée automatiquement des applications React/Next.js pour interagir avec les smart contracts
    Version 2.5 - Alignée sur l'architecture des agents
    """

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialise l'agent frontend Web3

        Args:
            config_path: Chemin vers le fichier de configuration
        """
        if config_path is None:
            config_path = str(project_root / "agents" / "frontend_web3" / "config.yaml")

        # Initialiser l'agent de base
        super().__init__(config_path)

        # Configuration spécifique
        agent_config = self._agent_config.get('agent', {})
        self._display_name = agent_config.get('display_name', '🎨 Agent Frontend Web3')
        self._frontend_config = self._agent_config.get('frontend', {})
        self._deployment_config = self._agent_config.get('deployment', {})

        # État interne
        self._projects: Dict[str, FrontendProject] = {}
        self._components_generated = 0
        self._templates: Dict[str, str] = {}
        self._templates_2_0: Dict[str, str] = {}
        self._contract_abis: Dict[str, ContractABI] = {}
        self._components: Dict[str, Any] = {}
        self._sub_agents: Dict[str, Any] = {}
        self._initialized = False

        # Statistiques internes
        self._stats = {
            'total_projects': 0,
            'total_components_generated': 0,
            'total_contracts_analyzed': 0,
            'deployments': 0,
            'uptime_start': datetime.now().isoformat()
        }

        # Tâches de fond
        self._cleanup_task_obj = None

        # Créer les répertoires
        self._create_directories()

        self._logger.info(f"🎨 Agent frontend Web3 créé - v{self._version}")

    def _get_default_config(self) -> Dict[str, Any]:
        """Configuration par défaut (si aucune config fournie)"""
        return {
            "agent": {
                "name": "frontend_web3",
                "display_name": "🎨 Agent Frontend Web3",
                "description": "Génération d'interfaces React/Next.js pour smart contracts",
                "version": "2.5.0",
                "capabilities": [
                    "react_generation",
                    "nextjs_generation",
                    "wallet_integration",
                    "contract_interaction",
                    "banking_dashboard_2_0",
                    "lending_marketplace_2_0",
                    "nft_lending",
                    "credit_scoring",
                    "defi_composer"
                ],
                "dependencies": ["smart_contract", "coder"]
            },
            "frontend": {
                "default_framework": "nextjs",
                "default_library": "wagmi",
                "output_path": "./frontend",
                "include_tests": True,
                "include_docs": True,
                "theme": "dark",
                "colors": {
                    "primary": "#3b82f6",
                    "secondary": "#10b981",
                    "accent": "#8b5cf6",
                    "background": "#0f172a",
                    "text": "#f8fafc"
                }
            },
            "deployment": {
                "auto_deploy": False,
                "platform": "vercel",
                "vercel_token": None,
                "ipfs_gateway": "https://ipfs.io/ipfs/"
            }
        }

    def _create_directories(self):
        """Crée les répertoires nécessaires"""
        dirs = [
            self._frontend_config.get("output_path", "./frontend"),
            self._agent_config.get("templates_path", "./agents/frontend_web3/templates"),
            self._agent_config.get("abis_path", "./agents/frontend_web3/contracts/abi"),
            self._agent_config.get("components_path", "./agents/frontend_web3/components"),
            self._agent_config.get("hooks_path", "./agents/frontend_web3/hooks"),
            self._agent_config.get("utils_path", "./agents/frontend_web3/utils"),
            self._agent_config.get("styles_path", "./agents/frontend_web3/styles"),
        ]

        for dir_path in dirs:
            Path(dir_path).mkdir(parents=True, exist_ok=True)
            self._logger.debug(f"📁 Répertoire créé: {dir_path}")

    # ============================================================================
    # MÉTHODES D'INITIALISATION (ALIGNÉES)
    # ============================================================================

    async def initialize(self) -> bool:
        """
        Initialisation asynchrone de l'agent
        """
        try:
            self._set_status(AgentStatus.INITIALIZING)
            self._logger.info("🎨 Initialisation du Frontend Web3 Agent...")

            # Appeler l'initialisation du parent
            base_result = await super().initialize()
            if not base_result:
                return False

            # Initialiser les composants spécifiques
            await self._initialize_components()

            # Initialiser les sous-agents
            await self._initialize_sub_agents()

            # Charger les templates
            await self._load_templates()

            # Charger les projets existants
            await self._load_projects()

            # Démarrer les tâches de fond
            self._start_background_tasks()

            self._initialized = True
            self._set_status(AgentStatus.READY)
            self._logger.info("✅ Agent Frontend Web3 prêt")
            return True

        except Exception as e:
            self._logger.error(f"❌ Erreur initialisation: {e}")
            self._logger.error(traceback.format_exc())
            self._set_status(AgentStatus.ERROR)
            return False

    async def _initialize_components(self) -> bool:
        """
        Initialise les composants spécifiques.
        Appelé par BaseAgent.initialize().
        """
        try:
            self._logger.info("Initialisation des composants Frontend Web3...")

            self._components = {
                "react_generator": self._init_react_generator(),
                "nextjs_generator": self._init_nextjs_generator(),
                "vue_generator": self._init_vue_generator(),
                "contract_analyzer": self._init_contract_analyzer(),
                "deployment_manager": self._init_deployment_manager()
            }

            self._logger.info(f"✅ Composants: {list(self._components.keys())}")
            return True

        except Exception as e:
            self._logger.error(f"Erreur composants: {e}")
            return False

    async def _initialize_sub_agents(self):
        """
        Initialise les sous-agents spécialisés de manière robuste
        Cette méthode ne doit jamais lever d'exception
        """
        self._sub_agents = {}

        try:
            # Liste des sous-agents à tenter de charger (basée sur config.yaml)
            sub_agent_configs = self._agent_config.get('agent', {}).get('subAgents', [])

            # Si la liste est vide, utiliser les sous-agents par défaut
            if not sub_agent_configs:
                sub_agent_configs = [
                    {"id": "react_expert", "name": "React/Next.js Expert", "enabled": True},
                    {"id": "web3_integration", "name": "Web3 Integration Expert", "enabled": True},
                    {"id": "ui_ux_expert", "name": "UI/UX Designer", "enabled": True},
                    {"id": "defi_ui_specialist", "name": "DeFi UI Specialist", "enabled": True},
                    {"id": "nft_ui_specialist", "name": "NFT UI Specialist", "enabled": True},
                    {"id": "performance_optimizer", "name": "Web3 Performance Optimizer", "enabled": True},
                    {"id": "security_ui_specialist", "name": "UI Security Specialist", "enabled": True},
                ]

            for config in sub_agent_configs:
                agent_id = config.get('id')
                if not config.get('enabled', True):
                    continue

                try:
                    # Tentative d'import dynamique du module
                    module_name = f"agents.frontend_web3.sous_agents.{agent_id}.agent"
                    class_name = self._get_sub_agent_class_name(agent_id)

                    # Vérifier si le fichier existe
                    module_path = Path(__file__).parent / "sous_agents" / agent_id / "agent.py"
                    if not module_path.exists():
                        self._logger.debug(f"  ℹ️ Sous-agent {agent_id} non développé (fichier manquant)")
                        continue

                    module = importlib.import_module(module_name)
                    agent_class = getattr(module, class_name, None)

                    if agent_class:
                        config_path = config.get('config_path', str(Path(__file__).parent / "sous_agents" / agent_id / "config.yaml"))
                        sub_agent = agent_class(config_path)
                        self._sub_agents[agent_id] = sub_agent
                        self._logger.info(f"  ✓ Sous-agent {agent_id} initialisé")
                    else:
                        self._logger.debug(f"  ℹ️ Classe {class_name} non trouvée dans {agent_id}")

                except ImportError as e:
                    self._logger.debug(f"  ℹ️ Sous-agent {agent_id} non disponible: {e}")
                except Exception as e:
                    self._logger.warning(f"  ⚠️ Erreur initialisation {agent_id}: {e}")

        except Exception as e:
            self._logger.error(f"❌ Erreur globale initialisation sous-agents: {e}")

        self._logger.info(f"✅ Sous-agents chargés: {len(self._sub_agents)}")

    def _get_sub_agent_class_name(self, agent_id: str) -> str:
        """Convertit un ID de sous-agent en nom de classe"""
        # Convertit "react_expert" en "ReactExpertSubAgent"
        parts = agent_id.split('_')
        class_name = ''.join(p.capitalize() for p in parts) + 'SubAgent'
        return class_name

    def _start_background_tasks(self):
        """Démarre les tâches de fond"""
        loop = asyncio.get_event_loop()
        self._cleanup_task_obj = loop.create_task(self._cleanup_task())
        self._logger.debug("🧹 Tâche de nettoyage démarrée")

    async def _cleanup_task(self):
        """
        Tâche de nettoyage périodique
        """
        self._logger.info("🧹 Tâche de nettoyage démarrée")
        while self._status == AgentStatus.READY:
            try:
                # Nettoyage toutes les heures
                await asyncio.sleep(3600)

                self._logger.debug("Nettoyage périodique...")

                # Nettoyer les anciens projets (plus de 30 jours)
                retention_days = 30
                cutoff = datetime.now() - timedelta(days=retention_days)
                
                projects_to_remove = []
                for project_id, project in self._projects.items():
                    if project.created_at < cutoff:
                        projects_to_remove.append(project_id)
                
                for project_id in projects_to_remove:
                    del self._projects[project_id]
                    self._logger.debug(f"🗑️ Ancien projet supprimé: {project_id}")

            except asyncio.CancelledError:
                self._logger.info("🛑 Tâche de nettoyage arrêtée")
                break
            except Exception as e:
                self._logger.error(f"❌ Erreur dans la tâche de nettoyage: {e}")
                await asyncio.sleep(60)

    # ============================================================================
    # MÉTHODES D'INITIALISATION DES COMPOSANTS
    # ============================================================================

    def _init_react_generator(self) -> Dict[str, Any]:
        """Initialise le générateur React"""
        return {
            "version": "18.2.0",
            "template": "vite",
            "dependencies": [
                "ethers@5.7.2",
                "@rainbow-me/rainbowkit@0.12.0",
                "wagmi@1.3.0",
                "viem@1.10.0",
                "react-router-dom@6.14.0",
                "tailwindcss@3.3.0"
            ],
            "enabled": True
        }

    def _init_nextjs_generator(self) -> Dict[str, Any]:
        """Initialise le générateur Next.js"""
        return {
            "version": "13.4.0",
            "template": "app",
            "dependencies": [
                "ethers@5.7.2",
                "@rainbow-me/rainbowkit@0.12.0",
                "wagmi@1.3.0",
                "viem@1.10.0",
                "next-auth@4.22.0",
                "tailwindcss@3.3.0"
            ],
            "enabled": True
        }

    def _init_vue_generator(self) -> Dict[str, Any]:
        """Initialise le générateur Vue.js"""
        return {
            "version": "3.3.0",
            "template": "vite",
            "dependencies": [
                "ethers@5.7.2",
                "web3@4.0.0",
                "vue-router@4.2.0",
                "pinia@2.1.0",
                "tailwindcss@3.3.0"
            ],
            "enabled": False
        }

    def _init_contract_analyzer(self) -> Dict[str, Any]:
        """Initialise l'analyseur de contrats"""
        return {
            "extract_abi": True,
            "generate_types": True,
            "analyze_functions": True,
            "analyze_events": True,
            "enabled": True
        }

    def _init_deployment_manager(self) -> Dict[str, Any]:
        """Initialise le gestionnaire de déploiement"""
        return {
            "platforms": ["vercel", "netlify", "ipfs"],
            "auto_deploy": self._deployment_config.get("auto_deploy", False),
            "default_platform": self._deployment_config.get("platform", "vercel"),
            "enabled": True
        }

    async def _load_templates(self):
        """Charge les templates 2.0"""
        templates_path = Path(self._agent_config.get("templates_path", "./agents/frontend_web3/templates"))
        templates_path.mkdir(parents=True, exist_ok=True)

        # Templates 2.0
        self._templates_2_0 = {
            # Banking
            "banking_dashboard_2_0": self._create_banking_dashboard_2_0(),
            "virtual_cards": self._create_virtual_cards(),
            "savings_pods": self._create_savings_pods(),
            "round_up_savings": self._create_round_up_savings(),
            "spending_insights": self._create_spending_insights(),
            "budget_forecast": self._create_budget_forecast(),
            "bill_splitting": self._create_bill_splitting(),
            "direct_debit": self._create_direct_debit(),
            
            # Lending
            "lending_marketplace_2_0": self._create_lending_marketplace_2_0(),
            "collateral_management": self._create_collateral_management(),
            "liquidation_guard": self._create_liquidation_guard(),
            "yield_optimizer": self._create_yield_optimizer(),
            "loan_builder": self._create_loan_builder(),
            "credit_scoring": self._create_credit_scoring(),
            "nft_lending": self._create_nft_lending(),
            
            # Web3 Innovations
            "gasless_interface": self._create_gasless_interface(),
            "social_recovery": self._create_social_recovery(),
            "passkey_auth": self._create_passkey_auth(),
            "defi_composer": self._create_defi_composer(),
            "cross_chain_swap": self._create_cross_chain_swap(),
            "bridge_page": self._create_bridge_page_2_0(),
            "session_keys": self._create_session_keys(),
        }

        # Fusionner avec les templates existants
        self._templates.update(self._templates_2_0)

        self._logger.info(f"📋 Templates 2.0: {len(self._templates_2_0)}")
        self._logger.info(f"📋 Templates totaux: {len(self._templates)}")

    async def _load_projects(self):
        """Charge les projets existants depuis le disque"""
        try:
            output_path = Path(self._frontend_config.get("output_path", "./frontend"))
            projects_file = output_path / "projects_index.json"
            
            if projects_file.exists():
                with open(projects_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for project_data in data.get("projects", []):
                        project = FrontendProject.from_dict(project_data)
                        self._projects[project.id] = project
                
                self._logger.info(f"📦 {len(self._projects)} projets chargés")
        except Exception as e:
            self._logger.warning(f"⚠️ Erreur chargement projets: {e}")

    async def _save_projects(self):
        """Sauvegarde les projets sur le disque"""
        try:
            output_path = Path(self._frontend_config.get("output_path", "./frontend"))
            output_path.mkdir(parents=True, exist_ok=True)
            
            projects_file = output_path / "projects_index.json"
            with open(projects_file, 'w', encoding='utf-8') as f:
                json.dump({
                    "projects": [p.to_dict() for p in self._projects.values()],
                    "timestamp": datetime.now().isoformat()
                }, f, indent=2, ensure_ascii=False)
            
            self._logger.debug(f"💾 Projets sauvegardés: {projects_file}")
        except Exception as e:
            self._logger.error(f"❌ Erreur sauvegarde projets: {e}")

    # ============================================================================
    # MÉTHODES DE GESTION D'ÉTAT (ALIGNÉES)
    # ============================================================================

    async def shutdown(self) -> bool:
        """Arrête l'agent proprement"""
        self._logger.info("Arrêt de l'agent FrontendWeb3...")
        self._set_status(AgentStatus.SHUTTING_DOWN)

        # Annuler la tâche de nettoyage
        if self._cleanup_task_obj and not self._cleanup_task_obj.done():
            self._cleanup_task_obj.cancel()
            try:
                await self._cleanup_task_obj
            except asyncio.CancelledError:
                pass

        # Arrêter les sous-agents
        for agent_name, agent_instance in self._sub_agents.items():
            try:
                await agent_instance.shutdown()
                self._logger.debug(f"  ✓ Sous-agent {agent_name} arrêté")
            except Exception as e:
                self._logger.warning(f"  ⚠️ Erreur arrêt sous-agent {agent_name}: {e}")

        # Sauvegarder les données
        await self._save_projects()
        await self._save_stats()

        # Appeler la méthode parent
        await super().shutdown()

        self._logger.info("✅ Agent FrontendWeb3 arrêté")
        return True

    async def pause(self) -> bool:
        """Met l'agent en pause"""
        self._logger.info("Pause de l'agent FrontendWeb3...")

        # Mettre en pause les sous-agents
        for agent_name, agent_instance in self._sub_agents.items():
            try:
                await agent_instance.pause()
            except Exception as e:
                self._logger.warning(f"⚠️ Erreur pause sous-agent {agent_name}: {e}")

        self._set_status(AgentStatus.PAUSED)
        return True

    async def resume(self) -> bool:
        """Reprend l'activité"""
        self._logger.info("Reprise de l'agent FrontendWeb3...")

        # Reprendre les sous-agents
        for agent_name, agent_instance in self._sub_agents.items():
            try:
                await agent_instance.resume()
            except Exception as e:
                self._logger.warning(f"⚠️ Erreur reprise sous-agent {agent_name}: {e}")

        self._set_status(AgentStatus.READY)
        return True

    async def _save_stats(self):
        """Sauvegarde les statistiques"""
        try:
            output_dir = Path(self._frontend_config.get("output_path", "./frontend"))
            stats_file = output_dir / "frontend_stats.json"
            with open(stats_file, 'w', encoding='utf-8') as f:
                json.dump({
                    "stats": self._stats,
                    "projects": len(self._projects),
                    "components_generated": self._components_generated,
                    "timestamp": datetime.now().isoformat()
                }, f, indent=2)
            self._logger.info(f"✅ Statistiques sauvegardées")
        except Exception as e:
            self._logger.warning(f"⚠️ Impossible de sauvegarder: {e}")

    # ============================================================================
    # MÉTHODES DE SANTÉ ET D'INFORMATION (ALIGNÉES)
    # ============================================================================

    async def health_check(self) -> Dict[str, Any]:
        """Vérifie la santé de l'agent"""
        # Calculer l'uptime
        uptime = None
        if self._stats.get('uptime_start'):
            start = datetime.fromisoformat(self._stats['uptime_start'])
            uptime = str(datetime.now() - start)

        # Vérifier la santé des sous-agents
        sub_agents_health = {}
        for agent_name, agent_instance in self._sub_agents.items():
            try:
                if hasattr(agent_instance, 'health_check'):
                    health = await agent_instance.health_check()
                    sub_agents_health[agent_name] = {
                        "status": health.get("status", "unknown"),
                        "ready": health.get("ready", False)
                    }
                else:
                    sub_agents_health[agent_name] = {"status": "unknown", "error": "No health_check method"}
            except Exception as e:
                sub_agents_health[agent_name] = {"status": "error", "error": str(e)}

        return {
            "agent": self.name,
            "display_name": self._display_name,
            "status": self._status.value if hasattr(self._status, 'value') else str(self._status),
            "ready": self._status == AgentStatus.READY,
            "initialized": self._initialized,
            "uptime": uptime,
            "sub_agents": len(self._sub_agents),
            "sub_agents_health": sub_agents_health,
            "stats": self._stats,
            "timestamp": datetime.now().isoformat()
        }

    def get_agent_info(self) -> Dict[str, Any]:
        """Retourne les informations de l'agent pour le registre"""
        agent_config = self._agent_config.get('agent', {})
        capabilities = agent_config.get('capabilities', [])

        if capabilities and isinstance(capabilities[0], dict):
            capabilities = [cap.get('name') for cap in capabilities if cap.get('name')]

        return {
            "id": self.name,
            "name": "FrontendWeb3Agent",
            "display_name": self._display_name,
            "version": agent_config.get('version', '2.5.0'),
            "description": agent_config.get('description', 'Génération d\'interfaces Web3'),
            "status": self._status.value if hasattr(self._status, 'value') else str(self._status),
            "capabilities": capabilities,
            "features": {
                "frameworks": ["nextjs", "react", "vue"],
                "templates_2_0": list(self._templates_2_0.keys()),
                "sub_agents": list(self._sub_agents.keys()),
                "deployment_platforms": ["vercel", "netlify", "ipfs"]
            },
            "stats": {
                "projects_generated": len(self._projects),
                "components_generated": self._components_generated,
                "deployments": self._stats['deployments']
            }
        }

    async def get_sub_agents_status(self) -> Dict[str, Any]:
        """Retourne le statut de tous les sous-agents"""
        status = {}
        for agent_name, agent_instance in self._sub_agents.items():
            try:
                health = await agent_instance.health_check()
                status[agent_name] = {
                    "status": health.get("status", "unknown"),
                    "agent_info": agent_instance.get_agent_info()
                }
            except Exception as e:
                status[agent_name] = {
                    "status": "error",
                    "error": str(e)
                }

        return {
            "total_sub_agents": len(self._sub_agents),
            "sub_agents": status
        }

    async def delegate_to_sub_agent(self, task_type: str, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Délègue une tâche à un sous-agent approprié.

        Args:
            task_type: Type de tâche à déléguer
            task_data: Données de la tâche

        Returns:
            Résultat de l'exécution par le sous-agent
        """
        # Mapping des types de tâches vers les sous-agents
        sub_agent_mapping = {
            "react": "react_expert",
            "nextjs": "react_expert",
            "web3": "web3_integration",
            "wallet": "web3_integration",
            "contract": "web3_integration",
            "ui": "ui_ux_expert",
            "ux": "ui_ux_expert",
            "defi": "defi_ui_specialist",
            "nft": "nft_ui_specialist",
            "performance": "performance_optimizer",
            "security": "security_ui_specialist"
        }

        for pattern, agent_name in sub_agent_mapping.items():
            if task_type.startswith(pattern):
                if agent_name in self._sub_agents:
                    self._logger.info(f"➡️ Délégation de la tâche {task_type} au sous-agent {agent_name}")
                    # Créer un message pour le sous-agent
                    msg = Message(
                        sender=self.name,
                        recipient=agent_name,
                        content=task_data,
                        message_type=f"frontend.{task_type}",
                        correlation_id=f"delegate_{datetime.now().timestamp()}"
                    )
                    return await self._sub_agents[agent_name].handle_message(msg)

        # Fallback: utiliser l'agent principal
        self._logger.info(f"ℹ️ Aucun sous-agent trouvé pour {task_type}, utilisation de l'agent principal")
        
        # Exécuter la tâche localement selon le type
        if task_type == "generate":
            return {
                "project": (await self.generate_project(
                    task_data.get("project_name", "Web3App"),
                    task_data.get("contracts", []),
                    task_data.get("components", []),
                    task_data.get("framework", "nextjs")
                )).to_dict()
            }
        elif task_type == "deploy":
            url = await self.deploy_to_vercel(task_data.get("project_id", ""))
            return {"url": url, "success": url is not None}
        elif task_type == "extract_abi":
            return await self.extract_contract_abi(task_data.get("contract_path", ""))
        else:
            return {"success": False, "error": f"Type de tâche non supporté: {task_type}"}

    # ============================================================================
    # GESTION DES MESSAGES (ALIGNÉE)
    # ============================================================================

    async def _handle_custom_message(self, message: Message) -> Optional[Message]:
        """
        Gère les messages personnalisés pour le Frontend Web3 Agent.
        """
        try:
            msg_type = message.message_type
            self._logger.debug(f"Message personnalisé reçu: {msg_type} de {message.sender}")

            # D'abord, essayer de déléguer à un sous-agent
            if message.content and "sub_agent_task" in message.content:
                task_type = message.content.get("sub_agent_task")
                return await self.delegate_to_sub_agent(task_type, message.content)

            # Mapping des types de messages vers les méthodes
            handlers = {
                "frontend.generate": self._handle_generate,
                "frontend.deploy": self._handle_deploy,
                "frontend.list_projects": self._handle_list_projects,
                "frontend.extract_abi": self._handle_extract_abi,
                "frontend.stats": self._handle_stats,
                "frontend.get_sub_agents_status": self._handle_get_sub_agents_status,
                "frontend.pause": self._handle_pause,
                "frontend.resume": self._handle_resume,
                "frontend.shutdown": self._handle_shutdown,
            }

            if msg_type in handlers:
                return await handlers[msg_type](message)

            self._logger.warning(f"Aucun handler pour le type: {msg_type}")
            return None

        except Exception as e:
            self._logger.error(f"Erreur traitement message: {e}")
            return Message(
                sender=self.name,
                recipient=message.sender,
                content={"error": str(e), "traceback": traceback.format_exc()},
                message_type=MessageType.ERROR.value,
                correlation_id=message.message_id
            )

    async def _handle_generate(self, message: Message) -> Message:
        """Gère la génération de projet frontend"""
        content = message.content
        project = await self.generate_project(
            project_name=content.get("project_name", "Web3App"),
            contract_paths=content.get("contracts", []),
            components=content.get("components", []),
            framework=content.get("framework", "nextjs")
        )

        return Message(
            sender=self.name,
            recipient=message.sender,
            content={
                "project_id": project.id,
                "output_path": project.output_path,
                "components": len(project.components)
            },
            message_type="frontend.generated",
            correlation_id=message.message_id
        )

    async def _handle_deploy(self, message: Message) -> Message:
        """Gère le déploiement d'un projet"""
        project_id = message.content.get("project_id", "")
        url = await self.deploy_to_vercel(project_id)

        return Message(
            sender=self.name,
            recipient=message.sender,
            content={"url": url, "success": url is not None},
            message_type="frontend.deployed",
            correlation_id=message.message_id
        )

    async def _handle_list_projects(self, message: Message) -> Message:
        """Liste tous les projets générés"""
        return Message(
            sender=self.name,
            recipient=message.sender,
            content={"projects": [p.to_dict() for p in self._projects.values()]},
            message_type="frontend.projects_list",
            correlation_id=message.message_id
        )

    async def _handle_extract_abi(self, message: Message) -> Message:
        """Extrait l'ABI d'un contrat"""
        contract_path = message.content.get("contract_path", "")
        abi_info = await self.extract_contract_abi(contract_path)

        return Message(
            sender=self.name,
            recipient=message.sender,
            content=abi_info,
            message_type="frontend.abi_extracted",
            correlation_id=message.message_id
        )

    async def _handle_stats(self, message: Message) -> Message:
        """Retourne les statistiques"""
        return Message(
            sender=self.name,
            recipient=message.sender,
            content={"stats": self._stats, "agent_info": self.get_agent_info()},
            message_type="frontend.stats_response",
            correlation_id=message.message_id
        )

    async def _handle_get_sub_agents_status(self, message: Message) -> Message:
        """Gère la récupération du statut des sous-agents"""
        status = await self.get_sub_agents_status()
        return Message(
            sender=self.name,
            recipient=message.sender,
            content=status,
            message_type="frontend.sub_agents_status",
            correlation_id=message.message_id
        )

    async def _handle_pause(self, message: Message) -> Message:
        """Gère la pause"""
        await self.pause()
        return Message(
            sender=self.name,
            recipient=message.sender,
            content={"status": "paused"},
            message_type="frontend.status_update",
            correlation_id=message.message_id
        )

    async def _handle_resume(self, message: Message) -> Message:
        """Gère la reprise"""
        await self.resume()
        return Message(
            sender=self.name,
            recipient=message.sender,
            content={"status": "resumed"},
            message_type="frontend.status_update",
            correlation_id=message.message_id
        )

    async def _handle_shutdown(self, message: Message) -> Message:
        """Gère l'arrêt"""
        await self.shutdown()
        return Message(
            sender=self.name,
            recipient=message.sender,
            content={"status": "shutdown"},
            message_type="frontend.status_update",
            correlation_id=message.message_id
        )

    # ============================================================================
    # MÉTHODES FONCTIONNELLES (PRÉSERVÉES)
    # ============================================================================

    async def extract_contract_abi(self, contract_path: str) -> Dict:
        """Extrait l'ABI d'un contrat compilé"""
        self._logger.info(f"🔍 Extraction ABI de {contract_path}")
        self._stats['total_contracts_analyzed'] += 1

        contract_name = Path(contract_path).stem
        possible_paths = [
            f"./artifacts/contracts/{contract_name}.sol/{contract_name}.json",
            f"./out/{contract_name}.sol/{contract_name}.json",
            f"./build/contracts/{contract_name}.json"
        ]

        for path in possible_paths:
            if os.path.exists(path):
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        abi = data.get('abi', [])
                        abi_path = Path(self._agent_config.get("abis_path", "./agents/frontend_web3/contracts/abi")) / f"{contract_name}.json"
                        with open(abi_path, 'w', encoding='utf-8') as af:
                            json.dump(abi, af, indent=2)
                        self._logger.info(f"✅ ABI extraite: {abi_path}")
                        return {"name": contract_name, "abi": abi, "path": str(abi_path)}
                except Exception as e:
                    self._logger.warning(f"⚠️ Erreur lecture ABI: {e}")

        self._logger.warning(f"⚠️ ABI non trouvée pour {contract_name}")
        return {"name": contract_name, "abi": [], "path": None}

    async def generate_nextjs_project(self,
                                     project_name: str,
                                     contracts: List[str],
                                     components: List[ComponentType],
                                     theme: str = "dark") -> FrontendProject:
        """Génère un projet Next.js complet"""
        self._logger.info(f"🚀 Génération projet Next.js: {project_name}")

        project = FrontendProject(
            id=f"FRONTEND-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            name=project_name,
            framework=FrameworkType.NEXTJS,
            theme=theme
        )

        output_dir = Path(self._frontend_config.get("output_path", "./frontend")) / project.id

        self._create_nextjs_structure(output_dir, project_name)

        for contract in contracts:
            abi_info = await self.extract_contract_abi(contract)
            if abi_info["abi"]:
                project.contracts.append(abi_info)

        for component in components:
            await self._generate_component(project, component, output_dir)

        self._generate_nextjs_config(output_dir, project)
        self._generate_package_json(output_dir, project)
        self._generate_wagmi_config(output_dir, project)
        self._generate_layout(output_dir, project)

        project.output_path = str(output_dir)
        self._projects[project.id] = project
        self._stats['total_projects'] += 1
        self._stats['total_components_generated'] += len(components)

        # Sauvegarder l'index des projets
        await self._save_projects()

        self._logger.info(f"✅ Projet généré: {output_dir}")
        return project

    def _create_nextjs_structure(self, output_dir: Path, project_name: str):
        """Crée la structure de dossiers Next.js"""
        dirs = [
            output_dir / "app",
            output_dir / "app/api",
            output_dir / "components",
            output_dir / "components/ui",
            output_dir / "components/layout",
            output_dir / "lib",
            output_dir / "lib/contracts",
            output_dir / "lib/hooks",
            output_dir / "public",
            output_dir / "styles",
            output_dir / "types"
        ]

        for dir_path in dirs:
            dir_path.mkdir(parents=True, exist_ok=True)

    def _generate_nextjs_config(self, output_dir: Path, project: FrontendProject):
        """Génère next.config.js"""
        config = f"""/** @type {{import('next').NextConfig}} */
const nextConfig = {{
    reactStrictMode: true,
    swcMinify: true,
    images: {{
        domains: ['ipfs.io', 'gateway.pinata.cloud'],
    }},
    webpack: (config) => {{
        config.resolve.fallback = {{ fs: false, net: false, tls: false }};
        return config;
    }},
}};

module.exports = nextConfig;
"""
        with open(output_dir / "next.config.js", 'w', encoding='utf-8') as f:
            f.write(config)

    def _generate_package_json(self, output_dir: Path, project: FrontendProject):
        """Génère package.json"""
        package = {
            "name": project.name.lower().replace(" ", "-"),
            "version": "0.1.0",
            "private": True,
            "scripts": {
                "dev": "next dev",
                "build": "next build",
                "start": "next start",
                "lint": "next lint"
            },
            "dependencies": {
                "next": "13.4.0",
                "react": "18.2.0",
                "react-dom": "18.2.0",
                "ethers": "5.7.2",
                "@rainbow-me/rainbowkit": "0.12.0",
                "wagmi": "1.3.0",
                "viem": "1.10.0",
                "next-auth": "4.22.0",
                "apexcharts": "3.45.0",
                "react-apexcharts": "1.4.1"
            },
            "devDependencies": {
                "@types/node": "20.0.0",
                "@types/react": "18.2.0",
                "@types/react-dom": "18.2.0",
                "typescript": "5.0.0",
                "tailwindcss": "3.3.0",
                "autoprefixer": "10.4.0",
                "postcss": "8.4.0"
            }
        }

        with open(output_dir / "package.json", 'w', encoding='utf-8') as f:
            json.dump(package, f, indent=2)

    def _generate_wagmi_config(self, output_dir: Path, project: FrontendProject):
        """Génère la configuration wagmi"""
        config = f"""import {{ getDefaultWallets }} from '@rainbow-me/rainbowkit';
import {{ configureChains, createConfig }} from 'wagmi';
import {{ mainnet, polygon, optimism, arbitrum }} from 'wagmi/chains';
import {{ publicProvider }} from 'wagmi/providers/public';

const {{ chains, publicClient }} = configureChains(
    [mainnet, polygon, optimism, arbitrum],
    [publicProvider()]
);

const {{ connectors }} = getDefaultWallets({{
    appName: '{project.name}',
    projectId: process.env.NEXT_PUBLIC_WALLETCONNECT_PROJECT_ID || 'demo',
    chains
}});

export const config = createConfig({{
    autoConnect: true,
    connectors,
    publicClient
}});

export {{ chains }};
"""
        with open(output_dir / "lib" / "wagmi.ts", 'w', encoding='utf-8') as f:
            f.write(config)

    def _generate_layout(self, output_dir: Path, project: FrontendProject):
        """Génère le layout principal"""
        layout = f"""import './globals.css';
import '@rainbow-me/rainbowkit/styles.css';
import {{ RainbowKitProvider }} from '@rainbow-me/rainbowkit';
import {{ WagmiConfig }} from 'wagmi';
import {{ config, chains }} from '@/lib/wagmi';

export const metadata = {{
    title: '{project.name}',
    description: 'Web3 DApp generated by SmartContractDevPipeline',
}};

export default function RootLayout({{
    children,
}}: {{
    children: React.ReactNode;
}}) {{
    return (
        <html lang="en">
            <body>
                <WagmiConfig config={{config}}>
                    <RainbowKitProvider chains={{chains}}>
                        {{children}}
                    </RainbowKitProvider>
                </WagmiConfig>
            </body>
        </html>
    );
}}
"""
        with open(output_dir / "app" / "layout.tsx", 'w', encoding='utf-8') as f:
            f.write(layout)

    async def _generate_component(self,
                                 project: FrontendProject,
                                 component_type: ComponentType,
                                 output_dir: Path):
        """Génère un composant spécifique - Version 2.0"""
        
        # Mapping des composants vers leurs générateurs
        generators = {
            # Composants 2.0
            ComponentType.BANKING_DASHBOARD_2_0: self._generate_banking_dashboard_2_0,
            ComponentType.VIRTUAL_CARDS: self._generate_virtual_cards,
            ComponentType.SAVINGS_PODS: self._generate_savings_pods,
            ComponentType.CREDIT_SCORING: self._generate_credit_scoring,
            ComponentType.NFT_LENDING: self._generate_nft_lending,
            ComponentType.LENDING_MARKETPLACE_2_0: self._generate_lending_marketplace_2_0,
            ComponentType.GASLESS_INTERFACE: self._generate_gasless_interface,
            ComponentType.SOCIAL_RECOVERY: self._generate_social_recovery,
            ComponentType.PASSKEY_AUTH: self._generate_passkey_auth,
            ComponentType.DEFI_COMPOSER: self._generate_defi_composer,
            ComponentType.BRIDGE: self._generate_bridge_page_2_0,
            
            # Composants existants (stubs)
            ComponentType.MINT_PAGE: self._generate_mint_page,
            ComponentType.DASHBOARD: self._generate_dashboard,
            ComponentType.NFT_GALLERY: self._generate_nft_gallery,
            ComponentType.TOKEN_TRANSFER: self._generate_token_transfer,
            ComponentType.STAKING: self._generate_staking_page,
            ComponentType.GOVERNANCE: self._generate_governance_page,
            ComponentType.SWAP: self._generate_swap_page,
            ComponentType.ANALYTICS: self._generate_analytics_page,
            ComponentType.PROFILE: self._generate_profile_page,
            ComponentType.AUCTION: self._generate_auction_page,
            ComponentType.LENDING: self._generate_lending_page,
            ComponentType.MULTISIG: self._generate_multisig_page,
            ComponentType.AIRDROP: self._generate_airdrop_page,
            ComponentType.MARKETPLACE: self._generate_marketplace_page,
        }

        generator = generators.get(component_type)
        if generator:
            await generator(project, output_dir)
            project.components.append({"type": component_type.value, "path": f"app/{component_type.value}"})
            self._components_generated += 1

    # ============================================================================
    # MÉTHODES DE GÉNÉRATION DES COMPOSANTS 2.0 (Vos templates existants)
    # ============================================================================

    async def _generate_banking_dashboard_2_0(self, project: FrontendProject, output_dir: Path):
        """Génère le dashboard bancaire nouvelle génération"""
        template = self._templates_2_0.get("banking_dashboard_2_0", "")
        
        # Remplacer les variables
        template = template.replace("{{BANK_NAME}}", project.name)
        template = template.replace("{{USER_NAME}}", "Thomas")
        template = template.replace("{{USER_INITIALS}}", "TD")
        template = template.replace("{{TOTAL_BALANCE}}", "45,890")
        template = template.replace("{{BALANCE_CHANGE}}", "2.4")
        template = template.replace("{{ETH_BALANCE}}", "12.5")
        template = template.replace("{{BTC_BALANCE}}", "0.45")
        template = template.replace("{{DATE}}", datetime.now().strftime("%d %B %Y"))
        
        colors = self._frontend_config.get("colors", {})
        template = template.replace("{{PRIMARY_COLOR}}", colors.get("primary", "#3b82f6"))
        template = template.replace("{{SECONDARY_COLOR}}", colors.get("secondary", "#10b981"))
        template = template.replace("{{ACCENT_COLOR}}", colors.get("accent", "#8b5cf6"))
        
        component_dir = output_dir / "app" / "banking"
        component_dir.mkdir(exist_ok=True)
        
        with open(component_dir / "page.tsx", 'w', encoding='utf-8') as f:
            f.write(f'''"use client";

import {{ useAccount }} from 'wagmi';
import {{ useEffect, useState }} from 'react';

export default function BankingDashboard() {{
    const {{ address, isConnected }} = useAccount();
    
    return (
        <>
        {template}
        </>
    );
}}
''')

    async def _generate_virtual_cards(self, project: FrontendProject, output_dir: Path):
        """Génère la page de gestion de cartes virtuelles"""
        template = self._templates_2_0.get("virtual_cards", "")
        component_dir = output_dir / "app" / "cards"
        component_dir.mkdir(exist_ok=True)
        
        with open(component_dir / "page.tsx", 'w', encoding='utf-8') as f:
            f.write(f'''"use client";

export default function VirtualCards() {{
    return (
        <>
        {template}
        </>
    );
}}
''')

    async def _generate_savings_pods(self, project: FrontendProject, output_dir: Path):
        """Génère la page des pockets d'épargne"""
        template = self._templates_2_0.get("savings_pods", "")
        component_dir = output_dir / "app" / "savings"
        component_dir.mkdir(exist_ok=True)
        
        with open(component_dir / "page.tsx", 'w', encoding='utf-8') as f:
            f.write(f'''"use client";

export default function SavingsPods() {{
    return (
        <>
        {template}
        </>
    );
}}
''')

    async def _generate_credit_scoring(self, project: FrontendProject, output_dir: Path):
        """Génère la page de score de crédit"""
        template = self._templates_2_0.get("credit_scoring", "")
        template = template.replace("{{PROJECT_NAME}}", project.name)
        
        component_dir = output_dir / "app" / "credit-score"
        component_dir.mkdir(exist_ok=True)
        
        with open(component_dir / "page.tsx", 'w', encoding='utf-8') as f:
            f.write(f'''"use client";

export default function CreditScore() {{
    return (
        <>
        {template}
        </>
    );
}}
''')

    async def _generate_nft_lending(self, project: FrontendProject, output_dir: Path):
        """Génère la page de NFT lending"""
        template = self._templates_2_0.get("nft_lending", "")
        template = template.replace("{{PROJECT_NAME}}", project.name)
        
        component_dir = output_dir / "app" / "nft-lending"
        component_dir.mkdir(exist_ok=True)
        
        with open(component_dir / "page.tsx", 'w', encoding='utf-8') as f:
            f.write(f'''"use client";

export default function NFTLending() {{
    return (
        <>
        {template}
        </>
    );
}}
''')

    async def _generate_lending_marketplace_2_0(self, project: FrontendProject, output_dir: Path):
        """Génère la marketplace de prêts"""
        template = self._templates_2_0.get("lending_marketplace_2_0", "")
        template = template.replace("{{PROTOCOL_NAME}}", f"{project.name} Lending")
        template = template.replace("{{TVL}}", "45.2")
        template = template.replace("{{LOAN_VOLUME}}", "28.5")
        template = template.replace("{{VOLUME_CHANGE}}", "12.3")
        template = template.replace("{{LENDERS}}", "1,234")
        template = template.replace("{{BORROWERS}}", "856")
        template = template.replace("{{AVG_RATE}}", "4.8")
        
        component_dir = output_dir / "app" / "lending"
        component_dir.mkdir(exist_ok=True)
        
        with open(component_dir / "page.tsx", 'w', encoding='utf-8') as f:
            f.write(f'''"use client";

export default function LendingMarketplace() {{
    return (
        <>
        {template}
        </>
    );
}}
''')

    async def _generate_gasless_interface(self, project: FrontendProject, output_dir: Path):
        """Génère le composant gasless"""
        template = self._templates_2_0.get("gasless_interface", "")
        component_dir = output_dir / "components" / "gasless"
        component_dir.mkdir(parents=True, exist_ok=True)
        
        with open(component_dir / "GaslessTransaction.tsx", 'w', encoding='utf-8') as f:
            f.write(f'''"use client";

import {{ useState }} from 'react';

export default function GaslessTransaction() {{
    return (
        <>
        {template}
        </>
    );
}}
''')

    async def _generate_social_recovery(self, project: FrontendProject, output_dir: Path):
        """Génère le composant social recovery"""
        template = self._templates_2_0.get("social_recovery", "")
        component_dir = output_dir / "components" / "security"
        component_dir.mkdir(parents=True, exist_ok=True)
        
        with open(component_dir / "SocialRecovery.tsx", 'w', encoding='utf-8') as f:
            f.write(f'''"use client";

export default function SocialRecovery() {{
    return (
        <>
        {template}
        </>
    );
}}
''')

    async def _generate_passkey_auth(self, project: FrontendProject, output_dir: Path):
        """Génère le composant d'authentification biométrique"""
        template = self._templates_2_0.get("passkey_auth", "")
        component_dir = output_dir / "components" / "auth"
        component_dir.mkdir(parents=True, exist_ok=True)
        
        with open(component_dir / "PasskeyAuth.tsx", 'w', encoding='utf-8') as f:
            f.write(f'''"use client";

export default function PasskeyAuth() {{
    return (
        <>
        {template}
        </>
    );
}}
''')

    async def _generate_defi_composer(self, project: FrontendProject, output_dir: Path):
        """Génère le composant DeFi composer"""
        template = self._templates_2_0.get("defi_composer", "")
        component_dir = output_dir / "app" / "composer"
        component_dir.mkdir(exist_ok=True)
        
        with open(component_dir / "page.tsx", 'w', encoding='utf-8') as f:
            f.write(f'''"use client";

export default function DeFiComposer() {{
    return (
        <>
        {template}
        </>
    );
}}
''')

    async def _generate_bridge_page_2_0(self, project: FrontendProject, output_dir: Path):
        """Génère la page de bridge"""
        template = self._templates_2_0.get("bridge_page", "")
        template = template.replace("{{PROJECT_NAME}}", project.name)
        
        component_dir = output_dir / "app" / "bridge"
        component_dir.mkdir(exist_ok=True)
        
        with open(component_dir / "page.tsx", 'w', encoding='utf-8') as f:
            f.write(f'''"use client";

export default function Bridge() {{
    return (
        <>
        {template}
        </>
    );
}}
''')

    # ============================================================================
    # MÉTHODES EXISTANTES (STUBS POUR COMPOSANTS EXISTANTS)
    # ============================================================================

    async def _generate_mint_page(self, project: FrontendProject, output_dir: Path):
        """Génère une page de mint NFT"""
        pass

    async def _generate_dashboard(self, project: FrontendProject, output_dir: Path):
        """Génère un dashboard DeFi"""
        pass

    async def _generate_nft_gallery(self, project: FrontendProject, output_dir: Path):
        """Génère une galerie NFT"""
        pass

    async def _generate_token_transfer(self, project: FrontendProject, output_dir: Path):
        """Génère une page de transfert"""
        pass

    async def _generate_staking_page(self, project: FrontendProject, output_dir: Path):
        """Génère une page de staking"""
        pass

    async def _generate_governance_page(self, project: FrontendProject, output_dir: Path):
        """Génère une page de gouvernance"""
        pass

    async def _generate_swap_page(self, project: FrontendProject, output_dir: Path):
        """Génère une page de swap"""
        pass

    async def _generate_analytics_page(self, project: FrontendProject, output_dir: Path):
        """Génère une page d'analytics"""
        pass

    async def _generate_profile_page(self, project: FrontendProject, output_dir: Path):
        """Génère une page de profil"""
        pass

    async def _generate_auction_page(self, project: FrontendProject, output_dir: Path):
        """Génère une page d'enchères"""
        pass

    async def _generate_lending_page(self, project: FrontendProject, output_dir: Path):
        """Génère une page de lending"""
        await self._generate_lending_marketplace_2_0(project, output_dir)

    async def _generate_multisig_page(self, project: FrontendProject, output_dir: Path):
        """Génère une page multisig"""
        pass

    async def _generate_airdrop_page(self, project: FrontendProject, output_dir: Path):
        """Génère une page d'airdrop"""
        pass

    async def _generate_marketplace_page(self, project: FrontendProject, output_dir: Path):
        """Génère une page marketplace"""
        await self._generate_nft_gallery(project, output_dir)

    # ============================================================================
    # TEMPLATES 2.0 - BANKING CORE (Vos templates existants, préservés)
    # ============================================================================

    def _create_banking_dashboard_2_0(self) -> str:
        """Template bancaire nouvelle génération"""
        return '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>{{BANK_NAME}} • Banking Web3</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://cdn.jsdelivr.net/npm/apexcharts"></script>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
        * { font-family: 'Inter', sans-serif; }
        .glass { 
            background: rgba(15, 25, 35, 0.8);
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
            border: 1px solid rgba(255, 255, 255, 0.05);
        }
        .glass-card {
            background: linear-gradient(145deg, rgba(20, 30, 45, 0.7), rgba(10, 20, 30, 0.9));
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.03);
            border-radius: 28px;
        }
        .neon-glow { box-shadow: 0 0 30px rgba(59, 130, 246, 0.15); }
        .animated-gradient {
            background: linear-gradient(45deg, {{PRIMARY_COLOR}}80, {{SECONDARY_COLOR}}80, {{ACCENT_COLOR}}80);
            background-size: 200% 200%;
            animation: gradient 15s ease infinite;
        }
        @keyframes gradient {
            0% { background-position: 0% 50%; }
            50% { background-position: 100% 50%; }
            100% { background-position: 0% 50%; }
        }
        .virtual-card {
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }
        .virtual-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 20px 40px rgba(0,0,0,0.3);
        }
    </style>
</head>
<body class="bg-[#0A0F1A] text-white antialiased">
    <div class="min-h-screen">
        <!-- Top Navigation -->
        <div class="glass fixed top-0 left-0 right-0 z-50 px-6 py-4">
            <div class="max-w-7xl mx-auto flex justify-between items-center">
                <div class="flex items-center space-x-8">
                    <h1 class="text-2xl font-bold bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">
                        {{BANK_NAME}}
                    </h1>
                    <span class="px-3 py-1 bg-blue-500/20 text-blue-300 rounded-full text-xs font-medium">
                        ⚡ Web3 Banking
                    </span>
                </div>
                <div class="flex items-center space-x-6">
                    <!-- Voice Command -->
                    <button class="p-2 hover:bg-white/10 rounded-full transition" onclick="toggleVoice()">
                        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                                  d="M12 18.75a6 6 0 006-6v-1.5m-6 7.5a6 6 0 01-6-6v-1.5m6 7.5v3.75m-3.75 0h7.5M12 15.75a3 3 0 01-3-3V4.5a3 3 0 116 0v8.25a3 3 0 01-3 3z"></path>
                        </svg>
                    </button>
                    <!-- Biometric Auth -->
                    <button class="p-2 bg-gradient-to-r from-blue-500 to-purple-500 rounded-full">
                        <svg class="w-5 h-5" fill="none" stroke="white" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                                  d="M16.5 10.5V6.75a4.5 4.5 0 10-9 0v3.75m-.75 11.25h10.5a2.25 2.25 0 002.25-2.25v-6.75a2.25 2.25 0 00-2.25-2.25H6.75a2.25 2.25 0 00-2.25 2.25v6.75a2.25 2.25 0 002.25 2.25z"></path>
                        </svg>
                    </button>
                    <!-- Avatar -->
                    <div class="w-10 h-10 bg-gradient-to-r from-blue-500 to-purple-500 rounded-full flex items-center justify-center">
                        <span class="text-sm font-bold">{{USER_INITIALS}}</span>
                    </div>
                </div>
            </div>
        </div>

        <!-- Main Dashboard -->
        <div class="max-w-7xl mx-auto pt-24 px-6 pb-12">
            <!-- Welcome + Balance -->
            <div class="flex justify-between items-start mb-8">
                <div>
                    <h2 class="text-3xl font-bold">Bonjour, {{USER_NAME}} 👋</h2>
                    <p class="text-gray-400 mt-2">{{DATE}} • Dernière connexion il y a 2 min</p>
                </div>
                <div class="flex space-x-3">
                    <span class="px-4 py-2 bg-green-500/10 text-green-400 rounded-full text-sm flex items-center">
                        <span class="w-2 h-2 bg-green-500 rounded-full mr-2 animate-pulse"></span>
                        Wallet Connecté
                    </span>
                </div>
            </div>

            <!-- Balance Cards -->
            <div class="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
                <div class="glass-card p-6 neon-glow col-span-2">
                    <div class="flex justify-between items-start">
                        <div>
                            <p class="text-sm text-gray-400 mb-2">Solde Total</p>
                            <div class="flex items-end space-x-2">
                                <span class="text-4xl font-bold">${{TOTAL_BALANCE}}</span>
                                <span class="text-sm text-green-400 mb-1">+{{BALANCE_CHANGE}}%</span>
                            </div>
                            <div class="flex items-center mt-4 space-x-4">
                                <span class="text-xs text-gray-400">≈ {{ETH_BALANCE}} ETH</span>
                                <span class="text-xs text-gray-400">• ≈ {{BTC_BALANCE}} BTC</span>
                            </div>
                        </div>
                        <div class="flex space-x-2">
                            <button class="px-4 py-2 bg-blue-600 rounded-xl hover:bg-blue-700 transition">
                                Dépôt
                            </button>
                            <button class="px-4 py-2 bg-gray-700 rounded-xl hover:bg-gray-600 transition">
                                Retrait
                            </button>
                        </div>
                    </div>
                    <div class="mt-6 h-16" id="miniSparkline"></div>
                </div>
                
                <!-- Quick Actions -->
                <div class="glass-card p-6">
                    <h3 class="font-semibold mb-4">Actions rapides</h3>
                    <div class="grid grid-cols-2 gap-3">
                        <button class="p-3 bg-white/5 rounded-xl hover:bg-white/10 transition">
                            <span class="text-2xl mb-1 block">💳</span>
                            <span class="text-xs">Payer</span>
                        </button>
                        <button class="p-3 bg-white/5 rounded-xl hover:bg-white/10 transition">
                            <span class="text-2xl mb-1 block">📤</span>
                            <span class="text-xs">Envoyer</span>
                        </button>
                        <button class="p-3 bg-white/5 rounded-xl hover:bg-white/10 transition">
                            <span class="text-2xl mb-1 block">💰</span>
                            <span class="text-xs">Épargner</span>
                        </button>
                        <button class="p-3 bg-white/5 rounded-xl hover:bg-white/10 transition">
                            <span class="text-2xl mb-1 block">🔄</span>
                            <span class="text-xs">Swap</span>
                        </button>
                    </div>
                </div>
            </div>

            <!-- Virtual Cards -->
            <div class="mb-8">
                <div class="flex justify-between items-center mb-4">
                    <h3 class="text-xl font-bold">Cartes virtuelles</h3>
                    <button class="text-sm text-blue-400 hover:text-blue-300">+ Nouvelle carte</button>
                </div>
                <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
                    <div class="bg-gradient-to-br from-indigo-900 to-indigo-800 rounded-2xl p-6 virtual-card">
                        <div class="flex justify-between items-start mb-8">
                            <span class="text-xs font-medium opacity-80">💳 Principale</span>
                            <span class="text-xs bg-white/20 px-3 py-1 rounded-full">Web3</span>
                        </div>
                        <div class="mb-6">
                            <span class="text-lg font-mono">•••• •••• •••• 4242</span>
                        </div>
                        <div class="flex justify-between items-center">
                            <div>
                                <p class="text-xs opacity-70">Titulaire</p>
                                <p class="font-medium">{{USER_NAME}}</p>
                            </div>
                            <div>
                                <p class="text-xs opacity-70">Expire</p>
                                <p class="font-medium">12/28</p>
                            </div>
                        </div>
                    </div>
                    <div class="bg-gradient-to-br from-purple-900 to-purple-800 rounded-2xl p-6 virtual-card">
                        <div class="flex justify-between items-start mb-8">
                            <span class="text-xs font-medium opacity-80">🔄 Jetable</span>
                            <span class="text-xs bg-white/20 px-3 py-1 rounded-full">24h</span>
                        </div>
                        <div class="mb-6">
                            <span class="text-lg font-mono">•••• •••• •••• 1234</span>
                        </div>
                        <div class="flex justify-between items-center">
                            <div>
                                <p class="text-xs opacity-70">Titulaire</p>
                                <p class="font-medium">{{USER_NAME}}</p>
                            </div>
                            <div>
                                <p class="text-xs opacity-70">Expire</p>
                                <p class="font-medium">Temporaire</p>
                            </div>
                        </div>
                    </div>
                    <div class="bg-gradient-to-br from-blue-900 to-blue-800 rounded-2xl p-6 virtual-card">
                        <div class="flex justify-between items-start mb-8">
                            <span class="text-xs font-medium opacity-80">🌍 Voyage</span>
                            <span class="text-xs bg-white/20 px-3 py-1 rounded-full">0% frais</span>
                        </div>
                        <div class="mb-6">
                            <span class="text-lg font-mono">•••• •••• •••• 5678</span>
                        </div>
                        <div class="flex justify-between items-center">
                            <div>
                                <p class="text-xs opacity-70">Titulaire</p>
                                <p class="font-medium">{{USER_NAME}}</p>
                            </div>
                            <div>
                                <p class="text-xs opacity-70">Expire</p>
                                <p class="font-medium">EUR/USD</p>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Savings Pods -->
            <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
                <div class="glass-card p-6">
                    <div class="flex justify-between items-center mb-4">
                        <h3 class="font-semibold">Pockets d'épargne</h3>
                        <button class="text-xs text-blue-400">+ Nouveau</button>
                    </div>
                    <div class="space-y-4">
                        <div class="flex justify-between items-center">
                            <div class="flex items-center space-x-3">
                                <div class="w-8 h-8 bg-blue-500/20 rounded-lg flex items-center justify-center">
                                    🏠
                                </div>
                                <div>
                                    <p class="text-sm font-medium">Projet Maison</p>
                                    <p class="text-xs text-gray-400">Objectif 50k €</p>
                                </div>
                            </div>
                            <div class="text-right">
                                <p class="text-sm font-bold">12,450 €</p>
                                <p class="text-xs text-green-400">24%</p>
                            </div>
                        </div>
                        <div class="flex justify-between items-center">
                            <div class="flex items-center space-x-3">
                                <div class="w-8 h-8 bg-purple-500/20 rounded-lg flex items-center justify-center">
                                    ✈️
                                </div>
                                <div>
                                    <p class="text-sm font-medium">Voyage Japon</p>
                                    <p class="text-xs text-gray-400">Objectif 3k €</p>
                                </div>
                            </div>
                            <div class="text-right">
                                <p class="text-sm font-bold">2,150 €</p>
                                <p class="text-xs text-green-400">72%</p>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Round-up Savings -->
                <div class="glass-card p-6">
                    <div class="flex items-center justify-between mb-4">
                        <div>
                            <h3 class="font-semibold">Arrondi automatique</h3>
                            <p class="text-xs text-gray-400 mt-1">Épargne 1.234 € ce mois-ci</p>
                        </div>
                        <label class="relative inline-flex items-center cursor-pointer">
                            <input type="checkbox" class="sr-only peer" checked>
                            <div class="w-11 h-6 bg-gray-700 rounded-full peer peer-checked:bg-blue-600"></div>
                        </label>
                    </div>
                    <div class="flex justify-between items-center p-3 bg-white/5 rounded-xl">
                        <span class="text-sm">Multiplicateur</span>
                        <div class="flex space-x-2">
                            <button class="px-3 py-1 bg-blue-600 rounded-lg text-sm">2x</button>
                            <button class="px-3 py-1 bg-white/10 rounded-lg text-sm">4x</button>
                            <button class="px-3 py-1 bg-white/10 rounded-lg text-sm">10x</button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script>
        // Sparkline Chart
        var options = {
            series: [{ data: [31, 40, 28, 51, 42, 109, 100] }],
            chart: { type: 'area', height: 60, sparkline: { enabled: true } },
            stroke: { curve: 'smooth', width: 2 },
            colors: ['#3b82f6']
        };
        if(document.getElementById("miniSparkline")) {
            new ApexCharts(document.querySelector("#miniSparkline"), options).render();
        }

        // Voice Commands
        function toggleVoice() {
            alert("🎤 Voice command: 'Send 50€ to Marc'");
        }

        // Haptic Feedback
        document.querySelectorAll('button').forEach(btn => {
            btn.addEventListener('click', () => {
                if (window.navigator.vibrate) window.navigator.vibrate(50);
            });
        });
    </script>
</body>
</html>'''

    def _create_virtual_cards(self) -> str:
        """Template de gestion de cartes virtuelles"""
        return self._create_banking_dashboard_2_0()

    def _create_savings_pods(self) -> str:
        """Template de pockets d'épargne"""
        return self._create_banking_dashboard_2_0()

    def _create_round_up_savings(self) -> str:
        """Template d'arrondi automatique"""
        return self._create_banking_dashboard_2_0()

    def _create_spending_insights(self) -> str:
        """Template d'analyse des dépenses"""
        return self._create_banking_dashboard_2_0()

    def _create_budget_forecast(self) -> str:
        """Template de prévisions budgétaires"""
        return self._create_banking_dashboard_2_0()

    def _create_bill_splitting(self) -> str:
        """Template de partage de factures"""
        return self._create_banking_dashboard_2_0()

    def _create_direct_debit(self) -> str:
        """Template de prélèvements automatiques"""
        return self._create_banking_dashboard_2_0()

    def _create_lending_marketplace_2_0(self) -> str:
        """Template de marketplace de prêts P2P"""
        return '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{PROTOCOL_NAME}} • Lending 2.0</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&display=swap');
        * { font-family: 'Space Grotesk', sans-serif; }
        .lending-card {
            background: linear-gradient(145deg, #1a1e2a, #0f1219);
            border: 1px solid rgba(255,255,255,0.03);
            border-radius: 24px;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        }
        .lending-card:hover {
            transform: translateY(-4px);
            border-color: rgba(59,130,246,0.3);
            box-shadow: 0 20px 40px -12px rgba(0,0,0,0.5);
        }
        .risk-badge {
            padding: 4px 12px;
            border-radius: 100px;
            font-size: 0.75rem;
            font-weight: 600;
            text-transform: uppercase;
        }
    </style>
</head>
<body class="bg-[#0A0C12] text-white">
    <div class="max-w-7xl mx-auto px-4 py-8">
        <!-- Header -->
        <div class="flex justify-between items-center mb-12">
            <div>
                <h1 class="text-4xl font-bold mb-2">{{PROTOCOL_NAME}}</h1>
                <p class="text-gray-400">Lending & Borrowing • Cross-chain • {{TVL}}M TVL</p>
            </div>
            <div class="flex space-x-4">
                <button class="px-6 py-3 bg-gradient-to-r from-blue-600 to-blue-700 rounded-xl font-medium">
                    + Créer une offre
                </button>
                <button class="px-6 py-3 bg-gray-800 rounded-xl font-medium hover:bg-gray-700">
                    Emprunter
                </button>
            </div>
        </div>

        <!-- Market Overview -->
        <div class="grid grid-cols-1 md:grid-cols-4 gap-6 mb-12">
            <div class="lending-card p-6">
                <p class="text-sm text-gray-400 mb-2">Volume total prêts</p>
                <p class="text-2xl font-bold">${{LOAN_VOLUME}}M</p>
                <p class="text-xs text-green-400 mt-1">+{{VOLUME_CHANGE}}%</p>
            </div>
            <div class="lending-card p-6">
                <p class="text-sm text-gray-400 mb-2">Prêteurs actifs</p>
                <p class="text-2xl font-bold">{{LENDERS}}</p>
            </div>
            <div class="lending-card p-6">
                <p class="text-sm text-gray-400 mb-2">Emprunteurs</p>
                <p class="text-2xl font-bold">{{BORROWERS}}</p>
            </div>
            <div class="lending-card p-6">
                <p class="text-sm text-gray-400 mb-2">Taux moyen</p>
                <p class="text-2xl font-bold">{{AVG_RATE}}%</p>
            </div>
        </div>

        <!-- Active Loans Marketplace -->
        <h2 class="text-2xl font-bold mb-6">🏆 Offres de prêts disponibles</h2>
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            <div class="lending-card p-6">
                <div class="flex justify-between items-start mb-4">
                    <div>
                        <span class="text-xl font-bold">10,000 USDC</span>
                        <p class="text-xs text-gray-400">Prêt personnel</p>
                    </div>
                    <span class="risk-badge bg-green-500/20 text-green-400">Faible</span>
                </div>
                <div class="space-y-3 mb-6">
                    <div class="flex justify-between text-sm">
                        <span class="text-gray-400">Taux</span>
                        <span class="font-medium text-green-400">4.2% APY</span>
                    </div>
                    <div class="flex justify-between text-sm">
                        <span class="text-gray-400">Durée</span>
                        <span>90 jours</span>
                    </div>
                    <div class="flex justify-between text-sm">
                        <span class="text-gray-400">Score</span>
                        <span>720</span>
                    </div>
                </div>
                <div class="flex space-x-3">
                    <button class="flex-1 px-4 py-2 bg-blue-600 rounded-lg hover:bg-blue-700 transition">
                        Financer
                    </button>
                    <button class="px-4 py-2 bg-gray-700 rounded-lg hover:bg-gray-600 transition">
                        Détails
                    </button>
                </div>
            </div>
            <div class="lending-card p-6">
                <div class="flex justify-between items-start mb-4">
                    <div>
                        <span class="text-xl font-bold">5 ETH</span>
                        <p class="text-xs text-gray-400">Prêt collatéralisé</p>
                    </div>
                    <span class="risk-badge bg-yellow-500/20 text-yellow-400">Moyen</span>
                </div>
                <div class="space-y-3 mb-6">
                    <div class="flex justify-between text-sm">
                        <span class="text-gray-400">Taux</span>
                        <span class="font-medium text-green-400">3.8% APY</span>
                    </div>
                    <div class="flex justify-between text-sm">
                        <span class="text-gray-400">LTV</span>
                        <span>65%</span>
                    </div>
                    <div class="flex justify-between text-sm">
                        <span class="text-gray-400">Durée</span>
                        <span>180 jours</span>
                    </div>
                </div>
                <div class="flex space-x-3">
                    <button class="flex-1 px-4 py-2 bg-blue-600 rounded-lg hover:bg-blue-700 transition">
                        Financer
                    </button>
                    <button class="px-4 py-2 bg-gray-700 rounded-lg hover:bg-gray-600 transition">
                        Détails
                    </button>
                </div>
            </div>
            <div class="lending-card p-6">
                <div class="flex justify-between items-start mb-4">
                    <div>
                        <span class="text-xl font-bold">50,000 DAI</span>
                        <p class="text-xs text-gray-400">Prêt entreprise</p>
                    </div>
                    <span class="risk-badge bg-blue-500/20 text-blue-400">Stable</span>
                </div>
                <div class="space-y-3 mb-6">
                    <div class="flex justify-between text-sm">
                        <span class="text-gray-400">Taux</span>
                        <span class="font-medium text-green-400">5.1% APY</span>
                    </div>
                    <div class="flex justify-between text-sm">
                        <span class="text-gray-400">Durée</span>
                        <span>365 jours</span>
                    </div>
                    <div class="flex justify-between text-sm">
                        <span class="text-gray-400">Garantie</span>
                        <span>120%</span>
                    </div>
                </div>
                <div class="flex space-x-3">
                    <button class="flex-1 px-4 py-2 bg-blue-600 rounded-lg hover:bg-blue-700 transition">
                        Financer
                    </button>
                    <button class="px-4 py-2 bg-gray-700 rounded-lg hover:bg-gray-600 transition">
                        Détails
                    </button>
                </div>
            </div>
        </div>

        <!-- Liquidation Guard -->
        <div class="mt-12 lending-card p-6 bg-gradient-to-r from-yellow-900/30 to-red-900/30 border border-yellow-500/30">
            <div class="flex items-center justify-between">
                <div class="flex items-center space-x-4">
                    <div class="w-12 h-12 bg-yellow-500/20 rounded-full flex items-center justify-center">
                        🛡️
                    </div>
                    <div>
                        <h3 class="text-lg font-bold">Liquidation Guard</h3>
                        <p class="text-sm text-gray-300">Vos positions sont surveillées en temps réel</p>
                    </div>
                </div>
                <div class="flex items-center space-x-6">
                    <div>
                        <p class="text-xs text-gray-400">Niveau de risque</p>
                        <p class="text-lg font-bold text-green-400">24% LTV</p>
                    </div>
                    <button class="px-6 py-2 bg-yellow-600 rounded-lg hover:bg-yellow-700">
                        Ajouter du collatéral
                    </button>
                </div>
            </div>
        </div>
    </div>
</body>
</html>'''

    def _create_bridge_page_2_0(self) -> str:
        """Template de bridge cross-chain"""
        return '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Bridge • {{PROJECT_NAME}}</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        .gradient-bg {
            background: linear-gradient(135deg, {{PRIMARY_COLOR}} 0%, {{ACCENT_COLOR}} 100%);
        }
    </style>
</head>
<body class="bg-[#0A0C12] text-white">
    <div class="min-h-screen flex items-center justify-center p-4">
        <div class="max-w-2xl w-full bg-gray-800/50 rounded-3xl p-8 border border-gray-700">
            <h1 class="text-3xl font-bold mb-2">Cross-Chain Bridge</h1>
            <p class="text-gray-400 mb-8">Transfer assets seamlessly between networks</p>
            
            <!-- Network Selection -->
            <div class="grid grid-cols-2 gap-4 mb-6">
                <div class="bg-gray-900/50 rounded-2xl p-4 border border-gray-700">
                    <label class="block text-sm text-gray-400 mb-2">From</label>
                    <select class="w-full bg-gray-800 rounded-xl px-4 py-3 border border-gray-600">
                        <option>Ethereum</option>
                        <option>Polygon</option>
                        <option>Arbitrum</option>
                        <option>Optimism</option>
                        <option>Base</option>
                    </select>
                </div>
                <div class="bg-gray-900/50 rounded-2xl p-4 border border-gray-700">
                    <label class="block text-sm text-gray-400 mb-2">To</label>
                    <select class="w-full bg-gray-800 rounded-xl px-4 py-3 border border-gray-600">
                        <option>Polygon</option>
                        <option>Ethereum</option>
                        <option>Arbitrum</option>
                        <option>Optimism</option>
                        <option>Base</option>
                    </select>
                </div>
            </div>

            <!-- Token & Amount -->
            <div class="bg-gray-900/50 rounded-2xl p-4 border border-gray-700 mb-6">
                <div class="flex justify-between mb-2">
                    <label class="text-sm text-gray-400">Token</label>
                    <span class="text-sm text-gray-400">Balance: {{BALANCE}}</span>
                </div>
                <div class="flex space-x-3">
                    <input type="number" placeholder="0.0" 
                           class="flex-1 bg-gray-800 text-2xl outline-none px-4 py-3 rounded-xl border border-gray-600">
                    <select class="bg-gray-800 rounded-xl px-6 py-3 border border-gray-600">
                        <option>ETH</option>
                        <option>USDC</option>
                        <option>DAI</option>
                    </select>
                </div>
            </div>

            <!-- Bridge Info -->
            <div class="bg-gray-900/30 rounded-xl p-4 text-sm mb-6">
                <div class="flex justify-between mb-2">
                    <span class="text-gray-400">Estimated time</span>
                    <span>≈ 10-15 minutes</span>
                </div>
                <div class="flex justify-between mb-2">
                    <span class="text-gray-400">Bridge fee</span>
                    <span>0.1% (≈ $2.50)</span>
                </div>
                <div class="flex justify-between">
                    <span class="text-gray-400">You will receive</span>
                    <span class="text-green-400 font-bold">1.998 ETH</span>
                </div>
            </div>

            <!-- Bridge Button -->
            <button class="w-full gradient-bg text-white font-bold py-4 px-6 rounded-xl 
                         hover:opacity-90 transition transform hover:scale-[1.02]">
                Bridge Tokens
            </button>

            <!-- Recent Transactions -->
            <div class="mt-8">
                <h3 class="text-lg font-bold mb-4">Recent Transactions</h3>
                <div class="space-y-3">
                    <div class="flex justify-between items-center bg-gray-900/30 rounded-xl p-4">
                        <div>
                            <p class="font-medium">Bridge 5 ETH → Polygon</p>
                            <p class="text-sm text-gray-400">2 minutes ago</p>
                        </div>
                        <span class="px-3 py-1 bg-green-500/20 text-green-400 rounded-full text-sm">Completed</span>
                    </div>
                    <div class="flex justify-between items-center bg-gray-900/30 rounded-xl p-4">
                        <div>
                            <p class="font-medium">Bridge 1,000 USDC → Arbitrum</p>
                            <p class="text-sm text-gray-400">15 minutes ago</p>
                        </div>
                        <span class="px-3 py-1 bg-yellow-500/20 text-yellow-400 rounded-full text-sm">Processing</span>
                    </div>
                </div>
            </div>
        </div>
    </div>
</body>
</html>'''

    def _create_collateral_management(self) -> str:
        """Template de gestion de collatéral"""
        return self._create_lending_marketplace_2_0()

    def _create_liquidation_guard(self) -> str:
        """Template de protection contre la liquidation"""
        return self._create_lending_marketplace_2_0()

    def _create_yield_optimizer(self) -> str:
        """Template d'optimisation de rendement"""
        return self._create_lending_marketplace_2_0()

    def _create_loan_builder(self) -> str:
        """Template de constructeur de prêts"""
        return self._create_lending_marketplace_2_0()

    def _create_gasless_interface(self) -> str:
        """Template de transactions gasless"""
        return '''<div class="fixed bottom-8 left-8 glass rounded-2xl p-4 w-96">
            <div class="flex items-center justify-between mb-4">
                <h4 class="font-semibold">⚡ Gasless Transaction</h4>
                <span class="px-2 py-1 bg-green-500/20 text-green-400 rounded-full text-xs">Beta</span>
            </div>
            <div class="flex items-center space-x-3 mb-4">
                <div class="flex-1 p-3 bg-white/5 rounded-xl">
                    <span class="text-sm text-gray-400">Frais de gas</span>
                    <p class="text-lg font-bold text-green-400">0.00 ETH</p>
                </div>
                <div class="p-3 bg-white/5 rounded-xl">
                    <span class="text-sm text-gray-400">Validateur</span>
                    <p class="font-medium">Gelato</p>
                </div>
            </div>
            <button class="w-full px-4 py-3 bg-gradient-to-r from-purple-600 to-blue-600 rounded-xl font-medium">
                Sponsoriser la transaction
            </button>
        </div>'''

    def _create_social_recovery(self) -> str:
        """Template de récupération sociale"""
        return '''<div class="glass rounded-2xl p-6">
            <h3 class="text-lg font-bold mb-4">👥 Social Recovery</h3>
            <p class="text-sm text-gray-400 mb-4">Choisis 3 gardiens de confiance</p>
            <div class="space-y-3 mb-6">
                <div class="flex items-center justify-between p-3 bg-white/5 rounded-xl">
                    <div class="flex items-center space-x-3">
                        <div class="w-8 h-8 bg-blue-500 rounded-full"></div>
                        <div>
                            <p class="font-medium">alice.eth</p>
                            <p class="text-xs text-gray-400">Confirmé</p>
                        </div>
                    </div>
                    <span class="text-green-400">✓</span>
                </div>
                <div class="flex items-center justify-between p-3 bg-white/5 rounded-xl">
                    <div class="flex items-center space-x-3">
                        <div class="w-8 h-8 bg-purple-500 rounded-full"></div>
                        <div>
                            <p class="font-medium">bob.eth</p>
                            <p class="text-xs text-gray-400">En attente</p>
                        </div>
                    </div>
                    <span class="text-yellow-400">⏳</span>
                </div>
            </div>
            <button class="w-full px-4 py-2 bg-blue-600 rounded-lg">Configurer recovery</button>
        </div>'''

    def _create_passkey_auth(self) -> str:
        """Template d'authentification biométrique"""
        return '''<div class="glass-card p-6 text-center">
            <div class="w-16 h-16 bg-gradient-to-r from-blue-500 to-purple-500 rounded-full mx-auto mb-4 flex items-center justify-center">
                <svg class="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                          d="M16.5 10.5V6.75a4.5 4.5 0 10-9 0v3.75m-.75 11.25h10.5a2.25 2.25 0 002.25-2.25v-6.75a2.25 2.25 0 00-2.25-2.25H6.75a2.25 2.25 0 00-2.25 2.25v6.75a2.25 2.25 0 002.25 2.25z"></path>
                </svg>
            </div>
            <h3 class="text-xl font-bold mb-2">Passkey Auth</h3>
            <p class="text-sm text-gray-400 mb-6">Connectez-vous avec Face ID ou Touch ID</p>
            <button class="w-full px-4 py-3 bg-blue-600 rounded-xl font-medium hover:bg-blue-700">
                Authentifier
            </button>
        </div>'''

    def _create_defi_composer(self) -> str:
        """Template de composition DeFi no-code"""
        return '''<div class="glass-card p-6">
            <h3 class="text-lg font-bold mb-4">🧩 DeFi Composer</h3>
            <p class="text-sm text-gray-400 mb-6">Glisse et dépose pour créer ta stratégie</p>
            
            <div class="grid grid-cols-2 gap-4 mb-6">
                <div class="p-4 bg-white/5 rounded-xl border border-dashed border-blue-500/50">
                    <span class="text-sm">💰 Deposit</span>
                    <p class="text-xs text-gray-400 mt-1">USDC • 1000$</p>
                </div>
                <div class="p-4 bg-white/5 rounded-xl border border-dashed border-purple-500/50">
                    <span class="text-sm">🏊‍♂️ Stake</span>
                    <p class="text-xs text-gray-400 mt-1">Aave • 3.2% APY</p>
                </div>
                <div class="p-4 bg-white/5 rounded-xl border border-dashed border-green-500/50">
                    <span class="text-sm">🔄 Swap</span>
                    <p class="text-xs text-gray-400 mt-1">ETH → DAI</p>
                </div>
                <div class="p-4 bg-white/5 rounded-xl border border-dashed border-yellow-500/50">
                    <span class="text-sm">⚡ Leverage</span>
                    <p class="text-xs text-gray-400 mt-1">2x • 8.5% APY</p>
                </div>
            </div>
            
            <div class="flex items-center justify-between p-4 bg-gradient-to-r from-blue-600/20 to-purple-600/20 rounded-xl">
                <div>
                    <p class="text-sm font-medium">Rendement estimé</p>
                    <p class="text-2xl font-bold text-green-400">+12.4% APY</p>
                </div>
                <button class="px-6 py-2 bg-blue-600 rounded-lg">
                    Exécuter
                </button>
            </div>
        </div>'''

    def _create_credit_scoring(self) -> str:
        """Template de scoring de crédit"""
        return '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Credit Scoring • {{PROJECT_NAME}}</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        .score-circle {
            transition: stroke-dashoffset 0.5s ease;
        }
        .metric-card {
            background: linear-gradient(145deg, #1a1e2a, #0f1219);
            border: 1px solid rgba(255,255,255,0.03);
            border-radius: 20px;
            transition: all 0.3s ease;
        }
        .metric-card:hover {
            transform: translateY(-4px);
            border-color: rgba(59,130,246,0.3);
        }
    </style>
</head>
<body class="bg-[#0A0C12] text-white">
    <div class="max-w-7xl mx-auto px-4 py-8">
        <!-- Header -->
        <div class="flex justify-between items-center mb-8">
            <div>
                <h1 class="text-3xl font-bold mb-2">Credit Scoring</h1>
                <p class="text-gray-400">On-chain creditworthiness assessment</p>
            </div>
            <div class="flex space-x-3">
                <span class="px-4 py-2 bg-blue-600 rounded-lg">Connect Wallet</span>
            </div>
        </div>

        <!-- Main Score -->
        <div class="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
            <div class="lg:col-span-2 metric-card p-8">
                <div class="flex items-center space-x-8">
                    <!-- Score Circle -->
                    <div class="relative w-32 h-32">
                        <svg class="w-32 h-32 transform -rotate-90">
                            <circle cx="64" cy="64" r="54" stroke="#2d3748" stroke-width="8" fill="none"/>
                            <circle class="score-circle" cx="64" cy="64" r="54" 
                                    stroke="#3b82f6" stroke-width="8" fill="none"
                                    stroke-dasharray="339.292" stroke-dashoffset="101.788"
                                    style="stroke-dashoffset: 101.788px;"/>
                        </svg>
                        <div class="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 text-center">
                            <span class="text-3xl font-bold">702</span>
                            <span class="text-sm text-gray-400 block">/850</span>
                        </div>
                    </div>
                    <!-- Score Info -->
                    <div>
                        <h2 class="text-2xl font-bold mb-2">Good Credit Score</h2>
                        <p class="text-gray-400 mb-2">Last updated: March 10, 2026</p>
                        <div class="flex space-x-2">
                            <span class="px-3 py-1 bg-green-500/20 text-green-400 rounded-full text-sm">+12 pts</span>
                            <span class="px-3 py-1 bg-blue-500/20 text-blue-400 rounded-full text-sm">Top 15%</span>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- Quick Stats -->
            <div class="metric-card p-6">
                <h3 class="text-lg font-bold mb-4">Quick Stats</h3>
                <div class="space-y-4">
                    <div class="flex justify-between">
                        <span class="text-gray-400">Total Transactions</span>
                        <span class="font-bold">847</span>
                    </div>
                    <div class="flex justify-between">
                        <span class="text-gray-400">Volume</span>
                        <span class="font-bold">$124.5K</span>
                    </div>
                    <div class="flex justify-between">
                        <span class="text-gray-400">Active Protocols</span>
                        <span class="font-bold">12</span>
                    </div>
                    <div class="flex justify-between">
                        <span class="text-gray-400">Wallet Age</span>
                        <span class="font-bold">2.3 years</span>
                    </div>
                </div>
            </div>
        </div>

        <!-- Factors Grid -->
        <h2 class="text-2xl font-bold mb-6">Score Factors</h2>
        <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div class="metric-card p-6">
                <div class="flex items-center space-x-3 mb-4">
                    <span class="text-2xl">💰</span>
                    <h3 class="text-lg font-bold">Transaction History</h3>
                </div>
                <div class="space-y-3">
                    <div class="flex justify-between">
                        <span class="text-gray-400">Consistency</span>
                        <span class="text-green-400">High</span>
                    </div>
                    <div class="flex justify-between">
                        <span class="text-gray-400">Volume</span>
                        <span class="text-yellow-400">Medium</span>
                    </div>
                    <div class="flex justify-between">
                        <span class="text-gray-400">Frequency</span>
                        <span class="text-green-400">High</span>
                    </div>
                </div>
            </div>
            <div class="metric-card p-6">
                <div class="flex items-center space-x-3 mb-4">
                    <span class="text-2xl">🏦</span>
                    <h3 class="text-lg font-bold">Protocol Engagement</h3>
                </div>
                <div class="space-y-3">
                    <div class="flex justify-between">
                        <span class="text-gray-400">Lending</span>
                        <span class="text-green-400">Active</span>
                    </div>
                    <div class="flex justify-between">
                        <span class="text-gray-400">DEX Usage</span>
                        <span class="text-green-400">High</span>
                    </div>
                    <div class="flex justify-between">
                        <span class="text-gray-400">Staking</span>
                        <span class="text-yellow-400">Low</span>
                    </div>
                </div>
            </div>
            <div class="metric-card p-6">
                <div class="flex items-center space-x-3 mb-4">
                    <span class="text-2xl">🔒</span>
                    <h3 class="text-lg font-bold">Risk Metrics</h3>
                </div>
                <div class="space-y-3">
                    <div class="flex justify-between">
                        <span class="text-gray-400">Liquidation Risk</span>
                        <span class="text-green-400">0.2%</span>
                    </div>
                    <div class="flex justify-between">
                        <span class="text-gray-400">Health Factor</span>
                        <span class="text-green-400">2.8</span>
                    </div>
                    <div class="flex justify-between">
                        <span class="text-gray-400">Bad Debt</span>
                        <span class="text-green-400">None</span>
                    </div>
                </div>
            </div>
        </div>

        <!-- Recent Activity -->
        <div class="mt-8 metric-card p-6">
            <h3 class="text-lg font-bold mb-4">Recent Activity</h3>
            <div class="space-y-3">
                <div class="flex justify-between items-center py-2 border-b border-gray-800">
                    <div>
                        <p class="font-medium">Deposited 5 ETH into Aave</p>
                        <p class="text-sm text-gray-400">2 hours ago</p>
                    </div>
                    <span class="text-green-400">+15 pts</span>
                </div>
                <div class="flex justify-between items-center py-2 border-b border-gray-800">
                    <div>
                        <p class="font-medium">Repaid 1,000 USDC loan</p>
                        <p class="text-sm text-gray-400">1 day ago</p>
                    </div>
                    <span class="text-green-400">+8 pts</span>
                </div>
                <div class="flex justify-between items-center py-2">
                    <div>
                        <p class="font-medium">Swapped 2 ETH for DAI on Uniswap</p>
                        <p class="text-sm text-gray-400">3 days ago</p>
                    </div>
                    <span class="text-green-400">+5 pts</span>
                </div>
            </div>
        </div>
    </div>
</body>
</html>'''

    def _create_nft_lending(self) -> str:
        """Template de NFT lending"""
        return '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>NFT Lending • {{PROJECT_NAME}}</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        .nft-card {
            background: linear-gradient(145deg, #1a1e2a, #0f1219);
            border: 1px solid rgba(255,255,255,0.03);
            border-radius: 20px;
            transition: all 0.3s ease;
            overflow: hidden;
        }
        .nft-card:hover {
            transform: translateY(-4px);
            border-color: #3b82f6;
            box-shadow: 0 10px 30px -10px #3b82f6;
        }
        .nft-image {
            height: 200px;
            background: linear-gradient(45deg, #2d3748, #1a202c);
            display: flex;
            align-items: center;
            justify-content: center;
        }
    </style>
</head>
<body class="bg-[#0A0C12] text-white">
    <div class="max-w-7xl mx-auto px-4 py-8">
        <!-- Header -->
        <div class="flex justify-between items-center mb-8">
            <div>
                <h1 class="text-3xl font-bold mb-2">NFT Lending</h1>
                <p class="text-gray-400">Borrow against your NFTs or lend to earn yield</p>
            </div>
            <div class="flex space-x-3">
                <button class="px-4 py-2 bg-blue-600 rounded-lg">Lend NFT</button>
                <button class="px-4 py-2 bg-purple-600 rounded-lg">Borrow</button>
            </div>
        </div>

        <!-- Stats -->
        <div class="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
            <div class="nft-card p-4">
                <p class="text-sm text-gray-400">Total Loans</p>
                <p class="text-2xl font-bold">847</p>
            </div>
            <div class="nft-card p-4">
                <p class="text-sm text-gray-400">Volume</p>
                <p class="text-2xl font-bold">2,450 ETH</p>
            </div>
            <div class="nft-card p-4">
                <p class="text-sm text-gray-400">Avg LTV</p>
                <p class="text-2xl font-bold">42%</p>
            </div>
            <div class="nft-card p-4">
                <p class="text-sm text-gray-400">Avg Interest</p>
                <p class="text-2xl font-bold">8.5%</p>
            </div>
        </div>

        <!-- Active Loans -->
        <h2 class="text-2xl font-bold mb-4">Active Loans</h2>
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            <div class="nft-card">
                <div class="nft-image">
                    <span class="text-6xl">🖼️</span>
                </div>
                <div class="p-4">
                    <h3 class="text-xl font-bold mb-2">Bored Ape #8742</h3>
                    <div class="space-y-2 mb-4">
                        <div class="flex justify-between">
                            <span class="text-gray-400">Loan Amount</span>
                            <span class="font-bold">15 ETH</span>
                        </div>
                        <div class="flex justify-between">
                            <span class="text-gray-400">Interest</span>
                            <span class="text-green-400">6.5%</span>
                        </div>
                        <div class="flex justify-between">
                            <span class="text-gray-400">LTV</span>
                            <span>35%</span>
                        </div>
                        <div class="flex justify-between">
                            <span class="text-gray-400">Duration</span>
                            <span>90 days</span>
                        </div>
                    </div>
                    <button class="w-full px-4 py-2 bg-blue-600 rounded-lg hover:bg-blue-700">
                        Fund Loan
                    </button>
                </div>
            </div>
            <div class="nft-card">
                <div class="nft-image">
                    <span class="text-6xl">⚔️</span>
                </div>
                <div class="p-4">
                    <h3 class="text-xl font-bold mb-2">CryptoPunk #5209</h3>
                    <div class="space-y-2 mb-4">
                        <div class="flex justify-between">
                            <span class="text-gray-400">Loan Amount</span>
                            <span class="font-bold">25 ETH</span>
                        </div>
                        <div class="flex justify-between">
                            <span class="text-gray-400">Interest</span>
                            <span class="text-green-400">5.2%</span>
                        </div>
                        <div class="flex justify-between">
                            <span class="text-gray-400">LTV</span>
                            <span>28%</span>
                        </div>
                        <div class="flex justify-between">
                            <span class="text-gray-400">Duration</span>
                            <span>60 days</span>
                        </div>
                    </div>
                    <button class="w-full px-4 py-2 bg-blue-600 rounded-lg hover:bg-blue-700">
                        Fund Loan
                    </button>
                </div>
            </div>
            <div class="nft-card">
                <div class="nft-image">
                    <span class="text-6xl">👾</span>
                </div>
                <div class="p-4">
                    <h3 class="text-xl font-bold mb-2">Azuki #3021</h3>
                    <div class="space-y-2 mb-4">
                        <div class="flex justify-between">
                            <span class="text-gray-400">Loan Amount</span>
                            <span class="font-bold">8 ETH</span>
                        </div>
                        <div class="flex justify-between">
                            <span class="text-gray-400">Interest</span>
                            <span class="text-green-400">7.8%</span>
                        </div>
                        <div class="flex justify-between">
                            <span class="text-gray-400">LTV</span>
                            <span>42%</span>
                        </div>
                        <div class="flex justify-between">
                            <span class="text-gray-400">Duration</span>
                            <span>30 days</span>
                        </div>
                    </div>
                    <button class="w-full px-4 py-2 bg-blue-600 rounded-lg hover:bg-blue-700">
                        Fund Loan
                    </button>
                </div>
            </div>
        </div>

        <!-- Your Positions -->
        <h2 class="text-2xl font-bold mt-8 mb-4">Your Positions</h2>
        <div class="nft-card p-4">
            <div class="flex justify-between items-center">
                <div>
                    <p class="font-bold">You have no active positions</p>
                    <p class="text-sm text-gray-400">Start lending or borrowing to see your positions here</p>
                </div>
                <button class="px-4 py-2 bg-purple-600 rounded-lg">Browse NFTs</button>
            </div>
        </div>
    </div>
</body>
</html>'''

    def _create_cross_chain_swap(self) -> str:
        """Template de swap cross-chain"""
        return self._create_bridge_page_2_0()

    def _create_session_keys(self) -> str:
        """Template de clés de session"""
        return '''<div class="glass-card p-6">
            <h3 class="text-lg font-bold mb-4">🔑 Session Keys</h3>
            <p class="text-sm text-gray-400 mb-4">Autorisations temporaires pour gaming</p>
            <div class="space-y-3">
                <div class="flex justify-between items-center p-3 bg-white/5 rounded-xl">
                    <div>
                        <p class="font-medium">Game Session #1</p>
                        <p class="text-xs text-gray-400">Expire dans 2h</p>
                    </div>
                    <span class="px-2 py-1 bg-green-500/20 text-green-400 rounded-full text-xs">Active</span>
                </div>
                <button class="w-full px-4 py-2 bg-blue-600 rounded-lg">
                    + Nouvelle session
                </button>
            </div>
        </div>'''

    # ============================================================================
    # MÉTHODES DE PROJET
    # ============================================================================

    async def generate_project(self,
                             project_name: str,
                             contract_paths: List[str],
                             components: List[str],
                             framework: str = "nextjs") -> FrontendProject:
        """Génère un projet frontend complet"""
        
        framework_type = FrameworkType(framework)
        component_types = []
        
        # Convertir les noms de composants en ComponentType
        for comp in components:
            try:
                component_types.append(ComponentType(comp))
            except ValueError:
                self._logger.warning(f"⚠️ Composant inconnu: {comp}")
        
        if framework_type == FrameworkType.NEXTJS:
            project = await self.generate_nextjs_project(
                project_name, contract_paths, component_types
            )
        else:
            raise ValueError(f"Framework {framework} non supporté")
        
        return project

    async def deploy_to_vercel(self, project_id: str) -> Optional[str]:
        """Déploie le projet sur Vercel"""
        self._logger.info(f"🚀 Déploiement sur Vercel: {project_id}")
        
        if project_id not in self._projects:
            self._logger.error(f"❌ Projet {project_id} non trouvé")
            return None
        
        project = self._projects[project_id]
        
        try:
            # Vérifier si Vercel CLI est installé
            result = subprocess.run(["vercel", "--version"], capture_output=True, text=True)
            if result.returncode != 0:
                self._logger.warning("⚠️ Vercel CLI non installé")
                return None
            
            # Se déplacer dans le répertoire du projet
            os.chdir(project.output_path)
            
            # Déployer
            result = subprocess.run(
                ["vercel", "--prod", "--yes"],
                capture_output=True,
                text=True,
                timeout=300
            )
            
            # Extraire l'URL du résultat
            match = re.search(r"https://[^\s]+\.vercel\.app", result.stdout)
            if match:
                url = match.group(0)
                project.deploy_url = url
                self._stats['deployments'] += 1
                self._logger.info(f"✅ Déployé sur: {url}")
                return url
            
        except Exception as e:
            self._logger.error(f"❌ Erreur déploiement: {e}")
        
        return None


# ============================================================================
# FONCTIONS D'USINE
# ============================================================================

def create_frontend_web3_agent(config_path: Optional[str] = None) -> FrontendWeb3Agent:
    """Crée une instance de l'agent frontend Web3"""
    return FrontendWeb3Agent(config_path)


# ============================================================================
# POINT D'ENTRÉE POUR EXÉCUTION DIRECTE
# ============================================================================

if __name__ == "__main__":
    async def main():
        print("🎨 TEST AGENT FRONTEND WEB3 2.0")
        print("="*60)
        
        agent = FrontendWeb3Agent()
        await agent.initialize()
        
        agent_info = agent.get_agent_info()
        print(f"✅ Agent: {agent_info['name']} v{agent_info['version']}")
        print(f"✅ Statut: {agent_info['status']}")
        print(f"✅ Templates 2.0: {len(agent_info['features']['templates_2_0'])}")
        print(f"✅ Sous-agents: {agent_info['features']['sub_agents']}")
        
        # Test de génération
        project = await agent.generate_project(
            project_name="BankingWeb3 Demo",
            contract_paths=[],
            components=[
                "banking_dashboard_2_0",
                "virtual_cards",
                "savings_pods",
                "credit_scoring",
                "nft_lending",
                "lending_marketplace_2_0",
                "defi_composer"
            ],
            framework="nextjs"
        )
        
        print(f"\n📦 Projet généré!")
        print(f"  📁 Output: {project.output_path}")
        print(f"  📄 Composants: {len(project.components)}")
        
        health = await agent.health_check()
        print(f"\n❤️  Health: {health['status']}")
        
        await agent.shutdown()
        print(f"\n✅ Test terminé")
        print("\n" + "="*60)
    
    asyncio.run(main())
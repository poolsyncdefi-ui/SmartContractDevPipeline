import logging

logger = logging.getLogger(__name__)

"""
Agent de génération d'interfaces Web3 - Version 2.0
Banking Grade · Lending Protocol · Web3 Native
Design systémique, UX bancaire, composants intelligents
"""

__version__ = '2.0.0'
__author__ = 'SmartContractDevPipeline'
__description__ = 'Agent nouvelle génération fusionnant UX bancaire, lending protocol et innovations Web3'

import os
import json
import yaml
import asyncio
import subprocess
import re
from datetime import datetime
from enum import Enum, auto
from pathlib import Path
from typing import Dict, List, Any, Optional, Union

# Import de BaseAgent
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from agents.base_agent.base_agent import BaseAgent, AgentStatus, AgentStatus


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
    
    # === BANKING CORE 2.0 ===
    BANKING_DASHBOARD_2_0 = "banking_dashboard_2_0"
    VIRTUAL_CARDS = "virtual_cards"
    SAVINGS_PODS = "savings_pods"
    ROUND_UP_SAVINGS = "round_up_savings"
    SPENDING_INSIGHTS = "spending_insights"
    BUDGET_FORECAST = "budget_forecast"
    BILL_SPLITTING = "bill_splitting"
    DIRECT_DEBIT = "direct_debit"
    
    # === LENDING 2.0 ===
    LENDING_MARKETPLACE_2_0 = "lending_marketplace_2_0"
    COLLATERAL_MANAGEMENT = "collateral_management"
    LIQUIDATION_GUARD = "liquidation_guard"
    YIELD_OPTIMIZER = "yield_optimizer"
    LOAN_BUILDER = "loan_builder"
    CREDIT_SCORING = "credit_scoring"
    NFT_LENDING = "nft_lending"
    
    # === WEB3 INNOVATIONS ===
    GASLESS_INTERFACE = "gasless_interface"
    SOCIAL_RECOVERY = "social_recovery"
    PASSKEY_AUTH = "passkey_auth"
    DEFI_COMPOSER = "defi_composer"
    CROSS_CHAIN_SWAP = "cross_chain_swap"
    SESSION_KEYS = "session_keys"
    
    # === UX 2.0 ===
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


class FrontendProject:
    """Projet frontend généré"""
    def __init__(self, name: str, framework: FrameworkType):
        self.id = f"FRONTEND-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        self.name = name
        self.framework = framework
        self.components: List[Dict] = []
        self.contracts: List[Dict] = []
        self.pages: List[str] = []
        self.output_path = None
        self.deploy_url = None
        self.created_at = datetime.now()
        self.project_type = "web3_dapp"
        self.library = Web3Library.WAGMI
        self.theme = "dark"
        self.features = []
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "framework": self.framework.value,
            "components": len(self.components),
            "contracts": len(self.contracts),
            "output_path": self.output_path,
            "deploy_url": self.deploy_url,
            "created_at": self.created_at.isoformat()
        }


def _load_capabilities_2_0(self) -> List[str]:
    """Charge les capacités nouvelle génération"""
    return [
        # Banking Core
        'banking_dashboard_2_0', 'virtual_cards', 'savings_pods',
        'round_up_savings', 'spending_insights', 'budget_forecast',
        'bill_splitting', 'direct_debit',
        # Lending Protocol
        'lending_marketplace_2_0', 'collateral_management',
        'liquidation_guard', 'yield_optimizer', 'loan_builder',
        'credit_scoring', 'nft_lending',
        # Web3 Innovations
        'gasless_interface', 'social_recovery', 'passkey_auth',
        'defi_composer', 'cross_chain_swap', 'session_keys',
        # UX 2.0
        'voice_commands', 'gesture_navigation', 'haptic_feedback',
        'biometric_confirm'
    ]


class FrontendWeb3Agent(BaseAgent):
    """
    Agent de génération d'interfaces Web3
    Crée automatiquement des applications React/Next.js pour interagir avec les smart contracts
    """
    
    def __init__(self, config_path: str = ""):
        super().__init__(config_path)
        
        # Charger la configuration
        if config_path and os.path.exists(config_path):
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    file_config = yaml.safe_load(f)
                    if file_config and 'agent' in file_config:
                        agent_config = file_config['agent']
                        self._name = agent_config.get('name', self._name)
                        self._display_name = agent_config.get('display_name', self._display_name)
                        self._version = agent_config.get('version', self._version)
                        # Charger les capacités 2.0
                        self._agent_config['agent']['capabilities'] = self._load_capabilities_2_0()
            except Exception as e:
                self._logger.warning(f"⚠️ Erreur chargement config: {e}")
        
        self._default_config = self._get_default_config()
        if not self._agent_config:
            self._agent_config = self._default_config
        
        self._logger.info("🎨 Agent frontend Web3 créé")
        
        # État interne
        self._projects: Dict[str, FrontendProject] = {}
        self._components_generated = 0
        self._templates = {}
        self._contract_abis = {}
        self._components = {}
        self._templates_2_0 = {}
        
        # Créer les répertoires
        self._create_directories()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Configuration par défaut"""
        return {
            "agent": {
                "name": "frontend_web3",
                "display_name": "🎨 Agent Frontend Web3",
                "description": "Génération d'interfaces React/Next.js pour smart contracts",
                "version": "1.0.0",
                "capabilities": [
                    "react_generation",
                    "nextjs_generation",
                    "vue_generation",
                    "wallet_integration",
                    "contract_interaction",
                    "ipfs_deployment",
                    "vercel_deployment",
                    "theme_customization"
                ],
                "dependencies": ["smart_contract", "coder"]
            },
            "frontend": {
                "default_framework": "nextjs",
                "default_library": "wagmi",
                "output_path": "./frontend",
                "include_tests": True,
                "include_docs": True,
                "optimize_build": True,
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
                "ipfs_gateway": "https://ipfs.io/ipfs/",
                "domain": None
            },
            "templates_path": "./agents/frontend_web3/templates",
            "abis_path": "./agents/frontend_web3/contracts/abi"
        }
    
    def _load_capabilities_2_0(self) -> List[str]:
        """Charge les capacités nouvelle génération"""
        return [
            # Banking Core
            'banking_dashboard_2_0', 'virtual_cards', 'savings_pods',
            'round_up_savings', 'spending_insights', 'budget_forecast',
            'bill_splitting', 'direct_debit',
            # Lending Protocol
            'lending_marketplace_2_0', 'collateral_management',
            'liquidation_guard', 'yield_optimizer', 'loan_builder',
            'credit_scoring', 'nft_lending',
            # Web3 Innovations
            'gasless_interface', 'social_recovery', 'passkey_auth',
            'defi_composer', 'cross_chain_swap', 'session_keys',
            # UX 2.0
            'voice_commands', 'gesture_navigation', 'haptic_feedback',
            'biometric_confirm'
        ]
    
    def _create_directories(self):
        """Crée les répertoires nécessaires"""
        dirs = [
            self._agent_config["frontend"]["output_path"],
            self._agent_config["templates_path"],
            self._agent_config["abis_path"]
        ]
        
        for dir_path in dirs:
            Path(dir_path).mkdir(parents=True, exist_ok=True)
            self._logger.debug(f"📁 Répertoire créé: {dir_path}")
    
    async def initialize(self) -> bool:
        """Initialisation asynchrone"""
        try:
            self._set_status(AgentStatus.INITIALIZING)
            self._logger.info("Initialisation de l'agent frontend Web3...")
            
            # Initialiser les composants
            await self._initialize_components()
            
            # Charger les templates
            await self._load_templates()
            
            self._logger.info("Agent frontend Web3 initialisé")
            
            result = await super().initialize()
            
            if result:
                self._set_status(AgentStatus.READY)
                self._logger.info("✅ Agent frontend Web3 prêt")
            
            return result
            
        except Exception as e:
            self._logger.error(f"❌ Erreur initialisation: {e}")
            self._set_status(AgentStatus.ERROR)
            return False
    
    async def _initialize_components(self):
        """Initialise les composants"""
        self._logger.info("Initialisation des composants...")
        
        self._components = {
            "react_generator": self._init_react_generator(),
            "nextjs_generator": self._init_nextjs_generator(),
            "vue_generator": self._init_vue_generator(),
            "contract_analyzer": self._init_contract_analyzer(),
            "deployment_manager": self._init_deployment_manager()
        }
        
        self._logger.info(f"✅ Composants: {list(self._components.keys())}")
        return self._components
    
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
                "axios@1.4.0",
                "tailwindcss@3.3.0"
            ],
            "dev_dependencies": [
                "@types/react",
                "@types/react-dom",
                "@vitejs/plugin-react"
            ]
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
            "dev_dependencies": [
                "@types/node",
                "@types/react",
                "@types/react-dom",
                "typescript"
            ]
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
            "analyze_events": True
        }
    
    def _init_deployment_manager(self) -> Dict[str, Any]:
        """Initialise le gestionnaire de déploiement"""
        return {
            "platforms": ["vercel", "netlify", "ipfs"],
            "auto_deploy": self._agent_config["deployment"]["auto_deploy"],
            "default_platform": self._agent_config["deployment"]["platform"]
        }
    
    async def _load_templates(self):
        """Charge les templates 2.0"""
        templates_path = Path(self._agent_config["templates_path"])
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
        
        # Sauvegarder tous les templates
        for name, template in self._templates.items():
            file_path = templates_path / f"{name}.html"
            if not file_path.exists():
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(template)
                self._logger.debug(f"✅ Template 2.0 créé: {name}")
        
        self._logger.info(f"📋 Templates 2.0: {list(self._templates_2_0.keys())}")
        self._logger.info(f"📋 Templates totaux: {len(self._templates)}")
    
    # ------------------------------------------------------------------------
    # TEMPLATES 2.0 - BANKING CORE
    # ------------------------------------------------------------------------
    
    def _create_banking_dashboard_2_0(self) -> str:
        """Template bancaire nouvelle génération - Type Revolut/N26"""
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
                                <p class="text-xs opacity-70">Devise</p>
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
    
    # ------------------------------------------------------------------------
    # TEMPLATES 2.0 - LENDING PROTOCOL
    # ------------------------------------------------------------------------
    
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
    
    def _create_credit_scoring(self) -> str:
        """Template de score de crédit"""
        return '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Credit Score • {{PROJECT_NAME}}</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&display=swap');
        * { font-family: 'Space Grotesk', sans-serif; }
        .score-meter {
            background: conic-gradient(
                from 0deg,
                #ef4444 0deg 72deg,
                #f59e0b 72deg 144deg,
                #10b981 144deg 216deg,
                #3b82f6 216deg 288deg,
                #8b5cf6 288deg 360deg
            );
            border-radius: 50%;
            width: 200px;
            height: 200px;
        }
        .score-inner {
            width: 160px;
            height: 160px;
            background: #0f1219;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            flex-direction: column;
        }
    </style>
</head>
<body class="bg-[#0A0C12] text-white">
    <div class="max-w-7xl mx-auto px-4 py-12">
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-12">
            <!-- Score Card -->
            <div class="glass-card p-8">
                <h2 class="text-2xl font-bold mb-6">📊 Web3 Credit Score</h2>
                <div class="flex flex-col items-center">
                    <div class="score-meter flex items-center justify-center mb-6">
                        <div class="score-inner">
                            <span class="text-5xl font-bold">782</span>
                            <span class="text-sm text-gray-400">/ 850</span>
                        </div>
                    </div>
                    <span class="px-4 py-2 bg-green-500/20 text-green-400 rounded-full text-sm">
                        Excellent • Top 15%
                    </span>
                </div>
                
                <div class="grid grid-cols-2 gap-4 mt-8">
                    <div class="p-4 bg-white/5 rounded-xl">
                        <p class="text-xs text-gray-400">Historique</p>
                        <p class="text-lg font-bold">Excellent</p>
                    </div>
                    <div class="p-4 bg-white/5 rounded-xl">
                        <p class="text-xs text-gray-400">Utilisation</p>
                        <p class="text-lg font-bold">23%</p>
                    </div>
                    <div class="p-4 bg-white/5 rounded-xl">
                        <p class="text-xs text-gray-400">Âge du compte</p>
                        <p class="text-lg font-bold">2 ans</p>
                    </div>
                    <div class="p-4 bg-white/5 rounded-xl">
                        <p class="text-xs text-gray-400">Transactions</p>
                        <p class="text-lg font-bold">847</p>
                    </div>
                </div>
            </div>

            <!-- Score Simulator -->
            <div class="glass-card p-8">
                <h2 class="text-2xl font-bold mb-6">🎯 Simulateur de score</h2>
                <div class="space-y-6">
                    <div>
                        <label class="block text-sm text-gray-400 mb-2">Nouveau prêt</label>
                        <input type="range" min="0" max="50000" value="10000" 
                               class="w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer">
                        <div class="flex justify-between mt-2">
                            <span class="text-xs text-gray-400">0 €</span>
                            <span class="text-sm font-bold">10 000 €</span>
                            <span class="text-xs text-gray-400">50 000 €</span>
                        </div>
                    </div>
                    
                    <div>
                        <label class="block text-sm text-gray-400 mb-2">Durée</label>
                        <div class="flex space-x-2">
                            <button class="flex-1 px-4 py-2 bg-blue-600 rounded-lg">12 mois</button>
                            <button class="flex-1 px-4 py-2 bg-white/10 rounded-lg">24 mois</button>
                            <button class="flex-1 px-4 py-2 bg-white/10 rounded-lg">36 mois</button>
                        </div>
                    </div>
                    
                    <div class="p-4 bg-gradient-to-r from-blue-600/20 to-purple-600/20 rounded-xl">
                        <p class="text-sm text-gray-300 mb-2">Score projeté</p>
                        <p class="text-3xl font-bold text-blue-400">756</p>
                        <p class="text-xs text-gray-400 mt-2">↓ -26 points (éligible)</p>
                    </div>
                    
                    <button class="w-full px-6 py-3 bg-blue-600 rounded-xl font-medium hover:bg-blue-700">
                        Simuler un emprunt
                    </button>
                </div>
            </div>
        </div>
        
        <!-- Loan Recommendations -->
        <div class="mt-12">
            <h2 class="text-xl font-bold mb-6">💡 Offres personnalisées</h2>
            <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div class="glass-card p-6">
                    <div class="flex justify-between items-start mb-4">
                        <span class="text-2xl">🏦</span>
                        <span class="px-2 py-1 bg-green-500/20 text-green-400 rounded-full text-xs">Pré-approuvé</span>
                    </div>
                    <h3 class="text-lg font-bold mb-2">Prêt personnel</h3>
                    <p class="text-sm text-gray-400 mb-4">TAEG 3.2% • Jusqu'à 50k€</p>
                    <p class="text-xs text-gray-400">Mensualité estimée</p>
                    <p class="text-xl font-bold">234 €</p>
                </div>
                <div class="glass-card p-6">
                    <div class="flex justify-between items-start mb-4">
                        <span class="text-2xl">🚗</span>
                        <span class="px-2 py-1 bg-blue-500/20 text-blue-400 rounded-full text-xs">Auto</span>
                    </div>
                    <h3 class="text-lg font-bold mb-2">Prêt automobile</h3>
                    <p class="text-sm text-gray-400 mb-4">TAEG 2.8% • Jusqu'à 30k€</p>
                    <p class="text-xs text-gray-400">Mensualité estimée</p>
                    <p class="text-xl font-bold">312 €</p>
                </div>
                <div class="glass-card p-6">
                    <div class="flex justify-between items-start mb-4">
                        <span class="text-2xl">💎</span>
                        <span class="px-2 py-1 bg-purple-500/20 text-purple-400 rounded-full text-xs">Premium</span>
                    </div>
                    <h3 class="text-lg font-bold mb-2">Prêt immobilier</h3>
                    <p class="text-sm text-gray-400 mb-4">TAEG 1.8% • Jusqu'à 300k€</p>
                    <p class="text-xs text-gray-400">Mensualité estimée</p>
                    <p class="text-xl font-bold">1,023 €</p>
                </div>
            </div>
        </div>
    </div>
</body>
</html>'''
    
    def _create_nft_lending(self) -> str:
        """Template de lending sur NFT"""
        return '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>NFT Lending • {{PROJECT_NAME}}</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-[#0A0C12] text-white">
    <div class="max-w-7xl mx-auto px-4 py-12">
        <div class="flex justify-between items-center mb-8">
            <div>
                <h1 class="text-3xl font-bold mb-2">🖼️ NFT Lending</h1>
                <p class="text-gray-400">Empruntez contre vos NFT • Floor price lending</p>
            </div>
            <div class="flex space-x-4">
                <span class="px-4 py-2 bg-blue-500/20 text-blue-400 rounded-full text-sm">
                    TVL: $45.2M
                </span>
                <span class="px-4 py-2 bg-green-500/20 text-green-400 rounded-full text-sm">
                    Taux: 4.8%
                </span>
            </div>
        </div>

        <!-- Your NFTs -->
        <div class="glass-card p-6 mb-8">
            <h2 class="text-xl font-bold mb-4">Vos NFT éligibles</h2>
            <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div class="bg-white/5 rounded-xl p-4">
                    <div class="aspect-square bg-gradient-to-br from-blue-500/20 to-blue-600/20 rounded-lg mb-3 flex items-center justify-center">
                        <span class="text-3xl">🦍</span>
                    </div>
                    <h3 class="font-medium text-sm">BAYC #4592</h3>
                    <p class="text-xs text-gray-400">Bored Ape</p>
                    <div class="flex justify-between items-center mt-3">
                        <span class="text-sm font-bold">12.5 ETH</span>
                        <span class="text-xs text-green-400">LTV 65%</span>
                    </div>
                    <button class="w-full mt-3 px-3 py-1 bg-blue-600 rounded-lg text-sm">
                        Emprunter
                    </button>
                </div>
                <div class="bg-white/5 rounded-xl p-4">
                    <div class="aspect-square bg-gradient-to-br from-purple-500/20 to-purple-600/20 rounded-lg mb-3 flex items-center justify-center">
                        <span class="text-3xl">🎭</span>
                    </div>
                    <h3 class="font-medium text-sm">Art Block #123</h3>
                    <p class="text-xs text-gray-400">Fidenza</p>
                    <div class="flex justify-between items-center mt-3">
                        <span class="text-sm font-bold">8.2 ETH</span>
                        <span class="text-xs text-green-400">LTV 55%</span>
                    </div>
                    <button class="w-full mt-3 px-3 py-1 bg-blue-600 rounded-lg text-sm">
                        Emprunter
                    </button>
                </div>
                <div class="bg-white/5 rounded-xl p-4">
                    <div class="aspect-square bg-gradient-to-br from-pink-500/20 to-pink-600/20 rounded-lg mb-3 flex items-center justify-center">
                        <span class="text-3xl">👾</span>
                    </div>
                    <h3 class="font-medium text-sm">Azuki #789</h3>
                    <p class="text-xs text-gray-400">Azuki</p>
                    <div class="flex justify-between items-center mt-3">
                        <span class="text-sm font-bold">3.8 ETH</span>
                        <span class="text-xs text-green-400">LTV 60%</span>
                    </div>
                    <button class="w-full mt-3 px-3 py-1 bg-blue-600 rounded-lg text-sm">
                        Emprunter
                    </button>
                </div>
                <div class="bg-white/5 rounded-xl p-4">
                    <div class="aspect-square bg-gradient-to-br from-green-500/20 to-green-600/20 rounded-lg mb-3 flex items-center justify-center">
                        <span class="text-3xl">🐧</span>
                    </div>
                    <h3 class="font-medium text-sm">Pudgy #3456</h3>
                    <p class="text-xs text-gray-400">Pudgy</p>
                    <div class="flex justify-between items-center mt-3">
                        <span class="text-sm font-bold">1.2 ETH</span>
                        <span class="text-xs text-green-400">LTV 70%</span>
                    </div>
                    <button class="w-full mt-3 px-3 py-1 bg-blue-600 rounded-lg text-sm">
                        Emprunter
                    </button>
                </div>
            </div>
        </div>

        <!-- Active Loans -->
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div class="glass-card p-6">
                <h3 class="text-lg font-bold mb-4">📋 Vos emprunts</h3>
                <div class="space-y-4">
                    <div class="flex items-center justify-between p-4 bg-white/5 rounded-xl">
                        <div class="flex items-center space-x-3">
                            <span class="text-2xl">🦍</span>
                            <div>
                                <p class="font-medium">BAYC #4592</p>
                                <p class="text-xs text-gray-400">Collatéral: 12.5 ETH</p>
                            </div>
                        </div>
                        <div class="text-right">
                            <p class="font-bold">8.1 ETH</p>
                            <p class="text-xs text-green-400">65% LTV</p>
                        </div>
                    </div>
                    <div class="flex items-center justify-between p-4 bg-white/5 rounded-xl">
                        <div class="flex items-center space-x-3">
                            <span class="text-2xl">🎭</span>
                            <div>
                                <p class="font-medium">Art Block #123</p>
                                <p class="text-xs text-gray-400">Collatéral: 8.2 ETH</p>
                            </div>
                        </div>
                        <div class="text-right">
                            <p class="font-bold">4.5 ETH</p>
                            <p class="text-xs text-yellow-400">55% LTV</p>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="glass-card p-6">
                <h3 class="text-lg font-bold mb-4">📊 Market Overview</h3>
                <div class="space-y-3">
                    <div class="flex justify-between">
                        <span>Blue Chip LTV</span>
                        <span class="font-medium">65-75%</span>
                    </div>
                    <div class="w-full bg-gray-700 rounded-full h-2">
                        <div class="bg-green-500 h-2 rounded-full" style="width: 70%"></div>
                    </div>
                    <div class="flex justify-between mt-3">
                        <span>Collection LTV</span>
                        <span class="font-medium">40-55%</span>
                    </div>
                    <div class="w-full bg-gray-700 rounded-full h-2">
                        <div class="bg-yellow-500 h-2 rounded-full" style="width: 48%"></div>
                    </div>
                </div>
                
                <div class="mt-6 p-4 bg-gradient-to-r from-yellow-900/30 to-red-900/30 rounded-xl border border-yellow-500/30">
                    <div class="flex items-center justify-between">
                        <div class="flex items-center space-x-3">
                            <span class="text-2xl">⚠️</span>
                            <div>
                                <p class="font-medium">Liquidation imminent</p>
                                <p class="text-xs text-gray-400">BAYC #4592 • 78% LTV</p>
                            </div>
                        </div>
                        <button class="px-4 py-2 bg-yellow-600 rounded-lg text-sm">
                            Ajouter collatéral
                        </button>
                    </div>
                </div>
            </div>
        </div>
    </div>
</body>
</html>'''
    
    # ------------------------------------------------------------------------
    # TEMPLATES 2.0 - WEB3 INNOVATIONS
    # ------------------------------------------------------------------------
    
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
    
    def _create_cross_chain_swap(self) -> str:
        """Template de swap cross-chain"""
        return self._create_bridge_page_2_0()  # Réutilisation
    
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
    
    # ------------------------------------------------------------------------
    # MÉTHODES DE GÉNÉRATION DES COMPOSANTS 2.0
    # ------------------------------------------------------------------------
    
    async def _generate_banking_dashboard_2_0(self, project: FrontendProject, output_dir: Path):
        """Génère le dashboard bancaire nouvelle génération"""
        template = self._templates["banking_dashboard_2_0"]
        
        # Remplacer les variables
        template = template.replace("{{BANK_NAME}}", project.name)
        template = template.replace("{{USER_NAME}}", "Thomas")
        template = template.replace("{{USER_INITIALS}}", "TD")
        template = template.replace("{{TOTAL_BALANCE}}", "45,890")
        template = template.replace("{{BALANCE_CHANGE}}", "2.4")
        template = template.replace("{{ETH_BALANCE}}", "12.5")
        template = template.replace("{{BTC_BALANCE}}", "0.45")
        template = template.replace("{{DATE}}", datetime.now().strftime("%d %B %Y"))
        
        # Remplacer les couleurs
        template = template.replace("{{PRIMARY_COLOR}}", self._agent_config["frontend"]["colors"]["primary"])
        template = template.replace("{{SECONDARY_COLOR}}", self._agent_config["frontend"]["colors"]["secondary"])
        template = template.replace("{{ACCENT_COLOR}}", self._agent_config["frontend"]["colors"]["accent"])
        
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
        
        project.components.append({"type": "banking_dashboard_2_0", "path": "app/banking"})
        self._components_generated += 1
    
    async def _generate_virtual_cards(self, project: FrontendProject, output_dir: Path):
        """Génère la page de gestion de cartes virtuelles"""
        component_dir = output_dir / "app" / "cards"
        component_dir.mkdir(exist_ok=True)
        
        template = self._templates["virtual_cards"]
        # Réutilisation du template banking avec focus sur les cartes
        
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
        
        project.components.append({"type": "virtual_cards", "path": "app/cards"})
        self._components_generated += 1
    
    async def _generate_savings_pods(self, project: FrontendProject, output_dir: Path):
        """Génère la page des pockets d'épargne"""
        component_dir = output_dir / "app" / "savings"
        component_dir.mkdir(exist_ok=True)
        
        template = self._templates["savings_pods"]
        
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
        
        project.components.append({"type": "savings_pods", "path": "app/savings"})
        self._components_generated += 1
    
    async def _generate_credit_scoring(self, project: FrontendProject, output_dir: Path):
        """Génère la page de score de crédit"""
        component_dir = output_dir / "app" / "credit-score"
        component_dir.mkdir(exist_ok=True)
        
        template = self._templates["credit_scoring"]
        template = template.replace("{{PROJECT_NAME}}", project.name)
        
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
        
        project.components.append({"type": "credit_scoring", "path": "app/credit-score"})
        self._components_generated += 1
    
    async def _generate_nft_lending(self, project: FrontendProject, output_dir: Path):
        """Génère la page de NFT lending"""
        component_dir = output_dir / "app" / "nft-lending"
        component_dir.mkdir(exist_ok=True)
        
        template = self._templates["nft_lending"]
        template = template.replace("{{PROJECT_NAME}}", project.name)
        
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
        
        project.components.append({"type": "nft_lending", "path": "app/nft-lending"})
        self._components_generated += 1
    
    async def _generate_lending_marketplace_2_0(self, project: FrontendProject, output_dir: Path):
        """Génère la marketplace de prêts"""
        component_dir = output_dir / "app" / "lending"
        component_dir.mkdir(exist_ok=True)
        
        template = self._templates["lending_marketplace_2_0"]
        template = template.replace("{{PROTOCOL_NAME}}", f"{project.name} Lending")
        template = template.replace("{{TVL}}", "45.2")
        template = template.replace("{{LOAN_VOLUME}}", "28.5")
        template = template.replace("{{VOLUME_CHANGE}}", "12.3")
        template = template.replace("{{LENDERS}}", "1,234")
        template = template.replace("{{BORROWERS}}", "856")
        template = template.replace("{{AVG_RATE}}", "4.8")
        
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
        
        project.components.append({"type": "lending_marketplace_2_0", "path": "app/lending"})
        self._components_generated += 1
    
    async def _generate_gasless_interface(self, project: FrontendProject, output_dir: Path):
        """Génère le composant gasless"""
        component_dir = output_dir / "components" / "gasless"
        component_dir.mkdir(parents=True, exist_ok=True)
        
        template = self._templates["gasless_interface"]
        
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
        
        project.components.append({"type": "gasless_interface", "path": "components/gasless/GaslessTransaction.tsx"})
        self._components_generated += 1
    
    async def _generate_social_recovery(self, project: FrontendProject, output_dir: Path):
        """Génère le composant social recovery"""
        component_dir = output_dir / "components" / "security"
        component_dir.mkdir(parents=True, exist_ok=True)
        
        template = self._templates["social_recovery"]
        
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
        
        project.components.append({"type": "social_recovery", "path": "components/security/SocialRecovery.tsx"})
        self._components_generated += 1
    
    async def _generate_passkey_auth(self, project: FrontendProject, output_dir: Path):
        """Génère le composant d'authentification biométrique"""
        component_dir = output_dir / "components" / "auth"
        component_dir.mkdir(parents=True, exist_ok=True)
        
        template = self._templates["passkey_auth"]
        
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
        
        project.components.append({"type": "passkey_auth", "path": "components/auth/PasskeyAuth.tsx"})
        self._components_generated += 1
    
    async def _generate_defi_composer(self, project: FrontendProject, output_dir: Path):
        """Génère le composant DeFi composer"""
        component_dir = output_dir / "app" / "composer"
        component_dir.mkdir(exist_ok=True)
        
        template = self._templates["defi_composer"]
        
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
        
        project.components.append({"type": "defi_composer", "path": "app/composer"})
        self._components_generated += 1
    
    # ------------------------------------------------------------------------
    # MÉTHODES EXISTANTES (À GARDER TELLES QUELLES)
    # ------------------------------------------------------------------------
    
    async def extract_contract_abi(self, contract_path: str) -> Dict:
        """Extrait l'ABI d'un contrat compilé"""
        self._logger.info(f"🔍 Extraction ABI de {contract_path}")
        
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
                        abi_path = Path(self._agent_config["abis_path"]) / f"{contract_name}.json"
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
        
        project = FrontendProject(project_name, FrameworkType.NEXTJS)
        project.theme = theme
        output_dir = Path(self._agent_config["frontend"]["output_path"]) / project.id
        
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
        
        # Composants existants
        if component_type == ComponentType.MINT_PAGE:
            await self._generate_mint_page(project, output_dir)
        elif component_type == ComponentType.DASHBOARD:
            await self._generate_dashboard(project, output_dir)
        elif component_type == ComponentType.NFT_GALLERY:
            await self._generate_nft_gallery(project, output_dir)
        elif component_type == ComponentType.TOKEN_TRANSFER:
            await self._generate_token_transfer(project, output_dir)
        elif component_type == ComponentType.STAKING:
            await self._generate_staking_page(project, output_dir)
        elif component_type == ComponentType.GOVERNANCE:
            await self._generate_governance_page(project, output_dir)
        elif component_type == ComponentType.SWAP:
            await self._generate_swap_page(project, output_dir)
        elif component_type == ComponentType.BRIDGE:
            await self._generate_bridge_page(project, output_dir)
        elif component_type == ComponentType.ANALYTICS:
            await self._generate_analytics_page(project, output_dir)
        elif component_type == ComponentType.PROFILE:
            await self._generate_profile_page(project, output_dir)
        elif component_type == ComponentType.AUCTION:
            await self._generate_auction_page(project, output_dir)
        elif component_type == ComponentType.LENDING:
            await self._generate_lending_page(project, output_dir)
        elif component_type == ComponentType.MULTISIG:
            await self._generate_multisig_page(project, output_dir)
        elif component_type == ComponentType.AIRDROP:
            await self._generate_airdrop_page(project, output_dir)
        elif component_type == ComponentType.MARKETPLACE:
            await self._generate_marketplace_page(project, output_dir)
        
        # === NOUVEAUX COMPOSANTS 2.0 ===
        elif component_type == ComponentType.BANKING_DASHBOARD_2_0:
            await self._generate_banking_dashboard_2_0(project, output_dir)
        elif component_type == ComponentType.VIRTUAL_CARDS:
            await self._generate_virtual_cards(project, output_dir)
        elif component_type == ComponentType.SAVINGS_PODS:
            await self._generate_savings_pods(project, output_dir)
        elif component_type == ComponentType.CREDIT_SCORING:
            await self._generate_credit_scoring(project, output_dir)
        elif component_type == ComponentType.NFT_LENDING:
            await self._generate_nft_lending(project, output_dir)
        elif component_type == ComponentType.LENDING_MARKETPLACE_2_0:
            await self._generate_lending_marketplace_2_0(project, output_dir)
        elif component_type == ComponentType.GASLESS_INTERFACE:
            await self._generate_gasless_interface(project, output_dir)
        elif component_type == ComponentType.SOCIAL_RECOVERY:
            await self._generate_social_recovery(project, output_dir)
        elif component_type == ComponentType.PASSKEY_AUTH:
            await self._generate_passkey_auth(project, output_dir)
        elif component_type == ComponentType.DEFI_COMPOSER:
            await self._generate_defi_composer(project, output_dir)
    
    # ------------------------------------------------------------------------
    # MÉTHODES DE GÉNÉRATION EXISTANTES (À GARDER)
    # ------------------------------------------------------------------------
    
    async def _generate_mint_page(self, project: FrontendProject, output_dir: Path):
        """Génère une page de mint NFT"""
        # Garder le code existant
        pass
    
    async def _generate_dashboard(self, project: FrontendProject, output_dir: Path):
        """Génère un dashboard DeFi"""
        # Garder le code existant
        pass
    
    async def _generate_nft_gallery(self, project: FrontendProject, output_dir: Path):
        """Génère une galerie NFT"""
        # Garder le code existant
        pass
    
    async def _generate_token_transfer(self, project: FrontendProject, output_dir: Path):
        """Génère une page de transfert"""
        # Garder le code existant
        pass
    
    async def _generate_staking_page(self, project: FrontendProject, output_dir: Path):
        """Génère une page de staking"""
        # Garder le code existant
        pass
    
    async def _generate_governance_page(self, project: FrontendProject, output_dir: Path):
        """Génère une page de gouvernance"""
        # Garder le code existant
        pass
    
    async def _generate_swap_page(self, project: FrontendProject, output_dir: Path):
        """Génère une page de swap"""
        # Garder le code existant
        pass
    
    async def _generate_bridge_page(self, project: FrontendProject, output_dir: Path):
        """Génère une page de bridge"""
        # Garder le code existant
        pass
    
    async def _generate_analytics_page(self, project: FrontendProject, output_dir: Path):
        """Génère une page d'analytics"""
        # Garder le code existant
        pass
    
    async def _generate_profile_page(self, project: FrontendProject, output_dir: Path):
        """Génère une page de profil"""
        # Garder le code existant
        pass
    
    async def _generate_auction_page(self, project: FrontendProject, output_dir: Path):
        """Génère une page d'enchères"""
        # Garder le code existant
        pass
    
    async def _generate_lending_page(self, project: FrontendProject, output_dir: Path):
        """Génère une page de lending"""
        # Garder le code existant
        pass
    
    async def _generate_multisig_page(self, project: FrontendProject, output_dir: Path):
        """Génère une page multisig"""
        # Garder le code existant
        pass
    
    async def _generate_airdrop_page(self, project: FrontendProject, output_dir: Path):
        """Génère une page d'airdrop"""
        # Garder le code existant
        pass
    
    async def _generate_marketplace_page(self, project: FrontendProject, output_dir: Path):
        """Génère une page marketplace"""
        await self._generate_nft_gallery(project, output_dir)
    
    # ------------------------------------------------------------------------
    # MÉTHODES DE PROJET
    # ------------------------------------------------------------------------
    
    async def generate_project(self,
                             project_name: str,
                             contract_paths: List[str],
                             components: List[str],
                             framework: str = "nextjs") -> FrontendProject:
        """Génère un projet frontend complet"""
        
        framework_type = FrameworkType(framework)
        component_types = [ComponentType(c) for c in components]
        
        if framework_type == FrameworkType.NEXTJS:
            project = await self.generate_nextjs_project(
                project_name, contract_paths, component_types
            )
        else:
            raise ValueError(f"Framework {framework} non supporté")
        
        return project
    
    async def deploy_to_vercel(self, project_id: str) -> str:
        """Déploie le projet sur Vercel"""
        self._logger.info(f"🚀 Déploiement sur Vercel: {project_id}")
        
        if project_id not in self._projects:
            raise ValueError(f"Projet {project_id} non trouvé")
        
        project = self._projects[project_id]
        
        try:
            result = subprocess.run(["vercel", "--version"], capture_output=True, text=True)
            if result.returncode != 0:
                self._logger.warning("⚠️ Vercel CLI non installé")
                return None
            
            os.chdir(project.output_path)
            result = subprocess.run(["vercel", "--prod", "--yes"], capture_output=True, text=True)
            
            match = re.search(r"https://[^\s]+\.vercel\.app", result.stdout)
            if match:
                project.deploy_url = match.group(0)
                self._logger.info(f"✅ Déployé sur: {project.deploy_url}")
                return project.deploy_url
            
        except Exception as e:
            self._logger.error(f"❌ Erreur déploiement: {e}")
        
        return None
    
    async def health_check(self) -> Dict[str, Any]:
        """Vérifie la santé de l'agent"""
        return {
            "agent": self._name,
            "status": self._status.value,
            "ready": self._status == AgentStatus.READY,
            "projects_generated": len(self._projects),
            "components_generated": self._components_generated,
            "templates_available": list(self._templates.keys()),
            "templates_2_0": list(self._templates_2_0.keys()) if hasattr(self, '_templates_2_0') else [],
            "frameworks": ["nextjs", "react"],
            "components": list(self._components.keys()),
            "uptime": self.uptime.total_seconds()
        }
    
    def get_agent_info(self) -> Dict[str, Any]:
        """Informations de l'agent"""
        return {
            "id": self._name,
            "name": self._display_name,
            "type": "frontend",
            "version": self._version,
            "description": self._description,
            "status": self._status.value,
            "capabilities": self._agent_config.get("agent", {}).get("capabilities", []),
            "projects_created": len(self._projects),
            "templates": list(self._templates.keys()),
            "templates_2_0": list(self._templates_2_0.keys()) if hasattr(self, '_templates_2_0') else [],
            "default_framework": self._agent_config["frontend"]["default_framework"]
        }
    
    async def _handle_custom_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Gestion des messages personnalisés"""
        msg_type = message.get("type", "")
        
        if msg_type == "generate_frontend":
            project = await self.generate_project(
                project_name=message["project_name"],
                contract_paths=message["contracts"],
                components=message["components"],
                framework=message.get("framework", "nextjs")
            )
            return {
                "project_id": project.id,
                "output_path": project.output_path,
                "components": len(project.components)
            }
        
        elif msg_type == "deploy":
            url = await self.deploy_to_vercel(message["project_id"])
            return {"url": url}
        
        elif msg_type == "list_projects":
            return {
                "projects": [p.to_dict() for p in self._projects.values()]
            }
        
        elif msg_type == "extract_abi":
            abi = await self.extract_contract_abi(message["contract_path"])
            return abi
        
        return {"status": "received", "type": msg_type}


# ------------------------------------------------------------------------
# FONCTIONS D'USINE
# ------------------------------------------------------------------------

def create_frontend_web3_agent(config_path: str = "") -> FrontendWeb3Agent:
    """Crée une instance de l'agent frontend Web3"""
    return FrontendWeb3Agent(config_path)


# ------------------------------------------------------------------------
# POINT D'ENTRÉE POUR EXÉCUTION DIRECTE
# ------------------------------------------------------------------------

if __name__ == "__main__":
    async def main():
        print("🎨 TEST AGENT FRONTEND WEB3 2.0")
        print("="*60)
        
        agent = FrontendWeb3Agent()
        await agent.initialize()
        
        print(f"✅ Agent version: {__version__}")
        print(f"✅ Templates 2.0: {list(agent._templates_2_0.keys())}")
        print(f"✅ Templates totaux: {len(agent._templates)}")
        
        # Générer un projet de démonstration
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
        
        print(f"\n📦 Projet 2.0 généré!")
        print(f"  📁 Output: {project.output_path}")
        print(f"  📄 Composants: {len(project.components)}")
        print(f"\n🚀 Pour lancer le projet:")
        print(f"  cd {project.output_path}")
        print(f"  npm install")
        print(f"  npm run dev")
        print(f"\n🌐 http://localhost:3000/banking")
        print(f"🌐 http://localhost:3000/lending")
        print(f"🌐 http://localhost:3000/credit-score")
        print(f"🌐 http://localhost:3000/nft-lending")
        
        print("\n" + "="*60)
        print("🎉 FRONTEND WEB3 AGENT 2.0 OPÉRATIONNEL !")
        print("="*60)
    
    asyncio.run(main())
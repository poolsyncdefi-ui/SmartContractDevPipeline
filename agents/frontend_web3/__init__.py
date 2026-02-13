"""
Package Frontend Web3
Génération d'interfaces React/Next.js pour smart contracts
Version: 1.0.0

Ce package fournit un agent spécialisé dans la génération automatique
d'applications Web3 complètes avec support multi-chaînes, wallet integration,
et 15+ composants prêts à l'emploi (mint, staking, governance, swap, etc.)
"""

import os
import yaml
from pathlib import Path
from typing import Dict, List, Any, Optional

# -----------------------------------------------------------------------------
# CONSTANTES DU PACKAGE
# -----------------------------------------------------------------------------

__version__ = '1.0.0'
__author__ = 'SmartContractDevPipeline'
__description__ = 'Agent de génération d\'interfaces Web3 pour smart contracts'
__capabilities__ = [
    'react_generation',
    'nextjs_generation',
    'vue_generation',
    'wallet_integration',
    'contract_interaction',
    'ipfs_deployment',
    'vercel_deployment',
    'theme_customization',
    'mint_page_generation',
    'nft_gallery_generation',
    'staking_page_generation',
    'governance_page_generation',
    'swap_page_generation',
    'bridge_page_generation',
    'analytics_dashboard_generation',
    'profile_page_generation',
    'auction_house_generation',
    'lending_page_generation',
    'multisig_wallet_generation',
    'airdrop_page_generation'
]

# -----------------------------------------------------------------------------
# IMPORT DES CLASSES PRINCIPALES
# -----------------------------------------------------------------------------

from .frontend_agent import (
    # Agent principal
    FrontendWeb3Agent,
    
    # Énums pour configuration
    FrameworkType,
    ComponentType,
    Web3Library,
    
    # Classes de données
    FrontendProject,
    
    # Fonctions d'usine
    create_frontend_web3_agent,
)

# -----------------------------------------------------------------------------
# FONCTIONS DE CHARGEMENT DE CONFIGURATION
# -----------------------------------------------------------------------------

def load_agent_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Charge la configuration de l'agent frontend Web3.
    
    Args:
        config_path: Chemin vers le fichier de configuration YAML.
                    Si None, utilise le chemin par défaut.
    
    Returns:
        Dictionnaire de configuration
    """
    default_config_path = Path(__file__).parent / "config.yaml"
    
    # Déterminer le chemin à utiliser
    if config_path is None:
        config_file = default_config_path
    else:
        config_file = Path(config_path)
    
    # Configuration par défaut (fallback)
    default_config = {
        "agent": {
            "name": "frontend_web3",
            "display_name": "🎨 Agent Frontend Web3",
            "version": __version__,
            "capabilities": __capabilities__
        },
        "frontend": {
            "default_framework": "nextjs",
            "default_library": "wagmi",
            "output_path": "./frontend",
            "theme": "dark",
            "components_available": [
                "mint_page", "dashboard", "nft_gallery", "token_transfer",
                "staking_page", "governance_page", "swap_page", "bridge_page",
                "analytics_dashboard", "profile_page", "auction_house",
                "lending_page", "multisig_wallet", "airdrop_page", "marketplace"
            ]
        }
    }
    
    # Charger la configuration si le fichier existe
    if config_file.exists():
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                if config:
                    # Fusionner avec la config par défaut
                    merged_config = default_config.copy()
                    for key, value in config.items():
                        if key in merged_config and isinstance(merged_config[key], dict) and isinstance(value, dict):
                            merged_config[key].update(value)
                        else:
                            merged_config[key] = value
                    return merged_config
        except Exception as e:
            print(f"⚠️ Erreur chargement config: {e}")
    
    return default_config


def get_supported_components() -> List[str]:
    """
    Retourne la liste de tous les composants supportés.
    
    Returns:
        Liste des noms des composants disponibles
    """
    return [
        "mint_page",
        "dashboard",
        "nft_gallery",
        "token_transfer",
        "staking_page",
        "governance_page",
        "swap_page",
        "bridge_page",
        "analytics_dashboard",
        "profile_page",
        "auction_house",
        "lending_page",
        "multisig_wallet",
        "airdrop_page",
        "marketplace"
    ]


def get_component_description(component_name: str) -> str:
    """
    Retourne la description d'un composant.
    
    Args:
        component_name: Nom du composant
    
    Returns:
        Description du composant
    """
    descriptions = {
        "mint_page": "Page de mint NFT avec compteur, prix et preview",
        "dashboard": "Dashboard DeFi avec métriques TVL, volume, utilisateurs",
        "nft_gallery": "Galerie NFT responsive avec grille et filtres",
        "token_transfer": "Interface de transfert de tokens avec validation",
        "staking_page": "Page de staking avec pools, APY et rewards",
        "governance_page": "Portail de gouvernance DAO avec propositions et votes",
        "swap_page": "Interface DEX swap avec taux et slippage",
        "bridge_page": "Interface de bridge cross-chain multi-réseaux",
        "analytics_dashboard": "Dashboard analytics avec charts et métriques",
        "profile_page": "Page de profil utilisateur avec portfolio",
        "auction_house": "Maison d'enchères NFT avec live bidding",
        "lending_page": "Interface de lending/borrowing avec marchés",
        "multisig_wallet": "Wallet multi-signatures avec confirmations",
        "airdrop_page": "Page de claim airdrop avec éligibilité",
        "marketplace": "Marketplace NFT avec achats/ventes"
    }
    return descriptions.get(component_name, "Composant personnalisé")


def get_framework_config(framework: str = "nextjs") -> Dict[str, Any]:
    """
    Retourne la configuration pour un framework spécifique.
    
    Args:
        framework: Nom du framework ('nextjs', 'react', 'vue')
    
    Returns:
        Configuration du framework
    """
    frameworks = {
        "nextjs": {
            "version": "13.4.0",
            "template": "app",
            "dependencies": {
                "next": "13.4.0",
                "react": "18.2.0",
                "react-dom": "18.2.0",
                "ethers": "5.7.2",
                "@rainbow-me/rainbowkit": "0.12.0",
                "wagmi": "1.3.0",
                "viem": "1.10.0"
            }
        },
        "react": {
            "version": "18.2.0",
            "template": "vite",
            "dependencies": {
                "react": "18.2.0",
                "react-dom": "18.2.0",
                "ethers": "5.7.2",
                "@rainbow-me/rainbowkit": "0.12.0",
                "wagmi": "1.3.0",
                "viem": "1.10.0",
                "react-router-dom": "6.14.0"
            }
        },
        "vue": {
            "version": "3.3.0",
            "template": "vite",
            "dependencies": {
                "vue": "3.3.0",
                "ethers": "5.7.2",
                "web3": "4.0.0",
                "vue-router": "4.2.0"
            },
            "enabled": False
        }
    }
    return frameworks.get(framework, frameworks["nextjs"])

# -----------------------------------------------------------------------------
# EXPORT PUBLIC DU PACKAGE
# -----------------------------------------------------------------------------

__all__ = [
    # Agent principal
    'FrontendWeb3Agent',
    
    # Énums
    'FrameworkType',
    'ComponentType',
    'Web3Library',
    
    # Classes
    'FrontendProject',
    
    # Fonctions d'usine
    'create_frontend_web3_agent',
    
    # Fonctions utilitaires
    'load_agent_config',
    'get_supported_components',
    'get_component_description',
    'get_framework_config',
    
    # Métadonnées
    '__version__',
    '__author__',
    '__description__',
    '__capabilities__'
]

# -----------------------------------------------------------------------------
# INITIALISATION RAPIDE
# -----------------------------------------------------------------------------

def quick_start(output_dir: str = "./frontend", project_name: str = "MyWeb3App"):
    """
    Fonction de démarrage rapide pour générer une application Web3.
    
    Args:
        output_dir: Répertoire de sortie
        project_name: Nom du projet
    
    Returns:
        Instance de l'agent initialisé
    """
    agent = create_frontend_web3_agent()
    
    print(f"""
    🎨 Agent Frontend Web3 v{__version__} prêt !
    
    📁 Output: {output_dir}
    📦 Projet: {project_name}
    
    Commandes:
      agent = create_frontend_web3_agent()
      await agent.initialize()
      project = await agent.generate_project(
          project_name="{project_name}",
          contract_paths=["./contracts/YourContract.sol"],
          components=["mint_page", "dashboard"],
          framework="nextjs"
      )
    
    📚 Composants disponibles: {len(get_supported_components())}
    """)
    
    return agent


# -----------------------------------------------------------------------------
# TEST DU PACKAGE
# -----------------------------------------------------------------------------

if __name__ == "__main__":
    """Test simple du package"""
    print(f"📦 Frontend Web3 Agent v{__version__}")
    print("=" * 50)
    print(f"✅ Agent: {__description__}")
    print(f"✅ Capacités: {len(__capabilities__)}")
    print(f"✅ Composants: {len(get_supported_components())}")
    print("\n📋 Composants disponibles:")
    for comp in get_supported_components()[:5]:
        print(f"  • {comp}: {get_component_description(comp)}")
    print(f"  ... et {len(get_supported_components()) - 5} autres")
    print("\n🚀 Initialisation rapide:")
    print('  from agents.frontend_web3 import create_frontend_web3_agent')
    print('  agent = create_frontend_web3_agent("agents/frontend_web3/config.yaml")')
    print("=" * 50)
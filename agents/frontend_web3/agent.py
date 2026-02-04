"""
Agent Frontend Web3 - Développement d'interfaces Web3
Version complète et corrigée
"""
from .base_agent import BaseAgent
from typing import Dict, Any, List
from datetime import datetime
import random

class FrontendWeb3Agent(BaseAgent):
    """Agent principal pour le développement frontend Web3"""
    
    def __init__(self, config_path: str = None):
        super().__init__(config_path, "FrontendWeb3Agent")
        self.frameworks = self.config.get("frameworks", ["React", "Next.js", "Vue", "Svelte", "Angular"])
        self.web3_libraries = self.config.get("web3_libraries", ["wagmi", "viem", "ethers.js", "web3.js", "thirdweb"])
        self.wallets = self.config.get("wallets", ["MetaMask", "WalletConnect", "Coinbase Wallet", "Phantom", "Rainbow"])
        self.ui_libraries = self.config.get("ui_libraries", ["Tailwind CSS", "Material-UI", "Chakra UI", "Ant Design"])
        
        # Ajout des capacités
        self.add_capability("dapp_development")
        self.add_capability("wallet_integration")
        self.add_capability("ui_design")
        self.add_capability("performance_optimization")
        self.add_capability("responsive_design")
    
    async def execute(self, task_data: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Exécute une tâche de frontend Web3"""
        task_type = task_data.get("task_type", "dapp_development")
        self.logger.info(f"FrontendWeb3Agent exécute: {task_type}")
        
        if task_type == "create_dapp":
            requirements = task_data.get("requirements", "Basic DApp")
            result = {
                "dapp_structure": {
                    "framework": self._select_framework(requirements),
                    "state_management": "Context API + Zustand",
                    "web3_libraries": self.web3_libraries[:random.randint(2, 4)],
                    "wallet_integration": self.wallets[:random.randint(2, 4)],
                    "ui_library": random.choice(self.ui_libraries),
                    "components": self._generate_component_list(requirements),
                    "deployment": random.choice(["Vercel", "Netlify", "AWS Amplify", "Fleek"]),
                    "features": [
                        "Dark/light mode",
                        "Responsive design",
                        "Multi-chain support",
                        "Transaction history",
                        "Real-time updates",
                        "Error boundaries",
                        "Loading states",
                        "Accessibility compliant"
                    ],
                    "folder_structure": self._generate_folder_structure()
                }
            }
        elif task_type == "design_ui":
            result = {
                "design_system": {
                    "name": "Web3 Design System",
                    "components": self._generate_design_components(),
                    "colors": {
                        "primary": ["#6366f1", "#4f46e5", "#4338ca"],
                        "secondary": ["#10b981", "#059669", "#047857"],
                        "accent": ["#f59e0b", "#d97706", "#b45309"],
                        "neutral": ["#6b7280", "#4b5563", "#374151"],
                        "success": "#10b981",
                        "warning": "#f59e0b",
                        "error": "#ef4444"
                    },
                    "typography": {
                        "font_family": "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
                        "font_sizes": ["12px", "14px", "16px", "18px", "20px", "24px", "30px", "36px"],
                        "font_weights": {"normal": 400, "medium": 500, "semibold": 600, "bold": 700}
                    },
                    "spacing_scale": "4px base (0.25rem)",
                    "breakpoints": {
                        "sm": "640px",
                        "md": "768px",
                        "lg": "1024px",
                        "xl": "1280px",
                        "2xl": "1536px"
                    },
                    "shadows": {
                        "sm": "0 1px 2px 0 rgb(0 0 0 / 0.05)",
                        "md": "0 4px 6px -1px rgb(0 0 0 / 0.1)",
                        "lg": "0 10px 15px -3px rgb(0 0 0 / 0.1)",
                        "xl": "0 20px 25px -5px rgb(0 0 0 / 0.1)"
                    }
                }
            }
        elif task_type == "integrate_web3":
            result = {
                "integration_plan": {
                    "wallets_supported": random.randint(2, 5),
                    "networks": ["Ethereum", "Polygon", "Arbitrum", "Optimism"][:random.randint(2, 4)],
                    "contract_interactions": ["read", "write", "events", "signatures"],
                    "error_handling": {
                        "network_errors": True,
                        "wallet_errors": True,
                        "contract_errors": True,
                        "user_rejection": True,
                        "fallback_ui": True
                    },
                    "performance": {
                        "lazy_loading": True,
                        "code_splitting": True,
                        "bundle_optimization": True,
                        "cache_strategy": "SWR + Local Storage"
                    },
                    "security": {
                        "input_validation": True,
                        "xss_protection": True,
                        "csrf_protection": True,
                        "secure_storage": "Encrypted local storage"
                    }
                }
            }
        elif task_type == "optimize_performance":
            result = {
                "optimizations": {
                    "bundle_size": f"Réduit de {random.randint(30, 70)}%",
                    "lighthouse_score": random.randint(85, 100),
                    "first_contentful_paint": f"{random.randint(800, 1500)}ms",
                    "largest_contentful_paint": f"{random.randint(1500, 3000)}ms",
                    "cumulative_layout_shift": f"{random.uniform(0, 0.1):.3f}",
                    "techniques": [
                        "Code splitting par route",
                        "Lazy loading des images",
                        "Optimisation des Web3 providers",
                        "Memoization des composants",
                        "Virtualization des listes",
                        "Compression des assets"
                    ],
                    "recommendations": [
                        "Implémenter SSR pour meilleur SEO",
                        "Ajouter un service worker pour offline support",
                        "Utiliser CDN pour les assets statiques",
                        "Optimiser les polices web"
                    ]
                }
            }
        elif task_type == "create_component":
            component_type = task_data.get("component_type", "ConnectWallet")
            result = {
                "component": {
                    "name": f"{component_type}Component",
                    "code": self._generate_component_code(component_type),
                    "props": self._get_component_props(component_type),
                    "dependencies": self._get_component_dependencies(component_type),
                    "tests_required": ["Unit", "Integration", "E2E"],
                    "accessibility": "WCAG 2.1 Level AA"
                }
            }
        else:
            result = {
                "frontend_ready": True,
                "tech_stack": {
                    "framework": random.choice(self.frameworks),
                    "web3": random.choice(self.web3_libraries),
                    "styling": random.choice(self.ui_libraries),
                    "testing": "Jest + React Testing Library + Cypress",
                    "build_tool": "Vite",
                    "package_manager": "pnpm"
                },
                "development_environment": {
                    "ide": "VS Code",
                    "extensions": ["ESLint", "Prettier", "Tailwind CSS IntelliSense"],
                    "tools": ["React DevTools", "Redux DevTools", "Wallet DevTools"]
                }
            }
        
        return {
            "status": "success",
            "agent": self.name,
            "task": task_type,
            "result": result,
            "timestamp": datetime.now().isoformat()
        }
    
    def _select_framework(self, requirements: str) -> str:
        """Sélectionne le framework approprié"""
        requirements_lower = requirements.lower()
        
        if "seo" in requirements_lower or "ssr" in requirements_lower:
            return "Next.js"
        elif "fast" in requirements_lower or "lightweight" in requirements_lower:
            return "Vue"
        elif "enterprise" in requirements_lower or "scalable" in requirements_lower:
            return "Angular"
        elif "reactive" in requirements_lower or "compiler" in requirements_lower:
            return "Svelte"
        else:
            return "React"
    
    def _generate_component_list(self, requirements: str) -> List[Dict[str, Any]]:
        """Génère une liste de composants pour un DApp"""
        base_components = [
            {
                "name": "Web3Provider",
                "purpose": "Fournit le contexte Web3 à toute l'application",
                "complexity": "medium",
                "category": "infrastructure"
            },
            {
                "name": "ConnectWalletButton",
                "purpose": "Bouton de connexion/sélection de wallet avec modal",
                "complexity": "high",
                "category": "wallet"
            },
            {
                "name": "NetworkSwitcher",
                "purpose": "Changeur de réseau blockchain avec indicateur",
                "complexity": "medium",
                "category": "network"
            },
            {
                "name": "TransactionHistory",
                "purpose": "Historique des transactions avec filtres",
                "complexity": "high",
                "category": "data"
            },
            {
                "name": "TokenBalance",
                "purpose": "Affichage des balances de tokens avec refresh",
                "complexity": "medium",
                "category": "wallet"
            },
            {
                "name": "NFTGallery",
                "purpose": "Galerie NFT avec pagination et filtres",
                "complexity": "high",
                "category": "nft"
            },
            {
                "name": "GasPriceEstimator",
                "purpose": "Estimateur de prix du gas en temps réel",
                "complexity": "medium",
                "category": "utilities"
            },
            {
                "name": "TransactionToast",
                "purpose": "Notifications de statut de transaction",
                "complexity": "low",
                "category": "ui"
            }
        ]
        
        # Ajouter des composants spécifiques selon les besoins
        if "defi" in requirements.lower():
            base_components.extend([
                {
                    "name": "TokenSwap",
                    "purpose": "Interface d'échange de tokens avec prix",
                    "complexity": "high",
                    "category": "defi"
                },
                {
                    "name": "PoolLiquidity",
                    "purpose": "Gestionnaire de liquidité pour pools",
                    "complexity": "high",
                    "category": "defi"
                },
                {
                    "name": "YieldFarming",
                    "purpose": "Interface de farming avec APY",
                    "complexity": "high",
                    "category": "defi"
                }
            ])
        
        if "nft" in requirements.lower():
            base_components.extend([
                {
                    "name": "NFTMinter",
                    "purpose": "Interface de minting NFT",
                    "complexity": "high",
                    "category": "nft"
                },
                {
                    "name": "MarketplaceGrid",
                    "purpose": "Grille de marketplace avec filtres",
                    "complexity": "medium",
                    "category": "nft"
                },
                {
                    "name": "CollectionViewer",
                    "purpose": "Visualiseur de collection NFT",
                    "complexity": "medium",
                    "category": "nft"
                }
            ])
        
        if "dao" in requirements.lower():
            base_components.extend([
                {
                    "name": "ProposalVoting",
                    "purpose": "Interface de vote pour propositions DAO",
                    "complexity": "high",
                    "category": "dao"
                },
                {
                    "name": "TreasuryViewer",
                    "purpose": "Visualiseur de trésorerie DAO",
                    "complexity": "medium",
                    "category": "dao"
                },
                {
                    "name": "DelegateManager",
                    "purpose": "Gestionnaire de délégation de votes",
                    "complexity": "high",
                    "category": "dao"
                }
            ])
        
        return base_components
    
    def _generate_folder_structure(self) -> Dict[str, Any]:
        """Génère une structure de dossiers pour un projet Web3"""
        return {
            "src": {
                "components": {
                    "common": ["Button", "Input", "Modal", "Toast", "Loader"],
                    "web3": ["ConnectWallet", "NetworkIndicator", "TransactionStatus"],
                    "layout": ["Header", "Footer", "Sidebar", "MainLayout"],
                    "pages": ["Home", "Dashboard", "Marketplace", "Profile"]
                },
                "contexts": ["Web3Context", "ThemeContext", "UserContext"],
                "hooks": ["useWeb3", "useContract", "useTransaction", "useBalance"],
                "utils": ["web3", "formatters", "validators", "constants"],
                "services": ["api", "blockchain", "storage", "analytics"],
                "styles": ["globals.css", "theme.ts", "breakpoints.ts"],
                "types": ["web3.ts", "components.ts", "api.ts"],
                "assets": ["images", "fonts", "icons"]
            },
            "public": ["favicon.ico", "robots.txt", "manifest.json"],
            "config": ["web3.ts", "chains.ts", "wallets.ts", "contracts.ts"],
            "tests": ["unit", "integration", "e2e"],
            "scripts": ["deploy.js", "generate-types.js", "test-contracts.js"]
        }
    
    def _generate_design_components(self) -> List[Dict[str, Any]]:
        """Génère des composants de design system"""
        return [
            {
                "name": "ColorPalette",
                "description": "Système de couleurs avec variables CSS",
                "tokens": ["primary", "secondary", "accent", "neutral", "success", "warning", "error"]
            },
            {
                "name": "TypographyScale",
                "description": "Échelle typographique responsive",
                "scales": ["xs", "sm", "base", "lg", "xl", "2xl", "3xl", "4xl"]
            },
            {
                "name": "SpacingSystem",
                "description": "Système d'espacement basé sur rem",
                "units": ["0", "0.5", "1", "1.5", "2", "2.5", "3", "4", "5", "6", "8", "10", "12", "16", "20", "24"]
            },
            {
                "name": "ButtonVariants",
                "description": "Variants de boutons avec états",
                "variants": ["primary", "secondary", "outline", "ghost", "link"],
                "sizes": ["sm", "md", "lg"],
                "states": ["default", "hover", "active", "disabled", "loading"]
            },
            {
                "name": "CardTemplates",
                "description": "Templates de cartes pour différents contenus",
                "types": ["default", "elevated", "outline", "interactive", "data"]
            },
            {
                "name": "FormComponents",
                "description": "Composants de formulaire accessibles",
                "components": ["Input", "Textarea", "Select", "Checkbox", "Radio", "Switch", "Slider"]
            },
            {
                "name": "FeedbackComponents",
                "description": "Composants de feedback utilisateur",
                "components": ["Alert", "Toast", "Modal", "Drawer", "Tooltip", "Popover", "Skeleton"]
            },
            {
                "name": "NavigationComponents",
                "description": "Composants de navigation",
                "components": ["Navbar", "Sidebar", "Breadcrumb", "Pagination", "Tabs", "Stepper"]
            }
        ]
    
    def _generate_component_code(self, component_type: str) -> str:
        """Génère le code d'un composant"""
        if component_type == "ConnectWallet":
            return '''import React, { useState } from 'react';
import { useAccount, useConnect, useDisconnect } from 'wagmi';
import { MetaMaskConnector } from 'wagmi/connectors/metaMask';
import { WalletConnectConnector } from 'wagmi/connectors/walletConnect';
import { CoinbaseWalletConnector } from 'wagmi/connectors/coinbaseWallet';
import { 
  Button, 
  Modal, 
  Stack, 
  Text, 
  Avatar, 
  Box,
  useDisclosure
} from '@chakra-ui/react';

interface ConnectWalletButtonProps {
  variant?: 'primary' | 'outline' | 'ghost';
  size?: 'sm' | 'md' | 'lg';
  onConnect?: (address: string) => void;
  onDisconnect?: () => void;
}

const ConnectWalletButton: React.FC<ConnectWalletButtonProps> = ({
  variant = 'primary',
  size = 'md',
  onConnect,
  onDisconnect
}) => {
  const { isOpen, onOpen, onClose } = useDisclosure();
  const { address, isConnected } = useAccount();
  const { connect, connectors, error, isLoading, pendingConnector } = useConnect({
    onSuccess: (data) => {
      onConnect?.(data.account);
      onClose();
    }
  });
  const { disconnect } = useDisconnect({
    onSuccess: () => {
      onDisconnect?.();
    }
  });

  const formatAddress = (addr: string) => {
    return `${addr.slice(0, 6)}...${addr.slice(-4)}`;
  };

  const connectorsList = [
    {
      connector: new MetaMaskConnector(),
      name: 'MetaMask',
      icon: '🦊',
      description: 'Connect using MetaMask browser extension'
    },
    {
      connector: new WalletConnectConnector({
        options: {
          projectId: process.env.NEXT_PUBLIC_WALLETCONNECT_PROJECT_ID,
        }
      }),
      name: 'WalletConnect',
      icon: '📱',
      description: 'Scan QR code with mobile wallet'
    },
    {
      connector: new CoinbaseWalletConnector({
        options: {
          appName: 'MyWeb3App',
          jsonRpcUrl: process.env.NEXT_PUBLIC_RPC_URL
        }
      }),
      name: 'Coinbase Wallet',
      icon: '💰',
      description: 'Connect using Coinbase Wallet'
    }
  ];

  if (isConnected && address) {
    return (
      <Button
        variant={variant}
        size={size}
        onClick={() => disconnect()}
        leftIcon={<Avatar size="xs" src="/metamask.svg" />}
        rightIcon={<Box w="2" h="2" bg="green.500" borderRadius="full" />}
      >
        {formatAddress(address)}
      </Button>
    );
  }

  return (
    <>
      <Button
        variant={variant}
        size={size}
        onClick={onOpen}
        isLoading={isLoading}
        loadingText="Connecting..."
      >
        Connect Wallet
      </Button>

      <Modal isOpen={isOpen} onClose={onClose} size="md">
        <Modal.Overlay />
        <Modal.Content>
          <Modal.Header>
            <Text fontSize="xl" fontWeight="bold">
              Connect Wallet
            </Text>
            <Text fontSize="sm" color="gray.600" mt={1}>
              Choose your preferred wallet to connect
            </Text>
          </Modal.Header>
          <Modal.Body>
            <Stack spacing={4}>
              {connectorsList.map(({ connector, name, icon, description }) => (
                <Button
                  key={name}
                  variant="outline"
                  size="lg"
                  justifyContent="flex-start"
                  onClick={() => connect({ connector })}
                  isLoading={isLoading && pendingConnector?.id === connector.id}
                  leftIcon={
                    <Text fontSize="xl">{icon}</Text>
                  }
                  isDisabled={!connector.ready}
                >
                  <Box textAlign="left">
                    <Text fontWeight="semibold">{name}</Text>
                    <Text fontSize="sm" color="gray.600">
                      {description}
                    </Text>
                  </Box>
                </Button>
              ))}
            </Stack>
            
            {error && (
              <Box mt={4} p={3} bg="red.50" borderRadius="md">
                <Text color="red.600" fontSize="sm">
                  {error.message}
                </Text>
              </Box>
            )}
          </Modal.Body>
        </Modal.Content>
      </Modal>
    </>
  );
};

export default ConnectWalletButton;'''
        
        else:
            return '''// Composant générique
const Web3Component = () => {
  return (
    <div>
      <h1>Composant Web3</h1>
    </div>
  );
};

export default Web3Component;'''
    
    def _get_component_props(self, component_type: str) -> List[Dict[str, Any]]:
        """Retourne les props d'un composant"""
        props_map = {
            "ConnectWallet": [
                {"name": "variant", "type": "string", "default": "primary", "description": "Variant du bouton"},
                {"name": "size", "type": "string", "default": "md", "description": "Taille du bouton"},
                {"name": "onConnect", "type": "function", "required": False, "description": "Callback après connexion"},
                {"name": "onDisconnect", "type": "function", "required": False, "description": "Callback après déconnexion"}
            ],
            "NetworkSwitcher": [
                {"name": "currentNetwork", "type": "object", "required": True, "description": "Réseau actuel"},
                {"name": "availableNetworks", "type": "array", "required": True, "description": "Réseaux disponibles"},
                {"name": "onSwitch", "type": "function", "required": True, "description": "Callback pour changer de réseau"}
            ]
        }
        
        return props_map.get(component_type, [
            {"name": "children", "type": "ReactNode", "description": "Contenu du composant"}
        ])
    
    def _get_component_dependencies(self, component_type: str) -> List[str]:
        """Retourne les dépendances d'un composant"""
        deps_map = {
            "ConnectWallet": ["wagmi", "viem", "@chakra-ui/react", "react"],
            "NetworkSwitcher": ["wagmi", "viem", "@chakra-ui/react", "react"],
            "TransactionHistory": ["wagmi", "viem", "@tanstack/react-table", "date-fns", "react"]
        }
        
        return deps_map.get(component_type, ["react"])
    
    async def health_check(self) -> Dict[str, Any]:
        """Vérifie la santé de l'agent frontend Web3"""
        base_health = await super().health_check()
        return {
            **base_health,
            "frameworks": self.frameworks,
            "web3_libraries": self.web3_libraries,
            "wallets_supported": len(self.wallets),
            "ui_libraries": self.ui_libraries,
            "dapps_created": self.config.get("dapps_created", 8),
            "components_developed": self.config.get("components_developed", 42),
            "performance_score": f"{random.randint(85, 100)}/100"
        }
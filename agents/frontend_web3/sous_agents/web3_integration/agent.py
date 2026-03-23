#!/usr/bin/env python3
"""
Web3Integration SubAgent - Expert Intégration Web3
Version: 2.0.0 (ALIGNÉ SUR CIRCUIT_BREAKER)

Expert en intégration blockchain avec wagmi, viem, ethers.js,
support multi-chaînes, gestion de wallets et interactions avec contrats.
"""

import logging
import sys
import asyncio
import json
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, Optional, List, Union, Callable
from enum import Enum
from dataclasses import dataclass, field
import uuid

# Configuration des imports
current_dir = Path(__file__).parent.absolute()
# Définir project_root
project_root = Path(__file__).parent.parent.parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from agents.sous_agents.base_subagent import BaseSubAgent
from agents.base_agent.base_agent import Message, MessageType, AgentStatus

logger = logging.getLogger(__name__)


# ============================================================================
# ÉNUMS ET CLASSES DE DONNÉES
# ============================================================================

class ChainType(Enum):
    """Types de blockchains supportées"""
    ETHEREUM = "ethereum"
    POLYGON = "polygon"
    ARBITRUM = "arbitrum"
    OPTIMISM = "optimism"
    BSC = "bsc"
    AVALANCHE = "avalanche"
    BASE = "base"
    
    @classmethod
    def from_string(cls, chain_str: str) -> 'ChainType':
        mapping = {
            "ethereum": cls.ETHEREUM,
            "polygon": cls.POLYGON,
            "arbitrum": cls.ARBITRUM,
            "optimism": cls.OPTIMISM,
            "bsc": cls.BSC,
            "avalanche": cls.AVALANCHE,
            "base": cls.BASE
        }
        return mapping.get(chain_str.lower(), cls.ETHEREUM)


class LibraryType(Enum):
    """Types de bibliothèques Web3"""
    WAGMI = "wagmi"
    VIEM = "viem"
    ETHERS = "ethers"
    WEB3_JS = "web3.js"


@dataclass
class WalletConfig:
    """Configuration de wallet"""
    project_id: str = ""
    chains: List[ChainType] = field(default_factory=lambda: [ChainType.ETHEREUM])
    library: LibraryType = LibraryType.WAGMI
    auto_connect: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "project_id": self.project_id[:10] + "..." if self.project_id else "",
            "chains": [c.value for c in self.chains],
            "library": self.library.value,
            "auto_connect": self.auto_connect
        }


@dataclass
class ContractConfig:
    """Configuration de contrat"""
    address: str
    abi: List[Dict[str, Any]] = field(default_factory=list)
    name: str = ""
    chain: ChainType = ChainType.ETHEREUM
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "address": self.address,
            "name": self.name,
            "chain": self.chain.value,
            "abi_functions": len([i for i in self.abi if i.get("type") == "function"])
        }


@dataclass
class Web3GenerationResult:
    """Résultat de génération d'intégration Web3"""
    result_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    result_type: str = ""
    code: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    processing_time_ms: float = 0.0
    success: bool = True
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "result_id": self.result_id,
            "result_type": self.result_type,
            "code": self.code[:500] + "..." if len(self.code) > 500 else self.code,
            "created_at": self.created_at.isoformat(),
            "processing_time_ms": self.processing_time_ms,
            "success": self.success,
            "error": self.error,
            "metadata": self.metadata
        }


@dataclass
class Web3Stats:
    """Statistiques d'intégration Web3"""
    integrations_generated: int = 0
    integrations_succeeded: int = 0
    integrations_failed: int = 0
    by_type: Dict[str, int] = field(default_factory=dict)
    by_chain: Dict[str, int] = field(default_factory=dict)
    by_library: Dict[str, int] = field(default_factory=dict)
    total_processing_time: float = 0.0
    avg_processing_time: float = 0.0
    last_generation: Optional[datetime] = None
    start_time: datetime = field(default_factory=datetime.now)
    
    def record_generation(self, result_type: str, chain: ChainType, library: LibraryType,
                          processing_time: float, success: bool):
        """Enregistre une génération"""
        self.integrations_generated += 1
        if success:
            self.integrations_succeeded += 1
        else:
            self.integrations_failed += 1
            
        self.total_processing_time += processing_time
        self.avg_processing_time = self.total_processing_time / self.integrations_generated
        self.last_generation = datetime.now()
        
        # Statistiques par type
        self.by_type[result_type] = self.by_type.get(result_type, 0) + 1
        self.by_chain[chain.value] = self.by_chain.get(chain.value, 0) + 1
        self.by_library[library.value] = self.by_library.get(library.value, 0) + 1
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "integrations_generated": self.integrations_generated,
            "integrations_succeeded": self.integrations_succeeded,
            "integrations_failed": self.integrations_failed,
            "by_type": self.by_type,
            "by_chain": self.by_chain,
            "by_library": self.by_library,
            "avg_processing_time_ms": round(self.avg_processing_time, 2),
            "total_processing_time_ms": round(self.total_processing_time, 2),
            "last_generation": self.last_generation.isoformat() if self.last_generation else None,
            "uptime_seconds": (datetime.now() - self.start_time).total_seconds()
        }


# ============================================================================
# SOUS-AGENT PRINCIPAL
# ============================================================================

class Web3IntegrationSubAgent(BaseSubAgent):
    """
    Sous-agent expert intégration Web3
    
    Génère des connecteurs de wallet, interactions avec contrats,
    gestion de transactions et support multi-chaînes.
    """
    
    def __init__(self, config_path: str = ""):
        """Initialise l'expert Web3"""
        # 🔧 CORRECTION : Résoudre le chemin absolu
        if not config_path:
            config_path = str(Path(__file__).parent / "config.yaml")
        elif not Path(config_path).is_absolute():
            config_path = str(project_root / config_path)
        
        logger.debug(f"🔧 Chargement config depuis: {config_path}")
        super().__init__(config_path)
        
        # Récupérer la configuration
        if 'subagent' in self._config:
            config = self._config.get('subagent', {})
        elif 'agent' in self._config:
            config = self._config.get('agent', {})
        else:
            config = {}
        
        # Métadonnées
        self._subagent_display_name = config.get('display_name', "🔗 Expert Intégration Web3")
        self._subagent_description = config.get('description', "Intégration Web3 (wagmi, viem, ethers)")
        self._subagent_version = config.get('version', "2.0.0")
        self._subagent_category = config.get('category', "frontend_web3")
        self._subagent_capabilities = [
            "web3.generate_wallet_connector",
            "web3.generate_contract_interaction",
            "web3.generate_transaction_builder",
            "web3.generate_events_listener",
            "web3.generate_network_config",
            "web3.generate_abi_loader"
        ]
        
        # Templates
        self._templates = self._load_templates()
        
        # Statistiques
        self._stats = Web3Stats()
        
        # File d'attente pour les événements
        self._event_queue: asyncio.Queue = asyncio.Queue()
        
        # Tâche de traitement
        self._processor_task: Optional[asyncio.Task] = None
        
        logger.info(f"✅ {self._subagent_display_name} initialisé")

    # ============================================================================
    # INITIALISATION
    # ============================================================================
    
    async def _initialize_subagent_components(self) -> bool:
        """Initialise les composants spécifiques"""
        logger.info("Initialisation des composants Web3 Integration...")
        
        # Démarrer la tâche de traitement
        self._processor_task = asyncio.create_task(self._processor_loop())
        
        self._components = {
            "version": self._subagent_version,
            "chains": [c.value for c in ChainType],
            "libraries": [l.value for l in LibraryType],
            "templates": list(self._templates.keys())
        }
        
        logger.info("✅ Composants Web3 Integration initialisés")
        return True
        
    async def _initialize_components(self) -> bool:
        """Implémentation requise par BaseAgent"""
        return await self._initialize_subagent_components()

    def _get_capability_handlers(self) -> Dict[str, Callable]:
        """Retourne les handlers spécifiques"""
        return {
            "web3.generate_wallet_connector": self._handle_generate_wallet_connector,
            "web3.generate_contract_interaction": self._handle_generate_contract_interaction,
            "web3.generate_transaction_builder": self._handle_generate_transaction_builder,
            "web3.generate_events_listener": self._handle_generate_events_listener,
            "web3.generate_network_config": self._handle_generate_network_config,
            "web3.generate_abi_loader": self._handle_generate_abi_loader,
        }
    
    # ============================================================================
    # TEMPLATES
    # ============================================================================
    
    def _load_templates(self) -> Dict[str, str]:
        """Charge les templates d'intégration Web3"""
        return {
            "wallet_connector": """
import {{ configureChains, createConfig }} from 'wagmi'
import {{ mainnet, polygon, arbitrum, optimism }} from 'wagmi/chains'
import {{ publicProvider }} from 'wagmi/providers/public'
import {{ MetaMaskConnector }} from 'wagmi/connectors/metaMask'
import {{ WalletConnectConnector }} from 'wagmi/connectors/walletConnect'

const {chains} = [{chain_list}]

const {{ publicClient, webSocketPublicClient }} = configureChains(
  chains,
  [publicProvider()]
)

export const config = createConfig({{
  autoConnect: true,
  connectors: [
    new MetaMaskConnector({{ chains }}),
    new WalletConnectConnector({{
      chains,
      options: {{
        projectId: '{project_id}',
        showQrModal: true,
      }},
    }}),
  ],
  publicClient,
  webSocketPublicClient,
}})
""",
            "contract_interaction": """
import {{ useContractRead, useContractWrite, usePrepareContractWrite }} from 'wagmi'
import {{ abi }} from './{contract_name}.json'

const contractAddress = '{contract_address}'

export function use{contract_name}() {{
  // Read functions
  const {{ data: balance }} = useContractRead({{
    address: contractAddress,
    abi,
    functionName: 'balanceOf',
    args: [address],
  }})

  // Write functions
  const {{ config }} = usePrepareContractWrite({{
    address: contractAddress,
    abi,
    functionName: 'transfer',
    args: [to, amount],
  }})
  
  const {{ write: transfer }} = useContractWrite(config)

  return {{
    balance,
    transfer,
  }}
}}
""",
            "transaction_builder": """
import {{ parseEther }} from 'viem'
import {{ useSendTransaction, usePrepareSendTransaction }} from 'wagmi'

export function useTransaction() {{
  const {{ config }} = usePrepareSendTransaction({{
    to: '{to_address}',
    value: parseEther('{value}'),
  }})
  
  const {{ sendTransaction }} = useSendTransaction(config)
  
  return {{ sendTransaction }}
}}
"""
        }
    
    # ============================================================================
    # TÂCHES DE FOND
    # ============================================================================
    
    async def _processor_loop(self):
        """Boucle de traitement"""
        logger.info("🔄 Boucle de traitement démarrée")
        
        while self._status.value == "ready":
            try:
                while not self._event_queue.empty():
                    event = await self._event_queue.get()
                    await self._process_event(event)
                await asyncio.sleep(1)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"❌ Erreur dans la boucle: {e}")
                await asyncio.sleep(5)
    
    async def _process_event(self, event: Dict[str, Any]):
        """Traite un événement"""
        pass
    
    # ============================================================================
    # GÉNÉRATION D'INTÉGRATIONS
    # ============================================================================
    
    async def generate_wallet_connector(self, config: WalletConfig) -> Web3GenerationResult:
        """Génère un connecteur de wallet"""
        start_time = time.time()
        result = Web3GenerationResult(result_type="wallet_connector")
        
        try:
            template = self._templates.get("wallet_connector", self._templates["wallet_connector"])
            
            chain_list = ", ".join([c.value for c in config.chains])
            
            result.code = template.format(
                chains=", ".join([c.value for c in config.chains]),
                chain_list=chain_list,
                project_id=config.project_id or "YOUR_PROJECT_ID"
            )
            result.success = True
            
            processing_time = (time.time() - start_time) * 1000
            result.processing_time_ms = processing_time
            self._stats.record_generation("wallet_connector", config.chains[0], config.library, processing_time, True)
            
            await self._log_event("wallet_connector_generated", {
                "result_id": result.result_id,
                "chains": [c.value for c in config.chains],
                "library": config.library.value,
                "processing_time_ms": processing_time
            })
            
        except Exception as e:
            result.success = False
            result.error = str(e)
            processing_time = (time.time() - start_time) * 1000
            result.processing_time_ms = processing_time
            self._stats.record_generation("wallet_connector", ChainType.ETHEREUM, LibraryType.WAGMI, processing_time, False)
            logger.error(f"❌ Erreur génération wallet connector: {e}")
        
        return result
    
    async def generate_contract_interaction(self, config: ContractConfig) -> Web3GenerationResult:
        """Génère une interaction avec contrat"""
        start_time = time.time()
        result = Web3GenerationResult(result_type="contract_interaction")
        
        try:
            template = self._templates.get("contract_interaction", self._templates["contract_interaction"])
            
            result.code = template.format(
                contract_name=config.name or "Contract",
                contract_address=config.address
            )
            result.success = True
            
            processing_time = (time.time() - start_time) * 1000
            result.processing_time_ms = processing_time
            self._stats.record_generation("contract_interaction", config.chain, LibraryType.WAGMI, processing_time, True)
            
        except Exception as e:
            result.success = False
            result.error = str(e)
            processing_time = (time.time() - start_time) * 1000
            result.processing_time_ms = processing_time
            self._stats.record_generation("contract_interaction", config.chain, LibraryType.WAGMI, processing_time, False)
        
        return result
    
    async def generate_transaction_builder(self, to_address: str, value: str = "0.1") -> Web3GenerationResult:
        """Génère un constructeur de transactions"""
        start_time = time.time()
        result = Web3GenerationResult(result_type="transaction_builder")
        
        try:
            template = self._templates.get("transaction_builder", self._templates["transaction_builder"])
            
            result.code = template.format(
                to_address=to_address,
                value=value
            )
            result.success = True
            
            processing_time = (time.time() - start_time) * 1000
            result.processing_time_ms = processing_time
            self._stats.record_generation("transaction_builder", ChainType.ETHEREUM, LibraryType.WAGMI, processing_time, True)
            
        except Exception as e:
            result.success = False
            result.error = str(e)
            processing_time = (time.time() - start_time) * 1000
            result.processing_time_ms = processing_time
            self._stats.record_generation("transaction_builder", ChainType.ETHEREUM, LibraryType.WAGMI, processing_time, False)
        
        return result
    
    async def generate_events_listener(self, contract_config: ContractConfig) -> Web3GenerationResult:
        """Génère un écouteur d'événements"""
        start_time = time.time()
        result = Web3GenerationResult(result_type="events_listener")
        
        try:
            code = f"""
import {{ useContractEvent }} from 'wagmi'
import {{ abi }} from './{contract_config.name or "Contract"}.json'

export function use{contract_config.name or "Contract"}Events() {{
  useContractEvent({{
    address: '{contract_config.address}',
    abi,
    eventName: 'Transfer',
    listener: (from, to, value) => {{
      console.log(`Transfer: ${{from}} -> ${{to}} | ${{value}}`)
    }},
  }})

  useContractEvent({{
    address: '{contract_config.address}',
    abi,
    eventName: 'Approval',
    listener: (owner, spender, value) => {{
      console.log(`Approval: ${{owner}} -> ${{spender}} | ${{value}}`)
    }},
  }})
}}
"""
            result.code = code
            result.success = True
            
            processing_time = (time.time() - start_time) * 1000
            result.processing_time_ms = processing_time
            self._stats.record_generation("events_listener", contract_config.chain, LibraryType.WAGMI, processing_time, True)
            
        except Exception as e:
            result.success = False
            result.error = str(e)
            processing_time = (time.time() - start_time) * 1000
            result.processing_time_ms = processing_time
            self._stats.record_generation("events_listener", contract_config.chain, LibraryType.WAGMI, processing_time, False)
        
        return result
    
    async def generate_network_config(self, chains: List[ChainType]) -> Web3GenerationResult:
        """Génère une configuration réseau"""
        start_time = time.time()
        result = Web3GenerationResult(result_type="network_config")
        
        try:
            networks = {}
            for chain in chains:
                networks[chain.value] = {
                    "chainId": self._get_chain_id(chain),
                    "rpcUrl": f"https://{chain.value}.rpc.com",
                    "explorer": f"https://{chain.value}.scan.com"
                }
            
            code = f"""
export const networks = {json.dumps(networks, indent=2)}

export const switchNetwork = async (ethereum, chainId) => {{
  try {{
    await ethereum.request({{
      method: 'wallet_switchEthereumChain',
      params: [{{ chainId: `0x${{chainId.toString(16)}}` }}],
    }})
  }} catch (error) {{
    console.error('Failed to switch network:', error)
  }}
}}
"""
            result.code = code
            result.success = True
            
            processing_time = (time.time() - start_time) * 1000
            result.processing_time_ms = processing_time
            self._stats.record_generation("network_config", chains[0] if chains else ChainType.ETHEREUM, LibraryType.WAGMI, processing_time, True)
            
        except Exception as e:
            result.success = False
            result.error = str(e)
            processing_time = (time.time() - start_time) * 1000
            result.processing_time_ms = processing_time
            self._stats.record_generation("network_config", ChainType.ETHEREUM, LibraryType.WAGMI, processing_time, False)
        
        return result
    
    async def generate_abi_loader(self, contract_address: str) -> Web3GenerationResult:
        """Génère un chargeur d'ABI"""
        start_time = time.time()
        result = Web3GenerationResult(result_type="abi_loader")
        
        try:
            code = f"""
import {{ ethers }} from 'ethers'

export class ABILoader {{
  constructor(provider) {{
    this.provider = provider
    this.cache = new Map()
  }}

  async loadABI(address) {{
    if (this.cache.has(address)) {{
      return this.cache.get(address)
    }}

    try {{
      const response = await fetch(
        `https://api.etherscan.io/api?module=contract&action=getabi&address=${{address}}`
      )
      const data = await response.json()
      
      if (data.status === '1') {{
        const abi = JSON.parse(data.result)
        this.cache.set(address, abi)
        return abi
      }}
    }} catch (error) {{
      console.warn('Failed to fetch ABI:', error)
    }}

    const minimalABI = [
      'function name() view returns (string)',
      'function symbol() view returns (string)',
      'function totalSupply() view returns (uint256)',
      'function balanceOf(address) view returns (uint256)',
      'function transfer(address to, uint256 amount) returns (bool)',
      'event Transfer(address indexed from, address indexed to, uint256 value)'
    ]
    
    this.cache.set(address, minimalABI)
    return minimalABI
  }}

  async getContract(address, signerOrProvider) {{
    const abi = await this.loadABI(address)
    return new ethers.Contract(address, abi, signerOrProvider)
  }}
}}

export default new ABILoader()
"""
            result.code = code
            result.success = True
            
            processing_time = (time.time() - start_time) * 1000
            result.processing_time_ms = processing_time
            self._stats.record_generation("abi_loader", ChainType.ETHEREUM, LibraryType.ETHERS, processing_time, True)
            
        except Exception as e:
            result.success = False
            result.error = str(e)
            processing_time = (time.time() - start_time) * 1000
            result.processing_time_ms = processing_time
            self._stats.record_generation("abi_loader", ChainType.ETHEREUM, LibraryType.ETHERS, processing_time, False)
        
        return result
    
    def _get_chain_id(self, chain: ChainType) -> int:
        """Retourne l'ID de la chaîne"""
        ids = {
            ChainType.ETHEREUM: 1,
            ChainType.POLYGON: 137,
            ChainType.ARBITRUM: 42161,
            ChainType.OPTIMISM: 10,
            ChainType.BSC: 56,
            ChainType.AVALANCHE: 43114,
            ChainType.BASE: 8453
        }
        return ids.get(chain, 1)
    
    # ============================================================================
    # HANDLERS DE CAPACITÉS
    # ============================================================================
    
    async def _handle_generate_wallet_connector(self, params: Dict[str, Any]) -> Dict[str, Any]:
        chains = [ChainType.from_string(c) for c in params.get("chains", ["ethereum"])]
        config = WalletConfig(
            project_id=params.get("project_id", ""),
            chains=chains,
            library=LibraryType.from_string(params.get("library", "wagmi")),
            auto_connect=params.get("auto_connect", True)
        )
        result = await self.generate_wallet_connector(config)
        return result.to_dict()
    
    async def _handle_generate_contract_interaction(self, params: Dict[str, Any]) -> Dict[str, Any]:
        config = ContractConfig(
            address=params.get("address", "0x..."),
            abi=params.get("abi", []),
            name=params.get("name", "Contract"),
            chain=ChainType.from_string(params.get("chain", "ethereum"))
        )
        result = await self.generate_contract_interaction(config)
        return result.to_dict()
    
    async def _handle_generate_transaction_builder(self, params: Dict[str, Any]) -> Dict[str, Any]:
        to_address = params.get("to", "0x...")
        value = params.get("value", "0.1")
        result = await self.generate_transaction_builder(to_address, value)
        return result.to_dict()
    
    async def _handle_generate_events_listener(self, params: Dict[str, Any]) -> Dict[str, Any]:
        config = ContractConfig(
            address=params.get("address", "0x..."),
            abi=params.get("abi", []),
            name=params.get("name", "Contract"),
            chain=ChainType.from_string(params.get("chain", "ethereum"))
        )
        result = await self.generate_events_listener(config)
        return result.to_dict()
    
    async def _handle_generate_network_config(self, params: Dict[str, Any]) -> Dict[str, Any]:
        chains = [ChainType.from_string(c) for c in params.get("chains", ["ethereum"])]
        result = await self.generate_network_config(chains)
        return result.to_dict()
    
    async def _handle_generate_abi_loader(self, params: Dict[str, Any]) -> Dict[str, Any]:
        address = params.get("address", "0x...")
        result = await self.generate_abi_loader(address)
        return result.to_dict()
    
    # ============================================================================
    # GESTION DES MESSAGES
    # ============================================================================
    
    def _get_standard_handlers(self) -> Dict[str, Callable]:
        return {
            f"{self.name}.status": self._handle_status,
            f"{self.name}.metrics": self._handle_metrics,
            f"{self.name}.health": self._handle_health,
            f"{self.name}.capabilities": self._handle_capabilities,
            f"{self.name}.info": self._handle_info,
            f"{self.name}.stats": self._handle_stats,
        }
    
    async def _handle_status(self, message: Message) -> Message:
        return Message(
            sender=self.name,
            recipient=message.sender,
            content={
                'status': self._status.value,
                'initialized': self._initialized,
                'display_name': self._subagent_display_name,
                'stats': self._stats.to_dict()
            },
            message_type=f"{self.name}.status_response",
            correlation_id=message.message_id
        )
    
    async def _handle_metrics(self, message: Message) -> Message:
        return Message(
            sender=self.name,
            recipient=message.sender,
            content=self._stats.to_dict(),
            message_type=f"{self.name}.metrics_response",
            correlation_id=message.message_id
        )
    
    async def _handle_health(self, message: Message) -> Message:
        health = await self.health_check()
        return Message(
            sender=self.name,
            recipient=message.sender,
            content=health,
            message_type=f"{self.name}.health_response",
            correlation_id=message.message_id
        )
    
    async def _handle_capabilities(self, message: Message) -> Message:
        return Message(
            sender=self.name,
            recipient=message.sender,
            content={
                'capabilities': self._subagent_capabilities,
                'version': self._subagent_version,
                'display_name': self._subagent_display_name,
                'category': self._subagent_category
            },
            message_type=f"{self.name}.capabilities_response",
            correlation_id=message.message_id
        )
    
    async def _handle_info(self, message: Message) -> Message:
        return Message(
            sender=self.name,
            recipient=message.sender,
            content=self.get_agent_info(),
            message_type=f"{self.name}.info_response",
            correlation_id=message.message_id
        )
    
    async def _handle_stats(self, message: Message) -> Message:
        return Message(
            sender=self.name,
            recipient=message.sender,
            content=self._stats.to_dict(),
            message_type=f"{self.name}.stats_response",
            correlation_id=message.message_id
        )
    
    async def handle_message(self, message: Message) -> Optional[Message]:
        try:
            msg_type = message.message_type
            logger.debug(f"📨 Message reçu: {msg_type} de {message.sender}")

            handlers = self._get_standard_handlers()
            handlers.update(self._get_capability_handlers())

            if msg_type in handlers:
                handler = getattr(self, handlers[msg_type], None)
                if handler:
                    result = await handler(message.content)
                    return Message(
                        sender=self.name,
                        recipient=message.sender,
                        content=result,
                        message_type=f"{msg_type}_response",
                        correlation_id=message.message_id
                    )

            return None

        except Exception as e:
            logger.error(f"❌ Erreur: {e}")
            return Message(
                sender=self.name,
                recipient=message.sender,
                content={"error": str(e)},
                message_type=MessageType.ERROR.value,
                correlation_id=message.message_id
            )
    
    # ============================================================================
    # UTILITAIRES
    # ============================================================================
    
    async def _log_event(self, event_type: str, data: Dict[str, Any]):
        event = {"type": event_type, "timestamp": datetime.now().isoformat(), "data": data}
        await self._event_queue.put(event)
        logger.info(f"📋 Événement: {event_type}")
    
    # ============================================================================
    # SANTÉ ET STATISTIQUES
    # ============================================================================
    
    async def health_check(self) -> Dict[str, Any]:
        base_health = await super().health_check()
        
        issues = []
        if self._event_queue.qsize() > 100:
            issues.append(f"File d'événements élevée: {self._event_queue.qsize()}")
        
        health_status = "healthy" if not issues else "degraded"

        return {
            **base_health,
            "agent": self.name,
            "display_name": self._subagent_display_name,
            "category": self._subagent_category,
            "status": self._status.value,
            "ready": self._status == AgentStatus.READY,
            "initialized": self._initialized,
            "health_status": health_status,
            "issues": issues,
            "stats": self._stats.to_dict(),
            "components": self._components,
            "timestamp": datetime.now().isoformat()
        }
    
    def get_agent_info(self) -> Dict[str, Any]:
        return {
            "id": self.name,
            "name": self.__class__.__name__,
            "display_name": self._subagent_display_name,
            "category": self._subagent_category,
            "version": self._subagent_version,
            "description": self._subagent_description,
            "status": self._status.value,
            "capabilities": self._subagent_capabilities,
            "parent_agent": self._config.get('parent_relationship', {}).get('parent_name', 'frontend_web3'),
            "stats": self._stats.to_dict()
        }
    
    async def get_stats(self) -> Dict[str, Any]:
        return self._stats.to_dict()
    
    async def shutdown(self) -> bool:
        logger.info(f"Arrêt de {self._subagent_display_name}...")
        
        if self._processor_task and not self._processor_task.done():
            self._processor_task.cancel()
            try:
                await self._processor_task
            except asyncio.CancelledError:
                pass
        
        try:
            await super().shutdown()
        except Exception:
            pass
        
        logger.info(f"✅ {self._subagent_display_name} arrêté")
        return True
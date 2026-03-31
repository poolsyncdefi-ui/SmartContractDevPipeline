"""
Blockchain Architect SubAgent - Spécialiste en architecture blockchain
Version: 2.0.0 (ALIGNÉ SUR BACKEND ARCHITECT)

Expert en conception d'architectures blockchain multi-chaînes (Ethereum, Polygon, Arbitrum, Solana)
avec smart contracts, tokenomics, DeFi, NFT, et cross-chain bridges.
"""

import logging
import sys
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
from enum import Enum
from dataclasses import dataclass, field

# Configuration des imports
current_dir = Path(__file__).parent.absolute()
project_root = current_dir.parent.parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from agents.sous_agents.base_subagent import BaseSubAgent
from agents.base_agent.base_agent import Message, MessageType, AgentCapability

logger = logging.getLogger(__name__)


# ============================================================================
# ÉNUMS ET CLASSES DE DONNÉES
# ============================================================================

class BlockchainType(Enum):
    """Types de blockchains supportées"""
    ETHEREUM = "ethereum"
    POLYGON = "polygon"
    ARBITRUM = "arbitrum"
    OPTIMISM = "optimism"
    BASE = "base"
    SOLANA = "solana"
    AVALANCHE = "avalanche"
    BSC = "bsc"
    FANTOM = "fantom"
    CELO = "celo"
    MOONBEAM = "moonbeam"
    
    @classmethod
    def from_string(cls, chain_str: str) -> 'BlockchainType':
        mapping = {
            "ethereum": cls.ETHEREUM, "eth": cls.ETHEREUM,
            "polygon": cls.POLYGON, "matic": cls.POLYGON,
            "arbitrum": cls.ARBITRUM, "arb": cls.ARBITRUM,
            "optimism": cls.OPTIMISM, "op": cls.OPTIMISM,
            "base": cls.BASE,
            "solana": cls.SOLANA, "sol": cls.SOLANA,
            "avalanche": cls.AVALANCHE, "avax": cls.AVALANCHE,
            "bsc": cls.BSC, "bnb": cls.BSC,
            "fantom": cls.FANTOM, "ftm": cls.FANTOM,
            "celo": cls.CELO,
            "moonbeam": cls.MOONBEAM, "glmr": cls.MOONBEAM
        }
        return mapping.get(chain_str.lower(), cls.ETHEREUM)
    
    def get_display_name(self) -> str:
        names = {
            BlockchainType.ETHEREUM: "Ethereum",
            BlockchainType.POLYGON: "Polygon",
            BlockchainType.ARBITRUM: "Arbitrum",
            BlockchainType.OPTIMISM: "Optimism",
            BlockchainType.BASE: "Base",
            BlockchainType.SOLANA: "Solana",
            BlockchainType.AVALANCHE: "Avalanche",
            BlockchainType.BSC: "Binance Smart Chain",
            BlockchainType.FANTOM: "Fantom",
            BlockchainType.CELO: "Celo",
            BlockchainType.MOONBEAM: "Moonbeam"
        }
        return names.get(self, "Unknown")
    
    def get_chain_id(self) -> int:
        ids = {
            BlockchainType.ETHEREUM: 1,
            BlockchainType.POLYGON: 137,
            BlockchainType.ARBITRUM: 42161,
            BlockchainType.OPTIMISM: 10,
            BlockchainType.BASE: 8453,
            BlockchainType.SOLANA: 0,
            BlockchainType.AVALANCHE: 43114,
            BlockchainType.BSC: 56,
            BlockchainType.FANTOM: 250,
            BlockchainType.CELO: 42220,
            BlockchainType.MOONBEAM: 1284
        }
        return ids.get(self, 0)
    
    def is_evm_compatible(self) -> bool:
        return self not in [BlockchainType.SOLANA]
    
    def get_currency_symbol(self) -> str:
        symbols = {
            BlockchainType.ETHEREUM: "ETH",
            BlockchainType.POLYGON: "MATIC",
            BlockchainType.ARBITRUM: "ETH",
            BlockchainType.OPTIMISM: "ETH",
            BlockchainType.BASE: "ETH",
            BlockchainType.SOLANA: "SOL",
            BlockchainType.AVALANCHE: "AVAX",
            BlockchainType.BSC: "BNB",
            BlockchainType.FANTOM: "FTM",
            BlockchainType.CELO: "CELO",
            BlockchainType.MOONBEAM: "GLMR"
        }
        return symbols.get(self, "ETH")


class ContractType(Enum):
    """Types de smart contracts"""
    TOKEN_ERC20 = "erc20"
    TOKEN_ERC721 = "erc721"
    TOKEN_ERC1155 = "erc1155"
    DEX = "dex"
    LENDING = "lending"
    STAKING = "staking"
    VAULT = "vault"
    GOVERNANCE = "governance"
    BRIDGE = "bridge"
    ORACLE = "oracle"
    NFT_MARKETPLACE = "nft_marketplace"
    YIELD_FARM = "yield_farm"
    OPTIONS = "options"
    PERPETUALS = "perpetuals"
    PRICE_ORACLE = "price_oracle"
    
    def get_display_name(self) -> str:
        names = {
            ContractType.TOKEN_ERC20: "ERC20 Token",
            ContractType.TOKEN_ERC721: "ERC721 NFT",
            ContractType.TOKEN_ERC1155: "ERC1155 Multi-Token",
            ContractType.DEX: "Decentralized Exchange",
            ContractType.LENDING: "Lending Protocol",
            ContractType.STAKING: "Staking Contract",
            ContractType.VAULT: "Yield Vault",
            ContractType.GOVERNANCE: "Governance DAO",
            ContractType.BRIDGE: "Cross-Chain Bridge",
            ContractType.ORACLE: "Oracle",
            ContractType.NFT_MARKETPLACE: "NFT Marketplace",
            ContractType.YIELD_FARM: "Yield Farm",
            ContractType.OPTIONS: "Options Protocol",
            ContractType.PERPETUALS: "Perpetuals Exchange",
            ContractType.PRICE_ORACLE: "Price Oracle"
        }
        return names.get(self, "Unknown Contract")


@dataclass
class SmartContractSpec:
    """Spécifications d'un smart contract"""
    name: str
    contract_type: ContractType
    blockchain: BlockchainType
    description: str
    standards: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    interfaces: List[str] = field(default_factory=list)
    events: List[Dict[str, str]] = field(default_factory=list)
    state_variables: List[Dict[str, str]] = field(default_factory=list)
    security_considerations: List[str] = field(default_factory=list)
    gas_optimizations: List[str] = field(default_factory=list)
    upgradeable: bool = False
    proxy_type: Optional[str] = None
    dependencies_list: List[str] = field(default_factory=list)
    test_coverage_target: float = 95.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "contract_type": self.contract_type.value,
            "blockchain": self.blockchain.value,
            "description": self.description,
            "standards": self.standards,
            "dependencies": self.dependencies,
            "interfaces": self.interfaces,
            "events": self.events,
            "state_variables": self.state_variables,
            "security_considerations": self.security_considerations,
            "gas_optimizations": self.gas_optimizations,
            "upgradeable": self.upgradeable,
            "proxy_type": self.proxy_type,
            "dependencies_list": self.dependencies_list,
            "test_coverage_target": self.test_coverage_target
        }


@dataclass
class Tokenomics:
    """Configuration tokenomics"""
    token_name: str
    token_symbol: str
    total_supply: int
    decimals: int = 18
    initial_distribution: Dict[str, float] = field(default_factory=dict)
    vesting_schedule: List[Dict[str, Any]] = field(default_factory=list)
    emission_rate: Optional[float] = None
    max_supply: Optional[int] = None
    burn_percentage: Optional[float] = None
    tax_percentage: Optional[float] = None
    liquidity_allocation: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "token_name": self.token_name,
            "token_symbol": self.token_symbol,
            "total_supply": self.total_supply,
            "decimals": self.decimals,
            "initial_distribution": self.initial_distribution,
            "vesting_schedule": self.vesting_schedule,
            "emission_rate": self.emission_rate,
            "max_supply": self.max_supply,
            "burn_percentage": self.burn_percentage,
            "tax_percentage": self.tax_percentage,
            "liquidity_allocation": self.liquidity_allocation
        }


@dataclass
class DeFiProtocol:
    """Configuration d'un protocole DeFi"""
    name: str
    protocol_type: str
    tvl_target: float
    fee_model: str
    reward_tokens: List[str] = field(default_factory=list)
    risk_parameters: Dict[str, Any] = field(default_factory=dict)
    oracles_required: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "protocol_type": self.protocol_type,
            "tvl_target": self.tvl_target,
            "fee_model": self.fee_model,
            "reward_tokens": self.reward_tokens,
            "risk_parameters": self.risk_parameters,
            "oracles_required": self.oracles_required
        }


@dataclass
class NFTCollection:
    """Configuration d'une collection NFT"""
    name: str
    symbol: str
    max_supply: int
    base_uri: str
    royalty_percentage: float = 5.0
    mint_price: Optional[float] = None
    mint_start: Optional[datetime] = None
    mint_end: Optional[datetime] = None
    traits: List[str] = field(default_factory=list)
    metadata_storage: str = "ipfs"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "symbol": self.symbol,
            "max_supply": self.max_supply,
            "base_uri": self.base_uri,
            "royalty_percentage": self.royalty_percentage,
            "mint_price": self.mint_price,
            "mint_start": self.mint_start.isoformat() if self.mint_start else None,
            "mint_end": self.mint_end.isoformat() if self.mint_end else None,
            "traits": self.traits,
            "metadata_storage": self.metadata_storage
        }


@dataclass
class BlockchainArchitecture:
    """Conception d'architecture blockchain complète"""
    design_id: str
    name: str
    description: str
    version: str = "1.0.0"
    primary_blockchain: BlockchainType = BlockchainType.ETHEREUM
    secondary_chains: List[BlockchainType] = field(default_factory=list)
    contracts: List[SmartContractSpec] = field(default_factory=list)
    tokenomics: Optional[Tokenomics] = None
    defi_protocols: List[DeFiProtocol] = field(default_factory=list)
    nft_collections: List[NFTCollection] = field(default_factory=list)
    cross_chain_bridges: List[str] = field(default_factory=list)
    oracles: List[str] = field(default_factory=list)
    wallet_integration: Dict[str, Any] = field(default_factory=dict)
    gas_optimization_strategy: Dict[str, Any] = field(default_factory=dict)
    security_audit_required: bool = True
    formal_verification_required: bool = False
    estimated_gas_costs: Dict[str, int] = field(default_factory=dict)
    estimated_deployment_cost_usd: float = 0.0
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "design_id": self.design_id,
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "primary_blockchain": self.primary_blockchain.value,
            "secondary_chains": [c.value for c in self.secondary_chains],
            "contracts": [c.to_dict() for c in self.contracts],
            "tokenomics": self.tokenomics.to_dict() if self.tokenomics else None,
            "defi_protocols": [p.to_dict() for p in self.defi_protocols],
            "nft_collections": [n.to_dict() for n in self.nft_collections],
            "cross_chain_bridges": self.cross_chain_bridges,
            "oracles": self.oracles,
            "wallet_integration": self.wallet_integration,
            "gas_optimization_strategy": self.gas_optimization_strategy,
            "security_audit_required": self.security_audit_required,
            "formal_verification_required": self.formal_verification_required,
            "estimated_gas_costs": self.estimated_gas_costs,
            "estimated_deployment_cost_usd": self.estimated_deployment_cost_usd,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }


# ============================================================================
# SOUS-AGENT PRINCIPAL
# ============================================================================

class BlockchainArchitectSubAgent(BaseSubAgent):
    """
    Sous-agent spécialisé en architecture blockchain.
    
    Expert en conception d'architectures blockchain multi-chaînes,
    smart contracts, tokenomics, DeFi, NFT, et cross-chain bridges.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialise le sous-agent Blockchain Architect.
        """
        if config_path is None:
            config_path = str(current_dir / "config.yaml")
        
        # Appel au parent (BaseSubAgent)
        super().__init__(config_path)
        
        # Métadonnées
        self._subagent_display_name = "⛓️ Expert Blockchain Architecture"
        self._subagent_description = "Sous-agent spécialisé en conception d'architecture blockchain multi-chaînes"
        self._subagent_version = "2.0.0"
        self._subagent_category = "blockchain"
        self._subagent_capabilities = [
            "blockchain.design_architecture",
            "blockchain.design_contract",
            "blockchain.design_tokenomics",
            "blockchain.get_chains",
            "blockchain.estimate_gas",
            "blockchain.cross_chain",
            "blockchain.security_audit"
        ]
        
        # État spécifique
        self._supported_chains: List[BlockchainType] = [
            BlockchainType.ETHEREUM, BlockchainType.POLYGON,
            BlockchainType.ARBITRUM, BlockchainType.OPTIMISM,
            BlockchainType.BASE, BlockchainType.SOLANA,
            BlockchainType.AVALANCHE, BlockchainType.BSC,
            BlockchainType.FANTOM, BlockchainType.CELO, BlockchainType.MOONBEAM
        ]
        self._default_chain = BlockchainType.ETHEREUM
        self._designs: Dict[str, BlockchainArchitecture] = {}
        self._templates: Dict[str, Any] = {}
        self._patterns_library: Dict[str, Any] = {}
        
        # Standards et patterns
        self._erc_standards = ["ERC20", "ERC721", "ERC1155", "ERC2981", "ERC4626", "ERC2612", "ERC4361"]
        self._security_patterns = ["ReentrancyGuard", "Pausable", "Ownable", "AccessControl", "Timelock"]
        self._audit_firms = ["Trail of Bits", "OpenZeppelin", "Quantstamp", "CertiK", "Hacken"]
        
        # Métriques spécifiques
        self._blockchain_metrics = {
            "designs_created": 0,
            "contracts_designed": 0,
            "cross_chain_designs": 0,
            "tokenomics_designed": 0,
            "defi_protocols_designed": 0,
            "nft_collections_designed": 0,
            "audit_recommendations": 0
        }
        
        # Configuration
        self._blockchain_config = self._config.get('blockchain', {}) if self._config else {}
        self._default_chain = BlockchainType.from_string(
            self._blockchain_config.get('default_chain', 'ethereum')
        )
        
        # Charger les templates
        self._load_templates()
        self._load_patterns()
        
        # Charger les capacités depuis la configuration
        self._load_capabilities_from_config()
        
        logger.info(f"✅ {self._subagent_display_name} v{self._subagent_version} initialisé")
    
    # ========================================================================
    # IMPLÉMENTATION DES MÉTHODES ABSTRACTES (BaseSubAgent)
    # ========================================================================
    
    async def _initialize_subagent_components(self) -> bool:
        """Initialise les composants spécifiques"""
        logger.info("Initialisation des composants Blockchain Architect...")
        
        # Initialiser les designs
        self._designs = {}
        
        logger.info("✅ Composants Blockchain Architect initialisés")
        return True
    
    async def _initialize_components(self) -> bool:
        """
        Implémentation requise par BaseAgent.
        Délègue à _initialize_subagent_components.
        """
        return await self._initialize_subagent_components()
    
    def _get_capability_handlers(self) -> Dict[str, Any]:
        """Retourne les handlers spécifiques"""
        return {
            "blockchain.design_architecture": self._handle_design_blockchain,
            "blockchain.design_contract": self._handle_design_contract,
            "blockchain.design_tokenomics": self._handle_design_tokenomics,
            "blockchain.get_chains": self._handle_get_chains,
            "blockchain.estimate_gas": self._handle_estimate_gas,
            "blockchain.cross_chain": self._handle_design_cross_chain,
            "blockchain.security_audit": self._handle_security_audit,
        }
    
    def _load_capabilities_from_config(self):
        """Charge les capacités depuis la configuration"""
        caps = self._config.get('capabilities', [])
        for cap in caps:
            if isinstance(cap, dict):
                self.add_capability(AgentCapability(
                    name=cap.get('name', 'unknown'),
                    description=cap.get('description', ''),
                    version=cap.get('version', '1.0.0')
                ))
        if caps:
            self._logger.info(f"✅ {len(caps)} capacités chargées depuis la configuration")
    
    # ========================================================================
    # HANDLERS DE CAPACITÉS
    # ========================================================================
    
    async def _handle_design_blockchain(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handler pour la conception d'architecture blockchain"""
        requirements = params.get("requirements", {})
        return await self.design_blockchain_architecture(requirements)
    
    async def _handle_design_contract(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handler pour la conception de smart contract"""
        requirements = params.get("requirements", {})
        return await self.design_smart_contract(requirements)
    
    async def _handle_design_tokenomics(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handler pour la conception de tokenomics"""
        requirements = params.get("requirements", {})
        return await self.design_tokenomics(requirements)
    
    async def _handle_get_chains(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handler pour obtenir la liste des blockchains"""
        return await self.get_chains()
    
    async def _handle_estimate_gas(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handler pour estimer les coûts de gaz"""
        contract_type = params.get("contract_type", "erc20")
        blockchain = params.get("blockchain", "ethereum")
        return await self.estimate_gas_costs(contract_type, blockchain)
    
    async def _handle_design_cross_chain(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handler pour la conception de bridge cross-chain"""
        source = params.get("source_chain", "ethereum")
        targets = params.get("target_chains", [])
        return await self.design_cross_chain_bridge(source, targets)
    
    async def _handle_security_audit(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handler pour les exigences d'audit"""
        contract_type = params.get("contract_type", "erc20")
        blockchain = params.get("blockchain", "ethereum")
        return await self.get_security_audit_requirements(contract_type, blockchain)
    
    # ========================================================================
    # MÉTHODES DE CHARGEMENT
    # ========================================================================
    
    def _load_templates(self):
        """Charge les templates de contracts"""
        templates_dir = current_dir / "templates"
        
        if templates_dir.exists():
            self._logger.info(f"Chargement des templates depuis {templates_dir}")
            for template_file in templates_dir.glob("*.yaml"):
                try:
                    import yaml
                    with open(template_file, 'r', encoding='utf-8') as f:
                        template = yaml.safe_load(f)
                        template_name = template_file.stem
                        self._templates[template_name] = template
                except Exception as e:
                    self._logger.error(f"Erreur chargement template {template_file}: {e}")
        else:
            self._logger.warning("Répertoire des templates non trouvé")
            self._templates = self._get_default_templates()
    
    def _load_patterns(self):
        """Charge les patterns d'architecture blockchain"""
        patterns_file = current_dir / "patterns.yaml"
        
        if patterns_file.exists():
            try:
                import yaml
                with open(patterns_file, 'r', encoding='utf-8') as f:
                    self._patterns_library = yaml.safe_load(f)
                self._logger.info(f"Patterns chargés depuis {patterns_file}")
            except Exception as e:
                self._logger.error(f"Erreur chargement patterns: {e}")
                self._patterns_library = self._get_default_patterns()
        else:
            self._logger.warning("Fichier des patterns non trouvé")
            self._patterns_library = self._get_default_patterns()
    
    def _get_default_templates(self) -> Dict[str, Any]:
        """Retourne les templates par défaut"""
        return {
            "erc20": {
                "name": "ERC20 Token",
                "description": "Standard fungible token",
                "standards": ["ERC20"],
                "features": ["transfer", "approve", "transferFrom", "balanceOf", "allowance"],
            },
            "erc721": {
                "name": "ERC721 NFT",
                "description": "Non-fungible token",
                "standards": ["ERC721", "ERC2981"],
                "features": ["mint", "transferFrom", "tokenURI", "ownerOf"],
            },
            "staking": {
                "name": "Staking Contract",
                "description": "Token staking with rewards",
                "features": ["stake", "unstake", "claimRewards", "getRewards"],
            }
        }
    
    def _get_default_patterns(self) -> Dict[str, Any]:
        """Retourne les patterns par défaut"""
        return {
            "security_patterns": [
                {"name": "ReentrancyGuard", "description": "Protection contre les attaques de réentrance"},
                {"name": "Pausable", "description": "Mécanisme d'arrêt d'urgence"},
                {"name": "Ownable", "description": "Contrôle d'accès basé sur le propriétaire"},
            ]
        }
    
    # ========================================================================
    # MÉTHODES PUBLIQUES PRINCIPALES
    # ========================================================================
    
    async def design_blockchain_architecture(self, requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Conçoit une architecture blockchain complète."""
        try:
            chain_str = requirements.get("blockchain", "ethereum")
            primary_chain = BlockchainType.from_string(chain_str)
            
            design_id = f"blockchain_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            design = BlockchainArchitecture(
                design_id=design_id,
                name=requirements.get("name", "Blockchain Architecture"),
                description=requirements.get("description", ""),
                primary_blockchain=primary_chain
            )
            
            self._designs[design_id] = design
            self._blockchain_metrics["designs_created"] += 1
            
            return {
                "success": True,
                "design": design.to_dict(),
                "design_id": design_id
            }
            
        except Exception as e:
            logger.error(f"Erreur conception blockchain: {e}")
            return {"success": False, "error": str(e)}
    
    async def design_smart_contract(self, requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Conçoit un smart contract spécifique."""
        try:
            contract_type_str = requirements.get("contract_type", "erc20")
            contract_type = None
            for ct in ContractType:
                if ct.value == contract_type_str.lower():
                    contract_type = ct
                    break
            if contract_type is None:
                contract_type = ContractType.TOKEN_ERC20
            
            blockchain = BlockchainType.from_string(requirements.get("blockchain", "ethereum"))
            
            contract = SmartContractSpec(
                name=requirements.get("name", "Contract"),
                contract_type=contract_type,
                blockchain=blockchain,
                description=requirements.get("description", "")
            )
            
            self._blockchain_metrics["contracts_designed"] += 1
            
            return {
                "success": True,
                "contract": contract.to_dict()
            }
            
        except Exception as e:
            logger.error(f"Erreur conception contract: {e}")
            return {"success": False, "error": str(e)}
    
    async def design_tokenomics(self, requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Conçoit la tokenomics d'un projet."""
        try:
            tokenomics = Tokenomics(
                token_name=requirements.get("token_name", "Token"),
                token_symbol=requirements.get("token_symbol", "TKN"),
                total_supply=requirements.get("total_supply", 1_000_000_000),
                decimals=requirements.get("decimals", 18),
                initial_distribution=requirements.get("initial_distribution", {})
            )
            
            self._blockchain_metrics["tokenomics_designed"] += 1
            
            return {
                "success": True,
                "tokenomics": tokenomics.to_dict()
            }
            
        except Exception as e:
            logger.error(f"Erreur conception tokenomics: {e}")
            return {"success": False, "error": str(e)}
    
    async def design_defi_protocol(self, requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Conçoit un protocole DeFi."""
        try:
            protocol = DeFiProtocol(
                name=requirements.get("name", "DeFi Protocol"),
                protocol_type=requirements.get("protocol_type", "lending"),
                tvl_target=requirements.get("tvl_target", 10_000_000),
                fee_model=requirements.get("fee_model", "0.3%")
            )
            
            self._blockchain_metrics["defi_protocols_designed"] += 1
            
            return {
                "success": True,
                "protocol": protocol.to_dict()
            }
            
        except Exception as e:
            logger.error(f"Erreur conception DeFi: {e}")
            return {"success": False, "error": str(e)}
    
    async def design_nft_collection(self, requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Conçoit une collection NFT."""
        try:
            collection = NFTCollection(
                name=requirements.get("name", "NFT Collection"),
                symbol=requirements.get("symbol", "NFT"),
                max_supply=requirements.get("max_supply", 10000),
                base_uri=requirements.get("base_uri", "ipfs://"),
                royalty_percentage=requirements.get("royalty_percentage", 5.0)
            )
            
            self._blockchain_metrics["nft_collections_designed"] += 1
            
            return {
                "success": True,
                "collection": collection.to_dict()
            }
            
        except Exception as e:
            logger.error(f"Erreur conception NFT: {e}")
            return {"success": False, "error": str(e)}
    
    async def design_cross_chain_bridge(self, source_chain: str, target_chains: List[str]) -> Dict[str, Any]:
        """Conçoit un bridge cross-chain."""
        try:
            source = BlockchainType.from_string(source_chain)
            targets = [BlockchainType.from_string(t) for t in target_chains]
            
            self._blockchain_metrics["cross_chain_designs"] += 1
            
            return {
                "success": True,
                "bridge_design": {
                    "source_chain": source.value,
                    "target_chains": [t.value for t in targets],
                    "bridge_type": "wormhole" if all(c.is_evm_compatible() for c in targets + [source]) else "custom"
                }
            }
            
        except Exception as e:
            logger.error(f"Erreur conception bridge: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_chains(self) -> Dict[str, Any]:
        """Retourne la liste des blockchains supportées."""
        return {
            "success": True,
            "chains": [
                {
                    "id": c.value,
                    "name": c.get_display_name(),
                    "chain_id": c.get_chain_id(),
                    "evm_compatible": c.is_evm_compatible(),
                    "currency": c.get_currency_symbol()
                }
                for c in self._supported_chains
            ],
            "total": len(self._supported_chains)
        }
    
    async def estimate_gas_costs(self, contract_type: str, blockchain: str) -> Dict[str, Any]:
        """Estime les coûts de gaz."""
        try:
            chain = BlockchainType.from_string(blockchain)
            
            gas_estimates = {
                "erc20": {"deployment": 1_500_000},
                "erc721": {"deployment": 2_000_000},
                "dex": {"deployment": 3_500_000},
                "lending": {"deployment": 4_000_000}
            }
            
            estimates = gas_estimates.get(contract_type, gas_estimates["erc20"])
            
            return {
                "success": True,
                "gas_units": estimates,
                "blockchain": chain.value,
                "currency": chain.get_currency_symbol()
            }
            
        except Exception as e:
            logger.error(f"Erreur estimation gaz: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_security_audit_requirements(self, contract_type: str, blockchain: str) -> Dict[str, Any]:
        """Retourne les exigences d'audit."""
        self._blockchain_metrics["audit_recommendations"] += 1
        
        return {
            "success": True,
            "requirements": {
                "mandatory_audits": ["OpenZeppelin", "CertiK"],
                "recommended_audits": ["Trail of Bits"],
                "estimated_audit_cost": "$15,000 - $25,000",
                "estimated_audit_duration_days": 14
            }
        }
    
    # ========================================================================
    # MÉTHODES DE RÉCUPÉRATION
    # ========================================================================
    
    def get_design(self, design_id: str) -> Optional[Dict[str, Any]]:
        """Récupère une conception d'architecture blockchain"""
        design = self._designs.get(design_id)
        return design.to_dict() if design else None
    
    def list_designs(self) -> List[Dict[str, Any]]:
        """Liste toutes les conceptions disponibles"""
        return [
            {
                "design_id": design.design_id,
                "name": design.name,
                "primary_blockchain": design.primary_blockchain.value,
                "created_at": design.created_at.isoformat()
            }
            for design in self._designs.values()
        ]
    
    def get_metrics(self) -> Dict[str, Any]:
        """Retourne les métriques du sous-agent"""
        return {
            **self._blockchain_metrics,
            "designs_count": len(self._designs),
            "supported_chains": [c.value for c in self._supported_chains]
        }
    
    # ========================================================================
    # NETTOYAGE
    # ========================================================================
    
    async def _cleanup(self):
        """Nettoie les ressources du sous-agent"""
        logger.info("Nettoyage des ressources Blockchain Architect...")
        self._designs.clear()
        await super()._cleanup()


# ============================================================================
# FONCTION D'USINE
# ============================================================================

def create_blockchain_architect_subagent(config_path: Optional[str] = None) -> BlockchainArchitectSubAgent:
    """Crée une instance du sous-agent Blockchain Architect"""
    return BlockchainArchitectSubAgent(config_path)
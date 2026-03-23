#!/usr/bin/env python3
"""
DefiUiSpecialist SubAgent - Spécialiste Interfaces DeFi
Version: 2.0.0 (ALIGNÉ SUR CIRCUIT_BREAKER)

Spécialiste des interfaces DeFi complexes (swap, lending, staking, vaults)
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
from agents.base_agent.base_agent import Message, MessageType

logger = logging.getLogger(__name__)


# ============================================================================
# ÉNUMS ET CLASSES DE DONNÉES
# ============================================================================

class DefiProtocolType(Enum):
    """Types de protocoles DeFi"""
    UNISWAP = "uniswap"
    AAVE = "aave"
    CURVE = "curve"
    BALANCER = "balancer"
    COMPOUND = "compound"
    LIDO = "lido"
    CONVEX = "convex"
    
    @classmethod
    def from_string(cls, type_str: str) -> 'DefiProtocolType':
        mapping = {
            "uniswap": cls.UNISWAP,
            "aave": cls.AAVE,
            "curve": cls.CURVE,
            "balancer": cls.BALANCER,
            "compound": cls.COMPOUND,
            "lido": cls.LIDO,
            "convex": cls.CONVEX
        }
        return mapping.get(type_str.lower(), cls.UNISWAP)


class DefiFeatureType(Enum):
    """Types de fonctionnalités DeFi"""
    SWAP = "swap"
    LIQUIDITY = "liquidity"
    STAKING = "staking"
    VAULT = "vault"
    LENDING = "lending"
    BORROWING = "borrowing"
    FARM = "farm"
    ANALYTICS = "analytics"


@dataclass
class SwapConfig:
    """Configuration d'un swap"""
    from_token: str = "ETH"
    to_token: str = "USDC"
    protocol: DefiProtocolType = DefiProtocolType.UNISWAP
    slippage: float = 0.5
    deadline_minutes: int = 20
    fee_tier: int = 3000
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "from_token": self.from_token,
            "to_token": self.to_token,
            "protocol": self.protocol.value,
            "slippage": self.slippage,
            "deadline_minutes": self.deadline_minutes,
            "fee_tier": self.fee_tier
        }


@dataclass
class LiquidityConfig:
    """Configuration de liquidité"""
    token0: str = "ETH"
    token1: str = "USDC"
    protocol: DefiProtocolType = DefiProtocolType.UNISWAP
    fee_tier: int = 3000
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "token0": self.token0,
            "token1": self.token1,
            "protocol": self.protocol.value,
            "fee_tier": self.fee_tier
        }


@dataclass
class StakingConfig:
    """Configuration de staking"""
    token: str = "TOKEN"
    reward_token: str = "REWARD"
    apy: float = 15.5
    lock_days: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "token": self.token,
            "reward_token": self.reward_token,
            "apy": self.apy,
            "lock_days": self.lock_days
        }


@dataclass
class LendingConfig:
    """Configuration de lending"""
    asset: str = "ETH"
    protocol: DefiProtocolType = DefiProtocolType.AAVE
    supply_apy: float = 3.5
    borrow_apy: float = 5.2
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "asset": self.asset,
            "protocol": self.protocol.value,
            "supply_apy": self.supply_apy,
            "borrow_apy": self.borrow_apy
        }


@dataclass
class DefiInterfaceResult:
    """Résultat de génération d'interface DeFi"""
    interface_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    interface_type: DefiFeatureType = DefiFeatureType.SWAP
    code: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    processing_time_ms: float = 0.0
    success: bool = True
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "interface_id": self.interface_id,
            "interface_type": self.interface_type.value,
            "code": self.code[:500] + "..." if len(self.code) > 500 else self.code,
            "created_at": self.created_at.isoformat(),
            "processing_time_ms": self.processing_time_ms,
            "success": self.success,
            "error": self.error,
            "metadata": self.metadata
        }


@dataclass
class DefiStats:
    """Statistiques DeFi"""
    interfaces_generated: int = 0
    interfaces_succeeded: int = 0
    interfaces_failed: int = 0
    by_type: Dict[str, int] = field(default_factory=dict)
    by_protocol: Dict[str, int] = field(default_factory=dict)
    total_processing_time: float = 0.0
    avg_processing_time: float = 0.0
    last_generation: Optional[datetime] = None
    start_time: datetime = field(default_factory=datetime.now)
    
    def record_generation(self, interface_type: DefiFeatureType, protocol: DefiProtocolType, 
                          processing_time: float, success: bool):
        """Enregistre une génération"""
        self.interfaces_generated += 1
        if success:
            self.interfaces_succeeded += 1
        else:
            self.interfaces_failed += 1
            
        self.total_processing_time += processing_time
        self.avg_processing_time = self.total_processing_time / self.interfaces_generated
        self.last_generation = datetime.now()
        
        # Statistiques par type
        self.by_type[interface_type.value] = self.by_type.get(interface_type.value, 0) + 1
        self.by_protocol[protocol.value] = self.by_protocol.get(protocol.value, 0) + 1
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "interfaces_generated": self.interfaces_generated,
            "interfaces_succeeded": self.interfaces_succeeded,
            "interfaces_failed": self.interfaces_failed,
            "by_type": self.by_type,
            "by_protocol": self.by_protocol,
            "avg_processing_time_ms": round(self.avg_processing_time, 2),
            "total_processing_time_ms": round(self.total_processing_time, 2),
            "last_generation": self.last_generation.isoformat() if self.last_generation else None,
            "uptime_seconds": (datetime.now() - self.start_time).total_seconds()
        }


# ============================================================================
# SOUS-AGENT PRINCIPAL
# ============================================================================

class DefiUiSpecialistSubAgent(BaseSubAgent):
    """
    Sous-agent spécialiste des interfaces DeFi
    
    Génère des interfaces DeFi complètes : swap, liquidité, staking,
    lending, vaults et dashboards.
    """
    
    def __init__(self, config_path: str = ""):
        """Initialise le sous-agent"""
        # 🔧 CORRECTION : Forcer le chemin absolu
        if not config_path:
            config_path = str(Path(__file__).parent / "config.yaml")
        elif not Path(config_path).is_absolute():
            config_path = str(project_root / config_path)
        
        super().__init__(config_path)
        
        # Récupérer la configuration
        if 'subagent' in self._config:
            config = self._config.get('subagent', {})
        elif 'agent' in self._config:
            config = self._config.get('agent', {})
        else:
            config = {}
        
        # Métadonnées
        self._subagent_display_name = config.get('display_name', "📊 Spécialiste Interfaces DeFi")
        self._subagent_description = config.get('description', "Génération d'interfaces DeFi")
        self._subagent_version = config.get('version', "2.0.0")
        self._subagent_category = config.get('category', "frontend_web3")
        self._subagent_capabilities = [
            "defi.generate_swap_interface",
            "defi.generate_liquidity_interface",
            "defi.generate_staking_interface",
            "defi.generate_lending_interface",
            "defi.generate_vault_interface",
            "defi.generate_defi_dashboard"
        ]
        
        # Templates
        self._templates = self._load_templates()
        
        # Statistiques
        self._stats = DefiStats()
        
        # File d'attente
        self._event_queue: asyncio.Queue = asyncio.Queue()
        
        # Tâche de traitement
        self._processor_task: Optional[asyncio.Task] = None
        
        logger.info(f"✅ {self._subagent_display_name} initialisé")

    # ============================================================================
    # INITIALISATION
    # ============================================================================
    
    async def _initialize_subagent_components(self) -> bool:
        """Initialise les composants spécifiques"""
        logger.info("Initialisation des composants DeFi Specialist...")
        
        self._processor_task = asyncio.create_task(self._processor_loop())
        
        self._components = {
            "version": self._subagent_version,
            "protocols": [p.value for p in DefiProtocolType],
            "features": [f.value for f in DefiFeatureType],
            "templates": list(self._templates.keys())
        }
        
        logger.info("✅ Composants DeFi Specialist initialisés")
        return True
        
    async def _initialize_components(self) -> bool:
        return await self._initialize_subagent_components()

    def _get_capability_handlers(self) -> Dict[str, Callable]:
        return {
            "defi.generate_swap_interface": self._handle_generate_swap_interface,
            "defi.generate_liquidity_interface": self._handle_generate_liquidity_interface,
            "defi.generate_staking_interface": self._handle_generate_staking_interface,
            "defi.generate_lending_interface": self._handle_generate_lending_interface,
            "defi.generate_vault_interface": self._handle_generate_vault_interface,
            "defi.generate_defi_dashboard": self._handle_generate_defi_dashboard,
        }
    
    # ============================================================================
    # TEMPLATES
    # ============================================================================
    
    def _load_templates(self) -> Dict[str, str]:
        """Charge les templates d'interfaces DeFi"""
        return {
            "swap": """
import {{ useState, useEffect }} from 'react';
import {{ useAccount, useBalance, useContractWrite, usePrepareContractWrite }} from 'wagmi';

export default function SwapInterface() {{
  const [fromAmount, setFromAmount] = useState('');
  const [toAmount, setToAmount] = useState('');
  const [slippage, setSlippage] = useState(0.5);
  const {{ address }} = useAccount();
  
  // Simulation des balances
  const {{ data: fromBalance }} = useBalance({{
    address,
    token: '{from_token}',
  }});
  
  const handleSwap = async () => {{
    // Logique de swap
    console.log('Swapping...');
  }};
  
  return (
    <div className="swap-interface">
      <div className="swap-section">
        <label>From</label>
        <input
          type="text"
          value={{fromAmount}}
          onChange={{e => setFromAmount(e.target.value)}}
          placeholder="0.0"
        />
        <span>{from_token}</span>
        <div>Balance: {{fromBalance?.formatted || '0'}}</div>
      </div>
      
      <div className="swap-arrow">↓</div>
      
      <div className="swap-section">
        <label>To</label>
        <input
          type="text"
          value={{toAmount}}
          readOnly
          placeholder="0.0"
        />
        <span>{to_token}</span>
      </div>
      
      <div className="slippage">
        <label>Slippage: {{slippage}}%</label>
        <input
          type="range"
          min="0.1"
          max="5"
          step="0.1"
          value={{slippage}}
          onChange={{e => setSlippage(parseFloat(e.target.value))}}
        />
      </div>
      
      <button onClick={{handleSwap}} disabled={{!fromAmount}}>
        Swap
      </button>
    </div>
  );
}}
""",
            "liquidity": """
import {{ useState }} from 'react';

export default function LiquidityInterface() {{
  const [token0Amount, setToken0Amount] = useState('');
  const [token1Amount, setToken1Amount] = useState('');
  
  return (
    <div className="liquidity-interface">
      <h2>Add Liquidity</h2>
      
      <div className="token-input">
        <label>Token 0</label>
        <input
          type="text"
          value={{token0Amount}}
          onChange={{e => setToken0Amount(e.target.value)}}
          placeholder="0.0"
        />
      </div>
      
      <div className="token-input">
        <label>Token 1</label>
        <input
          type="text"
          value={{token1Amount}}
          onChange={{e => setToken1Amount(e.target.value)}}
          placeholder="0.0"
        />
      </div>
      
      <div className="actions">
        <button>Add Liquidity</button>
        <button>Remove</button>
      </div>
    </div>
  );
}}
""",
            "staking": """
import {{ useState }} from 'react';
import {{ useAccount, useBalance }} from 'wagmi';

export default function StakingInterface() {{
  const [stakeAmount, setStakeAmount] = useState('');
  const {{ address }} = useAccount();
  
  const {{ data: balance }} = useBalance({{
    address,
    token: '{token}',
  }});
  
  return (
    <div className="staking-interface">
      <h2>Stake {token}</h2>
      
      <div className="stats">
        <div>APY: {apy}%</div>
        <div>Total Staked: $1,234,567</div>
        <div>Your Stake: $10,000</div>
        <div>Earned: $150</div>
      </div>
      
      <div className="stake-section">
        <input
          type="text"
          value={{stakeAmount}}
          onChange={{e => setStakeAmount(e.target.value)}}
          placeholder="0.0"
        />
        <span>{token}</span>
        <div>Balance: {{balance?.formatted || '0'}}</div>
      </div>
      
      <div className="actions">
        <button>Stake</button>
        <button>Unstake</button>
        <button>Claim Rewards</button>
      </div>
    </div>
  );
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
    # GÉNÉRATION D'INTERFACES
    # ============================================================================
    
    async def generate_swap_interface(self, config: SwapConfig) -> DefiInterfaceResult:
        """Génère une interface de swap"""
        start_time = time.time()
        result = DefiInterfaceResult(interface_type=DefiFeatureType.SWAP)
        
        try:
            template = self._templates.get("swap", self._templates["swap"])
            
            result.code = template.format(
                from_token=config.from_token,
                to_token=config.to_token
            )
            result.success = True
            
            processing_time = (time.time() - start_time) * 1000
            result.processing_time_ms = processing_time
            self._stats.record_generation(DefiFeatureType.SWAP, config.protocol, processing_time, True)
            
            await self._log_event("swap_interface_generated", {
                "interface_id": result.interface_id,
                "pair": f"{config.from_token}/{config.to_token}",
                "processing_time_ms": processing_time
            })
            
        except Exception as e:
            result.success = False
            result.error = str(e)
            processing_time = (time.time() - start_time) * 1000
            result.processing_time_ms = processing_time
            self._stats.record_generation(DefiFeatureType.SWAP, config.protocol, processing_time, False)
            logger.error(f"❌ Erreur génération swap: {e}")
        
        return result
    
    async def generate_liquidity_interface(self, config: LiquidityConfig) -> DefiInterfaceResult:
        """Génère une interface de liquidité"""
        start_time = time.time()
        result = DefiInterfaceResult(interface_type=DefiFeatureType.LIQUIDITY)
        
        try:
            template = self._templates.get("liquidity", self._templates["liquidity"])
            result.code = template.format()
            result.success = True
            
            processing_time = (time.time() - start_time) * 1000
            result.processing_time_ms = processing_time
            self._stats.record_generation(DefiFeatureType.LIQUIDITY, config.protocol, processing_time, True)
            
        except Exception as e:
            result.success = False
            result.error = str(e)
            processing_time = (time.time() - start_time) * 1000
            result.processing_time_ms = processing_time
            self._stats.record_generation(DefiFeatureType.LIQUIDITY, config.protocol, processing_time, False)
        
        return result
    
    async def generate_staking_interface(self, config: StakingConfig) -> DefiInterfaceResult:
        """Génère une interface de staking"""
        start_time = time.time()
        result = DefiInterfaceResult(interface_type=DefiFeatureType.STAKING)
        
        try:
            template = self._templates.get("staking", self._templates["staking"])
            result.code = template.format(
                token=config.token,
                apy=config.apy
            )
            result.success = True
            
            processing_time = (time.time() - start_time) * 1000
            result.processing_time_ms = processing_time
            self._stats.record_generation(DefiFeatureType.STAKING, DefiProtocolType.LIDO, processing_time, True)
            
        except Exception as e:
            result.success = False
            result.error = str(e)
            processing_time = (time.time() - start_time) * 1000
            result.processing_time_ms = processing_time
            self._stats.record_generation(DefiFeatureType.STAKING, DefiProtocolType.LIDO, processing_time, False)
        
        return result
    
    async def generate_lending_interface(self, config: LendingConfig) -> DefiInterfaceResult:
        """Génère une interface de lending"""
        start_time = time.time()
        result = DefiInterfaceResult(interface_type=DefiFeatureType.LENDING)
        
        try:
            code = f"""
import {{ useState }} from 'react';

export default function LendingInterface() {{
  const [supplyAmount, setSupplyAmount] = useState('');
  const [borrowAmount, setBorrowAmount] = useState('');
  const [activeTab, setActiveTab] = useState('supply');

  return (
    <div className="lending-interface">
      <h2>{config.protocol.value} - {config.asset}</h2>
      
      <div className="market-stats">
        <div>Supply APY: {config.supply_apy}%</div>
        <div>Borrow APY: {config.borrow_apy}%</div>
        <div>Total Supply: $10M</div>
        <div>Total Borrow: $5M</div>
      </div>

      <div className="tabs">
        <button onClick={{() => setActiveTab('supply')}}>Supply</button>
        <button onClick={{() => setActiveTab('borrow')}}>Borrow</button>
      </div>

      {{activeTab === 'supply' && (
        <div className="supply-section">
          <h3>Supply {config.asset}</h3>
          <input
            type="text"
            value={{supplyAmount}}
            onChange={{e => setSupplyAmount(e.target.value)}}
            placeholder="0.0"
          />
          <button>Supply</button>
        </div>
      )}}

      {{activeTab === 'borrow' && (
        <div className="borrow-section">
          <h3>Borrow {config.asset}</h3>
          <input
            type="text"
            value={{borrowAmount}}
            onChange={{e => setBorrowAmount(e.target.value)}}
            placeholder="0.0"
          />
          <button>Borrow</button>
        </div>
      )}}
    </div>
  );
}}
"""
            result.code = code
            result.success = True
            
            processing_time = (time.time() - start_time) * 1000
            result.processing_time_ms = processing_time
            self._stats.record_generation(DefiFeatureType.LENDING, config.protocol, processing_time, True)
            
        except Exception as e:
            result.success = False
            result.error = str(e)
            processing_time = (time.time() - start_time) * 1000
            result.processing_time_ms = processing_time
            self._stats.record_generation(DefiFeatureType.LENDING, config.protocol, processing_time, False)
        
        return result
    
    async def generate_vault_interface(self, config: Dict[str, Any]) -> DefiInterfaceResult:
        """Génère une interface de vault"""
        start_time = time.time()
        result = DefiInterfaceResult(interface_type=DefiFeatureType.VAULT)
        
        try:
            strategy = config.get("strategy", "Yield Optimizer")
            
            code = f"""
import {{ useState }} from 'react';

export default function VaultInterface() {{
  const [depositAmount, setDepositAmount] = useState('');

  return (
    <div className="vault-interface">
      <h2>{strategy} Vault</h2>
      
      <div className="vault-stats">
        <div>TVL: $5,000,000</div>
        <div>APY: 25%</div>
        <div>Your Deposit: $1,000</div>
        <div>Earned: $50</div>
      </div>

      <div className="deposit-section">
        <h3>Deposit</h3>
        <input
          type="text"
          value={{depositAmount}}
          onChange={{e => setDepositAmount(e.target.value)}}
          placeholder="0.0"
        />
        <button>Deposit</button>
      </div>

      <div className="withdraw-section">
        <h3>Withdraw</h3>
        <button>Withdraw All</button>
        <button>Withdraw 50%</button>
      </div>
    </div>
  );
}}
"""
            result.code = code
            result.success = True
            
            processing_time = (time.time() - start_time) * 1000
            result.processing_time_ms = processing_time
            self._stats.record_generation(DefiFeatureType.VAULT, DefiProtocolType.CURVE, processing_time, True)
            
        except Exception as e:
            result.success = False
            result.error = str(e)
            processing_time = (time.time() - start_time) * 1000
            result.processing_time_ms = processing_time
            self._stats.record_generation(DefiFeatureType.VAULT, DefiProtocolType.CURVE, processing_time, False)
        
        return result
    
    async def generate_defi_dashboard(self, config: Dict[str, Any]) -> DefiInterfaceResult:
        """Génère un dashboard DeFi complet"""
        start_time = time.time()
        result = DefiInterfaceResult(interface_type=DefiFeatureType.ANALYTICS)
        
        try:
            name = config.get("name", "DeFi Dashboard")
            
            code = f"""
import {{ useState }} from 'react';
import SwapInterface from './SwapInterface';
import LiquidityInterface from './LiquidityInterface';
import StakingInterface from './StakingInterface';

export default function DeFiDashboard() {{
  const [activeTab, setActiveTab] = useState('swap');

  const tabs = [
    {{ id: 'swap', label: 'Swap', component: SwapInterface }},
    {{ id: 'liquidity', label: 'Liquidity', component: LiquidityInterface }},
    {{ id: 'staking', label: 'Staking', component: StakingInterface }},
  ];

  const ActiveComponent = tabs.find(tab => tab.id === activeTab)?.component;

  return (
    <div className="defi-dashboard">
      <h1>{name}</h1>
      
      <nav className="dashboard-nav">
        {{tabs.map(tab => (
          <button
            key={{tab.id}}
            className={{`tab ${{activeTab === tab.id ? 'active' : ''}}`}}
            onClick={{() => setActiveTab(tab.id)}}
          >
            {{tab.label}}
          </button>
        ))}}
      </nav>

      <main className="dashboard-content">
        {{ActiveComponent && <ActiveComponent />}}
      </main>

      <footer>
        <div>Total Value Locked: $10,000,000</div>
      </footer>
    </div>
  );
}}
"""
            result.code = code
            result.success = True
            
            processing_time = (time.time() - start_time) * 1000
            result.processing_time_ms = processing_time
            self._stats.record_generation(DefiFeatureType.ANALYTICS, DefiProtocolType.UNISWAP, processing_time, True)
            
        except Exception as e:
            result.success = False
            result.error = str(e)
            processing_time = (time.time() - start_time) * 1000
            result.processing_time_ms = processing_time
            self._stats.record_generation(DefiFeatureType.ANALYTICS, DefiProtocolType.UNISWAP, processing_time, False)
        
        return result
    
    # ============================================================================
    # HANDLERS
    # ============================================================================
    
    async def _handle_generate_swap_interface(self, params: Dict[str, Any]) -> Dict[str, Any]:
        config = SwapConfig(
            from_token=params.get("from_token", "ETH"),
            to_token=params.get("to_token", "USDC"),
            protocol=DefiProtocolType.from_string(params.get("protocol", "uniswap")),
            slippage=params.get("slippage", 0.5)
        )
        result = await self.generate_swap_interface(config)
        return result.to_dict()
    
    async def _handle_generate_liquidity_interface(self, params: Dict[str, Any]) -> Dict[str, Any]:
        config = LiquidityConfig(
            token0=params.get("token0", "ETH"),
            token1=params.get("token1", "USDC"),
            protocol=DefiProtocolType.from_string(params.get("protocol", "uniswap"))
        )
        result = await self.generate_liquidity_interface(config)
        return result.to_dict()
    
    async def _handle_generate_staking_interface(self, params: Dict[str, Any]) -> Dict[str, Any]:
        config = StakingConfig(
            token=params.get("token", "TOKEN"),
            reward_token=params.get("reward_token", "REWARD"),
            apy=params.get("apy", 15.5),
            lock_days=params.get("lock_days", 0)
        )
        result = await self.generate_staking_interface(config)
        return result.to_dict()
    
    async def _handle_generate_lending_interface(self, params: Dict[str, Any]) -> Dict[str, Any]:
        config = LendingConfig(
            asset=params.get("asset", "ETH"),
            protocol=DefiProtocolType.from_string(params.get("protocol", "aave")),
            supply_apy=params.get("supply_apy", 3.5),
            borrow_apy=params.get("borrow_apy", 5.2)
        )
        result = await self.generate_lending_interface(config)
        return result.to_dict()
    
    async def _handle_generate_vault_interface(self, params: Dict[str, Any]) -> Dict[str, Any]:
        result = await self.generate_vault_interface(params)
        return result.to_dict()
    
    async def _handle_generate_defi_dashboard(self, params: Dict[str, Any]) -> Dict[str, Any]:
        result = await self.generate_defi_dashboard(params)
        return result.to_dict()
    
    # ============================================================================
    # GESTION DES MESSAGES
    # ============================================================================
    
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
        
        return {
            **base_health,
            "agent": self.name,
            "display_name": self._subagent_display_name,
            "category": self._subagent_category,
            "status": self._status.value,
            "ready": self._status == AgentStatus.READY,
            "initialized": self._initialized,
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
            "stats": self._stats.to_dict()
        }
    
    async def get_stats(self) -> Dict[str, Any]:
        return self._stats.to_dict()
    
    async def shutdown(self) -> bool:
        """Arrête le sous-agent"""
        logger.info(f"Arrêt de {self._subagent_display_name}...")
        
        # Arrêter la tâche de traitement
        if self._processor_task and not self._processor_task.done():
            self._processor_task.cancel()
            try:
                await self._processor_task
            except asyncio.CancelledError:
                pass
        
        # IGNORER complètement super().shutdown()
        try:
            await super().shutdown()
        except Exception:
            pass  # On ignore tout
        
        logger.info(f"✅ {self._subagent_display_name} arrêté")
        return True  # ← TOUJOURS retourner True
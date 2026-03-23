#!/usr/bin/env python3
"""
NftUiSpecialist SubAgent - Spécialiste Interfaces NFT
Version: 2.0.0 (ALIGNÉ SUR CIRCUIT_BREAKER)

Spécialiste des interfaces NFT (gallery, mint, auction, marketplace)
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

class NftStandard(Enum):
    """Standards NFT"""
    ERC721 = "erc721"
    ERC1155 = "erc1155"
    ERC721A = "erc721a"
    
    @classmethod
    def from_string(cls, type_str: str) -> 'NftStandard':
        mapping = {
            "erc721": cls.ERC721,
            "erc1155": cls.ERC1155,
            "erc721a": cls.ERC721A
        }
        return mapping.get(type_str.lower(), cls.ERC721)


class NftFeatureType(Enum):
    """Types de fonctionnalités NFT"""
    GALLERY = "gallery"
    MINT = "mint"
    AUCTION = "auction"
    MARKETPLACE = "marketplace"
    DETAIL = "detail"
    COLLECTION = "collection"


@dataclass
class NftConfig:
    """Configuration NFT de base"""
    name: str = "NFT Collection"
    symbol: str = "NFT"
    standard: NftStandard = NftStandard.ERC721
    max_supply: int = 10000
    price: float = 0.1
    metadata_uri: str = "ipfs://..."
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "symbol": self.symbol,
            "standard": self.standard.value,
            "max_supply": self.max_supply,
            "price": self.price,
            "metadata_uri": self.metadata_uri
        }


@dataclass
class MintConfig(NftConfig):
    """Configuration de mint"""
    max_per_wallet: int = 5
    presale_enabled: bool = False
    whitelist_enabled: bool = False
    start_time: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            **super().to_dict(),
            "max_per_wallet": self.max_per_wallet,
            "presale_enabled": self.presale_enabled,
            "whitelist_enabled": self.whitelist_enabled,
            "start_time": self.start_time.isoformat() if self.start_time else None
        }


@dataclass
class AuctionConfig:
    """Configuration d'enchère"""
    nft_id: str = ""
    starting_bid: float = 1.0
    min_increment: float = 0.1
    duration_hours: int = 24
    reserve_price: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "nft_id": self.nft_id,
            "starting_bid": self.starting_bid,
            "min_increment": self.min_increment,
            "duration_hours": self.duration_hours,
            "reserve_price": self.reserve_price
        }


@dataclass
class NftInterfaceResult:
    """Résultat de génération d'interface NFT"""
    interface_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    interface_type: NftFeatureType = NftFeatureType.GALLERY
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
class NftStats:
    """Statistiques NFT"""
    interfaces_generated: int = 0
    interfaces_succeeded: int = 0
    interfaces_failed: int = 0
    by_type: Dict[str, int] = field(default_factory=dict)
    by_standard: Dict[str, int] = field(default_factory=dict)
    total_processing_time: float = 0.0
    avg_processing_time: float = 0.0
    last_generation: Optional[datetime] = None
    start_time: datetime = field(default_factory=datetime.now)
    
    def record_generation(self, interface_type: NftFeatureType, standard: NftStandard,
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
        self.by_standard[standard.value] = self.by_standard.get(standard.value, 0) + 1
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "interfaces_generated": self.interfaces_generated,
            "interfaces_succeeded": self.interfaces_succeeded,
            "interfaces_failed": self.interfaces_failed,
            "by_type": self.by_type,
            "by_standard": self.by_standard,
            "avg_processing_time_ms": round(self.avg_processing_time, 2),
            "total_processing_time_ms": round(self.total_processing_time, 2),
            "last_generation": self.last_generation.isoformat() if self.last_generation else None,
            "uptime_seconds": (datetime.now() - self.start_time).total_seconds()
        }


# ============================================================================
# SOUS-AGENT PRINCIPAL
# ============================================================================

class NftUiSpecialistSubAgent(BaseSubAgent):
    """
    Sous-agent spécialiste des interfaces NFT
    
    Génère des interfaces NFT complètes : galerie, mint, enchères,
    marketplace et pages de détail.
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
        self._subagent_display_name = config.get('display_name', "🖼️ Spécialiste Interfaces NFT")
        self._subagent_description = config.get('description', "Génération d'interfaces NFT")
        self._subagent_version = config.get('version', "2.0.0")
        self._subagent_category = config.get('category', "frontend_web3")
        self._subagent_capabilities = [
            "nft.generate_gallery",
            "nft.generate_mint_interface",
            "nft.generate_auction_interface",
            "nft.generate_marketplace",
            "nft.generate_detail_page",
            "nft.generate_collection_page"
        ]
        
        # Templates
        self._templates = self._load_templates()
        
        # Statistiques
        self._stats = NftStats()
        
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
        logger.info("Initialisation des composants NFT Specialist...")
        
        self._processor_task = asyncio.create_task(self._processor_loop())
        
        self._components = {
            "version": self._subagent_version,
            "standards": [s.value for s in NftStandard],
            "features": [f.value for f in NftFeatureType],
            "templates": list(self._templates.keys())
        }
        
        logger.info("✅ Composants NFT Specialist initialisés")
        return True
        
    async def _initialize_components(self) -> bool:
        return await self._initialize_subagent_components()

    def _get_capability_handlers(self) -> Dict[str, Callable]:
        return {
            "nft.generate_gallery": self._handle_generate_gallery,
            "nft.generate_mint_interface": self._handle_generate_mint_interface,
            "nft.generate_auction_interface": self._handle_generate_auction_interface,
            "nft.generate_marketplace": self._handle_generate_marketplace,
            "nft.generate_detail_page": self._handle_generate_detail_page,
            "nft.generate_collection_page": self._handle_generate_collection_page,
        }
    
    # ============================================================================
    # TEMPLATES
    # ============================================================================
    
    def _load_templates(self) -> Dict[str, str]:
        """Charge les templates d'interfaces NFT"""
        return {
            "gallery": """
import {{ useState, useEffect }} from 'react';
import NFTCard from './NFTCard';

export default function NFTGallery() {{
  const [nfts, setNfts] = useState([]);
  const [loading, setLoading] = useState(true);
  
  useEffect(() => {{
    fetchNFTs();
  }}, []);
  
  const fetchNFTs = async () => {{
    // Simuler un appel API
    setLoading(false);
  }};
  
  if (loading) return <div>Loading...</div>;
  
  return (
    <div className="nft-gallery">
      <div className="gallery-header">
        <h1>{collection_name}</h1>
        <div className="filters">
          <input type="text" placeholder="Search NFTs..." />
          <select>
            <option>All</option>
            <option>For Sale</option>
            <option>Has Offers</option>
          </select>
        </div>
      </div>
      
      <div className="nft-grid">
        {{nfts.map(nft => (
          <NFTCard key={{nft.id}} nft={{nft}} />
        ))}}
      </div>
    </div>
  );
}}
""",
            "mint": """
import {{ useState }} from 'react';
import {{ useAccount, useBalance, useContractWrite, usePrepareContractWrite }} from 'wagmi';

export default function MintInterface() {{
  const [mintAmount, setMintAmount] = useState(1);
  const [totalPrice, setTotalPrice] = useState({price});
  const {{ address }} = useAccount();
  
  const {{ data: balance }} = useBalance({{
    address,
    token: 'ETH',
  }});
  
  const handleMint = async () => {{
    console.log('Minting...');
  }};
  
  return (
    <div className="mint-interface">
      <h2>Mint {collection_name}</h2>
      
      <div className="mint-info">
        <div>Price: {price} ETH</div>
        <div>Max per wallet: {max_per_wallet}</div>
        <div>Total minted: 1,234/{max_supply}</div>
      </div>
      
      <div className="mint-controls">
        <button onClick={{() => setMintAmount(Math.max(1, mintAmount - 1))}}>-</button>
        <span>{{mintAmount}}</span>
        <button onClick={{() => setMintAmount(Math.min({max_per_wallet}, mintAmount + 1))}}>+</button>
      </div>
      
      <div className="total-price">
        Total: {{totalPrice}} ETH + gas
      </div>
      
      <button className="mint-button" onClick={{handleMint}} disabled={{!address}}>
        Mint
      </button>
    </div>
  );
}}
""",
            "auction": """
import {{ useState, useEffect }} from 'react';

export default function AuctionInterface() {{
  const [bidAmount, setBidAmount] = useState('');
  const [timeLeft, setTimeLeft] = useState('');
  
  useEffect(() => {{
    const timer = setInterval(() => {{
      setTimeLeft('2d 4h 30m');
    }}, 1000);
    return () => clearInterval(timer);
  }}, []);
  
  return (
    <div className="auction-interface">
      <h2>{nft_name} - Auction</h2>
      
      <div className="auction-header">
        <div className="current-bid">
          <label>Current Bid</label>
          <div className="bid-value">{starting_bid} ETH</div>
        </div>
        <div className="time-left">
          <label>Time Left</label>
          <div className="time-value">{{timeLeft}}</div>
        </div>
      </div>
      
      <div className="bid-history">
        <h3>Bid History</h3>
        <div className="bids-list">
          {/* Liste des enchères */}
        </div>
      </div>
      
      <div className="place-bid">
        <h3>Place a Bid</h3>
        <p>Minimum increment: {min_increment} ETH</p>
        <input
          type="text"
          value={{bidAmount}}
          onChange={{e => setBidAmount(e.target.value)}}
          placeholder="Enter bid amount"
        />
        <button disabled={{!bidAmount}}>Place Bid</button>
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
    
    async def generate_gallery(self, config: NftConfig) -> NftInterfaceResult:
        """Génère une galerie NFT"""
        start_time = time.time()
        result = NftInterfaceResult(interface_type=NftFeatureType.GALLERY)
        
        try:
            template = self._templates.get("gallery", self._templates["gallery"])
            
            result.code = template.format(
                collection_name=config.name,
                max_supply=config.max_supply
            )
            result.success = True
            
            processing_time = (time.time() - start_time) * 1000
            result.processing_time_ms = processing_time
            self._stats.record_generation(NftFeatureType.GALLERY, config.standard, processing_time, True)
            
            await self._log_event("gallery_generated", {
                "interface_id": result.interface_id,
                "collection": config.name,
                "processing_time_ms": processing_time
            })
            
        except Exception as e:
            result.success = False
            result.error = str(e)
            processing_time = (time.time() - start_time) * 1000
            result.processing_time_ms = processing_time
            self._stats.record_generation(NftFeatureType.GALLERY, config.standard, processing_time, False)
            logger.error(f"❌ Erreur génération galerie: {e}")
        
        return result
    
    async def generate_mint_interface(self, config: MintConfig) -> NftInterfaceResult:
        """Génère une interface de mint"""
        start_time = time.time()
        result = NftInterfaceResult(interface_type=NftFeatureType.MINT)
        
        try:
            template = self._templates.get("mint", self._templates["mint"])
            
            result.code = template.format(
                collection_name=config.name,
                price=config.price,
                max_per_wallet=config.max_per_wallet,
                max_supply=config.max_supply
            )
            result.success = True
            
            processing_time = (time.time() - start_time) * 1000
            result.processing_time_ms = processing_time
            self._stats.record_generation(NftFeatureType.MINT, config.standard, processing_time, True)
            
        except Exception as e:
            result.success = False
            result.error = str(e)
            processing_time = (time.time() - start_time) * 1000
            result.processing_time_ms = processing_time
            self._stats.record_generation(NftFeatureType.MINT, config.standard, processing_time, False)
        
        return result
    
    async def generate_auction_interface(self, config: AuctionConfig) -> NftInterfaceResult:
        """Génère une interface d'enchère"""
        start_time = time.time()
        result = NftInterfaceResult(interface_type=NftFeatureType.AUCTION)
        
        try:
            template = self._templates.get("auction", self._templates["auction"])
            
            result.code = template.format(
                nft_name=config.nft_id or "NFT",
                starting_bid=config.starting_bid,
                min_increment=config.min_increment
            )
            result.success = True
            
            processing_time = (time.time() - start_time) * 1000
            result.processing_time_ms = processing_time
            self._stats.record_generation(NftFeatureType.AUCTION, NftStandard.ERC721, processing_time, True)
            
        except Exception as e:
            result.success = False
            result.error = str(e)
            processing_time = (time.time() - start_time) * 1000
            result.processing_time_ms = processing_time
            self._stats.record_generation(NftFeatureType.AUCTION, NftStandard.ERC721, processing_time, False)
        
        return result
    
    async def generate_marketplace(self, config: NftConfig) -> NftInterfaceResult:
        """Génère une marketplace NFT"""
        start_time = time.time()
        result = NftInterfaceResult(interface_type=NftFeatureType.MARKETPLACE)
        
        try:
            code = f"""
import {{ useState }} from 'react';
import NFTGrid from './NFTGrid';

export default function Marketplace() {{
  const [filter, setFilter] = useState('all');
  const [sort, setSort] = useState('recent');
  
  return (
    <div className="marketplace">
      <header className="marketplace-header">
        <h1>{config.name} Marketplace</h1>
        
        <div className="filters">
          <select value={{filter}} onChange={{e => setFilter(e.target.value)}}>
            <option value="all">All</option>
            <option value="buy-now">Buy Now</option>
            <option value="on-auction">On Auction</option>
          </select>
          
          <select value={{sort}} onChange={{e => setSort(e.target.value)}}>
            <option value="recent">Recently Listed</option>
            <option value="price-low">Price: Low to High</option>
            <option value="price-high">Price: High to Low</option>
          </select>
        </div>
      </header>
      
      <div className="marketplace-stats">
        <div>Total listings: 10,234</div>
        <div>Total volume: 15,234 ETH</div>
      </div>
      
      <main>
        <NFTGrid filter={{filter}} sort={{sort}} />
      </main>
    </div>
  );
}}
"""
            result.code = code
            result.success = True
            
            processing_time = (time.time() - start_time) * 1000
            result.processing_time_ms = processing_time
            self._stats.record_generation(NftFeatureType.MARKETPLACE, config.standard, processing_time, True)
            
        except Exception as e:
            result.success = False
            result.error = str(e)
            processing_time = (time.time() - start_time) * 1000
            result.processing_time_ms = processing_time
            self._stats.record_generation(NftFeatureType.MARKETPLACE, config.standard, processing_time, False)
        
        return result
    
    async def generate_detail_page(self, nft_id: str, collection: str = "Collection") -> NftInterfaceResult:
        """Génère une page de détail NFT"""
        start_time = time.time()
        result = NftInterfaceResult(interface_type=NftFeatureType.DETAIL)
        
        try:
            code = f"""
import {{ useState }} from 'react';
import { useParams } from 'react-router-dom';

export default function NFTDetailPage() {{
  const [activeTab, setActiveTab] = useState('details');
  const {{ id }} = useParams();
  
  return (
    <div className="nft-detail-page">
      <div className="nft-content">
        <div className="nft-media">
          <img src="/nft-image.jpg" alt="NFT" />
        </div>
        
        <div className="nft-info">
          <h1>{collection} #{nft_id}</h1>
          
          <div className="nft-stats">
            <div className="stat">
              <label>Owned by</label>
              <div>0x1234...5678</div>
            </div>
            <div className="stat">
              <label>Current price</label>
              <div>2.5 ETH</div>
            </div>
          </div>
          
          <div className="nft-actions">
            <button className="buy-now">Buy Now</button>
            <button className="make-offer">Make Offer</button>
          </div>
          
          <div className="nft-details-tabs">
            <button className={{activeTab === 'details' ? 'active' : ''}}
                    onClick={{() => setActiveTab('details')}}>Details</button>
            <button className={{activeTab === 'attributes' ? 'active' : ''}}
                    onClick={{() => setActiveTab('attributes')}}>Attributes</button>
            <button className={{activeTab === 'activity' ? 'active' : ''}}
                    onClick={{() => setActiveTab('activity')}}>Activity</button>
          </div>
          
          <div className="nft-details-content">
            {{activeTab === 'details' && <div>NFT Details...</div>}}
            {{activeTab === 'attributes' && <div>Attributes...</div>}}
            {{activeTab === 'activity' && <div>Activity...</div>}}
          </div>
        </div>
      </div>
    </div>
  );
}}
"""
            result.code = code
            result.success = True
            
            processing_time = (time.time() - start_time) * 1000
            result.processing_time_ms = processing_time
            self._stats.record_generation(NftFeatureType.DETAIL, NftStandard.ERC721, processing_time, True)
            
        except Exception as e:
            result.success = False
            result.error = str(e)
            processing_time = (time.time() - start_time) * 1000
            result.processing_time_ms = processing_time
            self._stats.record_generation(NftFeatureType.DETAIL, NftStandard.ERC721, processing_time, False)
        
        return result
    
    async def generate_collection_page(self, config: NftConfig) -> NftInterfaceResult:
        """Génère une page de collection"""
        start_time = time.time()
        result = NftInterfaceResult(interface_type=NftFeatureType.COLLECTION)
        
        try:
            code = f"""
import {{ useState }} from 'react';
import CollectionStats from './CollectionStats';
import CollectionGrid from './CollectionGrid';

export default function CollectionPage() {{
  const [activeTab, setActiveTab] = useState('items');
  
  return (
    <div className="collection-page">
      <div className="collection-header">
        <img src="/collection-banner.jpg" alt="{config.name}" />
        <div className="collection-info">
          <h1>{config.name}</h1>
          <p>A collection of {config.max_supply} unique NFTs</p>
        </div>
      </div>
      
      <CollectionStats />
      
      <div className="collection-tabs">
        <button className={{activeTab === 'items' ? 'active' : ''}}
                onClick={{() => setActiveTab('items')}}>Items</button>
        <button className={{activeTab === 'activity' ? 'active' : ''}}
                onClick={{() => setActiveTab('activity')}}>Activity</button>
      </div>
      
      <div className="collection-content">
        {{activeTab === 'items' && <CollectionGrid />}}
        {{activeTab === 'activity' && <CollectionActivity />}}
      </div>
    </div>
  );
}}
"""
            result.code = code
            result.success = True
            
            processing_time = (time.time() - start_time) * 1000
            result.processing_time_ms = processing_time
            self._stats.record_generation(NftFeatureType.COLLECTION, config.standard, processing_time, True)
            
        except Exception as e:
            result.success = False
            result.error = str(e)
            processing_time = (time.time() - start_time) * 1000
            result.processing_time_ms = processing_time
            self._stats.record_generation(NftFeatureType.COLLECTION, config.standard, processing_time, False)
        
        return result
    
    # ============================================================================
    # HANDLERS
    # ============================================================================
    
    async def _handle_generate_gallery(self, params: Dict[str, Any]) -> Dict[str, Any]:
        config = NftConfig(
            name=params.get("name", "NFT Collection"),
            symbol=params.get("symbol", "NFT"),
            standard=NftStandard.from_string(params.get("standard", "erc721")),
            max_supply=params.get("max_supply", 10000)
        )
        result = await self.generate_gallery(config)
        return result.to_dict()
    
    async def _handle_generate_mint_interface(self, params: Dict[str, Any]) -> Dict[str, Any]:
        config = MintConfig(
            name=params.get("name", "NFT Collection"),
            symbol=params.get("symbol", "NFT"),
            standard=NftStandard.from_string(params.get("standard", "erc721")),
            max_supply=params.get("max_supply", 10000),
            price=params.get("price", 0.1),
            max_per_wallet=params.get("max_per_wallet", 5),
            presale_enabled=params.get("presale_enabled", False)
        )
        result = await self.generate_mint_interface(config)
        return result.to_dict()
    
    async def _handle_generate_auction_interface(self, params: Dict[str, Any]) -> Dict[str, Any]:
        config = AuctionConfig(
            nft_id=params.get("nft_id", ""),
            starting_bid=params.get("starting_bid", 1.0),
            min_increment=params.get("min_increment", 0.1),
            duration_hours=params.get("duration_hours", 24)
        )
        result = await self.generate_auction_interface(config)
        return result.to_dict()
    
    async def _handle_generate_marketplace(self, params: Dict[str, Any]) -> Dict[str, Any]:
        config = NftConfig(
            name=params.get("name", "Marketplace"),
            symbol=params.get("symbol", "MKT"),
            max_supply=params.get("max_supply", 10000)
        )
        result = await self.generate_marketplace(config)
        return result.to_dict()
    
    async def _handle_generate_detail_page(self, params: Dict[str, Any]) -> Dict[str, Any]:
        nft_id = params.get("nft_id", "1")
        collection = params.get("collection", "Collection")
        result = await self.generate_detail_page(nft_id, collection)
        return result.to_dict()
    
    async def _handle_generate_collection_page(self, params: Dict[str, Any]) -> Dict[str, Any]:
        config = NftConfig(
            name=params.get("name", "Collection"),
            symbol=params.get("symbol", "COL"),
            max_supply=params.get("max_supply", 10000)
        )
        result = await self.generate_collection_page(config)
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
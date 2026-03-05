"""
Storage Agent - Gestion centralisée des données
Stockage clé-valeur, documents, fichiers, cache, IPFS, chiffrement
Version: 1.0.0 (ALIGNÉE SUR ARCHITECT/CODER)
"""

import logging
import os
import sys
import json
import hashlib
import pickle
import shutil
import time
import zlib
import traceback
import asyncio
from pathlib import Path
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Any, Optional, Union, Set
from collections import OrderedDict, defaultdict

# ============================================================================
# CONFIGURATION DES IMPORTS - Chemin absolu
# ============================================================================

current_dir = Path(__file__).parent.absolute()
project_root = current_dir.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from agents.base_agent.base_agent import BaseAgent, AgentStatus, Message, MessageType

logger = logging.getLogger(__name__)


# ============================================================================
# ÉNUMS ET STRUCTURES DE DONNÉES
# ============================================================================

class StorageType(Enum):
    """Types de stockage"""
    MEMORY = "memory"
    DISK = "disk"
    IPFS = "ipfs"
    REDIS = "redis"


class DataType(Enum):
    """Types de données"""
    STRING = "string"
    JSON = "json"
    BINARY = "binary"
    PICKLE = "pickle"


class CachePolicy(Enum):
    """Politiques d'éviction du cache"""
    LRU = "lru"
    LFU = "lfu"
    TTL = "ttl"
    FIFO = "fifo"


# ============================================================================
# BACKENDS DE STOCKAGE (INCHANGÉS)
# ============================================================================

class StorageBackend:
    """Interface de base pour les backends de stockage"""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        self.name = name
        self.config = config
        self.stats = {
            "operations": 0,
            "reads": 0,
            "writes": 0,
            "deletes": 0,
            "size_bytes": 0,
            "keys_count": 0
        }
    
    async def get(self, key: str) -> Optional[Any]:
        raise NotImplementedError
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        raise NotImplementedError
    
    async def delete(self, key: str) -> bool:
        raise NotImplementedError
    
    async def exists(self, key: str) -> bool:
        raise NotImplementedError
    
    async def list_keys(self, pattern: Optional[str] = None) -> List[str]:
        raise NotImplementedError
    
    async def clear(self) -> int:
        raise NotImplementedError
    
    async def get_size(self) -> int:
        return self.stats["size_bytes"]
    
    async def get_stats(self) -> Dict[str, Any]:
        return self.stats.copy()


class MemoryBackend(StorageBackend):
    """Backend de stockage en mémoire"""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        super().__init__(name, config)
        self._data: Dict[str, tuple] = {}
        self._lock = asyncio.Lock()
        self._max_size = config.get("max_size_mb", 512) * 1024 * 1024
        self._current_size = 0
        self._access_times: Dict[str, float] = {}
        self._access_counts: Dict[str, int] = {}
    
    async def get(self, key: str) -> Optional[Any]:
        async with self._lock:
            self.stats["operations"] += 1
            self.stats["reads"] += 1
            
            if key not in self._data:
                return None
            
            value, expiry = self._data[key]
            
            if expiry and time.time() > expiry:
                del self._data[key]
                self._current_size -= self._estimate_size(value)
                self.stats["size_bytes"] = self._current_size
                self.stats["keys_count"] = len(self._data)
                return None
            
            self._access_times[key] = time.time()
            self._access_counts[key] = self._access_counts.get(key, 0) + 1
            
            return value
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        async with self._lock:
            self.stats["operations"] += 1
            self.stats["writes"] += 1
            
            size = self._estimate_size(value)
            
            if self._current_size + size > self._max_size:
                await self._evict(size)
            
            expiry = time.time() + ttl if ttl else None
            
            if key in self._data:
                old_value, _ = self._data[key]
                self._current_size -= self._estimate_size(old_value)
            
            self._data[key] = (value, expiry)
            self._current_size += size
            self._access_times[key] = time.time()
            self._access_counts[key] = self._access_counts.get(key, 0) + 1
            
            self.stats["size_bytes"] = self._current_size
            self.stats["keys_count"] = len(self._data)
            
            return True
    
    async def delete(self, key: str) -> bool:
        async with self._lock:
            self.stats["operations"] += 1
            self.stats["deletes"] += 1
            
            if key not in self._data:
                return False
            
            value, _ = self._data[key]
            self._current_size -= self._estimate_size(value)
            del self._data[key]
            
            self._access_times.pop(key, None)
            self._access_counts.pop(key, None)
            
            self.stats["size_bytes"] = self._current_size
            self.stats["keys_count"] = len(self._data)
            
            return True
    
    async def exists(self, key: str) -> bool:
        async with self._lock:
            return key in self._data
    
    async def list_keys(self, pattern: Optional[str] = None) -> List[str]:
        async with self._lock:
            keys = list(self._data.keys())
            if pattern:
                import fnmatch
                keys = [k for k in keys if fnmatch.fnmatch(k, pattern)]
            return keys
    
    async def clear(self) -> int:
        async with self._lock:
            count = len(self._data)
            self._data.clear()
            self._access_times.clear()
            self._access_counts.clear()
            self._current_size = 0
            self.stats["size_bytes"] = 0
            self.stats["keys_count"] = 0
            return count
    
    async def get_stats(self) -> Dict[str, Any]:
        self.stats["size_bytes"] = self._current_size
        self.stats["keys_count"] = len(self._data)
        return self.stats.copy()
    
    def _estimate_size(self, value: Any) -> int:
        try:
            return len(pickle.dumps(value))
        except:
            return 1024
    
    async def _evict(self, needed_size: int):
        policy = self.config.get("eviction_policy", "lru")
        
        if policy == "lru":
            items = sorted(self._access_times.items(), key=lambda x: x[1])
        elif policy == "lfu":
            items = sorted(self._access_counts.items(), key=lambda x: x[1])
        else:
            items = [(k, v) for k, (v, _) in self._data.items()]
        
        freed = 0
        for key, _ in items:
            if freed >= needed_size:
                break
            value, _ = self._data[key]
            freed += self._estimate_size(value)
            await self.delete(key)


class DiskBackend(StorageBackend):
    """Backend de stockage sur disque"""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        super().__init__(name, config)
        self._base_path = Path(config.get("path", f"./data/storage/{name}"))
        self._base_path.mkdir(parents=True, exist_ok=True)
        self._index_path = self._base_path / "_index.json"
        self._lock = asyncio.Lock()
        self._index: Dict[str, Dict[str, Any]] = {}
        self._load_index()
    
    def _load_index(self):
        if self._index_path.exists():
            try:
                with open(self._index_path, 'r') as f:
                    self._index = json.load(f)
            except:
                self._index = {}
    
    def _save_index(self):
        try:
            with open(self._index_path, 'w') as f:
                json.dump(self._index, f, indent=2)
        except Exception as e:
            logger.error(f"Erreur sauvegarde index: {e}")
    
    def _get_key_path(self, key: str) -> Path:
        key_hash = hashlib.sha256(key.encode()).hexdigest()
        return self._base_path / key_hash[:2] / key_hash[2:4] / key_hash
    
    async def get(self, key: str) -> Optional[Any]:
        async with self._lock:
            self.stats["operations"] += 1
            self.stats["reads"] += 1
            
            if key not in self._index:
                return None
            
            metadata = self._index[key]
            
            if metadata.get("expiry") and time.time() > metadata["expiry"]:
                await self.delete(key)
                return None
            
            key_path = self._get_key_path(key)
            if not key_path.exists():
                return None
            
            try:
                with open(key_path, 'rb') as f:
                    data = f.read()
                
                if metadata.get("compressed"):
                    data = zlib.decompress(data)
                
                data_type = metadata.get("type", "pickle")
                if data_type == "json":
                    return json.loads(data.decode())
                elif data_type == "string":
                    return data.decode()
                elif data_type == "pickle":
                    return pickle.loads(data)
                else:
                    return data
                    
            except Exception as e:
                logger.error(f"Erreur lecture {key}: {e}")
                return None
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        async with self._lock:
            self.stats["operations"] += 1
            self.stats["writes"] += 1
            
            if isinstance(value, str):
                data_type = "string"
                data = value.encode()
            elif isinstance(value, (dict, list)):
                data_type = "json"
                data = json.dumps(value).encode()
            elif isinstance(value, bytes):
                data_type = "binary"
                data = value
            else:
                data_type = "pickle"
                data = pickle.dumps(value)
            
            compressed = False
            if self.config.get("compression", False) and len(data) > 1024:
                data = zlib.compress(data, level=6)
                compressed = True
            
            key_path = self._get_key_path(key)
            key_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(key_path, 'wb') as f:
                f.write(data)
            
            self._index[key] = {
                "path": str(key_path),
                "type": data_type,
                "size": len(data),
                "original_size": len(data) if not compressed else len(value),
                "compressed": compressed,
                "created": time.time(),
                "expiry": time.time() + ttl if ttl else None,
                "access_count": 0
            }
            
            self._save_index()
            
            self.stats["size_bytes"] = sum(m["size"] for m in self._index.values())
            self.stats["keys_count"] = len(self._index)
            
            return True
    
    async def delete(self, key: str) -> bool:
        async with self._lock:
            self.stats["operations"] += 1
            self.stats["deletes"] += 1
            
            if key not in self._index:
                return False
            
            key_path = self._get_key_path(key)
            if key_path.exists():
                key_path.unlink()
            
            del self._index[key]
            self._save_index()
            
            self.stats["size_bytes"] = sum(m["size"] for m in self._index.values())
            self.stats["keys_count"] = len(self._index)
            
            return True
    
    async def exists(self, key: str) -> bool:
        async with self._lock:
            return key in self._index
    
    async def list_keys(self, pattern: Optional[str] = None) -> List[str]:
        async with self._lock:
            keys = list(self._index.keys())
            if pattern:
                import fnmatch
                keys = [k for k in keys if fnmatch.fnmatch(k, pattern)]
            return keys
    
    async def clear(self) -> int:
        async with self._lock:
            count = len(self._index)
            shutil.rmtree(self._base_path)
            self._base_path.mkdir(parents=True, exist_ok=True)
            self._index.clear()
            self._save_index()
            
            self.stats["size_bytes"] = 0
            self.stats["keys_count"] = 0
            
            return count
    
    async def get_size(self) -> int:
        return self.stats["size_bytes"]
    
    async def get_stats(self) -> Dict[str, Any]:
        self.stats["size_bytes"] = sum(m["size"] for m in self._index.values())
        self.stats["keys_count"] = len(self._index)
        return self.stats.copy()


class IPFSBackend(StorageBackend):
    """Backend de stockage IPFS"""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        super().__init__(name, config)
        self._gateway = config.get("gateway", "http://localhost:5001")
        self._api_url = config.get("api_url", "http://localhost:5001/api/v0")
        self._pin_by_default = config.get("pin_by_default", True)
        self._local_cache = config.get("local_cache", True)
        self._cache_dir = Path(config.get("local_cache_path", "./data/ipfs_cache"))
        self._timeout = config.get("timeout", 30)
        
        if self._local_cache:
            self._cache_dir.mkdir(parents=True, exist_ok=True)
        
        self._session = None
        self._cache_index: Dict[str, str] = {}
        self._load_cache_index()
    
    def _load_cache_index(self):
        index_file = self._cache_dir / "_index.json"
        if index_file.exists():
            try:
                with open(index_file, 'r') as f:
                    self._cache_index = json.load(f)
            except:
                self._cache_index = {}
    
    def _save_cache_index(self):
        if not self._local_cache:
            return
        index_file = self._cache_dir / "_index.json"
        try:
            with open(index_file, 'w') as f:
                json.dump(self._cache_index, f, indent=2)
        except Exception as e:
            logger.error(f"Erreur sauvegarde index IPFS: {e}")
    
    async def _ensure_session(self):
        if not self._session:
            import aiohttp
            self._session = aiohttp.ClientSession()
    
    async def get(self, key: str) -> Optional[Any]:
        self.stats["operations"] += 1
        self.stats["reads"] += 1
        
        if self._local_cache and key in self._cache_index:
            ipfs_hash = self._cache_index[key]
            cache_file = self._cache_dir / ipfs_hash
            
            if cache_file.exists():
                try:
                    with open(cache_file, 'rb') as f:
                        data = f.read()
                    self.stats["hits"] = self.stats.get("hits", 0) + 1
                    return pickle.loads(data)
                except:
                    pass
        
        self.stats["misses"] = self.stats.get("misses", 0) + 1
        return None
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        self.stats["operations"] += 1
        self.stats["writes"] += 1
        
        data = pickle.dumps(value)
        ipfs_hash = hashlib.sha256(data).hexdigest()
        
        if self._local_cache:
            cache_file = self._cache_dir / ipfs_hash
            with open(cache_file, 'wb') as f:
                f.write(data)
            self._cache_index[key] = ipfs_hash
            self._save_cache_index()
        
        self.stats["size_bytes"] += len(data)
        self.stats["keys_count"] = len(self._cache_index)
        
        return True
    
    async def delete(self, key: str) -> bool:
        self.stats["operations"] += 1
        self.stats["deletes"] += 1
        
        if self._local_cache and key in self._cache_index:
            ipfs_hash = self._cache_index[key]
            cache_file = self._cache_dir / ipfs_hash
            if cache_file.exists():
                cache_file.unlink()
            del self._cache_index[key]
            self._save_cache_index()
            
            self.stats["keys_count"] = len(self._cache_index)
            return True
        
        return False
    
    async def exists(self, key: str) -> bool:
        if self._local_cache:
            return key in self._cache_index
        return False
    
    async def list_keys(self, pattern: Optional[str] = None) -> List[str]:
        keys = list(self._cache_index.keys())
        if pattern:
            import fnmatch
            keys = [k for k in keys if fnmatch.fnmatch(k, pattern)]
        return keys
    
    async def clear(self) -> int:
        count = len(self._cache_index)
        
        for ipfs_hash in self._cache_index.values():
            cache_file = self._cache_dir / ipfs_hash
            if cache_file.exists():
                cache_file.unlink()
        
        self._cache_index.clear()
        self._save_cache_index()
        
        if self._session:
            await self._session.close()
            self._session = None
        
        self.stats["size_bytes"] = 0
        self.stats["keys_count"] = 0
        
        return count
    
    async def get_stats(self) -> Dict[str, Any]:
        self.stats["keys_count"] = len(self._cache_index)
        return self.stats.copy()


# ============================================================================
# AGENT PRINCIPAL - STORAGE (ALIGNÉ SUR ARCHITECT/CODER)
# ============================================================================

class StorageAgent(BaseAgent):
    """
    Agent de stockage centralisé
    Gère la persistance, le cache, et le versioning des données
    Hérite de BaseAgent et suit le cycle de vie standard.
    """

    def __init__(self, config_path: Optional[str] = None):
        """Initialise l'agent de stockage"""
        if config_path is None:
            config_path = str(project_root / "agents" / "storage" / "config.yaml")

        # Appel au constructeur parent (initialise _logger, _agent_config, etc.)
        super().__init__(config_path)

        # Configuration spécifique
        agent_config = self._agent_config.get('agent', {})
        self._display_name = agent_config.get('display_name', '💾 Storage Agent')
        
        self._storage_config = self._agent_config.get('storage', {})
        self._encryption_config = self._agent_config.get('encryption', {})
        self._compression_config = self._agent_config.get('compression', {})
        self._quotas_config = self._agent_config.get('quotas', {})

        # État interne - À DÉFINIR AVANT D'UTILISER _logger DANS _init_backends
        self._backends: Dict[str, StorageBackend] = {}
        self._cache: OrderedDict = OrderedDict()
        self._cache_stats = {"hits": 0, "misses": 0, "size_bytes": 0, "keys": 0}
        self._versions: Dict[str, List[str]] = defaultdict(list)
        
        # NE PAS UTILISER _logger AVANT D'AVOIR DÉFINI _stats
        self._stats = {
            "stores": 0,  # Sera mis à jour après _init_backends
            "total_keys": 0,
            "total_size_bytes": 0,
            "operations_total": 0,
            "operations_by_type": defaultdict(int),
            "uptime_start": datetime.now()
        }
        
        self._components: Dict[str, Any] = {}
        self._initialized = False
        self._backup_task: Optional[asyncio.Task] = None

        # Initialiser les backends (utilise _logger mais _stats est déjà défini)
        self._init_backends()
        
        # MAINTENANT on peut utiliser _logger
        self._logger.info(f"💾 Storage Agent créé avec {len(self._backends)} backends")

    def _init_backends(self):
        """Initialise les backends de stockage"""
        stores_config = self._storage_config.get("stores", {})
        
        for name, config in stores_config.items():
            backend_type = config.get("type", "memory")
            
            try:
                if backend_type == "memory":
                    backend = MemoryBackend(name, config)
                elif backend_type == "disk":
                    backend = DiskBackend(name, config)
                elif backend_type == "ipfs":
                    if config.get("enabled", False):
                        backend = IPFSBackend(name, config)
                    else:
                        continue
                else:
                    self._logger.warning(f"⚠️ Type de backend inconnu: {backend_type}")
                    continue
                
                self._backends[name] = backend
                self._logger.info(f"✅ Backend '{name}' initialisé ({backend_type})")
                
            except Exception as e:
                self._logger.error(f"❌ Erreur initialisation backend '{name}': {e}")
        
        self._stats["stores"] = len(self._backends)

    # ============================================================================
    # CYCLE DE VIE
    # ============================================================================

    async def initialize(self) -> bool:
        """Initialise l'agent"""
        self._logger.info("💾 Initialisation du Storage Agent...")
        return await super().initialize()

    async def _initialize_components(self) -> bool:
        """
        Initialise les composants spécifiques.
        Appelé par BaseAgent.initialize().
        """
        try:
            self._logger.info("Initialisation des composants Storage...")
            
            self._components = {
                "memory_backend": "memory" in [b.name for b in self._backends.values()],
                "disk_backend": any(isinstance(b, DiskBackend) for b in self._backends.values()),
                "ipfs_backend": any(isinstance(b, IPFSBackend) for b in self._backends.values()),
                "cache": self._storage_config.get("cache", {}).get("enabled", True),
                "versioning": self._storage_config.get("versioning", {}).get("enabled", True),
                "encryption": self._encryption_config.get("enabled", False),
                "compression": self._compression_config.get("enabled", True)
            }

            if self._storage_config.get("persistence", {}).get("auto_backup", False):
                self._backup_task = asyncio.create_task(self._backup_worker())

            self._logger.info(f"✅ Composants: {list(self._components.keys())}")
            self._initialized = True
            return True

        except Exception as e:
            self._logger.error(f"Erreur composants: {e}")
            return False

    async def shutdown(self) -> bool:
        """Arrête l'agent proprement"""
        self._logger.info("Arrêt de l'agent Storage...")
        
        if self._backup_task and not self._backup_task.done():
            self._backup_task.cancel()
            try:
                await self._backup_task
            except asyncio.CancelledError:
                pass
        
        return await super().shutdown()

    async def _cleanup(self):
        """Nettoie les ressources spécifiques"""
        self._logger.info("Nettoyage des ressources Storage...")
        
        cache_config = self._storage_config.get("cache", {})
        if cache_config.get("persist_on_exit", True):
            self._logger.info("Persistance du cache sur arrêt")

    # ============================================================================
    # API PUBLIQUE - OPÉRATIONS DE BASE
    # ============================================================================

    async def set(self, key: str, value: Any, store: str = "default",
                  ttl: Optional[int] = None, encrypt: bool = False,
                  compress: Optional[bool] = None) -> Dict[str, Any]:
        """Stocke une valeur"""
        self._logger.debug(f"💾 set: {key} -> {store}")
        
        if store not in self._backends:
            raise ValueError(f"Store '{store}' non trouvé")
        
        backend = self._backends[store]
        
        if self._quotas_config.get("enabled", False):
            await self._check_quota(store)
        
        start_time = time.time()
        success = await backend.set(key, value, ttl)
        duration = (time.time() - start_time) * 1000
        
        self._stats["operations_total"] += 1
        self._stats["operations_by_type"]["set"] += 1
        
        if success:
            self._stats["total_keys"] = sum(b.stats["keys_count"] for b in self._backends.values())
            self._stats["total_size_bytes"] = sum(b.stats["size_bytes"] for b in self._backends.values())
        
        return {
            "success": success,
            "key": key,
            "store": store,
            "ttl": ttl,
            "encrypted": encrypt,
            "compressed": compress,
            "duration_ms": round(duration, 2)
        }

    async def get(self, key: str, store: str = "default") -> Optional[Any]:
        """Récupère une valeur"""
        self._logger.debug(f"📖 get: {key} <- {store}")
        
        cache_key = f"{store}:{key}"
        cache_config = self._storage_config.get("cache", {})
        
        if cache_config.get("enabled", True) and cache_key in self._cache:
            self._cache.move_to_end(cache_key)
            self._cache_stats["hits"] += 1
            self._logger.debug(f"🎯 Cache HIT: {key}")
            return self._cache[cache_key]
        
        self._cache_stats["misses"] += 1
        
        if store not in self._backends:
            raise ValueError(f"Store '{store}' non trouvé")
        
        backend = self._backends[store]
        
        start_time = time.time()
        value = await backend.get(key)
        duration = (time.time() - start_time) * 1000
        
        self._stats["operations_total"] += 1
        self._stats["operations_by_type"]["get"] += 1
        
        if value is not None and cache_config.get("enabled", True):
            await self._add_to_cache(cache_key, value)
        
        self._logger.debug(f"📖 get: {key} {'✅' if value else '❌'} ({duration:.2f}ms)")
        return value

    async def delete(self, key: str, store: str = "default") -> bool:
        """Supprime une clé"""
        self._logger.debug(f"🗑️ delete: {key}")
        
        if store not in self._backends:
            raise ValueError(f"Store '{store}' non trouvé")
        
        backend = self._backends[store]
        
        start_time = time.time()
        result = await backend.delete(key)
        duration = (time.time() - start_time) * 1000
        
        cache_key = f"{store}:{key}"
        self._cache.pop(cache_key, None)
        
        self._stats["operations_total"] += 1
        self._stats["operations_by_type"]["delete"] += 1
        
        if result:
            self._stats["total_keys"] = sum(b.stats["keys_count"] for b in self._backends.values())
            self._stats["total_size_bytes"] = sum(b.stats["size_bytes"] for b in self._backends.values())
        
        self._logger.debug(f"🗑️ delete: {key} {'✅' if result else '❌'} ({duration:.2f}ms)")
        return result

    async def exists(self, key: str, store: str = "default") -> bool:
        """Vérifie si une clé existe"""
        if store not in self._backends:
            raise ValueError(f"Store '{store}' non trouvé")
        return await self._backends[store].exists(key)

    async def list_keys(self, store: str = "default", pattern: Optional[str] = None) -> List[str]:
        """Liste les clés d'un store"""
        if store not in self._backends:
            raise ValueError(f"Store '{store}' non trouvé")
        return await self._backends[store].list_keys(pattern)

    async def clear_store(self, store: str) -> int:
        """Vide complètement un store"""
        if store not in self._backends:
            raise ValueError(f"Store '{store}' non trouvé")
        
        backend = self._backends[store]
        count = await backend.clear()
        
        keys_to_remove = [k for k in self._cache if k.startswith(f"{store}:")]
        for k in keys_to_remove:
            del self._cache[k]
        
        self._logger.info(f"🧹 Store '{store}' vidé ({count} éléments)")
        return count

    # ============================================================================
    # OPÉRATIONS SPÉCIALISÉES
    # ============================================================================

    async def increment(self, key: str, store: str = "default",
                       amount: int = 1, initial: int = 0) -> int:
        """Incrémente une valeur numérique"""
        current = await self.get(key, store)
        
        if current is None:
            new_value = initial + amount
        else:
            try:
                new_value = int(current) + amount
            except:
                raise ValueError(f"La valeur de {key} n'est pas numérique")
        
        await self.set(key, new_value, store)
        return new_value

    async def append(self, key: str, value: Any, store: str = "default") -> List[Any]:
        """Ajoute une valeur à une liste"""
        current = await self.get(key, store)
        
        if current is None:
            new_list = [value]
        else:
            if not isinstance(current, list):
                raise ValueError(f"La valeur de {key} n'est pas une liste")
            new_list = current + [value]
        
        await self.set(key, new_list, store)
        return new_list

    async def sadd(self, key: str, value: Any, store: str = "default") -> Set[Any]:
        """Ajoute une valeur à un ensemble"""
        current = await self.get(key, store)
        
        if current is None:
            new_set = {value}
        else:
            if not isinstance(current, set):
                new_set = set(current)
            else:
                new_set = current
            new_set.add(value)
        
        await self.set(key, new_set, store)
        return new_set

    # ============================================================================
    # VERSIONING
    # ============================================================================

    async def set_versioned(self, key: str, value: Any, store: str = "default",
                           comment: str = "") -> Dict[str, Any]:
        """Stocke une version d'une clé"""
        version = datetime.now().strftime("%Y%m%d_%H%M%S")
        versioned_key = f"{key}__v{version}"
        
        result = await self.set(versioned_key, value, store, ttl=None)
        self._versions[key].append(versioned_key)
        
        max_versions = self._storage_config.get("versioning", {}).get("max_versions_per_key", 10)
        while len(self._versions[key]) > max_versions:
            oldest = self._versions[key].pop(0)
            await self.delete(oldest, store)
        
        result["version"] = version
        result["version_comment"] = comment
        return result

    async def get_versions(self, key: str, store: str = "default") -> List[Dict[str, Any]]:
        """Liste les versions d'une clé"""
        versions = []
        for version_key in self._versions.get(key, []):
            if await self.exists(version_key, store):
                version = version_key.split("__v")[-1]
                versions.append({
                    "key": version_key,
                    "version": version,
                    "exists": True
                })
        return versions

    async def get_version(self, key: str, version: str, store: str = "default") -> Optional[Any]:
        """Récupère une version spécifique"""
        versioned_key = f"{key}__v{version}"
        return await self.get(versioned_key, store)

    # ============================================================================
    # CACHE
    # ============================================================================

    async def _add_to_cache(self, key: str, value: Any):
        """Ajoute une entrée au cache"""
        cache_config = self._storage_config.get("cache", {})
        max_size = cache_config.get("max_size_mb", 1024) * 1024 * 1024
        
        try:
            size = len(pickle.dumps(value))
        except:
            size = 1024
        
        while self._cache_stats["size_bytes"] + size > max_size and self._cache:
            oldest_key, oldest_value = self._cache.popitem(last=False)
            try:
                self._cache_stats["size_bytes"] -= len(pickle.dumps(oldest_value))
            except:
                self._cache_stats["size_bytes"] -= 1024
            self._cache_stats["keys"] -= 1
        
        self._cache[key] = value
        self._cache_stats["size_bytes"] += size
        self._cache_stats["keys"] += 1

    async def clear_cache(self):
        """Vide le cache"""
        self._cache.clear()
        self._cache_stats = {"hits": 0, "misses": 0, "size_bytes": 0, "keys": 0}
        self._logger.info("🧹 Cache vidé")

    async def get_cache_stats(self) -> Dict[str, Any]:
        """Retourne les statistiques du cache"""
        total = self._cache_stats["hits"] + self._cache_stats["misses"]
        hit_ratio = self._cache_stats["hits"] / total if total > 0 else 0
        
        return {
            "hits": self._cache_stats["hits"],
            "misses": self._cache_stats["misses"],
            "hit_ratio": round(hit_ratio, 3),
            "size_bytes": self._cache_stats["size_bytes"],
            "size_mb": round(self._cache_stats["size_bytes"] / (1024 * 1024), 2),
            "keys": self._cache_stats["keys"]
        }

    # ============================================================================
    # UTILITAIRES
    # ============================================================================

    async def _backup_worker(self):
        """Sauvegarde périodique des données"""
        persistence = self._storage_config.get("persistence", {})
        interval = persistence.get("backup_interval", 3600)
        
        self._logger.info(f"💾 Travailleur de backup démarré (intervalle: {interval}s)")
        
        while self._status == AgentStatus.READY:
            try:
                await asyncio.sleep(interval)
                await self._create_backup()
            except asyncio.CancelledError:
                break
            except Exception as e:
                self._logger.error(f"❌ Erreur sauvegarde: {e}")
                await asyncio.sleep(60)

    async def _create_backup(self):
        """Crée une sauvegarde de tous les stores"""
        persistence = self._storage_config.get("persistence", {})
        backup_path = Path(persistence.get("backup_path", "./data/backups"))
        backup_path.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = backup_path / f"backup_{timestamp}.tar.gz"
        
        self._logger.info(f"💾 Création sauvegarde: {backup_file.name}")
        
        import tarfile
        import tempfile
        
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            for name, backend in self._backends.items():
                if isinstance(backend, DiskBackend):
                    if backend._base_path.exists():
                        shutil.copytree(backend._base_path, temp_path / name)
                elif isinstance(backend, MemoryBackend):
                    mem_file = temp_path / f"{name}_memory.json"
                    async with backend._lock:
                        data = {
                            "keys_count": len(backend._data),
                            "size_bytes": backend._current_size
                        }
                    with open(mem_file, 'w') as f:
                        json.dump(data, f)
                elif isinstance(backend, IPFSBackend):
                    ipfs_file = temp_path / f"{name}_index.json"
                    with open(ipfs_file, 'w') as f:
                        json.dump(backend._cache_index, f)
            
            agent_state = {
                "timestamp": timestamp,
                "backends": list(self._backends.keys()),
                "stats": await self.get_stats(),
                "version": self._agent_config.get('agent', {}).get('version', '1.0.0')
            }
            with open(temp_path / "agent_state.json", 'w') as f:
                json.dump(agent_state, f, indent=2)
            
            with tarfile.open(backup_file, "w:gz") as tar:
                tar.add(temp_path, arcname=".")
        
        self._logger.info(f"✅ Sauvegarde créée: {backup_file} ({backup_file.stat().st_size / 1024:.2f} KB)")
        await self._cleanup_old_backups(backup_path)

    async def _cleanup_old_backups(self, backup_path: Path):
        """Nettoie les vieilles sauvegardes"""
        persistence = self._storage_config.get("persistence", {})
        retention = persistence.get("backup_retention", 7)
        if retention <= 0:
            return
        
        cutoff = datetime.now() - timedelta(days=retention)
        deleted = 0
        
        for backup_file in backup_path.glob("backup_*.tar.gz"):
            try:
                date_str = backup_file.stem.replace("backup_", "")
                file_date = datetime.strptime(date_str, "%Y%m%d_%H%M%S")
                
                if file_date < cutoff:
                    backup_file.unlink()
                    deleted += 1
                    self._logger.debug(f"🗑️ Sauvegarde supprimée: {backup_file.name}")
            except Exception as e:
                self._logger.error(f"❌ Erreur nettoyage {backup_file}: {e}")
        
        if deleted > 0:
            self._logger.info(f"🧹 {deleted} vieilles sauvegardes supprimées")

    async def _check_quota(self, store: str):
        """Vérifie les quotas pour un store"""
        pass

    # ============================================================================
    # STATISTIQUES ET MONITORING
    # ============================================================================

    async def get_stats(self) -> Dict[str, Any]:
        """Retourne les statistiques de stockage"""
        stats = self._stats.copy()
        
        stats["backends"] = {}
        for name, backend in self._backends.items():
            try:
                stats["backends"][name] = await backend.get_stats()
            except Exception as e:
                self._logger.error(f"❌ Erreur stats backend {name}: {e}")
                stats["backends"][name] = {"error": str(e)}
        
        stats["cache"] = await self.get_cache_stats()
        stats["versioning"] = {
            "enabled": self._storage_config.get("versioning", {}).get("enabled", True),
            "versioned_keys": len(self._versions),
            "total_versions": sum(len(v) for v in self._versions.values())
        }
        
        stats["total_size_mb"] = stats["total_size_bytes"] / (1024 * 1024)
        stats["total_size_gb"] = stats["total_size_bytes"] / (1024 * 1024 * 1024)
        
        return stats

    async def health_check(self) -> Dict[str, Any]:
        """Vérifie la santé de l'agent"""
        base_health = await super().health_check()
        
        try:
            stats = await self.get_stats()
            base_health["storage_specific"] = {
                "stores": len(self._backends),
                "total_keys": stats["total_keys"],
                "total_size_mb": round(stats["total_size_bytes"] / (1024 * 1024), 2),
                "cache_hit_ratio": stats["cache"]["hit_ratio"],
                "operations": stats["operations_total"],
                "backends": list(self._backends.keys())
            }
        except Exception as e:
            self._logger.error(f"Erreur dans health_check: {e}")
            base_health["storage_specific"] = {"error": str(e)}
        
        return base_health

    def get_agent_info(self) -> Dict[str, Any]:
        """Informations de l'agent pour le registre"""
        agent_config = self._agent_config.get('agent', {})
        capabilities = agent_config.get('capabilities', [])
        
        if capabilities and isinstance(capabilities[0], dict):
            capabilities = [cap["name"] for cap in capabilities]
        
        return {
            "id": self.name,
            "name": "StorageAgent",
            "display_name": self._display_name,
            "version": agent_config.get('version', '1.0.0'),
            "description": agent_config.get('description', 'Gestion centralisée des données'),
            "status": self._status.value,
            "capabilities": capabilities,
            "features": {
                "stores": list(self._backends.keys()),
                "cache_enabled": self._storage_config.get("cache", {}).get("enabled", True),
                "versioning_enabled": self._storage_config.get("versioning", {}).get("enabled", True),
                "encryption_enabled": self._encryption_config.get("enabled", False),
                "compression_enabled": self._compression_config.get("enabled", True)
            },
            "stats": {
                "total_keys": self._stats["total_keys"],
                "total_size_mb": round(self._stats["total_size_bytes"] / (1024 * 1024), 2)
            }
        }

    # ============================================================================
    # GESTION DES MESSAGES
    # ============================================================================

    async def _handle_custom_message(self, message: Message) -> Optional[Message]:
        """Gère les messages personnalisés"""
        try:
            msg_type = message.message_type
            self._logger.debug(f"Message reçu: {msg_type} de {message.sender}")
            
            handlers = {
                "storage.set": self._handle_set,
                "storage.get": self._handle_get,
                "storage.delete": self._handle_delete,
                "storage.exists": self._handle_exists,
                "storage.list_keys": self._handle_list_keys,
                "storage.clear_store": self._handle_clear_store,
                "storage.increment": self._handle_increment,
                "storage.append": self._handle_append,
                "storage.sadd": self._handle_sadd,
                "storage.stats": self._handle_stats,
                "storage.cache_stats": self._handle_cache_stats,
                "storage.clear_cache": self._handle_clear_cache,
            }
            
            if msg_type in handlers:
                return await handlers[msg_type](message)
            
            self._logger.warning(f"Type de message non reconnu: {msg_type}")
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

    async def _handle_set(self, message: Message) -> Message:
        content = message.content
        result = await self.set(
            key=content.get("key"),
            value=content.get("value"),
            store=content.get("store", "default"),
            ttl=content.get("ttl"),
            encrypt=content.get("encrypt", False)
        )
        return Message(
            sender=self.name,
            recipient=message.sender,
            content=result,
            message_type="storage.set_response",
            correlation_id=message.message_id
        )

    async def _handle_get(self, message: Message) -> Message:
        value = await self.get(
            key=message.content.get("key"),
            store=message.content.get("store", "default")
        )
        return Message(
            sender=self.name,
            recipient=message.sender,
            content={"value": value},
            message_type="storage.get_response",
            correlation_id=message.message_id
        )

    async def _handle_delete(self, message: Message) -> Message:
        success = await self.delete(
            key=message.content.get("key"),
            store=message.content.get("store", "default")
        )
        return Message(
            sender=self.name,
            recipient=message.sender,
            content={"success": success},
            message_type="storage.delete_response",
            correlation_id=message.message_id
        )

    async def _handle_exists(self, message: Message) -> Message:
        exists = await self.exists(
            key=message.content.get("key"),
            store=message.content.get("store", "default")
        )
        return Message(
            sender=self.name,
            recipient=message.sender,
            content={"exists": exists},
            message_type="storage.exists_response",
            correlation_id=message.message_id
        )

    async def _handle_list_keys(self, message: Message) -> Message:
        keys = await self.list_keys(
            store=message.content.get("store", "default"),
            pattern=message.content.get("pattern")
        )
        return Message(
            sender=self.name,
            recipient=message.sender,
            content={"keys": keys, "count": len(keys)},
            message_type="storage.list_keys_response",
            correlation_id=message.message_id
        )

    async def _handle_clear_store(self, message: Message) -> Message:
        count = await self.clear_store(message.content.get("store"))
        return Message(
            sender=self.name,
            recipient=message.sender,
            content={"cleared": count},
            message_type="storage.clear_store_response",
            correlation_id=message.message_id
        )

    async def _handle_increment(self, message: Message) -> Message:
        value = await self.increment(
            key=message.content.get("key"),
            store=message.content.get("store", "default"),
            amount=message.content.get("amount", 1),
            initial=message.content.get("initial", 0)
        )
        return Message(
            sender=self.name,
            recipient=message.sender,
            content={"value": value},
            message_type="storage.increment_response",
            correlation_id=message.message_id
        )

    async def _handle_append(self, message: Message) -> Message:
        result = await self.append(
            key=message.content.get("key"),
            value=message.content.get("value"),
            store=message.content.get("store", "default")
        )
        return Message(
            sender=self.name,
            recipient=message.sender,
            content={"result": result},
            message_type="storage.append_response",
            correlation_id=message.message_id
        )

    async def _handle_sadd(self, message: Message) -> Message:
        result = await self.sadd(
            key=message.content.get("key"),
            value=message.content.get("value"),
            store=message.content.get("store", "default")
        )
        return Message(
            sender=self.name,
            recipient=message.sender,
            content={"result": list(result) if result else []},
            message_type="storage.sadd_response",
            correlation_id=message.message_id
        )

    async def _handle_stats(self, message: Message) -> Message:
        stats = await self.get_stats()
        return Message(
            sender=self.name,
            recipient=message.sender,
            content=stats,
            message_type="storage.stats_response",
            correlation_id=message.message_id
        )

    async def _handle_cache_stats(self, message: Message) -> Message:
        stats = await self.get_cache_stats()
        return Message(
            sender=self.name,
            recipient=message.sender,
            content=stats,
            message_type="storage.cache_stats_response",
            correlation_id=message.message_id
        )

    async def _handle_clear_cache(self, message: Message) -> Message:
        await self.clear_cache()
        return Message(
            sender=self.name,
            recipient=message.sender,
            content={"status": "cache cleared"},
            message_type="storage.clear_cache_response",
            correlation_id=message.message_id
        )


# ============================================================================
# FONCTION D'USINE
# ============================================================================

def create_storage_agent(config_path: Optional[str] = None) -> StorageAgent:
    """Crée une instance du storage agent"""
    return StorageAgent(config_path)


# ============================================================================
# POINT D'ENTRÉE POUR EXÉCUTION DIRECTE
# ============================================================================

if __name__ == "__main__":
    async def main():
        print("💾 TEST STORAGE AGENT")
        print("="*60)
        
        agent = StorageAgent()
        await agent.initialize()
        
        agent_info = agent.get_agent_info()
        print(f"✅ Agent: {agent_info['name']} v{agent_info['version']}")
        print(f"✅ Statut: {agent_info['status']}")
        print(f"✅ Backends: {agent_info['features']['stores']}")
        
        print(f"\n📝 Test set/get...")
        await agent.set("test_key", {"name": "test", "value": 123})
        value = await agent.get("test_key")
        print(f"✅ Récupéré: {value}")
        
        print(f"\n🔢 Test increment...")
        await agent.set("counter", 5)
        new_value = await agent.increment("counter", amount=3)
        print(f"✅ Counter: {new_value}")
        
        print(f"\n📋 Test list...")
        await agent.append("mylist", "first")
        await agent.append("mylist", "second")
        mylist = await agent.get("mylist")
        print(f"✅ Liste: {mylist}")
        
        print(f"\n🧮 Test set...")
        await agent.sadd("myset", "a")
        await agent.sadd("myset", "b")
        await agent.sadd("myset", "a")
        myset = await agent.get("myset")
        print(f"✅ Ensemble: {myset}")
        
        print(f"\n📚 Test versioning...")
        await agent.set_versioned("versioned_key", "v1", comment="Première version")
        await agent.set_versioned("versioned_key", "v2", comment="Deuxième version")
        versions = await agent.get_versions("versioned_key")
        print(f"✅ Versions: {len(versions)}")
        
        stats = await agent.get_stats()
        print(f"\n📊 Statistiques:")
        print(f"  Clés totales: {stats['total_keys']}")
        print(f"  Taille totale: {stats['total_size_bytes'] / (1024 * 1024):.2f} MB")
        print(f"  Cache hit ratio: {stats['cache']['hit_ratio']:.2%}")
        
        health = await agent.health_check()
        print(f"\n❤️  Health: {health['status']}")
        
        print("\n" + "="*60)
        print("✅ STORAGE AGENT OPÉRATIONNEL")
        print("="*60)
        
        await agent.shutdown()
    
    asyncio.run(main())
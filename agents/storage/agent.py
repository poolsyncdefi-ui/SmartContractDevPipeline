import logging

logger = logging.getLogger(__name__)

"""
Storage Agent - Gestion centralisée des données
Stockage clé-valeur, documents, fichiers, cache, IPFS, chiffrement
Version: 1.0.0
"""

import os
import sys
import json
import hashlib
import pickle
import shutil
import time
import zlib
import gzip
from pathlib import Path
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Any, Optional, Union, BinaryIO, Tuple, Set
from collections import OrderedDict, defaultdict
import asyncio
import threading
import traceback
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

# Import BaseAgent
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from agents.base_agent.base_agent import BaseAgent, AgentStatus, AgentStatus


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
    LRU = "lru"  # Least Recently Used
    LFU = "lfu"  # Least Frequently Used
    TTL = "ttl"  # Time To Live
    FIFO = "fifo"  # First In First Out


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
        """Récupère une valeur"""
        raise NotImplementedError
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Stocke une valeur"""
        raise NotImplementedError
    
    async def delete(self, key: str) -> bool:
        """Supprime une clé"""
        raise NotImplementedError
    
    async def exists(self, key: str) -> bool:
        """Vérifie si une clé existe"""
        raise NotImplementedError
    
    async def list_keys(self, pattern: Optional[str] = None) -> List[str]:
        """Liste les clés"""
        raise NotImplementedError
    
    async def clear(self) -> int:
        """Vide le backend"""
        raise NotImplementedError
    
    async def get_size(self) -> int:
        """Retourne la taille en bytes"""
        return self.stats["size_bytes"]
    
    async def get_stats(self) -> Dict[str, Any]:
        """Retourne les statistiques de stockage"""
        stats = self.stats.copy()
        
        # Statistiques par backend
        stats["backends"] = {}
        for name, backend in self._backends.items():
            backend_stats = await backend.get_stats()
            stats["backends"][name] = backend_stats
        
        # Cache
        stats["cache"] = await self.get_cache_stats()
        
        # Versioning
        stats["versioning"] = {
            "enabled": self._config["storage"]["versioning"]["enabled"],
            "versioned_keys": len(self._versions),
            "total_versions": sum(len(v) for v in self._versions.values())
        }
        
        # 🔥 AJOUTE CES LIGNES
        stats["total_size_mb"] = stats["total_size_bytes"] / (1024 * 1024)
        
        return stats

class MemoryBackend(StorageBackend):
    """Backend de stockage en mémoire"""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        super().__init__(name, config)
        self._data: Dict[str, Tuple[Any, Optional[float]]] = {}  # key -> (value, expiry)
        self._lock = asyncio.Lock()
        self._max_size = config.get("max_size_mb", 512) * 1024 * 1024
        self._current_size = 0
        self._access_times: Dict[str, float] = {}  # Pour LRU
        self._access_counts: Dict[str, int] = {}  # Pour LFU
    
    async def get(self, key: str) -> Optional[Any]:
        async with self._lock:
            self.stats["operations"] += 1
            self.stats["reads"] += 1
            
            if key not in self._data:
                return None
            
            value, expiry = self._data[key]
            
            # Vérifier l'expiration
            if expiry and time.time() > expiry:
                del self._data[key]
                self._current_size -= self._estimate_size(value)
                self.stats["size_bytes"] = self._current_size
                self.stats["keys_count"] = len(self._data)
                return None
            
            # Mettre à jour les métriques d'accès
            self._access_times[key] = time.time()
            self._access_counts[key] = self._access_counts.get(key, 0) + 1
            
            return value
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        async with self._lock:
            self.stats["operations"] += 1
            self.stats["writes"] += 1
            
            # Calculer la taille
            size = self._estimate_size(value)
            
            # Vérifier l'espace disponible
            if self._current_size + size > self._max_size:
                await self._evict(size)
            
            # Calculer l'expiration
            expiry = time.time() + ttl if ttl else None
            
            # Supprimer l'ancienne valeur si elle existe
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
            
            if key in self._access_times:
                del self._access_times[key]
            if key in self._access_counts:
                del self._access_counts[key]
            
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
        """Retourne les statistiques"""
        # Mettre à jour avant de retourner
        self.stats["size_bytes"] = self._current_size
        self.stats["keys_count"] = len(self._data)
        return self.stats.copy()
    
    def _estimate_size(self, value: Any) -> int:
        """Estime la taille d'une valeur en mémoire"""
        try:
            return len(pickle.dumps(value))
        except:
            return 1024  # Estimation par défaut
    
    async def _evict(self, needed_size: int):
        """Évince des entrées pour libérer de l'espace"""
        policy = self.config.get("eviction_policy", "lru")
        
        if policy == "lru":
            # Trier par accès le plus ancien
            items = sorted(self._access_times.items(), key=lambda x: x[1])
        elif policy == "lfu":
            # Trier par accès le moins fréquent
            items = sorted(self._access_counts.items(), key=lambda x: x[1])
        else:  # fifo
            # Trier par ordre d'insertion (basé sur les timestamps)
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
        """Charge l'index des fichiers"""
        if self._index_path.exists():
            try:
                with open(self._index_path, 'r') as f:
                    self._index = json.load(f)
            except:
                self._index = {}
    
    def _save_index(self):
        """Sauvegarde l'index"""
        try:
            with open(self._index_path, 'w') as f:
                json.dump(self._index, f, indent=2)
        except Exception as e:
            print(f"Erreur sauvegarde index: {e}")
    
    def _get_key_path(self, key: str) -> Path:
        """Retourne le chemin d'un fichier pour une clé"""
        # Utiliser un hash pour éviter les problèmes de nom de fichier
        key_hash = hashlib.sha256(key.encode()).hexdigest()
        return self._base_path / key_hash[:2] / key_hash[2:4] / key_hash
    
    async def get(self, key: str) -> Optional[Any]:
        async with self._lock:
            self.stats["operations"] += 1
            self.stats["reads"] += 1
            
            if key not in self._index:
                return None
            
            metadata = self._index[key]
            
            # Vérifier l'expiration
            if metadata.get("expiry") and time.time() > metadata["expiry"]:
                await self.delete(key)
                return None
            
            key_path = self._get_key_path(key)
            if not key_path.exists():
                return None
            
            try:
                with open(key_path, 'rb') as f:
                    data = f.read()
                
                # Décompresser si nécessaire
                if metadata.get("compressed"):
                    data = zlib.decompress(data)
                
                # Déchiffrer si nécessaire
                # TODO: Implémenter déchiffrement
                
                # Désérialiser selon le type
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
                print(f"Erreur lecture {key}: {e}")
                return None
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        async with self._lock:
            self.stats["operations"] += 1
            self.stats["writes"] += 1
            
            # Déterminer le type de données
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
            
            # Compresser si nécessaire
            compressed = False
            if self.config.get("compression", False) and len(data) > 1024:
                data = zlib.compress(data, level=6)
                compressed = True
            
            # Créer le répertoire
            key_path = self._get_key_path(key)
            key_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Écrire le fichier
            with open(key_path, 'wb') as f:
                f.write(data)
            
            # Mettre à jour l'index
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
            
            # Mettre à jour les stats
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
        """Retourne les statistiques du backend"""
        # Mettre à jour les stats avant de les retourner
        self.stats["size_bytes"] = sum(m["size"] for m in self._index.values())
        self.stats["keys_count"] = len(self._index)
        return self.stats.copy()  # ✅ Simplement retourner ses propres stats

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
        self._cache_index: Dict[str, str] = {}  # key -> ipfs_hash
        self._load_cache_index()
    
    def _load_cache_index(self):
        """Charge l'index du cache local"""
        index_file = self._cache_dir / "_index.json"
        if index_file.exists():
            try:
                with open(index_file, 'r') as f:
                    self._cache_index = json.load(f)
            except:
                self._cache_index = {}
    
    def _save_cache_index(self):
        """Sauvegarde l'index du cache local"""
        if not self._local_cache:
            return
        index_file = self._cache_dir / "_index.json"
        try:
            with open(index_file, 'w') as f:
                json.dump(self._cache_index, f, indent=2)
        except Exception as e:
            print(f"Erreur sauvegarde index IPFS: {e}")
    
    async def _ensure_session(self):
        """Assure qu'une session HTTP existe"""
        if not self._session:
            import aiohttp
            self._session = aiohttp.ClientSession()
    
    async def get(self, key: str) -> Optional[Any]:
        """Récupère une valeur depuis IPFS"""
        self.stats["operations"] += 1
        self.stats["reads"] += 1
        
        # Vérifier le cache local d'abord
        if self._local_cache and key in self._cache_index:
            ipfs_hash = self._cache_index[key]
            cache_file = self._cache_dir / ipfs_hash
            
            if cache_file.exists():
                try:
                    with open(cache_file, 'rb') as f:
                        data = f.read()
                    self.stats["hits"] += 1
                    return pickle.loads(data)
                except:
                    pass
        
        self.stats["misses"] += 1
        
        # TODO: Implémenter la récupération depuis IPFS
        # Pour l'instant, retourner None
        return None
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Stocke une valeur sur IPFS"""
        self.stats["operations"] += 1
        self.stats["writes"] += 1
        
        # Sérialiser la valeur
        data = pickle.dumps(value)
        
        # TODO: Implémenter l'upload vers IPFS
        # Simulation : générer un hash fictif
        import hashlib
        ipfs_hash = hashlib.sha256(data).hexdigest()
        
        # Mettre en cache local si activé
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
        """Supprime une valeur d'IPFS"""
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
        """Vérifie si une clé existe"""
        if self._local_cache:
            return key in self._cache_index
        return False
    
    async def list_keys(self, pattern: Optional[str] = None) -> List[str]:
        """Liste les clés"""
        keys = list(self._cache_index.keys())
        if pattern:
            import fnmatch
            keys = [k for k in keys if fnmatch.fnmatch(k, pattern)]
        return keys
    
    async def clear(self) -> int:
        """Vide le cache local"""
        count = len(self._cache_index)
        
        # Supprimer les fichiers
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
        """Retourne les statistiques"""
        self.stats["keys_count"] = len(self._cache_index)
        return self.stats.copy()

class StorageAgent(BaseAgent):
    """
    Agent de stockage centralisé
    Gère la persistance, le cache, et le versioning des données
    """
    
    def __init__(self, config_path: str = ""):
        """Initialise l'agent de stockage"""
        super().__init__(config_path)
        
        self._logger.info("💾 Storage Agent créé")
        
        # Charger configuration
        self._load_configuration()
        
        # Backends de stockage
        self._backends: Dict[str, StorageBackend] = {}
        
        # Cache LRU global
        self._cache: OrderedDict = OrderedDict()
        self._cache_stats = {
            "hits": 0,
            "misses": 0,
            "size_bytes": 0,
            "keys": 0
        }
        
        # Versioning
        self._versions: Dict[str, List[str]] = defaultdict(list)
        
        # Statistiques
        self._stats = {
            "stores": 0,
            "total_keys": 0,
            "total_size_bytes": 0,
            "operations_total": 0,
            "operations_by_type": defaultdict(int)
        }
        
        # Composants
        self._components = {}
        
        # Tâches de fond
        self._cleanup_task = None
        self._backup_task = None
        
        # Initialiser les backends
        self._init_backends()
    
    def _load_configuration(self):
        """Charge la configuration depuis le fichier YAML"""
        try:
            config_path = os.path.join(os.path.dirname(__file__), "config.yaml")
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    self._config = yaml.safe_load(f)
                self._logger.info(f"✅ Configuration chargée: storage v{self._config['agent']['version']}")
            else:
                self._logger.warning("⚠️ Fichier config.yaml non trouvé")
                self._config = self._get_default_config()
        except Exception as e:
            self._logger.error(f"❌ Erreur chargement config: {e}")
            self._config = self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Configuration par défaut"""
        return {
            "agent": {
                "name": "storage",
                "display_name": "💾 Storage Agent",
                "version": "1.0.0"
            },
            "storage": {
                "stores": {
                    "default": {
                        "type": "disk",
                        "path": "./data/storage/default"
                    },
                    "memory": {
                        "type": "memory",
                        "max_size_mb": 512
                    },
                    "cache": {
                        "type": "memory",
                        "max_size_mb": 256,
                        "ttl_default": 300,
                        "eviction_policy": "lru"
                    }
                },
                "cache": {
                    "enabled": True,
                    "type": "lru",
                    "max_size_mb": 1024
                },
                "versioning": {
                    "enabled": True,
                    "max_versions_per_key": 10
                }
            },
            "compression": {
                "enabled": True,
                "algorithm": "zstd",
                "min_size_bytes": 1024
            }
        }
    
    def _init_backends(self):
        """Initialise les backends de stockage"""
        stores_config = self._config["storage"]["stores"]
        
        for name, config in stores_config.items():
            backend_type = config.get("type", "memory")
            
            if backend_type == "memory":
                backend = MemoryBackend(name, config)
            elif backend_type == "disk":
                backend = DiskBackend(name, config)
            elif backend_type == "ipfs":
                backend = IPFSBackend(name, config)
            else:
                self._logger.warning(f"⚠️ Type de backend inconnu: {backend_type}")
                continue
            
            self._backends[name] = backend
            self._logger.info(f"✅ Backend '{name}' initialisé ({backend_type})")
        
        self._stats["stores"] = len(self._backends)
    
    async def initialize(self) -> bool:
        """Initialisation asynchrone"""
        try:
            self._set_status(AgentStatus.INITIALIZING)
            self._logger.info("💾 Initialisation du Storage Agent...")
            
            # Initialiser les composants
            await self._initialize_components()
            
            # Démarrer les tâches de fond
            if self._config["storage"]["persistence"]["auto_backup"]:
                self._backup_task = asyncio.create_task(self._backup_worker())
            
            self._set_status(AgentStatus.READY)
            self._logger.info(f"✅ Storage Agent prêt - {len(self._backends)} backends actifs")
            return True
            
        except Exception as e:
            self._logger.error(f"❌ Erreur initialisation: {e}")
            self._logger.error(traceback.format_exc())
            self._set_status(AgentStatus.ERROR)
            return False
    
    async def _initialize_components(self):
        """Initialise les composants - requis par BaseAgent"""
        self._logger.info("Initialisation des composants...")
        
        self._components = {
            "memory_backend": "memory" in self._backends,
            "disk_backend": any(isinstance(b, DiskBackend) for b in self._backends.values()),
            "ipfs_backend": any(isinstance(b, IPFSBackend) for b in self._backends.values()),
            "cache": self._config["storage"]["cache"]["enabled"],
            "versioning": self._config["storage"]["versioning"]["enabled"]
        }
        
        self._logger.info(f"✅ Composants: {list(self._components.keys())}")
        return self._components
    
    # =================================================================
    # API PUBLIQUE - OPÉRATIONS DE BASE
    # =================================================================
    
    async def set(self, key: str, value: Any, 
                  store: str = "default",
                  ttl: Optional[int] = None,
                  encrypt: bool = False,
                  compress: Optional[bool] = None) -> Dict[str, Any]:
        """
        Stocke une valeur
        
        Args:
            key: Clé unique
            value: Valeur à stocker
            store: Nom du store
            ttl: Durée de vie en secondes
            encrypt: Chiffrer la donnée
            compress: Compresser la donnée (None = auto)
            
        Returns:
            Métadonnées du stockage
        """
        self._logger.debug(f"💾 set: {key} -> {store}")
        
        # Vérifier le store
        if store not in self._backends:
            raise ValueError(f"Store '{store}' non trouvé")
        
        backend = self._backends[store]
        
        # Traitement pré-stockage
        processed_value = value
        
        # Compression
        should_compress = compress
        if should_compress is None:
            should_compress = self._config["compression"]["enabled"]
        
        compressed = False
        if should_compress:
            # Le backend gère la compression
            pass
        
        # Chiffrement
        if encrypt and self._config["encryption"]["enabled"]:
            # TODO: Implémenter chiffrement
            pass
        
        # Stocker
        start_time = time.time()
        success = await backend.set(key, processed_value, ttl)
        duration = (time.time() - start_time) * 1000
        
        # Mettre à jour les stats
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
            "compressed": compressed,
            "duration_ms": round(duration, 2)
        }
    
    async def get(self, key: str, store: str = "default") -> Optional[Any]:
        """
        Récupère une valeur
        
        Args:
            key: Clé à récupérer
            store: Nom du store
            
        Returns:
            Valeur stockée ou None
        """
        self._logger.debug(f"📖 get: {key} <- {store}")
        
        # Vérifier le cache d'abord
        cache_key = f"{store}:{key}"
        if cache_key in self._cache:
            self._cache.move_to_end(cache_key)
            self._cache_stats["hits"] += 1
            self._logger.debug(f"🎯 Cache HIT: {key}")
            return self._cache[cache_key]
        
        self._cache_stats["misses"] += 1
        
        # Vérifier le store
        if store not in self._backends:
            raise ValueError(f"Store '{store}' non trouvé")
        
        backend = self._backends[store]
        
        # Récupérer
        start_time = time.time()
        value = await backend.get(key)
        duration = (time.time() - start_time) * 1000
        
        # Mettre à jour les stats
        self._stats["operations_total"] += 1
        self._stats["operations_by_type"]["get"] += 1
        
        # Mettre en cache si trouvé
        if value is not None and self._config["storage"]["cache"]["enabled"]:
            await self._add_to_cache(cache_key, value)
        
        self._logger.debug(f"📖 get: {key} {'✅' if value else '❌'} ({duration:.2f}ms)")
        
        return value
    
    async def delete(self, key: str, store: str = "default") -> bool:
        """
        Supprime une clé
        
        Args:
            key: Clé à supprimer
            store: Nom du store
            
        Returns:
            True si supprimé, False sinon
        """
        self._logger.debug(f"🗑️ delete: {key}")
        
        if store not in self._backends:
            raise ValueError(f"Store '{store}' non trouvé")
        
        backend = self._backends[store]
        
        start_time = time.time()
        result = await backend.delete(key)
        duration = (time.time() - start_time) * 1000
        
        # Supprimer du cache
        cache_key = f"{store}:{key}"
        if cache_key in self._cache:
            del self._cache[cache_key]
        
        # Mettre à jour les stats
        self._stats["operations_total"] += 1
        self._stats["operations_by_type"]["delete"] += 1
        
        if result:
            self._stats["total_keys"] = sum(b.stats["keys_count"] for b in self._backends.values())
            self._stats["total_size_bytes"] = sum(b.stats["size_bytes"] for b in self._backends.values())
        
        self._logger.debug(f"🗑️ delete: {key} {'✅' if result else '❌'} ({duration:.2f}ms)")
        
        return result
    
    async def exists(self, key: str, store: str = "default") -> bool:
        """
        Vérifie si une clé existe
        
        Args:
            key: Clé à vérifier
            store: Nom du store
            
        Returns:
            True si existe
        """
        if store not in self._backends:
            raise ValueError(f"Store '{store}' non trouvé")
        
        backend = self._backends[store]
        return await backend.exists(key)
    
    async def list_keys(self, store: str = "default", 
                        pattern: Optional[str] = None) -> List[str]:
        """
        Liste les clés d'un store
        
        Args:
            store: Nom du store
            pattern: Pattern glob (ex: "user:*")
            
        Returns:
            Liste des clés
        """
        if store not in self._backends:
            raise ValueError(f"Store '{store}' non trouvé")
        
        backend = self._backends[store]
        return await backend.list_keys(pattern)
    
    async def clear_store(self, store: str) -> int:
        """
        Vide complètement un store
        
        Args:
            store: Nom du store
            
        Returns:
            Nombre d'éléments supprimés
        """
        if store not in self._backends:
            raise ValueError(f"Store '{store}' non trouvé")
        
        backend = self._backends[store]
        count = await backend.clear()
        
        # Vider le cache pour ce store
        keys_to_remove = [k for k in self._cache if k.startswith(f"{store}:")]
        for k in keys_to_remove:
            del self._cache[k]
        
        self._logger.info(f"🧹 Store '{store}' vidé ({count} éléments)")
        
        return count
    
    # =================================================================
    # CACHE
    # =================================================================
    
    async def _add_to_cache(self, key: str, value: Any):
        """Ajoute une entrée au cache LRU"""
        cache_config = self._config["storage"]["cache"]
        max_size = cache_config.get("max_size_mb", 1024) * 1024 * 1024
        policy = cache_config.get("type", "lru")
        
        # Estimer la taille
        try:
            size = len(pickle.dumps(value))
        except:
            size = 1024
        
        # Vérifier l'espace
        while self._cache_stats["size_bytes"] + size > max_size:
            if not self._cache:
                break
            # Évincer la plus ancienne
            oldest_key, oldest_value = self._cache.popitem(last=False)
            try:
                self._cache_stats["size_bytes"] -= len(pickle.dumps(oldest_value))
            except:
                self._cache_stats["size_bytes"] -= 1024
            self._cache_stats["keys"] -= 1
        
        # Ajouter
        self._cache[key] = value
        self._cache_stats["size_bytes"] += size
        self._cache_stats["keys"] += 1
    
    async def clear_cache(self):
        """Vide le cache"""
        self._cache.clear()
        self._cache_stats = {
            "hits": 0,
            "misses": 0,
            "size_bytes": 0,
            "keys": 0
        }
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
    
    # =================================================================
    # VERSIONING
    # =================================================================
    
    async def set_versioned(self, key: str, value: Any,
                           store: str = "default",
                           comment: str = "") -> Dict[str, Any]:
        """
        Stocke une version d'une clé
        
        Args:
            key: Clé
            value: Valeur
            store: Store
            comment: Commentaire de version
            
        Returns:
            Métadonnées incluant la version
        """
        version = datetime.now().strftime("%Y%m%d_%H%M%S")
        versioned_key = f"{key}__v{version}"
        
        # Stocker la version
        result = await self.set(versioned_key, value, store, ttl=None)
        
        # Ajouter à l'index des versions
        self._versions[key].append(versioned_key)
        
        # Limiter le nombre de versions
        max_versions = self._config["storage"]["versioning"]["max_versions_per_key"]
        while len(self._versions[key]) > max_versions:
            oldest = self._versions[key].pop(0)
            await self.delete(oldest, store)
        
        result["version"] = version
        result["version_comment"] = comment
        
        return result
    
    async def get_versions(self, key: str, store: str = "default") -> List[Dict[str, Any]]:
        """
        Liste les versions d'une clé
        
        Args:
            key: Clé
            store: Store
            
        Returns:
            Liste des métadonnées des versions
        """
        versions = []
        for version_key in self._versions.get(key, []):
            exists = await self.exists(version_key, store)
            if exists:
                # Extraire la version du nom
                version = version_key.split("__v")[-1]
                versions.append({
                    "key": version_key,
                    "version": version,
                    "exists": True
                })
        return versions
    
    async def get_version(self, key: str, version: str,
                         store: str = "default") -> Optional[Any]:
        """
        Récupère une version spécifique
        
        Args:
            key: Clé
            version: Version (format: YYYYMMDD_HHMMSS)
            store: Store
            
        Returns:
            Valeur de cette version
        """
        versioned_key = f"{key}__v{version}"
        return await self.get(versioned_key, store)
    
    # =================================================================
    # OPÉRATIONS SPÉCIALISÉES
    # =================================================================
    
    async def increment(self, key: str, store: str = "default",
                       amount: int = 1, initial: int = 0) -> int:
        """
        Incrémente une valeur numérique
        
        Args:
            key: Clé
            store: Store
            amount: Montant de l'incrément
            initial: Valeur initiale si la clé n'existe pas
            
        Returns:
            Nouvelle valeur
        """
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
        """
        Ajoute une valeur à une liste
        
        Args:
            key: Clé
            value: Valeur à ajouter
            store: Store
            
        Returns:
            Liste mise à jour
        """
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
        """
        Ajoute une valeur à un ensemble
        
        Args:
            key: Clé
            value: Valeur à ajouter
            store: Store
            
        Returns:
            Ensemble mis à jour
        """
        current = await self.get(key, store)
        
        if current is None:
            new_set = {value}
        else:
            if not isinstance(current, set):
                # Convertir en set
                new_set = set(current)
            else:
                new_set = current
            new_set.add(value)
        
        await self.set(key, new_set, store)
        return new_set
    
    # =================================================================
    # UTILITAIRES
    # =================================================================
    
    async def _backup_worker(self):
        """Sauvegarde périodique des données"""
        if not self._config["storage"]["persistence"]["auto_backup"]:
            return
        
        interval = self._config["storage"]["persistence"]["backup_interval"]
        self._logger.info(f"💾 Travailleur de backup démarré (intervalle: {interval}s)")
        
        while self._status == AgentStatus.READY:
            try:
                await asyncio.sleep(interval)
                await self._create_backup()
            except Exception as e:
                self._logger.error(f"❌ Erreur sauvegarde: {e}")
                await asyncio.sleep(60)

    async def _create_backup(self):
        """Crée une sauvegarde de tous les stores"""
        backup_path = Path(self._config["storage"]["persistence"]["backup_path"])
        backup_path.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = backup_path / f"backup_{timestamp}.tar.gz"
        
        self._logger.info(f"💾 Création sauvegarde: {backup_file.name}")
        
        import tarfile
        import tempfile
        
        # Créer un répertoire temporaire pour la sauvegarde
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Sauvegarder chaque backend
            for name, backend in self._backends.items():
                if isinstance(backend, DiskBackend):
                    # Copier les fichiers du backend disque
                    backend_path = backend._base_path
                    if backend_path.exists():
                        dest_path = temp_path / name
                        shutil.copytree(backend_path, dest_path)
                
                elif isinstance(backend, MemoryBackend):
                    # Sauvegarder les données mémoire
                    mem_file = temp_path / f"{name}_memory.json"
                    data = {}
                    async with backend._lock:
                        # Ne pas essayer de sérialiser les données directement
                        # Juste enregistrer les métadonnées
                        data = {
                            "keys_count": len(backend._data),
                            "size_bytes": backend._current_size
                        }
                    with open(mem_file, 'w') as f:
                        json.dump(data, f)
                
                elif isinstance(backend, IPFSBackend):
                    # Sauvegarder l'index IPFS
                    ipfs_file = temp_path / f"{name}_index.json"
                    with open(ipfs_file, 'w') as f:
                        json.dump(backend._cache_index, f)
            
            # Sauvegarder l'état de l'agent
            agent_state = {
                "timestamp": timestamp,
                "backends": list(self._backends.keys()),
                "stats": await self.get_stats(),
                "version": self._config["agent"]["version"]
            }
            state_file = temp_path / "agent_state.json"
            with open(state_file, 'w') as f:
                json.dump(agent_state, f, indent=2)
            
            # Créer l'archive tar.gz
            with tarfile.open(backup_file, "w:gz") as tar:
                tar.add(temp_path, arcname=".")
        
        self._logger.info(f"✅ Sauvegarde créée: {backup_file} ({backup_file.stat().st_size / 1024:.2f} KB)")
        
        # Nettoyer les vieilles sauvegardes
        await self._cleanup_old_backups(backup_path)

    async def _cleanup_old_backups(self, backup_path: Path):
        """Nettoie les vieilles sauvegardes"""
        retention = self._config["storage"]["persistence"]["backup_retention"]
        if retention <= 0:
            return
        
        cutoff = datetime.now() - timedelta(days=retention)
        deleted = 0
        
        for backup_file in backup_path.glob("backup_*.tar.gz"):
            try:
                # Extraire la date du nom du fichier
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
    
    # =================================================================
    # STATISTIQUES ET MONITORING
    # =================================================================
    
    async def get_stats(self) -> Dict[str, Any]:
        """Retourne les statistiques de stockage"""
        stats = self._stats.copy()
        
        # Statistiques par backend
        stats["backends"] = {}
        for name, backend in self._backends.items():
            try:
                backend_stats = await backend.get_stats()
                stats["backends"][name] = backend_stats
            except Exception as e:
                self._logger.error(f"❌ Erreur récupération stats backend {name}: {e}")
                stats["backends"][name] = {"error": str(e)}
        
        # Cache
        stats["cache"] = await self.get_cache_stats()
        
        # Versioning
        stats["versioning"] = {
            "enabled": self._config["storage"]["versioning"]["enabled"],
            "versioned_keys": len(self._versions),
            "total_versions": sum(len(v) for v in self._versions.values())
        }
        
        # Calculs supplémentaires
        stats["total_size_mb"] = stats["total_size_bytes"] / (1024 * 1024)
        stats["total_size_gb"] = stats["total_size_bytes"] / (1024 * 1024 * 1024)
        
        return stats
    
    async def health_check(self) -> Dict[str, Any]:
        """Vérifie la santé de l'agent"""
        stats = await self.get_stats()
        
        return {
            "agent": self._name,
            "status": self._status.value,
            "ready": self._status == AgentStatus.READY,
            "stores": len(self._backends),
            "total_keys": stats["total_keys"],
            "total_size_mb": round(stats["total_size_bytes"] / (1024 * 1024), 2),
            "cache_hit_ratio": stats["cache"]["hit_ratio"],
            "operations": stats["operations_total"],
            "components": list(self._components.keys()),
            "uptime": self.uptime.total_seconds()
        }
    
    def get_agent_info(self) -> Dict[str, Any]:
        """Informations de l'agent"""
        return {
            "id": self._name,
            "name": self._config["agent"]["display_name"],
            "version": self._config["agent"]["version"],
            "description": self._config["agent"]["description"],
            "status": self._status.value,
            "capabilities": [cap["name"] for cap in self._config["agent"]["capabilities"]],
            "stores": list(self._backends.keys()),
            "cache_enabled": self._config["storage"]["cache"]["enabled"],
            "versioning_enabled": self._config["storage"]["versioning"]["enabled"]
        }
    
    async def _handle_custom_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Gestion des messages personnalisés"""
        msg_type = message.get("type", "")
        
        if msg_type == "set":
            return await self.set(
                message["key"],
                message["value"],
                message.get("store", "default"),
                message.get("ttl"),
                message.get("encrypt", False)
            )
        
        elif msg_type == "get":
            value = await self.get(
                message["key"],
                message.get("store", "default")
            )
            return {"value": value}
        
        elif msg_type == "delete":
            success = await self.delete(
                message["key"],
                message.get("store", "default")
            )
            return {"success": success}
        
        elif msg_type == "exists":
            exists = await self.exists(
                message["key"],
                message.get("store", "default")
            )
            return {"exists": exists}
        
        elif msg_type == "list_keys":
            keys = await self.list_keys(
                message.get("store", "default"),
                message.get("pattern")
            )
            return {"keys": keys}
        
        elif msg_type == "clear_store":
            count = await self.clear_store(message["store"])
            return {"cleared": count}
        
        elif msg_type == "increment":
            value = await self.increment(
                message["key"],
                message.get("store", "default"),
                message.get("amount", 1),
                message.get("initial", 0)
            )
            return {"value": value}
        
        elif msg_type == "stats":
            return await self.get_stats()
        
        elif msg_type == "cache_stats":
            return await self.get_cache_stats()
        
        elif msg_type == "clear_cache":
            await self.clear_cache()
            return {"status": "cache cleared"}
        
        return {"status": "received", "type": msg_type}


# ========================================================================
# FONCTIONS D'USINE
# ========================================================================

def create_storage_agent(config_path: str = "") -> 'StorageAgent':
    """Crée une instance du storage agent"""
    return StorageAgent(config_path)


# ========================================================================
# POINT D'ENTRÉE POUR EXÉCUTION DIRECTE
# ========================================================================

if __name__ == "__main__":
    import asyncio
    import yaml
    
    async def main():
        print("💾 TEST STORAGE AGENT")
        print("="*60)
        
        agent = StorageAgent()
        await agent.initialize()
        
        print(f"✅ Agent: {agent._config['agent']['display_name']} v{agent._config['agent']['version']}")
        print(f"✅ Statut: {agent._status.value}")
        print(f"✅ Backends: {list(agent._backends.keys())}")
        
        # Test set/get
        print(f"\n📝 Test set/get...")
        await agent.set("test_key", {"name": "test", "value": 123})
        value = await agent.get("test_key")
        print(f"✅ Récupéré: {value}")
        
        # Test increment
        print(f"\n🔢 Test increment...")
        await agent.set("counter", 5)
        new_value = await agent.increment("counter", amount=3)
        print(f"✅ Counter: {new_value}")
        
        # Test list
        print(f"\n📋 Test list...")
        await agent.append("mylist", "first")
        await agent.append("mylist", "second")
        mylist = await agent.get("mylist")
        print(f"✅ Liste: {mylist}")
        
        # Test set
        print(f"\n🧮 Test set...")
        await agent.sadd("myset", "a")
        await agent.sadd("myset", "b")
        await agent.sadd("myset", "a")  # Déjà présent
        myset = await agent.get("myset")
        print(f"✅ Ensemble: {myset}")
        
        # Test versioning
        print(f"\n📚 Test versioning...")
        await agent.set_versioned("versioned_key", "v1", comment="Première version")
        await agent.set_versioned("versioned_key", "v2", comment="Deuxième version")
        versions = await agent.get_versions("versioned_key")
        print(f"✅ Versions: {len(versions)}")
        
        # Statistiques
        stats = await agent.get_stats()
        print(f"\n📊 Statistiques:")
        print(f"  Clés totales: {stats['total_keys']}")
        print(f"  Taille totale: {stats['total_size_bytes'] / (1024 * 1024):.2f} MB")
        print(f"  Cache hit ratio: {stats['cache']['hit_ratio']:.2%}")
        
        print("\n" + "="*60)
        print("✅ STORAGE AGENT OPÉRATIONNEL")
        print("="*60)
    
    asyncio.run(main())
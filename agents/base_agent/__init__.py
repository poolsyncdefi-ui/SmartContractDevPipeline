"""
Package agents.base_agent - Version complète 4.0.0
Système d'import avancé avec compatibilité totale
"""

import os
import sys
import importlib.util
import importlib.machinery
import logging
import traceback
import inspect
import json
import yaml
import asyncio
from datetime import datetime
import hashlib
import uuid
from typing import Dict, Any, List, Optional, Type, Union, Callable
from dataclasses import dataclass, field, asdict
from enum import Enum
import threading

# =====================================================================
# CONFIGURATION DU SYSTÈME
# =====================================================================

class SystemConfiguration:
    """Configuration complète du système"""
    
    def __init__(self):
        # Niveaux de debug
        self.DEBUG_IMPORTS = os.environ.get('AGENTS_DEBUG_IMPORTS', 'false').lower() == 'true'
        self.DEBUG_CIRCULAR = os.environ.get('AGENTS_DEBUG_CIRCULAR', 'false').lower() == 'true'
        self.DEBUG_CACHE = os.environ.get('AGENTS_DEBUG_CACHE', 'false').lower() == 'true'
        self.VERBOSE_INIT = os.environ.get('AGENTS_VERBOSE_INIT', 'true').lower() == 'true'
        
        # Paramètres système
        self.MAX_IMPORT_DEPTH = 15
        self.ENABLE_PROXY_SYSTEM = True
        self.ENABLE_CACHE_SYSTEM = True
        self.ENABLE_FALLBACK_SYSTEM = True
        self.AUTO_CONFIGURE_ON_LOAD = True
        self.PREVENT_CIRCULAR_IMPORTS = True
        
        # Chemins
        self.BASE_AGENT_FILE = os.path.join(os.path.dirname(__file__), 'base_agent.py')
        self.CONFIG_FILE = os.path.join(os.path.dirname(__file__), 'config.yaml')
        self.LOG_DIR = os.path.join(os.path.dirname(__file__), 'logs')
        
        # Performance
        self.CACHE_MAX_SIZE = 100
        self.CACHE_TTL_SECONDS = 300
        
        # Sécurité
        self.VALIDATE_IMPORTS = True
        self.SANITIZE_MODULE_NAMES = True
        
    def to_dict(self) -> Dict[str, Any]:
        """Convertit en dictionnaire"""
        return {
            'debug_imports': self.DEBUG_IMPORTS,
            'debug_circular': self.DEBUG_CIRCULAR,
            'debug_cache': self.DEBUG_CACHE,
            'verbose_init': self.VERBOSE_INIT,
            'max_import_depth': self.MAX_IMPORT_DEPTH,
            'enable_proxy': self.ENABLE_PROXY_SYSTEM,
            'enable_cache': self.ENABLE_CACHE_SYSTEM,
            'enable_fallback': self.ENABLE_FALLBACK_SYSTEM,
            'auto_configure': self.AUTO_CONFIGURE_ON_LOAD,
            'prevent_circular': self.PREVENT_CIRCULAR_IMPORTS,
            'base_agent_file': self.BASE_AGENT_FILE,
            'config_file': self.CONFIG_FILE,
            'cache_max_size': self.CACHE_MAX_SIZE,
            'cache_ttl': self.CACHE_TTL_SECONDS,
            'validate_imports': self.VALIDATE_IMPORTS,
            'sanitize_names': self.SANITIZE_MODULE_NAMES,
            'timestamp': datetime.now().isoformat()
        }

# Initialiser la configuration
config = SystemConfiguration()

# =====================================================================
# SYSTÈME DE LOGGING AVANCÉ
# =====================================================================

class AdvancedLogger:
    """Système de logging avancé avec coloration et rotation"""
    
    # Codes de couleur ANSI
    COLOR_CODES = {
        'BLACK': '\033[30m',
        'RED': '\033[31m',
        'GREEN': '\033[32m',
        'YELLOW': '\033[33m',
        'BLUE': '\033[34m',
        'MAGENTA': '\033[35m',
        'CYAN': '\033[36m',
        'WHITE': '\033[37m',
        'BRIGHT_BLACK': '\033[90m',
        'BRIGHT_RED': '\033[91m',
        'BRIGHT_GREEN': '\033[92m',
        'BRIGHT_YELLOW': '\033[93m',
        'BRIGHT_BLUE': '\033[94m',
        'BRIGHT_MAGENTA': '\033[95m',
        'BRIGHT_CYAN': '\033[96m',
        'BRIGHT_WHITE': '\033[97m',
        'RESET': '\033[0m',
        'BOLD': '\033[1m',
        'UNDERLINE': '\033[4m'
    }
    
    # Mapping niveaux -> couleurs
    LEVEL_COLORS = {
        'DEBUG': 'BRIGHT_BLACK',
        'INFO': 'BRIGHT_GREEN',
        'WARNING': 'BRIGHT_YELLOW',
        'ERROR': 'BRIGHT_RED',
        'CRITICAL': 'BRIGHT_MAGENTA'
    }
    
    def __init__(self, name: str):
        self.name = name
        self._lock = threading.RLock()
        self._log_file = None
        self._ensure_log_dir()
        
    def _ensure_log_dir(self):
        """Crée le dossier de logs si nécessaire"""
        try:
            if not os.path.exists(config.LOG_DIR):
                os.makedirs(config.LOG_DIR, exist_ok=True)
        except Exception:
            pass
    
    def _get_color(self, level: str) -> str:
        """Retourne le code couleur pour un niveau"""
        color_name = self.LEVEL_COLORS.get(level, 'WHITE')
        return self.COLOR_CODES.get(color_name, '')
    
    def _format_message(self, level: str, message: str, **kwargs) -> str:
        """Formate un message de log"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
        color = self._get_color(level)
        reset = self.COLOR_CODES['RESET']
        
        # Format de base
        formatted = f"{color}[{timestamp}] [{level:8}] {self.name}: {message}{reset}"
        
        # Ajouter les kwargs si présents
        if kwargs:
            try:
                kwargs_str = json.dumps(kwargs, indent=2, default=str)
                formatted += f"\n{color}  Details:{reset}\n{kwargs_str}"
            except:
                formatted += f" {kwargs}"
        
        return formatted
    
    def log(self, level: str, message: str, **kwargs):
        """Log un message avec niveau"""
        with self._lock:
            # Afficher à l'écran selon la configuration
            should_display = (
                config.VERBOSE_INIT or
                level in ['ERROR', 'CRITICAL', 'WARNING'] or
                (config.DEBUG_IMPORTS and level == 'DEBUG')
            )
            
            if should_display:
                print(self._format_message(level, message, **kwargs))
            
            # Toujours loguer dans le fichier
            self._log_to_file(level, message, kwargs)
    
    def debug(self, message: str, **kwargs):
        self.log('DEBUG', message, **kwargs)
    
    def info(self, message: str, **kwargs):
        self.log('INFO', message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        self.log('WARNING', message, **kwargs)
    
    def error(self, message: str, **kwargs):
        self.log('ERROR', message, **kwargs)
    
    def critical(self, message: str, **kwargs):
        self.log('CRITICAL', message, **kwargs)
    
    def _log_to_file(self, level: str, message: str, kwargs: Dict[str, Any]):
        """Log dans un fichier"""
        try:
            log_file = os.path.join(config.LOG_DIR, f'{datetime.now().strftime("%Y%m%d")}.log')
            
            with open(log_file, 'a', encoding='utf-8') as f:
                log_entry = {
                    'timestamp': datetime.now().isoformat(),
                    'level': level,
                    'module': self.name,
                    'message': message,
                    'kwargs': kwargs
                }
                
                if 'exception' in kwargs:
                    log_entry['traceback'] = traceback.format_exc()
                
                f.write(json.dumps(log_entry) + '\n')
                
        except Exception:
            pass  # Ne pas échouer sur une erreur de log

# Initialiser le logger principal
logger = AdvancedLogger('agents.base_agent')

# =====================================================================
# SYSTÈME DE PROTECTION CONTRE LES IMPORTS CIRCULAIRES
# =====================================================================

class CircularImportProtection:
    """Protection avancée contre les imports circulaires"""
    
    def __init__(self):
        self._import_stack = []
        self._import_graph = {}
        self._blocked_paths = set()
        self._lock = threading.RLock()
        self._stats = {
            'total_imports': 0,
            'blocked_imports': 0,
            'circular_detected': 0,
            'max_depth_reached': 0
        }
    
    def enter_import(self, module_name: str, caller: Optional[str] = None) -> bool:
        """
        Enregistre le début d'un import.
        Retourne False si un import circulaire est détecté.
        """
        with self._lock:
            self._stats['total_imports'] += 1
            
            # Vérifier si bloqué
            if module_name in self._blocked_paths:
                self._stats['blocked_imports'] += 1
                if config.DEBUG_CIRCULAR:
                    logger.debug(f"Import bloqué: {module_name}")
                return False
            
            # Vérifier la circularité
            if module_name in self._import_stack:
                self._stats['circular_detected'] += 1
                circular_path = ' -> '.join(self._import_stack + [module_name])
                
                if config.DEBUG_CIRCULAR:
                    logger.warning(f"Import circulaire détecté: {circular_path}")
                
                # Bloquer ce chemin
                self._blocked_paths.add(module_name)
                
                # Enregistrer dans le graph
                if caller:
                    if caller not in self._import_graph:
                        self._import_graph[caller] = []
                    self._import_graph[caller].append(module_name)
                
                return False
            
            # Vérifier la profondeur
            if len(self._import_stack) >= config.MAX_IMPORT_DEPTH:
                self._stats['max_depth_reached'] += 1
                logger.error(f"Profondeur d'import maximale atteinte: {config.MAX_IMPORT_DEPTH}")
                return False
            
            # Ajouter à la pile
            self._import_stack.append(module_name)
            
            if config.DEBUG_CIRCULAR:
                logger.debug(f"Import entrant: {module_name} (profondeur: {len(self._import_stack)})")
            
            return True
    
    def exit_import(self, module_name: str):
        """Marque la fin d'un import"""
        with self._lock:
            if self._import_stack and self._import_stack[-1] == module_name:
                self._import_stack.pop()
                
                if config.DEBUG_CIRCULAR:
                    logger.debug(f"Import terminé: {module_name}")
    
    def get_current_stack(self) -> List[str]:
        """Retourne la pile d'imports actuelle"""
        with self._lock:
            return self._import_stack.copy()
    
    def get_stats(self) -> Dict[str, int]:
        """Retourne les statistiques"""
        with self._lock:
            return self._stats.copy()
    
    def get_import_graph(self) -> Dict[str, List[str]]:
        """Retourne le graph des imports"""
        with self._lock:
            return self._import_graph.copy()
    
    def reset(self):
        """Réinitialise le système"""
        with self._lock:
            self._import_stack.clear()
            self._blocked_paths.clear()
            self._stats = {k: 0 for k in self._stats}
            logger.info("Système de protection réinitialisé")

# Initialiser le système de protection
import_protector = CircularImportProtection()

# =====================================================================
# SYSTÈME DE CACHE D'IMPORT AVANCÉ
# =====================================================================

class ImportCache:
    """Cache d'imports avec expiration et statistiques"""
    
    @dataclass
    class CacheEntry:
        """Entrée de cache"""
        value: Any
        timestamp: float
        ttl: float
        hits: int = 0
        last_accessed: float = field(default_factory=lambda: datetime.now().timestamp())
    
    def __init__(self):
        self._cache = {}
        self._lock = threading.RLock()
        self._stats = {
            'hits': 0,
            'misses': 0,
            'sets': 0,
            'evictions': 0,
            'expirations': 0
        }
    
    def get(self, key: str, default=None) -> Any:
        """Récupère une valeur du cache"""
        with self._lock:
            # Nettoyer les entrées expirées
            self._clean_expired()
            
            if key in self._cache:
                entry = self._cache[key]
                entry.hits += 1
                entry.last_accessed = datetime.now().timestamp()
                self._stats['hits'] += 1
                
                if config.DEBUG_CACHE:
                    logger.debug(f"Cache hit: {key} (hits: {entry.hits})")
                
                return entry.value
            
            self._stats['misses'] += 1
            return default
    
    def set(self, key: str, value: Any, ttl: Optional[float] = None):
        """Met une valeur en cache"""
        with self._lock:
            if ttl is None:
                ttl = config.CACHE_TTL_SECONDS
            
            # Vérifier la taille maximale
            if len(self._cache) >= config.CACHE_MAX_SIZE:
                self._evict_oldest()
            
            entry = self.CacheEntry(
                value=value,
                timestamp=datetime.now().timestamp(),
                ttl=ttl
            )
            
            self._cache[key] = entry
            self._stats['sets'] += 1
            
            if config.DEBUG_CACHE:
                logger.debug(f"Cache set: {key} (TTL: {ttl}s)")
    
    def _clean_expired(self):
        """Nettoie les entrées expirées"""
        now = datetime.now().timestamp()
        expired_keys = []
        
        for key, entry in self._cache.items():
            if now - entry.timestamp > entry.ttl:
                expired_keys.append(key)
        
        for key in expired_keys:
            del self._cache[key]
            self._stats['expirations'] += 1
        
        if expired_keys and config.DEBUG_CACHE:
            logger.debug(f"Expirés nettoyés: {len(expired_keys)} entrées")
    
    def _evict_oldest(self):
        """Évince l'entrée la plus ancienne"""
        if not self._cache:
            return
        
        oldest_key = min(self._cache.keys(), 
                        key=lambda k: self._cache[k].last_accessed)
        
        del self._cache[oldest_key]
        self._stats['evictions'] += 1
        
        if config.DEBUG_CACHE:
            logger.debug(f"Éviction: {oldest_key}")
    
    def clear(self):
        """Vide le cache"""
        with self._lock:
            self._cache.clear()
            logger.info("Cache vidé")
    
    def get_stats(self) -> Dict[str, Any]:
        """Retourne les statistiques"""
        with self._lock:
            stats = self._stats.copy()
            stats['size'] = len(self._cache)
            stats['keys'] = list(self._cache.keys())
            return stats
    
    def diagnose(self) -> Dict[str, Any]:
        """Diagnostique le cache"""
        with self._lock:
            now = datetime.now().timestamp()
            
            entries_info = []
            for key, entry in self._cache.items():
                age = now - entry.timestamp
                remaining_ttl = max(0, entry.ttl - age)
                
                entries_info.append({
                    'key': key,
                    'age_seconds': age,
                    'remaining_ttl': remaining_ttl,
                    'hits': entry.hits,
                    'last_accessed_seconds_ago': now - entry.last_accessed
                })
            
            return {
                'stats': self.get_stats(),
                'entries': entries_info,
                'timestamp': datetime.now().isoformat()
            }

# Initialiser le cache
import_cache = ImportCache()

# =====================================================================
# IMPORTEUR DYNAMIQUE AVANCÉ
# =====================================================================

class AdvancedImporter:
    """Système d'import dynamique avancé"""
    
    def __init__(self):
        self._loaded_modules = {}
        self._failed_imports = {}
        self._module_versions = {}
        self._lock = threading.RLock()
        self._stats = {
            'successful_imports': 0,
            'failed_imports': 0,
            'cached_imports': 0,
            'dynamic_imports': 0
        }
    
    def import_class(self, file_path: str, class_name: str, 
                    fallback_class: Optional[Type] = None) -> Type:
        """
        Importe une classe depuis un fichier.
        """
        cache_key = f"{file_path}::{class_name}"
        
        # Vérifier le cache
        if config.ENABLE_CACHE_SYSTEM:
            cached = import_cache.get(cache_key)
            if cached is not None:
                self._stats['cached_imports'] += 1
                logger.debug(f"Import depuis cache: {class_name}")
                return cached
        
        # Protection contre les imports circulaires
        if config.PREVENT_CIRCULAR_IMPORTS:
            if not import_protector.enter_import(cache_key, 'AdvancedImporter'):
                logger.warning(f"Import circulaire évité: {class_name}")
                
                if fallback_class:
                    return fallback_class
                raise ImportError(f"Import circulaire détecté pour {class_name}")
        
        try:
            # Vérifier l'existence du fichier
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"Fichier non trouvé: {file_path}")
            
            logger.info(f"Import dynamique: {class_name} depuis {file_path}")
            
            # Générer un nom de module unique
            module_hash = hashlib.sha256(file_path.encode()).hexdigest()[:12]
            unique_name = f"_dynamic_{class_name}_{module_hash}"
            
            # Créer la spécification
            spec = importlib.util.spec_from_file_location(unique_name, file_path)
            
            if spec is None:
                raise ImportError(f"Impossible de créer spec pour {file_path}")
            
            if spec.loader is None:
                raise ImportError(f"Loader non disponible pour {file_path}")
            
            # Créer le module
            module = importlib.util.module_from_spec(spec)
            
            # Configurer les métadonnées
            module.__name__ = unique_name
            module.__file__ = file_path
            module.__package__ = None
            module.__dynamic_import__ = True
            module.__import_time__ = datetime.now().isoformat()
            
            # Exécuter le module
            spec.loader.exec_module(module)
            
            # Récupérer la classe
            if not hasattr(module, class_name):
                raise AttributeError(f"Classe '{class_name}' non trouvée dans {file_path}")
            
            target_class = getattr(module, class_name)
            
            # Configurer la classe
            target_class.__module__ = f"agents.base_agent.dynamic.{class_name}"
            target_class.__file__ = file_path
            target_class.__spec__ = spec
            
            # Enregistrer
            self._loaded_modules[cache_key] = {
                'module': module,
                'class': target_class,
                'spec': spec,
                'timestamp': datetime.now().isoformat(),
                'file_path': file_path
            }
            
            self._module_versions[class_name] = {
                'version': getattr(target_class, '__version__', '1.0.0'),
                'module': target_class.__module__,
                'import_time': datetime.now().isoformat()
            }
            
            # Mettre en cache
            if config.ENABLE_CACHE_SYSTEM:
                import_cache.set(cache_key, target_class)
            
            self._stats['successful_imports'] += 1
            self._stats['dynamic_imports'] += 1
            
            logger.info(f"✅ Import réussi: {class_name}")
            
            if config.PREVENT_CIRCULAR_IMPORTS:
                import_protector.exit_import(cache_key)
            
            return target_class
            
        except Exception as e:
            if config.PREVENT_CIRCULAR_IMPORTS:
                import_protector.exit_import(cache_key)
            
            # Enregistrer l'échec
            self._failed_imports[cache_key] = {
                'error': str(e),
                'traceback': traceback.format_exc(),
                'timestamp': datetime.now().isoformat(),
                'file_path': file_path,
                'class_name': class_name
            }
            
            self._stats['failed_imports'] += 1
            logger.error(f"❌ Échec import {class_name}: {e}")
            
            # Utiliser la classe de secours si disponible
            if fallback_class:
                logger.warning(f"Utilisation classe de secours pour {class_name}")
                return fallback_class
            
            # Créer une classe de secours
            return self._create_fallback_class(class_name, str(e))
    
    def _create_fallback_class(self, class_name: str, error_msg: str) -> Type:
        """Crée une classe de secours"""
        class FallbackClass:
            """Classe de secours générée dynamiquement"""
            __fallback__ = True
            __error__ = error_msg
            __name__ = class_name
            __qualname__ = class_name
            __module__ = f"agents.base_agent.fallback.{class_name}"
            
            def __init__(self, *args, **kwargs):
                raise ImportError(
                    f"{class_name} non disponible. "
                    f"Erreur d'import: {error_msg[:200]}"
                )
            
            @classmethod
            def is_fallback(cls):
                return True
            
            def __repr__(self):
                return f"<Fallback{class_name} [ERROR]>"
        
        return FallbackClass
    
    def get_loaded_modules(self) -> Dict[str, Any]:
        """Retourne les modules chargés"""
        with self._lock:
            return self._loaded_modules.copy()
    
    def get_failed_imports(self) -> Dict[str, Any]:
        """Retourne les imports échoués"""
        with self._lock:
            return self._failed_imports.copy()
    
    def get_stats(self) -> Dict[str, int]:
        """Retourne les statistiques"""
        with self._lock:
            return self._stats.copy()
    
    def clear(self):
        """Nettoie l'importeur"""
        with self._lock:
            self._loaded_modules.clear()
            self._failed_imports.clear()
            self._stats = {k: 0 for k in self._stats}
            logger.info("Importeur nettoyé")

# Initialiser l'importeur
dynamic_importer = AdvancedImporter()

# =====================================================================
# IMPORT DES CLASSES PRINCIPALES
# =====================================================================

def import_critical_classes():
    """Importe les classes critiques depuis base_agent.py"""
    
    base_agent_file = config.BASE_AGENT_FILE
    
    if not os.path.exists(base_agent_file):
        logger.critical(f"Fichier base_agent.py non trouvé: {base_agent_file}")
        raise FileNotFoundError(f"base_agent.py manquant: {base_agent_file}")
    
    # UNIQUEMENT les classes qui existent réellement dans base_agent.py
    EXISTING_CLASSES = [
        'BaseAgent',
        'AgentCapability',
        'AgentStatus',
        'TaskResult',
        'AgentConfiguration'
    ]
    
    # Dictionnaire pour stocker les classes
    all_classes = {}
    
    logger.info(f"Import des classes depuis {base_agent_file}")
    
    # Importer uniquement les classes qui existent
    for class_name in EXISTING_CLASSES:
        try:
            cls = dynamic_importer.import_class(base_agent_file, class_name)
            all_classes[class_name] = cls
            globals()[class_name] = cls
            logger.info(f"✅ {class_name} importé")
        except Exception as e:
            logger.error(f"❌ Échec import {class_name}: {e}")
            
            # Pour BaseAgent et AgentConfiguration, on DOIT avoir une classe
            if class_name in ['BaseAgent', 'AgentConfiguration']:
                logger.critical(f"CRITIQUE: {class_name} manquant - création d'urgence")
                
                if class_name == 'BaseAgent':
                    # Classe BaseAgent d'urgence
                    class EmergencyBaseAgent:
                        def __init__(self, config=None):
                            self.config = config or {}
                            self.name = "EmergencyBaseAgent"
                            self.status = "ERROR"
                        def execute_task(self, task):
                            return {"error": "BaseAgent non disponible"}
                    
                    cls = EmergencyBaseAgent
                else:
                    # AgentConfiguration d'urgence
                    class EmergencyAgentConfiguration:
                        def __init__(self, **kwargs):
                            self.__dict__.update(kwargs)
                    
                    cls = EmergencyAgentConfiguration
                
                all_classes[class_name] = cls
                globals()[class_name] = cls
    
    return all_classes

# Exécuter l'import des classes
imported_classes = import_critical_classes()

# S'assurer que BaseAgent est disponible
if 'BaseAgent' not in imported_classes:
    logger.critical("BaseAgent non importé - création d'urgence")
    
    class EmergencyBaseAgent:
        """Classe BaseAgent d'urgence"""
        def __init__(self, *args, **kwargs):
            raise ImportError("BaseAgent non disponible - système d'import défaillant")
    
    BaseAgent = EmergencyBaseAgent
    imported_classes['BaseAgent'] = BaseAgent
else:
    BaseAgent = imported_classes['BaseAgent']

# =====================================================================
# SYSTÈME DE MODULE PROXY POUR 'base_agent'
# =====================================================================

class BaseAgentModuleProxy:
    """
    Proxy module complet pour 'base_agent'.
    Permet 'from base_agent import BaseAgent'
    """
    
    def __init__(self):
        self._real_module = None
        self._attribute_cache = {}
        self._module_lock = threading.RLock()
        
        # Métadonnées du module
        self.__name__ = 'base_agent'
        self.__file__ = __file__
        self.__path__ = []
        self.__package__ = 'agents.base_agent'
        self.__version__ = '4.0.0'
        self.__author__ = 'SmartContractDevPipeline'
        self.__description__ = 'Module proxy pour agents.base_agent'
        
        # Initialiser avec les classes importées
        self._initialize_from_imported()
        
        logger.info(f"Module proxy 'base_agent' initialisé avec {len(self._attribute_cache)} classes")
    
    def _initialize_from_imported(self):
        """Initialise le cache avec les classes importées"""
        with self._module_lock:
            for class_name, class_obj in imported_classes.items():
                self._attribute_cache[class_name] = class_obj
                setattr(self, class_name, class_obj)
    
    def _load_real_module(self):
        """Charge le vrai module de manière paresseuse"""
        with self._module_lock:
            if self._real_module is not None:
                return
            
            try:
                # Créer un module dynamique
                module_spec = importlib.util.spec_from_loader(
                    'real_base_agent_module',
                    loader=None,
                    origin=__file__
                )
                
                self._real_module = importlib.util.module_from_spec(module_spec)
                self._real_module.__name__ = 'base_agent'
                self._real_module.__file__ = __file__
                self._real_module.__package__ = 'agents.base_agent'
                
                # Injecter toutes les classes
                for attr_name, attr_value in self._attribute_cache.items():
                    setattr(self._real_module, attr_name, attr_value)
                
                # Injecter les utilitaires
                for util_name in ['logger', 'import_cache', 'dynamic_importer']:
                    if util_name in globals():
                        setattr(self._real_module, util_name, globals()[util_name])
                
                logger.debug("Module réel chargé paresseusement")
                
            except Exception as e:
                logger.error(f"Erreur chargement module réel: {e}")
                
                # Module de secours
                class FallbackModule:
                    def __getattr__(self, name):
                        raise ImportError(f"Module 'base_agent' non disponible: {e}")
                
                self._real_module = FallbackModule()
    
    def __getattr__(self, name: str) -> Any:
        """Gère l'accès aux attributs"""
        # Vérifier le cache d'abord
        if name in self._attribute_cache:
            return self._attribute_cache[name]
        
        # Vérifier si c'est une métadonnée
        if name.startswith('__') and name.endswith('__'):
            raise AttributeError(f"module 'base_agent' has no attribute '{name}'")
        
        # Essayer de charger dynamiquement
        if config.BASE_AGENT_FILE and os.path.exists(config.BASE_AGENT_FILE):
            try:
                logger.debug(f"Chargement dynamique via proxy: {name}")
                
                cls = dynamic_importer.import_class(config.BASE_AGENT_FILE, name)
                
                # Mettre en cache
                with self._module_lock:
                    self._attribute_cache[name] = cls
                    setattr(self, name, cls)
                
                return cls
                
            except Exception as e:
                logger.debug(f"Échec chargement dynamique {name}: {e}")
        
        # Charger le module réel et vérifier
        self._load_real_module()
        
        if hasattr(self._real_module, name):
            attr = getattr(self._real_module, name)
            
            # Mettre en cache
            with self._module_lock:
                self._attribute_cache[name] = attr
            
            return attr
        
        # Attribut non trouvé
        available = sorted(list(self._attribute_cache.keys()) + 
                          ['__name__', '__file__', '__version__'])
        
        raise AttributeError(
            f"module 'base_agent' has no attribute '{name}'. "
            f"Available: {', '.join(available[:10])}..."
        )
    
    def __dir__(self):
        """Retourne la liste des attributs disponibles"""
        with self._module_lock:
            all_attrs = set(self._attribute_cache.keys())
            all_attrs.update(self.__dict__.keys())
            
            if self._real_module:
                all_attrs.update(dir(self._real_module))
            
            # Ajouter les attributs standards
            all_attrs.update([
                '__name__', '__file__', '__path__', '__package__',
                '__version__', '__doc__', '__author__', '__description__'
            ])
            
            return sorted(all_attrs)
    
    def get_available_classes(self) -> List[str]:
        """Retourne les classes disponibles"""
        with self._module_lock:
            return list(self._attribute_cache.keys())
    
    def reload(self):
        """Recharge toutes les classes"""
        logger.info("Rechargement du module proxy...")
        
        with self._module_lock:
            # Vider les caches
            self._attribute_cache.clear()
            import_cache.clear()
            dynamic_importer.clear()
            
            # Réimporter les classes
            global imported_classes
            imported_classes = import_critical_classes()
            
            # Réinitialiser
            self._initialize_from_imported()
            self._real_module = None
            
            logger.info(f"Rechargement terminé: {len(self._attribute_cache)} classes")

# =====================================================================
# CONFIGURATION DU SYSTÈME D'IMPORT GLOBAL
# =====================================================================

def configure_global_import_system() -> Dict[str, Any]:
    """
    Configure le système d'import global.
    """
    result = {
        'success': False,
        'timestamp': datetime.now().isoformat(),
        'steps': {},
        'errors': []
    }
    
    try:
        # Étape 1: Créer le proxy
        result['steps']['create_proxy'] = 'starting'
        proxy = BaseAgentModuleProxy()
        result['steps']['create_proxy'] = 'success'
        
        # Étape 2: Enregistrer dans sys.modules
        result['steps']['register_module'] = 'starting'
        sys.modules['base_agent'] = proxy
        sys.modules['agents.base_agent.base_agent'] = proxy
        result['steps']['register_module'] = 'success'
        
        # Étape 3: Tester l'import
        result['steps']['test_import'] = 'starting'
        try:
            # Test 1: from base_agent import BaseAgent
            from base_agent import BaseAgent as TestBA
            result['test_from_base_agent'] = {
                'success': True,
                'class': TestBA.__name__,
                'module': TestBA.__module__
            }
            
            # Test 2: import base_agent
            import base_agent as ba_module
            result['test_import_base_agent'] = {
                'success': True,
                'module': ba_module.__name__
            }
            
            result['steps']['test_import'] = 'success'
            result['success'] = True
            
            logger.info("✅ Système d'import global configuré avec succès")
            
        except ImportError as e:
            result['steps']['test_import'] = 'failed'
            result['errors'].append(f"Test import failed: {e}")
            logger.error(f"❌ Test import échoué: {e}")
        
        # Étape 4: Informations supplémentaires
        result['proxy_info'] = {
            'available_classes': proxy.get_available_classes(),
            'class_count': len(proxy.get_available_classes()),
            'module_name': proxy.__name__,
            'module_file': proxy.__file__
        }
        
    except Exception as e:
        result['steps']['error'] = str(e)
        result['errors'].append(f"Configuration failed: {e}")
        logger.critical(f"❌ Échec configuration système: {e}")
        traceback.print_exc()
    
    return result

# Configurer le système
if config.AUTO_CONFIGURE_ON_LOAD and config.ENABLE_PROXY_SYSTEM:
    import_config_result = configure_global_import_system()
else:
    import_config_result = {'success': False, 'reason': 'auto_configure_disabled'}

# =====================================================================
# EXPORTS ET MÉTADONNÉES
# =====================================================================

# Construire __all__ dynamiquement
__all__ = ['BaseAgent']  # Toujours exporter BaseAgent en premier

# Ajouter toutes les classes importées
for class_name in imported_classes.keys():
    if class_name != 'BaseAgent' and class_name not in __all__:
        __all__.append(class_name)

# Ajouter les utilitaires
__all__.extend([
    'logger',
    'config',
    'import_protector',
    'import_cache',
    'dynamic_importer'
])

# Métadonnées du package
__version__ = '4.0.0'
__author__ = 'SmartContractDevPipeline'
__date__ = '2026-02-07'
__license__ = 'Proprietary'
__description__ = 'Package de base complet pour tous les agents'
__url__ = 'https://github.com/SmartContractDevPipeline'

# Informations de build
__build_info__ = {
    'version': __version__,
    'build_date': __date__,
    'python_version': sys.version,
    'platform': sys.platform,
    'import_system_configured': import_config_result.get('success', False),
    'imported_classes_count': len(imported_classes),
    'imported_classes': list(imported_classes.keys()),
    'config': config.to_dict()
}

# =====================================================================
# SYSTÈME DE DIAGNOSTIC
# =====================================================================

class DiagnosticSystem:
    """Système de diagnostic complet"""
    
    @staticmethod
    def full_diagnosis() -> Dict[str, Any]:
        """Diagnostic complet du package"""
        diagnosis = {
            'timestamp': datetime.now().isoformat(),
            'package': __build_info__,
            'file_system': DiagnosticSystem._check_files(),
            'import_system': import_config_result,
            'cache_system': import_cache.diagnose(),
            'protection_system': {
                'stats': import_protector.get_stats(),
                'current_stack': import_protector.get_current_stack(),
                'import_graph': import_protector.get_import_graph()
            },
            'importer_system': {
                'stats': dynamic_importer.get_stats(),
                'loaded_modules': len(dynamic_importer.get_loaded_modules()),
                'failed_imports': len(dynamic_importer.get_failed_imports())
            },
            'sys_info': {
                'sys_path': sys.path[:5],
                'cwd': os.getcwd(),
                'python_executable': sys.executable
            }
        }
        
        # Tests d'import
        diagnosis['import_tests'] = DiagnosticSystem._run_import_tests()
        
        return diagnosis
    
    @staticmethod
    def _check_files() -> Dict[str, Any]:
        """Vérifie les fichiers"""
        current_dir = os.path.dirname(__file__)
        
        files = {
            'base_agent.py': {
                'path': os.path.join(current_dir, 'base_agent.py'),
                'exists': os.path.exists(os.path.join(current_dir, 'base_agent.py')),
                'size': os.path.getsize(os.path.join(current_dir, 'base_agent.py')) 
                        if os.path.exists(os.path.join(current_dir, 'base_agent.py')) else 0
            },
            'config.yaml': {
                'path': os.path.join(current_dir, 'config.yaml'),
                'exists': os.path.exists(os.path.join(current_dir, 'config.yaml'))
            },
            '__init__.py': {
                'path': __file__,
                'exists': True,
                'size': os.path.getsize(__file__)
            }
        }
        
        return files
    
    @staticmethod
    def _run_import_tests() -> Dict[str, Any]:
        """Exécute des tests d'import"""
        tests = {}
        
        test_cases = [
            ("from agents.base_agent import BaseAgent", 
             "Test import depuis agents.base_agent"),
            
            ("from base_agent import BaseAgent",
             "Test import depuis base_agent (proxy)"),
             
            ("import base_agent",
             "Test import module base_agent"),
             
            ("from agents.base_agent import AgentCapability",
             "Test import AgentCapability"),
             
            ("from base_agent import AgentCapability",
             "Test import AgentCapability depuis proxy")
        ]
        
        for code, description in test_cases:
            try:
                exec(code, globals())
                tests[description] = {'success': True, 'code': code}
            except Exception as e:
                tests[description] = {
                    'success': False,
                    'code': code,
                    'error': str(e),
                    'error_type': type(e).__name__
                }
        
        return tests
    
    @staticmethod
    def generate_report() -> str:
        """Génère un rapport formaté"""
        diag = DiagnosticSystem.full_diagnosis()
        
        report_lines = []
        report_lines.append("=" * 80)
        report_lines.append("DIAGNOSTIC COMPLET - agents.base_agent")
        report_lines.append(f"Version: {__version__}")
        report_lines.append("=" * 80)
        
        # Résumé
        report_lines.append("\n📊 RÉSUMÉ:")
        report_lines.append(f"  Package: {diag['package']['version']}")
        report_lines.append(f"  Date: {diag['timestamp']}")
        report_lines.append(f"  Classes importées: {len(diag['package']['imported_classes'])}")
        
        # Fichiers
        report_lines.append("\n📁 FICHIERS:")
        for file_name, file_info in diag['file_system'].items():
            status = "✅" if file_info['exists'] else "❌"
            size_mb = file_info.get('size', 0) / 1024 / 1024
            size_str = f" ({size_mb:.2f} MB)" if 'size' in file_info and file_info['size'] > 0 else ""
            report_lines.append(f"  {status} {file_name}: {file_info['path']}{size_str}")
        
        # Tests d'import
        report_lines.append("\n🧪 TESTS D'IMPORT:")
        successful_tests = 0
        for test_name, test_result in diag['import_tests'].items():
            status = "✅" if test_result['success'] else "❌"
            report_lines.append(f"  {status} {test_name}")
            if test_result['success']:
                successful_tests += 1
        
        # Statistiques
        report_lines.append("\n📈 STATISTIQUES:")
        report_lines.append(f"  Tests réussis: {successful_tests}/{len(diag['import_tests'])}")
        report_lines.append(f"  Cache: {diag['cache_system']['stats']}")
        report_lines.append(f"  Import dynamique: {diag['importer_system']['stats']}")
        
        # État du système
        report_lines.append("\n⚙️  ÉTAT DU SYSTÈME:")
        report_lines.append(f"  Import système: {'✅' if diag['import_system']['success'] else '❌'}")
        report_lines.append(f"  Protection: {diag['protection_system']['stats']}")
        
        # Recommandations
        if successful_tests < len(diag['import_tests']):
            report_lines.append("\n⚠️  RECOMMANDATIONS:")
            for test_name, test_result in diag['import_tests'].items():
                if not test_result['success']:
                    report_lines.append(f"  • {test_name}: {test_result.get('error', 'Unknown error')}")
        
        report_lines.append("\n" + "=" * 80)
        
        return '\n'.join(report_lines)

# =====================================================================
# INITIALISATION DU PACKAGE
# =====================================================================

def initialize_package(verbose: bool = None) -> Dict[str, Any]:
    """
    Initialise le package.
    """
    if verbose is None:
        verbose = config.VERBOSE_INIT
    
    init_result = {
        'success': False,
        'timestamp': datetime.now().isoformat(),
        'steps': {},
        'warnings': [],
        'errors': []
    }
    
    try:
        # Étape 1: Vérification des fichiers
        init_result['steps']['file_check'] = 'starting'
        if not os.path.exists(config.BASE_AGENT_FILE):
            error_msg = f"Fichier base_agent.py manquant: {config.BASE_AGENT_FILE}"
            init_result['errors'].append(error_msg)
            logger.critical(error_msg)
            init_result['steps']['file_check'] = 'failed'
            return init_result
        init_result['steps']['file_check'] = 'success'
        
        # Étape 2: Import des classes
        init_result['steps']['import_classes'] = 'starting'
        # Les classes sont déjà importées au chargement du module
        init_result['steps']['import_classes'] = 'success'
        
        # Étape 3: Configuration système
        init_result['steps']['system_config'] = 'starting'
        if config.AUTO_CONFIGURE_ON_LOAD:
            init_result['system_config'] = import_config_result
            init_result['steps']['system_config'] = 'success' if import_config_result.get('success') else 'failed'
        else:
            init_result['steps']['system_config'] = 'skipped'
        
        # Étape 4: Diagnostic
        init_result['steps']['diagnostic'] = 'starting'
        diagnostic = DiagnosticSystem.full_diagnosis()
        init_result['diagnostic'] = diagnostic
        
        # Déterminer le succès
        success_criteria = [
            os.path.exists(config.BASE_AGENT_FILE),
            'BaseAgent' in globals() and globals()['BaseAgent'] is not None,
            diagnostic['import_tests'].get('Test import depuis agents.base_agent', {}).get('success', False),
            diagnostic['import_tests'].get('Test import depuis base_agent (proxy)', {}).get('success', False)
        ]
        
        init_result['success'] = all(success_criteria)
        init_result['success_criteria'] = success_criteria
        init_result['steps']['diagnostic'] = 'success' if init_result['success'] else 'failed'
        
        # Afficher le résultat si demandé
        if verbose:
            if init_result['success']:
                logger.info("✅ INITIALISATION RÉUSSIE")
                logger.info(f"   Package {__version__} prêt")
                logger.info(f"   {len(imported_classes)} classes disponibles")
                
                # Afficher les classes principales
                main_classes = ['BaseAgent', 'AgentCapability', 'AgentStatus', 'TaskResult']
                for cls_name in main_classes:
                    if cls_name in imported_classes:
                        cls = imported_classes[cls_name]
                        is_fallback = hasattr(cls, '__fallback__') and cls.__fallback__
                        status = " (secours)" if is_fallback else ""
                        logger.info(f"   • {cls_name}{status}")
                
            else:
                logger.error("❌ INITIALISATION ÉCHOUÉE")
                for error in init_result['errors']:
                    logger.error(f"   • {error}")
                
                # Afficher le diagnostic
                print(DiagnosticSystem.generate_report())
        
        return init_result
        
    except Exception as e:
        init_result['steps']['exception'] = str(e)
        init_result['errors'].append(f"Exception: {e}")
        init_result['traceback'] = traceback.format_exc()
        
        logger.critical(f"Erreur initialisation: {e}")
        
        return init_result

# Initialisation automatique
if config.AUTO_CONFIGURE_ON_LOAD:
    package_initialization = initialize_package(verbose=config.VERBOSE_INIT)
else:
    package_initialization = {'success': False, 'reason': 'auto_configure_disabled'}

# =====================================================================
# FONCTIONS PUBLIQUES
# =====================================================================

def get_package_info() -> Dict[str, Any]:
    """Retourne les informations du package"""
    return {
        'name': 'agents.base_agent',
        'version': __version__,
        'description': __description__,
        'author': __author__,
        'initialized': package_initialization.get('success', False),
        'imported_classes': list(imported_classes.keys()),
        'import_system': import_config_result,
        'build_info': __build_info__
    }

def test_package() -> Dict[str, Any]:
    """Teste le package"""
    return DiagnosticSystem.full_diagnosis()

def reload_package():
    """Recharge le package"""
    logger.info("Rechargement du package...")
    
    # Recharger les classes
    global imported_classes
    imported_classes = import_critical_classes()
    
    # Recharger le proxy si configuré
    if 'base_agent' in sys.modules and hasattr(sys.modules['base_agent'], 'reload'):
        sys.modules['base_agent'].reload()
    
    # Vider les caches
    import_cache.clear()
    
    logger.info("Package rechargé")

# =====================================================================
# POINT D'ENTRÉE PRINCIPAL
# =====================================================================

def main():
    """Fonction principale"""
    print("\n" + "=" * 80)
    print("AGENTS.BASE_AGENT - MAIN")
    print("=" * 80)
    
    # Exécuter le diagnostic
    diagnostic = DiagnosticSystem.full_diagnosis()
    print(DiagnosticSystem.generate_report())
    
    # Calculer le score
    import_tests = diagnostic['import_tests']
    successful = sum(1 for test in import_tests.values() if test['success'])
    total = len(import_tests)
    percentage = (successful / total * 100) if total > 0 else 0
    
    print(f"\n📊 SCORE: {successful}/{total} ({percentage:.1f}%)")
    
    if percentage >= 90:
        print("🎉 EXCELLENT - Système pleinement fonctionnel")
        exit_code = 0
    elif percentage >= 70:
        print("✅ BON - Système fonctionnel")
        exit_code = 0
    elif percentage >= 50:
        print("⚠️  MOYEN - Système avec limitations")
        exit_code = 1
    else:
        print("❌ INSUFFISANT - Problèmes critiques")
        exit_code = 2
    
    print("\n💡 UTILISATION:")
    print("   from agents.base_agent import BaseAgent  # Recommandé")
    print("   from base_agent import BaseAgent         # Via proxy")
    print("\n🔧 DIAGNOSTIC:")
    print("   agents.base_agent.DiagnosticSystem.generate_report()")
    
    print("\n" + "=" * 80)
    
    exit(exit_code)

# Point d'entrée
if __name__ == '__main__':
    main()

# =====================================================================
# FIN DU FICHIER
# =====================================================================
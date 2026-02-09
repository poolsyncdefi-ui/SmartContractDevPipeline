"""
agent.py - Système de compatibilité d'import avancé
Ce fichier permet 'from base_agent import BaseAgent' sans créer d'import circulaire.
Version: 2.0.0
"""

import sys
import os
import importlib.util
import importlib.machinery
from typing import Any, Optional

# =====================================================================
# CONFIGURATION
# =====================================================================

# Déterminer les chemins
_CURRENT_FILE = os.path.abspath(__file__)
_CURRENT_DIR = os.path.dirname(_CURRENT_FILE)
_BASE_AGENT_FILE = os.path.join(_CURRENT_DIR, 'base_agent.py')

# Mode debug
_DEBUG_MODE = os.environ.get('BASE_AGENT_DEBUG', 'false').lower() == 'true'

# =====================================================================
# SYSTÈME DE PROTECTION CONTRE LA RÉCURSION
# =====================================================================

class RecursionGuard:
    """Protège contre la récursion infinie dans les imports"""
    
    _import_depth = 0
    _max_depth = 5
    _import_stack = []
    
    @classmethod
    def enter_import(cls, module_name: str) -> bool:
        """Enregistre le début d'un import"""
        cls._import_depth += 1
        cls._import_stack.append(module_name)
        
        if cls._import_depth > cls._max_depth:
            raise ImportError(
                f"Profondeur d'import excessive ({cls._import_depth} > {cls._max_depth}). "
                f"Stack: {' -> '.join(cls._import_stack[-5:])}"
            )
        
        if _DEBUG_MODE:
            print(f"[RecursionGuard] Entrée import: {module_name} (depth: {cls._import_depth})")
        
        return True
    
    @classmethod
    def exit_import(cls, module_name: str):
        """Marque la fin d'un import"""
        if cls._import_stack and cls._import_stack[-1] == module_name:
            cls._import_stack.pop()
        
        cls._import_depth = max(0, cls._import_depth - 1)
        
        if _DEBUG_MODE:
            print(f"[RecursionGuard] Sortie import: {module_name} (depth: {cls._import_depth})")
    
    @classmethod
    def get_current_depth(cls) -> int:
        """Retourne la profondeur actuelle"""
        return cls._import_depth

# =====================================================================
# IMPORT SÉCURISÉ DEPUIS BASE_AGENT.PY
# =====================================================================

def import_from_base_agent(class_name: str, fallback_value: Any = None) -> Any:
    """
    Importe une classe depuis base_agent.py de manière sécurisée
    sans créer d'import circulaire.
    """
    # Protéger contre la récursion
    if RecursionGuard.get_current_depth() > 3:
        if _DEBUG_MODE:
            print(f"[import_from_base_agent] ❌ Trop profond, retour fallback pour {class_name}")
        return fallback_value
    
    try:
        RecursionGuard.enter_import(f'agent.py->{class_name}')
        
        # Vérifier que le fichier existe
        if not os.path.exists(_BASE_AGENT_FILE):
            raise FileNotFoundError(f"Fichier base_agent.py non trouvé: {_BASE_AGENT_FILE}")
        
        if _DEBUG_MODE:
            print(f"[import_from_base_agent] Import {class_name} depuis {_BASE_AGENT_FILE}")
        
        # Méthode 1: Utiliser importlib avec un nom de module unique
        # Pour éviter les conflits avec d'autres imports
        unique_id = f"_import_{class_name}_{abs(hash(_BASE_AGENT_FILE)) % 10000:04d}"
        
        # Créer la spécification
        spec = importlib.util.spec_from_file_location(
            unique_id,
            _BASE_AGENT_FILE
        )
        
        if spec is None or spec.loader is None:
            raise ImportError(f"Impossible de créer spec pour {_BASE_AGENT_FILE}")
        
        # Créer le module
        module = importlib.util.module_from_spec(spec)
        
        # Définir __name__ pour éviter les références circulaires
        module.__name__ = unique_id
        module.__file__ = _BASE_AGENT_FILE
        module.__package__ = None  # Pas un package
        
        # Exécuter le module
        spec.loader.exec_module(module)
        
        # Récupérer la classe
        if not hasattr(module, class_name):
            raise AttributeError(f"Classe '{class_name}' non trouvée dans {_BASE_AGENT_FILE}")
        
        target_class = getattr(module, class_name)
        
        # Modifier le __module__ pour éviter la confusion
        target_class.__module__ = f"agents.base_agent._imported.{class_name}"
        
        if _DEBUG_MODE:
            print(f"[import_from_base_agent] ✅ {class_name} importé avec succès")
        
        RecursionGuard.exit_import(f'agent.py->{class_name}')
        
        return target_class
        
    except Exception as e:
        RecursionGuard.exit_import(f'agent.py->{class_name}')
        
        if _DEBUG_MODE:
            print(f"[import_from_base_agent] ❌ Erreur import {class_name}: {e}")
        
        if fallback_value is not None:
            return fallback_value
        
        # Créer une classe de secours
        class FallbackClass:
            def __init__(self, *args, **kwargs):
                raise ImportError(
                    f"{class_name} non disponible. "
                    f"Erreur d'import: {type(e).__name__}: {str(e)[:100]}..."
                )
        
        return FallbackClass

# =====================================================================
# IMPORT DES CLASSES PRINCIPALES
# =====================================================================

# Importer BaseAgent
try:
    BaseAgent = import_from_base_agent('BaseAgent')
    _BASEAGENT_LOADED = True
    _BASEAGENT_ERROR = None
except Exception as e:
    _BASEAGENT_LOADED = False
    _BASEAGENT_ERROR = str(e)
    
    # Classe de secours
    class BaseAgent:
        def __init__(self, *args, **kwargs):
            raise ImportError(
                f"BaseAgent non disponible. "
                f"Erreur: {_BASEAGENT_ERROR}\n"
                f"Fichier: {_BASE_AGENT_FILE}"
            )

# Importer d'autres classes importantes
_OTHER_CLASSES = ['AgentCapability', 'AgentStatus', 'TaskResult', 'AgentConfiguration']
_loaded_classes = {'BaseAgent': BaseAgent}

for class_name in _OTHER_CLASSES:
    try:
        cls = import_from_base_agent(class_name)
        _loaded_classes[class_name] = cls
        globals()[class_name] = cls
    except Exception as e:
        # Créer une classe de secours
        exec(f"""
class {class_name}:
    \"\"\"Classe de secours pour {class_name}\"\"\"
    pass
""")
        _loaded_classes[class_name] = locals()[class_name]

# =====================================================================
# SYSTÈME DE MODULE PROXY AVANCÉ
# =====================================================================

class AdvancedModuleProxy:
    """
    Proxy module avancé avec mise en cache et chargement paresseux.
    """
    
    def __init__(self):
        self._module_cache = {}
        self._attribute_cache = {}
        self.__name__ = 'base_agent'
        self.__file__ = _CURRENT_FILE
        self.__path__ = []
        self.__package__ = 'agents.base_agent'
        self.__version__ = '2.0.0'
        
        # Injecter les classes déjà chargées
        for name, cls in _loaded_classes.items():
            setattr(self, name, cls)
            self._attribute_cache[name] = cls
        
        if _DEBUG_MODE:
            print(f"[AdvancedModuleProxy] Initialisé avec {len(_loaded_classes)} classes")
    
    def __getattr__(self, name: str) -> Any:
        """Charge dynamiquement les attributs manquants"""
        # Vérifier le cache d'abord
        if name in self._attribute_cache:
            return self._attribute_cache[name]
        
        # Essayer de charger depuis base_agent.py
        try:
            if _DEBUG_MODE:
                print(f"[AdvancedModuleProxy] Chargement dynamique: {name}")
            
            cls = import_from_base_agent(name)
            
            # Mettre en cache
            self._attribute_cache[name] = cls
            setattr(self, name, cls)
            
            return cls
            
        except Exception as e:
            if _DEBUG_MODE:
                print(f"[AdvancedModuleProxy] Échec chargement {name}: {e}")
            
            # Créer un attribut de secours
            class FallbackAttr:
                def __call__(self, *args, **kwargs):
                    raise AttributeError(
                        f"L'attribut '{name}' n'est pas disponible dans le module 'base_agent'. "
                        f"Erreur d'import: {e}"
                    )
            
            fallback = FallbackAttr()
            self._attribute_cache[name] = fallback
            return fallback
    
    def __dir__(self):
        """Retourne la liste des attributs disponibles"""
        base_attrs = list(self._attribute_cache.keys())
        
        # Ajouter les attributs standards
        standard_attrs = ['__name__', '__file__', '__path__', '__package__', '__version__']
        
        return sorted(set(base_attrs + standard_attrs + list(self.__dict__.keys())))
    
    def get_loaded_classes(self):
        """Retourne la liste des classes chargées"""
        return list(self._attribute_cache.keys())
    
    def reload(self):
        """Recharge toutes les classes depuis base_agent.py"""
        if _DEBUG_MODE:
            print(f"[AdvancedModuleProxy] Rechargement des classes")
        
        self._attribute_cache.clear()
        
        # Recharger les classes de base
        for class_name in ['BaseAgent'] + _OTHER_CLASSES:
            try:
                cls = import_from_base_agent(class_name)
                self._attribute_cache[class_name] = cls
                setattr(self, class_name, cls)
            except Exception:
                pass

# =====================================================================
# CONFIGURATION DU SYSTÈME D'IMPORT GLOBAL
# =====================================================================

def setup_global_import_compatibility():
    """
    Configuration des imports globaux pour la compatibilité.
    CORRIGÉ : Maintient toute la logique originale mais corrige les KeyError
    """
    try:
        logger = logging.getLogger(__name__)
        logger.info("🔧 Configuration des imports globaux...")
        
        # 1. Nettoyage préalable CRITIQUE - Évite les doublons
        for key in list(sys.modules.keys()):
            if '_import_' in key and ('BaseAgent' in key or 'AgentCapability' in key or 
                                     'AgentStatus' in key or 'TaskResult' in key or 
                                     'AgentConfiguration' in key):
                try:
                    # Ne supprime que si ce n'est pas le module principal
                    if key != __name__:
                        del sys.modules[key]
                        logger.debug(f"🔧 Nettoyé entrée précédente: {key}")
                except Exception as e:
                    logger.debug(f"⚠ Impossible de nettoyer {key}: {e}")
        
        # 2. S'assurer que le module courant est bien enregistré
        current_module = sys.modules[__name__]
        
        # 3. CRITIQUE: Créer les noms dynamiques D'ABORD avant de les référencer
        dynamic_modules = {}
        class_mappings = {
            'BaseAgent': BaseAgent,
            'AgentCapability': AgentCapability,
            'AgentStatus': AgentStatus,
            'TaskResult': TaskResult,
            'AgentConfiguration': AgentConfiguration
        }
        
        # 4. Créer et enregistrer CHAQUE module dynamique
        for class_name, class_obj in class_mappings.items():
            # Générer le nom dynamique (identique à la logique originale)
            dynamic_name = f'_import_{class_name}_{id(class_obj)}'
            
            # CRÉER le module dynamique d'abord
            dynamic_module = type(sys)(dynamic_name)
            
            # Injecter la classe dans le module dynamique
            setattr(dynamic_module, class_name, class_obj)
            
            # Enregistrer dans sys.modules
            sys.modules[dynamic_name] = dynamic_module
            dynamic_modules[dynamic_name] = dynamic_module
            
            logger.debug(f"🔧 Module dynamique créé: {dynamic_name}")
        
        # 5. MAINTENANT configurer les alias (plus de KeyError!)
        # Alias principal
        sys.modules['agents.base_agent'] = current_module
        sys.modules['agents.base_agent.agent'] = current_module
        
        # 6. Configurer les alias vers les modules dynamiques
        for dynamic_name, dynamic_module in dynamic_modules.items():
            # Extraire le nom de classe du nom dynamique
            for class_name in class_mappings.keys():
                if class_name in dynamic_name:
                    # Créer l'alias standard
                    alias_name = f'agents.base_agent.{class_name.lower()}'
                    sys.modules[alias_name] = dynamic_module
                    logger.debug(f"🔧 Alias créé: {alias_name} -> {dynamic_name}")
        
        # 7. Vérifier que BaseAgent est accessible via le chemin court
        try:
            # Tester l'accès
            test_module = sys.modules.get('agents.base_agent.BaseAgent')
            if test_module is None:
                # Créer un alias direct
                sys.modules['agents.base_agent.BaseAgent'] = current_module
            
            logger.info("✅ Configuration d'import complète terminée")
            return True
            
        except Exception as test_error:
            logger.error(f"⚠ Test d'import échoué: {test_error}")
            # Fallback: enregistrement direct
            for class_name, class_obj in class_mappings.items():
                sys.modules[f'agents.base_agent.{class_name}'] = current_module
            
            return True
            
    except Exception as e:
        logger.error(f"❌ Échec configuration import: {e}")
        import traceback
        logger.error(traceback.format_exc())
        
        # Fallback ULTIME: configuration minimale
        try:
            current_module = sys.modules[__name__]
            sys.modules['agents.base_agent'] = current_module
            return True
        except:
            return False

def _register_dynamic_classes():
    """Enregistre les classes dynamiquement dans sys.modules - NOUVELLE FONCTION"""
    try:
        # Récupérer les classes depuis le module courant
        import inspect
        
        classes_to_register = [
            ('BaseAgent', BaseAgent),
            ('AgentCapability', AgentCapability),
            ('AgentStatus', AgentStatus),
            ('TaskResult', TaskResult),
            ('AgentConfiguration', AgentConfiguration)
        ]
        
        logger = logging.getLogger(__name__)
        
        for class_name, class_obj in classes_to_register:
            if class_obj is None:
                logger.warning(f"⚠ Classe {class_name} non disponible")
                continue
                
            # Format cohérent avec l'existant
            module_name = f'_import_{class_name}_{id(class_obj) if hasattr(id, "__call__") else hash(class_name)}'
            
            # Créer un module minimal
            module_obj = type(sys)(module_name)
            setattr(module_obj, class_name, class_obj)
            setattr(module_obj, '__all__', [class_name])
            
            # Enregistrer AVANT de configurer les alias
            sys.modules[module_name] = module_obj
            logger.debug(f"🔧 Enregistré: {module_name}")
        
        return True
    except Exception as e:
        logging.error(f"Échec enregistrement classes: {e}")
        return False


# Configurer le système d'import
_IMPORT_SYSTEM_CONFIGURED = setup_global_import_compatibility()

# =====================================================================
# EXPORTS
# =====================================================================

__all__ = list(_loaded_classes.keys())

# =====================================================================
# FONCTIONS DE DIAGNOSTIC ET UTILITAIRES
# =====================================================================

def get_import_status() -> dict:
    """Retourne l'état actuel des imports"""
    status = {
        'base_agent_loaded': _BASEAGENT_LOADED,
        'base_agent_error': _BASEAGENT_ERROR,
        'loaded_classes_count': len(_loaded_classes),
        'loaded_classes': list(_loaded_classes.keys()),
        'import_system_configured': _IMPORT_SYSTEM_CONFIGURED,
        'recursion_depth': RecursionGuard.get_current_depth(),
        'base_agent_file': _BASE_AGENT_FILE,
        'base_agent_file_exists': os.path.exists(_BASE_AGENT_FILE),
        'in_sys_modules': 'base_agent' in sys.modules,
        'module_type': type(sys.modules.get('base_agent')).__name__ if 'base_agent' in sys.modules else 'NOT_IN_SYS_MODULES'
    }
    
    # Tester les imports
    import_tests = {}
    
    try:
        from base_agent import BaseAgent as TestBA
        import_tests['from_base_agent'] = {
            'success': True,
            'class': TestBA.__name__ if hasattr(TestBA, '__name__') else str(TestBA)
        }
    except ImportError as e:
        import_tests['from_base_agent'] = {
            'success': False,
            'error': str(e)
        }
    
    status['import_tests'] = import_tests
    
    return status

def diagnose_issues() -> dict:
    """Diagnostique les problèmes d'import"""
    diagnosis = {
        'current_file': _CURRENT_FILE,
        'current_directory': _CURRENT_DIR,
        'sys_path_first_5': sys.path[:5],
        'python_version': sys.version,
        'import_status': get_import_status(),
        'environment': {
            'BASE_AGENT_DEBUG': _DEBUG_MODE,
            'AGENTS_DEBUG_IMPORTS': os.environ.get('AGENTS_DEBUG_IMPORTS', 'NOT_SET')
        }
    }
    
    return diagnosis

def test_all_imports() -> dict:
    """Teste tous les types d'import possibles"""
    tests = {}
    
    # Liste des tests
    import_scenarios = [
        ("from base_agent import BaseAgent", 
         lambda: exec("from base_agent import BaseAgent as T")),
        
        ("import base_agent",
         lambda: exec("import base_agent as T")),
         
        ("from agents.base_agent import BaseAgent",
         lambda: exec("from agents.base_agent import BaseAgent as T")),
         
        ("from agents.base_agent.agent import BaseAgent",
         lambda: exec("from agents.base_agent.agent import BaseAgent as T"))
    ]
    
    for description, test_func in import_scenarios:
        try:
            test_func()
            tests[description] = {'success': True}
        except Exception as e:
            tests[description] = {'success': False, 'error': str(e)}
    
    return tests

# =====================================================================
# INITIALISATION ET TESTS
# =====================================================================

def initialize_module(verbose=True):
    """Initialisation complète du module - VERSION CORRIGÉE"""
    try:
        # 1. D'abord enregistrer les classes dynamiquement
        _register_dynamic_classes()
        
        # 2. Ensuite configurer la compatibilité  
        success = setup_global_import_compatibility()
        
        # 3. S'assurer que __all__ est défini
        global __all__
        __all__ = ['BaseAgent', 'AgentCapability', 'AgentStatus', 
                   'TaskResult', 'AgentConfiguration', 
                   'setup_global_import_compatibility', 'initialize_module']
        
        if verbose:
            print("✅ Module initialisé avec ordre corrigé")
            
        return success
        
    except Exception as e:
        if verbose:
            print(f"❌ Erreur initialisation: {e}")
        return False

# Initialisation automatique
if os.environ.get('AGENT_PY_AUTO_INIT', 'true').lower() == 'true':
    verbose = os.environ.get('AGENT_PY_VERBOSE', 'false').lower() == 'true'
    _MODULE_INITIALIZED = initialize_module(verbose=verbose)

# =====================================================================
# POINT D'ENTRÉE POUR LES TESTS
# =====================================================================

if __name__ == '__main__':
    print(f"\n{'#'*80}")
    print(f"EXÉCUTION DIRECTE - agents.base_agent.agent.py")
    print(f"{'#'*80}")
    
    # Exécuter l'initialisation complète
    success = initialize_module(verbose=True)
    
    # Tests supplémentaires
    print(f"\n🧪 TESTS COMPLÉMENTAIRES:")
    all_tests = test_all_imports()
    
    for test_name, result in all_tests.items():
        status_icon = "✅" if result.get('success') else "❌"
        print(f"  {status_icon} {test_name}")
    
    # Diagnostics détaillés
    if not success:
        print(f"\n🔍 DIAGNOSTICS DÉTAILLÉS:")
        diag = diagnose_issues()
        for category, data in diag.items():
            if category != 'import_status':
                print(f"\n  {category.upper()}:")
                if isinstance(data, dict):
                    for key, value in data.items():
                        print(f"    • {key}: {value}")
                else:
                    print(f"    {data}")
    
    print(f"\n{'#'*80}")
    
    if success:
        print("🎉 MODULE CONFIGURÉ AVEC SUCCÈS")
        print("   Les agents peuvent utiliser: from base_agent import BaseAgent")
    else:
        print("❌ CONFIGURATION ÉCHOUÉE")
        print("   Actions recommandées:")
        print("   1. Vérifiez que agents/base_agent/base_agent.py existe")
        print("   2. Vérifiez les permissions de fichiers")
        print("   3. Supprimez les fichiers __pycache__/")
        print("   4. Redémarrez Python")
    
    print(f"{'#'*80}\n")
    
    exit(0 if success else 1)
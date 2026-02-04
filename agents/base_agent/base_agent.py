"""
BaseAgent - Classe de base pour tous les agents
Version complète et corrigée
"""
import yaml
import logging
import os
import asyncio
from datetime import datetime
from typing import Dict, Any, Optional, List, Callable
import hashlib
import json

logger = logging.getLogger(__name__)

class BaseAgent:
    """Classe de base pour tous les agents du pipeline"""
    
    def __init__(self, config_path: Optional[str] = None, agent_name: Optional[str] = None):
        self.config = {}
        self.name = agent_name or self.__class__.__name__
        self.agent_type = self._get_agent_type()
        self.logger = logging.getLogger(self.name)
        self._initialized = False
        self._capabilities = []
        
        if config_path:
            self.load_config(config_path)
        
        self._initialized = True
        self.logger.info(f"✅ {self.name} initialisé (type: {self.agent_type})")
    
    def _get_agent_type(self) -> str:
        """Détermine le type d'agent basé sur le nom de classe"""
        class_name = self.__class__.__name__
        if 'SubAgent' in class_name:
            return 'sous_agent'
        elif 'Agent' in class_name:
            return 'agent_principal'
        return 'agent_generique'
    
    def load_config(self, config_path: str) -> bool:
        """Charge la configuration depuis un fichier YAML"""
        try:
            if not config_path:
                self.logger.warning("Aucun chemin de configuration fourni")
                self.config = {"agent_name": self.name}
                return False
            
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    loaded_config = yaml.safe_load(f) or {}
                
                # Configuration par défaut
                default_config = {
                    "agent_name": self.name,
                    "agent_type": self.agent_type,
                    "version": "1.0.0",
                    "enabled": True,
                    "capabilities": [],
                    "created_at": datetime.now().isoformat()
                }
                
                # Fusion avec la config chargée
                self.config = {**default_config, **loaded_config}
                self._capabilities = self.config.get("capabilities", [])
                
                self.logger.info(f"✅ Configuration chargée: {config_path}")
                return True
            else:
                self.logger.warning(f"⚠️ Fichier config non trouvé: {config_path}")
                self.config = {"agent_name": self.name, "config_missing": True}
                return False
                
        except yaml.YAMLError as e:
            self.logger.error(f"❌ Erreur YAML dans {config_path}: {e}")
            self.config = {"agent_name": self.name, "yaml_error": str(e)}
            return False
        except Exception as e:
            self.logger.error(f"❌ Erreur chargement config {config_path}: {e}")
            self.config = {"agent_name": self.name, "error": str(e)}
            return False
    
    async def execute(self, task_data: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Exécute une tâche - À surcharger par les agents enfants"""
        try:
            task_type = task_data.get("task_type", "unknown")
            self.logger.info(f"Exécution tâche: {task_type}")
            
            # Réponse par défaut
            return {
                "status": "success",
                "agent": self.name,
                "agent_type": self.agent_type,
                "task": task_type,
                "timestamp": datetime.now().isoformat(),
                "config_loaded": bool(self.config) and not self.config.get("config_missing"),
                "message": f"Tâche '{task_type}' exécutée par {self.name}"
            }
            
        except Exception as e:
            self.logger.error(f"Erreur lors de l'exécution: {e}")
            return {
                "status": "error",
                "agent": self.name,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def health_check(self) -> Dict[str, Any]:
        """Vérifie la santé de l'agent"""
        try:
            health_status = {
                "status": "healthy",
                "agent": self.name,
                "type": self.agent_type,
                "initialized": self._initialized,
                "config_loaded": bool(self.config) and not self.config.get("config_missing"),
                "capabilities": self._capabilities,
                "timestamp": datetime.now().isoformat(),
                "checks": {
                    "config": bool(self.config),
                    "initialized": self._initialized,
                    "methods": {
                        "execute": callable(self.execute),
                        "health_check": callable(self.health_check)
                    }
                }
            }
            
            # Vérifications supplémentaires
            if self.config.get("config_missing"):
                health_status["status"] = "warning"
                health_status["warning"] = "Configuration manquante"
            elif self.config.get("error"):
                health_status["status"] = "error"
                health_status["error"] = self.config.get("error")
            
            return health_status
            
        except Exception as e:
            return {
                "status": "error",
                "agent": self.name,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def get_capabilities(self) -> List[str]:
        """Retourne les capacités de l'agent"""
        return self._capabilities
    
    def add_capability(self, capability: str) -> None:
        """Ajoute une capacité à l'agent"""
        if capability not in self._capabilities:
            self._capabilities.append(capability)
            self.logger.info(f"Capacité ajoutée: {capability}")
    
    def generate_hash(self, data: Any) -> str:
        """Génère un hash MD5 pour les données"""
        try:
            data_str = json.dumps(data, sort_keys=True) if not isinstance(data, str) else data
            return hashlib.md5(data_str.encode()).hexdigest()
        except Exception as e:
            self.logger.error(f"Erreur génération hash: {e}")
            return "hash_error"
    
    def validate_task_data(self, task_data: Dict[str, Any], required_fields: List[str]) -> Dict[str, Any]:
        """Valide les données de tâche"""
        validation_result = {
            "valid": True,
            "missing_fields": [],
            "errors": []
        }
        
        for field in required_fields:
            if field not in task_data:
                validation_result["valid"] = False
                validation_result["missing_fields"].append(field)
        
        return validation_result
    
    async def execute_with_timeout(self, task_data: Dict[str, Any], context: Dict[str, Any], 
                                 timeout: int = 30) -> Dict[str, Any]:
        """Exécute une tâche avec timeout"""
        try:
            return await asyncio.wait_for(self.execute(task_data, context), timeout=timeout)
        except asyncio.TimeoutError:
            self.logger.error(f"Timeout sur la tâche: {task_data.get('task_type', 'unknown')}")
            return {
                "status": "timeout",
                "agent": self.name,
                "task": task_data.get("task_type", "unknown"),
                "message": f"Timeout après {timeout} secondes"
            }
        except Exception as e:
            self.logger.error(f"Erreur avec timeout: {e}")
            return {
                "status": "error",
                "agent": self.name,
                "error": str(e)
            }
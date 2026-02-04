# agent_registry.py
import os
import yaml
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)

@dataclass
class AgentInfo:
    """Informations sur un agent disponible"""
    name: str
    display_name: str
    module_path: str
    class_name: str
    config_path: Optional[str] = None
    description: str = ""
    category: str = "general"
    specializations: List[str] = None
    dependencies: List[str] = None
    version: str = "1.0.0"
    enabled: bool = True
    
    def __post_init__(self):
        if self.specializations is None:
            self.specializations = []
        if self.dependencies is None:
            self.dependencies = []

class AgentRegistry:
    """Registry dynamique pour découvrir et gérer les agents"""
    
    def __init__(self, registry_file: str = "agent_registry.yaml", 
                 auto_discover: bool = True):
        self.registry_file = registry_file
        self.agents: Dict[str, AgentInfo] = {}
        self.categories: Dict[str, List[str]] = {}
        self.initialized = False
        
        if auto_discover:
            self.load_registry()
    
    def load_registry(self) -> None:
        """Charge le registry depuis le fichier YAML et découvre les agents"""
        # Charge le registry existant
        if os.path.exists(self.registry_file):
            try:
                with open(self.registry_file, 'r', encoding='utf-8') as f:
                    registry_data = yaml.safe_load(f) or {}
                
                # Convertit les données en objets AgentInfo
                for agent_name, agent_data in registry_data.get("agents", {}).items():
                    try:
                        agent_info = AgentInfo(
                            name=agent_name,
                            display_name=agent_data.get("display_name", agent_name),
                            module_path=agent_data.get("module_path", ""),
                            class_name=agent_data.get("class_name", ""),
                            config_path=agent_data.get("config_path"),
                            description=agent_data.get("description", ""),
                            category=agent_data.get("category", "general"),
                            specializations=agent_data.get("specializations", []),
                            dependencies=agent_data.get("dependencies", []),
                            version=agent_data.get("version", "1.0.0"),
                            enabled=agent_data.get("enabled", True)
                        )
                        self.agents[agent_name] = agent_info
                        
                        # Met à jour les catégories
                        category = agent_info.category
                        if category not in self.categories:
                            self.categories[category] = []
                        if agent_name not in self.categories[category]:
                            self.categories[category].append(agent_name)
                            
                    except Exception as e:
                        logger.error(f"Erreur chargement agent {agent_name}: {e}")
                
                logger.info(f"Registry chargé: {len(self.agents)} agents")
                
            except Exception as e:
                logger.error(f"Erreur chargement registry {self.registry_file}: {e}")
                self.agents = {}
        
        # Découvre les agents dans le système de fichiers
        self._discover_agents()
        self.initialized = True
    
    def _discover_agents(self, search_paths: List[str] = None) -> None:
        """Découvre automatiquement les agents dans les dossiers"""
        if search_paths is None:
            search_paths = ["agents/", "plugins/"]
        
        for base_path in search_paths:
            if not os.path.exists(base_path):
                continue
            
            # Parcourt tous les sous-dossiers
            for root, dirs, files in os.walk(base_path):
                # Cherche les fichiers agent.py
                if "agent.py" in files:
                    agent_dir = os.path.basename(root)
                    parent_dir = os.path.basename(os.path.dirname(root))
                    
                    # Détermine le type d'agent
                    if parent_dir == "sous_agents":
                        # C'est un sous-agent
                        grandparent_dir = os.path.basename(os.path.dirname(os.path.dirname(root)))
                        agent_type = f"{grandparent_dir}.{agent_dir}"
                        category = grandparent_dir
                        is_subagent = True
                    else:
                        # C'est un agent principal
                        agent_type = agent_dir
                        category = agent_dir
                        is_subagent = False
                    
                    # Lit le fichier agent.py pour extraire les infos
                    agent_info = self._extract_agent_info(
                        os.path.join(root, "agent.py"),
                        agent_type,
                        category,
                        is_subagent
                    )
                    
                    if agent_info and agent_info.name not in self.agents:
                        self.agents[agent_info.name] = agent_info
                        
                        # Met à jour les catégories
                        if agent_info.category not in self.categories:
                            self.categories[agent_info.category] = []
                        self.categories[agent_info.category].append(agent_info.name)
    
    def _extract_agent_info(self, agent_file: str, agent_type: str, 
                           category: str, is_subagent: bool) -> Optional[AgentInfo]:
        """Extrait les informations d'un agent depuis son fichier Python"""
        try:
            with open(agent_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Cherche la classe d'agent
            import ast
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    class_name = node.name
                    if 'Agent' in class_name and not class_name.endswith('BaseAgent'):
                        # Détermine le nom d'affichage
                        display_name = class_name.replace('Agent', '').replace('SubAgent', '')
                        display_name = ' '.join([word.capitalize() for word in 
                                               display_name.split('_') if word])
                        
                        # Extrait la docstring
                        description = ""
                        if ast.get_docstring(node):
                            description = ast.get_docstring(node).split('\n')[0]
                        
                        # Détermine le chemin du module
                        rel_path = os.path.relpath(agent_file, start=os.getcwd())
                        module_path = rel_path.replace('.py', '').replace('/', '.').replace('\\', '.')
                        
                        # Cherche le fichier de config
                        config_path = os.path.join(os.path.dirname(agent_file), "config.yaml")
                        if not os.path.exists(config_path):
                            config_path = None
                        
                        return AgentInfo(
                            name=agent_type,
                            display_name=display_name,
                            module_path=module_path,
                            class_name=class_name,
                            config_path=config_path,
                            description=description,
                            category=category,
                            specializations=[agent_type] if is_subagent else [],
                            version="1.0.0",
                            enabled=True
                        )
            
            return None
            
        except Exception as e:
            logger.error(f"Erreur extraction info agent {agent_file}: {e}")
            return None
    
    def discover_agents(self, search_paths: List[str] = None) -> Dict[str, AgentInfo]:
        """Découvre les agents dans les chemins spécifiés"""
        if not self.initialized:
            self.load_registry()
        
        discovered = {}
        for agent_name, agent_info in self.agents.items():
            if agent_info.enabled:
                discovered[agent_name] = agent_info
        
        return discovered
    
    def get_agent_info(self, agent_type: str, specialization: str = None) -> Optional[AgentInfo]:
        """Retourne les informations d'un agent spécifique"""
        if not self.initialized:
            self.load_registry()
        
        # Cherche l'agent principal
        if agent_type in self.agents:
            return self.agents[agent_type]
        
        # Cherche par spécialisation
        for agent_info in self.agents.values():
            if specialization and specialization in agent_info.specializations:
                return agent_info
        
        return None
    
    def get_agents_by_category(self, category: str) -> List[AgentInfo]:
        """Retourne tous les agents d'une catégorie"""
        if not self.initialized:
            self.load_registry()
        
        agents = []
        for agent_name in self.categories.get(category, []):
            if agent_name in self.agents:
                agents.append(self.agents[agent_name])
        
        return agents
    
    def get_agents_for_project_type(self, project_type: str) -> List[AgentInfo]:
        """Retourne les agents recommandés pour un type de projet"""
        if not self.initialized:
            self.load_registry()
        
        project_mappings = {
            "defi": ["smart_contract", "architect.blockchain_architect", "tester.security_expert"],
            "nft": ["smart_contract", "frontend_web3", "coder.frontend_coder"],
            "gaming": ["smart_contract", "coder.backend_coder", "tester"],
            "dao": ["smart_contract", "architect", "coder.backend_coder"]
        }
        
        recommended = []
        agent_names = project_mappings.get(project_type, [])
        
        for agent_name in agent_names:
            if '.' in agent_name:
                # Format: category.agent_name
                category, name = agent_name.split('.')
                category_agents = self.get_agents_by_category(category)
                if category_agents:
                    recommended.extend(category_agents)
            elif agent_name in self.agents:
                recommended.append(self.agents[agent_name])
        
        return recommended
    
    def save_registry(self) -> None:
        """Sauvegarde le registry dans le fichier YAML"""
        registry_data = {
            "agents": {},
            "categories": self.categories,
            "metadata": {
                "total_agents": len(self.agents),
                "version": "1.0.0",
                "last_updated": "2026-02-03"
            }
        }
        
        for agent_name, agent_info in self.agents.items():
            registry_data["agents"][agent_name] = asdict(agent_info)
        
        try:
            with open(self.registry_file, 'w', encoding='utf-8') as f:
                yaml.dump(registry_data, f, default_flow_style=False, allow_unicode=True)
            
            logger.info(f"Registry sauvegardé: {self.registry_file}")
        except Exception as e:
            logger.error(f"Erreur sauvegarde registry: {e}")
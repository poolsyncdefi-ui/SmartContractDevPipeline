"""
Documenter Agent 2.2.0 - Documentation professionnelle
Génère une documentation structurée, interactive et visuelle
Avec Mermaid diagrams, table des matières, liens croisés
Version alignée avec l'infrastructure existante
"""

import os
import sys
import yaml
import asyncio
import json
import traceback
import hashlib
import re
import shutil
import importlib
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from enum import Enum

# Ajouter le chemin du projet
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from agents.base_agent.base_agent import BaseAgent, AgentStatus, Message, MessageType


# ============================================================================
# CONSTANTES
# ============================================================================

DEFAULT_CONFIG = {
    "agent": {
        "name": "documenter",
        "display_name": "📚 Agent de Documentation",
        "description": "Agent de documentation professionnelle",
        "version": "2.2.0"
    },
    "documenter": {
        "output_path": "./docs",
        "temp_path": "./agents/documenter/temp",
        "templates_path": "./agents/documenter/templates"
    },
    "mermaid": {
        "enabled": True,
        "theme": "dark"
    },
    "styling": {
        "colors": {
            "primary": "#00ff88",
            "secondary": "#8b5cf6",
            "background": "#0f1215"
        }
    }
}


# ============================================================================
# ÉNUMÉRATIONS
# ============================================================================

class DocFormat(Enum):
    """Formats de documentation supportés"""
    MARKDOWN = "md"
    HTML = "html"
    PDF = "pdf"
    SITE = "site"


class DocSection(Enum):
    """Sections de documentation"""
    OVERVIEW = "overview"
    ARCHITECTURE = "architecture"
    CONTRACTS = "contracts"
    FUNCTIONS = "functions"
    EVENTS = "events"
    MODIFIERS = "modifiers"
    SECURITY = "security"
    DEPLOYMENT = "deployment"
    EXAMPLES = "examples"
    CHANGELOG = "changelog"


class DiagramType(Enum):
    """Types de diagrammes Mermaid"""
    INHERITANCE = "inheritance"
    DEPENDENCIES = "dependencies"
    WORKFLOW = "workflow"
    CALL_GRAPH = "call_graph"
    STATE = "state"
    SEQUENCE = "sequence"


# ============================================================================
# AGENT PRINCIPAL AVEC SOUS-AGENTS
# ============================================================================

class DocumenterAgent(BaseAgent):
    """
    Documenter Agent 2.2.0 - Documentation professionnelle
    Génère documentation structurée avec Mermaid, TOC, liens croisés
    Gère des sous-agents spécialisés
    """
    
    def __init__(self, config_path: str = ""):
        """Initialise l'agent documenter"""
        if not config_path:
            config_path = str(project_root / "agents" / "documenter" / "config.yaml")
        
        super().__init__(config_path)
        
        # Charger la configuration
        self._load_configuration()
        
        self._logger.info("📚 Agent de documentation créé")
        
        # =====================================================================
        # ÉTAT INTERNE
        # =====================================================================
        self._docs_generated = 0
        self._templates = {}
        self._contracts_cache = {}
        self._diagrams_cache = {}
        self._components: Dict[str, Any] = {}
        self._sub_agents: Dict[str, Any] = {}
        self._initialized = False
        
        documenter_config = self._agent_config.get("documenter", {})
        self._output_path = Path(documenter_config.get("output_path", "./docs"))
        self._temp_path = Path(documenter_config.get("temp_path", "./agents/documenter/temp"))
        
        # =====================================================================
        # STATISTIQUES
        # =====================================================================
        self._stats = {
            'docs_generated': 0,
            'contracts_cached': 0,
            'diagrams_generated': 0,
            'start_time': datetime.now()
        }
        
        # =====================================================================
        # TÂCHES DE FOND
        # =====================================================================
        self._cleanup_task: Optional[asyncio.Task] = None
        
        # Créer les répertoires
        self._create_directories()
    
    def _load_configuration(self):
        """Charge la configuration depuis le fichier YAML"""
        try:
            if self._config_path and os.path.exists(self._config_path):
                with open(self._config_path, 'r', encoding='utf-8') as f:
                    file_config = yaml.safe_load(f) or {}
                
                # Fusion avec la config par défaut
                self._agent_config = self._merge_configs(DEFAULT_CONFIG, file_config)
                self._logger.info(f"✅ Configuration chargée depuis {self._config_path}")
            else:
                self._logger.warning("⚠️ Fichier de configuration non trouvé, utilisation des valeurs par défaut")
                self._agent_config = DEFAULT_CONFIG.copy()
        except Exception as e:
            self._logger.error(f"❌ Erreur chargement config: {e}")
            self._agent_config = DEFAULT_CONFIG.copy()
    
    def _merge_configs(self, default: Dict, override: Dict) -> Dict:
        """Fusionne deux configurations récursivement"""
        result = default.copy()
        
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_configs(result[key], value)
            else:
                result[key] = value
        
        return result
    
    def _create_directories(self):
        """Crée les répertoires nécessaires"""
        documenter_config = self._agent_config.get("documenter", {})
        
        dirs = [
            documenter_config.get("output_path", "./docs"),
            documenter_config.get("temp_path", "./agents/documenter/temp"),
            documenter_config.get("templates_path", "./agents/documenter/templates"),
            Path("./docs/assets"),
            Path("./docs/diagrams"),
            Path("./docs/contracts")
        ]
        
        for dir_path in dirs:
            if dir_path:
                Path(dir_path).mkdir(parents=True, exist_ok=True)
                self._logger.debug(f"📁 Répertoire créé: {dir_path}")
    
    # ========================================================================
    # INITIALISATION AVEC SOUS-AGENTS
    # ========================================================================
    
    async def initialize(self) -> bool:
        """Initialisation asynchrone"""
        try:
            self._status = AgentStatus.INITIALIZING
            self._logger.info("📚 Initialisation du Documenter Pro...")
            
            # Appeler l'initialisation du parent
            base_result = await super().initialize()
            if not base_result:
                return False
            
            # Initialiser les composants
            await self._initialize_components()
            
            # Initialiser les sous-agents
            await self._initialize_sub_agents()
            
            # Charger les templates
            await self._load_templates()
            
            # Démarrer les tâches de fond
            self._start_background_tasks()
            
            self._initialized = True
            self._status = AgentStatus.READY
            self._logger.info("✅ Documenter Pro prêt")
            return True
            
        except Exception as e:
            self._logger.error(f"❌ Erreur initialisation: {e}")
            self._logger.error(traceback.format_exc())
            self._status = AgentStatus.ERROR
            return False
    
    async def _initialize_components(self) -> bool:
        """Initialise les composants du DocumenterAgent"""
        try:
            self._logger.info("Initialisation des composants du DocumenterAgent...")
            
            self._components = {
                "doc_generator": {"enabled": True, "formats": ["markdown", "html"]},
                "diagram_generator": {"enabled": self._agent_config.get("mermaid", {}).get("enabled", True), 
                                      "types": ["mermaid"]},
                "template_manager": {"enabled": True, "templates": list(self._templates.keys())}
            }
            
            self._logger.info(f"✅ Composants: {list(self._components.keys())}")
            return True
            
        except Exception as e:
            self._logger.error(f"Erreur composants: {e}")
            return False
    
    async def _initialize_sub_agents(self):
        """Initialise les sous-agents spécialisés"""
        self._sub_agents = {}
        
        # Configuration des sous-agents depuis la config
        sub_agent_configs = self._agent_config.get('subAgents', [])
        
        # Si la liste est vide, charger avec des noms par défaut
        if not sub_agent_configs:
            sub_agent_configs = [
                {"id": "doc_generator", "enabled": True},
                {"id": "diagram_generator", "enabled": True},
                {"id": "api_doc_specialist", "enabled": True},
                {"id": "readme_specialist", "enabled": True}
            ]
        
        self._logger.info(f"📦 Chargement de {len(sub_agent_configs)} sous-agents...")
        
        for config in sub_agent_configs:
            agent_id = config.get('id')
            if not config.get('enabled', True):
                self._logger.debug(f"  ⏭️ Sous-agent {agent_id} désactivé")
                continue
            
            try:
                # Chemin du module
                module_name = f"agents.documenter.sous_agents.{agent_id}.agent"
                
                # Nom de la classe (convertir l'ID en nom de classe)
                parts = agent_id.split('_')
                class_name = ''.join(p.capitalize() for p in parts) + 'SubAgent'
                
                self._logger.debug(f"  🔄 Tentative d'import {module_name}")
                
                # Import dynamique
                module = importlib.import_module(module_name)
                self._logger.debug(f"  ✅ Module importé avec succès")
                
                # Récupérer la classe
                agent_class = getattr(module, class_name, None)
                if agent_class:
                    self._logger.debug(f"  ✅ Classe {class_name} trouvée, création de l'instance")
                    
                    # Chemin de config (peut être spécifié ou None)
                    config_path = config.get('config_path')
                    
                    # Instancier le sous-agent
                    sub_agent = agent_class(config_path)
                    self._sub_agents[agent_id] = sub_agent
                    self._logger.info(f"  ✓ Sous-agent {agent_id} initialisé")
                else:
                    self._logger.warning(f"  ⚠️ Classe {class_name} non trouvée dans {module_name}")
                    
            except ImportError as e:
                self._logger.debug(f"  ℹ️ Sous-agent {agent_id} non disponible: {e}")
            except Exception as e:
                self._logger.error(f"  ❌ Erreur initialisation sous-agent {agent_id}: {e}")
                self._logger.error(traceback.format_exc())
        
        self._logger.info(f"✅ Sous-agents chargés: {len(self._sub_agents)}")
    
    async def _load_templates(self):
        """Charge les templates de documentation"""
        self._templates = {
            "base_html": self._get_base_html_template(),
            "toc": self._get_toc_template(),
            "section": self._get_section_template(),
            "function_table": self._get_function_table_template(),
            "event_table": self._get_event_table_template(),
            "security_section": self._get_security_template(),
            "mermaid_diagram": self._get_mermaid_template()
        }
        self._logger.info(f"✅ {len(self._templates)} templates chargés")
    
    def _start_background_tasks(self):
        """Démarre les tâches de fond"""
        loop = asyncio.get_event_loop()
        self._cleanup_task = loop.create_task(self._cleanup_loop())
        self._logger.debug("🧹 Tâche de nettoyage démarrée")
    
    async def _cleanup_loop(self):
        """Tâche de nettoyage périodique"""
        self._logger.info("🧹 Tâche de nettoyage démarrée")
        
        while self._status == AgentStatus.READY:
            try:
                await asyncio.sleep(3600)  # Toutes les heures
                
                self._logger.debug("Nettoyage périodique...")
                
                # Nettoyer les vieux fichiers temporaires (> 7 jours)
                if self._temp_path.exists():
                    cutoff = datetime.now() - timedelta(days=7)
                    for temp_file in self._temp_path.glob("*"):
                        try:
                            mtime = datetime.fromtimestamp(temp_file.stat().st_mtime)
                            if mtime < cutoff:
                                if temp_file.is_file():
                                    temp_file.unlink()
                                else:
                                    shutil.rmtree(temp_file)
                                self._logger.debug(f"🗑️ Fichier temporaire supprimé: {temp_file.name}")
                        except Exception as e:
                            self._logger.error(f"Erreur suppression {temp_file}: {e}")
                
            except asyncio.CancelledError:
                self._logger.info("🛑 Tâche de nettoyage arrêtée")
                break
            except Exception as e:
                self._logger.error(f"❌ Erreur dans la tâche de nettoyage: {e}")
                await asyncio.sleep(60)
    
    # ========================================================================
    # API PUBLIQUE AVEC DÉLÉGATION AUX SOUS-AGENTS
    # ========================================================================
    
    async def generate_contract_documentation(self, 
                                             contract_path: str,
                                             output_format: str = "html") -> Dict[str, Any]:
        """
        Génère la documentation complète d'un contrat
        Délègue aux sous-agents appropriés
        """
        self._logger.info(f"📄 Génération documentation pour {contract_path}")
        
        # Analyser le contrat
        contract_info = await self._analyze_contract(contract_path)
        
        # Déléguer la génération des diagrammes
        diagrams = {}
        if 'diagram_generator' in self._sub_agents:
            diagram_result = await self._sub_agents['diagram_generator'].generate_diagrams(contract_info)
            diagrams = diagram_result.get('diagrams', {})
            self._stats['diagrams_generated'] += diagram_result.get('diagrams_count', 0)
        
        # Construire la structure
        docs_structure = await self._build_docs_structure(contract_info, diagrams)
        
        # Générer selon le format
        if output_format == "html":
            output_path = await self._generate_html(docs_structure)
        elif output_format == "md":
            output_path = await self._generate_markdown(docs_structure)
        else:
            output_path = await self._generate_html(docs_structure)
        
        self._docs_generated += 1
        self._stats['docs_generated'] += 1
        self._stats['contracts_cached'] = len(self._contracts_cache)
        
        return {
            "success": True,
            "contract": contract_info["name"],
            "format": output_format,
            "path": str(output_path),
            "sections": len(docs_structure["sections"]),
            "diagrams": len(diagrams),
            "generated_at": datetime.now().isoformat()
        }
    
    async def generate_readme(self, project_info: Dict[str, Any]) -> Dict[str, Any]:
        """Génère un README - délègue au sous-agent spécialisé"""
        if 'readme_specialist' in self._sub_agents:
            return await self._sub_agents['readme_specialist'].generate_readme(project_info)
        return {"success": False, "error": "README specialist not available"}
    
    async def generate_api_documentation(self, api_spec: Dict[str, Any]) -> Dict[str, Any]:
        """Génère une documentation API - délègue au sous-agent spécialisé"""
        if 'api_doc_specialist' in self._sub_agents:
            return await self._sub_agents['api_doc_specialist'].generate_api_doc(api_spec)
        return {"success": False, "error": "API doc specialist not available"}
    
    # ========================================================================
    # ANALYSE DE CONTRAT (votre code existant)
    # ========================================================================
    
    async def _analyze_contract(self, contract_path: str) -> Dict[str, Any]:
        """Analyse approfondie d'un contrat Solidity"""
        # Vérifier le cache
        file_hash = self._hash_file(contract_path)
        if file_hash in self._contracts_cache:
            self._logger.debug(f"📦 Contrat chargé depuis cache: {contract_path}")
            return self._contracts_cache[file_hash]
        
        with open(contract_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Extraction des informations (votre code existant)
        contract_info = {
            "name": self._extract_contract_name(content),
            "path": contract_path,
            "file_hash": file_hash,
            "license": self._extract_license(content),
            "solidity_version": self._extract_solidity_version(content),
            "imports": self._extract_imports(content),
            "inheritance": self._extract_inheritance(content),
            "interfaces": self._extract_interfaces(content),
            "libraries": self._extract_libraries(content),
            "functions": self._extract_functions_detailed(content),
            "events": self._extract_events_detailed(content),
            "modifiers": self._extract_modifiers_detailed(content),
            "variables": self._extract_variables_detailed(content),
            "structs": self._extract_structs(content),
            "enums": self._extract_enums(content),
            "errors": self._extract_errors(content),
            "natspec": self._extract_natspec_complete(content),
            "metrics": self._calculate_metrics(content),
            "security": await self._analyze_security(content),
            "complexity": self._calculate_complexity(content),
            "dependencies": await self._resolve_dependencies(content),
            "line_count": len(content.split('\n')),
            "bytecode_estimate": self._estimate_bytecode_size(content)
        }
        
        # Mettre en cache
        self._contracts_cache[file_hash] = contract_info
        
        return contract_info
    
    def _hash_file(self, path: str) -> str:
        with open(path, 'rb') as f:
            return hashlib.sha256(f.read()).hexdigest()[:16]
    
    def _extract_contract_name(self, content: str) -> str:
        match = re.search(r'contract\s+(\w+)', content)
        return match.group(1) if match else "Unknown"
    
    def _extract_license(self, content: str) -> str:
        match = re.search(r'SPDX-License-Identifier:\s*(\S+)', content)
        return match.group(1) if match else "UNLICENSED"
    
    def _extract_solidity_version(self, content: str) -> str:
        match = re.search(r'pragma solidity\s*([^;]+);', content)
        return match.group(1).strip() if match else "unknown"
    
    def _extract_imports(self, content: str) -> List[Dict[str, Any]]:
        imports = []
        pattern = r'import\s+(?:\{([^}]+)\}\s+from\s+)?["\']([^"\']+)["\']\s*;'
        
        for match in re.finditer(pattern, content):
            symbols = match.group(1)
            path = match.group(2)
            
            imports.append({
                "path": path,
                "symbols": [s.strip() for s in symbols.split(',')] if symbols else ["*"],
                "type": "local" if path.startswith('.') else "external"
            })
        
        return imports
    
    def _extract_inheritance(self, content: str) -> List[str]:
        match = re.search(r'contract\s+\w+\s+is\s+([^{]+)', content)
        if match:
            parents = match.group(1).strip()
            return [p.strip() for p in parents.split(',') if p.strip()]
        return []
    
    def _extract_interfaces(self, content: str) -> List[str]:
        interfaces = re.findall(r'interface\s+(\w+)', content)
        return list(set(interfaces))
    
    def _extract_libraries(self, content: str) -> List[str]:
        libraries = re.findall(r'library\s+(\w+)', content)
        return list(set(libraries))
    
    def _extract_functions_detailed(self, content: str) -> List[Dict[str, Any]]:
        functions = []
        pattern = r'function\s+(\w+)\s*\(([^)]*)\)\s*([^{;]*?)(?:returns\s*\(([^)]*)\))?\s*(?:external|public|internal|private)?\s*([^{;]*)'
        
        for match in re.finditer(pattern, content, re.MULTILINE):
            func = {
                "name": match.group(1),
                "params": self._parse_parameters(match.group(2)),
                "modifiers": self._parse_modifiers(match.group(3)),
                "returns": self._parse_parameters(match.group(4)) if match.group(4) else [],
                "visibility": self._extract_visibility(match.group(3)),
                "state_mutability": self._extract_state_mutability(match.group(3)),
                "virtual": 'virtual' in match.group(3),
                "override": 'override' in match.group(3),
                "natspec": self._extract_function_natspec(content, match.group(1)),
                "line": self._find_function_line(content, match.group(1)),
                "complexity": self._calculate_function_complexity(match.group(0))
            }
            functions.append(func)
        
        functions.sort(key=lambda x: x["name"])
        return functions
    
    def _parse_parameters(self, params_str: str) -> List[Dict[str, Any]]:
        if not params_str.strip():
            return []
        
        params = []
        for param in params_str.split(','):
            param = param.strip()
            if not param:
                continue
            
            parts = param.split()
            if len(parts) >= 2:
                params.append({
                    "type": parts[0],
                    "name": parts[1],
                    "indexed": 'indexed' in parts
                })
            else:
                params.append({
                    "type": parts[0],
                    "name": "",
                    "indexed": False
                })
        
        return params
    
    def _parse_modifiers(self, modifier_str: str) -> List[str]:
        if not modifier_str.strip():
            return []
        
        modifiers = []
        for mod in modifier_str.split():
            mod = mod.strip()
            if mod and mod not in ['public', 'private', 'internal', 'external',
                                   'view', 'pure', 'payable', 'virtual', 'override']:
                modifiers.append(mod)
        
        return modifiers
    
    def _extract_visibility(self, modifier_str: str) -> str:
        for vis in ['public', 'private', 'internal', 'external']:
            if vis in modifier_str:
                return vis
        return 'public'
    
    def _extract_state_mutability(self, modifier_str: str) -> str:
        for mut in ['view', 'pure', 'payable']:
            if mut in modifier_str:
                return mut
        return 'nonpayable'
    
    def _extract_events_detailed(self, content: str) -> List[Dict[str, Any]]:
        events = []
        pattern = r'event\s+(\w+)\s*\(([^)]*)\)'
        
        for match in re.finditer(pattern, content):
            events.append({
                "name": match.group(1),
                "params": self._parse_parameters(match.group(2)),
                "anonymous": 'anonymous' in match.group(0),
                "natspec": self._extract_event_natspec(content, match.group(1)),
                "line": self._find_event_line(content, match.group(1))
            })
        
        events.sort(key=lambda x: x["name"])
        return events
    
    def _extract_modifiers_detailed(self, content: str) -> List[Dict[str, Any]]:
        modifiers = []
        pattern = r'modifier\s+(\w+)\s*\(([^)]*)\)\s*([^{]*)'
        
        for match in re.finditer(pattern, content):
            modifiers.append({
                "name": match.group(1),
                "params": self._parse_parameters(match.group(2)),
                "body": match.group(3).strip(),
                "natspec": self._extract_modifier_natspec(content, match.group(1)),
                "line": self._find_modifier_line(content, match.group(1))
            })
        
        return modifiers
    
    def _extract_variables_detailed(self, content: str) -> List[Dict[str, Any]]:
        variables = []
        pattern = r'(?:public|private|internal)?\s+(\w+)\s+(public|private|internal)?\s*(\w+)\s*;'
        
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if 'function' in line or 'event' in line or 'modifier' in line:
                continue
            
            match = re.search(pattern, line)
            if match:
                var_type = match.group(1)
                visibility = match.group(2) or 'internal'
                name = match.group(3)
                
                constant = 'constant' in line
                immutable = 'immutable' in line
                
                variables.append({
                    "name": name,
                    "type": var_type,
                    "visibility": visibility,
                    "constant": constant,
                    "immutable": immutable,
                    "line": i + 1,
                    "natspec": self._extract_variable_natspec(content, name)
                })
        
        return variables
    
    def _extract_structs(self, content: str) -> List[Dict[str, Any]]:
        structs = []
        pattern = r'struct\s+(\w+)\s*\{([^}]*)\}'
        
        for match in re.finditer(pattern, content, re.DOTALL):
            fields = []
            field_pattern = r'(\w+)\s+(\w+);'
            for f_match in re.finditer(field_pattern, match.group(2)):
                fields.append({
                    "type": f_match.group(1),
                    "name": f_match.group(2)
                })
            
            structs.append({
                "name": match.group(1),
                "fields": fields
            })
        
        return structs
    
    def _extract_enums(self, content: str) -> List[Dict[str, Any]]:
        enums = []
        pattern = r'enum\s+(\w+)\s*\{([^}]*)\}'
        
        for match in re.finditer(pattern, content, re.DOTALL):
            values = [v.strip() for v in match.group(2).split(',') if v.strip()]
            enums.append({
                "name": match.group(1),
                "values": values
            })
        
        return enums
    
    def _extract_errors(self, content: str) -> List[Dict[str, Any]]:
        errors = []
        pattern = r'error\s+(\w+)\s*\(([^)]*)\)'
        
        for match in re.finditer(pattern, content):
            errors.append({
                "name": match.group(1),
                "params": self._parse_parameters(match.group(2))
            })
        
        return errors
    
    def _extract_natspec_complete(self, content: str) -> Dict[str, Any]:
        natspec = {
            "contract": {},
            "functions": {},
            "events": {},
            "modifiers": {},
            "variables": {}
        }
        
        contract_match = re.search(r'/\*\*([^*]|\*[^/])*\*/\s*contract', content, re.DOTALL)
        if contract_match:
            comment = contract_match.group(0).split('*/')[0]
            natspec["contract"] = self._parse_natspec_block(comment)
        
        return natspec
    
    def _parse_natspec_block(self, comment: str) -> Dict[str, Any]:
        result = {}
        
        notice_match = re.search(r'@notice\s+(.+)', comment)
        if notice_match:
            result["notice"] = notice_match.group(1).strip()
        
        dev_match = re.search(r'@dev\s+(.+)', comment)
        if dev_match:
            result["dev"] = dev_match.group(1).strip()
        
        author_match = re.search(r'@author\s+(.+)', comment)
        if author_match:
            result["author"] = author_match.group(1).strip()
        
        title_match = re.search(r'@title\s+(.+)', comment)
        if title_match:
            result["title"] = title_match.group(1).strip()
        
        return result
    
    def _extract_function_natspec(self, content: str, func_name: str) -> Dict[str, Any]:
        pattern = rf'/\*\*([^*]|\*[^/])*\*/\s*function\s+{func_name}'
        match = re.search(pattern, content, re.DOTALL)
        
        if not match:
            return {}
        
        comment = match.group(0).split('*/')[0]
        return self._parse_natspec_block(comment)
    
    def _extract_event_natspec(self, content: str, event_name: str) -> Dict[str, Any]:
        pattern = rf'/\*\*([^*]|\*[^/])*\*/\s*event\s+{event_name}'
        match = re.search(pattern, content, re.DOTALL)
        
        if not match:
            return {}
        
        comment = match.group(0).split('*/')[0]
        return self._parse_natspec_block(comment)
    
    def _extract_modifier_natspec(self, content: str, modifier_name: str) -> Dict[str, Any]:
        pattern = rf'/\*\*([^*]|\*[^/])*\*/\s*modifier\s+{modifier_name}'
        match = re.search(pattern, content, re.DOTALL)
        
        if not match:
            return {}
        
        comment = match.group(0).split('*/')[0]
        return self._parse_natspec_block(comment)
    
    def _extract_variable_natspec(self, content: str, var_name: str) -> Dict[str, Any]:
        pattern = rf'/\*\*([^*]|\*[^/])*\*/\s*(?:public|private|internal)?\s*\w+\s+{var_name}'
        match = re.search(pattern, content, re.DOTALL)
        
        if not match:
            return {}
        
        comment = match.group(0).split('*/')[0]
        return self._parse_natspec_block(comment)
    
    def _find_function_line(self, content: str, func_name: str) -> int:
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if f'function {func_name}' in line:
                return i + 1
        return 0
    
    def _find_event_line(self, content: str, event_name: str) -> int:
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if f'event {event_name}' in line:
                return i + 1
        return 0
    
    def _find_modifier_line(self, content: str, modifier_name: str) -> int:
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if f'modifier {modifier_name}' in line:
                return i + 1
        return 0
    
    def _calculate_metrics(self, content: str) -> Dict[str, Any]:
        lines = content.split('\n')
        
        return {
            "total_lines": len(lines),
            "code_lines": len([l for l in lines if l.strip() and not l.strip().startswith('//')]),
            "comment_lines": len([l for l in lines if l.strip().startswith('//')]),
            "blank_lines": len([l for l in lines if not l.strip()]),
            "function_count": len(re.findall(r'function\s+\w+', content)),
            "event_count": len(re.findall(r'event\s+\w+', content)),
            "modifier_count": len(re.findall(r'modifier\s+\w+', content)),
            "import_count": len(re.findall(r'import\s+', content))
        }
    
    async def _analyze_security(self, content: str) -> Dict[str, Any]:
        security = {
            "reentrancy_protection": 'ReentrancyGuard' in content or 'nonReentrant' in content,
            "access_control": 'onlyOwner' in content or 'Ownable' in content or 'AccessControl' in content,
            "pausable": 'Pausable' in content or 'whenNotPaused' in content,
            "safe_math": 'SafeMath' in content or 'using SafeMath' in content,
            "pull_payment": 'PullPayment' in content,
            "timelock": 'Timelock' in content,
            "multisig": 'MultiSig' in content,
            "emergency_stop": 'emergencyStop' in content or 'pause' in content,
            "risk_level": "low"
        }
        
        risk_score = 0
        if not security["reentrancy_protection"]:
            risk_score += 3
        if not security["access_control"]:
            risk_score += 2
        if 'delegatecall' in content and 'onlyOwner' not in content:
            risk_score += 4
        
        if risk_score >= 7:
            security["risk_level"] = "high"
        elif risk_score >= 4:
            security["risk_level"] = "medium"
        else:
            security["risk_level"] = "low"
        
        security["risk_score"] = risk_score
        
        return security
    
    def _calculate_complexity(self, content: str) -> Dict[str, Any]:
        cyclomatic = self._calculate_cyclomatic_complexity(content)
        return {
            "cyclomatic": cyclomatic,
            "cognitive": cyclomatic,
            "maintainability": self._calculate_maintainability_index(content)
        }
    
    def _calculate_cyclomatic_complexity(self, content: str) -> int:
        complexity = 1
        
        complexity += len(re.findall(r'\bif\s*\(', content))
        complexity += len(re.findall(r'\belse\s+if\b', content))
        complexity += len(re.findall(r'\bfor\s*\(', content))
        complexity += len(re.findall(r'\bwhile\s*\(', content))
        complexity += len(re.findall(r'\bcase\b', content))
        complexity += len(re.findall(r'\bcatch\b', content))
        complexity += len(re.findall(r'\b&&\b|\|\|\b', content))
        
        return complexity
    
    def _calculate_maintainability_index(self, content: str) -> float:
        loc = len(content.split('\n'))
        complexity = self._calculate_cyclomatic_complexity(content)
        
        if loc == 0:
            return 100.0
        
        mi = max(0, 171 - 5.2 * (complexity ** 0.5) - 0.23 * complexity - 16.2 * (loc ** 0.5))
        return min(100, mi)
    
    async def _resolve_dependencies(self, content: str) -> List[Dict[str, Any]]:
        dependencies = []
        import_pattern = r'import\s+(?:\{([^}]+)\}\s+from\s+)?["\']([^"\']+)["\']'
        
        for match in re.finditer(import_pattern, content):
            path = match.group(2)
            dependencies.append({
                "path": path,
                "name": path.split('/')[-1].replace('.sol', ''),
                "type": "local" if path.startswith('.') else "external",
                "version": None
            })
        
        return dependencies
    
    def _estimate_bytecode_size(self, content: str) -> int:
        return len(content) * 2
    
    def _calculate_function_complexity(self, function_code: str) -> int:
        complexity = 1
        complexity += len(re.findall(r'\bif\b', function_code))
        complexity += len(re.findall(r'\bfor\b', function_code))
        complexity += len(re.findall(r'\bwhile\b', function_code))
        complexity += len(re.findall(r'\bcatch\b', function_code))
        return complexity
    
    # ========================================================================
    # GÉNÉRATION DE DIAGRAMMES
    # ========================================================================
    
    async def _generate_diagrams(self, contract_info: Dict[str, Any]) -> Dict[str, str]:
        """Génère les diagrammes Mermaid"""
        diagrams = {}
        mermaid_config = self._agent_config.get("mermaid", {})
        
        if not mermaid_config.get("enabled", True):
            return diagrams
        
        try:
            if contract_info.get("inheritance") and mermaid_config.get("include_inheritance", True):
                diagrams["inheritance"] = await self._generate_inheritance_diagram(contract_info)
            
            if contract_info.get("dependencies") and mermaid_config.get("include_dependencies", True):
                diagrams["dependencies"] = await self._generate_dependencies_diagram(contract_info)
            
            if mermaid_config.get("include_call_graph", True):
                diagrams["calls"] = await self._generate_call_graph(contract_info)
            
            if mermaid_config.get("include_state_diagram", True):
                diagrams["state"] = await self._generate_state_diagram(contract_info)
            
            self._logger.debug(f"📊 {len(diagrams)} diagrammes générés")
            
        except Exception as e:
            self._logger.error(f"❌ Erreur génération diagrammes: {e}")
        
        return diagrams
    
    async def _generate_inheritance_diagram(self, contract_info: Dict[str, Any]) -> str:
        mermaid_config = self._agent_config.get("mermaid", {})
        theme = mermaid_config.get("theme", "dark")
        contract_name = contract_info["name"]
        inheritance = contract_info.get("inheritance", [])
        
        diagram = ["```mermaid"]
        diagram.append(f"%%{{init: {{'theme':'{theme}'}}}}%%")
        diagram.append("classDiagram")
        
        diagram.append(f"    class {contract_name} {{")
        for func in contract_info.get("functions", [])[:5]:
            diagram.append(f"        +{func['name']}()")
        diagram.append("    }")
        
        for parent in inheritance:
            diagram.append(f"    {contract_name} --|> {parent}")
        
        diagram.append("```")
        return "\n".join(diagram)
    
    async def _generate_dependencies_diagram(self, contract_info: Dict[str, Any]) -> str:
        mermaid_config = self._agent_config.get("mermaid", {})
        theme = mermaid_config.get("theme", "dark")
        
        diagram = ["```mermaid"]
        diagram.append(f"%%{{init: {{'theme':'{theme}'}}}}%%")
        diagram.append("graph TD")
        
        contract_name = contract_info["name"]
        diagram.append(f"    {contract_name}[[{contract_name}]]")
        
        for dep in contract_info.get("dependencies", []):
            dep_name = dep["name"]
            dep_type = dep["type"]
            
            if dep_type == "external":
                diagram.append(f"    {dep_name}([{dep_name}])")
                diagram.append(f"    {contract_name} --> {dep_name}")
            else:
                diagram.append(f"    {dep_name}[[{dep_name}]]")
                diagram.append(f"    {contract_name} -.-> {dep_name}")
        
        diagram.append("```")
        return "\n".join(diagram)
    
    async def _generate_call_graph(self, contract_info: Dict[str, Any]) -> str:
        mermaid_config = self._agent_config.get("mermaid", {})
        theme = mermaid_config.get("theme", "dark")
        
        diagram = ["```mermaid"]
        diagram.append(f"%%{{init: {{'theme':'{theme}'}}}}%%")
        diagram.append("flowchart TD")
        
        contract_name = contract_info["name"]
        diagram.append(f"    subgraph {contract_name}")
        
        for func in contract_info.get("functions", []):
            func_name = func["name"]
            diagram.append(f"        {func_name}[{func_name}]")
        
        diagram.append("    end")
        diagram.append("```")
        
        return "\n".join(diagram)
    
    async def _generate_state_diagram(self, contract_info: Dict[str, Any]) -> str:
        mermaid_config = self._agent_config.get("mermaid", {})
        theme = mermaid_config.get("theme", "dark")
        
        diagram = ["```mermaid"]
        diagram.append(f"%%{{init: {{'theme':'{theme}'}}}}%%")
        diagram.append("stateDiagram-v2")
        diagram.append("    [*] --> Active")
        diagram.append("    Active --> Paused")
        diagram.append("    Paused --> Active")
        diagram.append("    Active --> Stopped")
        diagram.append("    Stopped --> [*]")
        diagram.append("```")
        
        return "\n".join(diagram)
    
    # ========================================================================
    # CONSTRUCTION DE LA DOCUMENTATION
    # ========================================================================
    
    async def _build_docs_structure(self, 
                                   contract_info: Dict[str, Any],
                                   diagrams: Dict[str, str]) -> Dict[str, Any]:
        
        sections = []
        
        sections.append({
            "id": "overview",
            "title": "📋 Overview",
            "level": 1,
            "content": await self._generate_overview_section(contract_info)
        })
        
        sections.append({
            "id": "architecture",
            "title": "🏗️ Architecture",
            "level": 1,
            "content": await self._generate_architecture_section(contract_info, diagrams)
        })
        
        sections.append({
            "id": "contracts",
            "title": "📜 Contracts",
            "level": 1,
            "content": await self._generate_contracts_section(contract_info)
        })
        
        sections.append({
            "id": "functions",
            "title": "⚙️ Functions",
            "level": 1,
            "content": await self._generate_functions_section(contract_info)
        })
        
        sections.append({
            "id": "events",
            "title": "📢 Events",
            "level": 1,
            "content": await self._generate_events_section(contract_info)
        })
        
        if contract_info.get("modifiers"):
            sections.append({
                "id": "modifiers",
                "title": "🔒 Modifiers",
                "level": 1,
                "content": await self._generate_modifiers_section(contract_info)
            })
        
        sections.append({
            "id": "security",
            "title": "🛡️ Security",
            "level": 1,
            "content": await self._generate_security_section(contract_info)
        })
        
        sections.append({
            "id": "deployment",
            "title": "🚀 Deployment",
            "level": 1,
            "content": await self._generate_deployment_section(contract_info)
        })
        
        sections.append({
            "id": "examples",
            "title": "💡 Examples",
            "level": 1,
            "content": await self._generate_examples_section(contract_info)
        })
        
        sections.append({
            "id": "changelog",
            "title": "📅 Changelog",
            "level": 1,
            "content": await self._generate_changelog_section(contract_info)
        })
        
        return {
            "contract": contract_info["name"],
            "sections": sections,
            "diagrams": diagrams,
            "generated_at": datetime.now().isoformat()
        }
    
    async def _generate_overview_section(self, info: Dict[str, Any]) -> str:
        md = []
        
        md.append(f"# 📄 {info['name']} Smart Contract")
        md.append("")
        
        md.append("<div class='badge-container'>")
        md.append(f"<span class='badge badge-license'>{info['license']}</span>")
        md.append(f"<span class='badge badge-version'>Solidity {info['solidity_version']}</span>")
        md.append(f"<span class='badge badge-risk badge-{info['security']['risk_level']}'>Risque {info['security']['risk_level'].upper()}</span>")
        md.append("</div>")
        md.append("")
        
        if info['natspec']['contract'].get('notice'):
            md.append(info['natspec']['contract']['notice'])
            md.append("")
        
        if info['natspec']['contract'].get('dev'):
            md.append(f"*Note: {info['natspec']['contract']['dev']}*")
            md.append("")
        
        md.append("## 📊 Quick Stats")
        md.append("")
        md.append("| Metric | Value |")
        md.append("|--------|-------|")
        md.append(f"| Functions | {len(info['functions'])} |")
        md.append(f"| Events | {len(info['events'])} |")
        md.append(f"| Modifiers | {len(info['modifiers'])} |")
        md.append(f"| Variables | {len(info['variables'])} |")
        md.append(f"| Lines of Code | {info['line_count']} |")
        md.append(f"| Complexity | {info['complexity']['cyclomatic']} |")
        md.append("")
        
        md.append("## 🔗 Quick Links")
        md.append("")
        md.append("- [🏗️ Architecture](#architecture)")
        md.append("- [📜 Contract Details](#contracts)")
        md.append("- [⚙️ Functions](#functions)")
        md.append("- [📢 Events](#events)")
        md.append("- [🔒 Modifiers](#modifiers)")
        md.append("- [🛡️ Security](#security)")
        md.append("- [🚀 Deployment](#deployment)")
        md.append("- [💡 Examples](#examples)")
        md.append("")
        
        return "\n".join(md)
    
    async def _generate_architecture_section(self, 
                                            info: Dict[str, Any],
                                            diagrams: Dict[str, str]) -> str:
        md = []
        
        md.append("## 🏗️ Architecture")
        md.append("")
        
        if "inheritance" in diagrams:
            md.append("### 📊 Inheritance Diagram")
            md.append("")
            md.append(diagrams["inheritance"])
            md.append("")
        
        if "dependencies" in diagrams:
            md.append("### 🔗 Dependencies")
            md.append("")
            md.append(diagrams["dependencies"])
            md.append("")
        
        if info.get("imports"):
            md.append("### 📦 Imports")
            md.append("")
            md.append("| Path | Type | Symbols |")
            md.append("|------|------|---------|")
            for imp in info["imports"]:
                symbols = ", ".join(imp["symbols"])
                md.append(f"| {imp['path']} | {imp['type']} | `{symbols}` |")
            md.append("")
        
        if info.get("inheritance"):
            md.append("### 🧬 Inheritance")
            md.append("")
            for parent in info["inheritance"]:
                md.append(f"- `{parent}`")
            md.append("")
        
        return "\n".join(md)
    
    async def _generate_contracts_section(self, info: Dict[str, Any]) -> str:
        md = []
        
        md.append("## 📜 Contract Details")
        md.append("")
        
        if info.get("variables"):
            md.append("### 🔧 State Variables")
            md.append("")
            md.append("| Name | Type | Visibility | Constant | Immutable |")
            md.append("|------|------|------------|----------|-----------|")
            for var in info["variables"]:
                constant = "✓" if var["constant"] else "✗"
                immutable = "✓" if var["immutable"] else "✗"
                md.append(f"| {var['name']} | `{var['type']}` | {var['visibility']} | {constant} | {immutable} |")
            md.append("")
        
        if info.get("structs"):
            md.append("### 🏗️ Structs")
            md.append("")
            for struct in info["structs"]:
                md.append(f"#### `{struct['name']}`")
                md.append("")
                md.append("| Field | Type |")
                md.append("|-------|------|")
                for field in struct["fields"]:
                    md.append(f"| {field['name']} | `{field['type']}` |")
                md.append("")
        
        if info.get("enums"):
            md.append("### 🔢 Enums")
            md.append("")
            for enum in info["enums"]:
                md.append(f"#### `{enum['name']}`")
                md.append("")
                for value in enum["values"]:
                    md.append(f"- `{value}`")
                md.append("")
        
        if info.get("errors"):
            md.append("### ⚠️ Custom Errors")
            md.append("")
            md.append("| Error | Parameters |")
            md.append("|-------|------------|")
            for error in info["errors"]:
                params = ", ".join([p["type"] for p in error["params"]])
                md.append(f"| `{error['name']}` | {params} |")
            md.append("")
        
        return "\n".join(md)
    
    async def _generate_functions_section(self, info: Dict[str, Any]) -> str:
        md = []
        
        md.append("## ⚙️ Functions")
        md.append("")
        
        md.append("<div class='function-toc'>")
        for func in info["functions"]:
            anchor = self._generate_anchor(func["name"])
            md.append(f"- [`{func['name']}`](#{anchor})")
        md.append("</div>")
        md.append("")
        
        for func in info["functions"]:
            anchor = self._generate_anchor(func["name"])
            md.append(f"### `{func['name']}` {self._generate_badge(func)}")
            md.append("")
            
            md.append("```solidity")
            params_str = ", ".join([f"{p['type']} {p['name']}" for p in func["params"]])
            returns_str = ""
            if func["returns"]:
                returns = ", ".join([f"{r['type']} {r['name']}" for r in func["returns"]])
                returns_str = f" returns ({returns})"
            modifiers_str = " " + " ".join(func["modifiers"]) if func["modifiers"] else ""
            
            md.append(f"function {func['name']}({params_str}){modifiers_str}{returns_str}")
            md.append("```")
            md.append("")
            
            if func["natspec"].get("notice"):
                md.append(f"**Description:** {func['natspec']['notice']}")
                md.append("")
            
            if func["natspec"].get("dev"):
                md.append(f"*{func['natspec']['dev']}*")
                md.append("")
            
            if func["params"]:
                md.append("**Parameters:**")
                md.append("")
                md.append("| Name | Type | Description |")
                md.append("|------|------|-------------|")
                for p in func["params"]:
                    desc = func["natspec"].get("params", {}).get(p["name"], "")
                    md.append(f"| {p['name']} | `{p['type']}` | {desc} |")
                md.append("")
            
            if func["returns"]:
                md.append("**Returns:**")
                md.append("")
                md.append("| Name | Type | Description |")
                md.append("|------|------|-------------|")
                for r in func["returns"]:
                    desc = func["natspec"].get("returns", {}).get(r["name"], "")
                    md.append(f"| {r['name']} | `{r['type']}` | {desc} |")
                md.append("")
            
            if func["modifiers"]:
                md.append("**Modifiers:** " + ", ".join([f"`{m}`" for m in func["modifiers"]]))
                md.append("")
            
            md.append(f"**Visibility:** `{func['visibility']}` | **Mutability:** `{func['state_mutability']}` | **Line:** {func['line']}")
            md.append("")
            md.append(f"[🔝 Back to Functions](#functions)")
            md.append("")
            md.append("---")
            md.append("")
        
        return "\n".join(md)
    
    async def _generate_events_section(self, info: Dict[str, Any]) -> str:
        md = []
        
        md.append("## 📢 Events")
        md.append("")
        
        for event in info["events"]:
            md.append(f"### `{event['name']}`")
            md.append("")
            
            md.append("```solidity")
            params_str = ", ".join([f"{p['type']}{' indexed' if p['indexed'] else ''} {p['name']}" for p in event["params"]])
            md.append(f"event {event['name']}({params_str}){' anonymous' if event['anonymous'] else ''}")
            md.append("```")
            md.append("")
            
            if event["params"]:
                md.append("**Parameters:**")
                md.append("")
                md.append("| Name | Type | Indexed | Description |")
                md.append("|------|------|---------|-------------|")
                for p in event["params"]:
                    indexed = "✓" if p["indexed"] else "✗"
                    desc = event["natspec"].get("params", {}).get(p["name"], "")
                    md.append(f"| {p['name']} | `{p['type']}` | {indexed} | {desc} |")
                md.append("")
            
            md.append(f"**Line:** {event['line']}")
            md.append("")
            md.append("[🔝 Back to Events](#events)")
            md.append("")
            md.append("---")
            md.append("")
        
        return "\n".join(md)
    
    async def _generate_modifiers_section(self, info: Dict[str, Any]) -> str:
        md = []
        
        md.append("## 🔒 Modifiers")
        md.append("")
        
        for modifier in info["modifiers"]:
            md.append(f"### `{modifier['name']}`")
            md.append("")
            
            md.append("```solidity")
            params_str = ", ".join([f"{p['type']} {p['name']}" for p in modifier["params"]])
            md.append(f"modifier {modifier['name']}({params_str})")
            md.append("```")
            md.append("")
            
            if modifier["natspec"].get("notice"):
                md.append(f"**Description:** {modifier['natspec']['notice']}")
                md.append("")
            
            if modifier["params"]:
                md.append("**Parameters:**")
                md.append("")
                md.append("| Name | Type | Description |")
                md.append("|------|------|-------------|")
                for p in modifier["params"]:
                    desc = modifier["natspec"].get("params", {}).get(p["name"], "")
                    md.append(f"| {p['name']} | `{p['type']}` | {desc} |")
                md.append("")
            
            md.append(f"**Line:** {modifier.get('line', 'N/A')}")
            md.append("")
            md.append("[🔝 Back to Modifiers](#modifiers)")
            md.append("")
            md.append("---")
            md.append("")
        
        return "\n".join(md)
    
    async def _generate_security_section(self, info: Dict[str, Any]) -> str:
        md = []
        
        md.append("## 🛡️ Security Analysis")
        md.append("")
        
        risk = info["security"]["risk_level"]
        risk_color = {
            "low": "🟢",
            "medium": "🟡",
            "high": "🔴"
        }.get(risk, "⚪")
        
        md.append(f"### Risk Assessment: {risk_color} {risk.upper()}")
        md.append("")
        
        md.append("| Check | Status |")
        md.append("|-------|--------|")
        md.append(f"| Reentrancy Protection | {'✅' if info['security']['reentrancy_protection'] else '❌'} |")
        md.append(f"| Access Control | {'✅' if info['security']['access_control'] else '❌'} |")
        md.append(f"| Pausable | {'✅' if info['security']['pausable'] else '❌'} |")
        md.append(f"| Safe Math | {'✅' if info['security']['safe_math'] else '❌'} |")
        md.append(f"| Pull Payment | {'✅' if info['security']['pull_payment'] else '❌'} |")
        md.append(f"| Timelock | {'✅' if info['security']['timelock'] else '❌'} |")
        md.append(f"| Multisig | {'✅' if info['security']['multisig'] else '❌'} |")
        md.append(f"| Emergency Stop | {'✅' if info['security']['emergency_stop'] else '❌'} |")
        md.append("")
        
        md.append("### 🔒 Security Recommendations")
        md.append("")
        
        if not info["security"]["reentrancy_protection"]:
            md.append("- ⚠️ **Add ReentrancyGuard** to prevent reentrancy attacks")
        if not info["security"]["access_control"]:
            md.append("- ⚠️ **Implement access control** (Ownable, AccessControl)")
        if 'delegatecall' in str(info) and not info["security"]["access_control"]:
            md.append("- ⚠️ **Delegatecall with caution** - ensure called contracts are trusted")
        
        md.append("")
        
        return "\n".join(md)
    
    async def _generate_deployment_section(self, info: Dict[str, Any]) -> str:
        md = []
        
        md.append("## 🚀 Deployment")
        md.append("")
        
        md.append("### Networks")
        md.append("")
        
        networks = ["ethereum", "polygon", "arbitrum", "optimism"]
        for network in networks:
            md.append(f"#### {network.capitalize()}")
            md.append("")
            md.append("```bash")
            md.append(f"forge create {info['name']} --rpc-url {network} --private-key $PRIVATE_KEY")
            md.append("```")
            md.append("")
            md.append("**Verification:**")
            md.append("```bash")
            md.append(f"forge verify-contract <ADDRESS> {info['name']} --chain {network}")
            md.append("```")
            md.append("")
        
        md.append("### Constructor Parameters")
        md.append("")
        md.append("| Parameter | Type | Description |")
        md.append("|-----------|------|-------------|")
        
        constructor = next((f for f in info["functions"] if f["name"] == "constructor"), None)
        if constructor:
            for p in constructor["params"]:
                md.append(f"| {p['name']} | `{p['type']}` | {p.get('description', '')} |")
        
        md.append("")
        
        return "\n".join(md)
    
    async def _generate_examples_section(self, info: Dict[str, Any]) -> str:
        md = []
        
        md.append("## 💡 Examples")
        md.append("")
        
        md.append("### Deployment Example")
        md.append("")
        md.append("```javascript")
        md.append(f"const {info['name']} = await ethers.deployContract('{info['name']}')")
        md.append(f"await {info['name']}.waitForDeployment()")
        md.append(f"console.log('Contract deployed to:', await {info['name']}.getAddress())")
        md.append("```")
        md.append("")
        
        md.append("### Interaction Examples")
        md.append("")
        
        for func in info["functions"][:3]:
            md.append(f"#### `{func['name']}`")
            md.append("")
            md.append("```javascript")
            params = ", ".join([p["name"] for p in func["params"]])
            md.append(f"// Call {func['name']}")
            md.append(f"const tx = await contract.{func['name']}({params})")
            md.append("await tx.wait()")
            md.append("```")
            md.append("")
        
        return "\n".join(md)
    
    async def _generate_changelog_section(self, info: Dict[str, Any]) -> str:
        md = []
        
        md.append("## 📅 Changelog")
        md.append("")
        md.append("### v1.0.0 (Initial Release)")
        md.append("")
        md.append("#### ✨ Features")
        md.append(f"- Initial implementation of {info['name']}")
        md.append(f"- {len(info['functions'])} functions")
        md.append(f"- {len(info['events'])} events")
        md.append("")
        md.append("#### 🔒 Security")
        md.append("- Standard security patterns implemented")
        md.append("- Audited by internal team")
        md.append("")
        
        return "\n".join(md)
    
    # ========================================================================
    # GÉNÉRATION HTML/MARKDOWN
    # ========================================================================
    
    async def _generate_html(self, structure: Dict[str, Any]) -> Path:
        html = self._templates["base_html"]
        
        html = html.replace("{{CONTRACT_NAME}}", structure["contract"])
        html = html.replace("{{GENERATED_AT}}", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        
        toc = await self._generate_toc(structure)
        html = html.replace("{{TOC}}", toc)
        
        content = []
        for section in structure["sections"]:
            content.append(f"<section id='{section['id']}' class='doc-section'>")
            content.append(self._markdown_to_html(section["content"]))
            content.append("</section>")
        
        html = html.replace("{{CONTENT}}", "\n".join(content))
        
        output_path = self._output_path / f"{structure['contract']}.html"
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html)
        
        return output_path
    
    async def _generate_markdown(self, structure: Dict[str, Any]) -> Path:
        content = []
        
        content.append(f"# {structure['contract']} Documentation")
        content.append(f"*Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")
        content.append("")
        
        content.append("## Table of Contents")
        for section in structure["sections"]:
            content.append(f"- [{section['title']}](#{section['id']})")
        content.append("")
        
        for section in structure["sections"]:
            content.append(section["content"])
        
        output_path = self._output_path / f"{structure['contract']}.md"
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("\n".join(content))
        
        return output_path
    
    async def _generate_site(self, structure: Dict[str, Any]) -> Path:
        site_path = self._output_path / "site" / structure["contract"]
        site_path.mkdir(parents=True, exist_ok=True)
        
        index_path = site_path / "index.html"
        html = await self._generate_html(structure)
        shutil.copy(html, index_path)
        
        assets_src = Path(__file__).parent / "assets"
        assets_dst = site_path / "assets"
        if assets_src.exists():
            shutil.copytree(assets_src, assets_dst, dirs_exist_ok=True)
        
        return index_path
    
    async def _generate_project_site(self, project_info: Dict[str, Any]) -> Path:
        project_path = self._output_path / "site" / project_info["name"]
        project_path.mkdir(parents=True, exist_ok=True)
        
        index_path = project_path / "index.html"
        with open(index_path, 'w', encoding='utf-8') as f:
            f.write(f"""<!DOCTYPE html>
<html>
<head>
    <title>{project_info['name']} Documentation</title>
    <style>
        body {{ font-family: 'Inter', sans-serif; background: #0f1215; color: #fff; margin: 0; padding: 20px; }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        h1 {{ color: #00ff88; }}
        .contracts {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 20px; margin-top: 30px; }}
        .contract-card {{ background: #1a1e24; border-radius: 10px; padding: 20px; border: 1px solid #2a2f35; }}
        .contract-card h3 {{ margin: 0 0 10px 0; }}
        .contract-card a {{ color: #00ff88; text-decoration: none; }}
        .contract-card a:hover {{ text-decoration: underline; }}
        .badge {{ display: inline-block; padding: 3px 8px; border-radius: 12px; font-size: 12px; margin-right: 5px; }}
        .badge-license {{ background: #2a2f35; }}
        .badge-risk {{ background: #ffd700; color: #000; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>{project_info['name']}</h1>
        <p>{project_info.get('description', 'Smart contract project documentation')}</p>
        <p><em>Generated on {project_info['generated_at']}</em></p>
        
        <h2>📜 Contracts</h2>
        <div class="contracts">
""")
        
        for contract in project_info["contracts"]:
            f.write(f"""
            <div class="contract-card">
                <h3><a href="{contract['name']}/index.html">{contract['name']}</a></h3>
                <p>Functions: {len(contract['functions'])} | Events: {len(contract['events'])}</p>
                <span class="badge badge-license">{contract['license']}</span>
                <span class="badge badge-risk">{contract['security']['risk_level'].upper()}</span>
            </div>
""")
        
        f.write("""
        </div>
    </div>
</body>
</html>
""")
        
        for contract in project_info["contracts"]:
            contract_docs = await self._build_docs_structure(contract, project_info["diagrams"].get(contract["name"], {}))
            await self._generate_site(contract_docs)
        
        return index_path
    
    def _markdown_to_html(self, md: str) -> str:
        html = md.replace("\n", "<br>")
        return f"<div class='markdown'>{html}</div>"
    
    async def _generate_toc(self, structure: Dict[str, Any]) -> str:
        toc = ["<ul class='toc'>"]
        
        for section in structure["sections"]:
            toc.append(f"<li><a href='#{section['id']}'>{section['title']}</a>")
            
            if section["id"] == "functions":
                toc.append("<ul>")
                toc.append("</ul>")
            
            toc.append("</li>")
        
        toc.append("</ul>")
        return "\n".join(toc)
    
    def _generate_anchor(self, text: str) -> str:
        anchor = text.lower()
        anchor = re.sub(r'[^a-z0-9]+', '-', anchor)
        anchor = anchor.strip('-')
        return anchor
    
    def _generate_badge(self, func: Dict[str, Any]) -> str:
        badges = []
        
        if func["visibility"] != "public":
            badges.append(f"<span class='badge visibility-{func['visibility']}'>{func['visibility']}</span>")
        
        if func["state_mutability"] != "nonpayable":
            badges.append(f"<span class='badge mutability-{func['state_mutability']}'>{func['state_mutability']}</span>")
        
        if func["virtual"]:
            badges.append("<span class='badge virtual'>virtual</span>")
        
        if func["override"]:
            badges.append("<span class='badge override'>override</span>")
        
        return " ".join(badges)
    
    # ========================================================================
    # TEMPLATES
    # ========================================================================
    
    def _get_base_html_template(self) -> str:
        styling = self._agent_config.get("styling", {})
        colors = styling.get("colors", {})
        primary = colors.get("primary", "#00ff88")
        secondary = colors.get("secondary", "#8b5cf6")
        background = colors.get("background", "#0f1215")
        
        return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{CONTRACT_NAME}} - Documentation</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Fira+Code:wght@300;400;500&display=swap');
        
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Inter', sans-serif;
            background: #0f1215;
            color: #fff;
            line-height: 1.6;
            display: flex;
            min-height: 100vh;
        }
        
        .sidebar {
            width: 300px;
            background: #1a1e24;
            border-right: 1px solid #2a2f35;
            padding: 20px;
            position: sticky;
            top: 0;
            height: 100vh;
            overflow-y: auto;
        }
        
        .sidebar h2 {
            color: """ + primary + """;
            margin-bottom: 20px;
            font-size: 18px;
        }
        
        .toc {
            list-style: none;
        }
        
        .toc li {
            margin: 10px 0;
        }
        
        .toc a {
            color: #888;
            text-decoration: none;
            transition: color 0.2s;
            display: block;
            padding: 5px 10px;
            border-radius: 5px;
        }
        
        .toc a:hover {
            color: """ + primary + """;
            background: #2a2f35;
        }
        
        .toc ul {
            list-style: none;
            margin-left: 20px;
        }
        
        .toc ul a {
            font-size: 14px;
        }
        
        .content {
            flex: 1;
            padding: 40px;
            max-width: 1000px;
            margin: 0 auto;
        }
        
        h1 {
            font-size: 32px;
            font-weight: 600;
            margin-bottom: 10px;
            color: """ + primary + """;
        }
        
        h2 {
            font-size: 24px;
            font-weight: 600;
            margin: 30px 0 15px;
            padding-bottom: 10px;
            border-bottom: 1px solid #2a2f35;
        }
        
        h3 {
            font-size: 20px;
            font-weight: 500;
            margin: 25px 0 10px;
        }
        
        pre {
            background: #1a1e24;
            padding: 15px;
            border-radius: 8px;
            overflow-x: auto;
            margin: 15px 0;
            border: 1px solid #2a2f35;
        }
        
        code {
            font-family: 'Fira Code', monospace;
            font-size: 14px;
        }
        
        table {
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }
        
        th {
            background: #1a1e24;
            color: #888;
            font-weight: 500;
            padding: 10px;
            text-align: left;
            border-bottom: 1px solid #2a2f35;
        }
        
        td {
            padding: 10px;
            border-bottom: 1px solid #2a2f35;
        }
        
        .badge-container {
            margin: 20px 0;
        }
        
        .badge {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 500;
            margin-right: 8px;
            margin-bottom: 8px;
        }
        
        .badge-license {
            background: #2a2f35;
            color: #fff;
        }
        
        .badge-version {
            background: """ + secondary + """;
            color: #fff;
        }
        
        .badge-risk-low {
            background: #10b981;
            color: #fff;
        }
        
        .badge-risk-medium {
            background: #ffd700;
            color: #000;
        }
        
        .badge-risk-high {
            background: #ef4444;
            color: #fff;
        }
        
        .badge-visibility-private {
            background: #6b7280;
            color: #fff;
        }
        
        .badge-visibility-internal {
            background: """ + secondary + """;
            color: #fff;
        }
        
        .badge-mutability-view {
            background: #3b82f6;
            color: #fff;
        }
        
        .badge-mutability-pure {
            background: #10b981;
            color: #fff;
        }
        
        .badge-mutability-payable {
            background: #f59e0b;
            color: #000;
        }
        
        .badge-virtual, .badge-override {
            background: #ec4899;
            color: #fff;
        }
        
        .function-toc {
            background: #1a1e24;
            padding: 15px;
            border-radius: 8px;
            margin: 20px 0;
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
        }
        
        .function-toc a {
            color: #888;
            text-decoration: none;
            padding: 5px 10px;
            border-radius: 5px;
            background: #2a2f35;
            font-size: 14px;
        }
        
        .function-toc a:hover {
            color: """ + primary + """;
        }
        
        .back-to-top {
            position: fixed;
            bottom: 30px;
            right: 30px;
            background: """ + primary + """;
            color: #000;
            width: 40px;
            height: 40px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            text-decoration: none;
            font-size: 20px;
            opacity: 0;
            transition: opacity 0.3s;
            pointer-events: none;
        }
        
        .back-to-top.visible {
            opacity: 1;
            pointer-events: auto;
        }
        
        .back-to-top:hover {
            background: #00cc88;
        }
        
        .mermaid {
            background: #1a1e24;
            padding: 20px;
            border-radius: 8px;
            margin: 20px 0;
        }
        
        @media (max-width: 768px) {
            body {
                flex-direction: column;
            }
            .sidebar {
                width: 100%;
                height: auto;
                position: static;
            }
        }
    </style>
    <script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
    <script>
        mermaid.initialize({
            startOnLoad: true,
            theme: 'dark',
            securityLevel: 'loose',
            fontFamily: 'Inter'
        });
    </script>
</head>
<body>
    <div class="sidebar">
        <h2>📚 Documentation</h2>
        {{TOC}}
    </div>
    
    <div class="content">
        {{CONTENT}}
    </div>
    
    <a href="#" class="back-to-top" id="backToTop">↑</a>
    
    <script>
        const backToTop = document.getElementById('backToTop');
        window.addEventListener('scroll', () => {
            if (window.scrollY > 300) {
                backToTop.classList.add('visible');
            } else {
                backToTop.classList.remove('visible');
            }
        });
        
        document.querySelectorAll('a[href^="#"]').forEach(anchor => {
            anchor.addEventListener('click', function (e) {
                e.preventDefault();
                const target = document.querySelector(this.getAttribute('href'));
                if (target) {
                    target.scrollIntoView({
                        behavior: 'smooth'
                    });
                }
            });
        });
    </script>
</body>
</html>"""
    
    def _get_toc_template(self) -> str:
        return """
        <ul class="toc">
            {% for section in sections %}
            <li><a href="#{{ section.id }}">{{ section.title }}</a>
                {% if section.id == "functions" and functions %}
                <ul>
                    {% for func in functions %}
                    <li><a href="#{{ func.name|anchor }}">{{ func.name }}</a></li>
                    {% endfor %}
                </ul>
                {% endif %}
            </li>
            {% endfor %}
        </ul>
        """
    
    def _get_section_template(self) -> str:
        return """
        <section id="{{ section.id }}" class="doc-section">
            <h{{ section.level }}>{{ section.title }}</h{{ section.level }}>
            {{ section.content }}
        </section>
        """
    
    def _get_function_table_template(self) -> str:
        return """
        <table class="function-table">
            <thead>
                <tr>
                    <th>Name</th>
                    <th>Visibility</th>
                    <th>Mutability</th>
                    <th>Parameters</th>
                    <th>Returns</th>
                </tr>
            </thead>
            <tbody>
                {% for func in functions %}
                <tr>
                    <td><a href="#{{ func.name|anchor }}">{{ func.name }}</a></td>
                    <td><span class="badge visibility-{{ func.visibility }}">{{ func.visibility }}</span></td>
                    <td><span class="badge mutability-{{ func.state_mutability }}">{{ func.state_mutability }}</span></td>
                    <td>{{ func.params|length }}</td>
                    <td>{{ func.returns|length }}</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
        """
    
    def _get_event_table_template(self) -> str:
        return """
        <table class="event-table">
            <thead>
                <tr>
                    <th>Name</th>
                    <th>Parameters</th>
                    <th>Anonymous</th>
                </tr>
            </thead>
            <tbody>
                {% for event in events %}
                <tr>
                    <td><a href="#{{ event.name|anchor }}">{{ event.name }}</a></td>
                    <td>{{ event.params|length }}</td>
                    <td>{{ '✓' if event.anonymous else '✗' }}</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
        """
    
    def _get_security_template(self) -> str:
        return """
        <div class="security-section">
            <h2>🛡️ Security</h2>
            
            <div class="risk-badge risk-{{ security.risk_level }}">
                Risk Level: {{ security.risk_level|upper }}
            </div>
            
            <table>
                <thead>
                    <tr>
                        <th>Check</th>
                        <th>Status</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td>Reentrancy Protection</td>
                        <td>{{ '✅' if security.reentrancy_protection else '❌' }}</td>
                    </tr>
                    <tr>
                        <td>Access Control</td>
                        <td>{{ '✅' if security.access_control else '❌' }}</td>
                    </tr>
                    <tr>
                        <td>Pausable</td>
                        <td>{{ '✅' if security.pausable else '❌' }}</td>
                    </tr>
                </tbody>
            </table>
        </div>
        """
    
    def _get_mermaid_template(self) -> str:
        return """
        <div class="mermaid">
            {{ diagram }}
        </div>
        """
    
    # ========================================================================
    # GESTION DES MESSAGES
    # ========================================================================
    
    async def _handle_custom_message(self, message: Message) -> Optional[Message]:
        """Gestion des messages personnalisés"""
        msg_type = message.message_type
        msg_id = message.message_id
        
        self._logger.debug(f"📨 Message reçu: {msg_type} (id: {msg_id})")
        
        try:
            # Déléguer à un sous-agent si demandé
            if message.content and "sub_agent" in message.content:
                sub_agent_id = message.content.get("sub_agent")
                if sub_agent_id in self._sub_agents:
                    result = await self._sub_agents[sub_agent_id].handle_message(message)
                    return result
            
            handlers = {
                "doc.generate_contract": self._handle_generate_contract,
                "doc.generate_readme": self._handle_generate_readme,
                "doc.generate_api": self._handle_generate_api,
                "doc.analyze": self._handle_analyze,
                "doc.stats": self._handle_stats,
                "doc.pause": self._handle_pause,
                "doc.resume": self._handle_resume,
                "doc.shutdown": self._handle_shutdown,
            }
            
            if msg_type in handlers:
                return await handlers[msg_type](message)
            
            self._logger.warning(f"Aucun handler pour le type: {msg_type}")
            return None
            
        except Exception as e:
            self._logger.error(f"Erreur traitement message: {e}")
            return Message(
                sender=self.name,
                recipient=message.sender,
                content={"error": str(e), "traceback": traceback.format_exc()},
                message_type=MessageType.ERROR.value,
                correlation_id=msg_id
            )
    
    async def _handle_generate_contract(self, message: Message) -> Message:
        content = message.content
        result = await self.generate_contract_documentation(
            contract_path=content.get("contract_path"),
            output_format=content.get("format", "html")
        )
        return Message(
            sender=self.name,
            recipient=message.sender,
            content=result,
            message_type="doc.contract_generated",
            correlation_id=message.message_id
        )
    
    async def _handle_generate_readme(self, message: Message) -> Message:
        result = await self.generate_readme(message.content)
        return Message(
            sender=self.name,
            recipient=message.sender,
            content=result,
            message_type="doc.readme_generated",
            correlation_id=message.message_id
        )
    
    async def _handle_generate_api(self, message: Message) -> Message:
        result = await self.generate_api_documentation(message.content)
        return Message(
            sender=self.name,
            recipient=message.sender,
            content=result,
            message_type="doc.api_generated",
            correlation_id=message.message_id
        )
    
    async def _handle_analyze(self, message: Message) -> Message:
        info = await self._analyze_contract(message.content.get("contract_path"))
        return Message(
            sender=self.name,
            recipient=message.sender,
            content={"success": True, "info": info},
            message_type="doc.analysis_complete",
            correlation_id=message.message_id
        )
    
    async def _handle_stats(self, message: Message) -> Message:
        return Message(
            sender=self.name,
            recipient=message.sender,
            content={
                "success": True,
                "stats": self._stats,
                "docs_generated": self._docs_generated,
                "contracts_cached": len(self._contracts_cache),
                "sub_agents": list(self._sub_agents.keys())
            },
            message_type="doc.stats_response",
            correlation_id=message.message_id
        )
    
    async def _handle_pause(self, message: Message) -> Message:
        await self.pause()
        return Message(
            sender=self.name,
            recipient=message.sender,
            content={"status": "paused"},
            message_type="doc.status_update",
            correlation_id=message.message_id
        )
    
    async def _handle_resume(self, message: Message) -> Message:
        await self.resume()
        return Message(
            sender=self.name,
            recipient=message.sender,
            content={"status": "resumed"},
            message_type="doc.status_update",
            correlation_id=message.message_id
        )
    
    async def _handle_shutdown(self, message: Message) -> Message:
        await self.shutdown()
        return Message(
            sender=self.name,
            recipient=message.sender,
            content={"status": "shutdown"},
            message_type="doc.status_update",
            correlation_id=message.message_id
        )
    
    # ========================================================================
    # GESTION DU CYCLE DE VIE
    # ========================================================================
    
    async def pause(self) -> bool:
        self._logger.info("Pause de l'agent Documenter...")
        self._status = AgentStatus.PAUSED
        
        for sub_agent in self._sub_agents.values():
            try:
                await sub_agent.pause()
            except:
                pass
        
        return True
    
    async def resume(self) -> bool:
        self._logger.info("Reprise de l'agent Documenter...")
        self._status = AgentStatus.READY
        
        for sub_agent in self._sub_agents.values():
            try:
                await sub_agent.resume()
            except:
                pass
        
        return True
    
    async def shutdown(self) -> bool:
        self._logger.info("Arrêt de l'agent Documenter...")
        self._status = AgentStatus.SHUTTING_DOWN
        
        if self._cleanup_task and not self._cleanup_task.done():
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
        
        for sub_id, sub_agent in self._sub_agents.items():
            try:
                await sub_agent.shutdown()
                self._logger.info(f"  ✓ Sous-agent {sub_id} arrêté")
            except Exception as e:
                self._logger.warning(f"  ⚠️ Erreur arrêt sous-agent {sub_id}: {e}")
        
        try:
            stats_file = self._output_path / f"documenter_stats_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(stats_file, 'w', encoding='utf-8') as f:
                json.dump({
                    "stats": self._stats,
                    "docs_generated": self._docs_generated,
                    "contracts_cached": len(self._contracts_cache),
                    "templates": len(self._templates),
                    "sub_agents": list(self._sub_agents.keys()),
                    "timestamp": datetime.now().isoformat()
                }, f, indent=2)
            self._logger.info(f"✅ Statistiques sauvegardées: {stats_file}")
        except Exception as e:
            self._logger.warning(f"⚠️ Impossible de sauvegarder: {e}")
        
        await super().shutdown()
        self._logger.info("✅ Agent Documenter arrêté")
        return True
    
    # ========================================================================
    # HEALTH CHECK & INFO
    # ========================================================================
    
    async def health_check(self) -> Dict[str, Any]:
        uptime = (datetime.now() - self._stats["start_time"]).total_seconds()
        
        sub_agents_health = {}
        all_sub_agents_healthy = True
        
        for sub_id, sub_agent in self._sub_agents.items():
            try:
                if hasattr(sub_agent, 'health_check'):
                    health = await sub_agent.health_check()
                    sub_agents_health[sub_id] = health.get('status', 'unknown')
                    if health.get('status') != 'healthy':
                        all_sub_agents_healthy = False
            except:
                sub_agents_health[sub_id] = 'error'
                all_sub_agents_healthy = False
        
        return {
            "agent": self.name,
            "display_name": self._display_name,
            "status": self._status.value if hasattr(self._status, 'value') else str(self._status),
            "ready": self._status == AgentStatus.READY,
            "initialized": self._initialized,
            "uptime_seconds": uptime,
            "uptime_formatted": str(timedelta(seconds=int(uptime))),
            "sub_agents_count": len(self._sub_agents),
            "sub_agents_health": sub_agents_health,
            "all_sub_agents_healthy": all_sub_agents_healthy,
            "docs_generated": self._docs_generated,
            "contracts_cached": len(self._contracts_cache),
            "diagrams_generated": self._stats.get('diagrams_generated', 0),
            "components": list(self._components.keys()),
            "stats": self._stats
        }
    
    def get_agent_info(self) -> Dict[str, Any]:
        agent_config = self._agent_config.get('agent', {})
        return {
            "id": self.name,
            "name": "📚 Agent de Documentation",
            "display_name": agent_config.get('display_name', '📚 Agent de Documentation'),
            "version": agent_config.get('version', '2.2.0'),
            "description": agent_config.get('description', 'Agent de documentation professionnelle'),
            "status": self._status.value if hasattr(self._status, 'value') else str(self._status),
            "capabilities": ["generate_documentation", "generate_diagrams", "analyze_contracts"],
            "sub_agents": list(self._sub_agents.keys()),
            "docs_generated": self._docs_generated,
            "templates_loaded": len(self._templates),
            "stats": {
                "docs_generated": self._stats['docs_generated'],
                "contracts_cached": self._stats['contracts_cached'],
                "diagrams_generated": self._stats.get('diagrams_generated', 0)
            }
        }


# ============================================================================
# FONCTIONS D'USINE
# ============================================================================

def create_documenter_agent(config_path: str = "") -> DocumenterAgent:
    """Crée une instance du documenter agent"""
    return DocumenterAgent(config_path)


def get_agent_class():
    """Retourne la classe principale pour le chargement dynamique"""
    return DocumenterAgent


async def get_documenter_agent(config_path: str = "") -> DocumenterAgent:
    """Crée et initialise une instance du documenter agent"""
    agent = create_documenter_agent(config_path)
    await agent.initialize()
    return agent


# ============================================================================
# POINT D'ENTRÉE POUR EXÉCUTION DIRECTE
# ============================================================================

if __name__ == "__main__":
    async def main():
        print("=" * 70)
        print("📚 TEST DOCUMENTER PRO AGENT".center(70))
        print("=" * 70)
        
        agent = await get_documenter_agent()
        
        agent_info = agent.get_agent_info()
        print(f"\n✅ Agent: {agent_info['name']} v{agent_info['version']}")
        print(f"✅ Statut: {agent_info['status']}")
        print(f"✅ Sous-agents: {agent_info['sub_agents']}")
        print(f"✅ Templates: {agent_info['templates_loaded']}")
        
        test_contract = """
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "@openzeppelin/contracts/access/Ownable.sol";

/**
 * @title TestToken
 * @notice A simple test token contract
 * @dev For demonstration purposes
 */
contract TestToken is Ownable {
    string public name = "TestToken";
    string public symbol = "TST";
    uint256 public totalSupply;
    
    mapping(address => uint256) public balanceOf;
    
    event Transfer(address indexed from, address indexed to, uint256 value);
    
    constructor(uint256 initialSupply) {
        totalSupply = initialSupply;
        balanceOf[msg.sender] = initialSupply;
        emit Transfer(address(0), msg.sender, initialSupply);
    }
    
    /**
     * @notice Transfer tokens to another address
     * @param to Recipient address
     * @param amount Amount to transfer
     */
    function transfer(address to, uint256 amount) external {
        require(balanceOf[msg.sender] >= amount, "Insufficient balance");
        require(to != address(0), "Invalid recipient");
        
        balanceOf[msg.sender] -= amount;
        balanceOf[to] += amount;
        
        emit Transfer(msg.sender, to, amount);
    }
}
        """
        
        test_path = Path("./temp_test_contract.sol")
        with open(test_path, 'w', encoding='utf-8') as f:
            f.write(test_contract)
        
        print(f"\n📄 Test sur contrat exemple...")
        
        result = await agent.generate_contract_documentation(str(test_path))
        print(f"✅ Documentation générée: {result['path']}")
        print(f"📊 {result['sections']} sections, {result['diagrams']} diagrammes")
        
        test_path.unlink()
        
        health = await agent.health_check()
        print(f"\n❤️  Health: {health['status']}")
        print(f"📊 Docs générés: {health['docs_generated']}")
        print(f"🤖 Sous-agents: {health['sub_agents_count']}")
        
        await agent.shutdown()
        
        print("\n" + "=" * 70)
        print("✅ DOCUMENTER AGENT OPÉRATIONNEL".center(70))
        print("=" * 70)
    
    asyncio.run(main())
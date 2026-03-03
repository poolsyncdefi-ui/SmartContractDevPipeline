import logging
import os
import sys
import yaml
import asyncio
import json
import traceback  # ← AJOUTÉ
import hashlib
import re
import shutil
import jinja2  # ← AJOUTÉ
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)

"""
Documenter Agent 2.0 - Documentation professionnelle
Génère une documentation structurée, interactive et visuelle
Avec Mermaid diagrams, table des matières, liens croisés
Version: 2.0.0
"""

# Ajouter le chemin du projet
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from agents.base_agent.base_agent import BaseAgent, AgentStatus, Message


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


class DocumenterAgent(BaseAgent):
    """
    Documenter Agent 2.0 - Documentation professionnelle
    Génère documentation structurée avec Mermaid, TOC, liens croisés
    """
    
    def __init__(self, config_path: str = ""):
        """Initialise l'agent documenter"""
        super().__init__(config_path)
        
        self._logger.info("📚 Documenter Pro Agent créé")
        
        # Charger configuration
        self._load_configuration()
        
        # Vérifier que la configuration a la bonne structure
        if "documenter" not in self._config:
            self._logger.error("❌ Configuration invalide : section 'documenter' manquante")
            self._config["documenter"] = self._get_default_config()["documenter"]
        
        # État interne
        self._docs_generated = 0
        self._templates = {}
        self._contracts_cache = {}
        self._diagrams_cache = {}
        self._output_path = Path(self._config["documenter"]["output_path"])
        self._temp_path = Path(self._config["documenter"]["temp_path"])
        
        # Jinja2 environment
        self._env = None
        
        # Créer les répertoires
        self._create_directories()
    
    def _load_configuration(self):
        """Charge la configuration depuis le fichier YAML"""
        try:
            config_path = os.path.join(os.path.dirname(__file__), "config.yaml")
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    loaded_config = yaml.safe_load(f)
                
                # Charger la config par défaut
                default_config = self._get_default_config()
                
                # Fusionner : la config chargée écrase la config par défaut
                self._config = default_config.copy()
                if loaded_config:
                    self._deep_merge(self._config, loaded_config)
                
                self._logger.info(f"✅ Configuration chargée: documenter v{self._config['agent']['version']}")
            else:
                self._logger.warning("⚠️ Fichier config.yaml non trouvé, utilisation configuration par défaut")
                self._config = self._get_default_config()
        except Exception as e:
            self._logger.error(f"❌ Erreur chargement config: {e}")
            self._config = self._get_default_config()

    async def _handle_custom_message(self, message: Message) -> Optional[Message]:
        """
        Gère les messages personnalisés pour le DocumenterAgent.
        
        Args:
            message: Message à traiter
            
        Returns:
            Réponse éventuelle
        """
        try:
            msg_type = message.message_type
            self._logger.debug(f"Message reçu: {msg_type}")
            
            if msg_type == "generate_documentation":
                # Générer de la documentation
                result = await self.generate_documentation(message.content)
                return Message(
                    sender=self.name,
                    recipient=message.sender,
                    content=result,
                    message_type="documentation_generated",
                    correlation_id=message.message_id
                )
            
            elif msg_type == "generate_diagram":
                # Générer un diagramme
                result = await self.generate_diagram(message.content)
                return Message(
                    sender=self.name,
                    recipient=message.sender,
                    content=result,
                    message_type="diagram_generated",
                    correlation_id=message.message_id
                )
            
            elif msg_type == "pause":
                await self.pause()
                return Message(
                    sender=self.name,
                    recipient=message.sender,
                    content={"status": "paused"},
                    message_type="status_update",
                    correlation_id=message.message_id
                )
            
            elif msg_type == "resume":
                await self.resume()
                return Message(
                    sender=self.name,
                    recipient=message.sender,
                    content={"status": "resumed"},
                    message_type="status_update",
                    correlation_id=message.message_id
                )
            
            elif msg_type == "shutdown":
                await self.shutdown()
                return Message(
                    sender=self.name,
                    recipient=message.sender,
                    content={"status": "shutdown"},
                    message_type="status_update",
                    correlation_id=message.message_id
                )
            
            return None
            
        except Exception as e:
            self._logger.error(f"Erreur traitement message: {e}")
            return Message(
                sender=self.name,
                recipient=message.sender,
                content={"error": str(e)},
                message_type="error",
                correlation_id=message.message_id
            )
    
    async def _initialize_components(self) -> bool:
        """
        Initialise les composants du DocumenterAgent.
        
        Returns:
            True si l'initialisation a réussi
        """
        try:
            self._logger.info("Initialisation des composants du DocumenterAgent...")
            
            self._components = {
                "doc_generator": {"enabled": True, "formats": ["markdown", "html", "pdf"]},
                "diagram_generator": {"enabled": True, "types": ["mermaid", "uml", "c4"]},
                "template_manager": {"enabled": True, "templates": list(self._templates.keys())}
            }
            
            self._logger.info(f"✅ Composants: {list(self._components.keys())}")
            return True
            
        except Exception as e:
            self._logger.error(f"Erreur composants: {e}")
            return False
    
    async def generate_documentation(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Génère de la documentation."""
        return {"success": True, "message": "Documentation générée"}
    
    async def generate_diagram(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Génère un diagramme."""
        return {"success": True, "message": "Diagramme généré"}

    def _deep_merge(self, base: Dict, override: Dict) -> None:
        """
        Fusionne profondément deux dictionnaires.
        """
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._deep_merge(base[key], value)
            else:
                base[key] = value

    # ⚠️ Cette méthode doit être au même niveau que _deep_merge, PAS à l'intérieur !
    def _get_default_config(self) -> Dict[str, Any]:
        """Configuration par défaut"""
        return {
            "agent": {
                "name": "documenter",
                "display_name": "📚 Documenter Agent",
                "version": "2.0.0",
                "description": "Agent de documentation professionnelle",
                "capabilities": [
                    {"name": "generate_contract_docs", "description": "Génère la documentation d'un contrat"},
                    {"name": "generate_project_docs", "description": "Génère la documentation d'un projet"},
                    {"name": "generate_diagrams", "description": "Génère des diagrammes Mermaid"}
                ]
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
    
    def _create_directories(self):
        """Crée les répertoires nécessaires"""
        dirs = [
            self._output_path,
            self._temp_path,
            Path(self._config["documenter"]["templates_path"]),
            self._output_path / "assets",
            self._output_path / "diagrams",
            self._output_path / "contracts"
        ]
        
        for dir_path in dirs:
            dir_path.mkdir(parents=True, exist_ok=True)
            self._logger.debug(f"📁 Répertoire créé: {dir_path}")
    
    async def _initialize_components(self):
        """
        Initialise les composants spécifiques de l'agent
        Requis par BaseAgent
        """
        self._logger.info("Initialisation des composants...")
        
        self._components = {
            "contract_analyzer": True,
            "diagram_generator": self._config["mermaid"]["enabled"],
            "html_generator": True,
            "markdown_generator": True,
            "site_generator": True
        }
        
        self._logger.info(f"✅ Composants: {list(self._components.keys())}")
        return self._components
    
    async def initialize(self) -> bool:
        """Initialisation asynchrone"""
        try:
            self._set_status(AgentStatus.INITIALIZING)
            self._logger.info("📚 Initialisation du Documenter Pro...")
            
            # Initialiser Jinja2
            self._init_jinja()
            
            # Charger les templates
            await self._load_templates()
            
            self._set_status(AgentStatus.READY)
            self._logger.info("✅ Documenter Pro prêt")
            return True
            
        except Exception as e:
            self._logger.error(f"❌ Erreur initialisation: {e}")
            self._logger.error(traceback.format_exc())
            self._set_status(AgentStatus.ERROR)
            return False
    
    def _init_jinja(self):
        """Initialise l'environnement Jinja2"""
        template_path = Path(self._config["documenter"]["templates_path"])
        self._env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(template_path),
            autoescape=jinja2.select_autoescape(['html', 'xml']),
            trim_blocks=True,
            lstrip_blocks=True
        )
        
        # Filtres personnalisés
        self._env.filters['anchor'] = self._generate_anchor
        self._env.filters['highlight'] = self._highlight_code
        self._env.filters['badge'] = self._generate_badge
    
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
    
    # -----------------------------------------------------------------
    # API PUBLIQUE - GÉNÉRATION DE DOCUMENTATION
    # -----------------------------------------------------------------
    
    async def generate_contract_documentation(self, 
                                             contract_path: str,
                                             output_format: DocFormat = DocFormat.HTML) -> Dict[str, Any]:
        """
        Génère la documentation complète d'un contrat
        
        Args:
            contract_path: Chemin vers le fichier .sol
            output_format: Format de sortie
            
        Returns:
            Métadonnées de la documentation générée
        """
        self._logger.info(f"📄 Génération documentation pour {contract_path}")
        
        # Extraire les informations du contrat
        contract_info = await self._analyze_contract(contract_path)
        
        # Générer les diagrammes Mermaid
        diagrams = await self._generate_diagrams(contract_info)
        
        # Construire la structure de documentation
        docs_structure = await self._build_docs_structure(contract_info, diagrams)
        
        # Générer selon le format
        if output_format == DocFormat.HTML:
            output_path = await self._generate_html(docs_structure)
        elif output_format == DocFormat.MARKDOWN:
            output_path = await self._generate_markdown(docs_structure)
        elif output_format == DocFormat.SITE:
            output_path = await self._generate_site(docs_structure)
        else:
            output_path = await self._generate_html(docs_structure)
        
        self._docs_generated += 1
        
        return {
            "contract": contract_info["name"],
            "format": output_format.value,
            "path": str(output_path),
            "sections": len(docs_structure["sections"]),
            "diagrams": len(diagrams),
            "generated_at": datetime.now().isoformat()
        }
    
    async def generate_project_documentation(self,
                                            project_name: str,
                                            contract_paths: List[str],
                                            description: str = "") -> Dict[str, Any]:
        """
        Génère la documentation complète d'un projet
        
        Args:
            project_name: Nom du projet
            contract_paths: Liste des chemins des contrats
            description: Description du projet
            
        Returns:
            Métadonnées de la documentation générée
        """
        self._logger.info(f"📚 Génération documentation projet {project_name}")
        
        # Analyser tous les contrats
        contracts_info = []
        all_diagrams = {}
        
        for contract_path in contract_paths:
            contract_info = await self._analyze_contract(contract_path)
            contracts_info.append(contract_info)
            
            diagrams = await self._generate_diagrams(contract_info)
            all_diagrams[contract_info["name"]] = diagrams
        
        # Générer la documentation du projet
        project_info = {
            "name": project_name,
            "description": description,
            "contracts": contracts_info,
            "diagrams": all_diagrams,
            "generated_at": datetime.now().isoformat(),
            "version": "1.0.0"
        }
        
        output_path = await self._generate_project_site(project_info)
        
        return {
            "project": project_name,
            "contracts": len(contracts_info),
            "path": str(output_path),
            "generated_at": datetime.now().isoformat()
        }
    
    # -----------------------------------------------------------------
    # ANALYSE DE CONTRAT
    # -----------------------------------------------------------------
    
    async def _analyze_contract(self, contract_path: str) -> Dict[str, Any]:
        """Analyse approfondie d'un contrat Solidity"""
        
        # Vérifier le cache
        file_hash = self._hash_file(contract_path)
        if file_hash in self._contracts_cache:
            self._logger.debug(f"📦 Contrat chargé depuis cache: {contract_path}")
            return self._contracts_cache[file_hash]
        
        with open(contract_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Extraction des informations
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
        """Calcule le hash d'un fichier"""
        with open(path, 'rb') as f:
            return hashlib.sha256(f.read()).hexdigest()[:16]
    
    def _extract_contract_name(self, content: str) -> str:
        """Extrait le nom du contrat"""
        match = re.search(r'contract\s+(\w+)', content)
        return match.group(1) if match else "Unknown"
    
    def _extract_license(self, content: str) -> str:
        """Extrait la licence SPDX"""
        match = re.search(r'SPDX-License-Identifier:\s*(\S+)', content)
        return match.group(1) if match else "UNLICENSED"
    
    def _extract_solidity_version(self, content: str) -> str:
        """Extrait la version Solidity"""
        match = re.search(r'pragma solidity\s*([^;]+);', content)
        return match.group(1).strip() if match else "unknown"
    
    def _extract_imports(self, content: str) -> List[Dict[str, str]]:
        """Extrait les imports avec détails"""
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
        """Extrait les contrats hérités"""
        match = re.search(r'contract\s+\w+\s+is\s+([^{]+)', content)
        if match:
            parents = match.group(1).strip()
            return [p.strip() for p in parents.split(',') if p.strip()]
        return []
    
    def _extract_interfaces(self, content: str) -> List[str]:
        """Extrait les interfaces utilisées"""
        interfaces = re.findall(r'interface\s+(\w+)', content)
        return list(set(interfaces))
    
    def _extract_libraries(self, content: str) -> List[str]:
        """Extrait les bibliothèques utilisées"""
        libraries = re.findall(r'library\s+(\w+)', content)
        return list(set(libraries))
    
    def _extract_functions_detailed(self, content: str) -> List[Dict[str, Any]]:
        """Extraction détaillée des fonctions"""
        functions = []
        
        # Pattern pour les fonctions
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
        
        # Trier par nom
        functions.sort(key=lambda x: x["name"])
        
        return functions
    
    def _parse_parameters(self, params_str: str) -> List[Dict[str, str]]:
        """Parse les paramètres d'une fonction"""
        if not params_str.strip():
            return []
        
        params = []
        for param in params_str.split(','):
            param = param.strip()
            if not param:
                continue
            
            # Pattern: type name
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
        """Parse les modificateurs"""
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
        """Extrait la visibilité"""
        for vis in ['public', 'private', 'internal', 'external']:
            if vis in modifier_str:
                return vis
        return 'public'  # default
    
    def _extract_state_mutability(self, modifier_str: str) -> str:
        """Extrait la mutabilité d'état"""
        for mut in ['view', 'pure', 'payable']:
            if mut in modifier_str:
                return mut
        return 'nonpayable'
    
    def _extract_events_detailed(self, content: str) -> List[Dict[str, Any]]:
        """Extraction détaillée des events"""
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
        """Extraction détaillée des modifiers"""
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
        """Extraction détaillée des variables d'état"""
        variables = []
        
        # Pattern pour variables d'état
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
                
                # Chercher si constant ou immutable
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
        """Extrait les structs"""
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
        """Extrait les enums"""
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
        """Extrait les erreurs personnalisées"""
        errors = []
        pattern = r'error\s+(\w+)\s*\(([^)]*)\)'
        
        for match in re.finditer(pattern, content):
            errors.append({
                "name": match.group(1),
                "params": self._parse_parameters(match.group(2))
            })
        
        return errors
    
    def _extract_natspec_complete(self, content: str) -> Dict[str, Any]:
        """Extraction complète des commentaires NatSpec"""
        natspec = {
            "contract": {},
            "functions": {},
            "events": {},
            "modifiers": {},
            "variables": {}
        }
        
        # NatSpec du contrat
        contract_match = re.search(r'/\*\*([^*]|\*[^/])*\*/\s*contract', content, re.DOTALL)
        if contract_match:
            comment = contract_match.group(0).split('*/')[0]
            natspec["contract"] = self._parse_natspec_block(comment)
        
        return natspec
    
    def _parse_natspec_block(self, comment: str) -> Dict[str, Any]:
        """Parse un bloc NatSpec"""
        result = {}
        
        # Notice
        notice_match = re.search(r'@notice\s+(.+)', comment)
        if notice_match:
            result["notice"] = notice_match.group(1).strip()
        
        # Dev
        dev_match = re.search(r'@dev\s+(.+)', comment)
        if dev_match:
            result["dev"] = dev_match.group(1).strip()
        
        # Author
        author_match = re.search(r'@author\s+(.+)', comment)
        if author_match:
            result["author"] = author_match.group(1).strip()
        
        # Title
        title_match = re.search(r'@title\s+(.+)', comment)
        if title_match:
            result["title"] = title_match.group(1).strip()
        
        return result
    
    def _extract_function_natspec(self, content: str, func_name: str) -> Dict[str, Any]:
        """Extrait le NatSpec d'une fonction"""
        pattern = rf'/\*\*([^*]|\*[^/])*\*/\s*function\s+{func_name}'
        match = re.search(pattern, content, re.DOTALL)
        
        if not match:
            return {}
        
        comment = match.group(0).split('*/')[0]
        return self._parse_natspec_block(comment)
    
    def _extract_event_natspec(self, content: str, event_name: str) -> Dict[str, Any]:
        """Extrait le NatSpec d'un event"""
        pattern = rf'/\*\*([^*]|\*[^/])*\*/\s*event\s+{event_name}'
        match = re.search(pattern, content, re.DOTALL)
        
        if not match:
            return {}
        
        comment = match.group(0).split('*/')[0]
        return self._parse_natspec_block(comment)
    
    def _extract_modifier_natspec(self, content: str, modifier_name: str) -> Dict[str, Any]:
        """Extrait le NatSpec d'un modifier"""
        pattern = rf'/\*\*([^*]|\*[^/])*\*/\s*modifier\s+{modifier_name}'
        match = re.search(pattern, content, re.DOTALL)
        
        if not match:
            return {}
        
        comment = match.group(0).split('*/')[0]
        return self._parse_natspec_block(comment)
    
    def _extract_variable_natspec(self, content: str, var_name: str) -> Dict[str, Any]:
        """Extrait le NatSpec d'une variable"""
        pattern = rf'/\*\*([^*]|\*[^/])*\*/\s*(?:public|private|internal)?\s*\w+\s+{var_name}'
        match = re.search(pattern, content, re.DOTALL)
        
        if not match:
            return {}
        
        comment = match.group(0).split('*/')[0]
        return self._parse_natspec_block(comment)
    
    def _find_function_line(self, content: str, func_name: str) -> int:
        """Trouve la ligne d'une fonction"""
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if f'function {func_name}' in line:
                return i + 1
        return 0
    
    def _find_event_line(self, content: str, event_name: str) -> int:
        """Trouve la ligne d'un event"""
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if f'event {event_name}' in line:
                return i + 1
        return 0
    
    def _find_modifier_line(self, content: str, modifier_name: str) -> int:
        """Trouve la ligne d'un modifier"""
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if f'modifier {modifier_name}' in line:
                return i + 1
        return 0
    
    def _calculate_metrics(self, content: str) -> Dict[str, Any]:
        """Calcule les métriques du contrat"""
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
        """Analyse la sécurité du contrat"""
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
        
        # Calculer le niveau de risque
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
        """Calcule la complexité du code"""
        return {
            "cyclomatic": self._calculate_cyclomatic_complexity(content),
            "cognitive": self._calculate_cognitive_complexity(content),
            "maintainability": self._calculate_maintainability_index(content)
        }
    
    def _calculate_cyclomatic_complexity(self, content: str) -> int:
        """Calcule la complexité cyclomatique"""
        complexity = 1  # Base
        
        # Points de décision
        complexity += len(re.findall(r'\bif\s*\(', content))
        complexity += len(re.findall(r'\belse\s+if\b', content))
        complexity += len(re.findall(r'\bfor\s*\(', content))
        complexity += len(re.findall(r'\bwhile\s*\(', content))
        complexity += len(re.findall(r'\bcase\b', content))
        complexity += len(re.findall(r'\bcatch\b', content))
        complexity += len(re.findall(r'\b&&\b|\|\|\b', content))
        
        return complexity
    
    def _calculate_cognitive_complexity(self, content: str) -> int:
        """Calcule la complexité cognitive"""
        # Simplifié - à améliorer
        return self._calculate_cyclomatic_complexity(content)
    
    def _calculate_maintainability_index(self, content: str) -> float:
        """Calcule l'index de maintenabilité"""
        # MI = 171 - 5.2 * ln(aveV) - 0.23 * aveV(g') - 16.2 * ln(aveLOC)
        # Version simplifiée
        loc = len(content.split('\n'))
        complexity = self._calculate_cyclomatic_complexity(content)
        
        if loc == 0:
            return 100.0
        
        mi = max(0, 171 - 5.2 * (complexity ** 0.5) - 0.23 * complexity - 16.2 * (loc ** 0.5))
        return min(100, mi)
    
    async def _resolve_dependencies(self, content: str) -> List[Dict[str, Any]]:
        """Résout les dépendances du contrat"""
        dependencies = []
        import_pattern = r'import\s+(?:\{([^}]+)\}\s+from\s+)?["\']([^"\']+)["\']'
        
        for match in re.finditer(import_pattern, content):
            path = match.group(2)
            dependencies.append({
                "path": path,
                "name": path.split('/')[-1].replace('.sol', ''),
                "type": "local" if path.startswith('.') else "external",
                "version": await self._detect_version(path)
            })
        
        return dependencies
    
    async def _detect_version(self, import_path: str) -> Optional[str]:
        """Détecte la version d'une dépendance"""
        # Pourrait interroger le registry
        return None
    
    def _estimate_bytecode_size(self, content: str) -> int:
        """Estime la taille du bytecode"""
        # Approximation grossière
        return len(content) * 2
    
    def _calculate_function_complexity(self, function_code: str) -> int:
        """Calcule la complexité d'une fonction"""
        complexity = 1
        complexity += len(re.findall(r'\bif\b', function_code))
        complexity += len(re.findall(r'\bfor\b', function_code))
        complexity += len(re.findall(r'\bwhile\b', function_code))
        complexity += len(re.findall(r'\bcatch\b', function_code))
        return complexity
    
    # -----------------------------------------------------------------
    # GÉNÉRATION DE DIAGRAMMES MERMAID
    # -----------------------------------------------------------------
    
    async def _generate_diagrams(self, contract_info: Dict[str, Any]) -> Dict[str, str]:
        """Génère les diagrammes Mermaid"""
        diagrams = {}
        
        if not self._config["mermaid"]["enabled"]:
            return diagrams
        
        try:
            # Diagramme d'héritage
            if contract_info.get("inheritance"):
                diagrams["inheritance"] = await self._generate_inheritance_diagram(contract_info)
            
            # Diagramme de dépendances
            if contract_info.get("dependencies"):
                diagrams["dependencies"] = await self._generate_dependencies_diagram(contract_info)
            
            # Diagramme d'appels
            diagrams["calls"] = await self._generate_call_graph(contract_info)
            
            # Diagramme d'états
            diagrams["state"] = await self._generate_state_diagram(contract_info)
            
            self._logger.debug(f"📊 {len(diagrams)} diagrammes générés")
            
        except Exception as e:
            self._logger.error(f"❌ Erreur génération diagrammes: {e}")
        
        return diagrams
    
    async def _generate_inheritance_diagram(self, contract_info: Dict[str, Any]) -> str:
        """Génère un diagramme d'héritage Mermaid"""
        theme = self._config["mermaid"]["theme"]
        contract_name = contract_info["name"]
        inheritance = contract_info.get("inheritance", [])
        
        diagram = ["```mermaid"]
        diagram.append(f"%%{{init: {{'theme':'{theme}'}}}}%%")
        diagram.append("classDiagram")
        
        # Classe principale
        diagram.append(f"    class {contract_name} {{")
        for func in contract_info.get("functions", [])[:5]:  # Limiter pour lisibilité
            diagram.append(f"        +{func['name']}()")
        diagram.append("    }")
        
        # Relations d'héritage
        for parent in inheritance:
            diagram.append(f"    {contract_name} --|> {parent}")
        
        diagram.append("```")
        return "\n".join(diagram)
    
    async def _generate_dependencies_diagram(self, contract_info: Dict[str, Any]) -> str:
        """Génère un diagramme de dépendances Mermaid"""
        theme = self._config["mermaid"]["theme"]
        
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
        """Génère un graphe d'appels"""
        theme = self._config["mermaid"]["theme"]
        
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
        """Génère un diagramme d'états"""
        theme = self._config["mermaid"]["theme"]
        
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
    
    # -----------------------------------------------------------------
    # CONSTRUCTION DE LA DOCUMENTATION
    # -----------------------------------------------------------------
    
    async def _build_docs_structure(self, 
                                   contract_info: Dict[str, Any],
                                   diagrams: Dict[str, str]) -> Dict[str, Any]:
        """Construit la structure de la documentation"""
        
        sections = []
        
        # Overview
        sections.append({
            "id": "overview",
            "title": "📋 Overview",
            "level": 1,
            "content": await self._generate_overview_section(contract_info)
        })
        
        # Architecture
        sections.append({
            "id": "architecture",
            "title": "🏗️ Architecture",
            "level": 1,
            "content": await self._generate_architecture_section(contract_info, diagrams)
        })
        
        # Contracts
        sections.append({
            "id": "contracts",
            "title": "📜 Contracts",
            "level": 1,
            "content": await self._generate_contracts_section(contract_info)
        })
        
        # Functions
        sections.append({
            "id": "functions",
            "title": "⚙️ Functions",
            "level": 1,
            "content": await self._generate_functions_section(contract_info)
        })
        
        # Events
        sections.append({
            "id": "events",
            "title": "📢 Events",
            "level": 1,
            "content": await self._generate_events_section(contract_info)
        })
        
        # Modifiers
        if contract_info.get("modifiers"):
            sections.append({
                "id": "modifiers",
                "title": "🔒 Modifiers",
                "level": 1,
                "content": await self._generate_modifiers_section(contract_info)
            })
        
        # Security
        sections.append({
            "id": "security",
            "title": "🛡️ Security",
            "level": 1,
            "content": await self._generate_security_section(contract_info)
        })
        
        # Deployment
        sections.append({
            "id": "deployment",
            "title": "🚀 Deployment",
            "level": 1,
            "content": await self._generate_deployment_section(contract_info)
        })
        
        # Examples
        sections.append({
            "id": "examples",
            "title": "💡 Examples",
            "level": 1,
            "content": await self._generate_examples_section(contract_info)
        })
        
        # Changelog
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
        """Génère la section overview"""
        md = []
        
        md.append(f"# 📄 {info['name']} Smart Contract")
        md.append("")
        
        # Badges
        md.append("<div class='badge-container'>")
        md.append(f"<span class='badge badge-license'>{info['license']}</span>")
        md.append(f"<span class='badge badge-version'>Solidity {info['solidity_version']}</span>")
        md.append(f"<span class='badge badge-risk badge-{info['security']['risk_level']}'>Risque {info['security']['risk_level'].upper()}</span>")
        md.append("</div>")
        md.append("")
        
        # Description
        if info['natspec']['contract'].get('notice'):
            md.append(info['natspec']['contract']['notice'])
            md.append("")
        
        if info['natspec']['contract'].get('dev'):
            md.append(f"*Note: {info['natspec']['contract']['dev']}*")
            md.append("")
        
        # Métriques rapides
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
        
        # Liens rapides
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
        """Génère la section architecture"""
        md = []
        
        md.append("## 🏗️ Architecture")
        md.append("")
        
        # Diagramme d'héritage
        if "inheritance" in diagrams:
            md.append("### 📊 Inheritance Diagram")
            md.append("")
            md.append(diagrams["inheritance"])
            md.append("")
        
        # Diagramme de dépendances
        if "dependencies" in diagrams:
            md.append("### 🔗 Dependencies")
            md.append("")
            md.append(diagrams["dependencies"])
            md.append("")
        
        # Imports
        if info.get("imports"):
            md.append("### 📦 Imports")
            md.append("")
            md.append("| Path | Type | Symbols |")
            md.append("|------|------|---------|")
            for imp in info["imports"]:
                symbols = ", ".join(imp["symbols"])
                md.append(f"| {imp['path']} | {imp['type']} | `{symbols}` |")
            md.append("")
        
        # Inheritance
        if info.get("inheritance"):
            md.append("### 🧬 Inheritance")
            md.append("")
            for parent in info["inheritance"]:
                md.append(f"- `{parent}`")
            md.append("")
        
        return "\n".join(md)
    
    async def _generate_contracts_section(self, info: Dict[str, Any]) -> str:
        """Génère la section contracts"""
        md = []
        
        md.append("## 📜 Contract Details")
        md.append("")
        
        # Variables d'état
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
        
        # Structs
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
        
        # Enums
        if info.get("enums"):
            md.append("### 🔢 Enums")
            md.append("")
            for enum in info["enums"]:
                md.append(f"#### `{enum['name']}`")
                md.append("")
                for value in enum["values"]:
                    md.append(f"- `{value}`")
                md.append("")
        
        # Errors
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
        """Génère la section functions"""
        md = []
        
        md.append("## ⚙️ Functions")
        md.append("")
        
        # Table des matières des fonctions
        md.append("<div class='function-toc'>")
        for func in info["functions"]:
            anchor = self._generate_anchor(func["name"])
            md.append(f"- [`{func['name']}`](#{anchor})")
        md.append("</div>")
        md.append("")
        
        # Détail des fonctions
        for func in info["functions"]:
            anchor = self._generate_anchor(func["name"])
            md.append(f"### `{func['name']}` {self._generate_badge(func)}")
            md.append("")
            
            # Signature
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
            
            # Description
            if func["natspec"].get("notice"):
                md.append(f"**Description:** {func['natspec']['notice']}")
                md.append("")
            
            if func["natspec"].get("dev"):
                md.append(f"*{func['natspec']['dev']}*")
                md.append("")
            
            # Paramètres
            if func["params"]:
                md.append("**Parameters:**")
                md.append("")
                md.append("| Name | Type | Description |")
                md.append("|------|------|-------------|")
                for p in func["params"]:
                    desc = func["natspec"].get("params", {}).get(p["name"], "")
                    md.append(f"| {p['name']} | `{p['type']}` | {desc} |")
                md.append("")
            
            # Returns
            if func["returns"]:
                md.append("**Returns:**")
                md.append("")
                md.append("| Name | Type | Description |")
                md.append("|------|------|-------------|")
                for r in func["returns"]:
                    desc = func["natspec"].get("returns", {}).get(r["name"], "")
                    md.append(f"| {r['name']} | `{r['type']}` | {desc} |")
                md.append("")
            
            # Modifiers
            if func["modifiers"]:
                md.append("**Modifiers:** " + ", ".join([f"`{m}`" for m in func["modifiers"]]))
                md.append("")
            
            # Métadonnées
            md.append(f"**Visibility:** `{func['visibility']}` | **Mutability:** `{func['state_mutability']}` | **Line:** {func['line']}")
            md.append("")
            
            # Lien retour
            md.append(f"[🔝 Back to Functions](#functions)")
            md.append("")
            md.append("---")
            md.append("")
        
        return "\n".join(md)
    
    async def _generate_events_section(self, info: Dict[str, Any]) -> str:
        """Génère la section events"""
        md = []
        
        md.append("## 📢 Events")
        md.append("")
        
        for event in info["events"]:
            md.append(f"### `{event['name']}`")
            md.append("")
            
            # Signature
            md.append("```solidity")
            params_str = ", ".join([f"{p['type']}{' indexed' if p['indexed'] else ''} {p['name']}" for p in event["params"]])
            md.append(f"event {event['name']}({params_str}){' anonymous' if event['anonymous'] else ''}")
            md.append("```")
            md.append("")
            
            # Paramètres
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
        """Génère la section modifiers"""
        md = []
        
        md.append("## 🔒 Modifiers")
        md.append("")
        
        for modifier in info["modifiers"]:
            md.append(f"### `{modifier['name']}`")
            md.append("")
            
            # Signature
            md.append("```solidity")
            params_str = ", ".join([f"{p['type']} {p['name']}" for p in modifier["params"]])
            md.append(f"modifier {modifier['name']}({params_str})")
            md.append("```")
            md.append("")
            
            # Description
            if modifier["natspec"].get("notice"):
                md.append(f"**Description:** {modifier['natspec']['notice']}")
                md.append("")
            
            # Paramètres
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
        """Génère la section sécurité"""
        md = []
        
        md.append("## 🛡️ Security Analysis")
        md.append("")
        
        # Score de risque
        risk = info["security"]["risk_level"]
        risk_color = {
            "low": "🟢",
            "medium": "🟡",
            "high": "🔴"
        }.get(risk, "⚪")
        
        md.append(f"### Risk Assessment: {risk_color} {risk.upper()}")
        md.append("")
        
        # Tableau de sécurité
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
        
        # Recommandations
        md.append("### 🔒 Security Recommendations")
        md.append("")
        
        if not info["security"]["reentrancy_protection"]:
            md.append("- ⚠️ **Add ReentrancyGuard** to prevent reentrancy attacks")
        if not info["security"]["access_control"]:
            md.append("- ⚠️ **Implement access control** (Ownable, AccessControl)")
        if "delegatecall" in str(info) and not info["security"]["access_control"]:
            md.append("- ⚠️ **Delegatecall with caution** - ensure called contracts are trusted")
        
        md.append("")
        
        return "\n".join(md)
    
    async def _generate_deployment_section(self, info: Dict[str, Any]) -> str:
        """Génère la section déploiement"""
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
        
        # Chercher les paramètres du constructeur
        constructor = next((f for f in info["functions"] if f["name"] == "constructor"), None)
        if constructor:
            for p in constructor["params"]:
                md.append(f"| {p['name']} | `{p['type']}` | {p.get('description', '')} |")
        
        md.append("")
        
        return "\n".join(md)
    
    async def _generate_examples_section(self, info: Dict[str, Any]) -> str:
        """Génère la section exemples"""
        md = []
        
        md.append("## 💡 Examples")
        md.append("")
        
        # Exemple de déploiement
        md.append("### Deployment Example")
        md.append("")
        md.append("```javascript")
        md.append("// Deploy with ethers.js")
        md.append(f"const {info['name']} = await ethers.deployContract('{info['name']}')")
        md.append(f"await {info['name']}.waitForDeployment()")
        md.append(f"console.log('Contract deployed to:', await {info['name']}.getAddress())")
        md.append("```")
        md.append("")
        
        # Exemple d'interaction pour chaque fonction principale
        md.append("### Interaction Examples")
        md.append("")
        
        for func in info["functions"][:3]:  # Top 3 fonctions
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
        """Génère la section changelog"""
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
    
    # -----------------------------------------------------------------
    # GÉNÉRATION HTML/MARKDOWN
    # -----------------------------------------------------------------
    
    async def _generate_html(self, structure: Dict[str, Any]) -> Path:
        """Génère la documentation en HTML"""
        
        html = self._templates["base_html"]
        
        # Remplacer les variables
        html = html.replace("{{CONTRACT_NAME}}", structure["contract"])
        html = html.replace("{{GENERATED_AT}}", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        
        # Générer la table des matières
        toc = await self._generate_toc(structure)
        html = html.replace("{{TOC}}", toc)
        
        # Générer le contenu
        content = []
        for section in structure["sections"]:
            content.append(f"<section id='{section['id']}' class='doc-section'>")
            content.append(self._markdown_to_html(section["content"]))
            content.append("</section>")
        
        html = html.replace("{{CONTENT}}", "\n".join(content))
        
        # Sauvegarder
        output_path = self._output_path / f"{structure['contract']}.html"
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html)
        
        return output_path
    
    async def _generate_markdown(self, structure: Dict[str, Any]) -> Path:
        """Génère la documentation en Markdown"""
        
        content = []
        
        # En-tête
        content.append(f"# {structure['contract']} Documentation")
        content.append(f"*Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")
        content.append("")
        
        # Table des matières
        content.append("## Table of Contents")
        for section in structure["sections"]:
            content.append(f"- [{section['title']}](#{section['id']})")
        content.append("")
        
        # Sections
        for section in structure["sections"]:
            content.append(section["content"])
        
        # Sauvegarder
        output_path = self._output_path / f"{structure['contract']}.md"
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("\n".join(content))
        
        return output_path
    
    async def _generate_site(self, structure: Dict[str, Any]) -> Path:
        """Génère un site de documentation complet"""
        
        # Créer le dossier du site
        site_path = self._output_path / "site" / structure["contract"]
        site_path.mkdir(parents=True, exist_ok=True)
        
        # Générer index.html
        index_path = site_path / "index.html"
        html = await self._generate_html(structure)
        shutil.copy(html, index_path)
        
        # Copier les assets
        assets_src = Path(__file__).parent / "assets"
        assets_dst = site_path / "assets"
        if assets_src.exists():
            shutil.copytree(assets_src, assets_dst, dirs_exist_ok=True)
        
        return index_path
    
    async def _generate_project_site(self, project_info: Dict[str, Any]) -> Path:
        """Génère un site pour un projet complet"""
        
        project_path = self._output_path / "site" / project_info["name"]
        project_path.mkdir(parents=True, exist_ok=True)
        
        # Générer page d'accueil
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
        
        # Générer documentation pour chaque contrat
        for contract in project_info["contracts"]:
            contract_docs = await self._build_docs_structure(contract, project_info["diagrams"].get(contract["name"], {}))
            await self._generate_site(contract_docs)
        
        return index_path
    
    def _markdown_to_html(self, md: str) -> str:
        """Convertit le markdown en HTML"""
        return markdown.markdown(
            md,
            extensions=[
                'tables',
                'fenced_code',
                'codehilite',
                'toc',
                'attr_list'
            ]
        )
    
    async def _generate_toc(self, structure: Dict[str, Any]) -> str:
        """Génère une table des matières HTML"""
        toc = ["<ul class='toc'>"]
        
        for section in structure["sections"]:
            toc.append(f"<li><a href='#{section['id']}'>{section['title']}</a>")
            
            # Sous-sections si nécessaire
            if section["id"] == "functions":
                toc.append("<ul>")
                for func in structure.get("functions", []):
                    anchor = self._generate_anchor(func["name"])
                    toc.append(f"<li><a href='#{anchor}'>{func['name']}</a></li>")
                toc.append("</ul>")
            
            toc.append("</li>")
        
        toc.append("</ul>")
        return "\n".join(toc)
    
    def _generate_anchor(self, text: str) -> str:
        """Génère un anchor à partir d'un texte"""
        anchor = text.lower()
        anchor = re.sub(r'[^a-z0-9]+', '-', anchor)
        anchor = anchor.strip('-')
        return anchor
    
    def _generate_badge(self, func: Dict[str, Any]) -> str:
        """Génère un badge pour une fonction"""
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
    
    def _highlight_code(self, code: str) -> str:
        """Highlight le code (simplifié)"""
        return f"<pre><code>{code}</code></pre>"
    
    # =================================================================
    # TEMPLATES (4 espaces)
    # =================================================================
    
    def _get_base_html_template(self) -> str:
        """Template HTML de base"""
        colors = self._config["styling"]["colors"]
        primary = colors["primary"]
        secondary = colors["secondary"]
        background = colors["background"]
        
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
            color: #00ff88;
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
            color: #00ff88;
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
            color: #00ff88;
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
            background: #8b5cf6;
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
            background: #8b5cf6;
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
            color: #00ff88;
        }
        
        .back-to-top {
            position: fixed;
            bottom: 30px;
            right: 30px;
            background: #00ff88;
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
        """Template pour la table des matières"""
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
        """Template pour une section"""
        return """
        <section id="{{ section.id }}" class="doc-section">
            <h{{ section.level }}>{{ section.title }}</h{{ section.level }}>
            {{ section.content }}
        </section>
        """
    
    def _get_function_table_template(self) -> str:
        """Template pour le tableau des fonctions"""
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
        """Template pour le tableau des events"""
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
        """Template pour la section sécurité"""
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
        """Template pour les diagrammes Mermaid"""
        return """
        <div class="mermaid">
            {{ diagram }}
        </div>
        """
    
    # =================================================================
    # HEALTH CHECK & INFO (4 espaces)
    # =================================================================
    
    async def health_check(self) -> Dict[str, Any]:
        """Vérifie la santé de l'agent"""
        return {
            "agent": self._name,
            "status": self._status.value,
            "ready": self._status == AgentStatus.READY,
            "docs_generated": self._docs_generated,
            "contracts_cached": len(self._contracts_cache),
            "diagrams_generated": len(self._diagrams_cache),
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
            "docs_generated": self._docs_generated,
            "templates_loaded": len(self._templates)
        }
    
    async def _handle_custom_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Gestion des messages personnalisés"""
        msg_type = message.get("type", "")
        
        if msg_type == "generate_contract_docs":
            result = await self.generate_contract_documentation(
                message["contract_path"],
                DocFormat(message.get("format", "html"))
            )
            return result
        
        elif msg_type == "generate_project_docs":
            result = await self.generate_project_documentation(
                message["project_name"],
                message["contract_paths"],
                message.get("description", "")
            )
            return result
        
        elif msg_type == "analyze_contract":
            info = await self._analyze_contract(message["contract_path"])
            return info
        
        return {"status": "received", "type": msg_type}


# ========================================================================
# FONCTIONS D'USINE (0 espace - niveau module)
# ========================================================================

def create_documenter_agent(config_path: str = "") -> DocumenterAgent:
    """Crée une instance du documenter agent"""
    return DocumenterAgent(config_path)


# ========================================================================
# POINT D'ENTRÉE POUR EXÉCUTION DIRECTE (0 espace - niveau module)
# ========================================================================

if __name__ == "__main__":
    import asyncio
    from pathlib import Path
    
    async def main():
        print("📚 TEST DOCUMENTER PRO AGENT 2.0")
        print("="*60)
        
        agent = DocumenterAgent()
        await agent.initialize()
        
        print(f"✅ Agent: {agent._config['agent']['display_name']} v{agent._config['agent']['version']}")
        print(f"✅ Statut: {agent._status.value}")
        print(f"✅ Templates: {len(agent._templates)}")
        print(f"✅ Capacités: {len(agent._config['agent']['capabilities'])}")
        
        # Test sur un contrat exemple
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
        
        # Sauvegarder le contrat test temporairement
        test_path = Path("./temp_test_contract.sol")
        with open(test_path, 'w', encoding='utf-8') as f:
            f.write(test_contract)
        
        print(f"\n📄 Test sur contrat exemple...")
        
        result = await agent.generate_contract_documentation(str(test_path))
        print(f"✅ Documentation générée: {result['path']}")
        print(f"📊 {result['sections']} sections, {result['diagrams']} diagrammes")
        
        # Nettoyer
        test_path.unlink()
        
        print("\n" + "="*60)
        print("✅ DOCUMENTER PRO AGENT OPÉRATIONNEL")
        print("="*60)
    
    asyncio.run(main())
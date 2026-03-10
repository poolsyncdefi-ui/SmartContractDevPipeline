"""
Coder Agent - Agent principal de développement de code
Implémente le code backend, frontend, DevOps, tests et documentation
basé sur l'architecture conçue par l'Architect Agent.
Version: 1.0.0 (ALIGNÉ)
"""

import os
import sys
import yaml
import json
import logging
import asyncio
from pathlib import Path
from typing import Dict, List, Any, Optional, Union, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)

# Ajouter le chemin du projet au PYTHONPATH
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from agents.base_agent.base_agent import BaseAgent, AgentStatus, Message


# -----------------------------------------------------------------------------
# CLASSES DE DONNÉES
# -----------------------------------------------------------------------------

class CodeLanguage(Enum):
    """Langages de programmation supportés"""
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
    SOLIDITY = "solidity"
    RUST = "rust"
    GO = "go"
    JAVA = "java"
    CSHARP = "csharp"


class Framework(Enum):
    """Frameworks supportés"""
    FASTAPI = "fastapi"
    EXPRESS = "express"
    NEXTJS = "nextjs"
    REACT = "react"
    VUE = "vue"
    HARDFHAT = "hardhat"
    ANCHOR = "anchor"


class ComponentType(Enum):
    """Types de composants logiciels"""
    BACKEND_SERVICE = "backend_service"
    FRONTEND_APP = "frontend_application"
    SMART_CONTRACT = "smart_contract"
    DATABASE = "database"
    API_GATEWAY = "api_gateway"


class GenerationStatus(Enum):
    """Statuts de génération de code"""
    PENDING = "pending"
    GENERATING = "generating"
    COMPLETED = "completed"
    FAILED = "failed"
    VALIDATING = "validating"


@dataclass
class CodeComponent:
    """Représente un composant de code à générer"""
    id: str
    name: str
    component_type: ComponentType
    language: CodeLanguage
    framework: Optional[Framework] = None
    description: str = ""
    dependencies: List[str] = field(default_factory=list)
    output_path: Optional[Path] = None
    config: Dict[str, Any] = field(default_factory=dict)
    status: GenerationStatus = GenerationStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class GeneratedFile:
    """Représente un fichier généré"""
    path: Path
    content: str
    language: CodeLanguage
    size_bytes: int
    line_count: int
    generated_at: datetime = field(default_factory=datetime.now)


@dataclass
class GenerationResult:
    """Résultat de la génération de code"""
    success: bool
    component_id: str
    component_name: str
    output_path: Path
    files_created: List[GeneratedFile] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)


# -----------------------------------------------------------------------------
# CLASSE CODER AGENT
# -----------------------------------------------------------------------------

class CoderAgent(BaseAgent):
    """
    Agent responsable du développement complet du code.
    Génère le code backend, frontend, DevOps, tests et documentation
    basé sur l'architecture conçue par l'Architect Agent.
    """

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialise l'agent Coder.

        Args:
            config_path: Chemin vers le fichier de configuration (optionnel)
        """
        # Déterminer le chemin de configuration
        if config_path is None:
            config_path = str(project_root / "agents" / "coder" / "config.yaml")

        # Initialiser l'agent de base
        super().__init__(config_path)

        # Configuration spécifique au Coder
        self._coder_config = self.load_coder_config()

        # État de l'agent
        self.current_plan = None
        self.generated_components: Dict[str, GenerationResult] = {}
        self.code_templates: Dict[str, str] = {}

        # Sous-agents
        self._sub_agents: Dict[str, Any] = {}

        # Initialiser les templates
        self._initialize_templates()

        self._logger.info(f"Agent Coder initialisé avec la configuration de {config_path}")

    async def initialize(self) -> bool:
        """
        Initialise l'agent Coder.

        Returns:
            True si l'initialisation a réussi
        """
        return await super().initialize()

    async def _initialize_components(self) -> bool:
        """
        Initialise les composants spécifiques du CoderAgent.

        Returns:
            True si l'initialisation a réussi
        """
        try:
            self._logger.info("Initialisation des composants du CoderAgent...")

            # Initialiser les templates
            self._initialize_templates()

            # Charger les configurations
            self._load_framework_configs()

            # Initialiser les sous-agents
            await self._initialize_sub_agents()

            self._logger.info("Composants du CoderAgent initialisés avec succès")
            return True

        except Exception as e:
            self._logger.error(f"Erreur lors de l'initialisation des composants: {e}")
            return False

    async def _initialize_sub_agents(self):
        """Initialise les sous-agents spécialisés"""
        try:
            # Import des sous-agents si disponibles
            try:
                from .sous_agents import (
                    BackendCoderSubAgent,
                    FrontendCoderSubAgent,
                    DevopsCoderSubAgent
                )
                
                # Initialiser les sous-agents
                self._sub_agents = {
                    "backend": BackendCoderSubAgent(),
                    "frontend": FrontendCoderSubAgent(),
                    "devops": DevopsCoderSubAgent()
                }
                self._logger.info(f"Sous-agents initialisés: {list(self._sub_agents.keys())}")
            except ImportError as e:
                self._logger.debug(f"Aucun sous-agent trouvé: {e}")
                self._sub_agents = {}
                
        except Exception as e:
            self._logger.error(f"Erreur lors de l'initialisation des sous-agents: {e}")
            self._sub_agents = {}

    # -------------------------------------------------------------------------
    # MÉTHODES DE CONFIGURATION
    # -------------------------------------------------------------------------

    def load_coder_config(self) -> Dict[str, Any]:
        """
        Charge la configuration spécifique au Coder.

        Returns:
            Dict contenant la configuration
        """
        return self._agent_config.get('configuration', {})

    def _initialize_templates(self):
        """Initialise les templates de code par défaut"""
        self.code_templates = {
            "python_fastapi_service": self._get_fastapi_template(),
            "javascript_express_service": self._get_express_template(),
            "react_component": self._get_react_template(),
            "solidity_contract": self._get_solidity_template(),
        }

    def _load_framework_configs(self):
        """Charge les configurations des frameworks supportés"""
        config_dir = project_root / "agents" / "coder" / "frameworks"

        if config_dir.exists():
            for config_file in config_dir.glob("*.yaml"):
                try:
                    with open(config_file, 'r', encoding='utf-8') as f:
                        framework_name = config_file.stem
                        self._logger.debug(f"Configuration chargée pour {framework_name}")
                except Exception as e:
                    self._logger.warning(f"Impossible de charger {config_file}: {e}")

    # -------------------------------------------------------------------------
    # MÉTHODES DE GÉNÉRATION DE CODE
    # -------------------------------------------------------------------------

    async def generate_code(self, plan: Dict[str, Any]) -> Dict[str, Any]:
        """
        Génère le code basé sur le plan d'implémentation.

        Args:
            plan: Plan d'implémentation provenant de l'Architect

        Returns:
            Dictionnaire avec les résultats de la génération
        """
        try:
            self._logger.info("Démarrage de la génération de code...")

            # Valider le plan
            if not self._validate_implementation_plan(plan):
                return {
                    "success": False,
                    "error": "Plan d'implémentation invalide",
                    "components_generated": 0
                }

            # Créer les composants
            components = self._create_components_from_plan(plan)

            # Générer les composants
            results = []
            for component in components:
                result = await self._generate_component(component)
                self.generated_components[component.name] = result
                results.append(result)

            success = all(r.success for r in results)

            return {
                "success": success,
                "total_components": len(results),
                "successful_components": sum(1 for r in results if r.success),
                "failed_components": [r.component_name for r in results if not r.success],
                "output_directory": str(self._get_output_directory())
            }

        except Exception as e:
            self._logger.error(f"Erreur lors de la génération de code: {e}")
            return {
                "success": False,
                "error": str(e),
                "components_generated": 0
            }

    def _validate_implementation_plan(self, plan: Dict[str, Any]) -> bool:
        """
        Valide le plan d'implémentation.

        Args:
            plan: Plan à valider

        Returns:
            True si le plan est valide
        """
        required_fields = ['architecture_id', 'components']

        for field in required_fields:
            if field not in plan:
                self._logger.error(f"Champ manquant dans le plan: {field}")
                return False

        if not isinstance(plan['components'], list):
            self._logger.error("Le champ 'components' doit être une liste")
            return False

        return True

    def _create_components_from_plan(self, plan_data: Dict[str, Any]) -> List[CodeComponent]:
        """
        Crée des composants à partir des données du plan.

        Args:
            plan_data: Données du plan

        Returns:
            Liste des composants
        """
        components = []

        for comp_data in plan_data['components']:
            try:
                component = CodeComponent(
                    name=comp_data.get('name', f"component_{len(components)}"),
                    component_type=ComponentType(comp_data.get('type', 'backend_service')),
                    language=CodeLanguage(comp_data.get('language', 'python')),
                    framework=Framework(comp_data.get('framework')) if comp_data.get('framework') else None,
                    description=comp_data.get('description', ''),
                    dependencies=comp_data.get('dependencies', []),
                    output_path=Path(comp_data.get('output_path', 'generated_code')),
                    config=comp_data.get('config', {})
                )
                components.append(component)
            except Exception as e:
                self._logger.warning(f"Impossible de créer le composant {comp_data.get('name')}: {e}")

        return components

    async def _generate_component(self, component: CodeComponent) -> GenerationResult:
        """
        Génère un composant de code.

        Args:
            component: Composant à générer

        Returns:
            Résultat de la génération
        """
        try:
            self._logger.info(f"Génération du composant: {component.name}")

            # Créer le répertoire de sortie
            output_dir = component.output_path or self._get_output_directory() / component.name
            output_dir.mkdir(parents=True, exist_ok=True)

            # Déterminer le template à utiliser
            template = self._select_template(component)

            if not template:
                return GenerationResult(
                    success=False,
                    component_name=component.name,
                    output_path=output_dir,
                    errors=[f"Aucun template disponible pour {component.language.value}/{component.component_type.value}"]
                )

            # Remplir le template
            rendered_code = self._render_template(template, component)

            # Déterminer le nom du fichier
            filename = self._get_filename(component)
            filepath = output_dir / filename

            # Écrire le fichier
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(rendered_code)

            return GenerationResult(
                success=True,
                component_name=component.name,
                output_path=output_dir,
                files_created=[filepath]
            )

        except Exception as e:
            self._logger.error(f"Erreur lors de la génération du composant {component.name}: {e}")
            return GenerationResult(
                success=False,
                component_name=component.name,
                output_path=Path(),
                errors=[str(e)]
            )

    def _select_template(self, component: CodeComponent) -> str:
        """
        Sélectionne le template approprié pour un composant.

        Args:
            component: Composant à générer

        Returns:
            Template de code
        """
        template_key = f"{component.language.value}_{component.component_type.value}"

        if template_key in self.code_templates:
            return self.code_templates[template_key]

        # Fallback par langage
        if component.language == CodeLanguage.PYTHON:
            return self.code_templates.get("python_fastapi_service", "")
        elif component.language == CodeLanguage.JAVASCRIPT:
            return self.code_templates.get("javascript_express_service", "")
        elif component.language == CodeLanguage.SOLIDITY:
            return self.code_templates.get("solidity_contract", "")

        return ""

    def _render_template(self, template: str, component: CodeComponent) -> str:
        """
        Remplit un template avec les données du composant.

        Args:
            template: Template à remplir
            component: Données du composant

        Returns:
            Code généré
        """
        # Remplacer les variables de base
        rendered = template.replace("{{ service_name }}", component.name)
        rendered = rendered.replace("{{ component_name }}", component.name)
        rendered = rendered.replace("{{ description }}", component.description)
        rendered = rendered.replace("{{ version }}", "1.0.0")

        # Remplacer les variables spécifiques au langage
        if component.language == CodeLanguage.PYTHON:
            rendered = rendered.replace("{{ model_name }}", f"{component.name.capitalize()}Model")
            rendered = rendered.replace("{{ port }}", str(component.config.get('port', 8000)))
        elif component.language == CodeLanguage.SOLIDITY:
            rendered = rendered.replace("{{ contract_name }}", component.name)
            rendered = rendered.replace("{{ author }}", "SmartContractDevPipeline")
            rendered = rendered.replace("{{ notice }}", component.description)
            rendered = rendered.replace("{{ solidity_version }}", component.config.get('solidity_version', '0.8.19'))

        return rendered

    def _get_filename(self, component: CodeComponent) -> str:
        """
        Détermine le nom de fichier pour un composant.

        Args:
            component: Composant

        Returns:
            Nom de fichier
        """
        extensions = {
            CodeLanguage.PYTHON: ".py",
            CodeLanguage.JAVASCRIPT: ".js",
            CodeLanguage.TYPESCRIPT: ".ts",
            CodeLanguage.SOLIDITY: ".sol",
            CodeLanguage.RUST: ".rs",
            CodeLanguage.GO: ".go",
            CodeLanguage.JAVA: ".java",
            CodeLanguage.CSHARP: ".cs"
        }

        extension = extensions.get(component.language, ".txt")

        if component.component_type == ComponentType.BACKEND_SERVICE:
            return f"main{extension}" if component.language == CodeLanguage.PYTHON else f"index{extension}"
        elif component.component_type == ComponentType.SMART_CONTRACT:
            return f"{component.name}{extension}"
        elif component.component_type == ComponentType.FRONTEND_APP:
            return f"{component.name}{extension}"
        else:
            return f"{component.name}{extension}"

    def _get_output_directory(self) -> Path:
        """Retourne le répertoire de sortie par défaut"""
        output_dir = project_root / "generated_code"
        output_dir.mkdir(exist_ok=True)
        return output_dir

    # -------------------------------------------------------------------------
    # MÉTHODES D'ARCHITECTURE (alignées sur Architect)
    # -------------------------------------------------------------------------

    async def split_spec_into_fragments(self, global_spec: Dict, strategy: str = "largeur_dabord") -> Dict[str, List[Dict]]:
        """
        Découpe une spécification globale en fragments individuels pour le développement.

        Args:
            global_spec: Spécification globale du projet
            strategy: Stratégie de découpage

        Returns:
            Dictionnaire avec les fragments par domaine et les métadonnées
        """
        self._logger.info(f"🔪 Découpage de la spécification en fragments...")

        fragments = {
            "by_domain": {},
            "by_priority": [],
            "by_complexity": [],
            "dependencies": {},
            "metadata": {
                "total_fragments": 0,
                "estimated_sprints": 0,
                "parallel_possible": True
            }
        }

        for fragment in global_spec.get("fragments", []):
            domain = fragment.get("domain", "unknown")

            # Ajouter des métadonnées pour le développement
            fragment["coder_config"] = {
                "max_iterations": 3,
                "validation_level": "comprehensive",
                "generate_tests": True,
                "generate_docs": True
            }

            # Stocker par domaine
            if domain not in fragments["by_domain"]:
                fragments["by_domain"][domain] = []
            fragments["by_domain"][domain].append(fragment)

            # Index par complexité
            complexity = fragment.get("complexity", 5)
            fragments["by_complexity"].append((complexity, fragment))

            # Graphe de dépendances
            deps = []
            for dep in global_spec.get("dependencies", []):
                if dep["from"] == fragment["id"]:
                    deps.append(dep["to"])
            if deps:
                fragments["dependencies"][fragment["id"]] = deps

        # Trier par complexité
        fragments["by_complexity"].sort(key=lambda x: x[0])

        # Calculer les métadonnées
        fragments["metadata"]["total_fragments"] = len(global_spec.get("fragments", []))
        fragments["metadata"]["estimated_sprints"] = self._estimate_sprints(fragments, strategy)

        # Sauvegarder les fragments
        base_dir = Path(f"./specs/fragments/{global_spec.get('project', 'unknown')}")
        base_dir.mkdir(parents=True, exist_ok=True)

        for fragment in global_spec.get("fragments", []):
            frag_file = base_dir / f"{fragment['id']}.json"
            with open(frag_file, 'w', encoding='utf-8') as f:
                json.dump(fragment, f, indent=2)
            self._logger.debug(f"  ✅ Fragment sauvegardé: {frag_file}")

        # Sauvegarder l'index
        index_file = base_dir / "_index.json"
        with open(index_file, 'w', encoding='utf-8') as f:
            json.dump({
                "project": global_spec.get("project", "unknown"),
                "fragments": [f["id"] for f in global_spec.get("fragments", [])],
                "dependencies": fragments["dependencies"],
                "metadata": fragments["metadata"]
            }, f, indent=2)

        self._logger.info(f"✅ Découpage terminé: {fragments['metadata']['total_fragments']} fragments")
        return fragments

    def _estimate_sprints(self, fragments: Dict, strategy: str) -> int:
        """Estime le nombre de sprints nécessaires"""
        if strategy == "largeur_dabord":
            # En largeur, on peut paralléliser
            return max(len(f) for f in fragments["by_domain"].values())
        else:
            # En profondeur, on exécute séquentiellement
            return sum(len(f) for f in fragments["by_domain"].values())

    # -------------------------------------------------------------------------
    # MÉTHODES UTILITAIRES
    # -------------------------------------------------------------------------

    async def validate_code(self, code: str) -> Dict[str, Any]:
        """
        Valide du code.

        Args:
            code: Code à valider

        Returns:
            Résultat de la validation
        """
        try:
            self._logger.info("Validation de code...")

            result = {
                "valid": True,
                "errors": [],
                "warnings": [],
                "suggestions": []
            }

            if not code or len(code.strip()) == 0:
                result["valid"] = False
                result["errors"].append("Code vide")

            self._logger.info(f"Code validé: {result['valid']}")
            return result

        except Exception as e:
            self._logger.error(f"Erreur lors de la validation du code: {e}")
            return {
                "valid": False,
                "errors": [str(e)],
                "warnings": [],
                "suggestions": []
            }

    # -------------------------------------------------------------------------
    # MÉTHODES DE SANTÉ ET D'INFORMATION
    # -------------------------------------------------------------------------

    async def health_check(self) -> Dict[str, Any]:
        """Vérifie la santé de l'agent."""
        base_health = await super().health_check()
        
        return {
            **base_health,
            "agent": self.name,
            "display_name": self._display_name,
            "status": self._status.value,
            "ready": self._status == AgentStatus.READY,
            "templates_loaded": len(self.code_templates),
            "components_generated": len(self.generated_components),
            "sub_agents": list(self._sub_agents.keys()),
            "timestamp": datetime.now().isoformat()
        }

    def get_agent_info(self) -> Dict[str, Any]:
        """Retourne les informations de l'agent."""
        agent_config = self._agent_config.get('agent', {})
        capabilities = agent_config.get('capabilities', [])
        
        if capabilities and isinstance(capabilities[0], dict):
            capabilities = [cap["name"] for cap in capabilities]

        return {
            "id": self.name,
            "name": "CoderAgent",
            "display_name": self._display_name,
            "version": agent_config.get('version', '2.2.0'),
            "description": agent_config.get('description', 'Agent de développement de code'),
            "status": self._status.value,
            "capabilities": capabilities,
            "features": {
                "templates": list(self.code_templates.keys()),
                "sub_agents": list(self._sub_agents.keys()),
                "languages_supported": [lang.value for lang in CodeLanguage]
            },
            "stats": {
                "components_generated": len(self.generated_components)
            }
        }

    # -------------------------------------------------------------------------
    # GESTION DES MESSAGES
    # -------------------------------------------------------------------------

    async def _handle_custom_message(self, message: Message) -> Optional[Message]:
        """
        Gère les messages personnalisés pour le CoderAgent.

        Args:
            message: Message à traiter

        Returns:
            Réponse éventuelle
        """
        try:
            message_type = message.message_type

            handlers = {
                "generate_code": self._handle_generate_code,
                "validate_code": self._handle_validate_code,
                "split_spec": self._handle_split_spec,
            }

            if message_type in handlers:
                return await handlers[message_type](message)

            self._logger.warning(f"Type de message non reconnu: {message_type}")
            return None

        except Exception as e:
            self._logger.error(f"Erreur lors du traitement du message personnalisé: {e}")
            return Message(
                sender=self.name,
                recipient=message.sender,
                content={"error": str(e)},
                message_type="error",
                correlation_id=message.message_id
            )

    async def _handle_generate_code(self, message: Message) -> Message:
        plan = message.content.get("plan", {})
        result = await self.generate_code(plan)
        return Message(
            sender=self.name,
            recipient=message.sender,
            content={"result": result},
            message_type="generation_result",
            correlation_id=message.message_id
        )

    async def _handle_validate_code(self, message: Message) -> Message:
        code = message.content.get("code", "")
        result = await self.validate_code(code)
        return Message(
            sender=self.name,
            recipient=message.sender,
            content={"validation_result": result},
            message_type="validation_result",
            correlation_id=message.message_id
        )

    async def _handle_split_spec(self, message: Message) -> Message:
        global_spec = message.content.get("spec", {})
        strategy = message.content.get("strategy", "largeur_dabord")
        result = await self.split_spec_into_fragments(global_spec, strategy)
        return Message(
            sender=self.name,
            recipient=message.sender,
            content={"fragments": result},
            message_type="split_spec_result",
            correlation_id=message.message_id
        )

    # -------------------------------------------------------------------------
    # TEMPLATES DE CODE
    # -------------------------------------------------------------------------

    def _get_fastapi_template(self) -> str:
        """Retourne un template FastAPI de base"""
        return '''"""
{{ service_name }} - Service FastAPI
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

app = FastAPI(title="{{ service_name }}", version="1.0.0")

class Item(BaseModel):
    name: str
    description: Optional[str] = None

@app.get("/")
async def root():
    return {"message": "Hello from {{ service_name }}"}

@app.get("/items/{item_id}")
async def read_item(item_id: int):
    return {"item_id": item_id}

@app.post("/items/")
async def create_item(item: Item):
    return {"item": item}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
'''

    def _get_express_template(self) -> str:
        """Retourne un template Express.js de base"""
        return '''/**
 * {{ service_name }} - Service Express.js
 */

const express = require('express');
const app = express();
const PORT = process.env.PORT || 3000;

app.use(express.json());

app.get('/', (req, res) => {
    res.json({ message: 'Hello from {{ service_name }}' });
});

app.get('/items/:id', (req, res) => {
    res.json({ item_id: req.params.id });
});

app.post('/items', (req, res) => {
    res.json({ item: req.body });
});

app.listen(PORT, () => {
    console.log(`{{ service_name }} listening on port ${PORT}`);
});
'''

    def _get_solidity_template(self) -> str:
        """Retourne un template Solidity de base"""
        return '''// SPDX-License-Identifier: MIT
pragma solidity ^{{ solidity_version }};

/**
 * @title {{ contract_name }}
 * @dev {{ description }}
 */

contract {{ contract_name }} {
    address public owner;
    
    struct Item {
        string name;
        address owner;
        uint256 createdAt;
    }
    
    Item[] public items;
    
    event ItemCreated(uint256 indexed itemId, address indexed owner, string name);
    
    constructor() {
        owner = msg.sender;
    }
    
    function createItem(string memory name) external returns (uint256) {
        require(bytes(name).length > 0, "Name cannot be empty");
        
        uint256 newItemId = items.length;
        items.push(Item({
            name: name,
            owner: msg.sender,
            createdAt: block.timestamp
        }));
        
        emit ItemCreated(newItemId, msg.sender, name);
        return newItemId;
    }
    
    function getItem(uint256 itemId) external view returns (Item memory) {
        require(itemId < items.length, "Item does not exist");
        return items[itemId];
    }
    
    function getTotalItems() external view returns (uint256) {
        return items.length;
    }
}
'''

    def _get_react_template(self) -> str:
        """Retourne un template React de base"""
        return '''import React, { useState, useEffect } from 'react';

const {{ component_name }} = () => {
    const [message, setMessage] = useState('Hello from {{ component_name }}');
    
    useEffect(() => {
        // Initialization code here
        console.log('Component mounted');
    }, []);
    
    return (
        <div>
            <h1>{{ component_name }}</h1>
            <p>{message}</p>
            <p>{{ description }}</p>
        </div>
    );
};

export default {{ component_name }};
'''


# ============================================================================
# FONCTION FACTORY
# ============================================================================

def create_coder_agent(config_path: Optional[str] = None) -> CoderAgent:
    """
    Crée une instance de l'agent Coder.

    Args:
        config_path: Chemin vers le fichier de configuration

    Returns:
        Instance de CoderAgent
    """
    return CoderAgent(config_path)


# -----------------------------------------------------------------------------
# POINT D'ENTRÉE POUR LES TESTS
# -----------------------------------------------------------------------------

async def test_coder_agent():
    """Teste l'agent Coder"""
    print("🧪 Test de l'agent Coder...")

    agent = CoderAgent()

    print(f"  Création: {agent}")
    print(f"  Nom: {agent.name}")

    success = await agent.initialize()
    print(f"  Initialisation: {'✅' if success else '❌'}")

    if success:
        plan = {
            "architecture_id": "test_arch_1",
            "components": [
                {
                    "name": "user-service",
                    "type": "backend_service",
                    "language": "python",
                    "framework": "fastapi",
                    "description": "Service de gestion des utilisateurs",
                    "config": {"port": 8001}
                },
                {
                    "name": "UserContract",
                    "type": "smart_contract",
                    "language": "solidity",
                    "description": "Contrat intelligent pour les utilisateurs"
                }
            ]
        }

        result = await agent.generate_code(plan)

        if result["success"]:
            print(f"  Génération de code: ✅")
            print(f"  Composants générés: {result['successful_components']}/{result['total_components']}")
        else:
            print(f"  ❌ Échec de la génération: {result.get('error', 'Erreur inconnue')}")

    health = await agent.health_check()
    print(f"  Santé: {health['status']}")

    await agent.shutdown()
    print(f"  Statut final: {agent.status}")

    print("✅ Test CoderAgent terminé")


if __name__ == "__main__":
    asyncio.run(test_coder_agent())
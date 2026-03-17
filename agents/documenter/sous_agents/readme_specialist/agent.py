#!/usr/bin/env python3
"""
README Specialist SubAgent - Spécialiste README
Version: 2.0.0

Expert en création de fichiers README pour projets.
"""

import logging
import sys
import asyncio
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List

# Configuration des imports
current_dir = Path(__file__).parent.absolute()
project_root = current_dir.parent.parent.parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from agents.sous_agents.base_subagent import BaseSubAgent

logger = logging.getLogger(__name__)


class ReadmeSpecialistSubAgent(BaseSubAgent):
    """
    Sous-agent spécialisé en création de fichiers README.
    Gère la génération de README pour différents types de projets.
    """

    def __init__(self, config_path: Optional[str] = None):
        super().__init__(config_path)

        self._subagent_display_name = "📖 Spécialiste README"
        self._subagent_description = "Expert en création de fichiers README"
        self._subagent_version = "2.0.0"
        self._subagent_category = "documentation"
        self._subagent_capabilities = [
            "readme.generate",
            "readme.generate_standard",
            "readme.generate_python",
            "readme.generate_js",
            "readme.generate_solidity"
        ]

        self._readme_config = self._agent_config.get('readme_specialist', {})
        self._include_badges = self._readme_config.get('include_badges', True)
        self._include_toc = self._readme_config.get('include_toc', True)

        logger.info(f"✅ {self._subagent_display_name} initialisé (v{self._subagent_version})")

    async def _initialize_subagent_components(self) -> bool:
        """Initialise les composants spécifiques."""
        logger.info("Initialisation des composants README Specialist...")
        return True

    async def _initialize_components(self) -> bool:
        """Implémentation requise par BaseSubAgent."""
        return await self._initialize_subagent_components()

    async def generate_readme(self, project_info: Dict[str, Any]) -> Dict[str, Any]:
        """Génère un fichier README générique."""
        logger.info(f"📖 Génération README pour {project_info.get('name', 'project')}")

        readme = []
        
        # Titre
        readme.append(f"# {project_info.get('name', 'Project Name')}\n")

        # Badges
        if self._include_badges:
            readme.append(self._generate_badges(project_info))

        # Description
        readme.append(f"\n## Description\n{project_info.get('description', 'Project description.')}\n")

        # Table des matières
        if self._include_toc:
            readme.append(self._generate_toc())

        # Installation
        readme.append(f"\n## Installation\n```bash\n{project_info.get('installation', 'npm install')}\n```\n")

        # Usage
        readme.append(f"\n## Usage\n```\n{project_info.get('usage', '# Example usage')}\n```\n")

        # Features
        features = project_info.get('features', [])
        if features:
            readme.append("## Features\n")
            for feature in features:
                readme.append(f"- {feature}\n")
            readme.append("\n")

        # API Documentation
        if project_info.get('has_api', False):
            readme.append("## API Documentation\n")
            readme.append("See [API documentation](docs/api.md) for details.\n")

        # Contributing
        readme.append("\n## Contributing\n")
        readme.append("Please read [CONTRIBUTING.md](CONTRIBUTING.md) for details.\n")

        # License
        readme.append(f"\n## License\n{project_info.get('license', 'MIT')}\n")

        readme_id = f"readme_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        return {
            'success': True,
            'readme_id': readme_id,
            'content': ''.join(readme),
            'sections_count': 7
        }

    def _generate_badges(self, project_info: Dict[str, Any]) -> str:
        """Génère les badges pour le README."""
        badges = []
        
        version = project_info.get('version', '1.0.0')
        badges.append(f"![Version](https://img.shields.io/badge/version-{version}-blue.svg)")

        license = project_info.get('license', 'MIT')
        badges.append(f"![License](https://img.shields.io/badge/license-{license}-green.svg)")

        if 'tests' in project_info:
            badges.append("![Tests](https://img.shields.io/badge/tests-passing-brightgreen.svg)")

        if 'coverage' in project_info:
            coverage = project_info['coverage']
            badges.append(f"![Coverage](https://img.shields.io/badge/coverage-{coverage}%25-yellow.svg)")

        return " ".join(badges) + "\n"

    def _generate_toc(self) -> str:
        """Génère une table des matières."""
        return """## Table of Contents
- [Description](#description)
- [Installation](#installation)
- [Usage](#usage)
- [Features](#features)
- [API Documentation](#api-documentation)
- [Contributing](#contributing)
- [License](#license)

"""

    async def generate_python_readme(self, project_info: Dict[str, Any]) -> Dict[str, Any]:
        """Génère un README pour projet Python."""
        project_info.update({
            "installation": "pip install -r requirements.txt\npip install -e .",
            "usage": "python -m mypackage",
            "has_api": True
        })
        return await self.generate_readme(project_info)

    async def generate_js_readme(self, project_info: Dict[str, Any]) -> Dict[str, Any]:
        """Génère un README pour projet JavaScript."""
        project_info.update({
            "installation": "npm install",
            "usage": "npm start",
            "has_api": True
        })
        return await self.generate_readme(project_info)

    async def generate_solidity_readme(self, project_info: Dict[str, Any]) -> Dict[str, Any]:
        """Génère un README pour projet Solidity."""
        project_info.update({
            "installation": "npm install\nnpx hardhat compile",
            "usage": "npx hardhat test",
            "features": [
                "ERC20 Token",
                "OpenZeppelin based",
                "Hardhat testing suite"
            ] + project_info.get('features', []),
            "has_api": True
        })
        return await self.generate_readme(project_info)

    async def generate_standard_readme(self, project_type: str, project_info: Dict[str, Any]) -> Dict[str, Any]:
        """Génère un README standard selon le type de projet."""
        if project_type == "python":
            return await self.generate_python_readme(project_info)
        elif project_type == "javascript" or project_type == "node":
            return await self.generate_js_readme(project_info)
        elif project_type == "solidity":
            return await self.generate_solidity_readme(project_info)
        else:
            return await self.generate_readme(project_info)

    def _get_capability_handlers(self) -> Dict[str, Any]:
        return {
            "readme.generate": self._handle_generate,
            "readme.generate_standard": self._handle_generate_standard,
            "readme.generate_python": self._handle_generate_python,
            "readme.generate_js": self._handle_generate_js,
            "readme.generate_solidity": self._handle_generate_solidity,
        }

    async def _handle_generate(self, params: Dict[str, Any]) -> Dict[str, Any]:
        return await self.generate_readme(project_info=params.get('project_info', {}))

    async def _handle_generate_standard(self, params: Dict[str, Any]) -> Dict[str, Any]:
        return await self.generate_standard_readme(
            project_type=params.get('project_type', 'generic'),
            project_info=params.get('project_info', {})
        )

    async def _handle_generate_python(self, params: Dict[str, Any]) -> Dict[str, Any]:
        return await self.generate_python_readme(project_info=params.get('project_info', {}))

    async def _handle_generate_js(self, params: Dict[str, Any]) -> Dict[str, Any]:
        return await self.generate_js_readme(project_info=params.get('project_info', {}))

    async def _handle_generate_solidity(self, params: Dict[str, Any]) -> Dict[str, Any]:
        return await self.generate_solidity_readme(project_info=params.get('project_info', {}))


# ============================================================================
# FONCTIONS D'EXPORT
# ============================================================================

def get_agent_class():
    return ReadmeSpecialistSubAgent
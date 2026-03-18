#!/usr/bin/env python3
"""
ReadmeSpecialist SubAgent - Spécialiste README
Version: 2.2.0 (ALIGNÉ SUR COMMUNICATION)
"""

import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
import time
import json
import re

project_root = Path(__file__).parent.parent.parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from agents.sous_agents.base_subagent import BaseSubAgent
from agents.base_agent.base_agent import Message, MessageType


class ReadmeSpecialistSubAgent(BaseSubAgent):
    """
    Sous-agent spécialisé dans la génération de README
    Version 2.2 - Aligné sur l'architecture Communication
    """

    def __init__(self, config_path: Optional[str] = None):
        super().__init__(config_path)
        
        subagent_config = self._config.get('subagent', {})
        self._display_name = subagent_config.get('display_name', '📖 Spécialiste README')
        
        self._initialized = False
        self._readmes_generated = 0
        self._readmes_failed = 0
        
        self._templates = self._load_templates()
        self._badge_styles = self._load_badge_styles()
        
        self._stats = {
            "readmes_generated": 0,
            "readmes_failed": 0,
            "by_style": {},
            "badges_generated": 0,
            "processing_time_total": 0,
            "processing_time_avg": 0,
            "uptime_start": datetime.now().isoformat()
        }
        
        self._logger.info(f"{self._display_name} créé")

    def _load_templates(self) -> Dict[str, str]:
        """Charge les templates de README"""
        return {
            "standard": """# {project_name}

{description}

## 🚀 Installation

```bash
{installation}
```

## 📖 Usage

```javascript
{usage}
```

## 📚 API Reference

{api_reference}

## 🤝 Contributing

{contributing}

## 📄 License

{license}
""",
            "minimal": """# {project_name}

{description}

## Installation
```bash
{installation}
```

## Usage
```javascript
{usage}
```

## License
{license}
""",
            "detailed": """# {project_name}

{description}

## 📋 Table des Matières
- [Installation](#installation)
- [Usage](#usage)
- [API Reference](#api-reference)
- [Configuration](#configuration)
- [Tests](#tests)
- [Contributing](#contributing)
- [License](#license)

## 🚀 Installation

### Prérequis
{prerequisites}

### Étapes
```bash
{installation}
```

## 📖 Usage

### Exemple basique
```javascript
{example_basic}
```

### Exemple avancé
```javascript
{example_advanced}
```

## 📚 API Reference

{api_reference}

## ⚙️ Configuration

{configuration}

## 🧪 Tests

```bash
{test_command}
```

## 🤝 Contributing

{contributing}

## 📄 License

{license}
""",
            "professional": """# {project_name}

<p align="center">
  <img src="{logo_url}" alt="{project_name} logo" width="200"/>
</p>

<p align="center">
  <strong>{description}</strong>
</p>

<p align="center">
  {badges}
</p>

---

## 📦 Installation

```bash
{installation}
```

## 🎯 Features

{features}

## 🚀 Quick Start

```javascript
{quick_start}
```

## 📖 Documentation

### API Reference

{api_reference}

### Configuration

{configuration}

## 🧪 Testing

```bash
{test_command}
```

## 🤝 Contributing

{contributing}

## 📄 License

{license}
"""
        }

    def _load_badge_styles(self) -> Dict[str, str]:
        """Charge les styles de badges"""
        return {
            "flat": "https://img.shields.io/badge/{name}-{value}-{color}?style=flat",
            "flat-square": "https://img.shields.io/badge/{name}-{value}-{color}?style=flat-square",
            "plastic": "https://img.shields.io/badge/{name}-{value}-{color}?style=plastic",
            "for-the-badge": "https://img.shields.io/badge/{name}-{value}-{color}?style=for-the-badge",
            "social": "https://img.shields.io/badge/{name}-{value}-{color}?style=social"
        }

    async def _initialize_subagent_components(self) -> bool:
        try:
            self._components = {
                "version": "2.2.0",
                "templates": list(self._templates.keys()),
                "badge_styles": list(self._badge_styles.keys()),
                "sections": ["installation", "usage", "api", "contributing", "license"],
                "supports_badges": True,
                "supports_toc": True
            }
            return True
        except Exception as e:
            self._logger.error(f"Erreur composants: {e}")
            return False

    async def _initialize_components(self) -> bool:
        return await self._initialize_subagent_components()

    def _get_capability_handlers(self) -> Dict[str, str]:
        return {
            "generate_readme": "handle_generate_readme",
            "generate_badges": "handle_generate_badges",
            "generate_toc": "handle_generate_toc",
            "validate_readme": "handle_validate_readme",
            "get_templates": "handle_get_templates",
            "format_readme": "handle_format_readme"
        }

    def _get_features(self) -> Dict[str, Any]:
        return {
            "templates": list(self._templates.keys()),
            "badge_styles": list(self._badge_styles.keys()),
            "sections": ["installation", "usage", "api", "contributing", "license", "tests", "configuration"],
            "badges": ["license", "version", "build", "coverage", "downloads"],
            "languages": ["markdown"],
            "max_sections": 20
        }

    async def generate_readme(self, project_info: Dict[str, Any], template: str = "standard", style: str = "flat") -> Dict[str, Any]:
        """Génère un README à partir des informations du projet"""
        start_time = time.time()
        
        try:
            if template not in self._templates:
                template = "standard"
            
            template_str = self._templates[template]
            
            # Préparer les données avec valeurs par défaut
            data = {
                "project_name": project_info.get("name", "Project Name"),
                "description": project_info.get("description", "Description du projet"),
                "installation": project_info.get("installation", "npm install"),
                "usage": project_info.get("usage", "// Exemple d'utilisation"),
                "api_reference": project_info.get("api_reference", "Documentation API à venir"),
                "contributing": project_info.get("contributing", "Les contributions sont les bienvenues !"),
                "license": project_info.get("license", "MIT"),
                "prerequisites": project_info.get("prerequisites", "Node.js 14+"),
                "example_basic": project_info.get("example_basic", "const result = await api.call()"),
                "example_advanced": project_info.get("example_advanced", "// Exemple avancé"),
                "configuration": project_info.get("configuration", "Aucune configuration requise"),
                "test_command": project_info.get("test_command", "npm test"),
                "features": project_info.get("features", "- Feature 1\n- Feature 2\n- Feature 3"),
                "quick_start": project_info.get("quick_start", "// Code de démarrage rapide"),
                "logo_url": project_info.get("logo_url", ""),
                "badges": ""
            }
            
            # Générer les badges si demandé
            if project_info.get("include_badges", False):
                badges_result = await self.generate_badges(
                    project_info.get("badges", []),
                    style
                )
                if badges_result["success"]:
                    data["badges"] = badges_result["badges"]
                    self._stats["badges_generated"] += badges_result["count"]
            
            # Générer la table des matières si demandée
            if project_info.get("include_toc", False) and template == "detailed":
                sections = self._extract_sections(template_str)
                toc_result = await self.generate_toc(sections)
                # Insérer la table des matières après la description
                parts = template_str.split("\n\n")
                if len(parts) > 2:
                    template_str = parts[0] + "\n\n" + toc_result["toc"] + "\n\n" + "\n\n".join(parts[2:])
            
            # Appliquer le template
            readme = template_str.format(**data)
            
            processing_time = time.time() - start_time
            self._readmes_generated += 1
            self._stats["readmes_generated"] += 1
            self._stats["by_style"][template] = self._stats["by_style"].get(template, 0) + 1
            self._stats["processing_time_total"] += processing_time
            self._stats["processing_time_avg"] = self._stats["processing_time_total"] / self._stats["readmes_generated"]
            
            return {
                "success": True,
                "readme": readme,
                "template": template,
                "sections": len(data),
                "size": len(readme),
                "badges_included": bool(data["badges"]),
                "processing_time": processing_time
            }
            
        except Exception as e:
            self._readmes_failed += 1
            self._stats["readmes_failed"] += 1
            return {"success": False, "error": str(e)}

    def _extract_sections(self, template: str) -> List[str]:
        """Extrait les sections d'un template"""
        sections = []
        lines = template.split('\n')
        for line in lines:
            if line.startswith('## '):
                section = line.replace('##', '').strip()
                sections.append(section)
        return sections

    async def generate_badges(self, badges: List[Dict[str, str]], style: str = "flat") -> Dict[str, Any]:
        """Génère des badges pour le README"""
        try:
            if style not in self._badge_styles:
                style = "flat"
            
            badge_template = self._badge_styles[style]
            generated_badges = []
            
            for badge in badges:
                name = badge.get("name", "").replace(" ", "_")
                value = badge.get("value", "").replace(" ", "_")
                color = badge.get("color", "green")
                
                badge_url = badge_template.format(
                    name=name,
                    value=value,
                    color=color
                )
                
                generated_badges.append(f"![{name}]({badge_url})")
            
            return {
                "success": True,
                "badges": " ".join(generated_badges),
                "count": len(generated_badges),
                "style": style
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def generate_toc(self, sections: List[str]) -> Dict[str, Any]:
        """Génère une table des matières"""
        try:
            toc_lines = ["## Table des matières", ""]
            
            for section in sections:
                # Créer un anchor à partir du nom de la section
                anchor = section.lower().replace(' ', '-').replace('é', 'e').replace('è', 'e').replace('à', 'a')
                toc_lines.append(f"- [{section}](#{anchor})")
            
            return {
                "success": True,
                "toc": "\n".join(toc_lines),
                "sections": len(sections)
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def validate_readme(self, readme: str, rules: Dict = None) -> Dict[str, Any]:
        """Valide un README"""
        rules = rules or {}
        issues = []
        
        # Vérifications basiques
        if not readme.startswith('# '):
            issues.append("Le README doit commencer par un titre H1")
        
        if '# ' in readme and readme.count('# ') < 1:
            issues.append("Au moins un titre principal requis")
        
        if rules.get("min_length") and len(readme) < rules["min_length"]:
            issues.append(f"Longueur minimale: {len(readme)} < {rules['min_length']}")
        
        if rules.get("max_length") and len(readme) > rules["max_length"]:
            issues.append(f"Longueur maximale: {len(readme)} > {rules['max_length']}")
        
        if rules.get("required_sections"):
            for section in rules["required_sections"]:
                if f"## {section}" not in readme and f"# {section}" not in readme:
                    issues.append(f"Section requise manquante: {section}")
        
        # Vérifier les badges (optionnel)
        if rules.get("require_badges") and "![License]" not in readme:
            issues.append("Badges de licence recommandés")
        
        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "length": len(readme),
            "sections": readme.count('# ') + readme.count('## ')
        }

    async def format_readme(self, readme: str, style: str = "clean") -> Dict[str, Any]:
        """Formate un README existant"""
        try:
            lines = readme.split('\n')
            formatted_lines = []
            
            i = 0
            while i < len(lines):
                line = lines[i].rstrip()
                
                if style == "clean":
                    # Nettoyer les espaces multiples
                    line = ' '.join(line.split())
                
                elif style == "compact":
                    # Supprimer les lignes vides en trop
                    if line == '' and i > 0 and lines[i-1].strip() == '':
                        i += 1
                        continue
                
                elif style == "readable":
                    # Ajouter des sauts de ligne après les titres
                    formatted_lines.append(line)
                    if line.startswith('#') and i < len(lines)-1 and lines[i+1].strip() != '':
                        formatted_lines.append('')
                    i += 1
                    continue
                
                formatted_lines.append(line)
                i += 1
            
            return {
                "success": True,
                "readme": '\n'.join(formatted_lines),
                "original_lines": len(lines),
                "formatted_lines": len(formatted_lines)
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def handle_generate_readme(self, message: Message) -> Message:
        content = message.content
        result = await self.generate_readme(
            content.get("project_info", {}),
            content.get("template", "standard"),
            content.get("style", "flat")
        )
        return Message(
            sender=self.__class__.__name__,
            recipient=message.sender,
            content=result,
            message_type="readme_generated",
            correlation_id=message.message_id
        )

    async def handle_generate_badges(self, message: Message) -> Message:
        content = message.content
        result = await self.generate_badges(
            content.get("badges", []),
            content.get("style", "flat")
        )
        return Message(
            sender=self.__class__.__name__,
            recipient=message.sender,
            content=result,
            message_type="badges_generated",
            correlation_id=message.message_id
        )

    async def handle_generate_toc(self, message: Message) -> Message:
        result = await self.generate_toc(message.content.get("sections", []))
        return Message(
            sender=self.__class__.__name__,
            recipient=message.sender,
            content=result,
            message_type="toc_generated",
            correlation_id=message.message_id
        )

    async def handle_validate_readme(self, message: Message) -> Message:
        content = message.content
        result = await self.validate_readme(
            content.get("readme", ""),
            content.get("rules", {})
        )
        return Message(
            sender=self.__class__.__name__,
            recipient=message.sender,
            content=result,
            message_type="readme_validated",
            correlation_id=message.message_id
        )

    async def handle_get_templates(self, message: Message) -> Message:
        return Message(
            sender=self.__class__.__name__,
            recipient=message.sender,
            content={
                "templates": list(self._templates.keys()),
                "count": len(self._templates),
                "badge_styles": list(self._badge_styles.keys())
            },
            message_type="templates_list",
            correlation_id=message.message_id
        )

    async def handle_format_readme(self, message: Message) -> Message:
        content = message.content
        result = await self.format_readme(
            content.get("readme", ""),
            content.get("style", "clean")
        )
        return Message(
            sender=self.__class__.__name__,
            recipient=message.sender,
            content=result,
            message_type="readme_formatted",
            correlation_id=message.message_id
        )

    async def handle_message(self, message: Message) -> Optional[Message]:
        try:
            msg_type = message.message_type
            handlers = self._get_capability_handlers()
            
            if msg_type in handlers:
                handler = getattr(self, handlers[msg_type], None)
                if handler:
                    return await handler(message)
            
            return Message(
                sender=self.__class__.__name__,
                recipient=message.sender,
                content={"error": f"Type non supporté: {msg_type}"},
                message_type=MessageType.ERROR.value,
                correlation_id=message.message_id
            )
        except Exception as e:
            return Message(
                sender=self.__class__.__name__,
                recipient=message.sender,
                content={"error": str(e)},
                message_type=MessageType.ERROR.value,
                correlation_id=message.message_id
            )

    async def health_check(self) -> Dict[str, Any]:
        uptime = None
        if self._stats.get('uptime_start'):
            start = datetime.fromisoformat(self._stats['uptime_start'])
            uptime = str(datetime.now() - start)

        success_rate = 0
        total = self._stats["readmes_generated"] + self._stats["readmes_failed"]
        if total > 0:
            success_rate = (self._stats["readmes_generated"] / total) * 100

        return {
            "status": self._status,
            "ready": self._initialized,
            "display_name": self._display_name,
            "uptime": uptime,
            "stats": {
                "readmes_generated": self._stats["readmes_generated"],
                "readmes_failed": self._stats["readmes_failed"],
                "by_style": self._stats["by_style"],
                "badges_generated": self._stats["badges_generated"],
                "success_rate": round(success_rate, 2),
                "processing_time_avg": round(self._stats["processing_time_avg"], 3)
            },
            "components": self._components,
            "timestamp": datetime.now().isoformat()
        }

    def get_agent_info(self) -> Dict[str, Any]:
        return {
            "id": "ReadmeSpecialistSubAgent",
            "name": self._display_name,
            "version": "2.2.0",
            "status": self._status,
            "capabilities": list(self._get_capability_handlers().keys()),
            "features": self._get_features(),
            "stats": {
                "readmes_generated": self._stats["readmes_generated"],
                "templates_available": len(self._templates),
                "success_rate": round(
                    (self._stats["readmes_generated"] / max(1, self._stats["readmes_generated"] + self._stats["readmes_failed"])) * 100, 2
                )
            }
        }

    async def get_stats(self) -> Dict[str, Any]:
        return self._stats

    async def shutdown(self) -> bool:
        self._logger.info(f"Arrêt de {self._display_name}...")
        await self._save_stats()
        
        # Appeler super().shutdown() mais ignorer son retour
        try:
            await super().shutdown()
        except Exception:
            pass  # Ignorer toute erreur
        
        return True
    
    async def _save_stats(self):
        try:
            stats_file = Path("./reports") / "documenter" / "readme_specialist" / f"stats_{datetime.now().strftime('%Y%m%d')}.json"
            stats_file.parent.mkdir(parents=True, exist_ok=True)
            with open(stats_file, 'w', encoding='utf-8') as f:
                json.dump(self._stats, f, indent=2, default=str)
        except Exception as e:
            self._logger.warning(f"Impossible de sauvegarder: {e}")
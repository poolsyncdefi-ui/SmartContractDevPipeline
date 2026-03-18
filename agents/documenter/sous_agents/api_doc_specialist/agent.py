#!/usr/bin/env python3
"""
ApiDocSpecialist SubAgent - Spécialiste documentation API
Version: 2.2.0 (ALIGNÉ SUR COMMUNICATION)
"""

import sys
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
import time

project_root = Path(__file__).parent.parent.parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from agents.sous_agents.base_subagent import BaseSubAgent
from agents.base_agent.base_agent import Message, MessageType


class ApiDocSpecialistSubAgent(BaseSubAgent):
    """
    Sous-agent spécialisé dans la documentation d'API
    Version 2.2 - Aligné sur l'architecture Communication
    """

    def __init__(self, config_path: Optional[str] = None):
        super().__init__(config_path)
        
        subagent_config = self._config.get('subagent', {})
        self._display_name = subagent_config.get('display_name', '🔌 Spécialiste Documentation API')
        
        self._initialized = False
        self._docs_generated = 0
        self._docs_failed = 0
        
        self._stats = {
            "docs_generated": 0,
            "docs_failed": 0,
            "by_format": {},
            "processing_time_total": 0,
            "processing_time_avg": 0,
            "uptime_start": datetime.now().isoformat()
        }
        
        self._logger.info(f"{self._display_name} créé")

    async def _initialize_subagent_components(self) -> bool:
        try:
            self._components = {
                "version": "2.2.0",
                "formats": ["openapi", "swagger", "markdown", "html"],
                "supports_openapi": True,
                "supports_examples": True
            }
            return True
        except Exception as e:
            self._logger.error(f"Erreur composants: {e}")
            return False

    async def _initialize_components(self) -> bool:
        return await self._initialize_subagent_components()

    def _get_capability_handlers(self) -> Dict[str, str]:
        return {
            "generate_api_doc": "handle_generate_api_doc",
            "generate_openapi": "handle_generate_openapi",
            "generate_swagger": "handle_generate_swagger",
            "generate_endpoints": "handle_generate_endpoints",
            "validate_api_spec": "handle_validate_api_spec",
            "generate_examples": "handle_generate_examples"
        }

    def _get_features(self) -> Dict[str, Any]:
        return {
            "formats": ["openapi", "swagger", "markdown", "html"],
            "openapi_versions": ["2.0", "3.0.0", "3.1.0"],
            "supports_examples": True,
            "supports_authentication": True,
            "max_endpoints": 500
        }

    async def generate_api_doc(self, spec: Dict[str, Any], format: str = "openapi") -> Dict[str, Any]:
        """Génère une documentation API à partir d'une spécification"""
        start_time = time.time()
        
        try:
            if format == "openapi":
                result = self._generate_openapi(spec)
            elif format == "swagger":
                result = self._generate_swagger(spec)
            elif format == "markdown":
                result = self._generate_markdown(spec)
            elif format == "html":
                result = self._generate_html(spec)
            else:
                return {"success": False, "error": f"Format non supporté: {format}"}
            
            processing_time = time.time() - start_time
            self._docs_generated += 1
            self._stats["docs_generated"] += 1
            self._stats["by_format"][format] = self._stats["by_format"].get(format, 0) + 1
            self._stats["processing_time_total"] += processing_time
            self._stats["processing_time_avg"] = self._stats["processing_time_total"] / self._stats["docs_generated"]
            
            return {
                "success": True,
                "content": result,
                "format": format,
                "endpoints": len(spec.get("paths", {})),
                "processing_time": processing_time
            }
            
        except Exception as e:
            self._docs_failed += 1
            self._stats["docs_failed"] += 1
            return {"success": False, "error": str(e)}

    def _generate_openapi(self, spec: Dict) -> str:
        """Génère une spécification OpenAPI"""
        import yaml
        
        openapi_spec = {
            "openapi": "3.0.0",
            "info": {
                "title": spec.get("name", "API Documentation"),
                "version": spec.get("version", "1.0.0"),
                "description": spec.get("description", "")
            },
            "paths": spec.get("paths", {}),
            "components": spec.get("components", {})
        }
        
        return yaml.dump(openapi_spec, default_flow_style=False)

    def _generate_swagger(self, spec: Dict) -> str:
        """Génère une spécification Swagger 2.0"""
        import yaml
        
        swagger_spec = {
            "swagger": "2.0",
            "info": {
                "title": spec.get("name", "API Documentation"),
                "version": spec.get("version", "1.0.0"),
                "description": spec.get("description", "")
            },
            "paths": spec.get("paths", {}),
            "definitions": spec.get("definitions", {})
        }
        
        return yaml.dump(swagger_spec, default_flow_style=False)

    def _generate_markdown(self, spec: Dict) -> str:
        """Génère une documentation Markdown"""
        lines = []
        lines.append(f"# {spec.get('name', 'API Documentation')}")
        lines.append("")
        lines.append(spec.get('description', ''))
        lines.append("")
        
        # Endpoints
        lines.append("## Endpoints")
        lines.append("")
        
        for path, methods in spec.get("paths", {}).items():
            for method, details in methods.items():
                lines.append(f"### `{method.upper()} {path}`")
                lines.append("")
                lines.append(details.get("description", ""))
                lines.append("")
                
                if "parameters" in details:
                    lines.append("**Parameters:**")
                    for param in details["parameters"]:
                        lines.append(f"- `{param.get('name')}`: {param.get('type')} - {param.get('description', '')}")
                    lines.append("")
                
                if "responses" in details:
                    lines.append("**Responses:**")
                    for code, response in details["responses"].items():
                        lines.append(f"- `{code}`: {response.get('description', '')}")
                    lines.append("")
        
        return "\n".join(lines)

    def _generate_html(self, spec: Dict) -> str:
        """Génère une documentation HTML"""
        title = spec.get('name', 'API Documentation')
        description = spec.get('description', '')
        
        endpoints_html = ""
        for path, methods in spec.get("paths", {}).items():
            for method, details in methods.items():
                endpoints_html += f"""
                <div class="endpoint">
                    <h3><span class="method {method}">{method.upper()}</span> {path}</h3>
                    <p>{details.get('description', '')}</p>
                </div>
                """
        
        return f"""<!DOCTYPE html>
<html>
<head>
    <title>{title}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; }}
        .endpoint {{ margin: 20px 0; padding: 10px; border-left: 3px solid #00ff88; }}
        .method {{ padding: 3px 8px; border-radius: 3px; color: white; }}
        .get {{ background: #3b82f6; }}
        .post {{ background: #10b981; }}
        .put {{ background: #8b5cf6; }}
        .delete {{ background: #ef4444; }}
    </style>
</head>
<body>
    <h1>{title}</h1>
    <p>{description}</p>
    {endpoints_html}
</body>
</html>"""

    async def validate_api_spec(self, spec: Dict) -> Dict[str, Any]:
        """Valide une spécification API"""
        issues = []
        
        # Vérifications requises
        if not spec.get("name"):
            issues.append("Nom de l'API requis")
        
        if not spec.get("version"):
            issues.append("Version requise")
        
        if "paths" not in spec or not spec["paths"]:
            issues.append("Au moins un endpoint requis")
        else:
            for path, methods in spec["paths"].items():
                if not path.startswith("/"):
                    issues.append(f"Le chemin {path} doit commencer par /")
        
        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "endpoints_count": len(spec.get("paths", {}))
        }

    async def generate_endpoints(self, functions: List[Dict]) -> Dict[str, Any]:
        """Génère des endpoints API à partir de fonctions"""
        paths = {}
        
        for func in functions:
            name = func.get("name")
            if name:
                path = f"/{name}"
                paths[path] = {
                    "post": {
                        "description": func.get("description", ""),
                        "parameters": [
                            {
                                "name": p.get("name"),
                                "in": "body",
                                "type": p.get("type"),
                                "description": p.get("description", "")
                            }
                            for p in func.get("params", [])
                        ],
                        "responses": {
                            "200": {
                                "description": "Success",
                                "schema": {
                                    "type": func.get("returns", "object")
                                }
                            }
                        }
                    }
                }
        
        return {
            "success": True,
            "paths": paths,
            "count": len(paths)
        }

    async def generate_examples(self, spec: Dict) -> Dict[str, Any]:
        """Génère des exemples d'utilisation"""
        examples = []
        
        for path, methods in spec.get("paths", {}).items():
            for method, details in methods.items():
                example = {
                    "endpoint": f"{method.upper()} {path}",
                    "description": details.get("description", ""),
                    "example_request": self._generate_example_request(method, path, details),
                    "example_response": self._generate_example_response(details)
                }
                examples.append(example)
        
        return {
            "success": True,
            "examples": examples,
            "count": len(examples)
        }

    def _generate_example_request(self, method: str, path: str, details: Dict) -> Dict:
        """Génère un exemple de requête"""
        request = {
            "method": method.upper(),
            "url": f"https://api.example.com{path}",
            "headers": {
                "Content-Type": "application/json",
                "Authorization": "Bearer <token>"
            }
        }
        
        if details.get("parameters"):
            request["body"] = {
                p.get("name"): f"<{p.get('type')}>"
                for p in details["parameters"]
            }
        
        return request

    def _generate_example_response(self, details: Dict) -> Dict:
        """Génère un exemple de réponse"""
        response = {
            "status": 200,
            "headers": {
                "Content-Type": "application/json"
            }
        }
        
        # Exemple basique
        response["body"] = {
            "success": True,
            "data": {}
        }
        
        return response

    async def handle_generate_api_doc(self, message: Message) -> Message:
        content = message.content
        result = await self.generate_api_doc(
            content.get("spec", {}),
            content.get("format", "openapi")
        )
        return Message(
            sender=self.__class__.__name__,
            recipient=message.sender,
            content=result,
            message_type="api_doc_generated",
            correlation_id=message.message_id
        )

    async def handle_generate_openapi(self, message: Message) -> Message:
        result = await self.generate_api_doc(message.content, "openapi")
        return Message(
            sender=self.__class__.__name__,
            recipient=message.sender,
            content=result,
            message_type="openapi_generated",
            correlation_id=message.message_id
        )

    async def handle_generate_swagger(self, message: Message) -> Message:
        result = await self.generate_api_doc(message.content, "swagger")
        return Message(
            sender=self.__class__.__name__,
            recipient=message.sender,
            content=result,
            message_type="swagger_generated",
            correlation_id=message.message_id
        )

    async def handle_generate_endpoints(self, message: Message) -> Message:
        result = await self.generate_endpoints(message.content.get("functions", []))
        return Message(
            sender=self.__class__.__name__,
            recipient=message.sender,
            content=result,
            message_type="endpoints_generated",
            correlation_id=message.message_id
        )

    async def handle_validate_api_spec(self, message: Message) -> Message:
        result = await self.validate_api_spec(message.content.get("spec", {}))
        return Message(
            sender=self.__class__.__name__,
            recipient=message.sender,
            content=result,
            message_type="api_spec_validated",
            correlation_id=message.message_id
        )

    async def handle_generate_examples(self, message: Message) -> Message:
        result = await self.generate_examples(message.content.get("spec", {}))
        return Message(
            sender=self.__class__.__name__,
            recipient=message.sender,
            content=result,
            message_type="examples_generated",
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
        return {
            "status": self._status,
            "ready": self._initialized,
            "display_name": self._display_name,
            "stats": {
                "docs_generated": self._stats["docs_generated"],
                "docs_failed": self._stats["docs_failed"],
                "by_format": self._stats["by_format"]
            },
            "timestamp": datetime.now().isoformat()
        }

    def get_agent_info(self) -> Dict[str, Any]:
        return {
            "id": "ApiDocSpecialistSubAgent",
            "name": self._display_name,
            "version": "2.2.0",
            "status": self._status,
            "capabilities": list(self._get_capability_handlers().keys()),
            "features": self._get_features(),
            "stats": {
                "docs_generated": self._stats["docs_generated"],
                "success_rate": round(
                    (self._stats["docs_generated"] / max(1, self._stats["docs_generated"] + self._stats["docs_failed"])) * 100, 2
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
            stats_file = Path("./reports") / "documenter" / "api_doc_specialist" / f"stats_{datetime.now().strftime('%Y%m%d')}.json"
            stats_file.parent.mkdir(parents=True, exist_ok=True)
            with open(stats_file, 'w') as f:
                json.dump(self._stats, f, indent=2, default=str)
        except Exception as e:
            self._logger.warning(f"Impossible de sauvegarder: {e}")
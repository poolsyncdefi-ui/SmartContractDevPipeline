#!/usr/bin/env python3
"""
API Doc Specialist SubAgent - Spécialiste documentation API
Version: 2.0.0

Expert en génération de documentation d'API (OpenAPI/Swagger, RAML, etc.)
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


class ApiDocSpecialistSubAgent(BaseSubAgent):
    """
    Sous-agent spécialisé en documentation d'API.
    Gère la génération de documentation OpenAPI/Swagger, Postman collections, etc.
    """

    def __init__(self, config_path: Optional[str] = None):
        super().__init__(config_path)

        self._subagent_display_name = "🔌 Spécialiste Documentation API"
        self._subagent_description = "Expert en documentation d'API (OpenAPI/Swagger)"
        self._subagent_version = "2.0.0"
        self._subagent_category = "documentation"
        self._subagent_capabilities = [
            "api.generate_openapi",
            "api.generate_swagger",
            "api.generate_postman",
            "api.generate_endpoint_doc",
            "api.validate_spec"
        ]

        self._api_config = self._agent_config.get('api_doc_specialist', {})
        self._formats = self._api_config.get('formats', ['openapi', 'swagger'])

        logger.info(f"✅ {self._subagent_display_name} initialisé (v{self._subagent_version})")

    async def _initialize_subagent_components(self) -> bool:
        """Initialise les composants spécifiques."""
        logger.info("Initialisation des composants API Doc Specialist...")
        return True

    async def _initialize_components(self) -> bool:
        """Implémentation requise par BaseSubAgent."""
        return await self._initialize_subagent_components()

    async def generate_openapi_spec(self, api_info: Dict[str, Any]) -> Dict[str, Any]:
        """Génère une spécification OpenAPI."""
        logger.info(f"📝 Génération OpenAPI pour {api_info.get('title', 'API')}")

        spec = {
            "openapi": "3.0.0",
            "info": {
                "title": api_info.get('title', 'API Documentation'),
                "description": api_info.get('description', ''),
                "version": api_info.get('version', '1.0.0'),
                "contact": api_info.get('contact', {})
            },
            "servers": api_info.get('servers', [{"url": "http://localhost:8000"}]),
            "paths": self._build_paths(api_info.get('endpoints', [])),
            "components": {
                "schemas": api_info.get('schemas', {}),
                "securitySchemes": api_info.get('securitySchemes', {})
            }
        }

        spec_id = f"openapi_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        return {
            'success': True,
            'spec_id': spec_id,
            'spec': spec,
            'endpoints_count': len(spec['paths'])
        }

    def _build_paths(self, endpoints: List[Dict]) -> Dict:
        """Construit les chemins OpenAPI à partir des endpoints."""
        paths = {}
        for endpoint in endpoints:
            path = endpoint.get('path', '/')
            method = endpoint.get('method', 'get').lower()
            
            if path not in paths:
                paths[path] = {}
            
            paths[path][method] = {
                "summary": endpoint.get('summary', ''),
                "description": endpoint.get('description', ''),
                "parameters": endpoint.get('parameters', []),
                "requestBody": endpoint.get('requestBody'),
                "responses": endpoint.get('responses', {
                    "200": {"description": "Successful response"}
                }),
                "tags": endpoint.get('tags', [])
            }
        return paths

    async def generate_swagger_ui(self, openapi_spec: Dict[str, Any]) -> Dict[str, Any]:
        """Génère une interface Swagger UI à partir d'une spécification."""
        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>{openapi_spec.get('info', {}).get('title', 'API Documentation')}</title>
    <link rel="stylesheet" type="text/css" href="https://unpkg.com/swagger-ui-dist@3/swagger-ui.css">
</head>
<body>
    <div id="swagger-ui"></div>
    <script src="https://unpkg.com/swagger-ui-dist@3/swagger-ui-bundle.js"></script>
    <script>
        SwaggerUIBundle({{
            spec: {json.dumps(openapi_spec, indent=2)},
            dom_id: '#swagger-ui',
            presets: [
                SwaggerUIBundle.presets.apis,
                SwaggerUIBundle.presets.standalone
            ]
        }});
    </script>
</body>
</html>"""

        return {
            'success': True,
            'html': html
        }

    async def generate_postman_collection(self, api_info: Dict[str, Any]) -> Dict[str, Any]:
        """Génère une collection Postman."""
        collection = {
            "info": {
                "name": api_info.get('title', 'API Collection'),
                "description": api_info.get('description', ''),
                "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
            },
            "item": []
        }

        for endpoint in api_info.get('endpoints', []):
            item = {
                "name": endpoint.get('name', 'Endpoint'),
                "request": {
                    "method": endpoint.get('method', 'GET'),
                    "url": {
                        "raw": endpoint.get('url', 'http://localhost:8000'),
                        "host": ["localhost"],
                        "path": endpoint.get('path', '').split('/')[1:]
                    },
                    "description": endpoint.get('description', '')
                }
            }
            collection["item"].append(item)

        return {
            'success': True,
            'collection': collection
        }

    async def generate_endpoint_documentation(self, endpoint: Dict[str, Any]) -> Dict[str, Any]:
        """Génère la documentation pour un endpoint spécifique."""
        doc = {
            "endpoint": f"{endpoint.get('method', 'GET')} {endpoint.get('path', '/')}",
            "summary": endpoint.get('summary', ''),
            "description": endpoint.get('description', ''),
            "parameters": [],
            "responses": []
        }

        for param in endpoint.get('parameters', []):
            doc["parameters"].append({
                "name": param.get('name', ''),
                "in": param.get('in', 'query'),
                "required": param.get('required', False),
                "type": param.get('schema', {}).get('type', 'string')
            })

        for status, response in endpoint.get('responses', {}).items():
            doc["responses"].append({
                "status": status,
                "description": response.get('description', '')
            })

        return {
            'success': True,
            'documentation': doc
        }

    async def validate_spec(self, spec: Dict[str, Any]) -> Dict[str, Any]:
        """Valide une spécification OpenAPI."""
        errors = []
        warnings = []

        # Vérifier les champs requis
        if 'openapi' not in spec:
            errors.append("Missing 'openapi' version")
        if 'info' not in spec:
            errors.append("Missing 'info' section")
        if 'paths' not in spec:
            errors.append("Missing 'paths' section")

        # Vérifier la structure
        if 'info' in spec:
            if 'title' not in spec['info']:
                warnings.append("Missing 'title' in info")
            if 'version' not in spec['info']:
                warnings.append("Missing 'version' in info")

        return {
            'success': len(errors) == 0,
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        }

    def _get_capability_handlers(self) -> Dict[str, Any]:
        return {
            "api.generate_openapi": self._handle_generate_openapi,
            "api.generate_swagger": self._handle_generate_swagger,
            "api.generate_postman": self._handle_generate_postman,
            "api.generate_endpoint_doc": self._handle_generate_endpoint_doc,
            "api.validate_spec": self._handle_validate_spec,
        }

    async def _handle_generate_openapi(self, params: Dict[str, Any]) -> Dict[str, Any]:
        return await self.generate_openapi_spec(api_info=params.get('api_info', {}))

    async def _handle_generate_swagger(self, params: Dict[str, Any]) -> Dict[str, Any]:
        spec = params.get('spec')
        if not spec:
            # Générer d'abord la spec
            spec_result = await self.generate_openapi_spec(params.get('api_info', {}))
            spec = spec_result.get('spec')
        return await self.generate_swagger_ui(spec)

    async def _handle_generate_postman(self, params: Dict[str, Any]) -> Dict[str, Any]:
        return await self.generate_postman_collection(api_info=params.get('api_info', {}))

    async def _handle_generate_endpoint_doc(self, params: Dict[str, Any]) -> Dict[str, Any]:
        return await self.generate_endpoint_documentation(endpoint=params.get('endpoint', {}))

    async def _handle_validate_spec(self, params: Dict[str, Any]) -> Dict[str, Any]:
        return await self.validate_spec(spec=params.get('spec', {}))


# ============================================================================
# FONCTIONS D'EXPORT
# ============================================================================

def get_agent_class():
    return ApiDocSpecialistSubAgent
# agents/coder/agent.py - VERSION COMPLÈTE
import os
import yaml
import json
import shutil
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
from agents.base_agent import BaseAgent

class CoderAgent(BaseAgent):
    def __init__(self, config_path: str = None):
        if config_path is None:
            config_path = os.path.join(os.path.dirname(__file__), "config.yaml")
        super().__init__(config_path)
        
        # Charger les capacités depuis le YAML
        self._load_capabilities_from_config()
    
    def _load_capabilities_from_config(self):
        """Charger les capacités depuis la configuration YAML."""
        if hasattr(self, 'config') and self.config:
            agent_config = self.config.get('agent', {})
            capabilities = agent_config.get('capabilities', [])
            
            # Extraire les noms des capacités
            self.capabilities = [cap.get('name') for cap in capabilities if cap.get('name')]
        else:
            # Fallback aux capacités par défaut
            self.capabilities = [
                "validate_config",
                "analyze_architecture",
                "generate_backend_code",
                "generate_frontend_code",
                "generate_devops_config",
                "implement_api_endpoints",
                "integrate_database",
                "setup_web3_integration",
                "implement_state_management",
                "create_ui_components",
                "optimize_performance",
                "write_unit_tests",
                "document_code",
                "enforce_coding_standards",
                "refactor_code",
                "review_prerequisites"
            ]
        
        # État de l'agent
        self.current_project = None
        self.code_metrics = {
            "files_created": 0,
            "lines_of_code": 0,
            "tests_written": 0,
            "complexity_score": 0.0
        }
        
    def _load_templates(self) -> Dict[str, Any]:
        """Charger les templates de code depuis le répertoire templates/."""
        templates = {}
        templates_dir = Path(__file__).parent / "templates"
        
        if templates_dir.exists():
            for template_file in templates_dir.glob("**/*"):
                if template_file.is_file():
                    rel_path = template_file.relative_to(templates_dir)
                    with open(template_file, 'r', encoding='utf-8') as f:
                        templates[str(rel_path)] = f.read()
        
        # Templates par défaut
        default_templates = {
            "python/api/main.py": '''from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional
import logging

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="{api_name}", version="1.0.0")

# Middleware CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """Endpoint racine."""
    return {{"message": "{api_name} API", "version": "1.0.0"}}

@app.get("/health")
async def health_check():
    """Endpoint de santé."""
    return {{"status": "healthy", "timestamp": "2024-01-01T00:00:00Z"}}

# Add more endpoints based on requirements
''',
            "react/component/Component.jsx": '''import React, {{ useState, useEffect }} from 'react';
import PropTypes from 'prop-types';
import './{component_name}.css';

/**
 * {component_name} - {description}
 */
const {component_name} = ({{
  initialValue = {default_value},
  onChange = () => {{}},
  className = '',
  disabled = false,
  ...props
}}) => {{
  const [value, setValue] = useState(initialValue);
  
  useEffect(() => {{
    setValue(initialValue);
  }}, [initialValue]);
  
  const handleChange = (newValue) => {{
    if (!disabled) {{
      setValue(newValue);
      onChange(newValue);
    }}
  }};
  
  return (
    <div className={`{component_name.lower()}-container ${{className}}`}}>
      <div className="{component_name.lower()}-content">
        {/* Implementation here */}
      </div>
    </div>
  );
}};

{component_name}.propTypes = {{
  initialValue: PropTypes.{prop_type},
  onChange: PropTypes.func,
  className: PropTypes.string,
  disabled: PropTypes.bool,
}};

{component_name}.defaultProps = {{
  initialValue: {default_value},
  onChange: () => {{}},
  className: '',
  disabled: false,
}};

export default {component_name};
''',
            "docker/Dockerfile.python": '''# Dockerfile for Python application
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \\
  CMD curl -f http://localhost:8000/health || exit 1

# Command to run
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
'''
        }
        
        templates.update(default_templates)
        return templates
    
    def analyze_architecture(self, architecture_spec: Dict[str, Any]) -> Dict[str, Any]:
        """Analyser l'architecture pour identifier les composants à développer."""
        self.logger.info(f"Analyzing architecture: {architecture_spec.get('name', 'Unnamed')}")
        
        analysis = {
            "project_name": architecture_spec.get("name", "Unknown"),
            "backend_components": [],
            "frontend_components": [],
            "devops_components": [],
            "database_components": [],
            "api_endpoints": [],
            "dependencies": {
                "python": [],
                "javascript": [],
                "system": []
            },
            "technical_requirements": [],
            "estimated_effort": {
                "backend": 0,
                "frontend": 0,
                "devops": 0,
                "total": 0
            }
        }
        
        # Analyse des composants
        components = architecture_spec.get("components", [])
        for component in components:
            comp_type = component.get("type", "").lower()
            comp_name = component.get("name", "")
            comp_desc = component.get("description", "")
            
            comp_analysis = {
                "name": comp_name,
                "type": comp_type,
                "description": comp_desc,
                "complexity": component.get("complexity", "medium"),
                "priority": component.get("priority", "medium"),
                "estimated_hours": self._estimate_effort(component),
                "dependencies": component.get("dependencies", []),
                "technologies": component.get("technologies", [])
            }
            
            if comp_type in ["api", "service", "microservice", "backend"]:
                analysis["backend_components"].append(comp_analysis)
                analysis["estimated_effort"]["backend"] += comp_analysis["estimated_hours"]
                
                # Extraire les endpoints
                for endpoint in component.get("endpoints", []):
                    analysis["api_endpoints"].append({
                        "component": comp_name,
                        "method": endpoint.get("method", "GET"),
                        "path": endpoint.get("path", "/"),
                        "description": endpoint.get("description", "")
                    })
                    
            elif comp_type in ["frontend", "ui", "dashboard", "webapp"]:
                analysis["frontend_components"].append(comp_analysis)
                analysis["estimated_effort"]["frontend"] += comp_analysis["estimated_hours"]
                
            elif comp_type in ["database", "cache", "storage"]:
                analysis["database_components"].append(comp_analysis)
                
            elif comp_type in ["infrastructure", "deployment", "ci_cd", "monitoring"]:
                analysis["devops_components"].append(comp_analysis)
                analysis["estimated_effort"]["devops"] += comp_analysis["estimated_hours"]
        
        # Calculer l'effort total
        analysis["estimated_effort"]["total"] = (
            analysis["estimated_effort"]["backend"] +
            analysis["estimated_effort"]["frontend"] +
            analysis["estimated_effort"]["devops"]
        )
        
        # Identifier les dépendances
        analysis["dependencies"]["python"] = self._extract_python_deps(architecture_spec)
        analysis["dependencies"]["javascript"] = self._extract_javascript_deps(architecture_spec)
        
        self.logger.info(f"Analysis complete: {len(components)} components analyzed")
        return analysis
    
    def generate_backend_code(self, component_spec: Dict[str, Any]) -> Dict[str, str]:
        """Générer le code backend pour un composant spécifique."""
        self.logger.info(f"Generating backend code for: {component_spec.get('name', 'Unknown')}")
        
        code_files = {}
        component_name = component_spec.get("name", "unknown").replace(" ", "_").lower()
        component_type = component_spec.get("type", "api").lower()
        
        # Créer la structure de répertoire
        base_dir = self.project_root / "backend" / component_name
        base_dir.mkdir(parents=True, exist_ok=True)
        
        if component_type == "api":
            # Générer l'API FastAPI complète
            api_structure = {
                "main.py": self._generate_api_main(component_spec),
                "requirements.txt": self._generate_requirements(component_spec),
                "Dockerfile": self._generate_dockerfile("python", component_spec),
                "docker-compose.yml": self._generate_docker_compose(component_spec),
                "app/__init__.py": "",
                "app/api/__init__.py": "",
                "app/api/v1/__init__.py": "",
                "app/api/v1/endpoints/__init__.py": "",
                "app/core/__init__.py": "",
                "app/core/config.py": self._generate_config(component_spec),
                "app/core/security.py": self._generate_security_config(),
                "app/models/__init__.py": "",
                "app/models/base.py": self._generate_base_model(),
                "app/schemas/__init__.py": "",
                "app/db/__init__.py": "",
                "app/db/session.py": self._generate_db_session(),
                "tests/__init__.py": "",
                "tests/test_api.py": self._generate_api_tests(component_spec)
            }
            
            for file_path, content in api_structure.items():
                full_path = base_dir / file_path
                full_path.parent.mkdir(parents=True, exist_ok=True)
                if content:
                    full_path.write_text(content, encoding='utf-8')
                    code_files[str(full_path.relative_to(self.project_root))] = content
        
        elif component_type == "database":
            # Générer les modèles de base de données
            db_files = self._generate_database_code(component_spec)
            for file_path, content in db_files.items():
                full_path = base_dir / file_path
                full_path.parent.mkdir(parents=True, exist_ok=True)
                full_path.write_text(content, encoding='utf-8')
                code_files[str(full_path.relative_to(self.project_root))] = content
        
        elif component_type == "service":
            # Générer un service microservice
            service_files = self._generate_service_code(component_spec)
            for file_path, content in service_files.items():
                full_path = base_dir / file_path
                full_path.parent.mkdir(parents=True, exist_ok=True)
                full_path.write_text(content, encoding='utf-8')
                code_files[str(full_path.relative_to(self.project_root))] = content
        
        self.code_metrics["files_created"] += len(code_files)
        self.logger.info(f"Generated {len(code_files)} backend files")
        
        return code_files
    
    def generate_frontend_code(self, component_spec: Dict[str, Any]) -> Dict[str, str]:
        """Générer le code frontend pour un composant spécifique."""
        self.logger.info(f"Generating frontend code for: {component_spec.get('name', 'Unknown')}")
        
        code_files = {}
        component_name = component_spec.get("name", "unknown").replace(" ", "_").lower()
        component_type = component_spec.get("type", "dashboard").lower()
        
        # Créer la structure de répertoire
        base_dir = self.project_root / "frontend" / component_name
        base_dir.mkdir(parents=True, exist_ok=True)
        
        if component_type == "dashboard":
            # Générer un dashboard React/Next.js complet
            frontend_structure = {
                "package.json": self._generate_package_json(component_spec),
                "next.config.js": self._generate_next_config(component_spec),
                "tailwind.config.js": self._generate_tailwind_config(),
                "postcss.config.js": self._generate_postcss_config(),
                "tsconfig.json": self._generate_tsconfig(),
                "app/globals.css": self._generate_global_css(),
                "app/layout.tsx": self._generate_layout_component(component_spec),
                "app/page.tsx": self._generate_main_page(component_spec),
                "components/ui/button.tsx": self._generate_button_component(),
                "components/ui/card.tsx": self._generate_card_component(),
                "components/dashboard/Header.tsx": self._generate_dashboard_header(component_spec),
                "components/dashboard/Sidebar.tsx": self._generate_dashboard_sidebar(component_spec),
                "components/dashboard/MetricsCard.tsx": self._generate_metrics_card(component_spec),
                "lib/utils.ts": self._generate_utils(),
                "hooks/useWeb3.ts": self._generate_web3_hook(),
                "contexts/Web3Context.tsx": self._generate_web3_context(),
                "public/favicon.ico": "",
                "README.md": self._generate_frontend_readme(component_spec)
            }
            
            for file_path, content in frontend_structure.items():
                full_path = base_dir / file_path
                full_path.parent.mkdir(parents=True, exist_ok=True)
                if content:
                    full_path.write_text(content, encoding='utf-8')
                    code_files[str(full_path.relative_to(self.project_root))] = content
        
        self.code_metrics["files_created"] += len(code_files)
        self.logger.info(f"Generated {len(code_files)} frontend files")
        
        return code_files
    
    def generate_devops_config(self, infra_spec: Dict[str, Any]) -> Dict[str, str]:
        """Générer les configurations DevOps."""
        self.logger.info(f"Generating DevOps config for infrastructure")
        
        config_files = {}
        infra_name = infra_spec.get("name", "infrastructure").replace(" ", "_").lower()
        
        # Créer la structure de répertoire
        base_dir = self.project_root / "devops" / infra_name
        base_dir.mkdir(parents=True, exist_ok=True)
        
        # Générer les configurations Docker
        docker_configs = {
            "docker-compose.prod.yml": self._generate_docker_compose_prod(infra_spec),
            "docker-compose.dev.yml": self._generate_docker_compose_dev(infra_spec),
            "nginx/nginx.conf": self._generate_nginx_config(infra_spec),
            "prometheus/prometheus.yml": self._generate_prometheus_config(),
            "grafana/dashboards/dashboard.json": self._generate_grafana_dashboard(),
            "scripts/deploy.sh": self._generate_deploy_script(infra_spec),
            "scripts/backup.sh": self._generate_backup_script(),
        }
        
        # Générer les configurations CI/CD
        cicd_configs = {
            ".github/workflows/ci.yml": self._generate_ci_pipeline(infra_spec),
            ".github/workflows/cd.yml": self._generate_cd_pipeline(infra_spec),
            ".github/workflows/deploy.yml": self._generate_deploy_pipeline(infra_spec),
        }
        
        # Générer les configurations Kubernetes
        k8s_configs = {
            "kubernetes/namespace.yaml": self._generate_k8s_namespace(infra_spec),
            "kubernetes/deployment.yaml": self._generate_k8s_deployment(infra_spec),
            "kubernetes/service.yaml": self._generate_k8s_service(infra_spec),
            "kubernetes/ingress.yaml": self._generate_k8s_ingress(infra_spec),
            "kubernetes/configmap.yaml": self._generate_k8s_configmap(infra_spec),
            "kubernetes/secrets.yaml": self._generate_k8s_secrets_template(),
            "kubernetes/hpa.yaml": self._generate_k8s_hpa(infra_spec),
        }
        
        # Combiner tous les fichiers
        all_configs = {**docker_configs, **cicd_configs, **k8s_configs}
        
        for file_path, content in all_configs.items():
            full_path = base_dir / file_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            if content:
                full_path.write_text(content, encoding='utf-8')
                config_files[str(full_path.relative_to(self.project_root))] = content
        
        self.code_metrics["files_created"] += len(config_files)
        self.logger.info(f"Generated {len(config_files)} DevOps config files")
        
        return config_files
    
    def implement_api_endpoints(self, endpoint_specs: List[Dict[str, Any]]) -> Dict[str, str]:
        """Implémenter les endpoints API REST/GraphQL."""
        self.logger.info(f"Implementing {len(endpoint_specs)} API endpoints")
        
        endpoint_files = {}
        
        for endpoint in endpoint_specs:
            component_name = endpoint.get("component", "api")
            endpoint_path = endpoint.get("path", "/")
            method = endpoint.get("method", "GET").upper()
            
            # Générer le fichier d'endpoint
            endpoint_code = self._generate_endpoint_code(endpoint)
            
            # Déterminer le chemin du fichier
            safe_component = component_name.replace(" ", "_").lower()
            safe_endpoint = endpoint_path.replace("/", "_").strip("_")
            file_name = f"app/api/v1/endpoints/{safe_endpoint}.py"
            
            full_path = self.project_root / "backend" / safe_component / file_name
            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.write_text(endpoint_code, encoding='utf-8')
            
            endpoint_files[str(full_path.relative_to(self.project_root))] = endpoint_code
        
        return endpoint_files
    
    def integrate_database(self, db_spec: Dict[str, Any]) -> Dict[str, str]:
        """Intégrer les modèles de base de données et ORM."""
        self.logger.info(f"Integrating database: {db_spec.get('type', 'Unknown')}")
        
        db_files = {}
        db_type = db_spec.get("type", "postgresql").lower()
        db_name = db_spec.get("name", "database").replace(" ", "_").lower()
        
        # Générer les modèles basés sur le schéma
        schema = db_spec.get("schema", {})
        models = schema.get("tables", [])
        
        # Fichier de configuration de la base de données
        db_config = self._generate_database_config(db_spec)
        config_path = self.project_root / "backend" / "shared" / "db" / "config.py"
        config_path.parent.mkdir(parents=True, exist_ok=True)
        config_path.write_text(db_config, encoding='utf-8')
        db_files[str(config_path.relative_to(self.project_root))] = db_config
        
        # Générer les modèles pour chaque table
        for table in models:
            model_code = self._generate_model_code(table, db_type)
            model_name = table.get("name", "Unknown").replace(" ", "_").lower()
            model_path = self.project_root / "backend" / "shared" / "models" / f"{model_name}.py"
            model_path.parent.mkdir(parents=True, exist_ok=True)
            model_path.write_text(model_code, encoding='utf-8')
            db_files[str(model_path.relative_to(self.project_root))] = model_code
        
        # Générer les migrations
        migration_code = self._generate_migration_script(models, db_type)
        migration_path = self.project_root / "backend" / "shared" / "db" / "migrations.py"
        migration_path.write_text(migration_code, encoding='utf-8')
        db_files[str(migration_path.relative_to(self.project_root))] = migration_code
        
        return db_files
    
    # Méthodes d'aide privées
    def _estimate_effort(self, component: Dict[str, Any]) -> int:
        """Estimer l'effort en heures pour un composant."""
        complexity = component.get("complexity", "medium")
        base_hours = {
            "low": 4,
            "medium": 8,
            "high": 16,
            "very_high": 32
        }
        return base_hours.get(complexity, 8)
    
    def _extract_python_deps(self, spec: Dict[str, Any]) -> List[str]:
        """Extraire les dépendances Python."""
        deps = [
            "fastapi==0.104.1",
            "uvicorn[standard]==0.24.0",
            "sqlalchemy==2.0.23",
            "alembic==1.12.1",
            "pydantic==2.5.0",
            "python-jose[cryptography]==3.3.0",
            "passlib[bcrypt]==1.7.4",
            "python-multipart==0.0.6",
            "httpx==0.25.1",
            "redis==5.0.1",
            "celery==5.3.4",
            "pytest==7.4.3",
            "pytest-asyncio==0.21.1"
        ]
        return deps
    
    def _extract_javascript_deps(self, spec: Dict[str, Any]) -> List[str]:
        """Extraire les dépendances JavaScript."""
        deps = {
            "dependencies": [
                "next@14.0.4",
                "react@18.2.0",
                "react-dom@18.2.0",
                "tailwindcss@3.3.5",
                "ethers@6.9.0",
                "wagmi@1.4.7",
                "viem@1.19.7",
                "@tanstack/react-query@5.12.0",
                "zustand@4.4.7",
                "axios@1.6.2"
            ],
            "devDependencies": [
                "@types/node@20.10.0",
                "@types/react@18.2.45",
                "@types/react-dom@18.2.18",
                "typescript@5.3.3",
                "eslint@8.55.0",
                "prettier@3.1.0"
            ]
        }
        return deps
    
    def _generate_api_main(self, spec: Dict[str, Any]) -> str:
        """Générer le fichier main.py pour une API."""
        api_name = spec.get("name", "API Service")
        api_version = spec.get("version", "1.0.0")
        
        return f'''from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
from app.api.v1.api import api_router
from app.core.config import settings

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gestion du cycle de vie de l'application."""
    # Démarrage
    logger.info("Starting {api_name}...")
    yield
    # Arrêt
    logger.info("Shutting down {api_name}...")

app = FastAPI(
    title="{api_name}",
    description="API service for {api_name}",
    version="{api_version}",
    lifespan=lifespan
)

# Middleware CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inclure les routes
app.include_router(api_router, prefix="/api/v1")

@app.get("/")
async def root():
    """Endpoint racine."""
    return {{"message": "{api_name}", "version": "{api_version}"}}

@app.get("/health")
async def health_check():
    """Endpoint de santé."""
    return {{"status": "healthy", "service": "{api_name}"}}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )
'''
    
    def _generate_requirements(self, spec: Dict[str, Any]) -> str:
        """Générer le fichier requirements.txt."""
        deps = self._extract_python_deps(spec)
        return "\n".join(deps)
    
    def _generate_dockerfile(self, language: str, spec: Dict[str, Any]) -> str:
        """Générer un Dockerfile."""
        if language == "python":
            return '''# Dockerfile for Python API
FROM python:3.11-slim as builder

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Runtime stage
FROM python:3.11-slim

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy virtual environment
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy application code
COPY . .

# Create non-root user
RUN groupadd -r appgroup && useradd -r -g appgroup -u 1000 appuser
RUN chown -R appuser:appgroup /app
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \\
  CMD curl -f http://localhost:8000/health || exit 1

# Command to run
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
'''
        return "# Dockerfile placeholder"
    
    # ... (autres méthodes de génération)
    
    def execute_capability(self, capability_name: str, **kwargs) -> Any:
        """Exécuter une capacité spécifique de l'agent."""
        if capability_name == "analyze_architecture":
            return self.analyze_architecture(kwargs.get("architecture_spec", {}))
        elif capability_name == "generate_backend_code":
            return self.generate_backend_code(kwargs.get("component_spec", {}))
        elif capability_name == "generate_frontend_code":
            return self.generate_frontend_code(kwargs.get("component_spec", {}))
        elif capability_name == "generate_devops_config":
            return self.generate_devops_config(kwargs.get("infra_spec", {}))
        elif capability_name == "implement_api_endpoints":
            return self.implement_api_endpoints(kwargs.get("endpoint_specs", []))
        elif capability_name == "integrate_database":
            return self.integrate_database(kwargs.get("db_spec", {}))
        else:
            return super().execute_capability(capability_name, **kwargs)
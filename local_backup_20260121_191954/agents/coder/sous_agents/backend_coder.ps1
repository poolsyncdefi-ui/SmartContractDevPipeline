# agents/coder/sous_agents/backend_coder.ps1
Write-Host "Création du Sous-Agent Code Backend..." -ForegroundColor Cyan

$backendAgentConfig = @'
# agents/coder/sous_agents/backend_config.yaml
sous_agent_id: "backend_coder_001"
parent_agent: "coder"
specialization: "Développement Backend & API"
model: "ollama:deepseek-coder:6.7b"
temperature: 0.2

capabilities:
  languages:
    - "Python (FastAPI, Django)"
    - "Node.js (Express, NestJS)"
    - "Go (Gin, Echo)"
    - "Java (Spring Boot)"
    - "Rust (Actix, Rocket)"
  database_orm:
    - "SQLAlchemy (Python)"
    - "Prisma (Node.js)"
    - "GORM (Go)"
    - "Hibernate (Java)"
    - "Diesel (Rust)"
  api_standards:
    - "RESTful API Design"
    - "GraphQL"
    - "gRPC"
    - "OpenAPI Specification"
  caching_strategies:
    - "Redis"
    - "Memcached"
    - "In-memory caching"
    - "CDN caching"

tools:
  - name: "api_generator"
    type: "openapi_generator"
    version: "1.0.0"
    
  - name: "database_designer"
    type: "schema_designer"
    version: "1.0.0"
    
  - name: "performance_optimizer"
    type: "backend_performance"
    version: "1.0.0"

context_requirements:
  api_complexity: "Complexité des endpoints"
  data_models: "Modèles de données"
  authentication: "Mécanismes d'authentification"
  rate_limiting: "Politiques de rate limiting"

outputs:
  required:
    - api_specification.yaml
    - database_schema.sql
    - service_implementations/
    - unit_tests/
  optional:
    - integration_tests/
    - performance_tests/
    - api_documentation/

learning_objectives:
  - "Optimiser les performances des API"
  - "Design des schémas de base de données"
  - "Implémenter l'authentification sécurisée"
  - "Gérer les migrations de données"
'@

$backendAgentConfig | Out-File -FilePath "$projectPath\agents\coder\sous_agents\backend_config.yaml" -Force -Encoding UTF8

# Code du sous-agent Backend
$backendAgentCode = @'
# agents/coder/sous_agents/backend_coder.py
import asyncio
from typing import Dict, Any, List
from pathlib import Path
import yaml
import json
from ...shared.base_agent import BaseAgent

class BackendCoderSubAgent(BaseAgent):
    """Sous-agent spécialisé en développement backend"""
    
    def __init__(self, config_path: str):
        super().__init__(config_path)
        self.languages = self.config.get("capabilities", {}).get("languages", [])
        self.frameworks = self._extract_frameworks()
        
    def _extract_frameworks(self) -> Dict[str, List[str]]:
        """Extrait les frameworks par langage"""
        frameworks = {}
        for lang_cap in self.languages:
            if '(' in lang_cap:
                lang = lang_cap.split('(')[0].strip()
                framework_str = lang_cap.split('(')[1].rstrip(')')
                frameworks[lang] = [f.strip() for f in framework_str.split(',')]
        return frameworks
    
    async def initialize(self) -> bool:
        """Initialise le sous-agent"""
        self.logger.info(f"Initialisation du Backend Coder")
        self.logger.info(f"Langages supportés: {list(self.frameworks.keys())}")
        return True
    
    async def develop_api(self, api_spec: Dict[str, Any]) -> Dict[str, Any]:
        """Développe une API complète"""
        self.logger.info(f"Développement de l'API: {api_spec.get('name', 'Unnamed API')}")
        
        # Sélection du stack technologique
        stack = await self._select_technology_stack(api_spec)
        
        # Génération du code
        generated_code = await self._generate_backend_code(api_spec, stack)
        
        # Création des tests
        tests = await self._generate_tests(api_spec, stack)
        
        # Documentation
        documentation = await self._generate_documentation(api_spec, stack)
        
        return {
            "technology_stack": stack,
            "generated_code": generated_code,
            "tests": tests,
            "documentation": documentation,
            "deployment_config": await self._generate_deployment_config(stack)
        }
    
    async def _select_technology_stack(self, api_spec: Dict[str, Any]) -> Dict[str, Any]:
        """Sélectionne le stack technologique optimal"""
        requirements = api_spec.get("requirements", {})
        
        # Critères de sélection
        if requirements.get("high_performance"):
            # Go ou Rust pour haute performance
            if "Go" in self.frameworks:
                return {
                    "language": "Go",
                    "framework": self.frameworks["Go"][0] if self.frameworks["Go"] else "Gin",
                    "database": "PostgreSQL",
                    "cache": "Redis"
                }
        
        if requirements.get("rapid_development"):
            # Python ou Node.js pour développement rapide
            if "Python" in self.frameworks:
                return {
                    "language": "Python",
                    "framework": self.frameworks["Python"][0] if self.frameworks["Python"] else "FastAPI",
                    "database": "PostgreSQL",
                    "cache": "Redis"
                }
        
        # Par défaut, utiliser Python
        return {
            "language": "Python",
            "framework": "FastAPI",
            "database": "PostgreSQL",
            "cache": "Redis"
        }
    
    async def _generate_backend_code(self, api_spec: Dict[str, Any], stack: Dict[str, Any]) -> Dict[str, Any]:
        """Génère le code backend"""
        language = stack["language"]
        framework = stack["framework"]
        
        code_structure = {
            "main_file": await self._generate_main_file(api_spec, language, framework),
            "models": await self._generate_models(api_spec, language),
            "routes": await self._generate_routes(api_spec, language, framework),
            "services": await self._generate_services(api_spec, language),
            "database": await self._generate_database_code(api_spec, stack["database"], language),
            "middleware": await self._generate_middleware(api_spec, language, framework),
            "config": await self._generate_config_files(language, framework)
        }
        
        return code_structure
    
    async def _generate_tests(self, api_spec: Dict[str, Any], stack: Dict[str, Any]) -> Dict[str, Any]:
        """Génère les tests"""
        language = stack["language"]
        
        tests = {
            "unit_tests": await self._generate_unit_tests(api_spec, language),
            "integration_tests": await self._generate_integration_tests(api_spec, language),
            "api_tests": await self._generate_api_tests(api_spec),
            "performance_tests": await self._generate_performance_tests(api_spec)
        }
        
        return tests
    
    async def execute(self, task: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Exécute une tâche de développement backend"""
        task_type = task.get("type", "develop_api")
        
        if task_type == "develop_api":
            return await self.develop_api(task.get("specification", {}))
        elif task_type == "optimize_performance":
            return await self.optimize_performance(task.get("codebase", {}))
        elif task_type == "refactor_code":
            return await self.refactor_code(task.get("codebase", {}))
        elif task_type == "add_feature":
            return await self.add_feature(task.get("feature", {}), task.get("codebase", {}))
        else:
            return {"error": f"Type de tâche non supporté: {task_type}"}
    
    async def optimize_performance(self, codebase: Dict[str, Any]) -> Dict[str, Any]:
        """Optimise les performances du code backend"""
        optimizations = []
        
        # Analyse des bottlenecks
        bottlenecks = await self._analyze_bottlenecks(codebase)
        
        for bottleneck in bottlenecks:
            optimization = await self._generate_optimization(bottleneck)
            optimizations.append(optimization)
        
        # Génération du code optimisé
        optimized_code = await self._apply_optimizations(codebase, optimizations)
        
        return {
            "bottlenecks_found": bottlenecks,
            "optimizations_applied": optimizations,
            "optimized_code": optimized_code,
            "performance_gain_estimate": await self._estimate_performance_gain(optimizations)
        }
    
    async def refactor_code(self, codebase: Dict[str, Any]) -> Dict[str, Any]:
        """Refactorise le code pour améliorer la qualité"""
        refactoring_actions = []
        
        # Détection des code smells
        code_smells = await self._detect_code_smells(codebase)
        
        for smell in code_smells:
            refactoring = await self._generate_refactoring(smell)
            refactoring_actions.append(refactoring)
        
        # Application des refactorings
        refactored_code = await self._apply_refactorings(codebase, refactoring_actions)
        
        return {
            "code_smells_found": code_smells,
            "refactoring_actions": refactoring_actions,
            "refactored_code": refactored_code,
            "quality_metrics": await self._calculate_quality_metrics(refactored_code)
        }
'@

$backendAgentCode | Out-File -FilePath "$projectPath\agents\coder\sous_agents\backend_coder.py" -Force -Encoding UTF8
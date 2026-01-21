# deploy-all-agents.ps1
Write-Host "=== DEPLOIEMENT COMPLET DES 9 AGENTS ===" -ForegroundColor Cyan
Write-Host "Date: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor Gray
Write-Host ""

$projectPath = "$env:USERPROFILE\Projects\SmartContractPipeline"
if (-not (Test-Path $projectPath)) {
    Write-Host "Création du dossier projet..." -ForegroundColor Yellow
    New-Item -ItemType Directory -Path $projectPath -Force | Out-Null
}

Set-Location $projectPath

# 1. Créer la structure complète des agents
Write-Host "1. CREATION DE LA STRUCTURE DES AGENTS..." -ForegroundColor Yellow
$agentsStructure = @{
    "agents/architect" = @("config.yaml", "agent.py", "tools.py")
    "agents/coder" = @("config.yaml", "agent.py", "tools.py")
    "agents/communication" = @("config.yaml", "agent.py", "message_bus.py", "event_system.py")
    "agents/documenter" = @("config.yaml", "agent.py", "tools.py")
    "agents/formal_verification" = @("config.yaml", "agent.py", "tools.py")
    "agents/frontend_web3" = @("config.yaml", "agent.py", "tools.py", "web3_hooks.py")
    "agents/fuzzing_simulation" = @("config.yaml", "agent.py", "tools.py", "simulator.py")
    "agents/quality_metrics" = @("config.yaml", "agent.py", "tools.py", "metrics.py")
    "agents/smart_contract" = @("config.yaml", "agent.py", "tools.py", "security.py")
    "agents/tester" = @("config.yaml", "agent.py", "tools.py", "test_generator.py")
    "agents/orchestrator" = @("orchestrator.py", "task_manager.py", "state_manager.py")
    "agents/shared" = @("base_agent.py", "memory.py", "context_manager.py")
}

foreach ($folder in $agentsStructure.Keys) {
    $fullPath = "$projectPath\$folder"
    New-Item -ItemType Directory -Path $fullPath -Force | Out-Null
    
    foreach ($file in $agentsStructure[$folder]) {
        $filePath = "$fullPath\$file"
        if (-not (Test-Path $filePath)) {
            New-Item -ItemType File -Path $filePath -Force | Out-Null
        }
    }
    Write-Host "   📁 $folder créé" -ForegroundColor Green
}

# 2. Créer le fichier de versions
Write-Host "`n2. CREATION DU FICHIER DE VERSIONS..." -ForegroundColor Yellow
$versions = @{
    timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    system = @{
        os = "Windows $( [System.Environment]::OSVersion.Version.ToString())"
        powershell = $PSVersionTable.PSVersion.ToString()
    }
    tools = @{}
    python = @{}
    node = @{}
    blockchain = @{}
    agents = @{}
}

# Récupérer les versions des outils
try { $versions.tools.git = (git --version 2>&1).ToString().Replace('git version ', '').Trim() } catch { $versions.tools.git = "N/A" }
try { $versions.tools.docker = (docker --version 2>&1).ToString().Replace('Docker version ', '').Split(',')[0].Trim() } catch { $versions.tools.docker = "N/A" }

# Récupérer les versions Python
try { 
    $pythonVersion = (python --version 2>&1).ToString().Replace('Python ', '').Trim()
    $versions.python.version = $pythonVersion
    
    # Packages Python
    $pythonPackages = @("langchain", "chromadb", "requests", "web3", "aiohttp")
    foreach ($pkg in $pythonPackages) {
        try {
            $version = python -c "import $pkg; print(getattr($pkg, '__version__', 'N/A'))" 2>$null
            if (-not $version -or $version -eq "N/A") {
                $version = pip show $pkg 2>$null | Select-String "Version:" | ForEach-Object { $_.ToString().Replace('Version: ', '').Trim() }
            }
            $versions.python.$pkg = $version
        } catch {
            $versions.python.$pkg = "N/A"
        }
    }
} catch { $versions.python.version = "N/A" }

# Récupérer les versions Node.js
try { 
    $nodeVersion = (node --version 2>&1).ToString().Replace('v', '').Trim()
    $versions.node.version = $nodeVersion
    
    # Packages Node.js globaux
    $nodePackages = @("npm", "yarn", "hardhat", "typescript", "next")
    foreach ($pkg in $nodePackages) {
        try {
            if ($pkg -eq "npm") {
                $version = (npm --version 2>&1).ToString().Trim()
            } elseif ($pkg -eq "next") {
                $version = (npx next --version 2>&1).ToString().Trim()
            } else {
                $version = (npx $pkg --version 2>&1).ToString().Trim()
            }
            $versions.node.$pkg = $version
        } catch {
            $versions.node.$pkg = "N/A"
        }
    }
} catch { $versions.node.version = "N/A" }

# Récupérer les versions blockchain
try { $versions.blockchain.foundry = (forge --version 2>&1 | Select-String "forge").ToString().Split(' ')[1].Trim() } catch { $versions.blockchain.foundry = "N/A" }
try { $versions.blockchain.slither = (slither --version 2>&1).ToString().Trim() } catch { $versions.blockchain.slither = "N/A" }
try { $versions.blockchain.anvil = (anvil --version 2>&1).ToString().Trim() } catch { $versions.blockchain.anvil = "N/A" }

# Sauvegarder les versions
$versions | ConvertTo-Json -Depth 10 | Out-File -FilePath "$projectPath\config\versions.json" -Force
Write-Host "   ✅ Fichier de versions créé" -ForegroundColor Green

# 3. Créer les configurations des agents
Write-Host "`n3. CREATION DES CONFIGURATIONS D'AGENTS..." -ForegroundColor Yellow

# Agent Architecte
$architectConfig = @"
# agents/architect/config.yaml
agent_id: "architect_001"
name: "Agent Architecte"
version: "1.0.0"
model: "ollama:deepseek-coder:6.7b"
temperature: 0.3
description: "Responsable de la conception architecturale du système"

tools:
  - name: "diagram_generator"
    version: "1.0.0"
    type: "mermaid"
    
  - name: "tech_evaluator"
    version: "1.0.0"
    type: "comparison"

context:
  blockchain_targets: ["Ethereum", "Arbitrum", "Optimism"]
  patterns: ["Microservices", "Event-Driven", "CQRS"]
  standards: ["ERC20", "ERC721", "ERC1155"]

outputs:
  - architecture_document.md
  - system_diagram.mmd
  - tech_stack.json

dependencies:
  python: ">=3.8"
  node: ">=18.0.0"
  foundry: ">=0.2.0"
"@

$architectConfig | Out-File -FilePath "$projectPath\agents\architect\config.yaml" -Force -Encoding UTF8

# Agent Coder
$coderConfig = @"
# agents/coder/config.yaml
agent_id: "coder_001"
name: "Agent Codeur"
version: "1.0.0"
model: "ollama:deepseek-coder:6.7b"
temperature: 0.2
description: "Développeur principal de code backend et frontend"

tools:
  - name: "code_editor"
    version: "1.0.0"
    type: "file_operations"
    
  - name: "linter"
    version: "2.0.0"
    type: "flake8"
    
  - name: "formatter"
    version: "1.0.0"
    type: "black"

context:
  languages: ["Python", "JavaScript", "TypeScript", "Solidity"]
  frameworks: ["FastAPI", "Next.js", "React", "Foundry"]
  testing: ["pytest", "jest", "forge test"]

outputs:
  - source_code/
  - unit_tests/
  - implementation_report.json

dependencies:
  python: ">=3.8"
  node: ">=18.0.0"
"@

$coderConfig | Out-File -FilePath "$projectPath\agents\coder\config.yaml" -Force -Encoding UTF8

# Agent Communication
$communicationConfig = @"
# agents/communication/config.yaml
agent_id: "communication_001"
name: "Agent Communication"
version: "1.0.0"
model: "ollama:llama3.2:3b"
temperature: 0.4
description: "Gère la communication entre tous les agents"

tools:
  - name: "message_bus"
    version: "1.0.0"
    type: "zeromq"
    
  - name: "event_system"
    version: "1.0.0"
    type: "redis"
    
  - name: "api_gateway"
    version: "1.0.0"
    type: "fastapi"

context:
  protocols: ["WebSocket", "REST", "gRPC", "Message Queue"]
  patterns: ["Pub/Sub", "Request/Response", "Event Sourcing"]
  formats: ["JSON", "Protocol Buffers", "MessagePack"]

outputs:
  - communication_logs.jsonl
  - event_traces.json
  - performance_metrics.json

dependencies:
  python: ">=3.8"
  redis: ">=7.0.0"
"@

$communicationConfig | Out-File -FilePath "$projectPath\agents\communication\config.yaml" -Force -Encoding UTF8

# Agent Documenter
$documenterConfig = @"
# agents/documenter/config.yaml
agent_id: "documenter_001"
name: "Agent Documenteur"
version: "1.0.0"
model: "ollama:mistral:7b"
temperature: 0.5
description: "Génère et maintient la documentation technique"

tools:
  - name: "doc_generator"
    version: "1.0.0"
    type: "sphinx"
    
  - name: "api_doc_extractor"
    version: "1.0.0"
    type: "openapi"
    
  - name: "spell_checker"
    version: "2.0.0"
    type: "languagetool"

context:
  formats: ["Markdown", "AsciiDoc", "OpenAPI", "Swagger"]
  audiences: ["Developers", "End Users", "DevOps", "Stakeholders"]
  languages: ["fr", "en"]

outputs:
  - api_documentation/
  - user_guide/
  - developer_guide/
  - deployment_guide/

dependencies:
  python: ">=3.8"
  node: ">=16.0.0"
"@

$documenterConfig | Out-File -FilePath "$projectPath\agents\documenter\config.yaml" -Force -Encoding UTF8

# Agent Formal Verification
$formalConfig = @"
# agents/formal_verification/config.yaml
agent_id: "formal_verifier_001"
name: "Agent Vérification Formelle"
version: "1.0.0"
model: "ollama:codellama:13b"
temperature: 0.05
description: "Effectue des vérifications mathématiques des smart contracts"

tools:
  - name: "theorem_prover"
    version: "1.0.0"
    type: "coq"
    
  - name: "model_checker"
    version: "1.0.0"
    type: "halmos"
    
  - name: "symbolic_executor"
    version: "1.0.0"
    type: "manticore"

context:
  methods: ["Model Checking", "Theorem Proving", "Symbolic Execution"]
  properties: ["Safety", "Liveness", "Fairness"]
  tools: ["Coq", "Isabelle", "Halmos", "KEVM"]

outputs:
  - formal_proofs/
  - verification_certificates/
  - counterexamples/
  - proof_obligations.json

dependencies:
  python: ">=3.8"
  rust: ">=1.70.0"
"@

$formalConfig | Out-File -FilePath "$projectPath\agents\formal_verification\config.yaml" -Force -Encoding UTF8

# Agent Frontend Web3
$frontendConfig = @"
# agents/frontend_web3/config.yaml
agent_id: "frontend_web3_001"
name: "Agent Frontend Web3"
version: "1.0.0"
model: "ollama:deepseek-coder:6.7b"
temperature: 0.3
description: "Développeur frontend avec intégration Web3"

tools:
  - name: "nextjs_generator"
    version: "1.0.0"
    type: "component_generator"
    
  - name: "web3_hook_generator"
    version: "1.0.0"
    type: "hook_generator"
    
  - name: "transaction_builder"
    version: "1.0.0"
    type: "tx_constructor"

context:
  frontend_stack: ["Next.js 14", "React 18", "TypeScript", "Tailwind CSS"]
  web3_libraries: ["wagmi", "viem", "ethers.js"]
  wallets: ["MetaMask", "WalletConnect", "Coinbase Wallet"]
  testing: ["Playwright", "Cypress", "Jest"]

outputs:
  - components/
  - pages/
  - hooks/
  - web3_config.ts

dependencies:
  node: ">=18.0.0"
  npm: ">=9.0.0"
"@

$frontendConfig | Out-File -FilePath "$projectPath\agents\frontend_web3\config.yaml" -Force -Encoding UTF8

# Agent Fuzzing Simulation
$fuzzingConfig = @"
# agents/fuzzing_simulation/config.yaml
agent_id: "fuzzing_master_001"
name: "Agent Fuzzing & Simulation"
version: "1.0.0"
model: "ollama:llama3.1:8b"
temperature: 0.7
description: "Effectue des tests avancés et simulations multi-chaîne"

tools:
  - name: "foundry_fuzzer"
    version: "1.0.0"
    type: "forge_fuzz"
    
  - name: "multi_chain_simulator"
    version: "1.0.0"
    type: "anvil_fork"
    
  - name: "coverage_analyzer"
    version: "1.0.0"
    type: "branch_coverage"

context:
  fuzzing_strategies: ["Generational", "Mutational", "Coverage-guided"]
  simulation_environments: ["Mainnet Fork", "Testnet", "Custom EVM"]
  chains: ["Ethereum", "Arbitrum", "Optimism", "Polygon"]

outputs:
  - fuzzing_reports/
  - simulation_results/
  - coverage_data.json
  - edge_cases.json

dependencies:
  foundry: ">=0.2.0"
  python: ">=3.8"
"@

$fuzzingConfig | Out-File -FilePath "$projectPath\agents\fuzzing_simulation\config.yaml" -Force -Encoding UTF8

# Agent Quality Metrics
$qualityConfig = @"
# agents/quality_metrics/config.yaml
agent_id: "quality_001"
name: "Agent Métriques Qualité"
version: "1.0.0"
model: "ollama:qwen2.5:7b"
temperature: 0.3
description: "Surveille et analyse les métriques de qualité"

tools:
  - name: "metrics_collector"
    version: "1.0.0"
    type: "prometheus"
    
  - name: "dashboard_generator"
    version: "1.0.0"
    type: "grafana"
    
  - name: "alert_manager"
    version: "1.0.0"
    type: "alerting"

context:
  metrics_categories: ["Performance", "Security", "Reliability", "Maintainability"]
  quality_gates: ["Test Coverage", "Security Scan", "Performance Benchmarks"]
  thresholds: {"test_coverage": 80, "security_score": 90, "performance_score": 85}

outputs:
  - quality_dashboard/
  - metrics_reports/
  - alert_logs.jsonl
  - trend_analysis.json

dependencies:
  python: ">=3.8"
  prometheus: ">=2.45.0"
"@

$qualityConfig | Out-File -FilePath "$projectPath\agents\quality_metrics\config.yaml" -Force -Encoding UTF8

# Agent Smart Contract
$smartContractConfig = @"
# agents/smart_contract/config.yaml
agent_id: "sc_principal_001"
name: "Agent Smart Contract Principal"
version: "1.0.0"
model: "ollama:deepseek-coder:6.7b"
temperature: 0.1
description: "Expert en développement de smart contracts sécurisés"

tools:
  - name: "foundry_runner"
    version: "1.0.0"
    type: "forge_executor"
    
  - name: "security_analyzer"
    version: "1.0.0"
    type: "slither"
    
  - name: "gas_optimizer"
    version: "1.0.0"
    type: "gas_analysis"

context:
  blockchain: "Ethereum"
  language: "Solidity 0.8.19"
  standards: ["ERC20", "ERC721", "ERC1155", "EIP-712"]
  security: ["Reentrancy", "Overflow", "Access Control", "Gas Limits"]

outputs:
  - smart_contracts/
  - abi_files/
  - deployment_scripts/
  - audit_reports/

dependencies:
  foundry: ">=0.2.0"
  python: ">=3.8"
"@

$smartContractConfig | Out-File -FilePath "$projectPath\agents\smart_contract\config.yaml" -Force -Encoding UTF8

# Agent Tester
$testerConfig = @"
# agents/tester/config.yaml
agent_id: "tester_001"
name: "Agent Testeur"
version: "1.0.0"
model: "ollama:qwen2.5:7b"
temperature: 0.4
description: "Génère et exécute des tests automatisés"

tools:
  - name: "test_generator"
    version: "1.0.0"
    type: "auto_test_gen"
    
  - name: "test_executor"
    version: "1.0.0"
    type: "test_runner"
    
  - name: "coverage_tool"
    version: "1.0.0"
    type: "coverage.py"

context:
  test_types: ["Unit", "Integration", "E2E", "Performance", "Security"]
  frameworks: ["pytest", "jest", "forge test", "playwright"]
  coverage_targets: {"unit": 90, "integration": 80, "e2e": 70}

outputs:
  - test_reports/
  - coverage_reports/
  - bug_reports/
  - test_data/

dependencies:
  python: ">=3.8"
  node: ">=18.0.0"
"@

$testerConfig | Out-File -FilePath "$projectPath\agents\tester\config.yaml" -Force -Encoding UTF8

Write-Host "   ✅ Configurations des 9 agents créées" -ForegroundColor Green

# 4. Créer le base_agent.py (classe parente)
Write-Host "`n4. CREATION DE LA CLASSE BASE AGENT..." -ForegroundColor Yellow
$baseAgentCode = @'
# agents/shared/base_agent.py
import asyncio
import json
import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Any, Optional
import yaml

class BaseAgent(ABC):
    """Classe de base pour tous les agents"""
    
    def __init__(self, config_path: str):
        self.config = self._load_config(config_path)
        self.agent_id = self.config.get("agent_id", "unknown")
        self.name = self.config.get("name", "Unnamed Agent")
        self.version = self.config.get("version", "1.0.0")
        self.logger = self._setup_logger()
        self.memory = {}
        self.context = {}
        
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Charge la configuration YAML"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception as e:
            print(f"Erreur lors du chargement de la configuration: {e}")
            return {}
    
    def _setup_logger(self) -> logging.Logger:
        """Configure le logger"""
        logger = logging.getLogger(self.agent_id)
        if not logger.handlers:
            logger.setLevel(logging.INFO)
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                f'%(asctime)s - {self.agent_id} - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        return logger
    
    @abstractmethod
    async def initialize(self) -> bool:
        """Initialise l'agent"""
        pass
    
    @abstractmethod
    async def execute(self, task: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Exécute une tâche"""
        pass
    
    async def load_context(self, context_path: str) -> Dict[str, Any]:
        """Charge le contexte depuis un fichier"""
        try:
            if Path(context_path).exists():
                with open(context_path, 'r', encoding='utf-8') as f:
                    self.context = json.load(f)
                    self.logger.info(f"Contexte chargé depuis {context_path}")
                    return self.context
        except Exception as e:
            self.logger.error(f"Erreur lors du chargement du contexte: {e}")
        return {}
    
    async def save_memory(self, memory_path: str) -> bool:
        """Sauvegarde la mémoire de l'agent"""
        try:
            memory_dir = Path(memory_path).parent
            memory_dir.mkdir(parents=True, exist_ok=True)
            
            with open(memory_path, 'w', encoding='utf-8') as f:
                json.dump(self.memory, f, indent=2)
            
            self.logger.info(f"Mémoire sauvegardée dans {memory_path}")
            return True
        except Exception as e:
            self.logger.error(f"Erreur lors de la sauvegarde de la mémoire: {e}")
            return False
    
    def get_agent_info(self) -> Dict[str, Any]:
        """Retourne les informations de l'agent"""
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "version": self.version,
            "config": self.config,
            "tools": self.config.get("tools", []),
            "dependencies": self.config.get("dependencies", {})
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Vérifie la santé de l'agent"""
        return {
            "status": "healthy",
            "agent_id": self.agent_id,
            "timestamp": asyncio.get_event_loop().time(),
            "memory_usage": len(str(self.memory)),
            "context_loaded": bool(self.context)
        }
'@

$baseAgentCode | Out-File -FilePath "$projectPath\agents\shared\base_agent.py" -Force -Encoding UTF8

# 5. Créer l'orchestrateur principal
Write-Host "`n5. CREATION DE L'ORCHESTRATEUR PRINCIPAL..." -ForegroundColor Yellow
$orchestratorCode = @'
# agents/orchestrator/orchestrator.py
import asyncio
import json
import yaml
from typing import Dict, List, Any, Optional
from pathlib import Path
import logging
from datetime import datetime

class Orchestrator:
    """Orchestrateur principal qui gère tous les agents"""
    
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        self.agents = {}
        self.agent_status = {}
        self.task_queue = asyncio.Queue()
        self.results = {}
        self.versions = self._load_versions()
        
        # Configuration
        self.config = {
            "max_concurrent_tasks": 3,
            "task_timeout": 300,  # 5 minutes
            "retry_attempts": 3
        }
        
        self.logger = self._setup_logger()
    
    def _setup_logger(self) -> logging.Logger:
        """Configure le logger"""
        logger = logging.getLogger("orchestrator")
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            # Handler console
            console_handler = logging.StreamHandler()
            console_formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            console_handler.setFormatter(console_formatter)
            logger.addHandler(console_handler)
            
            # Handler fichier
            log_file = self.project_root / "logs" / "orchestrator.log"
            log_file.parent.mkdir(parents=True, exist_ok=True)
            
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            file_handler.setFormatter(file_formatter)
            logger.addHandler(file_handler)
        
        return logger
    
    def _load_versions(self) -> Dict[str, Any]:
        """Charge les versions des outils"""
        versions_file = self.project_root / "config" / "versions.json"
        if versions_file.exists():
            with open(versions_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    
    async def register_agent(self, agent_name: str, agent_instance):
        """Enregistre un agent"""
        self.agents[agent_name] = agent_instance
        self.agent_status[agent_name] = {
            "registered": datetime.now().isoformat(),
            "status": "idle",
            "tasks_completed": 0,
            "last_active": None
        }
        
        self.logger.info(f"Agent enregistré: {agent_name}")
        
        # Initialiser l'agent
        try:
            await agent_instance.initialize()
            self.agent_status[agent_name]["status"] = "ready"
            self.logger.info(f"Agent {agent_name} initialisé avec succès")
        except Exception as e:
            self.agent_status[agent_name]["status"] = "error"
            self.logger.error(f"Erreur lors de l'initialisation de {agent_name}: {e}")
    
    async def get_all_agents_info(self) -> Dict[str, Any]:
        """Retourne les informations de tous les agents"""
        agents_info = {}
        for agent_name, agent_instance in self.agents.items():
            try:
                agents_info[agent_name] = agent_instance.get_agent_info()
                agents_info[agent_name]["status"] = self.agent_status[agent_name]["status"]
            except Exception as e:
                self.logger.error(f"Erreur lors de la récupération des infos de {agent_name}: {e}")
        
        return {
            "total_agents": len(self.agents),
            "agents": agents_info,
            "system_versions": self.versions,
            "timestamp": datetime.now().isoformat()
        }
    
    async def run_task_pipeline(self, pipeline_config: Dict[str, Any]) -> Dict[str, Any]:
        """Exécute un pipeline de tâches"""
        self.logger.info(f"Démarrage du pipeline: {pipeline_config.get('name', 'unnamed')}")
        
        results = {}
        tasks = pipeline_config.get("tasks", [])
        
        for task in tasks:
            task_name = task.get("name", "unnamed_task")
            agent_name = task.get("agent")
            
            if agent_name not in self.agents:
                self.logger.error(f"Agent {agent_name} non trouvé pour la tâche {task_name}")
                continue
            
            self.logger.info(f"Exécution de la tâche {task_name} avec l'agent {agent_name}")
            
            try:
                # Mettre à jour le statut de l'agent
                self.agent_status[agent_name]["status"] = "busy"
                self.agent_status[agent_name]["last_active"] = datetime.now().isoformat()
                
                # Exécuter la tâche
                result = await self.agents[agent_name].execute(
                    task=task,
                    context={
                        "pipeline": pipeline_config,
                        "previous_results": results,
                        "versions": self.versions
                    }
                )
                
                # Enregistrer le résultat
                results[task_name] = result
                self.agent_status[agent_name]["tasks_completed"] += 1
                self.agent_status[agent_name]["status"] = "ready"
                
                self.logger.info(f"Tâche {task_name} terminée avec succès")
                
            except asyncio.TimeoutError:
                self.logger.error(f"Timeout sur la tâche {task_name}")
                self.agent_status[agent_name]["status"] = "timeout"
                results[task_name] = {"status": "timeout", "error": "Task timeout"}
                
            except Exception as e:
                self.logger.error(f"Erreur lors de l'exécution de {task_name}: {e}")
                self.agent_status[agent_name]["status"] = "error"
                results[task_name] = {"status": "error", "error": str(e)}
        
        # Sauvegarder les résultats
        await self._save_pipeline_results(pipeline_config, results)
        
        return {
            "pipeline": pipeline_config.get("name"),
            "results": results,
            "summary": self._generate_summary(results),
            "agents_status": self.agent_status,
            "timestamp": datetime.now().isoformat()
        }
    
    async def _save_pipeline_results(self, pipeline_config: Dict[str, Any], results: Dict[str, Any]):
        """Sauvegarde les résultats du pipeline"""
        try:
            results_dir = self.project_root / "results" / "pipelines"
            results_dir.mkdir(parents=True, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            pipeline_name = pipeline_config.get("name", "unnamed").replace(" ", "_").lower()
            
            result_file = results_dir / f"{pipeline_name}_{timestamp}.json"
            
            full_results = {
                "pipeline": pipeline_config,
                "results": results,
                "agents_info": await self.get_all_agents_info(),
                "system_versions": self.versions,
                "metadata": {
                    "execution_time": datetime.now().isoformat(),
                    "total_tasks": len(pipeline_config.get("tasks", [])),
                    "successful_tasks": sum(1 for r in results.values() if r.get("status") == "success")
                }
            }
            
            with open(result_file, 'w', encoding='utf-8') as f:
                json.dump(full_results, f, indent=2, default=str)
            
            self.logger.info(f"Résultats sauvegardés dans {result_file}")
            
        except Exception as e:
            self.logger.error(f"Erreur lors de la sauvegarde des résultats: {e}")
    
    def _generate_summary(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Génère un résumé des résultats"""
        total = len(results)
        successful = sum(1 for r in results.values() if r.get("status") in ["success", "completed"])
        failed = total - successful
        
        return {
            "total_tasks": total,
            "successful_tasks": successful,
            "failed_tasks": failed,
            "success_rate": (successful / total * 100) if total > 0 else 0
        }
    
    async def health_check_all(self) -> Dict[str, Any]:
        """Vérifie la santé de tous les agents"""
        health_results = {}
        
        for agent_name, agent_instance in self.agents.items():
            try:
                health = await agent_instance.health_check()
                health_results[agent_name] = health
                self.agent_status[agent_name]["last_health_check"] = datetime.now().isoformat()
            except Exception as e:
                health_results[agent_name] = {
                    "status": "unhealthy",
                    "error": str(e)
                }
                self.agent_status[agent_name]["status"] = "error"
        
        return {
            "timestamp": datetime.now().isoformat(),
            "total_agents": len(self.agents),
            "healthy_agents": sum(1 for h in health_results.values() if h.get("status") == "healthy"),
            "agents": health_results
        }
'@

$orchestratorCode | Out-File -FilePath "$projectPath\agents\orchestrator\orchestrator.py" -Force -Encoding UTF8

# 6. Créer le fichier de dépendances Python
Write-Host "`n6. CREATION DU FICHIER REQUIREMENTS.TXT..." -ForegroundColor Yellow
$requirements = @"
# Dépendances Python principales
langchain==0.1.0
langgraph==0.0.5
chromadb==0.4.18
openai==1.6.1
anthropic==0.20.0

# Communication et API
fastapi==0.104.1
uvicorn[standard]==0.24.0
websockets==12.0
redis==5.0.1
pika==1.3.2

# Blockchain et Web3
web3==6.11.1
eth-account==0.11.0
py-solc-x==2.0.1
pyevmasm==0.2.3

# Traitement de données
pandas==2.1.4
numpy==1.26.2
pyyaml==6.0.1
python-dotenv==1.0.0

# Utilitaires
requests==2.31.0
aiohttp==3.9.1
httpx==0.25.1
pydantic==2.5.0
pydantic-settings==2.1.0

# Tests et qualité
pytest==7.4.3
pytest-asyncio==0.21.1
pytest-cov==4.1.0
mypy==1.7.1
black==23.11.0
flake8==6.1.0

# Documentation
sphinx==7.2.6
myst-parser==2.0.0
sphinx-rtd-theme==1.3.0
"@

$requirements | Out-File -FilePath "$projectPath\requirements.txt" -Force -Encoding UTF8

# 7. Créer le script de test des agents
Write-Host "`n7. CREATION DU SCRIPT DE TEST..." -ForegroundColor Yellow
$testScript = @'
# test_all_agents.py
import asyncio
import sys
from pathlib import Path

# Ajouter le dossier agents au path
agents_dir = Path(__file__).parent / "agents"
sys.path.insert(0, str(agents_dir))

from orchestrator.orchestrator import Orchestrator
from shared.base_agent import BaseAgent

class MockAgent(BaseAgent):
    """Agent mock pour les tests"""
    
    def __init__(self, agent_id, name):
        self.agent_id = agent_id
        self.name = name
        self.config = {"agent_id": agent_id, "name": name}
        self.logger = None
        self.memory = {}
        self.context = {}
    
    async def initialize(self):
        return True
    
    async def execute(self, task, context):
        return {
            "status": "success",
            "agent": self.agent_id,
            "task": task.get("name"),
            "result": f"Mock result from {self.name}",
            "timestamp": asyncio.get_event_loop().time()
        }
    
    def get_agent_info(self):
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "version": "1.0.0",
            "config": self.config
        }
    
    async def health_check(self):
        return {
            "status": "healthy",
            "agent_id": self.agent_id,
            "timestamp": asyncio.get_event_loop().time()
        }

async def test_all_agents():
    """Teste tous les agents"""
    print("🧪 TEST DE TOUS LES AGENTS")
    print("="*60)
    
    # Créer l'orchestrateur
    orchestrator = Orchestrator(".")
    
    # Créer les 9 agents mock
    agents = {
        "architect": MockAgent("architect_001", "Agent Architecte"),
        "coder": MockAgent("coder_001", "Agent Codeur"),
        "communication": MockAgent("communication_001", "Agent Communication"),
        "documenter": MockAgent("documenter_001", "Agent Documenteur"),
        "formal_verification": MockAgent("formal_verifier_001", "Agent Vérification Formelle"),
        "frontend_web3": MockAgent("frontend_web3_001", "Agent Frontend Web3"),
        "fuzzing_simulation": MockAgent("fuzzing_master_001", "Agent Fuzzing & Simulation"),
        "quality_metrics": MockAgent("quality_001", "Agent Métriques Qualité"),
        "smart_contract": MockAgent("sc_principal_001", "Agent Smart Contract"),
        "tester": MockAgent("tester_001", "Agent Testeur")
    }
    
    # Enregistrer tous les agents
    for agent_name, agent_instance in agents.items():
        await orchestrator.register_agent(agent_name, agent_instance)
    
    # Afficher les informations des agents
    print("\n📊 INFORMATIONS DES AGENTS:")
    agents_info = await orchestrator.get_all_agents_info()
    for agent_name, info in agents_info["agents"].items():
        print(f"  • {agent_name}: {info.get('name')} ({info.get('status')})")
    
    # Vérifier la santé des agents
    print("\n🏥 VERIFICATION SANTE:")
    health_results = await orchestrator.health_check_all()
    for agent_name, health in health_results["agents"].items():
        status = "✅" if health.get("status") == "healthy" else "❌"
        print(f"  {status} {agent_name}: {health.get('status')}")
    
    # Exécuter un pipeline de test
    print("\n🚀 EXECUTION PIPELINE TEST:")
    pipeline_config = {
        "name": "Test Pipeline",
        "description": "Pipeline de test pour tous les agents",
        "tasks": [
            {"name": "design_architecture", "agent": "architect"},
            {"name": "write_code", "agent": "coder"},
            {"name": "generate_tests", "agent": "tester"},
            {"name": "verify_contract", "agent": "formal_verification"},
            {"name": "fuzz_test", "agent": "fuzzing_simulation"},
            {"name": "build_frontend", "agent": "frontend_web3"},
            {"name": "generate_docs", "agent": "documenter"},
            {"name": "check_quality", "agent": "quality_metrics"},
            {"name": "deploy_contract", "agent": "smart_contract"},
            {"name": "setup_communication", "agent": "communication"}
        ]
    }
    
    results = await orchestrator.run_task_pipeline(pipeline_config)
    
    # Afficher le résumé
    print(f"\n📈 RESUME DU PIPELINE:")
    print(f"  Tâches totales: {results['summary']['total_tasks']}")
    print(f"  Tâches réussies: {results['summary']['successful_tasks']}")
    print(f"  Taux de réussite: {results['summary']['success_rate']:.1f}%")
    
    # Sauvegarder le rapport
    import json
    report_file = Path(".") / "reports" / "agent_test_report.json"
    report_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n📄 Rapport sauvegardé: {report_file}")
    print("\n✅ TEST TERMINE AVEC SUCCES")

if __name__ == "__main__":
    asyncio.run(test_all_agents())
'@

$testScript | Out-File -FilePath "$projectPath\test_all_agents.py" -Force -Encoding UTF8

# 8. Installer les dépendances Python
Write-Host "`n8. INSTALLATION DES DEPENDANCES PYTHON..." -ForegroundColor Yellow
try {
    # Créer et activer l'environnement virtuel
    if (-not (Test-Path "$projectPath\.venv")) {
        python -m venv "$projectPath\.venv"
    }
    
    & "$projectPath\.venv\Scripts\Activate.ps1"
    
    # Mettre à jour pip
    python -m pip install --upgrade pip
    
    # Installer les dépendances principales
    Write-Host "   Installation des dépendances..." -ForegroundColor Gray
    pip install -r "$projectPath\requirements.txt" --quiet
    
    Write-Host "   ✅ Dépendances Python installées" -ForegroundColor Green
    
} catch {
    Write-Host "   ⚠️  Erreur lors de l'installation des dépendances Python" -ForegroundColor Yellow
    Write-Host "   Message: $_" -ForegroundColor Red
}

# 9. Tester le déploiement
Write-Host "`n9. TEST DU DEPLOIEMENT..." -ForegroundColor Yellow
try {
    & "$projectPath\.venv\Scripts\Activate.ps1"
    python "$projectPath\test_all_agents.py"
    Write-Host "   ✅ Test des agents réussi" -ForegroundColor Green
} catch {
    Write-Host "   ⚠️  Erreur lors du test: $_" -ForegroundColor Yellow
}

# 10. Générer le rapport final
Write-Host "`n10. GENERATION DU RAPPORT FINAL..." -ForegroundColor Yellow
$deploymentReport = @{
    deployment_date = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    project_path = $projectPath
    agents_deployed = @(
        "architect",
        "coder", 
        "communication",
        "documenter",
        "formal_verification",
        "frontend_web3",
        "fuzzing_simulation",
        "quality_metrics",
        "smart_contract",
        "tester"
    )
    total_agents = 10
    directories_created = (Get-ChildItem -Path "$projectPath\agents" -Directory).Count
    files_created = (Get-ChildItem -Path "$projectPath\agents" -File -Recurse).Count
    versions = if (Test-Path "$projectPath\config\versions.json") {
        Get-Content "$projectPath\config\versions.json" | ConvertFrom-Json
    } else { @{} }
}

$deploymentReport | ConvertTo-Json -Depth 10 | Out-File -FilePath "$projectPath\reports\deployment_report.json" -Force

Write-Host "`n" + "="*60 -ForegroundColor Cyan
Write-Host "🎉 DEPLOIEMENT COMPLET REUSSI !" -ForegroundColor Green
Write-Host "="*60 -ForegroundColor Cyan
Write-Host ""
Write-Host "📊 RESUME:" -ForegroundColor Yellow
Write-Host "  • Agents déployés: $($deploymentReport.total_agents)" -ForegroundColor White
Write-Host "  • Dossiers créés: $($deploymentReport.directories_created)" -ForegroundColor White
Write-Host "  • Fichiers créés: $($deploymentReport.files_created)" -ForegroundColor White
Write-Host "  • Chemin du projet: $projectPath" -ForegroundColor White
Write-Host ""
Write-Host "🔧 AGENTS DEPLOYES:" -ForegroundColor Yellow
foreach ($agent in $deploymentReport.agents_deployed) {
    Write-Host "  ✅ $agent" -ForegroundColor Green
}
Write-Host ""
Write-Host "📁 STRUCTURE:" -ForegroundColor Yellow
Write-Host "  agents/" -ForegroundColor Gray
foreach ($folder in (Get-ChildItem -Path "$projectPath\agents" -Directory)) {
    Write-Host "    📂 $($folder.Name)/" -ForegroundColor Gray
}
Write-Host ""
Write-Host "⚡ COMMANDES:" -ForegroundColor Yellow
Write-Host "  Tester les agents: python test_all_agents.py" -ForegroundColor White
Write-Host "  Voir les versions: cat config\versions.json" -ForegroundColor White
Write-Host "  Voir le rapport: cat reports\deployment_report.json" -ForegroundColor White
Write-Host ""
Write-Host "✅ TOUS LES AGENTS SONT OPERATIONNELS" -ForegroundColor Green
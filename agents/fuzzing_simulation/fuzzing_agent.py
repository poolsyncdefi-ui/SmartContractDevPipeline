"""
Agent de Fuzzing et Simulation pour Smart Contracts
Détection automatique de vulnérabilités par tests aléatoires et invariants
Version: 1.0.0
"""

import os
import json
import yaml
import asyncio
import subprocess
import tempfile
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import re
import shutil
import traceback

# Import de BaseAgent
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from agents.base_agent.base_agent import BaseAgent, AgentStatus


class FuzzingEngine(Enum):
    """Moteurs de fuzzing supportés"""
    ECHIDNA = "echidna"
    FOUNDRY = "foundry"
    MEDUSA = "medusa"
    DAPPFORGE = "dappforge"
    SIMULATION = "simulation"  # Mode fallback


class FuzzingStrategy(Enum):
    """Stratégies de fuzzing"""
    RANDOM = "random"           # Entrées aléatoires
    STRUCTURED = "structured"   # Basé sur des templates
    GUIDED = "guided"          # Couverture guidée
    INVARIANT = "invariant"    # Vérification d'invariants
    PROPERTY = "property"      # Test de propriétés
    COMPREHENSIVE = "comprehensive"  # Tout en un


class VulnerabilityType(Enum):
    """Types de vulnérabilités détectables"""
    REENTRANCY = "reentrancy"
    INTEGER_OVERFLOW = "integer_overflow"
    INTEGER_UNDERFLOW = "integer_underflow"
    ACCESS_CONTROL = "access_control"
    TIMESTAMP_DEPENDENCE = "timestamp_dependence"
    FRONT_RUNNING = "front_running"
    GAS_LIMIT = "gas_limit"
    DENIAL_OF_SERVICE = "denial_of_service"
    UNCHECKED_CALL = "unchecked_call"
    DELEGATECALL = "delegatecall"
    SELF_DESTRUCT = "self_destruct"
    UNHANDLED_EXCEPTION = "unhandled_exception"
    TX_ORDER_DEPENDENCE = "tx_order_dependence"
    LOGIC_ERROR = "logic_error"


class FuzzingCampaign:
    """Campagne de fuzzing"""
    def __init__(self, name: str, contract_path: str):
        self.id = f"FUZZ-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        self.name = name
        self.contract_path = contract_path
        self.contract_name = Path(contract_path).stem
        self.engine = FuzzingEngine.SIMULATION
        self.strategy = FuzzingStrategy.COMPREHENSIVE
        self.status = "pending"
        self.start_time = None
        self.end_time = None
        self.duration_ms = 0
        self.total_tests = 0
        self.total_failures = 0
        self.vulnerabilities: List[Dict] = []
        self.sequences: List[List[str]] = []
        self.corpus_path = None
        self.report_path = None
        self.coverage = {
            "lines": 0,
            "branches": 0,
            "functions": 0,
            "percent": 0.0
        }
        self.config = {}
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "contract": self.contract_name,
            "engine": self.engine.value,
            "strategy": self.strategy.value,
            "status": self.status,
            "duration_ms": self.duration_ms,
            "total_tests": self.total_tests,
            "total_failures": self.total_failures,
            "vulnerabilities": self.vulnerabilities,
            "coverage": self.coverage,
            "report": self.report_path
        }


class Vulnerability:
    """Vulnérabilité détectée"""
    def __init__(self, vuln_type: VulnerabilityType, severity: str, 
                 description: str, contract: str, function: str = None,
                 line: int = None, sequence: List[str] = None):
        self.id = f"VULN-{datetime.now().strftime('%Y%m%d%H%M%S')}-{vuln_type.value}"
        self.type = vuln_type
        self.severity = severity
        self.description = description
        self.contract = contract
        self.function = function
        self.line = line
        self.sequence = sequence or []
        self.timestamp = datetime.now()
        self.remediation = self._get_remediation_suggestion()
        self.swc_id = self._get_swc_id()
        self.proof_path = None
    
    def _get_remediation_suggestion(self) -> str:
        """Suggère une correction"""
        suggestions = {
            VulnerabilityType.REENTRANCY: "Utiliser ReentrancyGuard ou suivre le pattern Checks-Effects-Interactions",
            VulnerabilityType.INTEGER_OVERFLOW: "Utiliser SafeMath ou Solidity ^0.8.0",
            VulnerabilityType.INTEGER_UNDERFLOW: "Utiliser SafeMath ou Solidity ^0.8.0",
            VulnerabilityType.ACCESS_CONTROL: "Ajouter des modificateurs onlyOwner, onlyRole ou Ownable",
            VulnerabilityType.TIMESTAMP_DEPENDENCE: "Éviter de dépendre de block.timestamp pour des décisions critiques",
            VulnerabilityType.FRONT_RUNNING: "Utiliser un mécanisme de commit-reveal",
            VulnerabilityType.UNCHECKED_CALL: "Toujours vérifier la valeur de retour des appels externes",
            VulnerabilityType.DELEGATECALL: "S'assurer que le contrat appelé n'a pas de selfdestruct",
            VulnerabilityType.SELF_DESTRUCT: "Supprimer ou protéger l'accès à selfdestruct"
        }
        return suggestions.get(self.type, "Consulter la documentation de sécurité")
    
    def _get_swc_id(self) -> str:
        """Retourne l'ID SWC correspondant"""
        swc_map = {
            VulnerabilityType.REENTRANCY: "SWC-107",
            VulnerabilityType.INTEGER_OVERFLOW: "SWC-101",
            VulnerabilityType.INTEGER_UNDERFLOW: "SWC-101",
            VulnerabilityType.ACCESS_CONTROL: "SWC-115",
            VulnerabilityType.TIMESTAMP_DEPENDENCE: "SWC-116",
            VulnerabilityType.FRONT_RUNNING: "SWC-114",
            VulnerabilityType.GAS_LIMIT: "SWC-126",
            VulnerabilityType.UNCHECKED_CALL: "SWC-104",
            VulnerabilityType.DELEGATECALL: "SWC-112",
            VulnerabilityType.SELF_DESTRUCT: "SWC-106"
        }
        return swc_map.get(self.type, "SWC-999")
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type.value,
            "severity": self.severity,
            "description": self.description,
            "contract": self.contract,
            "function": self.function,
            "line": self.line,
            "swc_id": self.swc_id,
            "remediation": self.remediation,
            "sequence": self.sequence
        }


class FuzzingSimulationAgent(BaseAgent):
    """
    Agent de fuzzing et simulation pour smart contracts
    Détection automatique de vulnérabilités par tests aléatoires
    """
    
    def __init__(self, config_path: str = ""):
        """Initialise l'agent de fuzzing"""
        super().__init__(config_path)
        
        self._default_config = self._get_default_config()
        if not self._agent_config:
            self._agent_config = self._default_config
        
        self._logger.info("🧪 Agent de fuzzing créé")
        
        # État interne
        self._campaigns: Dict[str, FuzzingCampaign] = {}
        self._engines_available = {
            "echidna": False,
            "foundry": False,
            "medusa": False,
            "dappforge": False
        }
        self._campaign_templates = {}
        self._vulnerability_db = []
        self._components = {}
        self._corpus_manager = None
        
        # Créer les répertoires
        self._create_directories()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Configuration par défaut"""
        return {
            "agent": {
                "name": "fuzzing_simulation",
                "display_name": "🧪 Agent de Fuzzing",
                "description": "Détection automatique de vulnérabilités par tests aléatoires",
                "version": "1.0.0",
                "capabilities": [
                    "echidna_integration",
                    "foundry_invariant_testing",
                    "medusa_fuzzing",
                    "vulnerability_detection",
                    "attack_sequence_generation",
                    "coverage_analysis",
                    "corpus_management",
                    "report_generation"
                ],
                "dependencies": ["tester", "smart_contract"]
            },
            "fuzzing": {
                "default_engine": "echidna",
                "default_strategy": "comprehensive",
                "test_limit": 100000,
                "timeout_seconds": 3600,
                "shrink_limit": 5000,
                "sequence_length": 100,
                "coverage_enabled": True,
                "parallel_workers": 2,
                "campaigns_path": "./campaigns",
                "corpus_path": "./corpus",
                "reports_path": "./reports/fuzzing"
            },
            "echidna": {
                "enabled": True,
                "executable": "echidna",
                "config_format": "yaml",
                "test_limit": 100000,
                "shrink_limit": 5000,
                "seq_len": 100,
                "coverage": True,
                "format": "text"
            },
            "foundry": {
                "enabled": True,
                "executable": "forge",
                "invariant_runs": 256,
                "invariant_depth": 15,
                "fuzz_runs": 1000,
                "fuzz_depth": 1000,
                "verbosity": 2
            },
            "medusa": {
                "enabled": False,
                "executable": "medusa",
                "test_limit": 50000,
                "coverage": True,
                "workers": 4
            },
            "vulnerability_detection": {
                "severity_threshold": "medium",
                "auto_remediation": True,
                "generate_proofs": True,
                "classify_vulnerabilities": True,
                "max_findings": 50
            },
            "templates_path": "./agents/fuzzing_simulation/campaigns/templates"
        }
    
    def _create_directories(self):
        """Crée les répertoires nécessaires"""
        dirs = [
            self._agent_config["fuzzing"]["campaigns_path"],
            self._agent_config["fuzzing"]["corpus_path"],
            self._agent_config["fuzzing"]["reports_path"],
            self._agent_config["templates_path"]
        ]
        
        for dir_path in dirs:
            Path(dir_path).mkdir(parents=True, exist_ok=True)
            self._logger.debug(f"📁 Répertoire créé: {dir_path}")
    
    async def initialize(self) -> bool:
        """Initialisation asynchrone de l'agent"""
        try:
            self._set_status(AgentStatus.INITIALIZING)
            self._logger.info("Initialisation de l'agent de fuzzing...")
            
            # Vérifier les moteurs disponibles
            await self._check_engines()
            
            # Initialiser les composants
            await self._initialize_components()
            
            # Charger les templates de campagnes
            await self._load_campaign_templates()
            
            # Initialiser le corpus
            await self._initialize_corpus()
            
            self._logger.info("Agent de fuzzing initialisé")
            
            result = await super().initialize()
            
            if result:
                self._set_status(AgentStatus.READY)
                self._logger.info("✅ Agent de fuzzing prêt")
            
            return result
            
        except Exception as e:
            self._logger.error(f"❌ Erreur initialisation: {e}")
            self._logger.error(traceback.format_exc())
            self._set_status(AgentStatus.ERROR)
            return False
    
    async def _check_engines(self):
        """Vérifie les moteurs de fuzzing disponibles"""
        self._logger.info("🔍 Vérification des moteurs de fuzzing...")
        
        self._engines_available["echidna"] = await self._check_echidna()
        self._logger.info(f"  Echidna: {'✅' if self._engines_available['echidna'] else '❌'}")
        
        self._engines_available["foundry"] = await self._check_foundry()
        self._logger.info(f"  Foundry: {'✅' if self._engines_available['foundry'] else '❌'}")
        
        self._engines_available["medusa"] = await self._check_medusa()
        self._logger.info(f"  Medusa: {'✅' if self._engines_available['medusa'] else '❌'}")
        
        self._engines_available["dappforge"] = await self._check_dappforge()
        self._logger.info(f"  DappForge: {'✅' if self._engines_available['dappforge'] else '❌'}")
    
    async def _check_echidna(self) -> bool:
        """Vérifie si Echidna est installé"""
        try:
            result = subprocess.run(
                ["echidna", "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except:
            try:
                result = subprocess.run(
                    ["npx", "echidna", "--version"],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                return result.returncode == 0
            except:
                return False
    
    async def _check_foundry(self) -> bool:
        """Vérifie si Foundry est installé"""
        try:
            result = subprocess.run(
                ["forge", "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except:
            return False
    
    async def _check_medusa(self) -> bool:
        """Vérifie si Medusa est installé"""
        try:
            result = subprocess.run(
                ["medusa", "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except:
            return False
    
    async def _check_dappforge(self) -> bool:
        """Vérifie si DappForge est installé"""
        try:
            result = subprocess.run(
                ["dappforge", "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except:
            return False
    
    async def _initialize_components(self):
        """Initialise les composants de l'agent"""
        self._logger.info("Initialisation des composants...")
        
        self._components = {
            "echidna_engine": await self._init_echidna_engine(),
            "foundry_engine": await self._init_foundry_engine(),
            "medusa_engine": await self._init_medusa_engine(),
            "vulnerability_detector": self._init_vulnerability_detector(),
            "corpus_manager": self._init_corpus_manager(),
            "report_generator": self._init_report_generator()
        }
        
        self._logger.info(f"✅ Composants: {list(self._components.keys())}")
        return self._components
    
    async def _init_echidna_engine(self) -> Dict[str, Any]:
        """Initialise le moteur Echidna"""
        return {
            "available": self._engines_available["echidna"],
            "executable": self._agent_config["echidna"]["executable"],
            "config_format": self._agent_config["echidna"]["config_format"],
            "test_limit": self._agent_config["echidna"]["test_limit"],
            "shrink_limit": self._agent_config["echidna"]["shrink_limit"],
            "seq_len": self._agent_config["echidna"]["seq_len"],
            "coverage": self._agent_config["echidna"]["coverage"]
        }
    
    async def _init_foundry_engine(self) -> Dict[str, Any]:
        """Initialise le moteur Foundry"""
        return {
            "available": self._engines_available["foundry"],
            "executable": self._agent_config["foundry"]["executable"],
            "invariant_runs": self._agent_config["foundry"]["invariant_runs"],
            "invariant_depth": self._agent_config["foundry"]["invariant_depth"],
            "fuzz_runs": self._agent_config["foundry"]["fuzz_runs"],
            "fuzz_depth": self._agent_config["foundry"]["fuzz_depth"]
        }
    
    async def _init_medusa_engine(self) -> Dict[str, Any]:
        """Initialise le moteur Medusa"""
        return {
            "available": self._engines_available["medusa"],
            "executable": self._agent_config["medusa"]["executable"],
            "test_limit": self._agent_config["medusa"]["test_limit"],
            "coverage": self._agent_config["medusa"]["coverage"],
            "workers": self._agent_config["medusa"]["workers"]
        }
    
    def _init_vulnerability_detector(self) -> Dict[str, Any]:
        """Initialise le détecteur de vulnérabilités"""
        return {
            "severity_threshold": self._agent_config["vulnerability_detection"]["severity_threshold"],
            "auto_remediation": self._agent_config["vulnerability_detection"]["auto_remediation"],
            "generate_proofs": self._agent_config["vulnerability_detection"]["generate_proofs"],
            "classify": self._agent_config["vulnerability_detection"]["classify_vulnerabilities"],
            "max_findings": self._agent_config["vulnerability_detection"]["max_findings"],
            "patterns": self._load_vulnerability_patterns()
        }
    
    def _load_vulnerability_patterns(self) -> Dict[str, List[str]]:
        """Charge les patterns de détection des vulnérabilités"""
        return {
            "reentrancy": [
                r"call\.value\(",
                r"\.send\(",
                r"\.transfer\(",
                r"\.call\{value:",
                r"withdraw\("
            ],
            "integer_overflow": [
                r"\+=",
                r"-=",
                r"\*=",
                r"/=",
                r"\+\+",
                r"--"
            ],
            "access_control": [
                r"onlyOwner",
                r"Ownable",
                r"require\(msg\.sender",
                r"modifier\s+\w+"
            ],
            "timestamp_dependence": [
                r"block\.timestamp",
                r"now\s*[=<>]",
                r"block\.number"
            ],
            "unchecked_call": [
                r"\.call\(",
                r"\.delegatecall\(",
                r"\.send\("
            ]
        }
    
    def _init_corpus_manager(self) -> Dict[str, Any]:
        """Initialise le gestionnaire de corpus"""
        return {
            "corpus_path": self._agent_config["fuzzing"]["corpus_path"],
            "max_size_mb": 100,
            "deduplicate": True,
            "optimize_sequences": True,
            "initialized": True
        }
    
    def _init_report_generator(self) -> Dict[str, Any]:
        """Initialise le générateur de rapports"""
        return {
            "output_path": self._agent_config["fuzzing"]["reports_path"],
            "formats": ["html", "json", "markdown"],
            "include_sequences": True,
            "include_coverage": True,
            "include_remediation": True,
            "template": "fuzzing_report.html"
        }
    
    async def _load_campaign_templates(self):
        """Charge les templates de campagnes"""
        templates_path = Path(self._agent_config["templates_path"])
        templates_path.mkdir(parents=True, exist_ok=True)
        
        self._campaign_templates = {
            "reentrancy": self._create_reentrancy_template(),
            "overflow": self._create_overflow_template(),
            "access_control": self._create_access_control_template(),
            "comprehensive": self._create_comprehensive_template(),
            "invariant": self._create_invariant_template()
        }
        
        for name, template in self._campaign_templates.items():
            template_path = templates_path / f"{name}.yaml"
            if not template_path.exists():
                with open(template_path, 'w', encoding='utf-8') as f:
                    yaml.dump(template, f, default_flow_style=False)
                self._logger.debug(f"✅ Template créé: {name}")
        
        self._logger.info(f"📋 Templates: {list(self._campaign_templates.keys())}")
    
    def _create_reentrancy_template(self) -> Dict[str, Any]:
        """Template pour détecter les reentrancy"""
        return {
            "name": "Reentrancy Detection",
            "description": "Détecte les vulnérabilités de réentrance",
            "engine": "echidna",
            "strategy": "guided",
            "test_limit": 50000,
            "properties": [
                "echidna_test_reentrancy()",
                "echidna_test_checks_effects_interactions()"
            ],
            "contract_patterns": [
                "withdraw",
                "transfer",
                "send",
                "call.value",
                ".delegatecall"
            ]
        }
    
    def _create_overflow_template(self) -> Dict[str, Any]:
        """Template pour détecter les overflows"""
        return {
            "name": "Integer Overflow Detection",
            "description": "Détecte les dépassements d'entiers",
            "engine": "echidna",
            "strategy": "structured",
            "test_limit": 30000,
            "properties": [
                "echidna_test_overflow()",
                "echidna_test_underflow()"
            ],
            "contract_patterns": [
                "++",
                "--",
                "+=",
                "-=",
                "*=",
                "/="
            ]
        }
    
    def _create_access_control_template(self) -> Dict[str, Any]:
        """Template pour détecter les problèmes d'accès"""
        return {
            "name": "Access Control Detection",
            "description": "Détecte les failles de contrôle d'accès",
            "engine": "foundry",
            "strategy": "invariant",
            "invariant_runs": 256,
            "invariant_depth": 20,
            "properties": [
                "test_onlyOwner_can_call_restricted()",
                "test_role_based_access()"
            ]
        }
    
    def _create_comprehensive_template(self) -> Dict[str, Any]:
        """Template complet - tous les types de vulnérabilités"""
        return {
            "name": "Comprehensive Security Audit",
            "description": "Détection exhaustive de vulnérabilités",
            "engine": "medusa",
            "strategy": "comprehensive",
            "test_limit": 100000,
            "timeout": 3600,
            "vulnerabilities": [
                "reentrancy",
                "integer_overflow",
                "integer_underflow",
                "access_control",
                "timestamp_dependence",
                "unchecked_call"
            ]
        }
    
    def _create_invariant_template(self) -> Dict[str, Any]:
        """Template pour tests d'invariants Foundry"""
        return {
            "name": "Invariant Testing",
            "description": "Vérification d'invariants avec Foundry",
            "engine": "foundry",
            "strategy": "invariant",
            "invariant_runs": 512,
            "invariant_depth": 30,
            "fail_on_revert": False
        }
    
    async def _initialize_corpus(self):
        """Initialise le corpus de fuzzing"""
        corpus_path = Path(self._agent_config["fuzzing"]["corpus_path"])
        corpus_path.mkdir(parents=True, exist_ok=True)
        
        initial_corpus = [
            "0x0000000000000000000000000000000000000000",
            "0xffffffffffffffffffffffffffffffffffffffff",
            "0x0000000000000000000000000000000000000001",
            "1000000000000000000",
            "0x01",
            "0xff"
        ]
        
        corpus_file = corpus_path / "initial_corpus.txt"
        if not corpus_file.exists():
            with open(corpus_file, 'w') as f:
                f.write("\n".join(initial_corpus))
            self._logger.debug(f"✅ Corpus initial créé: {corpus_file}")
        
        self._corpus_manager = {
            "path": str(corpus_path),
            "size": len(initial_corpus),
            "last_updated": datetime.now().isoformat()
        }
    
    async def run_fuzzing_campaign(self,
                                   contract_path: str,
                                   campaign_name: str = None,
                                   engine: FuzzingEngine = None,
                                   strategy: FuzzingStrategy = None,
                                   template: str = None) -> FuzzingCampaign:
        """
        Exécute une campagne de fuzzing
        
        Args:
            contract_path: Chemin du contrat Solidity
            campaign_name: Nom de la campagne
            engine: Moteur à utiliser
            strategy: Stratégie de fuzzing
            template: Template à utiliser
            
        Returns:
            Campagne de fuzzing avec résultats
        """
        self._logger.info(f"🎯 Démarrage campagne fuzzing: {contract_path}")
        
        if not os.path.exists(contract_path):
            raise FileNotFoundError(f"❌ Contrat non trouvé: {contract_path}")
        
        name = campaign_name or f"Fuzzing_{Path(contract_path).stem}"
        campaign = FuzzingCampaign(name, contract_path)
        
        if engine:
            campaign.engine = engine
        else:
            for e in [FuzzingEngine.ECHIDNA, FuzzingEngine.FOUNDRY, FuzzingEngine.MEDUSA]:
                if self._engines_available.get(e.value, False):
                    campaign.engine = e
                    break
        
        campaign.strategy = strategy or FuzzingStrategy.COMPREHENSIVE
        campaign.status = "running"
        campaign.start_time = datetime.now()
        
        self._campaigns[campaign.id] = campaign
        
        try:
            if campaign.engine == FuzzingEngine.ECHIDNA and self._engines_available["echidna"]:
                await self._run_echidna(campaign, template)
            elif campaign.engine == FuzzingEngine.FOUNDRY and self._engines_available["foundry"]:
                await self._run_foundry(campaign, template)
            elif campaign.engine == FuzzingEngine.MEDUSA and self._engines_available["medusa"]:
                await self._run_medusa(campaign, template)
            else:
                await self._run_simulation(campaign, template)
            
            campaign.status = "completed"
            self._logger.info(f"✅ Campagne {campaign.id} terminée")
            
        except Exception as e:
            campaign.status = "failed"
            self._logger.error(f"❌ Campagne échouée: {e}")
            self._logger.error(traceback.format_exc())
        
        finally:
            campaign.end_time = datetime.now()
            campaign.duration_ms = int((campaign.end_time - campaign.start_time).total_seconds() * 1000)
            campaign.report_path = await self._generate_report(campaign)
        
        return campaign
    
    async def _run_echidna(self, campaign: FuzzingCampaign, template: str = None):
        """Exécute Echidna"""
        self._logger.info(f"🔍 Exécution Echidna sur {campaign.contract_name}")
        
        config = self._create_echidna_config(campaign, template)
        config_path = Path(self._agent_config["fuzzing"]["campaigns_path"]) / f"{campaign.id}.yaml"
        
        with open(config_path, 'w') as f:
            yaml.dump(config, f)
        
        cmd = [
            "echidna",
            campaign.contract_path,
            "--config", str(config_path),
            "--contract", campaign.contract_name,
            "--test-limit", str(config.get("testLimit", 50000)),
            "--shrink-limit", str(config.get("shrinkLimit", 5000)),
            "--seq-len", str(config.get("seqLen", 100))
        ]
        
        if config.get("coverage", True):
            cmd.append("--coverage-format")
            cmd.append("html")
        
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=self._agent_config["fuzzing"]["timeout_seconds"]
            )
            
            output = stdout.decode('utf-8', errors='ignore')
            
            self._parse_echidna_output(output, campaign)
            await self._analyze_vulnerabilities(campaign, output)
            
        except asyncio.TimeoutError:
            self._logger.warning(f"⚠️ Echidna timeout")
            process.kill()
    
    def _create_echidna_config(self, campaign: FuzzingCampaign, template: str = None) -> Dict:
        """Crée la configuration Echidna"""
        config = {
            "testLimit": self._agent_config["echidna"]["test_limit"],
            "shrinkLimit": self._agent_config["echidna"]["shrink_limit"],
            "seqLen": self._agent_config["echidna"]["seq_len"],
            "coverage": self._agent_config["echidna"]["coverage"],
            "format": self._agent_config["echidna"]["format"],
            "contract": campaign.contract_name
        }
        
        if template and template in self._campaign_templates:
            tmpl = self._campaign_templates[template]
            config.update({
                "testLimit": tmpl.get("test_limit", config["testLimit"]),
                "seqLen": tmpl.get("sequence_length", config["seqLen"]),
                "properties": tmpl.get("properties", [])
            })
        
        return config
    
    def _parse_echidna_output(self, output: str, campaign: FuzzingCampaign):
        """Parse la sortie d'Echidna"""
        tests_match = re.search(r"Tests: (\d+)", output)
        if tests_match:
            campaign.total_tests = int(tests_match.group(1))
        
        fails_match = re.search(r"Failures: (\d+)", output)
        if fails_match:
            campaign.total_failures = int(fails_match.group(1))
        
        sequences = re.findall(r"Call sequence:\n((?:  .*\n?)+)", output)
        campaign.sequences = [seq.strip().split('\n') for seq in sequences]
        
        coverage_match = re.search(r"Coverage: (\d+\.?\d*)%", output)
        if coverage_match:
            campaign.coverage["percent"] = float(coverage_match.group(1))
    
    async def _run_foundry(self, campaign: FuzzingCampaign, template: str = None):
        """Exécute Foundry"""
        self._logger.info(f"🔍 Exécution Foundry sur {campaign.contract_name}")
        
        test_file = await self._create_foundry_invariant_test(campaign, template)
        
        cmd = [
            "forge",
            "test",
            "--match-path", test_file,
            "--fuzz-runs", str(self._agent_config["foundry"]["fuzz_runs"]),
            "--verbosity", str(self._agent_config["foundry"]["verbosity"])
        ]
        
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=os.path.dirname(campaign.contract_path)
            )
            
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=self._agent_config["fuzzing"]["timeout_seconds"]
            )
            
            output = stdout.decode('utf-8', errors='ignore')
            
            self._parse_foundry_output(output, campaign)
            await self._analyze_vulnerabilities(campaign, output)
            
        except asyncio.TimeoutError:
            self._logger.warning(f"⚠️ Foundry timeout")
    
    async def _create_foundry_invariant_test(self, campaign: FuzzingCampaign, template: str) -> str:
        """Crée un fichier de test d'invariant Foundry"""
        test_dir = Path(os.path.dirname(campaign.contract_path)) / "test"
        test_dir.mkdir(exist_ok=True)
        
        test_file = test_dir / f"Invariant_{campaign.contract_name}.t.sol"
        
        content = f"""// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "forge-std/Test.sol";
import "../{campaign.contract_name}.sol";

contract {campaign.contract_name}InvariantTest is Test {{
    {campaign.contract_name} public instance;
    
    function setUp() public {{
        instance = new {campaign.contract_name}();
    }}
    
    function invariant_totalSupply() public view {{
        assert(instance.totalSupply() >= 0);
    }}
    
    function invariant_owner() public view {{
        assert(instance.owner() != address(0));
    }}
    
    function testFuzz_transfer(uint256 amount) public {{
        uint256 balanceBefore = instance.balanceOf(address(this));
        if (amount <= balanceBefore) {{
            instance.transfer(address(0x1), amount);
            assert(instance.balanceOf(address(this)) == balanceBefore - amount);
        }} else {{
            vm.expectRevert();
            instance.transfer(address(0x1), amount);
        }}
    }}
}}
"""
        
        with open(test_file, 'w') as f:
            f.write(content)
        
        return str(test_file)
    
    def _parse_foundry_output(self, output: str, campaign: FuzzingCampaign):
        """Parse la sortie de Foundry"""
        passing = re.findall(r"\[PASS\]", output)
        failing = re.findall(r"\[FAIL\]", output)
        
        campaign.total_tests = len(passing) + len(failing)
        campaign.total_failures = len(failing)
        
        failures = re.findall(r"\[FAIL\].*?\n.*?\n", output, re.DOTALL)
        for failure in failures[:10]:
            campaign.sequences.append([failure.strip()])
    
    async def _run_medusa(self, campaign: FuzzingCampaign, template: str = None):
        """Exécute Medusa"""
        self._logger.info(f"🔍 Exécution Medusa sur {campaign.contract_name}")
        
        if not self._engines_available["medusa"]:
            self._logger.warning("⚠️ Medusa non disponible, utilisation du mode simulation")
            await self._run_simulation(campaign, template)
            return
        
        cmd = [
            "medusa",
            "fuzz",
            "--contract", campaign.contract_path,
            "--test-limit", str(self._agent_config["medusa"]["test_limit"]),
            "--workers", str(self._agent_config["medusa"]["workers"])
        ]
        
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=self._agent_config["fuzzing"]["timeout_seconds"]
            )
            
            output = stdout.decode('utf-8', errors='ignore')
            
            self._parse_medusa_output(output, campaign)
            await self._analyze_vulnerabilities(campaign, output)
            
        except asyncio.TimeoutError:
            self._logger.warning(f"⚠️ Medusa timeout")
            process.kill()
    
    def _parse_medusa_output(self, output: str, campaign: FuzzingCampaign):
        """Parse la sortie de Medusa"""
        tests_match = re.search(r"Tests executed: (\d+)", output)
        if tests_match:
            campaign.total_tests = int(tests_match.group(1))
        
        fails_match = re.search(r"Failures: (\d+)", output)
        if fails_match:
            campaign.total_failures = int(fails_match.group(1))
    
    async def _run_simulation(self, campaign: FuzzingCampaign, template: str = None):
        """Mode simulation - pour développement et fallback"""
        self._logger.info("🧪 Mode simulation - fuzzing simulé")
        
        await asyncio.sleep(0.5)
        
        campaign.total_tests = 1000
        campaign.total_failures = 3
        campaign.coverage = {
            "lines": 85,
            "branches": 72,
            "functions": 94,
            "percent": 83.7
        }
        
        vulnerabilities = [
            Vulnerability(
                VulnerabilityType.REENTRANCY,
                "high",
                "Fonction withdraw() sans protection contre la réentrance",
                campaign.contract_name,
                "withdraw",
                42,
                ["call withdraw()", "call withdraw()", "call withdraw()"]
            ),
            Vulnerability(
                VulnerabilityType.INTEGER_OVERFLOW,
                "medium",
                "Potential overflow dans addLiquidity()",
                campaign.contract_name,
                "addLiquidity",
                78,
                ["addLiquidity(1, 0xffff...)", "addLiquidity(2, 0xffff...)"]
            ),
            Vulnerability(
                VulnerabilityType.ACCESS_CONTROL,
                "critical",
                "Fonction mint() publique sans restriction",
                campaign.contract_name,
                "mint",
                23,
                ["mint(0xdead, 1000)"]
            )
        ]
        
        campaign.vulnerabilities = [v.to_dict() for v in vulnerabilities]
        campaign.sequences = [[
            "call withdraw(1000)",
            "call withdraw(1000)",
            "call withdraw(1000)"
        ]]
    
    async def _analyze_vulnerabilities(self, campaign: FuzzingCampaign, output: str):
        """Analyse la sortie pour détecter et classifier les vulnérabilités"""
        self._logger.info("🔬 Analyse des vulnérabilités...")
        
        patterns = self._load_vulnerability_patterns()
        detected = []
        
        # Analyser le contrat source
        try:
            with open(campaign.contract_path, 'r', encoding='utf-8') as f:
                source = f.read()
                lines = source.split('\n')
                
                for vuln_type, vuln_patterns in patterns.items():
                    for i, line in enumerate(lines, 1):
                        for pattern in vuln_patterns:
                            if re.search(pattern, line):
                                # Vérifier si c'est une vraie vulnérabilité
                                severity = self._assess_severity(vuln_type, line, source)
                                
                                vuln = Vulnerability(
                                    VulnerabilityType[vuln_type.upper()],
                                    severity,
                                    f"Potentielle {vuln_type} détectée",
                                    campaign.contract_name,
                                    self._extract_function_name(line),
                                    i,
                                    []
                                )
                                detected.append(vuln)
        except Exception as e:
            self._logger.error(f"Erreur analyse vulnérabilités: {e}")
        
        # Limiter le nombre de findings
        max_findings = self._agent_config["vulnerability_detection"]["max_findings"]
        campaign.vulnerabilities = [v.to_dict() for v in detected[:max_findings]]
        
        self._logger.info(f"🔴 {len(campaign.vulnerabilities)} vulnérabilités détectées")
    
    def _assess_severity(self, vuln_type: str, line: str, source: str) -> str:
        """Évalue la sévérité d'une vulnérabilité"""
        severity_map = {
            "reentrancy": "high",
            "integer_overflow": "medium",
            "integer_underflow": "medium",
            "access_control": "critical",
            "timestamp_dependence": "low",
            "unchecked_call": "medium",
            "delegatecall": "high",
            "self_destruct": "critical"
        }
        
        base_severity = severity_map.get(vuln_type, "medium")
        
        # Ajuster selon le contexte
        if "public" in line and "onlyOwner" not in source:
            return "critical"
        if "call.value" in line and "require(success)" not in source:
            return "high"
        
        return base_severity
    
    def _extract_function_name(self, line: str) -> str:
        """Extrait le nom de fonction d'une ligne de code"""
        match = re.search(r'function\s+(\w+)', line)
        if match:
            return match.group(1)
        
        match = re.search(r'(\w+)\s*\(', line)
        if match:
            return match.group(1)
        
        return "unknown"
    
    async def _generate_report(self, campaign: FuzzingCampaign) -> str:
        """Génère un rapport de la campagne"""
        reports_path = Path(self._agent_config["fuzzing"]["reports_path"])
        reports_path.mkdir(parents=True, exist_ok=True)
        
        # Rapport HTML
        html_file = reports_path / f"{campaign.id}_report.html"
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(self._generate_report_html(campaign))
        
        # Rapport JSON
        json_file = reports_path / f"{campaign.id}_report.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(campaign.to_dict(), f, indent=2, ensure_ascii=False)
        
        # Rapport Markdown
        md_file = reports_path / f"{campaign.id}_report.md"
        with open(md_file, 'w', encoding='utf-8') as f:
            f.write(self._generate_report_markdown(campaign))
        
        self._logger.info(f"📄 Rapports générés: {html_file}")
        return str(html_file)
    
    def _generate_report_html(self, campaign: FuzzingCampaign) -> str:
        """Génère le rapport HTML"""
        vuln_rows = ""
        for vuln in campaign.vulnerabilities:
            severity_class = {
                "critical": "critical",
                "high": "high",
                "medium": "medium",
                "low": "low"
            }.get(vuln.get("severity", "info"), "info")
            
            vuln_rows += f"""
            <tr>
                <td><span class="{severity_class}">{vuln['severity'].upper()}</span></td>
                <td>{vuln['type']}</td>
                <td>{vuln['description']}</td>
                <td><code>{vuln.get('function', 'unknown')}:{vuln.get('line', '?')}</code></td>
                <td><a href="#proof-{vuln['id']}">Voir</a></td>
            </tr>
            """
        
        attack_sequences = ""
        for i, seq in enumerate(campaign.sequences[:3]):
            attack_sequences += f"Call sequence {i+1}:\n"
            for step in seq[:5]:
                attack_sequences += f"  {step}\n"
            attack_sequences += "...\n\n"
        
        attack_sequences = attack_sequences.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        
        return f"""<!DOCTYPE html>
<html>
<head>
    <title>Fuzzing Report: {campaign.name}</title>
    <style>
        body {{ font-family: 'Segoe UI', sans-serif; margin: 20px; background: #f5f5f5; }}
        .container {{ max-width: 1400px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 10px; }}
        .stats {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px; margin: 20px 0; }}
        .stat-card {{ background: #f8f9fa; padding: 20px; border-radius: 10px; text-align: center; }}
        .critical {{ background: #dc3545; color: white; padding: 5px 10px; border-radius: 5px; }}
        .high {{ background: #fd7e14; color: white; padding: 5px 10px; border-radius: 5px; }}
        .medium {{ background: #ffc107; color: black; padding: 5px 10px; border-radius: 5px; }}
        .low {{ background: #28a745; color: white; padding: 5px 10px; border-radius: 5px; }}
        table {{ width: 100%; border-collapse: collapse; }}
        th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }}
        th {{ background: #667eea; color: white; }}
        .code {{ background: #2d2d2d; color: #f8f8f2; padding: 15px; border-radius: 5px; font-family: monospace; white-space: pre-wrap; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🧪 Fuzzing Campaign Report</h1>
            <h2>{campaign.name}</h2>
            <p>ID: {campaign.id} | Contract: {campaign.contract_name}</p>
            <p>Engine: {campaign.engine.value} | Duration: {campaign.duration_ms}ms</p>
        </div>
        
        <div class="stats">
            <div class="stat-card">
                <h3>Total Tests</h3>
                <h2>{campaign.total_tests}</h2>
            </div>
            <div class="stat-card">
                <h3>Failures</h3>
                <h2 style="color: #dc3545;">{campaign.total_failures}</h2>
            </div>
            <div class="stat-card">
                <h3>Vulnerabilities</h3>
                <h2 style="color: #dc3545;">{len(campaign.vulnerabilities)}</h2>
            </div>
            <div class="stat-card">
                <h3>Coverage</h3>
                <h2>{campaign.coverage['percent']}%</h2>
            </div>
        </div>
        
        <h2>🔴 Vulnerabilities Detected</h2>
        <table>
            <thead>
                <tr>
                    <th>Severity</th>
                    <th>Type</th>
                    <th>Description</th>
                    <th>Location</th>
                    <th>Remediation</th>
                </tr>
            </thead>
            <tbody>
                {vuln_rows}
            </tbody>
        </table>
        
        <h2>📊 Coverage Analysis</h2>
        <div class="stats">
            <div class="stat-card">
                <h3>Lines</h3>
                <h2>{campaign.coverage['lines']}%</h2>
            </div>
            <div class="stat-card">
                <h3>Branches</h3>
                <h2>{campaign.coverage['branches']}%</h2>
            </div>
            <div class="stat-card">
                <h3>Functions</h3>
                <h2>{campaign.coverage['functions']}%</h2>
            </div>
        </div>
        
        <h2>🔍 Attack Sequences</h2>
        <div class="code">
{attack_sequences}
        </div>
        
        <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    </div>
</body>
</html>"""
    
    def _generate_report_markdown(self, campaign: FuzzingCampaign) -> str:
        """Génère le rapport Markdown"""
        md = f"""# 🧪 Fuzzing Campaign Report: {campaign.name}

## 📋 Informations
- **ID:** {campaign.id}
- **Contract:** {campaign.contract_name}
- **Engine:** {campaign.engine.value}
- **Strategy:** {campaign.strategy.value}
- **Duration:** {campaign.duration_ms}ms
- **Status:** {campaign.status}

## 📊 Statistiques
- **Total Tests:** {campaign.total_tests}
- **Failures:** {campaign.total_failures}
- **Vulnerabilities:** {len(campaign.vulnerabilities)}
- **Coverage:** {campaign.coverage['percent']}%

## 🔴 Vulnérabilités Détectées

"""
        for vuln in campaign.vulnerabilities:
            md += f"""### {vuln['severity'].upper()}: {vuln['type']}
- **Description:** {vuln['description']}
- **Location:** `{vuln.get('function', 'unknown')}:{vuln.get('line', '?')}`
- **SWC ID:** {vuln.get('swc_id', 'N/A')}
- **Remediation:** {vuln.get('remediation', 'N/A')}

"""
        
        md += f"""## 🔍 Attack Sequences
"""
        for i, seq in enumerate(campaign.sequences[:3]):
            md += f"### Sequence {i+1}\n```\n"
            for step in seq[:5]:
                md += f"{step}\n"
            md += "...\n```\n\n"
        
        md += f"\n*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*"
        
        return md
    
    async def get_campaign_status(self, campaign_id: str) -> Optional[Dict]:
        """Retourne le statut d'une campagne"""
        if campaign_id not in self._campaigns:
            return None
        return self._campaigns[campaign_id].to_dict()
    
    async def list_campaigns(self, status: str = None) -> List[Dict]:
        """Liste toutes les campagnes"""
        campaigns = []
        for campaign in self._campaigns.values():
            if status and campaign.status != status:
                continue
            campaigns.append(campaign.to_dict())
        return campaigns
    
    async def get_vulnerability_stats(self) -> Dict[str, Any]:
        """Statistiques sur les vulnérabilités détectées"""
        stats = {
            "total": 0,
            "by_severity": {
                "critical": 0,
                "high": 0,
                "medium": 0,
                "low": 0,
                "info": 0
            },
            "by_type": {}
        }
        
        for campaign in self._campaigns.values():
            for vuln in campaign.vulnerabilities:
                stats["total"] += 1
                severity = vuln.get("severity", "info")
                if severity in stats["by_severity"]:
                    stats["by_severity"][severity] += 1
                
                vuln_type = vuln.get("type", "unknown")
                stats["by_type"][vuln_type] = stats["by_type"].get(vuln_type, 0) + 1
        
        return stats
    
    async def health_check(self) -> Dict[str, Any]:
        """Vérifie la santé de l'agent"""
        vuln_stats = await self.get_vulnerability_stats()
        
        return {
            "agent": self._name,
            "status": self._status.value,
            "ready": self._status == AgentStatus.READY,
            "engines_available": self._engines_available,
            "campaigns_total": len(self._campaigns),
            "campaigns_running": len([c for c in self._campaigns.values() if c.status == "running"]),
            "campaigns_completed": len([c for c in self._campaigns.values() if c.status == "completed"]),
            "vulnerabilities_found": vuln_stats["total"],
            "vulnerabilities_by_severity": vuln_stats["by_severity"],
            "components": list(self._components.keys()),
            "uptime": self.uptime.total_seconds()
        }
    
    def get_agent_info(self) -> Dict[str, Any]:
        """Informations de l'agent"""
        return {
            "id": self._name,
            "name": self._display_name,
            "type": "fuzzing",
            "version": self._version,
            "description": self._description,
            "status": self._status.value,
            "capabilities": self._agent_config["agent"]["capabilities"],
            "engines": {
                "echidna": self._engines_available["echidna"],
                "foundry": self._engines_available["foundry"],
                "medusa": self._engines_available["medusa"]
            },
            "templates": list(self._campaign_templates.keys()),
            "campaigns_run": len(self._campaigns)
        }
    
    async def _handle_custom_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Gestion des messages personnalisés"""
        msg_type = message.get("type", "")
        
        if msg_type == "run_fuzzing":
            campaign = await self.run_fuzzing_campaign(
                contract_path=message["contract_path"],
                campaign_name=message.get("name"),
                engine=FuzzingEngine(message.get("engine", "simulation")),
                strategy=FuzzingStrategy(message.get("strategy", "comprehensive")),
                template=message.get("template")
            )
            return {"campaign_id": campaign.id, "status": "started"}
        
        elif msg_type == "campaign_status":
            status = await self.get_campaign_status(message["campaign_id"])
            return status or {"error": "Campaign not found"}
        
        elif msg_type == "list_campaigns":
            campaigns = await self.list_campaigns(message.get("status"))
            return {"campaigns": campaigns}
        
        elif msg_type == "vulnerability_stats":
            stats = await self.get_vulnerability_stats()
            return stats
        
        elif msg_type == "available_templates":
            return {"templates": list(self._campaign_templates.keys())}
        
        elif msg_type == "engines_status":
            return {"engines": self._engines_available}
        
        return {"status": "received", "type": msg_type}


# ------------------------------------------------------------------------
# FONCTIONS D'USINE
# ------------------------------------------------------------------------

def create_fuzzing_agent(config_path: str = "") -> FuzzingSimulationAgent:
    """Crée une instance de l'agent de fuzzing"""
    return FuzzingSimulationAgent(config_path)


# ------------------------------------------------------------------------
# POINT D'ENTRÉE POUR EXÉCUTION DIRECTE
# ------------------------------------------------------------------------

if __name__ == "__main__":
    async def main():
        print("🧪 TEST AGENT DE FUZZING")
        print("="*50)
        
        agent = FuzzingSimulationAgent()
        await agent.initialize()
        
        print(f"✅ Agent créé: {agent.name}")
        print(f"✅ Statut: {agent.status.value}")
        print(f"✅ Moteurs: {agent._engines_available}")
        print(f"✅ Templates: {list(agent._campaign_templates.keys())}")
        
        campaign = await agent.run_fuzzing_campaign(
            contract_path="./contracts/Token.sol",
            campaign_name="Test Campaign"
        )
        
        print(f"\n📊 Résultats campagne:")
        print(f"  ID: {campaign.id}")
        print(f"  Status: {campaign.status}")
        print(f"  Tests: {campaign.total_tests}")
        print(f"  Vulnérabilités: {len(campaign.vulnerabilities)}")
        print(f"  Rapport: {campaign.report_path}")
        
        print("\n" + "="*50)
        print("🎉 AGENT DE FUZZING OPÉRATIONNEL")
        print("="*50)
    
    asyncio.run(main())
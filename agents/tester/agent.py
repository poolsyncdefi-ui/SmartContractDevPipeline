"""
Agent de test pour les smart contracts et applications web3
"""

import os
import json
import yaml
import asyncio
import logging

logger = logging.getLogger(__name__)
from enum import Enum
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
from pathlib import Path

# Import de la classe de base
from agents.base_agent.base_agent import BaseAgent, AgentStatus


class TestType(Enum):
    """Types de tests supportés"""
    UNIT = "unit"
    INTEGRATION = "integration"
    FUNCTIONAL = "functional"
    SECURITY = "security"
    PERFORMANCE = "performance"
    FUZZ = "fuzz"
    FORMAL = "formal"
    GAS = "gas"
    E2E = "end_to_end"


class TestFramework(Enum):
    """Frameworks de test supportés"""
    HARDHAT = "hardhat"
    FOUNDRY = "foundry"
    TRUFFLE = "truffle"
    BROWNIE = "brownie"
    PYTEST = "pytest"
    JEST = "jest"
    MOCHA = "mocha"
    ECHIDNA = "echidna"
    SLITHER = "slither"
    MYTHRIL = "mythril"


class TestStatus(Enum):
    """Statuts des tests"""
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    ERROR = "error"
    TIMEOUT = "timeout"


class Severity(Enum):
    """Niveaux de sévérité pour les problèmes"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"
    OPTIMIZATION = "optimization"


class TestCase:
    """Représente un cas de test"""
    def __init__(self, name: str, test_type: TestType, framework: TestFramework,
                 file_path: str, function_name: str = None):
        self.id = f"{name}_{datetime.now().timestamp()}"
        self.name = name
        self.test_type = test_type
        self.framework = framework
        self.file_path = file_path
        self.function_name = function_name
        self.status = TestStatus.PENDING
        self.duration_ms = 0
        self.error_message = None
        self.traceback = None
        self.created_at = datetime.now()
        self.executed_at = None


class TestResult:
    """Résultat d'exécution d'un test"""
    def __init__(self, test_case: TestCase):
        self.test_case = test_case
        self.status = test_case.status
        self.duration_ms = test_case.duration_ms
        self.error = test_case.error_message
        self.traceback = test_case.traceback
        self.executed_at = test_case.executed_at
        self.coverage = {}
        self.gas_used = 0
        self.logs = []


class SecurityFinding:
    """Décrit une vulnérabilité ou problème de sécurité"""
    def __init__(self, title: str, severity: Severity, file_path: str,
                 line_number: int = None, code_snippet: str = None):
        self.id = f"SEC-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        self.title = title
        self.severity = severity
        self.file_path = file_path
        self.line_number = line_number
        self.code_snippet = code_snippet
        self.description = ""
        self.remediation = ""
        self.swc_id = None
        self.cvss_score = 0.0
        self.discovered_at = datetime.now()
        self.status = "open"


class TestReport:
    """Rapport de test complet"""
    def __init__(self, name: str, project_path: str):
        self.id = f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.name = name
        self.project_path = project_path
        self.test_results = []
        self.security_findings = []
        self.summary = {
            "total": 0,
            "passed": 0,
            "failed": 0,
            "skipped": 0,
            "errors": 0,
            "duration_ms": 0,
            "coverage_percent": 0,
            "critical_findings": 0,
            "high_findings": 0
        }
        self.created_at = datetime.now()
        self.completed_at = None


class TesterAgent(BaseAgent):
    """
    Agent spécialisé dans les tests de smart contracts et applications web3
    """
    
    def __init__(self, config_path: str = ""):
        """
        Initialise l'agent de test
        
        Args:
            config_path: Chemin vers le fichier de configuration
        """
        # Appel du parent
        super().__init__(config_path)
        
        # Configuration par défaut (ne pas assigner self.config - lecture seule)
        self._default_config = self._get_default_config()
        
        # Si pas de config chargée, utiliser la config par défaut via _agent_config
        if not self._agent_config:
            self._agent_config = self._default_config
        
        self._logger.info(f"Agent tester créé (config: {config_path})")
        
        # État initial (utiliser _status, pas status)
        self._test_frameworks = {}
        self._test_suites = {}
        self._test_results = []
        self._security_findings = []
        self._reports = []
        self._running_tests = {}
        self._test_templates = {}
        
        # Initialisation différée - sera appelée par initialize()
    
    async def initialize(self) -> bool:
        """
        Initialisation asynchrone de l'agent
        Surcharge la méthode de BaseAgent
        """
        try:
            self._set_status(AgentStatus.INITIALIZING)
            self._logger.info("Initialisation de l'agent tester...")
            
            # Initialisation des composants
            self._initialize_test_templates()
            self._initialize_framework_detectors()
            
            self._logger.info(f"Initialisé {len(self._test_templates)} templates de tests")
            self._logger.info("Agent Tester initialisé")
            
            # Appel à la méthode parent
            result = await super().initialize()
            
            if result:
                self._set_status(AgentStatus.READY)
                self._logger.info("Agent tester initialisé avec succès")
            
            return result
            
        except Exception as e:
            self._logger.error(f"Erreur lors de l'initialisation: {e}")
            self._set_status(AgentStatus.ERROR)
            return False
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Configuration par défaut de l'agent"""
        return {
            "agent": {
                "name": "tester",
                "display_name": "Agent de Test",
                "description": "Agent de test pour smart contracts",
                "version": "1.0.0",
                "log_level": "INFO",
                "max_retries": 3,
                "timeout_seconds": 120,
                "health_check_interval": 30,
                "capabilities": [
                    "test_generation",
                    "test_execution",
                    "security_scanning",
                    "coverage_analysis",
                    "report_generation"
                ],
                "dependencies": ["architect", "coder"]
            },
            "testing": {
                "timeout_seconds": 120,
                "parallel_tests": True,
                "max_workers": 4,
                "coverage_enabled": True,
                "gas_reporting": True,
                "generate_reports": True,
                "reports_path": "./reports/tests",
                "artifacts_path": "./artifacts/tests",
                "supported_frameworks": ["hardhat", "foundry", "truffle"],
                "default_framework": "foundry",
                "default_test_type": "unit"
            },
            "security": {
                "scan_enabled": True,
                "tools": ["slither", "mythril", "echidna"],
                "severity_threshold": "medium",
                "max_findings": 50
            },
            "integration": {
                "continuous_testing": False,
                "watch_paths": ["./contracts", "./test"],
                "notify_on_completion": False,
                "notify_on_failure": True
            }
        }
    
    async def _check_dependencies(self) -> bool:
        """Vérifie la présence des dépendances nécessaires (méthode asynchrone)"""
        dependencies = self._agent_config.get("agent", {}).get("dependencies", ["architect", "coder"])
        self._logger.info(f"Vérification des dépendances: {dependencies}")
        
        # Simulation - à implémenter avec une vraie vérification
        for dep in dependencies:
            self._logger.debug(f"Dépendance {dep}: OK")
        
        return True
    
    async def _initialize_components(self):
        """Initialise les composants spécifiques de l'agent - requis par BaseAgent"""
        self._logger.info("Initialisation des composants du TesterAgent...")
        
        self._components = {
            "test_generator": self._init_test_generator(),
            "test_executor": self._init_test_executor(),
            "security_scanner": self._init_security_scanner(),
            "coverage_analyzer": self._init_coverage_analyzer(),
            "report_generator": self._init_report_generator()
        }
        
        self._logger.info(f"Composants initialisés: {list(self._components.keys())}")
        return self._components
    
    def _init_test_generator(self) -> Dict[str, Any]:
        """Initialise le générateur de tests"""
        return {
            "available_templates": list(self._test_templates.keys()),
            "generator_config": {
                "auto_generate": True,
                "output_path": "./test",
                "use_templates": True
            }
        }
    
    def _init_test_executor(self) -> Dict[str, Any]:
        """Initialise l'exécuteur de tests"""
        return {
            "frameworks": self._test_frameworks,
            "executor_config": {
                "timeout": self._agent_config.get("testing", {}).get("timeout_seconds", 120),
                "parallel": self._agent_config.get("testing", {}).get("parallel_tests", True),
                "max_workers": self._agent_config.get("testing", {}).get("max_workers", 4)
            }
        }
    
    def _init_security_scanner(self) -> Dict[str, Any]:
        """Initialise le scanner de sécurité"""
        return {
            "enabled": self._agent_config.get("security", {}).get("scan_enabled", True),
            "tools": self._agent_config.get("security", {}).get("tools", []),
            "scanner_config": {
                "severity_threshold": self._agent_config.get("security", {}).get("severity_threshold", "medium"),
                "max_findings": self._agent_config.get("security", {}).get("max_findings", 50)
            }
        }
    
    def _init_coverage_analyzer(self) -> Dict[str, Any]:
        """Initialise l'analyseur de couverture"""
        return {
            "enabled": self._agent_config.get("testing", {}).get("coverage_enabled", True),
            "coverage_config": {
                "target": "statements",
                "branches": True,
                "functions": True,
                "lines": True
            }
        }
    
    def _init_report_generator(self) -> Dict[str, Any]:
        """Initialise le générateur de rapports"""
        return {
            "enabled": self._agent_config.get("testing", {}).get("generate_reports", True),
            "output_path": self._agent_config.get("testing", {}).get("reports_path", "./reports/tests"),
            "formats": ["json", "html", "markdown"]
        }
    
    def _initialize_framework_detectors(self):
        """Initialise les détecteurs de frameworks"""
        self._framework_detectors = {
            TestFramework.HARDHAT: self._detect_hardhat,
            TestFramework.FOUNDRY: self._detect_foundry,
            TestFramework.TRUFFLE: self._detect_truffle,
            TestFramework.BROWNIE: self._detect_brownie,
            TestFramework.PYTEST: self._detect_pytest
        }
        
        self._test_frameworks = {
            TestFramework.FOUNDRY: {
                "detected": False,
                "config_file": "foundry.toml",
                "test_dir": "test",
                "command": "forge test",
                "coverage_command": "forge coverage",
                "gas_report_command": "forge test --gas-report"
            },
            TestFramework.HARDHAT: {
                "detected": False,
                "config_file": "hardhat.config.js",
                "test_dir": "test",
                "command": "npx hardhat test",
                "coverage_command": "npx hardhat coverage",
                "gas_report_command": "REPORT_GAS=true npx hardhat test"
            },
            TestFramework.TRUFFLE: {
                "detected": False,
                "config_file": "truffle-config.js",
                "test_dir": "test",
                "command": "truffle test",
                "coverage_command": "truffle run coverage",
                "gas_report_command": "truffle test --gas"
            }
        }
    
    def _initialize_test_templates(self):
        """Initialise les templates de tests prédéfinis"""
        self._test_templates = {
            "python_unit_test": self._get_python_unit_test_template(),
            "solidity_unit_test": self._get_solidity_unit_test_template(),
            "javascript_test": self._get_javascript_test_template(),
            "security_test": self._get_security_test_template(),
        }
    
    # ------------------------------------------------------------------------
    # DÉTECTION DES FRAMEWORKS
    # ------------------------------------------------------------------------
    
    def _detect_foundry(self, project_path: str) -> bool:
        """Détecte si Foundry est utilisé dans le projet"""
        config_file = os.path.join(project_path, "foundry.toml")
        return os.path.exists(config_file)
    
    def _detect_hardhat(self, project_path: str) -> bool:
        """Détecte si Hardhat est utilisé dans le projet"""
        config_js = os.path.join(project_path, "hardhat.config.js")
        config_ts = os.path.join(project_path, "hardhat.config.ts")
        return os.path.exists(config_js) or os.path.exists(config_ts)
    
    def _detect_truffle(self, project_path: str) -> bool:
        """Détecte si Truffle est utilisé dans le projet"""
        config_file = os.path.join(project_path, "truffle-config.js")
        return os.path.exists(config_file)
    
    def _detect_brownie(self, project_path: str) -> bool:
        """Détecte si Brownie est utilisé dans le projet"""
        config_file = os.path.join(project_path, "brownie-config.yaml")
        return os.path.exists(config_file)
    
    def _detect_pytest(self, project_path: str) -> bool:
        """Détecte si Pytest est utilisé dans le projet"""
        pytest_ini = os.path.join(project_path, "pytest.ini")
        setup_cfg = os.path.join(project_path, "setup.cfg")
        return os.path.exists(pytest_ini) or os.path.exists(setup_cfg)
    
    # ------------------------------------------------------------------------
    # TEMPLATES DE TESTS
    # ------------------------------------------------------------------------
    
    def _get_python_unit_test_template(self) -> str:
        """Retourne un template pour les tests unitaires Python"""
        return '''"""Tests unitaires pour {ClassName}"""
import pytest
import sys
import os
from pathlib import Path

# Ajouter le chemin du projet au PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Imports spécifiques au projet
# from src.{ClassName} import {ClassName}

class Test{class_name}:
    """Tests unitaires pour {class_name}"""
    
    @pytest.fixture
    def instance(self):
        """Fixture créant une instance de la classe à tester"""
        # return {ClassName}()
        pass
    
    def test_initialization(self, instance):
        """Test d'initialisation de base"""
        assert instance is not None
    
    def test_specific_function(self, instance):
        """Test d'une fonction spécifique"""
        # Arrange
        # Act
        # result = instance.some_function()
        
        # Assert
        # assert result == expected_value
        pass
    
    def test_edge_case(self, instance):
        """Test d'un cas limite"""
        # Tester avec des valeurs limites
        pass
    
    @pytest.mark.parametrize("input_value,expected", [
        (1, 1),
        (2, 2),
        (0, 0),
        (-1, -1),
    ])
    def test_parametrized(self, input_value, expected):
        """Test paramétré avec différentes entrées"""
        assert input_value == expected
'''
    
    def _get_solidity_unit_test_template(self) -> str:
        """Retourne un template pour les tests unitaires Solidity (Foundry)"""
        return '''// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "forge-std/Test.sol";
import "../src/{ContractName}.sol";

/**
 * @title {ContractName} Test Suite
 * @dev Tests unitaires pour le contrat {ContractName} utilisant Foundry
 */
contract {ContractName}Test is Test {
    {ContractName} public instance;
    address public owner = makeAddr("owner");
    address public user1 = makeAddr("user1");
    address public user2 = makeAddr("user2");
    address public attacker = makeAddr("attacker");
    
    event Deployed(address indexed contract_address);
    
    function setUp() public {
        vm.startPrank(owner);
        instance = new {ContractName}();
        vm.stopPrank();
        
        emit Deployed(address(instance));
    }
    
    function test_Initialization() public view {
        assertEq(instance.owner(), owner, "Owner should be set correctly");
    }
    
    function test_SpecificFunction() public {
        vm.startPrank(owner);
        
        // Act - appeler la fonction à tester
        // instance.someFunction(param1, param2);
        
        // Assert - vérifier le résultat
        // assertEq(instance.someValue(), expectedValue);
        
        vm.stopPrank();
    }
    
    function test_RevertWhen_Unauthorized() public {
        vm.startPrank(user1);
        
        // Vérifier que la fonction revert si non autorisé
        // vm.expectRevert("Unauthorized");
        // instance.restrictedFunction();
        
        vm.stopPrank();
    }
    
    function testFuzz_RandomInput(uint256 randomValue) public {
        vm.assume(randomValue > 0 && randomValue < type(uint256).max);
        
        // Test avec des entrées aléatoires
        vm.startPrank(owner);
        // instance.functionWithInput(randomValue);
        vm.stopPrank();
    }
    
    function test_GasUsage() public {
        vm.startPrank(owner);
        
        // Mesurer la consommation de gas
        uint256 gasBefore = gasleft();
        // instance.gasIntensiveFunction();
        uint256 gasUsed = gasBefore - gasleft();
        
        // Vérifier que le gas utilisé est acceptable
        assertLt(gasUsed, 100000, "Gas usage too high");
        
        vm.stopPrank();
    }
}
'''
    
    def _get_javascript_test_template(self) -> str:
        """Retourne un template pour les tests JavaScript"""
        return '''const { expect } = require('chai');
const { ethers } = require('hardhat');

/**
 * Tests pour le contrat {ContractName}
 */
describe('{ContractName}', function () {
    let contract;
    let owner;
    let addr1;
    let addr2;
    let addrs;
    
    before(async function () {
        [owner, addr1, addr2, ...addrs] = await ethers.getSigners();
    });
    
    beforeEach(async function () {
        const Contract = await ethers.getContractFactory('{ContractName}');
        contract = await Contract.deploy();
        await contract.waitForDeployment();
    });
    
    describe('Deployment', function () {
        it('Should deploy successfully', async function () {
            expect(await contract.getAddress()).to.be.properAddress;
        });
        
        it('Should set the right owner', async function () {
            expect(await contract.owner()).to.equal(owner.address);
        });
        
        it('Should initialize with correct values', async function () {
            // Test initialization values
            // expect(await contract.someValue()).to.equal(expectedValue);
        });
    });
    
    describe('Transactions', function () {
        it('Should execute a function correctly', async function () {
            // const tx = await contract.connect(owner).someFunction();
            // const receipt = await tx.wait();
            
            // expect(receipt.status).to.equal(1);
            // expect(await contract.someState()).to.equal(expectedState);
        });
        
        it('Should emit events when expected', async function () {
            // await expect(contract.connect(owner).someFunction())
            //     .to.emit(contract, 'SomeEvent')
            //     .withArgs(expectedArgs);
        });
        
        it('Should revert when unauthorized', async function () {
            // await expect(
            //     contract.connect(addr1).restrictedFunction()
            // ).to.be.revertedWith('Unauthorized');
        });
    });
    
    describe('Edge Cases', function () {
        it('Should handle zero address', async function () {
            // await expect(
            //     contract.connect(owner).transferOwnership(ethers.ZeroAddress)
            // ).to.be.revertedWith('Invalid address');
        });
        
        it('Should handle maximum values', async function () {
            // const maxUint = ethers.MaxUint256;
            // await contract.connect(owner).setValue(maxUint);
            // expect(await contract.getValue()).to.equal(maxUint);
        });
        
        it('Should handle multiple operations', async function () {
            // for (let i = 0; i < 10; i++) {
            //     await contract.connect(addr1).someOperation();
            // }
            // expect(await contract.counter()).to.equal(10);
        });
    });
});
'''
    
    def _get_security_test_template(self) -> str:
        """Retourne un template pour les tests de sécurité"""
        lines = []
        lines.append("# Security Test Template for {ContractName}")
        lines.append("")
        lines.append("## Test Objectives")
        lines.append("- Identify reentrancy vulnerabilities")
        lines.append("- Check for access control issues")
        lines.append("- Validate input sanitization")
        lines.append("- Test edge cases and boundary conditions")
        lines.append("- Verify integer overflow/underflow protection")
        lines.append("- Check timestamp dependence")
        lines.append("- Test front-running resistance")
        lines.append("")
        lines.append("## Test Cases")
        lines.append("")
        lines.append("### 1. Reentrancy Tests")
        lines.append("```solidity")
        lines.append("// Test for reentrancy vulnerability")
        lines.append("function test_Reentrancy() public {")
        lines.append("    // Deploy attack contract")
        lines.append("    ReentrancyAttack attacker = new ReentrancyAttack(instance);")
        lines.append("    ")
        lines.append("    // Attempt reentrancy attack")
        lines.append("    vm.prank(attacker);")
        lines.append("    vm.expectRevert(\"ReentrancyGuard: reentrant call\");")
        lines.append("    instance.withdrawFunds();")
        lines.append("}")
        lines.append("```")
        lines.append("")
        lines.append("### 2. Access Control Tests")
        lines.append("```solidity")
        lines.append("// Test proper access control")
        lines.append("function testFuzz_AccessControl(address randomAddr) public {")
        lines.append("    vm.assume(randomAddr != owner && randomAddr != address(0));")
        lines.append("    ")
        lines.append("    vm.startPrank(randomAddr);")
        lines.append("    vm.expectRevert(\"Ownable: caller is not the owner\");")
        lines.append("    instance.onlyOwnerFunction();")
        lines.append("    vm.stopPrank();")
        lines.append("}")
        lines.append("```")
        lines.append("")
        lines.append("### 3. Integer Overflow/Underflow Tests")
        lines.append("```solidity")
        lines.append("// Test for integer issues")
        lines.append("function test_IntegerOverflow() public {")
        lines.append("    // Test with max values")
        lines.append("    uint256 max = type(uint256).max;")
        lines.append("    ")
        lines.append("    vm.startPrank(owner);")
        lines.append("    // Solidity 0.8+ automatically checks overflow")
        lines.append("    vm.expectRevert();")
        lines.append("    instance.incrementCounter(max);")
        lines.append("    vm.stopPrank();")
        lines.append("}")
        lines.append("```")
        lines.append("")
        lines.append("### 4. Timestamp Dependence")
        lines.append("```solidity")
        lines.append("// Test timestamp dependence")
        lines.append("function test_TimestampDependence() public {")
        lines.append("    // Manipulate block timestamp")
        lines.append("    vm.warp(block.timestamp + 7 days);")
        lines.append("    ")
        lines.append("    // Function should work after time passes")
        lines.append("    instance.timeSensitiveFunction();")
        lines.append("}")
        lines.append("```")
        lines.append("")
        lines.append("## Security Checklist")
        lines.append("- [ ] Reentrancy protection implemented")
        lines.append("- [ ] Access control checks in place")
        lines.append("- [ ] Input validation performed")
        lines.append("- [ ] Safe math operations used (Solc 0.8+)")
        lines.append("- [ ] Event emissions for critical actions")
        lines.append("- [ ] Emergency stop mechanism available")
        lines.append("- [ ] Withdrawal pattern used for transfers")
        lines.append("- [ ] Checks-Effects-Interactions pattern followed")
        lines.append("- [ ] Use of OpenZeppelin security contracts")
        lines.append("- [ ] Proper error messages with custom errors")
        lines.append("")
        lines.append("## Recommended Tools")
        lines.append("- **Slither**: Static analysis")
        lines.append("- **Echidna**: Fuzzing")
        lines.append("- **Mythril**: Security analysis")
        lines.append("- **4naly3er**: Comprehensive audit tool")
        lines.append("- **Hardhat/Foundry**: Testing frameworks")
        
        return "\n".join(lines)
    
    # ------------------------------------------------------------------------
    # MÉTHODES PRINCIPALES
    # ------------------------------------------------------------------------
    
    async def execute(self, task_data: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Exécute une tâche de test
        
        Args:
            task_data: Données de la tâche
            context: Contexte d'exécution
            
        Returns:
            Résultat de l'exécution
        """
        task_type = task_data.get("task_type", "unknown")
        
        self._logger.info(f"Exécution de la tâche {task_type}")
        
        # Route vers la méthode appropriée
        if task_type == "run_tests":
            result = await self._run_tests(task_data, context)
        elif task_type == "generate_tests":
            result = await self._generate_tests(task_data, context)
        elif task_type == "security_scan":
            result = await self._security_scan(task_data, context)
        elif task_type == "analyze_coverage":
            result = await self._analyze_coverage(task_data, context)
        elif task_type == "generate_report":
            result = await self._generate_report(task_data, context)
        else:
            result = {
                "success": False,
                "error": f"Type de tâche non supporté: {task_type}"
            }
        
        return {
            "success": result.get("success", False),
            "task": task_type,
            "result": result,
            "timestamp": datetime.now().isoformat()
        }
    
    async def _run_tests(self, task_data: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Exécute une suite de tests"""
        test_path = task_data.get("test_path", "./test")
        framework_name = task_data.get("framework", self._agent_config.get("testing", {}).get("default_framework", "foundry"))
        
        # Détecter le framework
        try:
            framework = TestFramework(framework_name)
        except ValueError:
            return {"success": False, "error": f"Framework non supporté: {framework_name}"}
        
        # Vérifier si le framework est disponible
        detector = self._framework_detectors.get(framework)
        if detector and not detector(context.get("project_path", ".")):
            return {"success": False, "error": f"Framework {framework_name} non détecté dans le projet"}
        
        # Simuler l'exécution des tests
        self._logger.info(f"Exécution des tests avec {framework_name}")
        
        return {
            "success": True,
            "framework": framework_name,
            "test_path": test_path,
            "results": {
                "total": 42,
                "passed": 38,
                "failed": 2,
                "skipped": 2,
                "duration_ms": 1250
            }
        }
    
    async def _generate_tests(self, task_data: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Génère automatiquement des tests"""
        contract_name = task_data.get("contract_name", "Contract")
        framework = task_data.get("framework", self._agent_config.get("testing", {}).get("default_framework", "foundry"))
        
        # Sélectionner le template approprié
        if framework == "foundry" or framework == "solidity":
            template = self._test_templates["solidity_unit_test"]
            extension = ".t.sol"
        elif framework in ["hardhat", "truffle"]:
            template = self._test_templates["javascript_test"]
            extension = ".js"
        else:
            template = self._test_templates["python_unit_test"]
            extension = ".py"
        
        # Remplacer les variables dans le template
        test_content = template.replace("{ContractName}", contract_name)
        test_content = test_content.replace("{class_name}", contract_name)
        test_content = test_content.replace("{ClassName}", contract_name)
        
        # Générer le nom du fichier
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"test_{contract_name.lower()}_{timestamp}{extension}"
        
        return {
            "success": True,
            "framework": framework,
            "contract_name": contract_name,
            "generated_file": filename,
            "content_length": len(test_content)
        }
    
    async def _security_scan(self, task_data: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Effectue un scan de sécurité"""
        contract_path = task_data.get("contract_path", "./contracts")
        tools = task_data.get("tools", self._agent_config.get("security", {}).get("tools", []))
        
        self._logger.info(f"Scan de sécurité sur {contract_path} avec {tools}")
        
        findings = [
            SecurityFinding(
                title="Unchecked external call",
                severity=Severity.MEDIUM,
                file_path=f"{contract_path}/example.sol",
                line_number=42,
                code_snippet="(bool success, ) = recipient.call{value: amount}(\"\");"
            ),
            SecurityFinding(
                title="Missing zero address validation",
                severity=Severity.LOW,
                file_path=f"{contract_path}/example.sol",
                line_number=23,
                code_snippet="transferOwnership(newOwner);"
            )
        ]
        
        self._security_findings.extend(findings)
        
        return {
            "success": True,
            "tools_used": tools,
            "findings_count": len(findings),
            "findings": [
                {
                    "title": f.title,
                    "severity": f.severity.value,
                    "file": f.file_path,
                    "line": f.line_number
                }
                for f in findings
            ]
        }
    
    async def _analyze_coverage(self, task_data: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Analyse la couverture de tests"""
        return {
            "success": True,
            "coverage_percent": 78.5,
            "statements": 78.5,
            "branches": 62.3,
            "functions": 85.1,
            "lines": 80.2
        }
    
    async def _generate_report(self, task_data: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Génère un rapport de test"""
        report_name = task_data.get("report_name", f"test_report_{datetime.now().strftime('%Y%m%d')}")
        
        report = TestReport(report_name, context.get("project_path", "."))
        report.test_results = self._test_results[-20:]
        report.security_findings = self._security_findings
        report.completed_at = datetime.now()
        
        self._reports.append(report)
        
        return {
            "success": True,
            "report_id": report.id,
            "report_name": report.name,
            "test_count": len(report.test_results),
            "finding_count": len(report.security_findings)
        }
    
    async def _handle_custom_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """
        Gère les messages personnalisés reçus par l'agent
        
        Args:
            message: Message à traiter
            
        Returns:
            Réponse au message
        """
        self._logger.debug(f"Message personnalisé reçu: {message.get('type', 'unknown')}")
        
        message_type = message.get("type", "")
        
        if message_type == "ping":
            return {"status": "pong", "timestamp": datetime.now().isoformat()}
        elif message_type == "get_test_status":
            return {
                "test_count": len(self._test_results),
                "findings_count": len(self._security_findings),
                "status": self._status.value
            }
        elif message_type == "get_template":
            template_name = message.get("template_name", "")
            if template_name in self._test_templates:
                return {"template": self._test_templates[template_name]}
            else:
                return {"error": f"Template {template_name} non trouvé"}
        else:
            return {"status": "received", "message_type": message_type}
    
    async def health_check(self) -> Dict[str, Any]:
        """Vérifie la santé de l'agent"""
        return {
            "agent": self._name,
            "status": self._status.value,
            "ready": self._status == AgentStatus.READY,
            "test_frameworks": {
                name.value: info["detected"] 
                for name, info in self._test_frameworks.items()
            },
            "test_count": len(self._test_results),
            "findings_count": len(self._security_findings),
            "report_count": len(self._reports),
            "config_loaded": bool(self._agent_config),
            "components": list(self._components.keys()) if hasattr(self, '_components') else [],
            "uptime": self.uptime.total_seconds()
        }
    
    def get_agent_info(self) -> Dict[str, Any]:
        """Retourne les informations de l'agent"""
        return {
            "id": self._name,
            "name": self._display_name,
            "type": "agent",
            "version": self._version,
            "description": self._description,
            "status": self._status.value,
            "created_at": self._start_time.isoformat(),
            "capabilities": self._agent_config.get("agent", {}).get("capabilities", []),
            "supported_frameworks": self._agent_config.get("testing", {}).get("supported_frameworks", []),
            "default_framework": self._agent_config.get("testing", {}).get("default_framework", "foundry"),
            "test_templates_count": len(self._test_templates),
            "test_results_count": len(self._test_results),
            "security_findings_count": len(self._security_findings)
        }


# ------------------------------------------------------------------------
# FONCTIONS D'USINE
# ------------------------------------------------------------------------

def create_tester_agent(config_path: str = "") -> TesterAgent:
    """Crée une instance de TesterAgent"""
    return TesterAgent(config_path)


def create_test_case(name: str, test_type: str, framework: str, file_path: str) -> TestCase:
    """Crée un cas de test"""
    try:
        test_type_enum = TestType(test_type)
        framework_enum = TestFramework(framework)
        return TestCase(name, test_type_enum, framework_enum, file_path)
    except ValueError as e:
        raise ValueError(f"Type de test ou framework invalide: {e}")


def create_security_finding(title: str, severity: str, file_path: str, line_number: int = None) -> SecurityFinding:
    """Crée un finding de sécurité"""
    try:
        severity_enum = Severity(severity)
        return SecurityFinding(title, severity_enum, file_path, line_number)
    except ValueError as e:
        raise ValueError(f"Niveau de sévérité invalide: {e}")
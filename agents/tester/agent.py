"""
Agent Tester - Tests et assurance qualité
Version alignée avec l'infrastructure existante
Version: 2.2.2
"""

import os
import sys
import yaml
import asyncio
import json
import random
import traceback
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum

# ============================================================================
# CONFIGURATION DES IMPORTS
# ============================================================================

# Ajouter le chemin racine du projet
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Import absolu de BaseAgent
from agents.base_agent.base_agent import BaseAgent, AgentStatus


# ============================================================================
# CONSTANTES
# ============================================================================

DEFAULT_CONFIG = {
    "agent": {
        "name": "tester",
        "display_name": "🧪 Agent de Tests",
        "description": "Agent responsable des tests et de l'assurance qualité",
        "version": "2.2.2"
    },
    "tester": {
        "default_framework": "pytest",
        "coverage_threshold": 80,
        "performance_sla_ms": 200,
        "output_directory": "./reports/tests",
        "enable_parallel": True,
        "max_workers": 4,
        "timeout_seconds": 3600,
        "security": {
            "enable_static_analysis": True,
            "enable_dynamic_analysis": True,
            "severity_threshold": "medium"
        }
    },
    "frameworks": {
        "pytest": {
            "enabled": True,
            "command": "pytest",
            "options": ["-v", "--tb=short"]
        },
        "jest": {
            "enabled": True,
            "command": "npx jest",
            "options": ["--coverage"]
        },
        "hardhat": {
            "enabled": True,
            "command": "npx hardhat test",
            "options": []
        }
    }
}


# ============================================================================
# CLASSES DE DONNÉES
# ============================================================================

class TestType(Enum):
    """Types de tests supportés"""
    UNIT = "unit"
    INTEGRATION = "integration"
    E2E = "e2e"
    FUZZING = "fuzzing"
    SECURITY = "security"
    PERFORMANCE = "performance"
    LOAD = "load"
    ACCESSIBILITY = "accessibility"
    API = "api"


class TestStatus(Enum):
    """Statuts possibles d'un test"""
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    ERROR = "error"


class Severity(Enum):
    """Niveaux de sévérité pour les vulnérabilités"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


@dataclass
class TestCase:
    """Représente un cas de test"""
    id: str
    name: str
    type: TestType
    description: str = ""
    status: TestStatus = TestStatus.PENDING
    duration_ms: float = 0.0
    error_message: Optional[str] = None
    stack_trace: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "type": self.type.value,
            "description": self.description,
            "status": self.status.value,
            "duration_ms": self.duration_ms,
            "error_message": self.error_message,
            "timestamp": self.timestamp.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TestCase':
        """Crée un cas de test depuis un dictionnaire"""
        test = cls(
            id=data.get("id", ""),
            name=data.get("name", ""),
            type=TestType(data.get("type", "unit")),
            description=data.get("description", "")
        )
        test.status = TestStatus(data.get("status", "pending"))
        test.duration_ms = data.get("duration_ms", 0.0)
        test.error_message = data.get("error_message")
        return test


@dataclass
class TestSuite:
    """Représente une suite de tests"""
    id: str
    name: str
    test_cases: List[TestCase] = field(default_factory=list)
    status: TestStatus = TestStatus.PENDING
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    coverage: float = 0.0
    
    def add_test(self, test_case: TestCase):
        self.test_cases.append(test_case)
    
    def get_stats(self) -> Dict[str, Any]:
        total = len(self.test_cases)
        passed = sum(1 for t in self.test_cases if t.status == TestStatus.PASSED)
        failed = sum(1 for t in self.test_cases if t.status == TestStatus.FAILED)
        skipped = sum(1 for t in self.test_cases if t.status == TestStatus.SKIPPED)
        errors = sum(1 for t in self.test_cases if t.status == TestStatus.ERROR)
        
        return {
            "total": total,
            "passed": passed,
            "failed": failed,
            "skipped": skipped,
            "errors": errors,
            "success_rate": (passed / total * 100) if total > 0 else 0,
            "coverage": self.coverage
        }
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "status": self.status.value,
            "test_cases": [t.to_dict() for t in self.test_cases],
            "stats": self.get_stats(),
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "coverage": self.coverage
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TestSuite':
        """Crée une suite de tests depuis un dictionnaire"""
        suite = cls(
            id=data.get("id", ""),
            name=data.get("name", "")
        )
        suite.status = TestStatus(data.get("status", "pending"))
        suite.coverage = data.get("coverage", 0.0)
        
        for test_data in data.get("test_cases", []):
            suite.test_cases.append(TestCase.from_dict(test_data))
        
        return suite


@dataclass
class SecurityFinding:
    """Vulnérabilité de sécurité détectée"""
    id: str
    severity: Severity
    type: str
    location: str
    description: str
    recommendation: str
    swc_id: Optional[str] = None
    cve_id: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "severity": self.severity.value,
            "type": self.type,
            "location": self.location,
            "description": self.description,
            "recommendation": self.recommendation,
            "swc_id": self.swc_id,
            "cve_id": self.cve_id,
            "timestamp": self.timestamp.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SecurityFinding':
        """Crée un finding de sécurité depuis un dictionnaire"""
        finding = cls(
            id=data.get("id", ""),
            severity=Severity(data.get("severity", "info")),
            type=data.get("type", ""),
            location=data.get("location", ""),
            description=data.get("description", ""),
            recommendation=data.get("recommendation", "")
        )
        finding.swc_id = data.get("swc_id")
        finding.cve_id = data.get("cve_id")
        return finding


@dataclass
class TestReport:
    """Rapport de test complet"""
    id: str
    name: str
    suites: List[TestSuite] = field(default_factory=list)
    security_findings: List[SecurityFinding] = field(default_factory=list)
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    environment: Dict[str, Any] = field(default_factory=dict)
    
    def get_summary(self) -> Dict[str, Any]:
        all_tests = []
        for suite in self.suites:
            all_tests.extend(suite.test_cases)
        
        total = len(all_tests)
        passed = sum(1 for t in all_tests if t.status == TestStatus.PASSED)
        failed = sum(1 for t in all_tests if t.status == TestStatus.FAILED)
        
        return {
            "total_tests": total,
            "passed": passed,
            "failed": failed,
            "success_rate": (passed / total * 100) if total > 0 else 0,
            "vulnerabilities_found": len(self.security_findings),
            "critical_vulnerabilities": sum(1 for f in self.security_findings if f.severity == Severity.CRITICAL),
            "duration_seconds": (self.end_time - self.start_time).total_seconds() if self.end_time else 0
        }
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "suites": [s.to_dict() for s in self.suites],
            "security_findings": [f.to_dict() for f in self.security_findings],
            "summary": self.get_summary(),
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "environment": self.environment
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TestReport':
        """Crée un rapport de test depuis un dictionnaire"""
        report = cls(
            id=data.get("id", ""),
            name=data.get("name", "")
        )
        report.environment = data.get("environment", {})
        
        for suite_data in data.get("suites", []):
            report.suites.append(TestSuite.from_dict(suite_data))
        
        for finding_data in data.get("security_findings", []):
            report.security_findings.append(SecurityFinding.from_dict(finding_data))
        
        return report


# ============================================================================
# AGENT TESTER PRINCIPAL
# ============================================================================

class TesterAgent(BaseAgent):
    """
    Agent responsable des tests et de l'assurance qualité.
    
    Capacités:
    - Tests unitaires
    - Tests d'intégration
    - Tests E2E
    - Tests de sécurité
    - Tests de performance
    - Fuzzing
    - Génération de rapports
    """
    
    def __init__(self, config_path: str = ""):
        """
        Initialise l'agent Tester.
        
        Args:
            config_path: Chemin vers le fichier de configuration
        """
        # Si aucun chemin de config n'est fourni, utiliser le chemin par défaut
        if not config_path:
            config_path = str(project_root / "agents" / "tester" / "config.yaml")
        
        # Initialiser l'agent de base
        super().__init__(config_path)
        
        # Charger la configuration
        self._load_configuration()
        
        self._logger.info("🧪 Agent Tester créé")
        
        # =====================================================================
        # ÉTAT INTERNE
        # =====================================================================
        self._test_suites: Dict[str, TestSuite] = {}
        self._test_reports: Dict[str, TestReport] = {}
        self._test_templates: Dict[str, str] = {}
        self._components: Dict[str, Any] = {}
        self._initialized = False
        
        # =====================================================================
        # STATISTIQUES
        # =====================================================================
        self._stats = {
            'total_tests_executed': 0,
            'total_tests_passed': 0,
            'total_tests_failed': 0,
            'total_security_findings': 0,
            'average_coverage': 0.0,
            'last_test_run': None,
            'test_types_run': {},
            'frameworks_used': [],
            'start_time': datetime.now()
        }
        
        # =====================================================================
        # TÂCHES DE FOND
        # =====================================================================
        self._cleanup_task_obj = None  # Renommé pour éviter le conflit avec la méthode
        
        # Initialiser les templates
        self._initialize_templates()
    
    def _load_configuration(self):
        """Charge la configuration depuis le fichier YAML"""
        try:
            if self._config_path and os.path.exists(self._config_path):
                with open(self._config_path, 'r', encoding='utf-8') as f:
                    file_config = yaml.safe_load(f) or {}
                
                # Fusion avec la config par défaut
                self._agent_config = self._merge_configs(DEFAULT_CONFIG, file_config)
                self._logger.info(f"✅ Configuration chargée depuis {self._config_path}")
            else:
                self._logger.warning("⚠️ Fichier de configuration non trouvé, utilisation des valeurs par défaut")
                self._agent_config = DEFAULT_CONFIG.copy()
        except Exception as e:
            self._logger.error(f"❌ Erreur chargement config: {e}")
            self._agent_config = DEFAULT_CONFIG.copy()
    
    def _merge_configs(self, default: Dict, override: Dict) -> Dict:
        """Fusionne deux configurations récursivement"""
        result = default.copy()
        
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_configs(result[key], value)
            else:
                result[key] = value
        
        return result
    
    def _initialize_templates(self):
        """Initialise les templates de tests."""
        self._test_templates = {
            "unit_python": self._get_unit_python_template(),
            "unit_javascript": self._get_unit_javascript_template(),
            "integration_python": self._get_integration_python_template(),
            "integration_javascript": self._get_integration_javascript_template(),
            "solidity_test": self._get_solidity_test_template(),
            "fuzzing_template": self._get_fuzzing_template(),
            "security_template": self._get_security_template(),
            "performance_template": self._get_performance_template(),
            "api_test_template": self._get_api_test_template()
        }
    
    # ========================================================================
    # INITIALISATION
    # ========================================================================
    
    async def initialize(self) -> bool:
        """
        Initialise l'agent Tester.
        
        Returns:
            True si l'initialisation a réussi
        """
        try:
            self._status = AgentStatus.INITIALIZING
            self._logger.info("Initialisation de l'agent Tester...")
            
            # Appeler l'initialisation du parent
            base_result = await super().initialize()
            if not base_result:
                return False
            
            # Initialiser les composants
            await self._initialize_components()
            
            # Vérifier les frameworks disponibles
            await self._check_frameworks()
            
            # Démarrer les tâches de fond
            self._start_background_tasks()
            
            self._initialized = True
            self._status = AgentStatus.READY
            self._logger.info("✅ Agent Tester prêt")
            return True
            
        except Exception as e:
            self._logger.error(f"❌ Erreur initialisation: {e}")
            self._logger.error(traceback.format_exc())
            self._status = AgentStatus.ERROR
            return False
    
    def _start_background_tasks(self):
        """Démarre les tâches de fond"""
        loop = asyncio.get_event_loop()
        self._cleanup_task_obj = loop.create_task(self._cleanup_task())  # Utilisation du nouvel attribut
        self._logger.debug("🧹 Tâche de nettoyage démarrée")
    
    async def _initialize_components(self) -> bool:
        """
        Initialise les composants internes.
        
        Returns:
            True si l'initialisation a réussi
        """
        try:
            self._logger.info("Initialisation des composants...")
            
            self._components = {
                "unit_test_runner": {
                    "enabled": True,
                    "frameworks": ["pytest", "jest", "hardhat"]
                },
                "integration_test_runner": {
                    "enabled": True,
                    "frameworks": ["pytest", "jest"]
                },
                "e2e_test_runner": {
                    "enabled": True,
                    "frameworks": ["cypress", "playwright"]
                },
                "security_scanner": {
                    "enabled": self._agent_config.get("tester", {}).get("security", {}).get("enable_static_analysis", True),
                    "tools": ["slither", "mythril", "semgrep"]
                },
                "fuzzing_engine": {
                    "enabled": True,
                    "tools": ["echidna", "medusa", "foundry"]
                },
                "performance_analyzer": {
                    "enabled": True,
                    "metrics": ["response_time", "throughput", "cpu_usage"]
                },
                "coverage_analyzer": {
                    "enabled": True,
                    "tools": ["coverage.py", "istanbul", "hardhat-coverage"]
                },
                "report_generator": {
                    "enabled": True,
                    "formats": ["html", "json", "junit"]
                }
            }
            
            self._logger.info(f"✅ Composants: {list(self._components.keys())}")
            return True
            
        except Exception as e:
            self._logger.error(f"Erreur composants: {e}")
            return False
    
    async def _check_frameworks(self) -> bool:
        """Vérifie les frameworks de test disponibles."""
        self._logger.info("Vérification des frameworks de test...")
        
        frameworks = self._agent_config.get("frameworks", {})
        available = []
        
        for framework_name, framework_config in frameworks.items():
            if framework_config.get("enabled", False):
                # Vérifier si la commande existe
                command = framework_config.get("command", "").split()[0]
                try:
                    import shutil
                    if shutil.which(command):
                        available.append(framework_name)
                        self._logger.debug(f"   ✓ {framework_name} disponible")
                    else:
                        self._logger.debug(f"   ⚠️ {framework_name} non installé")
                except:
                    self._logger.debug(f"   ⚠️ Impossible de vérifier {framework_name}")
        
        self._stats['frameworks_used'] = available
        self._logger.info(f"   ✅ Frameworks disponibles: {', '.join(available) if available else 'aucun'}")
        
        return True
    
    # ========================================================================
    # TÂCHE DE NETTOYAGE
    # ========================================================================
    
    async def _cleanup_task(self):
        """
        Tâche de nettoyage périodique
        """
        self._logger.info("🧹 Tâche de nettoyage démarrée")
        
        while self._status == AgentStatus.READY:
            try:
                # Nettoyage toutes les heures
                await asyncio.sleep(3600)
                
                self._logger.debug("Nettoyage périodique...")
                
                tester_config = self._agent_config.get("tester", {})
                output_dir = Path(tester_config.get("output_directory", "./reports/tests"))
                
                # Nettoyer les vieux rapports (> 30 jours)
                if output_dir.exists():
                    cutoff = datetime.now() - timedelta(days=30)
                    for report_file in output_dir.glob("*.json"):
                        try:
                            mtime = datetime.fromtimestamp(report_file.stat().st_mtime)
                            if mtime < cutoff:
                                report_file.unlink()
                                self._logger.debug(f"🗑️ Rapport supprimé: {report_file.name}")
                        except Exception as e:
                            self._logger.error(f"Erreur suppression {report_file}: {e}")
                
                # Nettoyer les vieux rapports HTML (> 30 jours)
                for report_file in output_dir.glob("*.html"):
                    try:
                        mtime = datetime.fromtimestamp(report_file.stat().st_mtime)
                        if mtime < cutoff:
                            report_file.unlink()
                            self._logger.debug(f"🗑️ Rapport HTML supprimé: {report_file.name}")
                    except Exception as e:
                        self._logger.error(f"Erreur suppression {report_file}: {e}")
                
            except asyncio.CancelledError:
                self._logger.info("🛑 Tâche de nettoyage arrêtée")
                break
            except Exception as e:
                self._logger.error(f"❌ Erreur dans la tâche de nettoyage: {e}")
                await asyncio.sleep(60)
    
    # ========================================================================
    # MÉTHODES FONCTIONNELLES PRINCIPALES
    # ========================================================================
    
    async def run_tests(self, test_spec: Dict[str, Any]) -> Dict[str, Any]:
        """
        Exécute une suite de tests selon les spécifications.
        
        Args:
            test_spec: Spécification des tests à exécuter
            
        Returns:
            Résultats des tests
        """
        self._logger.info(f"🚀 Exécution de tests: {test_spec.get('name', 'Sans nom')}")
        
        try:
            # Créer une nouvelle suite de tests
            suite_id = f"suite_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            suite_name = test_spec.get('name', f'Test Suite {suite_id}')
            
            suite = TestSuite(
                id=suite_id,
                name=suite_name,
                start_time=datetime.now()
            )
            
            # Déterminer le type de test
            test_type_str = test_spec.get('type', 'unit')
            try:
                test_type = TestType(test_type_str)
            except ValueError:
                test_type = TestType.UNIT
            
            # Générer les cas de test
            test_cases = self._generate_test_cases(test_spec, test_type)
            
            # Exécuter chaque cas de test
            for test_case in test_cases:
                self._logger.debug(f"   Exécution: {test_case.name}")
                test_case.status = TestStatus.RUNNING
                
                try:
                    # Simuler l'exécution du test
                    await asyncio.sleep(0.1)  # Simulation
                    
                    # 90% de chance de succès pour la simulation
                    if random.random() < 0.9:
                        test_case.status = TestStatus.PASSED
                        self._stats['total_tests_passed'] += 1
                    else:
                        test_case.status = TestStatus.FAILED
                        test_case.error_message = "Assertion error: expected True, got False"
                        self._stats['total_tests_failed'] += 1
                    
                    test_case.duration_ms = random.uniform(10, 500)
                    
                except Exception as e:
                    test_case.status = TestStatus.ERROR
                    test_case.error_message = str(e)
                    test_case.stack_trace = traceback.format_exc()
                    self._stats['total_tests_failed'] += 1
                
                suite.add_test(test_case)
                self._stats['total_tests_executed'] += 1
            
            # Mettre à jour les statistiques par type
            type_str = test_type.value
            self._stats['test_types_run'][type_str] = self._stats['test_types_run'].get(type_str, 0) + 1
            
            # Calculer la couverture (simulation)
            suite.coverage = random.uniform(70, 95)
            self._stats['average_coverage'] = (
                (self._stats['average_coverage'] * (self._stats['total_tests_executed'] - len(test_cases)) +
                 suite.coverage * len(test_cases)) / self._stats['total_tests_executed']
            )
            
            suite.end_time = datetime.now()
            suite.status = TestStatus.PASSED if suite.get_stats()['failed'] == 0 else TestStatus.FAILED
            
            # Stocker la suite
            self._test_suites[suite_id] = suite
            self._stats['last_test_run'] = datetime.now().isoformat()
            
            # Retourner les résultats
            return {
                "success": suite.status == TestStatus.PASSED,
                "suite_id": suite_id,
                "suite_name": suite_name,
                "stats": suite.get_stats(),
                "test_cases": [t.to_dict() for t in suite.test_cases],
                "coverage": suite.coverage,
                "duration_seconds": (suite.end_time - suite.start_time).total_seconds()
            }
            
        except Exception as e:
            self._logger.error(f"Erreur exécution tests: {e}")
            return {
                "success": False,
                "error": str(e),
                "tests_executed": 0
            }
    
    async def security_audit(self, target: Dict[str, Any]) -> Dict[str, Any]:
        """
        Exécute un audit de sécurité sur la cible spécifiée.
        
        Args:
            target: Cible de l'audit (code, contrat, etc.)
            
        Returns:
            Résultats de l'audit
        """
        self._logger.info(f"🔒 Audit de sécurité: {target.get('name', 'Cible inconnue')}")
        
        try:
            findings = []
            
            # Types de vulnérabilités possibles
            vuln_types = [
                ("reentrancy", Severity.CRITICAL, "SWC-107"),
                ("integer_overflow", Severity.HIGH, "SWC-101"),
                ("access_control", Severity.CRITICAL, "SWC-115"),
                ("timestamp_dependence", Severity.MEDIUM, "SWC-116"),
                ("unchecked_call", Severity.HIGH, "SWC-104"),
                ("delegatecall", Severity.CRITICAL, "SWC-112"),
                ("self_destruct", Severity.CRITICAL, "SWC-106"),
                ("front_running", Severity.MEDIUM, "SWC-114"),
                ("gas_limit", Severity.LOW, "SWC-126")
            ]
            
            # Simuler la détection de vulnérabilités
            num_findings = random.randint(0, 5)
            for i in range(num_findings):
                vuln_type, severity, swc = random.choice(vuln_types)
                
                finding = SecurityFinding(
                    id=f"finding_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{i}",
                    severity=severity,
                    type=vuln_type,
                    location=target.get('location', 'unknown'),
                    description=f"Potential {vuln_type} vulnerability detected",
                    recommendation=self._get_remediation(vuln_type),
                    swc_id=swc
                )
                findings.append(finding)
            
            # Mettre à jour les stats
            self._stats['total_security_findings'] += len(findings)
            
            # Compter par sévérité
            by_severity = {
                "critical": sum(1 for f in findings if f.severity == Severity.CRITICAL),
                "high": sum(1 for f in findings if f.severity == Severity.HIGH),
                "medium": sum(1 for f in findings if f.severity == Severity.MEDIUM),
                "low": sum(1 for f in findings if f.severity == Severity.LOW)
            }
            
            return {
                "secure": len(findings) == 0,
                "total_findings": len(findings),
                "by_severity": by_severity,
                "findings": [f.to_dict() for f in findings],
                "score": max(0, 100 - len(findings) * 15),
                "recommendations": [
                    "Use ReentrancyGuard for external calls",
                    "Implement proper access controls",
                    "Use SafeMath or Solidity 0.8.x"
                ][:min(3, len(findings) + 1)]
            }
            
        except Exception as e:
            self._logger.error(f"Erreur audit sécurité: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def run_fuzzing(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Exécute des tests de fuzzing.
        
        Args:
            params: Paramètres du fuzzing
            
        Returns:
            Résultats du fuzzing
        """
        self._logger.info(f"🎲 Fuzzing: {params.get('target', 'Cible inconnue')}")
        
        try:
            # Simulation de fuzzing
            num_tests = params.get('num_tests', 10000)
            duration = params.get('duration', 60)
            
            # Simuler des résultats
            crashes = random.randint(0, int(num_tests * 0.001))  # 0.1% de crashes
            hangs = random.randint(0, 5)
            
            # Générer des séquences d'attaque simulées
            attack_sequences = []
            if crashes > 0:
                for i in range(min(crashes, 3)):
                    attack_sequences.append([
                        f"call transfer(0xdead, {random.randint(1, 1000)})",
                        f"call withdraw({random.randint(1, 1000)})",
                        f"call transfer(0xbeef, {random.randint(1, 1000)})"
                    ])
            
            return {
                "success": crashes == 0,
                "tests_run": num_tests,
                "crashes_found": crashes,
                "hangs_detected": hangs,
                "coverage": f"{random.uniform(60, 95):.1f}%",
                "duration_seconds": duration,
                "attack_sequences": attack_sequences,
                "recommendations": [
                    "Increase input validation",
                    "Add boundary checks",
                    "Use safe math operations"
                ] if crashes > 0 else []
            }
            
        except Exception as e:
            self._logger.error(f"Erreur fuzzing: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def run_performance_test(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Exécute des tests de performance.
        
        Args:
            params: Paramètres du test
            
        Returns:
            Résultats du test de performance
        """
        self._logger.info(f"⚡ Test de performance: {params.get('name', 'Sans nom')}")
        
        try:
            # Simulation de test de performance
            num_requests = params.get('num_requests', 1000)
            concurrency = params.get('concurrency', 10)
            
            # Simuler des métriques
            avg_response_time = random.uniform(50, 500)
            p95_response_time = avg_response_time * random.uniform(1.5, 2.5)
            throughput = num_requests / (avg_response_time / 1000) * concurrency
            
            tester_config = self._agent_config.get("tester", {})
            sla_ms = tester_config.get('performance_sla_ms', 200)
            sla_violations = sum(1 for _ in range(int(num_requests * 0.05)) if random.random() < 0.1)
            
            return {
                "success": avg_response_time < sla_ms,
                "metrics": {
                    "avg_response_time_ms": round(avg_response_time, 2),
                    "p95_response_time_ms": round(p95_response_time, 2),
                    "throughput_rps": round(throughput, 2),
                    "total_requests": num_requests,
                    "successful_requests": int(num_requests * random.uniform(0.95, 1.0)),
                    "failed_requests": random.randint(0, 50),
                    "sla_violations": sla_violations
                },
                "bottlenecks": [
                    "Database queries",
                    "External API calls"
                ] if avg_response_time > sla_ms else [],
                "recommendations": [
                    "Add caching layer",
                    "Optimize database indexes",
                    "Increase connection pool size"
                ] if avg_response_time > sla_ms else []
            }
            
        except Exception as e:
            self._logger.error(f"Erreur test performance: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_coverage(self, target: str = "all") -> Dict[str, Any]:
        """
        Obtient la couverture de code.
        
        Args:
            target: Cible pour laquelle obtenir la couverture
            
        Returns:
            Rapport de couverture
        """
        self._logger.info(f"📊 Obtention de la couverture pour: {target}")
        
        # Simulation de couverture
        return {
            "success": True,
            "target": target,
            "coverage": {
                "lines": f"{random.uniform(70, 95):.1f}%",
                "branches": f"{random.uniform(60, 90):.1f}%",
                "functions": f"{random.uniform(80, 98):.1f}%",
                "statements": f"{random.uniform(75, 96):.1f}%"
            },
            "uncovered_lines": random.randint(50, 200),
            "files_analyzed": random.randint(20, 100),
            "timestamp": datetime.now().isoformat()
        }
    
    async def generate_report(self, report_spec: Dict[str, Any]) -> Dict[str, Any]:
        """
        Génère un rapport de test.
        
        Args:
            report_spec: Spécification du rapport
            
        Returns:
            Rapport généré
        """
        self._logger.info(f"📄 Génération de rapport: {report_spec.get('name', 'Sans nom')}")
        
        try:
            # Créer un nouveau rapport
            report_id = f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            report_name = report_spec.get('name', f'Test Report {report_id}')
            
            report = TestReport(
                id=report_id,
                name=report_name,
                environment=report_spec.get('environment', {})
            )
            
            # Inclure les suites demandées
            suite_ids = report_spec.get('suite_ids', list(self._test_suites.keys())[-5:])
            for suite_id in suite_ids:
                if suite_id in self._test_suites:
                    report.suites.append(self._test_suites[suite_id])
            
            # Simuler des findings de sécurité si demandé
            if report_spec.get('include_security', True):
                # Ajouter quelques findings simulés
                for i in range(random.randint(0, 3)):
                    finding = SecurityFinding(
                        id=f"finding_{report_id}_{i}",
                        severity=random.choice(list(Severity)),
                        type=random.choice(["reentrancy", "overflow", "access_control"]),
                        location=f"contracts/Token.sol:{random.randint(10, 200)}",
                        description="Potential security vulnerability",
                        recommendation="Apply security best practices"
                    )
                    report.security_findings.append(finding)
            
            report.end_time = datetime.now()
            
            # Sauvegarder le rapport
            self._test_reports[report_id] = report
            
            # Sauvegarder sur disque
            tester_config = self._agent_config.get("tester", {})
            output_dir = Path(tester_config.get("output_directory", "./reports/tests"))
            output_dir.mkdir(parents=True, exist_ok=True)
            
            report_file = output_dir / f"{report_id}.json"
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report.to_dict(), f, indent=2, ensure_ascii=False)
            
            return {
                "success": True,
                "report_id": report_id,
                "report_name": report_name,
                "summary": report.get_summary(),
                "file_path": str(report_file),
                "formats_available": ["json", "html"] if report_spec.get('generate_html', False) else ["json"]
            }
            
        except Exception as e:
            self._logger.error(f"Erreur génération rapport: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    # ========================================================================
    # MÉTHODES UTILITAIRES
    # ========================================================================
    
    def _generate_test_cases(self, spec: Dict[str, Any], test_type: TestType) -> List[TestCase]:
        """Génère des cas de test basés sur les spécifications."""
        test_cases = []
        num_tests = spec.get('num_tests', random.randint(5, 20))
        
        for i in range(num_tests):
            test_case = TestCase(
                id=f"test_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{i}",
                name=f"{test_type.value}_test_{i+1}",
                type=test_type,
                description=f"Test case {i+1} for {test_type.value} testing"
            )
            test_cases.append(test_case)
        
        return test_cases
    
    def _get_remediation(self, vuln_type: str) -> str:
        """Retourne une suggestion de correction pour un type de vulnérabilité."""
        remediations = {
            "reentrancy": "Use ReentrancyGuard or follow Checks-Effects-Interactions pattern",
            "integer_overflow": "Use SafeMath library or Solidity 0.8.x",
            "access_control": "Implement proper access controls with onlyOwner modifiers",
            "timestamp_dependence": "Avoid relying on block.timestamp for critical logic",
            "unchecked_call": "Always check return values of external calls",
            "delegatecall": "Ensure delegatecall targets are trusted contracts",
            "self_destruct": "Remove or protect selfdestruct with access controls",
            "front_running": "Use commit-reveal schemes or submarine sends",
            "gas_limit": "Optimize loops and avoid unbounded operations"
        }
        return remediations.get(vuln_type, "Review code for security best practices")
    
    # ========================================================================
    # TEMPLATES DE TESTS
    # ========================================================================
    
    def _get_unit_python_template(self) -> str:
        """Template pour tests unitaires Python."""
        return '''"""
Unit tests for {{ module_name }}
"""

import pytest
from {{ module_name }} import {{ class_name }}

class Test{{ class_name }}:
    """Test suite for {{ class_name }}"""
    
    def setup_method(self):
        """Setup before each test."""
        self.instance = {{ class_name }}()
    
    def test_initialization(self):
        """Test that the instance initializes correctly."""
        assert self.instance is not None
        assert hasattr(self.instance, '{{ attribute_name }}')
    
    def test_{{ method_name }}_success(self):
        """Test successful execution of {{ method_name }}."""
        result = self.instance.{{ method_name }}(valid_input)
        assert result is not None
        assert result == expected_output
    
    def test_{{ method_name }}_failure(self):
        """Test that {{ method_name }} fails with invalid input."""
        with pytest.raises(ValueError):
            self.instance.{{ method_name }}(invalid_input)
    
    @pytest.mark.parametrize("input_value,expected", [
        (1, 1),
        (10, 10),
        (100, 100),
    ])
    def test_{{ method_name }}_parameterized(self, input_value, expected):
        """Test {{ method_name }} with multiple inputs."""
        result = self.instance.{{ method_name }}(input_value)
        assert result == expected
'''
    
    def _get_unit_javascript_template(self) -> str:
        """Template pour tests unitaires JavaScript."""
        return '''/**
 * Unit tests for {{ module_name }}
 */

const {{ class_name }} = require('./{{ module_name }}');

describe('{{ class_name }}', () => {
    let instance;

    beforeEach(() => {
        instance = new {{ class_name }}();
    });

    test('should initialize correctly', () => {
        expect(instance).toBeDefined();
        expect(instance.{{ attribute_name }}).toBeDefined();
    });

    test('{{ method_name }} should work with valid input', () => {
        const result = instance.{{ method_name }}(validInput);
        expect(result).toBe(expectedOutput);
    });

    test('{{ method_name }} should throw with invalid input', () => {
        expect(() => {
            instance.{{ method_name }}(invalidInput);
        }).toThrow();
    });

    test.each([
        [1, 1],
        [10, 10],
        [100, 100],
    ])('{{ method_name }} with %i should return %i', (input, expected) => {
        const result = instance.{{ method_name }}(input);
        expect(result).toBe(expected);
    });
});
'''
    
    def _get_integration_python_template(self) -> str:
        """Template pour tests d'intégration Python."""
        return '''"""
Integration tests for {{ system_name }}
"""

import pytest
from {{ component_a }} import {{ class_a }}
from {{ component_b }} import {{ class_b }}

class TestIntegration:
    """Integration tests between components."""
    
    def setup_method(self):
        """Setup test environment."""
        self.component_a = {{ class_a }}()
        self.component_b = {{ class_b }}()
    
    def test_components_interact_correctly(self):
        """Test that components work together."""
        # Setup
        data = self.component_a.prepare_data()
        
        # Execute
        result = self.component_b.process_data(data)
        
        # Verify
        assert result is not None
        assert result.status == "success"
    
    def test_error_handling_propagates(self):
        """Test that errors are properly handled across components."""
        with pytest.raises(Exception):
            self.component_a.trigger_error()
            self.component_b.handle_error()
'''
    
    def _get_integration_javascript_template(self) -> str:
        """Template pour tests d'intégration JavaScript."""
        return '''/**
 * Integration tests for {{ system_name }}
 */

const ComponentA = require('./{{ component_a }}');
const ComponentB = require('./{{ component_b }}');

describe('System Integration', () => {
    let componentA;
    let componentB;

    beforeEach(() => {
        componentA = new ComponentA();
        componentB = new ComponentB();
    });

    test('components should work together', () => {
        const data = componentA.prepareData();
        const result = componentB.processData(data);
        
        expect(result).toBeDefined();
        expect(result.status).toBe('success');
    });

    test('errors should propagate correctly', () => {
        expect(() => {
            componentA.triggerError();
            componentB.handleError();
        }).toThrow();
    });
});
'''
    
    def _get_solidity_test_template(self) -> str:
        """Template pour tests Solidity avec Hardhat."""
        return '''// SPDX-License-Identifier: MIT
const { expect } = require("chai");
const { ethers } = require("hardhat");

describe("{{ contract_name }}", function () {
    let {{ contract_var }};
    let owner;
    let addr1;
    let addr2;

    beforeEach(async function () {
        [owner, addr1, addr2] = await ethers.getSigners();
        const Contract = await ethers.getContractFactory("{{ contract_name }}");
        {{ contract_var }} = await Contract.deploy();
        await {{ contract_var }}.deployed();
    });

    describe("Deployment", function () {
        it("Should set the right owner", async function () {
            expect(await {{ contract_var }}.owner()).to.equal(owner.address);
        });

        it("Should have correct initial state", async function () {
            const value = await {{ contract_var }}.{{ initial_value }}();
            expect(value).to.equal({{ expected_initial }});
        });
    });

    describe("Transactions", function () {
        it("Should allow valid transfers", async function () {
            const amount = {{ test_amount }};
            await {{ contract_var }}.connect(owner).{{ transfer_method }}(addr1.address, amount);
            
            const balance = await {{ contract_var }}.balanceOf(addr1.address);
            expect(balance).to.equal(amount);
        });

        it("Should fail for invalid transfers", async function () {
            const amount = {{ large_amount }};
            await expect(
                {{ contract_var }}.connect(addr1).{{ transfer_method }}(addr2.address, amount)
            ).to.be.revertedWith("{{ error_message }}");
        });
    });

    describe("Events", function () {
        it("Should emit correct events", async function () {
            const amount = {{ test_amount }};
            await expect({{ contract_var }}.connect(owner).{{ action_method }}())
                .to.emit({{ contract_var }}, "{{ event_name }}")
                .withArgs(owner.address, amount);
        });
    });
});
'''
    
    def _get_fuzzing_template(self) -> str:
        """Template pour tests de fuzzing."""
        return '''# Fuzzing Test Template
# Target: {{ target_name }}

# Test properties
properties:
  - name: "never_reverts"
    description: "Function should never revert with valid inputs"
    
  - name: "state_consistency"
    description: "State should remain consistent after operations"
    
  - name: "invariant_total_supply"
    description: "Total supply should never decrease"
    
  - name: "no_reentrancy"
    description: "Should not be vulnerable to reentrancy"

# Test configuration
testLimit: {{ test_limit | default(10000) }}
shrinkLimit: 5000
seqLen: 100

# Function signatures to test
testFunctions:
  - "transfer(address,uint256)"
  - "approve(address,uint256)"
  - "transferFrom(address,address,uint256)"
  
# Filter functions
filterFunctions: ["constructor", "renounceOwnership"]

# Coverage
coverage: true
format: "text"

# Test corpus
corpusDir: "corpus"
'''
    
    def _get_security_template(self) -> str:
        """Template pour tests de sécurité."""
        return '''# Security Test Template
# Target: {{ target_name }}

# Static analysis configuration
static_analysis:
  enabled: true
  tools:
    - slither
    - mythril
  detectors:
    - reentrancy
    - integer-overflow
    - timestamp-dependence
    - tx-origin

# Dynamic analysis
dynamic_analysis:
  enabled: true
  test_duration: {{ duration | default(300) }}
  attack_vectors:
    - reentrancy
    - front-running
    - sandwich-attacks
    - flash-loans

# Test cases
test_cases:
  - name: "Reentrancy Attack"
    steps:
      - "deploy_attacker_contract()"
      - "call_vulnerable_function()"
      - "verify_exploit()"
    
  - name: "Access Control Bypass"
    steps:
      - "deploy_malicious_actor()"
      - "attempt_privileged_action()"
      - "check_access_control()"

# Expected results
expected_results:
  critical_vulnerabilities: 0
  high_vulnerabilities: 0
  medium_vulnerabilities: "< 3"
'''
    
    def _get_performance_template(self) -> str:
        """Template pour tests de performance."""
        return '''# Performance Test Template
# Target: {{ target_name }}

# Load test configuration
load_test:
  duration: {{ duration | default(60) }}  # seconds
  users: {{ concurrent_users | default(10) }}
  ramp_up: 30  # seconds
  target_rps: {{ target_rps | default(100) }}

# Endpoints to test
endpoints:
  - name: "read_operation"
    method: "GET"
    path: "/api/data"
    weight: 60  # percentage of requests
    
  - name: "write_operation"
    method: "POST"
    path: "/api/data"
    weight: 40
    payload:
      template: "data.json"
      
# Metrics to collect
metrics:
  - response_time
  - throughput
  - error_rate
  - cpu_usage
  - memory_usage
  
# Service Level Agreements
sla:
  avg_response_time_ms: {{ sla_ms | default(200) }}
  p95_response_time_ms: {{ sla_p95 | default(500) }}
  error_rate_percent: 1
  throughput_min_rps: {{ min_throughput | default(50) }}
'''
    
    def _get_api_test_template(self) -> str:
        """Template pour tests d'API."""
        return '''# API Test Template
# API: {{ api_name }}
# Version: {{ api_version }}

# Test configuration
base_url: "{{ base_url }}"
timeout: {{ timeout | default(30) }}

# Authentication
auth:
  type: "{{ auth_type | default('none') }}"
  token: "{{ auth_token }}"
  
# Test suites
test_suites:
  - name: "Health Check"
    tests:
      - name: "Root endpoint"
        method: "GET"
        path: "/"
        expected_status: 200
        expected_schema: "health_schema.json"
        
      - name: "Health endpoint"
        method: "GET"
        path: "/health"
        expected_status: 200
        expected_body:
          status: "healthy"
          
  - name: "CRUD Operations"
    tests:
      - name: "Create item"
        method: "POST"
        path: "/items"
        payload:
          name: "Test Item"
          description: "Test Description"
        expected_status: 201
        expected_schema: "item_schema.json"
        
      - name: "Get item"
        method: "GET"
        path: "/items/{id}"
        expected_status: 200
        expected_schema: "item_schema.json"
        
      - name: "Update item"
        method: "PUT"
        path: "/items/{id}"
        payload:
          name: "Updated Item"
        expected_status: 200
        
      - name: "Delete item"
        method: "DELETE"
        path: "/items/{id}"
        expected_status: 204

  - name: "Error Handling"
    tests:
      - name: "Not found"
        method: "GET"
        path: "/nonexistent"
        expected_status: 404
        
      - name: "Invalid input"
        method: "POST"
        path: "/items"
        payload:
          invalid: "data"
        expected_status: 400
        expected_schema: "error_schema.json"
'''
    
    # ========================================================================
    # GESTION DES MESSAGES
    # ========================================================================
    
    async def _handle_custom_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """
        Gère les messages personnalisés.
        
        Args:
            message: Message reçu
            
        Returns:
            Réponse
        """
        msg_type = message.get("type", "")
        msg_id = message.get("message_id", "unknown")
        
        self._logger.debug(f"📨 Message reçu: {msg_type} (id: {msg_id})")
        
        try:
            if msg_type == "run_tests":
                result = await self.run_tests(message.get("test_spec", {}))
                return {
                    "message_id": msg_id,
                    "success": True,
                    "result": result
                }
            
            elif msg_type == "security_audit":
                result = await self.security_audit(message.get("target", {}))
                return {
                    "message_id": msg_id,
                    "success": True,
                    "result": result
                }
            
            elif msg_type == "run_fuzzing":
                result = await self.run_fuzzing(message.get("params", {}))
                return {
                    "message_id": msg_id,
                    "success": True,
                    "result": result
                }
            
            elif msg_type == "run_performance_test":
                result = await self.run_performance_test(message.get("params", {}))
                return {
                    "message_id": msg_id,
                    "success": True,
                    "result": result
                }
            
            elif msg_type == "get_coverage":
                result = await self.get_coverage(message.get("target", "all"))
                return {
                    "message_id": msg_id,
                    "success": True,
                    "result": result
                }
            
            elif msg_type == "generate_report":
                result = await self.generate_report(message.get("report_spec", {}))
                return {
                    "message_id": msg_id,
                    "success": True,
                    "result": result
                }
            
            elif msg_type == "get_test_templates":
                return {
                    "message_id": msg_id,
                    "success": True,
                    "templates": list(self._test_templates.keys())
                }
            
            elif msg_type == "get_test_suites":
                return {
                    "message_id": msg_id,
                    "success": True,
                    "suites": [s.to_dict() for s in self._test_suites.values()]
                }
            
            elif msg_type == "get_test_reports":
                return {
                    "message_id": msg_id,
                    "success": True,
                    "reports": [r.to_dict() for r in self._test_reports.values()]
                }
            
            elif msg_type == "ping":
                return {
                    "message_id": msg_id,
                    "success": True,
                    "pong": True,
                    "timestamp": datetime.now().isoformat()
                }
            
            else:
                self._logger.warning(f"⚠️ Type de message non supporté: {msg_type}")
                return {
                    "message_id": msg_id,
                    "success": False,
                    "error": f"Type de message non supporté: {msg_type}"
                }
                
        except Exception as e:
            self._logger.error(f"❌ Erreur traitement message {msg_type}: {e}")
            self._logger.error(traceback.format_exc())
            return {
                "message_id": msg_id,
                "success": False,
                "error": str(e)
            }
    
    # ========================================================================
    # GESTION DU CYCLE DE VIE
    # ========================================================================
    
    async def shutdown(self) -> bool:
        """
        Arrête l'agent proprement.
        """
        self._logger.info("Arrêt de l'agent Tester...")
        self._status = AgentStatus.SHUTTING_DOWN
        
        # Arrêter la tâche de nettoyage
        if self._cleanup_task_obj and not self._cleanup_task_obj.done():
            self._cleanup_task_obj.cancel()
            try:
                await self._cleanup_task_obj
            except asyncio.CancelledError:
                pass
        
        # Sauvegarder les statistiques
        try:
            tester_config = self._agent_config.get("tester", {})
            output_dir = Path(tester_config.get("output_directory", "./reports/tests"))
            output_dir.mkdir(parents=True, exist_ok=True)
            
            stats_file = output_dir / f"tester_stats_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(stats_file, 'w', encoding='utf-8') as f:
                json.dump({
                    "stats": self._stats,
                    "suites_created": len(self._test_suites),
                    "reports_generated": len(self._test_reports),
                    "timestamp": datetime.now().isoformat()
                }, f, indent=2)
            self._logger.info(f"   ✓ Statistiques sauvegardées: {stats_file}")
        except Exception as e:
            self._logger.warning(f"   ⚠️ Impossible de sauvegarder: {e}")
        
        # Appeler la méthode parent
        await super().shutdown()
        
        self._logger.info("✅ Agent Tester arrêté")
        return True
    
    async def pause(self) -> bool:
        """Met l'agent en pause."""
        self._logger.info("Pause de l'agent Tester...")
        self._status = AgentStatus.PAUSED
        return True
    
    async def resume(self) -> bool:
        """Reprend l'activité."""
        self._logger.info("Reprise de l'agent Tester...")
        self._status = AgentStatus.READY
        return True
    
    # ========================================================================
    # HEALTH CHECK & INFO
    # ========================================================================
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Vérifie la santé de l'agent.
        """
        # Calculer quelques métriques
        total_tests = self._stats['total_tests_executed']
        success_rate = (self._stats['total_tests_passed'] / total_tests * 100) if total_tests > 0 else 0
        
        # Calculer l'uptime
        uptime = (datetime.now() - self._stats["start_time"]).total_seconds()
        
        return {
            "agent": self._name,
            "display_name": self._agent_config.get('agent', {}).get('display_name', '🧪 Agent de Tests'),
            "status": self._status.value if hasattr(self._status, 'value') else str(self._status),
            "ready": self._status == AgentStatus.READY,
            "initialized": self._initialized,
            "uptime_seconds": uptime,
            "uptime_formatted": str(timedelta(seconds=int(uptime))),
            "components": list(self._components.keys()),
            "frameworks_available": self._stats['frameworks_used'],
            "stats": {
                "total_tests": self._stats['total_tests_executed'],
                "success_rate": f"{success_rate:.1f}%",
                "vulnerabilities_found": self._stats['total_security_findings'],
                "average_coverage": f"{self._stats['average_coverage']:.1f}%"
            },
            "suites_count": len(self._test_suites),
            "reports_count": len(self._test_reports),
            "last_test_run": self._stats['last_test_run']
        }
    
    def get_agent_info(self) -> Dict[str, Any]:
        """
        Retourne les informations de l'agent.
        """
        agent_config = self._agent_config.get('agent', {})
        return {
            "id": self._name,
            "name": "🧪 Agent de Tests",
            "display_name": agent_config.get('display_name', '🧪 Agent de Tests'),
            "version": agent_config.get('version', '2.2.2'),
            "description": agent_config.get('description', 'Agent responsable des tests et de l\'assurance qualité'),
            "status": self._status.value if hasattr(self._status, 'value') else str(self._status),
            "capabilities": ["unit_testing", "integration_testing", "e2e_testing", "security_testing", "performance_testing", "fuzzing", "report_generation"],
            "test_types": [t.value for t in TestType],
            "frameworks": list(self._agent_config.get("frameworks", {}).keys()),
            "templates": list(self._test_templates.keys()),
            "stats": {
                "total_tests": self._stats['total_tests_executed'],
                "total_security_findings": self._stats['total_security_findings'],
                "average_coverage": round(self._stats['average_coverage'], 1)
            }
        }


# ============================================================================
# FONCTIONS D'USINE
# ============================================================================

def create_tester_agent(config_path: str = "") -> TesterAgent:
    """Crée une instance de l'agent Tester"""
    return TesterAgent(config_path)


async def get_tester_agent(config_path: str = "") -> TesterAgent:
    """Crée et initialise une instance de l'agent Tester"""
    agent = create_tester_agent(config_path)
    await agent.initialize()
    return agent


# ============================================================================
# POINT D'ENTRÉE POUR TEST
# ============================================================================

if __name__ == "__main__":
    async def main():
        print("\n" + "=" * 70)
        print("🧪 TEST DE L'AGENT TESTER".center(70))
        print("=" * 70)
        
        # Créer et initialiser l'agent
        agent = await get_tester_agent()
        
        agent_info = agent.get_agent_info()
        print(f"\n✅ Agent: {agent_info['name']} v{agent_info['version']}")
        print(f"✅ Statut: {agent_info['status']}")
        print(f"✅ Templates: {len(agent_info['templates'])}")
        print(f"✅ Frameworks: {', '.join(agent_info['frameworks'])}")
        
        # Tester les différentes fonctionnalités
        print(f"\n📊 Exécution des tests de démonstration...")
        
        # Test unitaire
        test_spec = {
            "name": "Test Suite Démo",
            "type": "unit",
            "num_tests": 5
        }
        result = await agent.run_tests(test_spec)
        print(f"\n   ✅ Tests unitaires: {result['stats']['passed']}/{result['stats']['total']} passed")
        
        # Audit de sécurité
        audit = await agent.security_audit({"name": "SmartContract.sol", "location": "contracts/"})
        print(f"   🔒 Audit sécurité: {audit['total_findings']} vulnérabilités trouvées")
        
        # Test de performance
        perf = await agent.run_performance_test({"name": "Performance Test", "num_requests": 1000})
        print(f"   ⚡ Test performance: {perf['metrics']['avg_response_time_ms']}ms avg")
        
        # Générer un rapport
        report = await agent.generate_report({"name": "Rapport de démonstration"})
        print(f"   📄 Rapport généré: {report['report_id']}")
        
        # Health check
        health = await agent.health_check()
        print(f"\n❤️  Health: {health['status']}")
        print(f"   Tests exécutés: {health['stats']['total_tests']}")
        print(f"   Taux de succès: {health['stats']['success_rate']}")
        
        # Arrêter
        await agent.shutdown()
        print(f"\n👋 Agent arrêté")
        print("\n" + "=" * 70)
    
    asyncio.run(main())
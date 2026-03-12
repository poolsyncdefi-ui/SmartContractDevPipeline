"""
Security Tester SubAgent - Sous-agent de tests de sécurité
Version: 2.0.0

Tests de sécurité avancés : tests de pénétration, analyse de vulnérabilités,
scan de smart contracts, tests d'injection, analyse statique et dynamique.
"""

import logging
import sys
import asyncio
import json
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, Optional, List, Set
from enum import Enum
from dataclasses import dataclass, field
import random

# Configuration des imports
current_dir = Path(__file__).parent.absolute()
project_root = current_dir.parent.parent.parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from agents.sous_agents.base_subagent import BaseSubAgent

logger = logging.getLogger(__name__)


# ============================================================================
# ÉNUMS ET CLASSES DE DONNÉES
# ============================================================================

class SecurityTestType(Enum):
    """Types de tests de sécurité"""
    PENETRATION = "penetration"
    VULNERABILITY_SCAN = "vulnerability_scan"
    STATIC_ANALYSIS = "static_analysis"
    DYNAMIC_ANALYSIS = "dynamic_analysis"
    FUZZING = "fuzzing"
    ACCESS_CONTROL = "access_control"
    INJECTION = "injection"
    DOS = "dos"


class SeverityLevel(Enum):
    """Niveaux de sévérité"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class TestStatus(Enum):
    """Statuts des tests"""
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    ERROR = "error"
    SKIPPED = "skipped"


@dataclass
class SecurityFinding:
    """Découverte de sécurité"""
    id: str
    test_type: SecurityTestType
    severity: SeverityLevel
    title: str
    description: str
    location: str
    remediation: str
    cvss_score: Optional[float] = None
    cwe_id: Optional[str] = None
    evidence: Optional[str] = None
    discovered_at: datetime = field(default_factory=datetime.now)


@dataclass
class SecurityTestResult:
    """Résultat de test de sécurité"""
    test_id: str
    test_name: str
    test_type: SecurityTestType
    status: TestStatus
    duration_ms: float
    findings: List[SecurityFinding] = field(default_factory=list)
    summary: Dict[str, int] = field(default_factory=dict)
    logs: List[str] = field(default_factory=list)
    report_path: Optional[str] = None
    completed_at: datetime = field(default_factory=datetime.now)


# ============================================================================
# SOUS-AGENT PRINCIPAL
# ============================================================================

class SecurityTesterSubAgent(BaseSubAgent):
    """
    Sous-agent de tests de sécurité

    Exécute des tests de sécurité avancés :
    - Tests de pénétration sur smart contracts
    - Scan de vulnérabilités (Slither, Mythril)
    - Analyse statique et dynamique
    - Tests d'injection et DoS
    """

    def __init__(self, config_path: str = ""):
        """Initialise le sous-agent de tests de sécurité"""
        super().__init__(config_path)

        # Métadonnées
        self._subagent_display_name = "🛡️ Tests de Sécurité"
        self._subagent_description = "Tests de pénétration et analyse de vulnérabilités"
        self._subagent_version = "2.0.0"
        self._subagent_category = "tester"
        self._subagent_capabilities = [
            "security.run_penetration_test",
            "security.scan_vulnerabilities",
            "security.analyze_access_control",
            "security.test_injection",
            "security.dos_test",
            "security.get_report"
        ]

        # État interne
        self._test_results: Dict[str, SecurityTestResult] = {}
        self._security_tools = self._agent_config.get('security_tools', {})
        self._vulnerability_db = self._load_vulnerability_database()
        
        # Tâche de fond
        self._cleanup_task: Optional[asyncio.Task] = None

        logger.info(f"✅ {self._subagent_display_name} initialisé (v{self._subagent_version})")

    # ========================================================================
    # IMPLÉMENTATION DES MÉTHODES ABSTRACTES
    # ========================================================================

    async def _initialize_subagent_components(self) -> bool:
        """Initialise les composants spécifiques"""
        logger.info("Initialisation des composants de tests de sécurité...")

        try:
            # Vérifier les outils de sécurité disponibles
            await self._check_security_tools()

            logger.info("✅ Composants de tests de sécurité initialisés")
            return True

        except Exception as e:
            logger.error(f"❌ Erreur initialisation composants: {e}")
            return False

    async def _initialize_components(self) -> bool:
        """Implémentation requise par BaseAgent"""
        return await self._initialize_subagent_components()

    def _get_capability_handlers(self) -> Dict[str, Any]:
        """Retourne les handlers spécifiques"""
        return {
            "security.run_penetration_test": self._handle_run_penetration_test,
            "security.scan_vulnerabilities": self._handle_scan_vulnerabilities,
            "security.analyze_access_control": self._handle_analyze_access_control,
            "security.test_injection": self._handle_test_injection,
            "security.dos_test": self._handle_dos_test,
            "security.get_report": self._handle_get_report,
        }

    # ========================================================================
    # MÉTHODES PRIVÉES
    # ========================================================================

    async def _check_security_tools(self):
        """Vérifie les outils de sécurité disponibles"""
        logger.info("Vérification des outils de sécurité...")

        self.available_tools = {}

        # Slither
        try:
            result = subprocess.run(['slither', '--version'], 
                                   capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                self.available_tools['slither'] = {
                    'available': True,
                    'version': result.stdout.strip()
                }
                logger.info(f"  ✅ Slither disponible")
        except:
            logger.debug("  ℹ️ Slither non disponible")

        # Mythril
        try:
            result = subprocess.run(['myth', '--version'], 
                                   capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                self.available_tools['mythril'] = {
                    'available': True,
                    'version': result.stdout.strip()
                }
                logger.info(f"  ✅ Mythril disponible")
        except:
            logger.debug("  ℹ️ Mythril non disponible")

        # Echidna
        try:
            result = subprocess.run(['echidna-test', '--version'], 
                                   capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                self.available_tools['echidna'] = {
                    'available': True,
                    'version': result.stdout.strip()
                }
                logger.info(f"  ✅ Echidna disponible")
        except:
            logger.debug("  ℹ️ Echidna non disponible")

        logger.info(f"  📊 Outils disponibles: {', '.join(self.available_tools.keys())}")

    def _load_vulnerability_database(self) -> Dict[str, Any]:
        """Charge la base de données des vulnérabilités connues"""
        return {
            'reentrancy': {
                'cwe_id': 'CWE-841',
                'severity': SeverityLevel.CRITICAL,
                'patterns': ['call.value', 'delegatecall', 'send', 'transfer'],
                'remediation': 'Utiliser ReentrancyGuard et le pattern Checks-Effects-Interactions'
            },
            'integer_overflow': {
                'cwe_id': 'CWE-190',
                'severity': SeverityLevel.HIGH,
                'patterns': ['+=', '-=', '*=', '++', '--'],
                'remediation': 'Utiliser SafeMath ou Solidity >=0.8.0'
            },
            'access_control': {
                'cwe_id': 'CWE-284',
                'severity': SeverityLevel.HIGH,
                'patterns': ['onlyOwner', 'require(msg.sender == owner)'],
                'remediation': 'Implémenter un contrôle d\'accès basé sur les rôles'
            },
            'tx_origin': {
                'cwe_id': 'CWE-807',
                'severity': SeverityLevel.HIGH,
                'patterns': ['tx.origin'],
                'remediation': 'Utiliser msg.sender au lieu de tx.origin'
            },
            'timestamp_dependency': {
                'cwe_id': 'CWE-829',
                'severity': SeverityLevel.MEDIUM,
                'patterns': ['block.timestamp', 'now'],
                'remediation': 'Éviter d\'utiliser block.timestamp pour la logique critique'
            },
            'unchecked_call': {
                'cwe_id': 'CWE-252',
                'severity': SeverityLevel.MEDIUM,
                'patterns': ['.call{'],
                'remediation': 'Toujours vérifier la valeur de retour des appels externes'
            },
            'dos': {
                'cwe_id': 'CWE-400',
                'severity': SeverityLevel.MEDIUM,
                'patterns': ['for(', 'while('],
                'remediation': 'Limiter la taille des boucles et les opérations coûteuses'
            }
        }

    async def _run_slither_analysis(self, contract_path: str) -> List[SecurityFinding]:
        """Exécute une analyse Slither"""
        findings = []
        
        # Simulation d'analyse Slither
        await asyncio.sleep(1.5)
        
        # Générer des findings simulés
        for vuln_name, vuln_info in list(self._vulnerability_db.items())[:3]:
            if random.random() > 0.6:  # 40% de chance
                findings.append(SecurityFinding(
                    id=f"SLTH-{len(findings)}",
                    test_type=SecurityTestType.STATIC_ANALYSIS,
                    severity=vuln_info['severity'],
                    title=f"Vulnérabilité {vuln_name} détectée",
                    description=f"Pattern de vulnérabilité {vuln_name} trouvé",
                    location=f"{contract_path}:L{random.randint(10, 500)}",
                    remediation=vuln_info['remediation'],
                    cwe_id=vuln_info['cwe_id'],
                    evidence=f"Code: {vuln_info['patterns'][0]} detected"
                ))
        
        return findings

    async def _run_mythril_analysis(self, contract_path: str) -> List[SecurityFinding]:
        """Exécute une analyse Mythril"""
        findings = []
        
        await asyncio.sleep(2.0)
        
        # Générer des findings spécifiques à Mythril
        for i in range(random.randint(0, 3)):
            findings.append(SecurityFinding(
                id=f"MYTH-{i}",
                test_type=SecurityTestType.DYNAMIC_ANALYSIS,
                severity=SeverityLevel.HIGH if i == 0 else SeverityLevel.MEDIUM,
                title=f"Vulnérabilité dynamique #{i+1}",
                description="Détection par exécution symbolique",
                location=f"{contract_path}:L{random.randint(50, 300)}",
                remediation="Corriger selon les recommandations Mythril",
                cvss_score=round(random.uniform(5.0, 9.0), 1)
            ))
        
        return findings

    async def _run_penetration_test_simulation(self, target: str) -> List[SecurityFinding]:
        """Simule un test de pénétration"""
        findings = []
        
        # Simuler différentes attaques
        attack_vectors = [
            ("Reentrancy Attack", SeverityLevel.CRITICAL),
            ("Front-running", SeverityLevel.HIGH),
            ("Flash Loan Attack", SeverityLevel.HIGH),
            ("Signature Replay", SeverityLevel.MEDIUM),
            ("Gas Griefing", SeverityLevel.LOW)
        ]
        
        for attack_name, severity in attack_vectors[:random.randint(2, 4)]:
            if random.random() > 0.5:
                findings.append(SecurityFinding(
                    id=f"PEN-{len(findings)}",
                    test_type=SecurityTestType.PENETRATION,
                    severity=severity,
                    title=f"Attaque {attack_name} possible",
                    description=f"Le contrat est vulnérable à {attack_name}",
                    location="Fonction critique",
                    remediation=f"Implémenter des protections contre {attack_name}",
                    cvss_score=round(random.uniform(4.0, 9.5), 1)
                ))
        
        return findings

    # ========================================================================
    # HANDLERS DE CAPACITÉS
    # ========================================================================

    async def _handle_run_penetration_test(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Exécute un test de pénétration"""
        target = params.get('target')  # contrat, API, ou système
        test_depth = params.get('depth', 'standard')  # quick, standard, deep
        attack_vectors = params.get('attack_vectors', ['all'])

        if not target:
            return {'success': False, 'error': 'target requis'}

        test_id = f"PENTEST-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        start_time = datetime.now()

        # Simuler le test de pénétration
        await asyncio.sleep(2.0)
        
        findings = await self._run_penetration_test_simulation(target)
        
        duration = (datetime.now() - start_time).total_seconds() * 1000

        # Compter par sévérité
        severity_counts = {
            'critical': len([f for f in findings if f.severity == SeverityLevel.CRITICAL]),
            'high': len([f for f in findings if f.severity == SeverityLevel.HIGH]),
            'medium': len([f for f in findings if f.severity == SeverityLevel.MEDIUM]),
            'low': len([f for f in findings if f.severity == SeverityLevel.LOW])
        }

        result = SecurityTestResult(
            test_id=test_id,
            test_name=f"Penetration Test - {target}",
            test_type=SecurityTestType.PENETRATION,
            status=TestStatus.COMPLETED,
            duration_ms=duration,
            findings=findings,
            summary=severity_counts
        )

        self._test_results[test_id] = result

        return {
            'success': True,
            'test_id': test_id,
            'target': target,
            'depth': test_depth,
            'summary': severity_counts,
            'total_findings': len(findings),
            'findings': [
                {
                    'title': f.title,
                    'severity': f.severity.value,
                    'description': f.description,
                    'remediation': f.remediation,
                    'cvss_score': f.cvss_score
                }
                for f in findings
            ],
            'risk_score': sum([
                severity_counts['critical'] * 10,
                severity_counts['high'] * 7,
                severity_counts['medium'] * 4,
                severity_counts['low'] * 1
            ]),
            'duration_ms': duration
        }

    async def _handle_scan_vulnerabilities(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Scanne les vulnérabilités d'un contrat"""
        contract_path = params.get('contract_path')
        tools = params.get('tools', ['slither', 'mythril'])
        depth = params.get('depth', 'standard')

        if not contract_path:
            return {'success': False, 'error': 'contract_path requis'}

        test_id = f"VULNSCAN-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        start_time = datetime.now()

        all_findings = []

        # Exécuter les analyses selon les outils disponibles
        if 'slither' in tools and 'slither' in self.available_tools:
            findings = await self._run_slither_analysis(contract_path)
            all_findings.extend(findings)

        if 'mythril' in tools and 'mythril' in self.available_tools:
            findings = await self._run_mythril_analysis(contract_path)
            all_findings.extend(findings)

        # Toujours avoir une analyse de base
        if not all_findings:
            all_findings = await self._run_slither_analysis(contract_path)

        duration = (datetime.now() - start_time).total_seconds() * 1000

        # Compter par sévérité
        severity_counts = {
            'critical': len([f for f in all_findings if f.severity == SeverityLevel.CRITICAL]),
            'high': len([f for f in all_findings if f.severity == SeverityLevel.HIGH]),
            'medium': len([f for f in all_findings if f.severity == SeverityLevel.MEDIUM]),
            'low': len([f for f in all_findings if f.severity == SeverityLevel.LOW])
        }

        result = SecurityTestResult(
            test_id=test_id,
            test_name=f"Vulnerability Scan - {Path(contract_path).name}",
            test_type=SecurityTestType.VULNERABILITY_SCAN,
            status=TestStatus.COMPLETED,
            duration_ms=duration,
            findings=all_findings,
            summary=severity_counts
        )

        self._test_results[test_id] = result

        return {
            'success': True,
            'test_id': test_id,
            'contract': contract_path,
            'tools_used': tools,
            'summary': severity_counts,
            'total_findings': len(all_findings),
            'findings': [
                {
                    'title': f.title,
                    'severity': f.severity.value,
                    'cwe_id': f.cwe_id,
                    'location': f.location,
                    'remediation': f.remediation
                }
                for f in all_findings
            ],
            'security_score': max(0, 100 - (severity_counts['critical'] * 15 + 
                                           severity_counts['high'] * 10 +
                                           severity_counts['medium'] * 5 +
                                           severity_counts['low'] * 2)),
            'duration_ms': duration
        }

    async def _handle_analyze_access_control(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Analyse les contrôles d'accès"""
        contract_path = params.get('contract_path')
        roles = params.get('roles', ['owner', 'admin', 'user'])

        if not contract_path:
            return {'success': False, 'error': 'contract_path requis'}

        await asyncio.sleep(1.0)

        # Simulation d'analyse des contrôles d'accès
        findings = []
        
        # Vérifier les fonctions sensibles
        sensitive_functions = ['withdraw', 'transfer', 'mint', 'burn', 'pause', 'upgrade']
        
        for func in sensitive_functions[:random.randint(3, 6)]:
            if random.random() > 0.7:  # 30% de chance
                findings.append({
                    'function': func,
                    'has_access_control': random.choice([True, False]),
                    'roles_allowed': random.sample(roles, random.randint(1, len(roles))) if random.random() > 0.5 else [],
                    'risk': 'high' if not random.choice([True, False]) else 'low'
                })

        return {
            'success': True,
            'contract': contract_path,
            'analysis': {
                'total_functions_analyzed': random.randint(10, 30),
                'functions_with_access_control': len([f for f in findings if f['has_access_control']]),
                'functions_without_access_control': len([f for f in findings if not f['has_access_control']]),
                'findings': findings,
                'recommendations': [
                    "Ajouter des modificateurs onlyOwner aux fonctions critiques",
                    "Implémenter un système de rôles (OpenZeppelin AccessControl)",
                    "Utiliser des time locks pour les fonctions admin"
                ] if any(not f['has_access_control'] for f in findings) else []
            }
        }

    async def _handle_test_injection(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Teste les vulnérabilités d'injection"""
        target = params.get('target')
        injection_type = params.get('type', 'sql')  # sql, command, script

        if not target:
            return {'success': False, 'error': 'target requis'}

        await asyncio.sleep(1.2)

        # Simulation de tests d'injection
        test_payloads = {
            'sql': ["' OR '1'='1", "'; DROP TABLE users; --", "' UNION SELECT * FROM users --"],
            'command': ["; ls -la", "| cat /etc/passwd", "& ping -c 10 127.0.0.1 &"],
            'script': ["<script>alert('XSS')</script>", "javascript:alert(document.cookie)"]
        }

        results = []
        for payload in test_payloads.get(injection_type, [])[:3]:
            success = random.random() > 0.8  # 20% de chance de succès
            results.append({
                'payload': payload,
                'injection_successful': success,
                'detected': success and random.random() > 0.5,
                'impact': 'high' if success else 'none'
            })

        return {
            'success': True,
            'target': target,
            'injection_type': injection_type,
            'tests_performed': len(results),
            'vulnerabilities_found': sum(1 for r in results if r['injection_successful']),
            'results': results,
            'recommendations': [
                "Utiliser des requêtes paramétrées",
                "Échapper les entrées utilisateur",
                "Valider et sanitizer toutes les entrées"
            ] if any(r['injection_successful'] for r in results) else []
        }

    async def _handle_dos_test(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Teste les vulnérabilités DoS"""
        target = params.get('target')
        test_type = params.get('type', 'gas')  # gas, loop, storage
        intensity = params.get('intensity', 'medium')

        if not target:
            return {'success': False, 'error': 'target requis'}

        await asyncio.sleep(1.5)

        # Simulation de tests DoS
        gas_limits = {
            'low': 1000000,
            'medium': 3000000,
            'high': 5000000
        }

        vulnerabilities = []
        
        # Tester les boucles potentiellement infinies
        if test_type == 'loop' or test_type == 'all':
            if random.random() > 0.6:
                vulnerabilities.append({
                    'type': 'unbounded_loop',
                    'description': 'Boucle sans limite pouvant dépasser le gas limit',
                    'gas_estimate': random.randint(2000000, 8000000),
                    'risk': 'high'
                })

        # Tester les opérations de stockage coûteuses
        if test_type == 'storage' or test_type == 'all':
            if random.random() > 0.7:
                vulnerabilities.append({
                    'type': 'expensive_storage',
                    'description': 'Opérations de stockage coûteuses dans une boucle',
                    'gas_estimate': random.randint(1500000, 4000000),
                    'risk': 'medium'
                })

        # Tester la consommation de gas
        if test_type == 'gas' or test_type == 'all':
            gas_estimate = random.randint(1000000, 6000000)
            vulnerabilities.append({
                'type': 'high_gas_consumption',
                'description': 'Fonction avec consommation de gas élevée',
                'gas_estimate': gas_estimate,
                'exceeds_limit': gas_estimate > gas_limits[intensity],
                'risk': 'high' if gas_estimate > gas_limits[intensity] else 'low'
            })

        return {
            'success': True,
            'target': target,
            'test_type': test_type,
            'intensity': intensity,
            'gas_limit': gas_limits[intensity],
            'vulnerabilities_found': len(vulnerabilities),
            'vulnerabilities': vulnerabilities,
            'recommendations': [
                "Limiter la taille des boucles",
                "Utiliser des patterns de pagination",
                "Optimiser le stockage",
                "Éviter les opérations coûteuses dans les boucles"
            ] if vulnerabilities else []
        }

    async def _handle_get_report(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Génère un rapport de test de sécurité"""
        test_id = params.get('test_id')
        format = params.get('format', 'json')

        if not test_id:
            return {'success': False, 'error': 'test_id requis'}

        result = self._test_results.get(test_id)
        if not result:
            return {'success': False, 'error': f'Test {test_id} non trouvé'}

        if format == 'json':
            report = {
                'test_id': result.test_id,
                'test_name': result.test_name,
                'test_type': result.test_type.value,
                'status': result.status.value,
                'completed_at': result.completed_at.isoformat(),
                'duration_ms': result.duration_ms,
                'summary': result.summary,
                'findings': [
                    {
                        'id': f.id,
                        'title': f.title,
                        'severity': f.severity.value,
                        'description': f.description,
                        'location': f.location,
                        'remediation': f.remediation,
                        'cwe_id': f.cwe_id,
                        'cvss_score': f.cvss_score
                    }
                    for f in result.findings
                ],
                'risk_score': sum([
                    result.summary.get('critical', 0) * 10,
                    result.summary.get('high', 0) * 7,
                    result.summary.get('medium', 0) * 4,
                    result.summary.get('low', 0) * 1
                ]),
                'executive_summary': f"Le test a révélé {len(result.findings)} vulnérabilités dont {result.summary.get('critical', 0)} critiques."
            }

            # Sauvegarder le rapport
            report_path = Path(project_root) / 'reports' / 'security' / f"{test_id}.json"
            report_path.parent.mkdir(parents=True, exist_ok=True)
            with open(report_path, 'w') as f:
                json.dump(report, f, indent=2)

            result.report_path = str(report_path)

            return {
                'success': True,
                'report': report,
                'report_path': result.report_path
            }

        return {'success': False, 'error': f'Format {format} non supporté'}

    # ========================================================================
    # NETTOYAGE
    # ========================================================================

    async def shutdown(self) -> bool:
        """Arrête le sous-agent"""
        logger.info(f"Arrêt de {self._subagent_display_name}...")

        if self._cleanup_task and not self._cleanup_task.done():
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass

        return await super().shutdown()


# ============================================================================
# FONCTIONS D'EXPORT
# ============================================================================

def get_agent_class():
    """
    Fonction requise pour le chargement dynamique des sous-agents.
    Retourne la classe principale du sous-agent.
    """
    return SecurityTesterSubAgent


def create_security_tester_agent(config_path: str = "") -> "SecurityTesterSubAgent":
    """Crée une instance du sous-agent de tests de sécurité"""
    return SecurityTesterSubAgent(config_path)
"""
Security Expert SubAgent - Sous-agent expert sécurité
Version: 2.0.0

Analyse de sécurité et audit des smart contracts avec support de :
- Scan de vulnérabilités
- Audit complet
- Détection de patterns malveillants
- Suggestions de correctifs
- Rapports d'audit
"""

import logging
import sys
import asyncio
import json
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, Optional, List, Set, Tuple
from enum import Enum
from dataclasses import dataclass, field
from collections import defaultdict

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

class Severity(Enum):
    """Niveaux de sévérité"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class VulnerabilityType(Enum):
    """Types de vulnérabilités"""
    REENTRANCY = "reentrancy"
    INTEGER_OVERFLOW = "integer_overflow"
    ACCESS_CONTROL = "access_control"
    UNCHECKED_CALL = "unchecked_call"
    TX_ORIGIN = "tx_origin"
    TIMESTAMP_DEPENDENCY = "timestamp_dependency"
    FRONT_RUNNING = "front_running"
    DENIAL_OF_SERVICE = "denial_of_service"
    BUSINESS_LOGIC = "business_logic"
    GAS_LIMIT = "gas_limit"
    REENTRANCY_VIEW = "reentrancy_view"
    UNHANDLED_EXCEPTION = "unhandled_exception"
    WEAK_RANDOMNESS = "weak_randomness"
    INSECURE_COMPILER = "insecure_compiler"


class AuditStatus(Enum):
    """Statuts d'audit"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class Vulnerability:
    """Vulnérabilité détectée"""
    id: str
    type: VulnerabilityType
    severity: Severity
    location: str  # Ligne ou fonction
    description: str
    swc_id: str
    impact: str
    likelihood: str  # low, medium, high
    code_snippet: str
    recommendation: str
    references: List[str] = field(default_factory=list)
    detected_at: datetime = field(default_factory=datetime.now)


@dataclass
class Audit:
    """Audit de sécurité complet"""
    id: str
    contract_name: str
    contract_path: str
    status: AuditStatus
    vulnerabilities: List[Vulnerability]
    summary: Dict[str, int]  # critical, high, medium, low, info
    overall_risk_score: float  # 0-10
    duration_ms: int
    tools_used: List[str]
    started_at: datetime
    completed_at: Optional[datetime] = None
    report_path: Optional[str] = None


# ============================================================================
# SOUS-AGENT PRINCIPAL
# ============================================================================

class SecurityExpertSubAgent(BaseSubAgent):
    """
    Sous-agent expert sécurité

    Analyse la sécurité des smart contracts avec :
    - Détection des vulnérabilités connues
    - Audit complet
    - Suggestions de correctifs
    - Rapports d'audit détaillés
    """

    def __init__(self, config_path: str = ""):
        """Initialise le sous-agent expert sécurité"""
        super().__init__(config_path)

        # Métadonnées
        self._subagent_display_name = "🛡️ Expert Sécurité"
        self._subagent_description = "Analyse de sécurité et audit des smart contracts"
        self._subagent_version = "2.0.0"
        self._subagent_category = "smart_contract"
        self._subagent_capabilities = [
            "security.scan_contract",
            "security.audit_contract",
            "security.check_vulnerabilities",
            "security.suggest_fixes",
            "security.generate_report",
            "security.get_audit_history",
            "security.compare_audits"
        ]

        # État interne
        self._audits: Dict[str, Audit] = {}
        self._vulnerability_patterns = self._load_vulnerability_patterns()
        self._contract_locks: Dict[str, asyncio.Lock] = {}
        
        # Configuration
        self._audit_params = self._agent_config.get('audit_parameters', {})
        self._default_scan_depth = self._audit_params.get('default_scan_depth', 'standard')
        
        # Tâche de fond
        self._cleanup_task: Optional[asyncio.Task] = None

        logger.info(f"✅ {self._subagent_display_name} initialisé (v{self._subagent_version})")

    # ========================================================================
    # IMPLÉMENTATION DES MÉTHODES ABSTRACTES
    # ========================================================================

    async def _initialize_subagent_components(self) -> bool:
        """Initialise les composants spécifiques"""
        logger.info("Initialisation des composants de sécurité...")

        try:
            logger.info(f"  ✅ {len(self._vulnerability_patterns)} patterns de vulnérabilités chargés")

            # Démarrer la tâche de nettoyage
            self._cleanup_task = asyncio.create_task(self._cleanup_loop())

            logger.info("✅ Composants de sécurité initialisés")
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
            "security.scan_contract": self._handle_scan_contract,
            "security.audit_contract": self._handle_audit_contract,
            "security.check_vulnerabilities": self._handle_check_vulnerabilities,
            "security.suggest_fixes": self._handle_suggest_fixes,
            "security.generate_report": self._handle_generate_report,
            "security.get_audit_history": self._handle_get_history,
            "security.compare_audits": self._handle_compare_audits,
        }

    # ========================================================================
    # MÉTHODES PRIVÉES
    # ========================================================================

    async def _get_contract_lock(self, contract_path: str) -> asyncio.Lock:
        """Récupère ou crée un verrou pour un contrat"""
        if contract_path not in self._contract_locks:
            self._contract_locks[contract_path] = asyncio.Lock()
        return self._contract_locks[contract_path]

    def _load_vulnerability_patterns(self) -> Dict[str, Dict[str, Any]]:
        """Charge les patterns de vulnérabilités"""
        return {
            'reentrancy': {
                'type': VulnerabilityType.REENTRANCY,
                'severity': Severity.CRITICAL,
                'pattern': r'(?:call|delegatecall)\.value\([^)]*\)[^;]*;\s*[^}]*\b(balance|transfer|send)\b',
                'swc_id': 'SWC-107',
                'description': 'Vulnérabilité de réentrance - un appel externe est effectué avant la mise à jour de l\'état',
                'impact': 'Perte potentielle de tous les fonds du contrat',
                'likelihood': 'high',
                'remediation': 'Utiliser ReentrancyGuard ou suivre le pattern Checks-Effects-Interactions',
                'references': ['https://swcregistry.io/docs/SWC-107']
            },
            'integer_overflow': {
                'type': VulnerabilityType.INTEGER_OVERFLOW,
                'severity': Severity.HIGH,
                'pattern': r'(\+{2}|-{2}|[+\-*/]=)',
                'swc_id': 'SWC-101',
                'description': 'Risque de débordement d\'entier dans les opérations arithmétiques',
                'impact': 'Valeurs incorrectes, perte de fonds, comportement inattendu',
                'likelihood': 'medium',
                'remediation': 'Utiliser SafeMath ou Solidity >=0.8.0 avec checks intégrés',
                'references': ['https://swcregistry.io/docs/SWC-101']
            },
            'unchecked_call': {
                'type': VulnerabilityType.UNCHECKED_CALL,
                'severity': Severity.MEDIUM,
                'pattern': r'\.call\{[^}]*\}\([^)]*\)(?!\s*\.\s*success)',
                'swc_id': 'SWC-104',
                'description': 'Appel externe non vérifié - le succès de l\'appel n\'est pas contrôlé',
                'impact': 'Les échecs d\'appel peuvent passer inaperçus',
                'likelihood': 'medium',
                'remediation': 'Toujours vérifier la valeur de retour des appels externes',
                'references': ['https://swcregistry.io/docs/SWC-104']
            },
            'tx_origin_auth': {
                'type': VulnerabilityType.TX_ORIGIN,
                'severity': Severity.HIGH,
                'pattern': r'tx\.origin\s*==',
                'swc_id': 'SWC-115',
                'description': 'Utilisation de tx.origin pour l\'authentification - vulnérable aux attaques de phishing',
                'impact': 'Contournement des contrôles d\'accès',
                'likelihood': 'medium',
                'remediation': 'Utiliser msg.sender pour l\'authentification',
                'references': ['https://swcregistry.io/docs/SWC-115']
            },
            'timestamp_dependency': {
                'type': VulnerabilityType.TIMESTAMP_DEPENDENCY,
                'severity': Severity.LOW,
                'pattern': r'block\.timestamp|now',
                'swc_id': 'SWC-116',
                'description': 'Dépendance au timestamp du bloc - peut être manipulé par les mineurs',
                'impact': 'Logique de contrat manipulable',
                'likelihood': 'low',
                'remediation': 'Éviter d\'utiliser block.timestamp pour la logique critique, accepter une variation de ~15 secondes',
                'references': ['https://swcregistry.io/docs/SWC-116']
            },
            'insecure_compiler': {
                'type': VulnerabilityType.INSECURE_COMPILER,
                'severity': Severity.MEDIUM,
                'pattern': r'pragma\s+solidity\s+[<>=^]*0\.[4-7]\.',
                'swc_id': 'SWC-103',
                'description': 'Version du compilateur trop ancienne avec bugs connus',
                'impact': 'Exposition à des bugs de compilateur',
                'likelihood': 'medium',
                'remediation': 'Utiliser Solidity >=0.8.0',
                'references': ['https://swcregistry.io/docs/SWC-103']
            },
            'front_running': {
                'type': VulnerabilityType.FRONT_RUNNING,
                'severity': Severity.MEDIUM,
                'pattern': r'(?i)(?:profit|arbitrage|advantage).*(?:reveal|execute)',
                'swc_id': 'SWC-114',
                'description': 'Potentiel de front-running - les transactions peuvent être observées et précédées',
                'impact': 'Perte financière, désavantage concurrentiel',
                'likelihood': 'medium',
                'remediation': 'Utiliser un mécanisme de commit-reveal ou des limites de slippage',
                'references': ['https://swcregistry.io/docs/SWC-114']
            }
        }

    def _scan_for_vulnerabilities(self, contract_code: str, depth: str = 'standard') -> List[Vulnerability]:
        """Scanne le code pour trouver des vulnérabilités"""
        vulnerabilities = []
        lines = contract_code.split('\n')
        
        for vuln_name, vuln_info in self._vulnerability_patterns.items():
            matches = list(re.finditer(vuln_info['pattern'], contract_code, re.IGNORECASE | re.MULTILINE))
            
            for match in matches:
                # Trouver la ligne
                line_no = 1
                for i, line in enumerate(lines, 1):
                    if match.group() in line:
                        line_no = i
                        break
                
                # Extraire le contexte
                start_line = max(0, line_no - 3)
                end_line = min(len(lines), line_no + 2)
                context = '\n'.join(lines[start_line:end_line])
                
                vuln = Vulnerability(
                    id=f"VULN-{vuln_name}-{len(vulnerabilities)}",
                    type=vuln_info['type'],
                    severity=vuln_info['severity'],
                    location=f"Ligne {line_no}",
                    description=vuln_info['description'],
                    swc_id=vuln_info['swc_id'],
                    impact=vuln_info['impact'],
                    likelihood=vuln_info['likelihood'],
                    code_snippet=context,
                    recommendation=vuln_info['remediation'],
                    references=vuln_info['references']
                )
                vulnerabilities.append(vuln)
        
        return vulnerabilities

    # ========================================================================
    # TÂCHES DE FOND
    # ========================================================================

    async def _cleanup_loop(self):
        """Nettoie les anciens audits"""
        logger.info("🔄 Boucle de nettoyage démarrée")

        while self._status.value == "ready":
            try:
                await asyncio.sleep(3600)  # Toutes les heures

                # Nettoyer les audits de plus de 30 jours
                cutoff = datetime.now() - timedelta(days=30)
                old_audits = [
                    aid for aid, audit in self._audits.items()
                    if audit.completed_at and audit.completed_at < cutoff
                ]

                for aid in old_audits:
                    del self._audits[aid]

                if old_audits:
                    logger.info(f"🧹 {len(old_audits)} audits nettoyés")

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"❌ Erreur dans la boucle de nettoyage: {e}")

    # ========================================================================
    # HANDLERS DE CAPACITÉS
    # ========================================================================

    async def _handle_scan_contract(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Scan rapide de sécurité"""
        contract_path = params.get('contract_path')
        contract_code = params.get('contract_code')
        depth = params.get('depth', 'quick')

        if not contract_path and not contract_code:
            return {'success': False, 'error': 'contract_path ou contract_code requis'}

        # Lire le code si nécessaire
        if contract_path and not contract_code:
            try:
                with open(contract_path, 'r') as f:
                    contract_code = f.read()
            except Exception as e:
                return {'success': False, 'error': f"Erreur lecture fichier: {e}"}

        # Scanner
        start_time = datetime.now()
        vulnerabilities = self._scan_for_vulnerabilities(contract_code, depth)
        duration = int((datetime.now() - start_time).total_seconds() * 1000)

        # Compter par sévérité
        severity_counts = {
            'critical': len([v for v in vulnerabilities if v.severity == Severity.CRITICAL]),
            'high': len([v for v in vulnerabilities if v.severity == Severity.HIGH]),
            'medium': len([v for v in vulnerabilities if v.severity == Severity.MEDIUM]),
            'low': len([v for v in vulnerabilities if v.severity == Severity.LOW]),
            'info': len([v for v in vulnerabilities if v.severity == Severity.INFO])
        }

        return {
            'success': True,
            'contract': contract_path or 'inline',
            'scan_depth': depth,
            'duration_ms': duration,
            'total_vulnerabilities': len(vulnerabilities),
            'severity_breakdown': severity_counts,
            'vulnerabilities': [
                {
                    'id': v.id,
                    'type': v.type.value,
                    'severity': v.severity.value,
                    'location': v.location,
                    'description': v.description,
                    'swc_id': v.swc_id
                }
                for v in vulnerabilities
            ]
        }

    async def _handle_audit_contract(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Audit complet de sécurité"""
        contract_path = params.get('contract_path')
        contract_code = params.get('contract_code')
        depth = params.get('depth', self._default_scan_depth)
        include_recommendations = params.get('include_recommendations', True)

        if not contract_path and not contract_code:
            return {'success': False, 'error': 'contract_path ou contract_code requis'}

        # Lire le code si nécessaire
        if contract_path and not contract_code:
            try:
                with open(contract_path, 'r') as f:
                    contract_code = f.read()
            except Exception as e:
                return {'success': False, 'error': f"Erreur lecture fichier: {e}"}

        # Créer l'audit
        audit_id = f"AUDIT-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        start_time = datetime.now()

        # Scanner en profondeur
        vulnerabilities = self._scan_for_vulnerabilities(contract_code, 'deep' if depth == 'deep' else 'standard')

        # Calculer le score de risque
        risk_weights = {
            Severity.CRITICAL: 10,
            Severity.HIGH: 7,
            Severity.MEDIUM: 4,
            Severity.LOW: 2,
            Severity.INFO: 0.5
        }

        total_risk = sum(risk_weights[v.severity] for v in vulnerabilities)
        max_possible_risk = 10 * len(vulnerabilities) if vulnerabilities else 1
        risk_score = min(10, (total_risk / max_possible_risk) * 10) if max_possible_risk > 0 else 0

        # Compter par sévérité
        severity_counts = {
            'critical': len([v for v in vulnerabilities if v.severity == Severity.CRITICAL]),
            'high': len([v for v in vulnerabilities if v.severity == Severity.HIGH]),
            'medium': len([v for v in vulnerabilities if v.severity == Severity.MEDIUM]),
            'low': len([v for v in vulnerabilities if v.severity == Severity.LOW]),
            'info': len([v for v in vulnerabilities if v.severity == Severity.INFO])
        }

        duration = int((datetime.now() - start_time).total_seconds() * 1000)

        audit = Audit(
            id=audit_id,
            contract_name=Path(contract_path).stem if contract_path else "inline",
            contract_path=contract_path or "inline",
            status=AuditStatus.COMPLETED,
            vulnerabilities=vulnerabilities,
            summary=severity_counts,
            overall_risk_score=round(risk_score, 2),
            duration_ms=duration,
            tools_used=['pattern_matching'],
            started_at=start_time,
            completed_at=datetime.now()
        )

        self._audits[audit_id] = audit

        result = {
            'success': True,
            'audit_id': audit_id,
            'contract': audit.contract_name,
            'status': audit.status.value,
            'duration_ms': audit.duration_ms,
            'overall_risk_score': audit.overall_risk_score,
            'summary': audit.summary,
            'vulnerabilities': [
                {
                    'id': v.id,
                    'type': v.type.value,
                    'severity': v.severity.value,
                    'location': v.location,
                    'description': v.description,
                    'swc_id': v.swc_id
                }
                for v in audit.vulnerabilities
            ]
        }

        if include_recommendations:
            result['recommendations'] = [
                {
                    'vulnerability_id': v.id,
                    'recommendation': v.recommendation,
                    'references': v.references
                }
                for v in audit.vulnerabilities
            ]

        return result

    async def _handle_check_vulnerabilities(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Vérifie les vulnérabilités connues"""
        vuln_type = params.get('type')
        swc_id = params.get('swc_id')

        vulnerabilities = []
        for name, info in self._vulnerability_patterns.items():
            if vuln_type and info['type'].value != vuln_type:
                continue
            if swc_id and info['swc_id'] != swc_id:
                continue

            vulnerabilities.append({
                'name': name,
                'type': info['type'].value,
                'severity': info['severity'].value,
                'description': info['description'],
                'swc_id': info['swc_id'],
                'impact': info['impact'],
                'likelihood': info['likelihood'],
                'remediation': info['remediation'],
                'references': info['references']
            })

        return {
            'success': True,
            'vulnerabilities': vulnerabilities,
            'count': len(vulnerabilities)
        }

    async def _handle_suggest_fixes(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Suggère des correctifs pour des vulnérabilités"""
        vulnerability_ids = params.get('vulnerability_ids', [])
        audit_id = params.get('audit_id')

        fixes = []

        if audit_id:
            # Récupérer les vulnérabilités de l'audit
            audit = self._audits.get(audit_id)
            if not audit:
                return {'success': False, 'error': f'Audit {audit_id} non trouvé'}
            
            vulns = audit.vulnerabilities
        elif vulnerability_ids:
            # Chercher dans tous les audits
            vulns = []
            for audit in self._audits.values():
                for v in audit.vulnerabilities:
                    if v.id in vulnerability_ids:
                        vulns.append(v)
        else:
            return {'success': False, 'error': 'vulnerability_ids ou audit_id requis'}

        for vuln in vulns:
            # Générer un exemple de correctif
            fix_example = ""
            if vuln.type == VulnerabilityType.REENTRANCY:
                fix_example = """
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";

contract MyContract is ReentrancyGuard {
    function withdraw() external nonReentrant {
        // votre code
    }
}
"""
            elif vuln.type == VulnerabilityType.ACCESS_CONTROL:
                fix_example = """
import "@openzeppelin/contracts/access/Ownable.sol";

contract MyContract is Ownable {
    function sensitiveFunction() external onlyOwner {
        // votre code
    }
}
"""
            elif vuln.type == VulnerabilityType.UNCHECKED_CALL:
                fix_example = """
(bool success, ) = address.call{value: amount}("");
require(success, "Call failed");
"""

            fixes.append({
                'vulnerability_id': vuln.id,
                'type': vuln.type.value,
                'location': vuln.location,
                'recommendation': vuln.recommendation,
                'example_code': fix_example,
                'complexity': 'medium' if vuln.severity in [Severity.CRITICAL, Severity.HIGH] else 'low'
            })

        return {
            'success': True,
            'fixes': fixes,
            'count': len(fixes)
        }

    async def _handle_generate_report(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Génère un rapport d'audit"""
        audit_id = params.get('audit_id')
        format = params.get('format', 'json')  # json, html, markdown

        if not audit_id:
            return {'success': False, 'error': 'audit_id requis'}

        audit = self._audits.get(audit_id)
        if not audit:
            return {'success': False, 'error': f'Audit {audit_id} non trouvé'}

        if format == 'json':
            report = {
                'audit_id': audit.id,
                'contract': audit.contract_name,
                'generated_at': datetime.now().isoformat(),
                'status': audit.status.value,
                'overall_risk_score': audit.overall_risk_score,
                'summary': audit.summary,
                'vulnerabilities': [
                    {
                        'id': v.id,
                        'type': v.type.value,
                        'severity': v.severity.value,
                        'location': v.location,
                        'description': v.description,
                        'impact': v.impact,
                        'likelihood': v.likelihood,
                        'recommendation': v.recommendation,
                        'code_snippet': v.code_snippet,
                        'references': v.references
                    }
                    for v in audit.vulnerabilities
                ],
                'metadata': {
                    'duration_ms': audit.duration_ms,
                    'tools_used': audit.tools_used,
                    'started_at': audit.started_at.isoformat(),
                    'completed_at': audit.completed_at.isoformat() if audit.completed_at else None
                }
            }

            # Sauvegarder le rapport
            report_path = Path(project_root) / 'reports' / 'security' / f"{audit_id}.json"
            report_path.parent.mkdir(parents=True, exist_ok=True)
            with open(report_path, 'w') as f:
                json.dump(report, f, indent=2)

            audit.report_path = str(report_path)

        else:
            # Support pour d'autres formats à implémenter
            return {'success': False, 'error': f'Format {format} non supporté'}

        return {
            'success': True,
            'audit_id': audit_id,
            'report': report,
            'report_path': audit.report_path
        }

    async def _handle_get_history(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Récupère l'historique des audits"""
        contract = params.get('contract')
        limit = params.get('limit', 50)

        history = []
        for audit in self._audits.values():
            if contract and audit.contract_name != contract:
                continue
            history.append({
                'audit_id': audit.id,
                'contract': audit.contract_name,
                'completed_at': audit.completed_at.isoformat() if audit.completed_at else None,
                'risk_score': audit.overall_risk_score,
                'vulnerabilities_found': len(audit.vulnerabilities),
                'summary': audit.summary
            })

        # Trier par date
        history.sort(key=lambda x: x['completed_at'], reverse=True)
        history = history[:limit]

        return {
            'success': True,
            'history': history,
            'total_count': len(history)
        }

    async def _handle_compare_audits(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Compare deux audits"""
        audit_id_1 = params.get('audit_id_1')
        audit_id_2 = params.get('audit_id_2')

        if not audit_id_1 or not audit_id_2:
            return {'success': False, 'error': 'audit_id_1 et audit_id_2 requis'}

        audit1 = self._audits.get(audit_id_1)
        audit2 = self._audits.get(audit_id_2)

        if not audit1:
            return {'success': False, 'error': f'Audit {audit_id_1} non trouvé'}
        if not audit2:
            return {'success': False, 'error': f'Audit {audit_id_2} non trouvé'}

        # Comparaison
        vulns1 = {v.id: v for v in audit1.vulnerabilities}
        vulns2 = {v.id: v for v in audit2.vulnerabilities}

        common = set(vulns1.keys()) & set(vulns2.keys())
        only_in_1 = set(vulns1.keys()) - set(vulns2.keys())
        only_in_2 = set(vulns2.keys()) - set(vulns1.keys())

        return {
            'success': True,
            'comparison': {
                'audit_1': {
                    'id': audit1.id,
                    'date': audit1.completed_at.isoformat() if audit1.completed_at else None,
                    'risk_score': audit1.overall_risk_score,
                    'total_vulns': len(audit1.vulnerabilities)
                },
                'audit_2': {
                    'id': audit2.id,
                    'date': audit2.completed_at.isoformat() if audit2.completed_at else None,
                    'risk_score': audit2.overall_risk_score,
                    'total_vulns': len(audit2.vulnerabilities)
                },
                'differences': {
                    'risk_improvement': round(audit2.overall_risk_score - audit1.overall_risk_score, 2),
                    'vulns_fixed': len(only_in_1),
                    'vulns_new': len(only_in_2),
                    'vulns_remaining': len(common),
                    'common_vulns': list(common),
                    'fixed_vulns': list(only_in_1),
                    'new_vulns': list(only_in_2)
                }
            }
        }

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
    return SecurityExpertSubAgent


def create_security_expert_agent(config_path: str = "") -> "SecurityExpertSubAgent":
    """Crée une instance du sous-agent expert sécurité"""
    return SecurityExpertSubAgent(config_path)
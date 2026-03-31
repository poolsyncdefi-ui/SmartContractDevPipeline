"""
Banking Specialist SubAgent - Spécialiste en architecture bancaire et financière
Version: 2.0.0 (ALIGNÉ SUR BLOCKCHAIN ARCHITECT)

Expert en conception d'architectures bancaires et financières robustes.
Spécialisations : systèmes bancaires cœur (core banking), paiements (SEPA, SWIFT, instant payments),
crédit, scoring, conformité réglementaire (PSD2, Bâle), et systèmes anti-fraude.
"""

import logging
import sys
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
from enum import Enum
from dataclasses import dataclass, field

# Configuration des imports
current_dir = Path(__file__).parent.absolute()
project_root = current_dir.parent.parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from agents.sous_agents.base_subagent import BaseSubAgent
from agents.base_agent.base_agent import Message, MessageType, AgentCapability

logger = logging.getLogger(__name__)


# ============================================================================
# ÉNUMS ET CLASSES DE DONNÉES
# ============================================================================

class BankingDomain(Enum):
    """Domaines bancaires"""
    RETAIL = "retail"           # Banque de détail
    CORPORATE = "corporate"     # Banque d'entreprise
    PRIVATE = "private"         # Gestion de fortune
    INVESTMENT = "investment"   # Banque d'investissement
    DIGITAL = "digital"         # Banque digitale


class PaymentScheme(Enum):
    """Schémas de paiement"""
    SEPA_CREDIT = "sepa_credit"
    SEPA_INSTANT = "sepa_instant"
    SWIFT_MT = "swift_mt"
    SWIFT_MX = "swift_mx"
    ACH = "ach"
    TARGET2 = "target2"
    FEDWIRE = "fedwire"
    CHAPS = "chaps"
    BACS = "bacs"
    RTP = "rtp"  # Real Time Payments


class CreditRiskModel(Enum):
    """Modèles de risque de crédit"""
    SCORING = "scoring"
    RATING = "rating"
    PD_LGD = "pd_lgd"
    IRB = "irb"  # Internal Ratings-Based
    STANDARDIZED = "standardized"


class ComplianceRegulation(Enum):
    """Réglementations de conformité"""
    PSD2 = "psd2"
    GDPR = "gdpr"
    BASEL_III = "basel_iii"
    BASEL_IV = "basel_iv"
    IFRS9 = "ifrs9"
    AML5 = "aml5"
    AMLD6 = "amld6"
    MICA = "mica"
    DORA = "dora"


@dataclass
class AccountSpec:
    """Spécifications d'un compte bancaire"""
    account_type: str  # checking, savings, loan, credit_card
    currency: str
    features: List[str]
    interest_rate: Optional[float] = None
    overdraft_limit: Optional[float] = None
    fees: Dict[str, float] = field(default_factory=dict)
    requires_kyc: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "account_type": self.account_type,
            "currency": self.currency,
            "features": self.features,
            "interest_rate": self.interest_rate,
            "overdraft_limit": self.overdraft_limit,
            "fees": self.fees,
            "requires_kyc": self.requires_kyc
        }


@dataclass
class PaymentFlow:
    """Configuration d'un flux de paiement"""
    name: str
    scheme: PaymentScheme
    processing_time_seconds: int
    settlement_time_seconds: int
    max_amount: float
    currency: str
    fees: Dict[str, float] = field(default_factory=dict)
    validation_rules: List[str] = field(default_factory=list)
    fraud_check_enabled: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "scheme": self.scheme.value,
            "processing_time_seconds": self.processing_time_seconds,
            "settlement_time_seconds": self.settlement_time_seconds,
            "max_amount": self.max_amount,
            "currency": self.currency,
            "fees": self.fees,
            "validation_rules": self.validation_rules,
            "fraud_check_enabled": self.fraud_check_enabled
        }


@dataclass
class CreditAssessment:
    """Configuration d'évaluation de crédit"""
    model: CreditRiskModel
    min_score: int
    max_loan_amount: float
    interest_rate_min: float
    interest_rate_max: float
    required_documents: List[str]
    decision_automation: bool = True
    human_review_threshold: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "model": self.model.value,
            "min_score": self.min_score,
            "max_loan_amount": self.max_loan_amount,
            "interest_rate_min": self.interest_rate_min,
            "interest_rate_max": self.interest_rate_max,
            "required_documents": self.required_documents,
            "decision_automation": self.decision_automation,
            "human_review_threshold": self.human_review_threshold
        }


@dataclass
class BankingArchitecture:
    """Conception d'architecture bancaire complète"""
    design_id: str
    name: str
    description: str
    version: str = "1.0.0"
    domain: BankingDomain = BankingDomain.RETAIL
    core_banking_system: str = "core_banking"
    accounts: List[AccountSpec] = field(default_factory=list)
    payment_flows: List[PaymentFlow] = field(default_factory=list)
    credit_assessment: Optional[CreditAssessment] = None
    compliance_frameworks: List[ComplianceRegulation] = field(default_factory=list)
    fraud_detection_enabled: bool = True
    open_banking_enabled: bool = False
    expected_customers: int = 100000
    expected_transactions_per_second: int = 1000
    availability_target: float = 99.99
    disaster_recovery_rto_seconds: int = 3600
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "design_id": self.design_id,
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "domain": self.domain.value,
            "core_banking_system": self.core_banking_system,
            "accounts": [a.to_dict() for a in self.accounts],
            "payment_flows": [p.to_dict() for p in self.payment_flows],
            "credit_assessment": self.credit_assessment.to_dict() if self.credit_assessment else None,
            "compliance_frameworks": [c.value for c in self.compliance_frameworks],
            "fraud_detection_enabled": self.fraud_detection_enabled,
            "open_banking_enabled": self.open_banking_enabled,
            "expected_customers": self.expected_customers,
            "expected_transactions_per_second": self.expected_transactions_per_second,
            "availability_target": self.availability_target,
            "disaster_recovery_rto_seconds": self.disaster_recovery_rto_seconds,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }


# ============================================================================
# SOUS-AGENT PRINCIPAL
# ============================================================================

class BankingSpecialistSubAgent(BaseSubAgent):
    """
    Sous-agent spécialisé en architecture bancaire et financière.
    
    Expert en conception de systèmes bancaires, paiements, crédit,
    conformité réglementaire et anti-fraude.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialise le sous-agent Banking Specialist.
        """
        if config_path is None:
            config_path = str(current_dir / "config.yaml")
        
        # Appel au parent (BaseSubAgent)
        super().__init__(config_path)
        
        # Métadonnées
        self._subagent_display_name = "🏦 Expert Banking Architecture"
        self._subagent_description = "Sous-agent spécialisé en architecture bancaire et financière"
        self._subagent_version = "2.0.0"
        self._subagent_category = "banking"
        self._subagent_capabilities = [
            "banking.design_core_system",
            "banking.design_payments",
            "banking.design_credit",
            "banking.compliance_check",
            "banking.fraud_detection",
            "banking.open_banking",
            "banking.reporting"
        ]
        
        # État spécifique
        self._supported_domains: List[BankingDomain] = [
            BankingDomain.RETAIL, BankingDomain.CORPORATE,
            BankingDomain.PRIVATE, BankingDomain.INVESTMENT, BankingDomain.DIGITAL
        ]
        self._designs: Dict[str, BankingArchitecture] = {}
        self._templates: Dict[str, Any] = {}
        self._patterns_library: Dict[str, Any] = {}
        
        # Standards et patterns bancaires
        self._payment_schemes = [s.value for s in PaymentScheme]
        self._compliance_frameworks = [c.value for c in ComplianceRegulation]
        
        # Métriques spécifiques
        self._banking_metrics = {
            "designs_created": 0,
            "payment_flows_designed": 0,
            "compliance_checks": 0,
            "fraud_rules_configured": 0
        }
        
        # Configuration
        self._banking_config = self._config.get('banking', {}) if self._config else {}
        self._default_domain = BankingDomain.from_string(
            self._banking_config.get('default_domain', 'retail')
        )
        
        # Charger les templates et patterns
        self._load_templates()
        self._load_patterns()
        
        # Charger les capacités depuis la configuration
        self._load_capabilities_from_config()
        
        logger.info(f"✅ {self._subagent_display_name} v{self._subagent_version} initialisé")
    
    # ========================================================================
    # IMPLÉMENTATION DES MÉTHODES ABSTRACTES (BaseSubAgent)
    # ========================================================================
    
    async def _initialize_subagent_components(self) -> bool:
        """Initialise les composants spécifiques"""
        logger.info("Initialisation des composants Banking Specialist...")
        
        self._designs = {}
        
        logger.info("✅ Composants Banking Specialist initialisés")
        return True
    
    async def _initialize_components(self) -> bool:
        """Implémentation requise par BaseAgent"""
        return await self._initialize_subagent_components()
    
    def _load_capabilities_from_config(self):
        """Charge les capacités depuis la configuration"""
        caps = self._config.get('capabilities', [])
        for cap in caps:
            if isinstance(cap, dict):
                self.add_capability(AgentCapability(
                    name=cap.get('name', 'unknown'),
                    description=cap.get('description', ''),
                    version=cap.get('version', '1.0.0')
                ))
        if caps:
            self._logger.info(f"✅ {len(caps)} capacités chargées depuis la configuration")
    
    def _get_capability_handlers(self) -> Dict[str, Any]:
        """Retourne les handlers spécifiques"""
        return {
            "banking.design_core_system": self._handle_design_core_system,
            "banking.design_payments": self._handle_design_payments,
            "banking.design_credit": self._handle_design_credit,
            "banking.compliance_check": self._handle_compliance_check,
            "banking.fraud_detection": self._handle_fraud_detection,
            "banking.open_banking": self._handle_open_banking,
            "banking.reporting": self._handle_reporting,
        }
    
    # ========================================================================
    # HANDLERS DE CAPACITÉS
    # ========================================================================
    
    async def _handle_design_core_system(self, params: Dict[str, Any]) -> Dict[str, Any]:
        requirements = params.get("requirements", {})
        return await self.design_core_banking_system(requirements)
    
    async def _handle_design_payments(self, params: Dict[str, Any]) -> Dict[str, Any]:
        requirements = params.get("requirements", {})
        return await self.design_payment_system(requirements)
    
    async def _handle_design_credit(self, params: Dict[str, Any]) -> Dict[str, Any]:
        requirements = params.get("requirements", {})
        return await self.design_credit_system(requirements)
    
    async def _handle_compliance_check(self, params: Dict[str, Any]) -> Dict[str, Any]:
        jurisdiction = params.get("jurisdiction", "EU")
        regulations = params.get("regulations", [])
        return await self.check_compliance(jurisdiction, regulations)
    
    async def _handle_fraud_detection(self, params: Dict[str, Any]) -> Dict[str, Any]:
        requirements = params.get("requirements", {})
        return await self.design_fraud_detection(requirements)
    
    async def _handle_open_banking(self, params: Dict[str, Any]) -> Dict[str, Any]:
        requirements = params.get("requirements", {})
        return await self.design_open_banking(requirements)
    
    async def _handle_reporting(self, params: Dict[str, Any]) -> Dict[str, Any]:
        requirements = params.get("requirements", {})
        return await self.design_regulatory_reporting(requirements)
    
    # ========================================================================
    # MÉTHODES DE CHARGEMENT
    # ========================================================================
    
    def _load_templates(self):
        """Charge les templates d'architecture bancaire"""
        templates_dir = current_dir / "templates"
        
        if templates_dir.exists():
            self._logger.info(f"Chargement des templates depuis {templates_dir}")
            for template_file in templates_dir.glob("*.yaml"):
                try:
                    import yaml
                    with open(template_file, 'r', encoding='utf-8') as f:
                        template = yaml.safe_load(f)
                        template_name = template_file.stem
                        self._templates[template_name] = template
                except Exception as e:
                    self._logger.error(f"Erreur chargement template {template_file}: {e}")
        else:
            self._logger.warning("Répertoire des templates non trouvé")
            self._templates = self._get_default_templates()
    
    def _load_patterns(self):
        """Charge les patterns d'architecture bancaire"""
        patterns_file = current_dir / "patterns.yaml"
        
        if patterns_file.exists():
            try:
                import yaml
                with open(patterns_file, 'r', encoding='utf-8') as f:
                    self._patterns_library = yaml.safe_load(f)
                self._logger.info(f"Patterns chargés depuis {patterns_file}")
            except Exception as e:
                self._logger.error(f"Erreur chargement patterns: {e}")
                self._patterns_library = self._get_default_patterns()
        else:
            self._logger.warning("Fichier des patterns non trouvé")
            self._patterns_library = self._get_default_patterns()
    
    def _get_default_templates(self) -> Dict[str, Any]:
        """Retourne les templates par défaut"""
        return {
            "retail_bank": {
                "name": "Retail Banking System",
                "domain": "retail",
                "accounts": ["checking", "savings", "credit_card"],
                "payment_schemes": ["SEPA_CREDIT", "SEPA_INSTANT"],
                "expected_customers": 100000
            },
            "corporate_bank": {
                "name": "Corporate Banking System",
                "domain": "corporate",
                "accounts": ["business_checking", "business_savings", "loan"],
                "payment_schemes": ["SWIFT_MT", "SWIFT_MX", "TARGET2"],
                "expected_customers": 5000
            }
        }
    
    def _get_default_patterns(self) -> Dict[str, Any]:
        """Retourne les patterns par défaut"""
        return {
            "core_banking_patterns": [
                {"name": "Double-Entry Accounting", "description": "Système comptable en partie double"},
                {"name": "Ledger Architecture", "description": "Architecture de grand livre"},
                {"name": "Event Sourcing", "description": "Traçabilité des transactions"}
            ],
            "payment_patterns": [
                {"name": "ISO 20022", "description": "Standard de messagerie financière"},
                {"name": "Settlement Finality", "description": "Garantie de règlement"},
                {"name": "Netting", "description": "Compensation des transactions"}
            ],
            "compliance_patterns": [
                {"name": "KYC/AML", "description": "Connaître son client et anti-blanchiment"},
                {"name": "Transaction Monitoring", "description": "Surveillance des transactions"},
                {"name": "Regulatory Reporting", "description": "Reporting réglementaire"}
            ]
        }
    
    # ========================================================================
    # MÉTHODES PUBLIQUES PRINCIPALES
    # ========================================================================
    
    async def design_core_banking_system(self, requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Conçoit un système bancaire cœur (core banking)."""
        try:
            domain_str = requirements.get("domain", "retail")
            domain = BankingDomain.RETAIL
            for d in BankingDomain:
                if d.value == domain_str.lower():
                    domain = d
                    break
            
            design_id = f"banking_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # Créer les comptes
            accounts = self._create_accounts(requirements, domain)
            
            # Configurer la conformité
            compliance = self._get_compliance_frameworks(requirements)
            
            design = BankingArchitecture(
                design_id=design_id,
                name=requirements.get("name", "Banking System"),
                description=requirements.get("description", ""),
                domain=domain,
                core_banking_system=requirements.get("core_system", "core_banking"),
                accounts=accounts,
                compliance_frameworks=compliance,
                expected_customers=requirements.get("expected_customers", 100000),
                expected_transactions_per_second=requirements.get("tps", 1000),
                availability_target=requirements.get("availability", 99.99)
            )
            
            self._designs[design_id] = design
            self._banking_metrics["designs_created"] += 1
            
            return {
                "success": True,
                "design": design.to_dict(),
                "design_id": design_id,
                "summary": {
                    "accounts_count": len(accounts),
                    "compliance_frameworks": len(compliance),
                    "expected_tps": design.expected_transactions_per_second
                }
            }
            
        except Exception as e:
            logger.error(f"Erreur conception core banking: {e}")
            return {"success": False, "error": str(e)}
    
    async def design_payment_system(self, requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Conçoit un système de paiement."""
        try:
            schemes = requirements.get("payment_schemes", ["sepa_credit"])
            payment_flows = []
            
            for scheme_name in schemes:
                scheme = PaymentScheme.SEPA_CREDIT
                for ps in PaymentScheme:
                    if ps.value == scheme_name.lower():
                        scheme = ps
                        break
                
                flow = PaymentFlow(
                    name=f"{scheme.value}_flow",
                    scheme=scheme,
                    processing_time_seconds=requirements.get("processing_time", 1),
                    settlement_time_seconds=requirements.get("settlement_time", 3600),
                    max_amount=requirements.get("max_amount", 1000000),
                    currency=requirements.get("currency", "EUR")
                )
                payment_flows.append(flow)
            
            self._banking_metrics["payment_flows_designed"] += len(payment_flows)
            
            return {
                "success": True,
                "payment_flows": [p.to_dict() for p in payment_flows],
                "recommendations": self._get_payment_recommendations(schemes)
            }
            
        except Exception as e:
            logger.error(f"Erreur conception paiement: {e}")
            return {"success": False, "error": str(e)}
    
    async def design_credit_system(self, requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Conçoit un système de crédit et scoring."""
        try:
            model_str = requirements.get("risk_model", "scoring")
            model = CreditRiskModel.SCORING
            for m in CreditRiskModel:
                if m.value == model_str.lower():
                    model = m
                    break
            
            assessment = CreditAssessment(
                model=model,
                min_score=requirements.get("min_score", 650),
                max_loan_amount=requirements.get("max_loan_amount", 500000),
                interest_rate_min=requirements.get("interest_rate_min", 2.5),
                interest_rate_max=requirements.get("interest_rate_max", 15.0),
                required_documents=requirements.get("required_documents", ["ID", "proof_of_income"]),
                decision_automation=requirements.get("auto_decision", True),
                human_review_threshold=requirements.get("human_review_threshold", 600)
            )
            
            return {
                "success": True,
                "credit_assessment": assessment.to_dict(),
                "recommendations": [
                    "Implement automated decisioning for low-risk applications",
                    "Use machine learning for credit scoring",
                    "Regular model validation and recalibration"
                ]
            }
            
        except Exception as e:
            logger.error(f"Erreur conception crédit: {e}")
            return {"success": False, "error": str(e)}
    
    async def check_compliance(self, jurisdiction: str, regulations: List[str]) -> Dict[str, Any]:
        """Vérifie la conformité réglementaire."""
        try:
            compliance_requirements = []
            
            if jurisdiction.upper() == "EU":
                compliance_requirements = [
                    {"regulation": "PSD2", "description": "Paiements, authentification forte", "mandatory": True},
                    {"regulation": "GDPR", "description": "Protection des données", "mandatory": True},
                    {"regulation": "MiCA", "description": "Marchés de crypto-actifs", "mandatory": False},
                    {"regulation": "DORA", "description": "Résilience opérationnelle digitale", "mandatory": True}
                ]
            elif jurisdiction.upper() == "SWITZERLAND":
                compliance_requirements = [
                    {"regulation": "FINMA", "description": "Autorité fédérale de surveillance", "mandatory": True},
                    {"regulation": "AMLA", "description": "Loi sur le blanchiment d'argent", "mandatory": True}
                ]
            
            self._banking_metrics["compliance_checks"] += 1
            
            return {
                "success": True,
                "jurisdiction": jurisdiction,
                "compliance_requirements": compliance_requirements,
                "risk_level": "medium" if len(compliance_requirements) > 3 else "low"
            }
            
        except Exception as e:
            logger.error(f"Erreur vérification conformité: {e}")
            return {"success": False, "error": str(e)}
    
    async def design_fraud_detection(self, requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Conçoit un système de détection de fraude."""
        try:
            fraud_rules = [
                {"name": "Velocity Check", "description": "Nombre de transactions dans un intervalle", "threshold": 10},
                {"name": "Amount Threshold", "description": "Montant anormalement élevé", "threshold": 10000},
                {"name": "Geographic Anomaly", "description": "Transaction depuis localisation inhabituelle", "enabled": True},
                {"name": "Device Fingerprinting", "description": "Détection de dispositif inconnu", "enabled": True}
            ]
            
            self._banking_metrics["fraud_rules_configured"] += len(fraud_rules)
            
            return {
                "success": True,
                "fraud_detection": {
                    "enabled": True,
                    "rules": fraud_rules,
                    "ml_models": ["anomaly_detection", "behavioral_analysis"],
                    "alert_threshold": requirements.get("alert_threshold", 0.7)
                },
                "recommendations": [
                    "Use machine learning for real-time fraud detection",
                    "Implement device fingerprinting",
                    "Monitor peer-to-peer transactions"
                ]
            }
            
        except Exception as e:
            logger.error(f"Erreur conception fraude: {e}")
            return {"success": False, "error": str(e)}
    
    async def design_open_banking(self, requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Conçoit une architecture open banking."""
        try:
            apis = [
                {"endpoint": "/accounts", "method": "GET", "scope": "accounts:read"},
                {"endpoint": "/transactions", "method": "GET", "scope": "transactions:read"},
                {"endpoint": "/payments", "method": "POST", "scope": "payments:create"}
            ]
            
            return {
                "success": True,
                "open_banking": {
                    "enabled": True,
                    "apis": apis,
                    "authentication": "OAuth2.0 + OIDC",
                    "scopes": ["accounts:read", "transactions:read", "payments:create"],
                    "psd2_compliant": True
                },
                "recommendations": [
                    "Implement consent management",
                    "Use OAuth2.0 with PKCE",
                    "Provide sandbox environment for developers"
                ]
            }
            
        except Exception as e:
            logger.error(f"Erreur conception open banking: {e}")
            return {"success": False, "error": str(e)}
    
    async def design_regulatory_reporting(self, requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Conçoit un système de reporting réglementaire."""
        try:
            reports = [
                {"name": "COREP", "frequency": "quarterly", "description": "Reporting de solvabilité"},
                {"name": "FINREP", "frequency": "quarterly", "description": "Reporting financier"},
                {"name": "AML Reports", "frequency": "monthly", "description": "Transactions suspectes"}
            ]
            
            return {
                "success": True,
                "regulatory_reporting": {
                    "reports": reports,
                    "automation_level": "high",
                    "formats": ["XBRL", "XML", "CSV"],
                    "submission_channels": ["API", "Portal", "SFTP"]
                }
            }
            
        except Exception as e:
            logger.error(f"Erreur conception reporting: {e}")
            return {"success": False, "error": str(e)}
    
    # ========================================================================
    # MÉTHODES PRIVÉES
    # ========================================================================
    
    def _create_accounts(self, requirements: Dict[str, Any], 
                         domain: BankingDomain) -> List[AccountSpec]:
        """Crée les comptes selon le domaine bancaire."""
        accounts = []
        
        if domain == BankingDomain.RETAIL:
            accounts = [
                AccountSpec("checking", "EUR", ["debit_card", "online_banking", "mobile_app"]),
                AccountSpec("savings", "EUR", ["interest_earning", "withdrawal_limit"], interest_rate=2.0),
                AccountSpec("credit_card", "EUR", ["revolving_credit"], overdraft_limit=5000)
            ]
        elif domain == BankingDomain.CORPORATE:
            accounts = [
                AccountSpec("business_checking", "EUR", ["multi_user", "high_limits", "api_access"]),
                AccountSpec("business_savings", "EUR", ["interest_earning", "liquidity"], interest_rate=1.5),
                AccountSpec("loan", "EUR", ["term_loan", "revolving_credit"], interest_rate=4.5)
            ]
        elif domain == BankingDomain.DIGITAL:
            accounts = [
                AccountSpec("digital_wallet", "EUR", ["instant_payments", "virtual_card"]),
                AccountSpec("crypto_account", "EUR", ["buy_sell", "staking"]),
                AccountSpec("investment", "EUR", ["stocks", "etf", "bonds"])
            ]
        
        return accounts
    
    def _get_compliance_frameworks(self, requirements: Dict[str, Any]) -> List[ComplianceRegulation]:
        """Retourne les frameworks de conformité requis."""
        frameworks = [ComplianceRegulation.PSD2, ComplianceRegulation.GDPR]
        
        if requirements.get("international", False):
            frameworks.append(ComplianceRegulation.BASEL_III)
        
        if requirements.get("crypto", False):
            frameworks.append(ComplianceRegulation.MICA)
        
        return frameworks
    
    def _get_payment_recommendations(self, schemes: List[str]) -> List[str]:
        """Retourne les recommandations pour les paiements."""
        recommendations = []
        
        if "sepa_instant" in schemes:
            recommendations.append("Implement ISO 20022 for SEPA Instant payments")
        if "swift" in str(schemes):
            recommendations.append("Use SWIFT gpi for cross-border payment tracking")
        
        recommendations.append("Implement fraud detection for all payment flows")
        recommendations.append("Ensure 24/7 availability for real-time payments")
        
        return recommendations
    
    # ========================================================================
    # MÉTHODES DE RÉCUPÉRATION
    # ========================================================================
    
    def get_design(self, design_id: str) -> Optional[Dict[str, Any]]:
        design = self._designs.get(design_id)
        return design.to_dict() if design else None
    
    def list_designs(self) -> List[Dict[str, Any]]:
        return [
            {
                "design_id": design.design_id,
                "name": design.name,
                "domain": design.domain.value,
                "accounts_count": len(design.accounts),
                "created_at": design.created_at.isoformat()
            }
            for design in self._designs.values()
        ]
    
    def get_metrics(self) -> Dict[str, Any]:
        return {
            **self._banking_metrics,
            "designs_count": len(self._designs),
            "supported_domains": [d.value for d in self._supported_domains]
        }
    
    # ========================================================================
    # NETTOYAGE
    # ========================================================================
    
    async def _cleanup(self):
        logger.info("Nettoyage des ressources Banking Specialist...")
        self._designs.clear()
        await super()._cleanup()


# ============================================================================
# FONCTION D'USINE
# ============================================================================

def create_banking_specialist_subagent(config_path: Optional[str] = None) -> BankingSpecialistSubAgent:
    """Crée une instance du sous-agent Banking Specialist"""
    return BankingSpecialistSubAgent(config_path)
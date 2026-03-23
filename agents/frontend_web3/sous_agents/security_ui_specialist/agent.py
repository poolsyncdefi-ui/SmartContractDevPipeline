#!/usr/bin/env python3
"""
SecurityUiSpecialist SubAgent - Spécialiste Sécurité UI
Version: 2.0.0 (ALIGNÉ SUR CIRCUIT_BREAKER)

Expert en sécurité des interfaces Web3 : transaction security, phishing protection,
wallet security, smart contract verification, approval management.
"""

import logging
import sys
import asyncio
import json
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, Optional, List, Union, Callable
from enum import Enum
from dataclasses import dataclass, field
import uuid

# Configuration des imports
current_dir = Path(__file__).parent.absolute()
# Définir project_root
project_root = Path(__file__).parent.parent.parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from agents.sous_agents.base_subagent import BaseSubAgent
from agents.base_agent.base_agent import Message, MessageType

logger = logging.getLogger(__name__)


# ============================================================================
# ÉNUMS ET CLASSES DE DONNÉES
# ============================================================================

class SecurityIssueType(Enum):
    """Types d'issues de sécurité"""
    PHISHING = "phishing"
    MALICIOUS_APPROVAL = "malicious_approval"
    UNSAFE_TRANSACTION = "unsafe_transaction"
    SUSPICIOUS_CONTRACT = "suspicious_contract"
    WALLET_VULNERABILITY = "wallet_vulnerability"


class SecurityLevel(Enum):
    """Niveaux de sécurité"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class TransactionSecurityCheck:
    """Vérification de sécurité d'une transaction"""
    to_address: str
    value: str
    data: Optional[str] = None
    gas_limit: Optional[int] = None
    issues: List[str] = field(default_factory=list)
    risk_level: SecurityLevel = SecurityLevel.LOW
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "to_address": self.to_address,
            "value": self.value,
            "data": self.data[:100] if self.data else None,
            "gas_limit": self.gas_limit,
            "issues": self.issues,
            "risk_level": self.risk_level.value
        }


@dataclass
class ApprovalCheck:
    """Vérification d'approbation de token"""
    token_address: str
    spender: str
    amount: str
    is_approved: bool = False
    issues: List[str] = field(default_factory=list)
    risk_level: SecurityLevel = SecurityLevel.LOW
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "token_address": self.token_address,
            "spender": self.spender,
            "amount": self.amount,
            "is_approved": self.is_approved,
            "issues": self.issues,
            "risk_level": self.risk_level.value
        }


@dataclass
class SecurityAnalysis:
    """Résultat d'analyse de sécurité"""
    analysis_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    issues: List[Dict[str, Any]] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    risk_score: int = 0
    created_at: datetime = field(default_factory=datetime.now)
    processing_time_ms: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "analysis_id": self.analysis_id,
            "issues": self.issues,
            "recommendations": self.recommendations,
            "risk_score": self.risk_score,
            "created_at": self.created_at.isoformat(),
            "processing_time_ms": self.processing_time_ms
        }


@dataclass
class SecurityResult:
    """Résultat de vérification de sécurité"""
    result_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    check_type: str = ""
    details: Dict[str, Any] = field(default_factory=dict)
    is_safe: bool = True
    risk_level: SecurityLevel = SecurityLevel.LOW
    created_at: datetime = field(default_factory=datetime.now)
    processing_time_ms: float = 0.0
    success: bool = True
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "result_id": self.result_id,
            "check_type": self.check_type,
            "details": self.details,
            "is_safe": self.is_safe,
            "risk_level": self.risk_level.value,
            "created_at": self.created_at.isoformat(),
            "processing_time_ms": self.processing_time_ms,
            "success": self.success,
            "error": self.error
        }


@dataclass
class SecurityStats:
    """Statistiques de sécurité"""
    checks_performed: int = 0
    checks_succeeded: int = 0
    checks_failed: int = 0
    by_type: Dict[str, int] = field(default_factory=dict)
    by_risk_level: Dict[str, int] = field(default_factory=dict)
    total_processing_time: float = 0.0
    avg_processing_time: float = 0.0
    last_check: Optional[datetime] = None
    start_time: datetime = field(default_factory=datetime.now)
    
    def record_check(self, check_type: str, risk_level: SecurityLevel, 
                     processing_time: float, success: bool):
        """Enregistre une vérification"""
        self.checks_performed += 1
        if success:
            self.checks_succeeded += 1
        else:
            self.checks_failed += 1
            
        self.total_processing_time += processing_time
        self.avg_processing_time = self.total_processing_time / self.checks_performed
        self.last_check = datetime.now()
        
        # Statistiques par type
        self.by_type[check_type] = self.by_type.get(check_type, 0) + 1
        self.by_risk_level[risk_level.value] = self.by_risk_level.get(risk_level.value, 0) + 1
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "checks_performed": self.checks_performed,
            "checks_succeeded": self.checks_succeeded,
            "checks_failed": self.checks_failed,
            "by_type": self.by_type,
            "by_risk_level": self.by_risk_level,
            "avg_processing_time_ms": round(self.avg_processing_time, 2),
            "total_processing_time_ms": round(self.total_processing_time, 2),
            "last_check": self.last_check.isoformat() if self.last_check else None,
            "uptime_seconds": (datetime.now() - self.start_time).total_seconds()
        }


# ============================================================================
# SOUS-AGENT PRINCIPAL
# ============================================================================

class SecurityUiSpecialistSubAgent(BaseSubAgent):
    """
    Sous-agent spécialiste sécurité UI
    
    Vérifie la sécurité des transactions, des approbations,
    protège contre le phishing et vérifie les contrats intelligents.
    """
    
    def __init__(self, config_path: str = ""):
        """Initialise le spécialiste sécurité"""
        # 🔧 CORRECTION : Construire le chemin correct
        if not config_path:
            # Chemin relatif depuis la racine du projet
            config_path = "agents/frontend_web3/sous_agents/security_ui_specialist/config.yaml"
        
        # Si le chemin n'est pas absolu, le résoudre par rapport à project_root
        if not Path(config_path).is_absolute():
            config_path = str(project_root / config_path)
        
        logger.debug(f"🔧 Chargement config depuis: {config_path}")
        super().__init__(config_path)
        
        # Récupérer la configuration
        if 'subagent' in self._config:
            config = self._config.get('subagent', {})
        elif 'agent' in self._config:
            config = self._config.get('agent', {})
        else:
            config = {}
        
        # Métadonnées
        self._subagent_display_name = config.get('display_name', "🛡️ Spécialiste Sécurité UI")
        self._subagent_description = config.get('description', "Sécurisation des interfaces utilisateur")
        self._subagent_version = config.get('version', "2.0.0")
        self._subagent_category = config.get('category', "frontend_web3")
        self._subagent_capabilities = [
            "security.check_transaction",
            "security.check_approval",
            "security.detect_phishing",
            "security.verify_contract",
            "security.analyze_wallet",
            "security.generate_report"
        ]
        
        # Statistiques
        self._stats = SecurityStats()
        
        # File d'attente
        self._event_queue: asyncio.Queue = asyncio.Queue()
        
        # Tâche de traitement
        self._processor_task: Optional[asyncio.Task] = None
        
        logger.info(f"✅ {self._subagent_display_name} initialisé")

    # ============================================================================
    # INITIALISATION
    # ============================================================================
    
    async def _initialize_subagent_components(self) -> bool:
        """Initialise les composants spécifiques"""
        logger.info("Initialisation des composants Security Specialist...")
        
        self._processor_task = asyncio.create_task(self._processor_loop())
        
        self._components = {
            "version": self._subagent_version,
            "security_checks": ["transaction", "approval", "phishing", "contract", "wallet"],
            "risk_levels": [l.value for l in SecurityLevel]
        }
        
        logger.info("✅ Composants Security Specialist initialisés")
        return True
        
    async def _initialize_components(self) -> bool:
        return await self._initialize_subagent_components()

    def _get_capability_handlers(self) -> Dict[str, Callable]:
        return {
            "security.check_transaction": self._handle_check_transaction,
            "security.check_approval": self._handle_check_approval,
            "security.detect_phishing": self._handle_detect_phishing,
            "security.verify_contract": self._handle_verify_contract,
            "security.analyze_wallet": self._handle_analyze_wallet,
            "security.generate_report": self._handle_generate_report,
        }
    
    # ============================================================================
    # TÂCHES DE FOND
    # ============================================================================
    
    async def _processor_loop(self):
        """Boucle de traitement"""
        logger.info("🔄 Boucle de traitement démarrée")
        
        while self._status.value == "ready":
            try:
                while not self._event_queue.empty():
                    event = await self._event_queue.get()
                    await self._process_event(event)
                await asyncio.sleep(1)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"❌ Erreur dans la boucle: {e}")
                await asyncio.sleep(5)
    
    async def _process_event(self, event: Dict[str, Any]):
        """Traite un événement"""
        pass
    
    # ============================================================================
    # VÉRIFICATIONS DE SÉCURITÉ
    # ============================================================================
    
    async def check_transaction(self, tx: Dict[str, Any]) -> SecurityResult:
        """Vérifie la sécurité d'une transaction"""
        start_time = time.time()
        result = SecurityResult(check_type="transaction")
        
        try:
            to_address = tx.get("to", "")
            value = tx.get("value", "0")
            data = tx.get("data")
            
            issues = []
            risk_level = SecurityLevel.LOW
            
            # Vérifier si l'adresse est suspecte
            if self._is_suspicious_address(to_address):
                issues.append("Adresse de destination suspecte")
                risk_level = SecurityLevel.HIGH
            
            # Vérifier si le montant est anormal
            value_eth = int(value) / 1e18 if isinstance(value, int) else float(value)
            if value_eth > 10:
                issues.append("Montant élevé détecté")
                if risk_level != SecurityLevel.HIGH:
                    risk_level = SecurityLevel.MEDIUM
            
            # Vérifier si le data contient un appel suspect
            if data and len(data) > 100:
                issues.append("Données de transaction anormalement longues")
                risk_level = SecurityLevel.MEDIUM
            
            result.details = {
                "to_address": to_address,
                "value_eth": value_eth,
                "has_data": bool(data)
            }
            result.is_safe = len(issues) == 0
            result.risk_level = risk_level
            
            processing_time = (time.time() - start_time) * 1000
            result.processing_time_ms = processing_time
            result.success = True
            self._stats.record_check("transaction", risk_level, processing_time, True)
            
            await self._log_event("transaction_checked", {
                "result_id": result.result_id,
                "is_safe": result.is_safe,
                "risk_level": risk_level.value
            })
            
        except Exception as e:
            result.success = False
            result.error = str(e)
            processing_time = (time.time() - start_time) * 1000
            result.processing_time_ms = processing_time
            self._stats.record_check("transaction", SecurityLevel.LOW, processing_time, False)
            logger.error(f"❌ Erreur vérification transaction: {e}")
        
        return result
    
    async def check_approval(self, approval: Dict[str, Any]) -> SecurityResult:
        """Vérifie la sécurité d'une approbation de token"""
        start_time = time.time()
        result = SecurityResult(check_type="approval")
        
        try:
            token = approval.get("token", "")
            spender = approval.get("spender", "")
            amount = approval.get("amount", "unlimited")
            
            issues = []
            risk_level = SecurityLevel.LOW
            
            # Vérifier le spender
            if self._is_suspicious_address(spender):
                issues.append("Adresse du spender suspecte")
                risk_level = SecurityLevel.CRITICAL
            
            # Vérifier le montant
            if amount == "unlimited" or (isinstance(amount, (int, float)) and amount > 1000000):
                issues.append("Montant d'approbation illimité ou très élevé")
                risk_level = SecurityLevel.HIGH
            
            # Vérifier le token
            if self._is_suspicious_address(token):
                issues.append("Adresse du token suspecte")
                risk_level = SecurityLevel.CRITICAL
            
            result.details = {
                "token": token,
                "spender": spender,
                "amount": str(amount)[:100]
            }
            result.is_safe = len(issues) == 0
            result.risk_level = risk_level
            
            processing_time = (time.time() - start_time) * 1000
            result.processing_time_ms = processing_time
            result.success = True
            self._stats.record_check("approval", risk_level, processing_time, True)
            
        except Exception as e:
            result.success = False
            result.error = str(e)
            processing_time = (time.time() - start_time) * 1000
            result.processing_time_ms = processing_time
            self._stats.record_check("approval", SecurityLevel.LOW, processing_time, False)
        
        return result
    
    async def detect_phishing(self, url: str, context: str = "") -> SecurityResult:
        """Détecte les tentatives de phishing"""
        start_time = time.time()
        result = SecurityResult(check_type="phishing")
        
        try:
            issues = []
            risk_level = SecurityLevel.LOW
            
            # Vérifications basiques
            suspicious_patterns = [
                "verify-wallet", "claim-rewards", "airdrop", "free-nft",
                "emergency-withdraw", "sync-wallet", "validate-wallet"
            ]
            
            url_lower = url.lower()
            for pattern in suspicious_patterns:
                if pattern in url_lower:
                    issues.append(f"Pattern suspect détecté: {pattern}")
                    risk_level = SecurityLevel.HIGH
            
            # Vérifier le domaine
            if "http" in url_lower and not url_lower.startswith("https://"):
                issues.append("URL non sécurisée (http)")
                risk_level = SecurityLevel.MEDIUM
            
            result.details = {
                "url": url,
                "context": context,
                "suspicious_patterns_found": len(issues)
            }
            result.is_safe = len(issues) == 0
            result.risk_level = risk_level
            
            processing_time = (time.time() - start_time) * 1000
            result.processing_time_ms = processing_time
            result.success = True
            self._stats.record_check("phishing", risk_level, processing_time, True)
            
        except Exception as e:
            result.success = False
            result.error = str(e)
            processing_time = (time.time() - start_time) * 1000
            result.processing_time_ms = processing_time
            self._stats.record_check("phishing", SecurityLevel.LOW, processing_time, False)
        
        return result
    
    async def verify_contract(self, contract_address: str, chain: str = "ethereum") -> SecurityResult:
        """Vérifie la sécurité d'un contrat intelligent"""
        start_time = time.time()
        result = SecurityResult(check_type="contract")
        
        try:
            issues = []
            risk_level = SecurityLevel.LOW
            
            # Vérification basique
            if not contract_address.startswith("0x") or len(contract_address) != 42:
                issues.append("Format d'adresse de contrat invalide")
                risk_level = SecurityLevel.MEDIUM
            
            # Simulation de vérification (à remplacer par une vraie API)
            if self._is_suspicious_address(contract_address):
                issues.append("Adresse de contrat suspecte")
                risk_level = SecurityLevel.HIGH
            
            result.details = {
                "contract_address": contract_address,
                "chain": chain,
                "verified": len(issues) == 0
            }
            result.is_safe = len(issues) == 0
            result.risk_level = risk_level
            
            processing_time = (time.time() - start_time) * 1000
            result.processing_time_ms = processing_time
            result.success = True
            self._stats.record_check("contract", risk_level, processing_time, True)
            
        except Exception as e:
            result.success = False
            result.error = str(e)
            processing_time = (time.time() - start_time) * 1000
            result.processing_time_ms = processing_time
            self._stats.record_check("contract", SecurityLevel.LOW, processing_time, False)
        
        return result
    
    async def analyze_wallet(self, wallet_address: str) -> SecurityResult:
        """Analyse la sécurité d'un wallet"""
        start_time = time.time()
        result = SecurityResult(check_type="wallet")
        
        try:
            issues = []
            risk_level = SecurityLevel.LOW
            
            # Vérification basique
            if not wallet_address.startswith("0x") or len(wallet_address) != 42:
                issues.append("Format d'adresse de wallet invalide")
                risk_level = SecurityLevel.MEDIUM
            
            result.details = {
                "wallet_address": wallet_address,
                "is_valid": len(issues) == 0
            }
            result.is_safe = len(issues) == 0
            result.risk_level = risk_level
            
            processing_time = (time.time() - start_time) * 1000
            result.processing_time_ms = processing_time
            result.success = True
            self._stats.record_check("wallet", risk_level, processing_time, True)
            
        except Exception as e:
            result.success = False
            result.error = str(e)
            processing_time = (time.time() - start_time) * 1000
            result.processing_time_ms = processing_time
            self._stats.record_check("wallet", SecurityLevel.LOW, processing_time, False)
        
        return result
    
    async def generate_report(self, wallet_address: str) -> SecurityAnalysis:
        """Génère un rapport de sécurité complet"""
        start_time = time.time()
        analysis = SecurityAnalysis()
        
        try:
            # Simuler une analyse complète
            analysis.issues = [
                {"type": "wallet", "description": "Wallet non vérifié", "risk": "medium"},
                {"type": "transactions", "description": "Historique de transactions anormal", "risk": "low"}
            ]
            analysis.recommendations = [
                "Utiliser un hardware wallet",
                "Vérifier les approbations de tokens",
                "Activer l'authentification à deux facteurs"
            ]
            analysis.risk_score = 65
            
            processing_time = (time.time() - start_time) * 1000
            analysis.processing_time_ms = processing_time
            
        except Exception as e:
            analysis.issues.append({"type": "error", "description": str(e), "risk": "critical"})
            logger.error(f"❌ Erreur génération rapport: {e}")
        
        return analysis
    
    def _is_suspicious_address(self, address: str) -> bool:
        """Vérifie si une adresse est dans la liste des adresses suspectes"""
        # Liste simplifiée - à remplacer par une vraie base de données
        suspicious = [
            "0x0000000000000000000000000000000000000000",
            "0xdead000000000000000000000000000000000000"
        ]
        return address.lower() in suspicious
    
    # ============================================================================
    # HANDLERS
    # ============================================================================
    
    async def _handle_check_transaction(self, params: Dict[str, Any]) -> Dict[str, Any]:
        result = await self.check_transaction(params)
        return result.to_dict()
    
    async def _handle_check_approval(self, params: Dict[str, Any]) -> Dict[str, Any]:
        result = await self.check_approval(params)
        return result.to_dict()
    
    async def _handle_detect_phishing(self, params: Dict[str, Any]) -> Dict[str, Any]:
        url = params.get("url", "")
        context = params.get("context", "")
        result = await self.detect_phishing(url, context)
        return result.to_dict()
    
    async def _handle_verify_contract(self, params: Dict[str, Any]) -> Dict[str, Any]:
        address = params.get("address", "")
        chain = params.get("chain", "ethereum")
        result = await self.verify_contract(address, chain)
        return result.to_dict()
    
    async def _handle_analyze_wallet(self, params: Dict[str, Any]) -> Dict[str, Any]:
        address = params.get("address", "")
        result = await self.analyze_wallet(address)
        return result.to_dict()
    
    async def _handle_generate_report(self, params: Dict[str, Any]) -> Dict[str, Any]:
        address = params.get("address", "")
        analysis = await self.generate_report(address)
        return analysis.to_dict()
    
    # ============================================================================
    # GESTION DES MESSAGES
    # ============================================================================
    
    async def handle_message(self, message: Message) -> Optional[Message]:
        try:
            msg_type = message.message_type
            logger.debug(f"📨 Message reçu: {msg_type} de {message.sender}")

            handlers = self._get_standard_handlers()
            handlers.update(self._get_capability_handlers())

            if msg_type in handlers:
                handler = getattr(self, handlers[msg_type], None)
                if handler:
                    result = await handler(message.content)
                    return Message(
                        sender=self.name,
                        recipient=message.sender,
                        content=result,
                        message_type=f"{msg_type}_response",
                        correlation_id=message.message_id
                    )

            return None

        except Exception as e:
            logger.error(f"❌ Erreur: {e}")
            return Message(
                sender=self.name,
                recipient=message.sender,
                content={"error": str(e)},
                message_type=MessageType.ERROR.value,
                correlation_id=message.message_id
            )
    
    # ============================================================================
    # UTILITAIRES
    # ============================================================================
    
    async def _log_event(self, event_type: str, data: Dict[str, Any]):
        event = {"type": event_type, "timestamp": datetime.now().isoformat(), "data": data}
        await self._event_queue.put(event)
        logger.info(f"📋 Événement: {event_type}")
    
    # ============================================================================
    # SANTÉ ET STATISTIQUES
    # ============================================================================
    
    async def health_check(self) -> Dict[str, Any]:
        base_health = await super().health_check()
        
        return {
            **base_health,
            "agent": self.name,
            "display_name": self._subagent_display_name,
            "category": self._subagent_category,
            "status": self._status.value,
            "ready": self._status == AgentStatus.READY,
            "initialized": self._initialized,
            "stats": self._stats.to_dict(),
            "components": self._components,
            "timestamp": datetime.now().isoformat()
        }
    
    def get_agent_info(self) -> Dict[str, Any]:
        return {
            "id": self.name,
            "name": self.__class__.__name__,
            "display_name": self._subagent_display_name,
            "category": self._subagent_category,
            "version": self._subagent_version,
            "description": self._subagent_description,
            "status": self._status.value,
            "capabilities": self._subagent_capabilities,
            "stats": self._stats.to_dict()
        }
    
    async def get_stats(self) -> Dict[str, Any]:
        return self._stats.to_dict()
    
    async def shutdown(self) -> bool:
        logger.info(f"Arrêt de {self._subagent_display_name}...")
        
        if self._processor_task and not self._processor_task.done():
            self._processor_task.cancel()
            try:
                await self._processor_task
            except asyncio.CancelledError:
                pass
        
        try:
            await super().shutdown()
        except Exception:
            pass
        
        logger.info(f"✅ {self._subagent_display_name} arrêté")
        return True
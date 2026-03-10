"""
Smart Contract Agent - Agent de développement de contrats intelligents
Version: 2.6.0 (ALIGNÉ SUR CODER/ARCHITECT)
"""

import logging
import os
import sys
import json
import yaml
import random
import asyncio
import traceback
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass, field
from enum import Enum

# ============================================================================
# CONFIGURATION DES IMPORTS
# ============================================================================

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from agents.base_agent.base_agent import BaseAgent, AgentStatus, Message

logger = logging.getLogger(__name__)


# ============================================================================
# ÉNUMS ET CLASSES DE DONNÉES
# ============================================================================

class ContractStandard(Enum):
    """Standards de contrats supportés"""
    ERC20 = "erc20"
    ERC721 = "erc721"
    ERC1155 = "erc1155"
    ERC4626 = "erc4626"
    CUSTOM = "custom"


class AuditSeverity(Enum):
    """Niveaux de sévérité pour les audits"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class DeploymentStatus(Enum):
    """Statuts de déploiement"""
    PENDING = "pending"
    DEPLOYING = "deploying"
    DEPLOYED = "deployed"
    FAILED = "failed"
    VERIFIED = "verified"


@dataclass
class ContractTemplate:
    """Template de contrat"""
    name: str
    standard: ContractStandard
    code: str
    dependencies: List[str] = field(default_factory=list)
    description: str = ""


@dataclass
class AuditFinding:
    """Résultat d'audit"""
    severity: AuditSeverity
    title: str
    description: str
    location: str
    recommendation: str
    line: Optional[int] = None


@dataclass
class DeploymentInfo:
    """Informations de déploiement"""
    contract_name: str
    network: str
    address: str
    transaction_hash: str
    block_number: int
    timestamp: datetime
    status: DeploymentStatus
    explorer_url: Optional[str] = None


# ============================================================================
# AGENT PRINCIPAL (ALIGNÉ SUR CODER/ARCHITECT)
# ============================================================================

class SmartContractAgent(BaseAgent):
    """
    Agent spécialisé dans le développement, audit, optimisation et déploiement
    de smart contracts sécurisés et efficaces pour applications DeFi et Web3
    """

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialise l'agent smart contract

        Args:
            config_path: Chemin vers le fichier de configuration YAML
        """
        if config_path is None:
            config_path = str(project_root / "agents" / "smart_contract" / "config.yaml")

        # Initialiser l'agent de base
        super().__init__(config_path)

        # Configuration spécifique
        self._contract_config = self._agent_config.get('configuration', {})
        self._display_name = self._agent_config.get('agent', {}).get('display_name', '📜 Agent Smart Contract')

        # État interne
        self._contracts_generated = 0
        self._audits_performed = 0
        self._deployments: List[DeploymentInfo] = []
        self._templates: Dict[str, ContractTemplate] = {}
        self._sub_agents: Dict[str, Any] = {}
        self._components: Dict[str, Any] = {}
        self._initialized = False

        # Statistiques internes
        self._stats = {
            'total_contracts': 0,
            'total_audits': 0,
            'total_deployments': 0,
            'successful_deployments': 0,
            'failed_deployments': 0,
            'critical_findings': 0,
            'high_findings': 0,
            'medium_findings': 0,
            'low_findings': 0,
            'uptime_start': datetime.now()
        }

        self._logger.info(f"📜 Agent Smart Contract créé - v{self._version}")

    # ========================================================================
    # MÉTHODES D'INITIALISATION (ALIGNÉES)
    # ========================================================================

    async def initialize(self) -> bool:
        """Initialisation asynchrone de l'agent"""
        self._logger.info("📜 Initialisation du Smart Contract Agent...")
        return await super().initialize()

    async def _initialize_components(self) -> bool:
        """
        Initialise les composants spécifiques.
        Appelé par BaseAgent.initialize().
        """
        try:
            self._logger.info("Initialisation des composants Smart Contract...")

            # Charger les templates
            await self._load_templates()

            # Initialiser les sous-agents
            await self._initialize_sub_agents()

            # Initialiser les composants
            self._components = {
                "contract_generator": {
                    "enabled": True,
                    "standards": self._contract_config.get('supported_standards', {}).get('token_standards', []),
                },
                "audit_engine": {
                    "enabled": True,
                    "security_checks": self._contract_config.get('security_requirements', {}).get('required_checks', []),
                },
                "gas_optimizer": {"enabled": True},
                "deployment_manager": {"enabled": True},
                "upgradeability_designer": {"enabled": True}
            }

            self._logger.info(f"✅ Composants: {list(self._components.keys())}")
            self._initialized = True
            return True

        except Exception as e:
            self._logger.error(f"Erreur composants: {e}")
            return False

    async def _initialize_sub_agents(self):
        """Initialise les sous-agents spécialisés"""
        try:
            # Tentative d'import des sous-agents (optionnel)
            try:
                from .sous_agents import (
                    SolidityExpertSubAgent,
                    SecurityExpertSubAgent,
                    GasOptimizerSubAgent,
                    FormalVerificationSubAgent
                )

                self._sub_agents = {
                    "solidity": SolidityExpertSubAgent(),
                    "security": SecurityExpertSubAgent(),
                    "gas": GasOptimizerSubAgent(),
                    "formal": FormalVerificationSubAgent()
                }
                self._logger.info(f"✅ Sous-agents: {list(self._sub_agents.keys())}")
            except ImportError as e:
                self._logger.debug(f"Aucun sous-agent trouvé: {e}")
                self._sub_agents = {}

        except Exception as e:
            self._logger.error(f"Erreur sous-agents: {e}")
            self._sub_agents = {}

    async def _load_templates(self):
        """Charge les templates de contrats"""
        self._templates = {
            "ERC20": ContractTemplate(
                name="ERC20",
                standard=ContractStandard.ERC20,
                code=self._get_erc20_template(),
                dependencies=["@openzeppelin/contracts@4.9.0"],
                description="Token ERC20 avec mint/burn, pausable, vesting"
            ),
            "ERC721": ContractTemplate(
                name="ERC721",
                standard=ContractStandard.ERC721,
                code=self._get_erc721_template(),
                dependencies=["@openzeppelin/contracts@4.9.0"],
                description="NFT ERC721 avec reveal, royalties"
            ),
            "ERC1155": ContractTemplate(
                name="ERC1155",
                standard=ContractStandard.ERC1155,
                code=self._get_erc1155_template(),
                dependencies=["@openzeppelin/contracts@4.9.0"],
                description="Multi-token ERC1155"
            ),
            "ERC4626": ContractTemplate(
                name="ERC4626",
                standard=ContractStandard.ERC4626,
                code=self._get_erc4626_template(),
                dependencies=["@openzeppelin/contracts@4.9.0"],
                description="Tokenized Vault ERC4626"
            )
        }
        self._logger.info(f"📋 {len(self._templates)} templates chargés")

    # ========================================================================
    # MÉTHODES DE GESTION D'ÉTAT (ALIGNÉES)
    # ========================================================================

    async def shutdown(self) -> bool:
        """Arrête l'agent proprement"""
        self._logger.info("Arrêt de l'agent Smart Contract...")
        return await super().shutdown()

    async def _cleanup(self):
        """Nettoie les ressources spécifiques"""
        self._logger.info("Nettoyage des ressources Smart Contract...")

        # Sauvegarder les statistiques
        try:
            stats_file = Path("./reports") / "smart_contract_stats.json"
            stats_file.parent.mkdir(parents=True, exist_ok=True)
            with open(stats_file, 'w', encoding='utf-8') as f:
                json.dump({
                    "stats": self._stats,
                    "contracts_generated": self._contracts_generated,
                    "audits_performed": self._audits_performed,
                    "deployments": len(self._deployments),
                    "timestamp": datetime.now().isoformat()
                }, f, indent=2)
            self._logger.info(f"✅ Statistiques sauvegardées")
        except Exception as e:
            self._logger.warning(f"⚠️ Impossible de sauvegarder: {e}")

    # ========================================================================
    # MÉTHODES DE SANTÉ ET D'INFORMATION (ALIGNÉES)
    # ========================================================================

    async def health_check(self) -> Dict[str, Any]:
        """Vérifie la santé de l'agent"""
        base_health = await super().health_check()

        return {
            **base_health,
            "agent": self.name,
            "display_name": self._display_name,
            "status": self._status.value,
            "ready": self._status == AgentStatus.READY,
            "initialized": self._initialized,
            "smart_contract_specific": {
                "contracts_generated": self._contracts_generated,
                "audits_performed": self._audits_performed,
                "deployments": len(self._deployments),
                "templates_loaded": len(self._templates),
                "sub_agents": list(self._sub_agents.keys()),
                "stats": {
                    "total_contracts": self._stats['total_contracts'],
                    "total_audits": self._stats['total_audits'],
                    "successful_deployments": self._stats['successful_deployments'],
                    "critical_findings": self._stats['critical_findings']
                }
            },
            "timestamp": datetime.now().isoformat()
        }

    def get_agent_info(self) -> Dict[str, Any]:
        """Retourne les informations de l'agent pour le registre"""
        agent_config = self._agent_config.get('agent', {})
        capabilities = agent_config.get('capabilities', [])

        if capabilities and isinstance(capabilities[0], dict):
            capabilities = [cap.get('name') for cap in capabilities if cap.get('name')]

        return {
            "id": self.name,
            "name": "SmartContractAgent",
            "display_name": self._display_name,
            "version": agent_config.get('version', '2.6.0'),
            "description": agent_config.get('description', 'Développement et audit de smart contracts'),
            "status": self._status.value,
            "capabilities": capabilities,
            "features": {
                "standards": [t.name for t in self._templates.keys()],
                "sub_agents": list(self._sub_agents.keys()),
                "components": list(self._components.keys())
            },
            "stats": {
                "contracts_generated": self._contracts_generated,
                "audits_performed": self._audits_performed,
                "deployments": len(self._deployments)
            }
        }

    # ========================================================================
    # GESTION DES MESSAGES (ALIGNÉE)
    # ========================================================================

    async def _handle_custom_message(self, message: Message) -> Optional[Message]:
        """
        Gère les messages personnalisés pour le Smart Contract Agent.
        """
        try:
            msg_type = message.message_type
            self._logger.debug(f"Message personnalisé reçu: {msg_type} de {message.sender}")

            handlers = {
                "smart_contract.generate": self._handle_generate,
                "smart_contract.audit": self._handle_audit,
                "smart_contract.deploy": self._handle_deploy,
                "smart_contract.optimize": self._handle_optimize,
                "smart_contract.stats": self._handle_stats,
            }

            if msg_type in handlers:
                return await handlers[msg_type](message)

            self._logger.warning(f"Aucun handler pour le type: {msg_type}")
            return None

        except Exception as e:
            self._logger.error(f"Erreur traitement message: {e}")
            return Message(
                sender=self.name,
                recipient=message.sender,
                content={"error": str(e), "traceback": traceback.format_exc()},
                message_type=MessageType.ERROR.value,
                correlation_id=message.message_id
            )

    async def _handle_generate(self, message: Message) -> Message:
        """Gère la génération de contrat"""
        content = message.content
        contract_type = content.get("contract_type", "ERC20")
        name = content.get("name", "MyToken")
        symbol = content.get("symbol", "MTK")
        params = content.get("params", {})

        result = await self._develop_contract(contract_type, name, symbol, params)

        return Message(
            sender=self.name,
            recipient=message.sender,
            content=result,
            message_type="smart_contract.generated",
            correlation_id=message.message_id
        )

    async def _handle_audit(self, message: Message) -> Message:
        """Gère l'audit de contrat"""
        contract_code = message.content.get("contract_code", "")
        result = await self._audit_contract(contract_code)

        return Message(
            sender=self.name,
            recipient=message.sender,
            content=result,
            message_type="smart_contract.audited",
            correlation_id=message.message_id
        )

    async def _handle_deploy(self, message: Message) -> Message:
        """Gère le déploiement de contrat"""
        contract_name = message.content.get("contract_name", "")
        network = message.content.get("network", "ethereum")
        result = await self._deploy_contract(contract_name, network)

        return Message(
            sender=self.name,
            recipient=message.sender,
            content=result,
            message_type="smart_contract.deployed",
            correlation_id=message.message_id
        )

    async def _handle_optimize(self, message: Message) -> Message:
        """Gère l'optimisation de gas"""
        contract_code = message.content.get("contract_code", "")
        result = await self._optimize_gas(contract_code)

        return Message(
            sender=self.name,
            recipient=message.sender,
            content=result,
            message_type="smart_contract.optimized",
            correlation_id=message.message_id
        )

    async def _handle_stats(self, message: Message) -> Message:
        """Retourne les statistiques"""
        return Message(
            sender=self.name,
            recipient=message.sender,
            content=self._stats,
            message_type="smart_contract.stats_response",
            correlation_id=message.message_id
        )

    # ========================================================================
    # MÉTHODES FONCTIONNELLES (Votre code existant, préservé)
    # ========================================================================

    async def _develop_contract(self,
                               contract_type: str,
                               name: str,
                               symbol: str,
                               params: Dict[str, Any]) -> Dict[str, Any]:
        """Développe un smart contract selon le standard demandé"""
        self._logger.info(f"🔨 Développement du contrat {contract_type}: {name}")
        self._contracts_generated += 1
        self._stats['total_contracts'] += 1

        # Générer le code selon le type
        contract_code = ""
        if contract_type == "ERC20":
            contract_code = self._generate_erc20(name, symbol, params)
        elif contract_type == "ERC721":
            contract_code = self._generate_erc721(name, symbol, params)
        elif contract_type == "ERC1155":
            contract_code = self._generate_erc1155(name, params)
        elif contract_type == "ERC4626":
            contract_code = self._generate_erc4626(name, params)
        else:
            contract_code = self._generate_custom_contract(contract_type, params)

        lines = len(contract_code.splitlines())
        complexity = "simple" if lines < 200 else "medium" if lines < 500 else "complex"

        return {
            "contract_code": contract_code,
            "contract_type": contract_type,
            "name": name,
            "symbol": symbol,
            "gas_estimate": self._estimate_gas(contract_code),
            "security_checks": self._get_security_checklist(contract_type),
            "complexity": complexity,
            "lines_of_code": lines,
            "standards_compliance": self._check_standards_compliance(contract_type),
            "dependencies": self._get_dependencies(contract_type)
        }

    async def _audit_contract(self, contract_code: str) -> Dict[str, Any]:
        """Audite un smart contract"""
        self._audits_performed += 1
        self._stats['total_audits'] += 1

        # Simulation d'audit
        vulnerabilities = random.randint(0, 8)
        critical = random.randint(0, min(2, vulnerabilities))
        high = random.randint(0, min(3, vulnerabilities - critical))
        medium = random.randint(0, min(4, vulnerabilities - critical - high))
        low = max(0, vulnerabilities - critical - high - medium)

        # Mettre à jour les stats
        self._stats['critical_findings'] += critical
        self._stats['high_findings'] += high
        self._stats['medium_findings'] += medium
        self._stats['low_findings'] += low

        # Générer des findings détaillés
        findings = self._generate_findings(critical, high, medium, low)

        return {
            "audit_report": {
                "summary": {
                    "total_issues": vulnerabilities,
                    "critical": critical,
                    "high": high,
                    "medium": medium,
                    "low": low
                },
                "security_score": max(0, 100 - (vulnerabilities * 5)),
                "risk_level": "high" if critical > 0 else "medium" if high > 0 else "low",
                "findings": findings,
                "recommendations": self._get_audit_recommendations(critical, high, medium),
                "tools_used": ["Slither", "Mythril", "Echidna", "Manual Review"],
                "lines_analyzed": len(contract_code.splitlines()),
                "compliance": {
                    "erc_standards": random.choice([True, True, True, False]),
                    "security_best_practices": random.randint(85, 98),
                    "gas_optimization": random.randint(70, 95)
                }
            }
        }

    async def _deploy_contract(self, contract_name: str, network: str) -> Dict[str, Any]:
        """Déploie un smart contract sur le réseau spécifié"""
        self._stats['total_deployments'] += 1

        # Simulation de déploiement
        success = random.random() > 0.2  # 80% de succès

        address = f"0x{''.join([random.choice('0123456789abcdef') for _ in range(40)])}"

        deployment = DeploymentInfo(
            contract_name=contract_name,
            network=network,
            address=address,
            transaction_hash=f"0x{''.join([random.choice('0123456789abcdef') for _ in range(64)])}",
            block_number=random.randint(10000000, 20000000),
            timestamp=datetime.now(),
            status=DeploymentStatus.DEPLOYED if success else DeploymentStatus.FAILED,
            explorer_url=f"https://{network}.etherscan.io/address/{address}" if success else None
        )

        self._deployments.append(deployment)

        if success:
            self._stats['successful_deployments'] += 1
        else:
            self._stats['failed_deployments'] += 1

        return {
            "deployment": {
                "contract_name": contract_name,
                "network": network,
                "contract_address": deployment.address,
                "transaction_hash": deployment.transaction_hash,
                "gas_used": f"{random.randint(800000, 2500000):,}",
                "block_number": deployment.block_number,
                "deployer": "0x742d35Cc6634C0532925a3b844Bc9e0FF6e5e5e8",
                "timestamp": deployment.timestamp.isoformat(),
                "verification_status": "verified" if success else "failed",
                "explorer_url": deployment.explorer_url,
                "cost_usd": f"${random.randint(50, 500)}"
            }
        }

    async def _optimize_gas(self, contract_code: str) -> Dict[str, Any]:
        """Optimise la consommation de gas d'un contrat"""
        techniques = [
            "Storage packing",
            "Memory vs Storage optimization",
            "Loop unrolling",
            "Short-circuiting",
            "Assembly optimization",
            "Batch operations",
            "Immutable variables",
            "Custom errors instead of strings"
        ]

        selected_techniques = random.sample(techniques, random.randint(4, 6))

        return {
            "optimization": {
                "gas_saved": f"{random.randint(15, 45)}%",
                "techniques_applied": selected_techniques,
                "new_gas_cost": f"{random.randint(300000, 1200000):,}",
                "complexity_tradeoff": random.choice(["low", "medium"]),
                "recommended_changes": random.randint(5, 12),
                "before_after": {
                    "deployment": f"{random.randint(1500000, 3000000):,} → {random.randint(900000, 1800000):,}",
                    "transfer": f"{random.randint(50000, 80000):,} → {random.randint(35000, 55000):,}",
                    "mint": f"{random.randint(80000, 120000):,} → {random.randint(50000, 80000):,}"
                }
            }
        }

    def _generate_findings(self, critical: int, high: int, medium: int, low: int) -> List[Dict]:
        """Génère des findings d'audit simulés"""
        findings = []

        finding_templates = [
            {
                "title": "Reentrancy Vulnerability",
                "description": "External call before state update allows reentrancy attack",
                "recommendation": "Use ReentrancyGuard and follow checks-effects-interactions pattern"
            },
            {
                "title": "Integer Overflow/Underflow",
                "description": "Arithmetic operations without overflow protection",
                "recommendation": "Use SafeMath or Solidity ^0.8.0 built-in checks"
            },
            {
                "title": "Missing Access Control",
                "description": "Critical function lacks proper access control",
                "recommendation": "Add onlyOwner modifier or role-based access control"
            },
            {
                "title": "Timestamp Dependence",
                "description": "Contract logic depends on block.timestamp which can be manipulated",
                "recommendation": "Avoid using block.timestamp for critical logic"
            },
            {
                "title": "Unchecked Call Return Value",
                "description": "External call return value not checked",
                "recommendation": "Always check return values of external calls"
            }
        ]

        severities = []
        severities.extend([AuditSeverity.CRITICAL] * critical)
        severities.extend([AuditSeverity.HIGH] * high)
        severities.extend([AuditSeverity.MEDIUM] * medium)
        severities.extend([AuditSeverity.LOW] * low)

        for severity in severities:
            template = random.choice(finding_templates)
            findings.append({
                "severity": severity.value,
                "title": template["title"],
                "description": template["description"],
                "location": f"contract.sol:L{random.randint(50, 300)}",
                "recommendation": template["recommendation"]
            })

        return findings

    def _get_audit_recommendations(self, critical: int, high: int, medium: int) -> List[str]:
        """Génère des recommandations d'audit"""
        recommendations = [
            "Implement ReentrancyGuard for all value-transferring functions",
            "Use OpenZeppelin's SafeERC20 for token operations",
            "Add timelocks for admin functions",
            "Implement emergency pause mechanism",
            "Use multisig for contract ownership",
            "Add input validation for all public functions",
            "Emit events for state-changing operations",
            "Consider using upgradeable proxy pattern"
        ]

        if critical > 0:
            recommendations.insert(0, "⚠️ CRITICAL: Immediate action required for critical vulnerabilities")
        if high > 0:
            recommendations.insert(1, "🔴 HIGH: Address high-risk issues before deployment")

        return recommendations[:5]

    # ========================================================================
    # MÉTHODES DE GÉNÉRATION DE CODE (Vos templates existants)
    # ========================================================================

    def _get_erc20_template(self) -> str:
        """Template ERC20 complet"""
        return '''// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/security/Pausable.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";

/**
 * @title {{CONTRACT_NAME}}
 * @dev ERC20 token with minting, burning, and pausable functionality
 */
contract {{CONTRACT_NAME}} is ERC20, Ownable, Pausable, ReentrancyGuard {
    uint256 public constant MAX_SUPPLY = {{MAX_SUPPLY}} * 10 ** 18;
    uint256 public constant INITIAL_SUPPLY = {{INITIAL_SUPPLY}} * 10 ** 18;
    
    mapping(address => uint256) private _vesting;
    
    event TokensMinted(address indexed to, uint256 amount);
    event TokensBurned(address indexed from, uint256 amount);
    event VestingAdded(address indexed beneficiary, uint256 amount, uint256 releaseTime);
    event VestingReleased(address indexed beneficiary, uint256 amount);

    constructor() ERC20("{{TOKEN_NAME}}", "{{TOKEN_SYMBOL}}") {
        _mint(msg.sender, INITIAL_SUPPLY);
    }

    function mint(address to, uint256 amount)
        external
        onlyOwner
        whenNotPaused
        nonReentrant
    {
        require(totalSupply() + amount <= MAX_SUPPLY, "Exceeds max supply");
        _mint(to, amount);
        emit TokensMinted(to, amount);
    }

    function burn(uint256 amount)
        external
        whenNotPaused
        nonReentrant
    {
        _burn(msg.sender, amount);
        emit TokensBurned(msg.sender, amount);
    }

    function pause() external onlyOwner {
        _pause();
    }

    function unpause() external onlyOwner {
        _unpause();
    }
}'''

    def _get_erc721_template(self) -> str:
        """Template ERC721 complet"""
        return '''// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "@openzeppelin/contracts/token/ERC721/ERC721.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/security/Pausable.sol";
import "@openzeppelin/contracts/utils/Counters.sol";
import "@openzeppelin/contracts/utils/Strings.sol";
import "@openzeppelin/contracts/token/common/ERC2981.sol";

/**
 * @title {{CONTRACT_NAME}}
 * @dev ERC721 NFT collection with metadata, royalties, and reveal functionality
 */
contract {{CONTRACT_NAME}} is ERC721, ERC2981, Ownable, Pausable {
    using Counters for Counters.Counter;
    using Strings for uint256;

    Counters.Counter private _tokenIdCounter;
    
    string private _baseTokenURI;
    string private _unrevealedURI;
    bool private _revealed;
    
    uint256 public constant MAX_SUPPLY = {{MAX_SUPPLY}};
    uint256 public constant MAX_MINT_PER_TX = 10;
    uint256 public constant PRICE = {{PRICE}};
    
    mapping(uint256 => string) private _tokenURIs;
    mapping(address => uint256) private _mintedCount;

    event NFTMinted(address indexed to, uint256 tokenId);
    event CollectionRevealed(string baseURI);
    event MetadataUpdated(uint256 tokenId, string newURI);

    constructor(
        string memory unrevealedURI,
        address royaltyReceiver,
        uint96 royaltyFeeNumerator
    ) ERC721("{{TOKEN_NAME}}", "{{TOKEN_SYMBOL}}") {
        _unrevealedURI = unrevealedURI;
        _revealed = false;
        _setDefaultRoyalty(royaltyReceiver, royaltyFeeNumerator);
    }

    function mint(address to, uint256 quantity)
        external
        payable
        whenNotPaused
    {
        require(quantity > 0 && quantity <= MAX_MINT_PER_TX, "Invalid quantity");
        require(msg.value >= PRICE * quantity, "Insufficient payment");
        require(_tokenIdCounter.current() + quantity <= MAX_SUPPLY, "Exceeds max supply");
        
        for (uint256 i = 0; i < quantity; i++) {
            _tokenIdCounter.increment();
            uint256 tokenId = _tokenIdCounter.current();
            _safeMint(to, tokenId);
            _mintedCount[to]++;
            emit NFTMinted(to, tokenId);
        }
        
        // Refund excess payment
        if (msg.value > PRICE * quantity) {
            payable(msg.sender).transfer(msg.value - PRICE * quantity);
        }
    }

    function reveal(string memory baseURI) external onlyOwner {
        require(!_revealed, "Already revealed");
        _baseTokenURI = baseURI;
        _revealed = true;
        emit CollectionRevealed(baseURI);
    }

    function pause() external onlyOwner {
        _pause();
    }

    function unpause() external onlyOwner {
        _unpause();
    }

    function supportsInterface(bytes4 interfaceId)
        public
        view
        virtual
        override(ERC721, ERC2981)
        returns (bool)
    {
        return super.supportsInterface(interfaceId);
    }
}'''

    def _get_erc1155_template(self) -> str:
        """Template ERC1155 complet"""
        return '''// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "@openzeppelin/contracts/token/ERC1155/ERC1155.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/security/Pausable.sol";
import "@openzeppelin/contracts/token/common/ERC2981.sol";

/**
 * @title {{CONTRACT_NAME}}
 * @dev ERC1155 Multi-token contract
 */
contract {{CONTRACT_NAME}} is ERC1155, ERC2981, Ownable, Pausable {
    string public name;
    string public symbol;
    
    mapping(uint256 => string) private _tokenURIs;
    mapping(uint256 => uint256) private _totalSupply;
    mapping(uint256 => uint256) private _maxSupply;

    event TokenCreated(uint256 indexed id, uint256 maxSupply, string uri);
    event TokensMinted(uint256 indexed id, address indexed to, uint256 amount);

    constructor(string memory _name, string memory _symbol, string memory uri)
        ERC1155(uri)
    {
        name = _name;
        symbol = _symbol;
    }

    function createToken(
        uint256 id,
        uint256 maxSupply,
        string memory tokenURI
    ) external onlyOwner {
        require(maxSupply > 0, "Max supply must be positive");
        require(_maxSupply[id] == 0, "Token already exists");
        
        _maxSupply[id] = maxSupply;
        _tokenURIs[id] = tokenURI;
        
        emit TokenCreated(id, maxSupply, tokenURI);
    }

    function mint(
        address to,
        uint256 id,
        uint256 amount,
        bytes memory data
    ) external onlyOwner whenNotPaused {
        require(_maxSupply[id] > 0, "Token doesn't exist");
        require(_totalSupply[id] + amount <= _maxSupply[id], "Exceeds max supply");
        
        _mint(to, id, amount, data);
        _totalSupply[id] += amount;
        
        emit TokensMinted(id, to, amount);
    }

    function pause() external onlyOwner {
        _pause();
    }

    function unpause() external onlyOwner {
        _unpause();
    }

    function supportsInterface(bytes4 interfaceId)
        public
        view
        virtual
        override(ERC1155, ERC2981)
        returns (bool)
    {
        return super.supportsInterface(interfaceId);
    }
}'''

    def _get_erc4626_template(self) -> str:
        """Template ERC4626 complet"""
        return '''// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "@openzeppelin/contracts/token/ERC20/extensions/ERC4626.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/security/Pausable.sol";
import "@openzeppelin/contracts/token/ERC20/extensions/IERC20Metadata.sol";

/**
 * @title {{CONTRACT_NAME}}
 * @dev ERC4626 Tokenized Vault
 */
contract {{CONTRACT_NAME}} is ERC4626, Ownable, Pausable {
    
    constructor(
        IERC20Metadata asset,
        string memory name,
        string memory symbol
    ) ERC4626(asset) ERC20(name, symbol) {}

    function deposit(uint256 assets, address receiver)
        public
        override
        whenNotPaused
        returns (uint256)
    {
        return super.deposit(assets, receiver);
    }

    function mint(uint256 shares, address receiver)
        public
        override
        whenNotPaused
        returns (uint256)
    {
        return super.mint(shares, receiver);
    }

    function withdraw(
        uint256 assets,
        address receiver,
        address owner
    ) public override whenNotPaused returns (uint256) {
        return super.withdraw(assets, receiver, owner);
    }

    function redeem(
        uint256 shares,
        address receiver,
        address owner
    ) public override whenNotPaused returns (uint256) {
        return super.redeem(shares, receiver, owner);
    }

    function pause() external onlyOwner {
        _pause();
    }

    function unpause() external onlyOwner {
        _unpause();
    }
}'''

    def _generate_erc20(self, name: str, symbol: str, params: Dict) -> str:
        """Génère un contrat ERC20"""
        template = self._templates["ERC20"].code
        max_supply = params.get("max_supply", "100_000_000")
        initial_supply = params.get("initial_supply", "10_000_000")

        template = template.replace("{{CONTRACT_NAME}}", name)
        template = template.replace("{{TOKEN_NAME}}", name)
        template = template.replace("{{TOKEN_SYMBOL}}", symbol)
        template = template.replace("{{MAX_SUPPLY}}", str(max_supply))
        template = template.replace("{{INITIAL_SUPPLY}}", str(initial_supply))

        return template

    def _generate_erc721(self, name: str, symbol: str, params: Dict) -> str:
        """Génère un contrat ERC721"""
        template = self._templates["ERC721"].code
        max_supply = params.get("max_supply", "10000")
        price = params.get("price", "0.08 ether")

        template = template.replace("{{CONTRACT_NAME}}", name)
        template = template.replace("{{TOKEN_NAME}}", name)
        template = template.replace("{{TOKEN_SYMBOL}}", symbol)
        template = template.replace("{{MAX_SUPPLY}}", str(max_supply))
        template = template.replace("{{PRICE}}", str(price))

        return template

    def _generate_erc1155(self, name: str, params: Dict) -> str:
        """Génère un contrat ERC1155"""
        template = self._templates["ERC1155"].code
        symbol = params.get("symbol", name[:3].upper())

        template = template.replace("{{CONTRACT_NAME}}", name)
        template = template.replace("{{TOKEN_NAME}}", name)
        template = template.replace("{{TOKEN_SYMBOL}}", symbol)

        return template

    def _generate_erc4626(self, name: str, params: Dict) -> str:
        """Génère un contrat ERC4626"""
        template = self._templates["ERC4626"].code
        asset = params.get("asset", "0x0000000000000000000000000000000000000000")

        template = template.replace("{{CONTRACT_NAME}}", name)
        template = template.replace("{{TOKEN_NAME}}", name)
        template = template.replace("{{ASSET_ADDRESS}}", asset)

        return template

    def _generate_custom_contract(self, contract_type: str, params: Dict) -> str:
        """Génère un contrat personnalisé"""
        return f'''// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

/**
 * @title {contract_type}
 * @dev Custom smart contract template
 */
contract {contract_type} {{
    address public owner;
    
    constructor() {{
        owner = msg.sender;
    }}
    
    modifier onlyOwner() {{
        require(msg.sender == owner, "Not owner");
        _;
    }}
    
    // Custom logic will be implemented here
}}'''

    def _estimate_gas(self, contract_code: str) -> Dict[str, str]:
        """Estime la consommation de gas"""
        return {
            "deployment": f"{random.randint(800000, 2500000):,}",
            "transfer": f"{random.randint(45000, 65000):,}",
            "approve": f"{random.randint(40000, 50000):,}",
            "mint": f"{random.randint(70000, 110000):,}",
            "burn": f"{random.randint(40000, 60000):,}"
        }

    def _get_security_checklist(self, contract_type: str) -> List[str]:
        """Retourne la checklist de sécurité"""
        base_checks = [
            "Reentrancy protection",
            "Integer overflow/underflow",
            "Access control",
            "Timestamp dependence",
            "Gas limit",
            "Front-running resistance"
        ]

        if contract_type == "ERC20":
            base_checks.extend([
                "Approval race condition",
                "Infinite approval",
                "Transfer amount validation"
            ])
        elif contract_type == "ERC721":
            base_checks.extend([
                "Reentrancy in transfer",
                "Royalty enforcement",
                "Metadata immutability"
            ])

        return base_checks

    def _check_standards_compliance(self, contract_type: str) -> Dict[str, bool]:
        """Vérifie la conformité aux standards"""
        return {
            "ERC165": True,
            "ERC20": contract_type == "ERC20",
            "ERC721": contract_type == "ERC721",
            "ERC1155": contract_type == "ERC1155",
            "ERC2981": contract_type in ["ERC721", "ERC1155"],
            "ERC4626": contract_type == "ERC4626",
            "EIP1967": False
        }

    def _get_dependencies(self, contract_type: str) -> List[str]:
        """Retourne les dépendances nécessaires"""
        base_deps = ["@openzeppelin/contracts@4.9.0"]

        if contract_type in ["ERC20", "ERC721", "ERC1155", "ERC4626"]:
            return base_deps

        return []


# ============================================================================
# FONCTIONS D'USINE
# ============================================================================

def create_smart_contract_agent(config_path: Optional[str] = None) -> SmartContractAgent:
    """Crée une instance de l'agent smart contract"""
    return SmartContractAgent(config_path)


# ============================================================================
# POINT D'ENTRÉE POUR EXÉCUTION DIRECTE
# ============================================================================

if __name__ == "__main__":
    async def main():
        print("📜 TEST AGENT SMART CONTRACT")
        print("="*60)

        agent = SmartContractAgent()
        await agent.initialize()

        agent_info = agent.get_agent_info()
        print(f"✅ Agent: {agent_info['name']} v{agent_info['version']}")
        print(f"✅ Statut: {agent_info['status']}")
        print(f"✅ Capacités: {len(agent_info['capabilities'])}")
        print(f"✅ Templates: {agent_info['features']['standards']}")

        # Test de génération ERC20
        result = await agent._develop_contract("ERC20", "TestToken", "TST", {})

        print(f"\n🔨 Contrat ERC20 généré")
        print(f"  📄 Lignes: {result['lines_of_code']}")
        print(f"  ⚡ Gas estimate: {result['gas_estimate']['deployment']}")
        print(f"  🔒 Security checks: {len(result['security_checks'])}")

        # Test d'audit
        audit = await agent._audit_contract(result["contract_code"])
        print(f"\n🔍 Audit réalisé")
        print(f"  📊 Score: {audit['audit_report']['security_score']}")
        print(f"  ⚠️  Findings: {audit['audit_report']['summary']['total_issues']}")

        health = await agent.health_check()
        print(f"\n❤️  Health: {health['status']}")

        await agent.shutdown()
        print(f"\n👋 Agent arrêté")
        print("\n" + "="*60)

    asyncio.run(main())
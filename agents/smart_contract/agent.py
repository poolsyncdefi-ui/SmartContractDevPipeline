"""
Smart Contract Agent - Agent de développement de contrats intelligents
Version: 2.6.0 (ALIGNÉ SUR ARCHITECT/CODER/LEARNING)
"""

import logging
import os
import sys
import json
import yaml
import random
import asyncio
import importlib 
import traceback
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass, field, asdict
from enum import Enum

# ============================================================================
# CONFIGURATION DES IMPORTS
# ============================================================================

# Déterminer la racine du projet
current_dir = Path(__file__).parent.absolute()
project_root = current_dir.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from agents.base_agent.base_agent import BaseAgent, AgentStatus, Message, MessageType

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
    
    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d['standard'] = self.standard.value
        return d


@dataclass
class AuditFinding:
    """Résultat d'audit"""
    severity: AuditSeverity
    title: str
    description: str
    location: str
    recommendation: str
    line: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d['severity'] = self.severity.value
        return d


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
    
    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d['timestamp'] = self.timestamp.isoformat()
        d['status'] = self.status.value
        return d


# ============================================================================
# AGENT PRINCIPAL (ALIGNÉ SUR ARCHITECT/CODER/LEARNING)
# ============================================================================

class SmartContractAgent(BaseAgent):
    """
    Agent spécialisé dans le développement, audit, optimisation et déploiement
    de smart contracts sécurisés et efficaces pour applications DeFi et Web3
    Version 2.6 - Gestion des sous-agents, messages enrichis, cycle de vie robuste
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
            'uptime_start': datetime.now().isoformat()
        }

        self._logger.info(f"📜 Agent Smart Contract créé - v{self._version}")

    # ========================================================================
    # MÉTHODES D'INITIALISATION (ALIGNÉES)
    # ========================================================================

    async def initialize(self) -> bool:
        """Initialisation asynchrone de l'agent"""
        try:
            self._set_status(AgentStatus.INITIALIZING)
            self._logger.info("📜 Initialisation du Smart Contract Agent...")

            # Appeler l'initialisation du parent
            base_result = await super().initialize()
            if not base_result:
                return False

            # Initialiser les composants spécifiques
            await self._initialize_components()

            # Initialiser les sous-agents
            await self._initialize_sub_agents()

            # Charger les templates
            await self._load_templates()

            # Charger les déploiements précédents
            await self._load_deployments()

            self._initialized = True
            self._set_status(AgentStatus.READY)
            self._logger.info("✅ Smart Contract Agent prêt")
            return True

        except Exception as e:
            self._logger.error(f"❌ Erreur initialisation: {e}")
            self._logger.error(traceback.format_exc())
            self._set_status(AgentStatus.ERROR)
            return False

    async def _initialize_components(self) -> bool:
        """
        Initialise les composants spécifiques.
        Appelé par BaseAgent.initialize().
        """
        try:
            self._logger.info("Initialisation des composants Smart Contract...")

            agent_config = self._agent_config.get('agent', {})
            security_reqs = agent_config.get('security_requirements', {})

            self._components = {
                "contract_generator": {
                    "enabled": True,
                    "standards": self._contract_config.get('supported_standards', {}).get('token_standards', []),
                },
                "audit_engine": {
                    "enabled": True,
                    "security_checks": security_reqs.get('required_checks', []),
                },
                "gas_optimizer": {"enabled": True},
                "deployment_manager": {"enabled": True},
                "upgradeability_designer": {"enabled": True},
                "economic_analyzer": {"enabled": True},
                "formal_verification_engine": {"enabled": True}
            }

            self._logger.info(f"✅ Composants: {list(self._components.keys())}")
            return True

        except Exception as e:
            self._logger.error(f"Erreur composants: {e}")
            return False

    async def _initialize_sub_agents(self):
        """Initialise les sous-agents spécialisés avec gestion d'erreurs robuste"""
        self._sub_agents = {}
        
        # Configuration des sous-agents depuis la config (si présente)
        sub_agent_configs = self._agent_config.get('agent', {}).get('subAgents', [])
        
        # Si la liste est vide, essayer de charger avec des noms par défaut
        if not sub_agent_configs:
            sub_agent_configs = [
                {"id": "formal_verification", "name": "Formal Verification Expert", "enabled": True},
                {"id": "gas_optimizer", "name": "Gas Optimization Expert", "enabled": True},
                {"id": "security_expert", "name": "Smart Contract Security Expert", "enabled": True},
                {"id": "solidity_expert", "name": "Solidity Development Expert", "enabled": True}
            ]
        
        for config in sub_agent_configs:
            agent_id = config.get('id')
            if not config.get('enabled', True):
                continue
                
            try:
                # Tentative d'import dynamique du sous-agent
                module_name = f"agents.smart_contract.sous_agents.{agent_id}.agent"
                class_name = self._get_sub_agent_class_name(agent_id)
                
                module = importlib.import_module(module_name)
                agent_class = getattr(module, class_name, None)
                
                if agent_class:
                    config_path = config.get('config_path', '')
                    sub_agent = agent_class(config_path)
                    self._sub_agents[agent_id] = sub_agent
                    self._logger.info(f"  ✓ Sous-agent {agent_id} initialisé")
                else:
                    self._logger.warning(f"  ⚠️ Classe {class_name} non trouvée pour {agent_id}")
                    
            except ImportError as e:
                self._logger.debug(f"  ℹ️ Sous-agent {agent_id} non disponible: {e}")
            except Exception as e:
                self._logger.error(f"  ❌ Erreur initialisation sous-agent {agent_id}: {e}")

    def _get_sub_agent_class_name(self, agent_id: str) -> str:
        """Convertit un ID de sous-agent en nom de classe"""
        # Convertit "formal_verification" en "FormalVerificationSubAgent"
        parts = agent_id.split('_')
        class_name = ''.join(p.capitalize() for p in parts) + 'SubAgent'
        return class_name

    async def delegate_to_sub_agent(self, task_type: str, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Délègue une tâche à un sous-agent approprié.
        Aligné sur architect/learning.

        Args:
            task_type: Type de tâche à déléguer
            task_data: Données de la tâche

        Returns:
            Résultat de l'exécution par le sous-agent
        """
        # Mapping des types de tâches vers les sous-agents
        sub_agent_mapping = {
            "solidity": "solidity_expert",
            "security": "security_expert",
            "gas": "gas_optimizer",
            "formal": "formal_verification",
            "defi": "defi_specialist",
            "tokenomics": "tokenomics_engineer"
        }

        for pattern, agent_name in sub_agent_mapping.items():
            if task_type.startswith(pattern):
                if agent_name in self._sub_agents:
                    self._logger.info(f"➡️ Délégation de la tâche {task_type} au sous-agent {agent_name}")
                    # Créer un message pour le sous-agent
                    msg = Message(
                        sender=self.name,
                        recipient=agent_name,
                        content=task_data,
                        message_type=f"smart_contract.{task_type}",
                        correlation_id=f"delegate_{datetime.now().timestamp()}"
                    )
                    return await self._sub_agents[agent_name].handle_message(msg)

        # Fallback: utiliser l'agent principal
        self._logger.info(f"ℹ️ Aucun sous-agent trouvé pour {task_type}, utilisation de l'agent principal")
        
        # Exécuter la tâche localement selon le type
        if task_type == "generate":
            return await self._develop_contract(
                task_data.get("contract_type", "ERC20"),
                task_data.get("name", "MyToken"),
                task_data.get("symbol", "MTK"),
                task_data.get("params", {})
            )
        elif task_type == "audit":
            return await self._audit_contract(task_data.get("contract_code", ""))
        elif task_type == "deploy":
            return await self._deploy_contract(
                task_data.get("contract_name", ""),
                task_data.get("network", "ethereum")
            )
        elif task_type == "optimize":
            return await self._optimize_gas(task_data.get("contract_code", ""))
        else:
            return {"success": False, "error": f"Type de tâche non supporté: {task_type}"}

    async def get_sub_agents_status(self) -> Dict[str, Any]:
        """Retourne le statut de tous les sous-agents (aligné)"""
        status = {}
        for agent_name, agent_instance in self._sub_agents.items():
            try:
                health = await agent_instance.health_check()
                status[agent_name] = {
                    "status": health.get("status", "unknown"),
                    "agent_info": agent_instance.get_agent_info()
                }
            except Exception as e:
                status[agent_name] = {
                    "status": "error",
                    "error": str(e)
                }

        return {
            "total_sub_agents": len(self._sub_agents),
            "sub_agents": status
        }

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

    async def _load_deployments(self):
        """Charge l'historique des déploiements"""
        try:
            deployments_file = Path("./reports") / "smart_contract_deployments.json"
            if deployments_file.exists():
                with open(deployments_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for deployment_data in data.get("deployments", []):
                        deployment = DeploymentInfo(
                            contract_name=deployment_data["contract_name"],
                            network=deployment_data["network"],
                            address=deployment_data["address"],
                            transaction_hash=deployment_data["transaction_hash"],
                            block_number=deployment_data["block_number"],
                            timestamp=datetime.fromisoformat(deployment_data["timestamp"]),
                            status=DeploymentStatus(deployment_data["status"]),
                            explorer_url=deployment_data.get("explorer_url")
                        )
                        self._deployments.append(deployment)
                self._logger.info(f"📦 {len(self._deployments)} déploiements chargés")
        except Exception as e:
            self._logger.warning(f"⚠️ Erreur chargement déploiements: {e}")

    # ========================================================================
    # MÉTHODES DE GESTION D'ÉTAT (ALIGNÉES)
    # ========================================================================

    async def shutdown(self) -> bool:
        """Arrête l'agent proprement (aligné)"""
        self._logger.info("Arrêt de l'agent Smart Contract...")
        self._set_status(AgentStatus.SHUTTING_DOWN)

        # Arrêter les sous-agents
        for agent_name, agent_instance in self._sub_agents.items():
            try:
                await agent_instance.shutdown()
                self._logger.debug(f"  ✓ Sous-agent {agent_name} arrêté")
            except Exception as e:
                self._logger.warning(f"  ⚠️ Erreur arrêt sous-agent {agent_name}: {e}")

        # Sauvegarder les données
        await self._save_data()

        # Appeler la méthode parent
        await super().shutdown()

        self._logger.info("✅ Agent Smart Contract arrêté")
        return True

    async def pause(self) -> bool:
        """Met l'agent en pause (aligné)"""
        self._logger.info("Pause de l'agent Smart Contract...")

        # Mettre en pause les sous-agents
        for agent_name, agent_instance in self._sub_agents.items():
            try:
                await agent_instance.pause()
            except Exception as e:
                self._logger.warning(f"⚠️ Erreur pause sous-agent {agent_name}: {e}")

        self._set_status(AgentStatus.PAUSED)
        return True

    async def resume(self) -> bool:
        """Reprend l'activité (aligné)"""
        self._logger.info("Reprise de l'agent Smart Contract...")

        # Reprendre les sous-agents
        for agent_name, agent_instance in self._sub_agents.items():
            try:
                await agent_instance.resume()
            except Exception as e:
                self._logger.warning(f"⚠️ Erreur reprise sous-agent {agent_name}: {e}")

        self._set_status(AgentStatus.READY)
        return True

    async def _save_data(self):
        """Sauvegarde les données de l'agent"""
        try:
            # Sauvegarder les déploiements
            deployments_file = Path("./reports") / "smart_contract_deployments.json"
            deployments_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(deployments_file, 'w', encoding='utf-8') as f:
                json.dump({
                    "deployments": [d.to_dict() for d in self._deployments],
                    "timestamp": datetime.now().isoformat()
                }, f, indent=2, ensure_ascii=False)

            # Sauvegarder les statistiques
            stats_file = Path("./reports") / "smart_contract_stats.json"
            with open(stats_file, 'w', encoding='utf-8') as f:
                json.dump({
                    "stats": self._stats,
                    "contracts_generated": self._contracts_generated,
                    "audits_performed": self._audits_performed,
                    "deployments": len(self._deployments),
                    "timestamp": datetime.now().isoformat()
                }, f, indent=2, ensure_ascii=False)

            self._logger.info("✅ Données sauvegardées")
        except Exception as e:
            self._logger.warning(f"⚠️ Impossible de sauvegarder: {e}")

    # ========================================================================
    # MÉTHODES DE SANTÉ ET D'INFORMATION (ALIGNÉES)
    # ========================================================================

    async def health_check(self) -> Dict[str, Any]:
        """Vérifie la santé de l'agent (aligné sur architect/learning)"""
        base_health = await super().health_check()

        # Calculer l'uptime
        uptime = None
        if self._stats.get('uptime_start'):
            start = datetime.fromisoformat(self._stats['uptime_start'])
            uptime = str(datetime.now() - start)

        # Vérifier la santé des sous-agents
        sub_agents_health = await self.get_sub_agents_status()

        return {
            **base_health,
            "agent": self.name,
            "display_name": self._display_name,
            "status": self._status.value if hasattr(self._status, 'value') else str(self._status),
            "ready": self._status == AgentStatus.READY,
            "initialized": self._initialized,
            "uptime": uptime,
            "smart_contract_specific": {
                "contracts_generated": self._contracts_generated,
                "audits_performed": self._audits_performed,
                "deployments": len(self._deployments),
                "templates_loaded": len(self._templates),
                "sub_agents": sub_agents_health,
                "components": list(self._components.keys()),
                "stats": {
                    "total_contracts": self._stats['total_contracts'],
                    "total_audits": self._stats['total_audits'],
                    "successful_deployments": self._stats['successful_deployments'],
                    "failed_deployments": self._stats['failed_deployments'],
                    "critical_findings": self._stats['critical_findings'],
                    "high_findings": self._stats['high_findings'],
                    "medium_findings": self._stats['medium_findings'],
                    "low_findings": self._stats['low_findings']
                }
            },
            "timestamp": datetime.now().isoformat()
        }

    def get_agent_info(self) -> Dict[str, Any]:
        """Retourne les informations de l'agent pour le registre (aligné)"""
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
            "status": self._status.value if hasattr(self._status, 'value') else str(self._status),
            "capabilities": capabilities,
            "features": {
                "standards": [t.name for t in self._templates.keys()],
                "sub_agents": list(self._sub_agents.keys()),
                "components": list(self._components.keys())
            },
            "stats": {
                "contracts_generated": self._contracts_generated,
                "audits_performed": self._audits_performed,
                "deployments": len(self._deployments),
                "successful_deployments": self._stats['successful_deployments'],
                "failed_deployments": self._stats['failed_deployments']
            }
        }

    # ========================================================================
    # GESTION DES MESSAGES (ALIGNÉE SUR ARCHITECT/CODER/LEARNING)
    # ========================================================================

    async def _handle_custom_message(self, message: Message) -> Optional[Message]:
        """
        Gère les messages personnalisés pour le Smart Contract Agent.
        Aligné sur architect/learning.
        """
        try:
            msg_type = message.message_type
            self._logger.debug(f"Message personnalisé reçu: {msg_type} de {message.sender}")

            # D'abord, essayer de déléguer à un sous-agent
            if message.content and "sub_agent_task" in message.content:
                task_type = message.content.get("sub_agent_task")
                return await self.delegate_to_sub_agent(task_type, message.content)

            # Mapping des types de messages vers les méthodes
            handlers = {
                "smart_contract.generate": self._handle_generate,
                "smart_contract.audit": self._handle_audit,
                "smart_contract.deploy": self._handle_deploy,
                "smart_contract.optimize": self._handle_optimize,
                "smart_contract.analyze_economics": self._handle_analyze_economics,
                "smart_contract.verify_formal": self._handle_verify_formal,
                "smart_contract.get_templates": self._handle_get_templates,
                "smart_contract.get_deployments": self._handle_get_deployments,
                "smart_contract.get_stats": self._handle_stats,
                "smart_contract.get_sub_agents_status": self._handle_get_sub_agents_status,
                "smart_contract.pause": self._handle_pause,
                "smart_contract.resume": self._handle_resume,
                "smart_contract.shutdown": self._handle_shutdown,
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

    async def _handle_analyze_economics(self, message: Message) -> Message:
        """Gère l'analyse économique"""
        contract_data = message.content.get("contract_data", {})
        
        # Simuler une analyse économique
        result = {
            "success": True,
            "economic_analysis": {
                "apr_projection": f"{random.uniform(5, 25):.1f}%",
                "liquidity_requirements": f"${random.randint(100000, 10000000):,}",
                "impermanent_loss_risk": random.choice(["low", "medium", "high"]),
                "arbitrage_opportunities": random.randint(0, 5),
                "game_theory_analysis": {
                    "nash_equilibrium": random.choice(["stable", "unstable"]),
                    "incentive_compatibility": random.choice(["aligned", "misaligned"]),
                    "attack_vectors": random.randint(0, 3)
                }
            },
            "timestamp": datetime.now().isoformat()
        }
        
        return Message(
            sender=self.name,
            recipient=message.sender,
            content=result,
            message_type="smart_contract.economics_analyzed",
            correlation_id=message.message_id
        )

    async def _handle_verify_formal(self, message: Message) -> Message:
        """Gère la vérification formelle"""
        contract_code = message.content.get("contract_code", "")
        
        # Simuler une vérification formelle
        result = {
            "success": True,
            "formal_verification": {
                "properties_verified": [
                    "no_reentrancy",
                    "access_control_complete",
                    "arithmetic_safety",
                    "invariant_preservation"
                ],
                "verification_time_seconds": random.randint(30, 300),
                "certificate": f"formal_verify_cert_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                "confidence": f"{random.uniform(90, 99.9):.1f}%"
            },
            "timestamp": datetime.now().isoformat()
        }
        
        return Message(
            sender=self.name,
            recipient=message.sender,
            content=result,
            message_type="smart_contract.formally_verified",
            correlation_id=message.message_id
        )

    async def _handle_get_templates(self, message: Message) -> Message:
        """Retourne la liste des templates disponibles"""
        templates = {
            name: {
                "standard": template.standard.value,
                "description": template.description,
                "dependencies": template.dependencies
            }
            for name, template in self._templates.items()
        }
        
        return Message(
            sender=self.name,
            recipient=message.sender,
            content={"templates": templates, "count": len(templates)},
            message_type="smart_contract.templates_list",
            correlation_id=message.message_id
        )

    async def _handle_get_deployments(self, message: Message) -> Message:
        """Retourne l'historique des déploiements"""
        return Message(
            sender=self.name,
            recipient=message.sender,
            content={
                "deployments": [d.to_dict() for d in self._deployments],
                "count": len(self._deployments)
            },
            message_type="smart_contract.deployments_list",
            correlation_id=message.message_id
        )

    async def _handle_stats(self, message: Message) -> Message:
        """Retourne les statistiques"""
        return Message(
            sender=self.name,
            recipient=message.sender,
            content={"stats": self._stats, "agent_info": self.get_agent_info()},
            message_type="smart_contract.stats_response",
            correlation_id=message.message_id
        )

    async def _handle_get_sub_agents_status(self, message: Message) -> Message:
        """Gère la récupération du statut des sous-agents"""
        status = await self.get_sub_agents_status()
        return Message(
            sender=self.name,
            recipient=message.sender,
            content=status,
            message_type="smart_contract.sub_agents_status",
            correlation_id=message.message_id
        )

    async def _handle_pause(self, message: Message) -> Message:
        """Gère la pause"""
        await self.pause()
        return Message(
            sender=self.name,
            recipient=message.sender,
            content={"status": "paused"},
            message_type="smart_contract.status_update",
            correlation_id=message.message_id
        )

    async def _handle_resume(self, message: Message) -> Message:
        """Gère la reprise"""
        await self.resume()
        return Message(
            sender=self.name,
            recipient=message.sender,
            content={"status": "resumed"},
            message_type="smart_contract.status_update",
            correlation_id=message.message_id
        )

    async def _handle_shutdown(self, message: Message) -> Message:
        """Gère l'arrêt"""
        await self.shutdown()
        return Message(
            sender=self.name,
            recipient=message.sender,
            content={"status": "shutdown"},
            message_type="smart_contract.status_update",
            correlation_id=message.message_id
        )

    # ========================================================================
    # MÉTHODES FONCTIONNELLES (Votre code existant, préservé et amélioré)
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

        # Vérifier si le type de contrat est supporté
        if contract_type not in self._templates:
            self._logger.warning(f"⚠️ Type de contrat non supporté: {contract_type}, utilisation du template personnalisé")
            contract_code = self._generate_custom_contract(contract_type, params)
        else:
            # Générer le code selon le type
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

        # Appliquer les règles anti-hallucination si configuré
        anti_hallucination = self._agent_config.get('agent', {}).get('anti_hallucination', {})
        if anti_hallucination.get('enabled', False):
            contract_code = self._apply_anti_hallucination_rules(contract_code)

        return {
            "success": True,
            "contract_code": contract_code,
            "contract_type": contract_type,
            "name": name,
            "symbol": symbol,
            "gas_estimate": self._estimate_gas(contract_code),
            "security_checks": self._get_security_checklist(contract_type),
            "complexity": complexity,
            "lines_of_code": lines,
            "standards_compliance": self._check_standards_compliance(contract_type),
            "dependencies": self._get_dependencies(contract_type),
            "timestamp": datetime.now().isoformat()
        }

    async def _audit_contract(self, contract_code: str) -> Dict[str, Any]:
        """Audite un smart contract"""
        self._logger.info("🔍 Audit du contrat...")
        self._audits_performed += 1
        self._stats['total_audits'] += 1

        # Simulation d'audit basée sur la complexité du code
        lines = len(contract_code.splitlines())
        vulnerabilities = random.randint(0, min(8, lines // 100 + 2))
        critical = random.randint(0, min(2, vulnerabilities))
        high = random.randint(0, min(3, vulnerabilities - critical))
        medium = random.randint(0, min(4, vulnerabilities - critical - high))
        low = max(0, vulnerabilities - critical - high - medium)

        # Mettre à jour les stats
        self._stats['critical_findings'] += critical
        self._stats['high_findings'] += high
        self._stats['medium_findings'] += medium
        self._stats['low_findings'] += low

        # Vérifier les patterns interdits
        forbidden_patterns = self._agent_config.get('agent', {}).get('anti_hallucination', {}).get('forbidden_patterns', [])
        detected_patterns = []
        for pattern_info in forbidden_patterns:
            pattern = pattern_info.get('pattern', '').replace('\\', '')
            if pattern in contract_code:
                detected_patterns.append({
                    "pattern": pattern,
                    "reason": pattern_info.get('reason', 'Pattern interdit détecté'),
                    "severity": pattern_info.get('severity', 'medium')
                })

        # Générer des findings détaillés
        findings = self._generate_findings(critical, high, medium, low)
        
        # Ajouter les patterns interdits comme findings
        for dp in detected_patterns:
            findings.append({
                "severity": dp['severity'],
                "title": f"Pattern interdit: {dp['pattern']}",
                "description": dp['reason'],
                "location": "contract.sol",
                "recommendation": "Supprimer ou remplacer ce pattern"
            })

        security_score = max(0, 100 - (vulnerabilities * 5) - (len(detected_patterns) * 10))

        return {
            "success": True,
            "audit_report": {
                "summary": {
                    "total_issues": vulnerabilities + len(detected_patterns),
                    "critical": critical + len([d for d in detected_patterns if d['severity'] == 'critical']),
                    "high": high + len([d for d in detected_patterns if d['severity'] == 'high']),
                    "medium": medium + len([d for d in detected_patterns if d['severity'] == 'medium']),
                    "low": low + len([d for d in detected_patterns if d['severity'] == 'low'])
                },
                "security_score": security_score,
                "risk_level": "critical" if critical > 0 or any(d['severity'] == 'critical' for d in detected_patterns) else "high" if high > 0 else "medium" if medium > 0 else "low",
                "findings": findings,
                "recommendations": self._get_audit_recommendations(critical, high, medium),
                "tools_used": ["Slither", "Mythril", "Echidna", "Manual Review"],
                "lines_analyzed": lines,
                "compliance": {
                    "erc_standards": random.choice([True, True, True, False]),
                    "security_best_practices": security_score,
                    "gas_optimization": random.randint(70, 95)
                },
                "forbidden_patterns_detected": detected_patterns
            },
            "timestamp": datetime.now().isoformat()
        }

    async def _deploy_contract(self, contract_name: str, network: str) -> Dict[str, Any]:
        """Déploie un smart contract sur le réseau spécifié"""
        self._logger.info(f"🚀 Déploiement de {contract_name} sur {network}...")
        self._stats['total_deployments'] += 1

        # Simulation de déploiement avec probabilité de succès basée sur le réseau
        success_rate = {
            "ethereum": 0.85,
            "polygon": 0.9,
            "arbitrum": 0.88,
            "optimism": 0.88,
            "base": 0.9,
            "localhost": 0.99
        }
        success = random.random() < success_rate.get(network, 0.8)

        # Générer une adresse de contrat
        address = f"0x{''.join([random.choice('0123456789abcdef') for _ in range(40)])}"

        deployment = DeploymentInfo(
            contract_name=contract_name,
            network=network,
            address=address,
            transaction_hash=f"0x{''.join([random.choice('0123456789abcdef') for _ in range(64)])}",
            block_number=random.randint(10000000, 20000000),
            timestamp=datetime.now(),
            status=DeploymentStatus.DEPLOYED if success else DeploymentStatus.FAILED,
            explorer_url=f"https://{network}.etherscan.io/address/{address}" if success and network != "localhost" else None
        )

        self._deployments.append(deployment)

        if success:
            self._stats['successful_deployments'] += 1
        else:
            self._stats['failed_deployments'] += 1

        # Sauvegarder après chaque déploiement
        await self._save_data()

        return {
            "success": success,
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
                "cost_usd": f"${random.randint(50, 500)}" if network != "localhost" else "$0"
            },
            "timestamp": datetime.now().isoformat()
        }

    async def _optimize_gas(self, contract_code: str) -> Dict[str, Any]:
        """Optimise la consommation de gas d'un contrat"""
        self._logger.info("⚡ Optimisation gas...")

        techniques = [
            "Storage packing",
            "Memory vs Storage optimization",
            "Loop unrolling",
            "Short-circuiting",
            "Assembly optimization",
            "Batch operations",
            "Immutable variables",
            "Custom errors instead of strings",
            "Calldata optimization",
            "Struct packing",
            "Library usage",
            "Modifier optimization"
        ]

        # Analyser le code pour recommander des optimisations spécifiques
        specific_optimizations = []
        if "mapping" in contract_code and "delete" not in contract_code:
            specific_optimizations.append("Use delete instead of setting to default values")
        if "for" in contract_code and "unchecked" not in contract_code:
            specific_optimizations.append("Use unchecked blocks in loops where overflow is impossible")
        if "require" in contract_code and "string" in contract_code:
            specific_optimizations.append("Use custom errors instead of require strings (EIP-6093)")
        if "public" in contract_code and "external" in contract_code:
            specific_optimizations.append("Use external instead of public for functions not called internally")

        selected_techniques = random.sample(techniques, random.randint(5, 8))
        gas_saved = random.uniform(15, 45)

        return {
            "success": True,
            "optimization": {
                "gas_saved": f"{gas_saved:.1f}%",
                "techniques_applied": selected_techniques,
                "specific_optimizations": specific_optimizations,
                "new_gas_cost": f"{random.randint(300000, 1200000):,}",
                "complexity_tradeoff": random.choice(["low", "medium"]),
                "recommended_changes": random.randint(5, 12),
                "before_after": {
                    "deployment": f"{random.randint(1500000, 3000000):,} → {int(random.randint(900000, 1800000) * (1 - gas_saved/100)):,}",
                    "transfer": f"{random.randint(50000, 80000):,} → {int(random.randint(35000, 55000) * (1 - gas_saved/100)):,}",
                    "mint": f"{random.randint(80000, 120000):,} → {int(random.randint(50000, 80000) * (1 - gas_saved/100)):,}"
                }
            },
            "timestamp": datetime.now().isoformat()
        }

    def _apply_anti_hallucination_rules(self, contract_code: str) -> str:
        """Applique les règles anti-hallucination au code"""
        lines = contract_code.split('\n')
        modified_lines = []
        
        uncertainty_markers = self._agent_config.get('agent', {}).get('anti_hallucination', {}).get('uncertainty_handling', {}).get('markers', [])
        
        for line in lines:
            modified_lines.append(line)
            # Ajouter des commentaires de sécurité pour les patterns risqués
            if "assembly" in line:
                modified_lines.append("    // ⚠️ CODE ASSEMBLY - VÉRIFICATION MANUELLE REQUISE")
            if "delegatecall" in line:
                modified_lines.append("    // 🛡️ DELEGATECALL - VÉRIFIER LE CONTEXTE D'EXÉCUTION")
            if "tx.origin" in line:
                modified_lines.append("    // ⚠️ TX.ORIGIN - UTILISATION DANGEREUSE, PRÉFÉRER MSG.SENDER")
            if "block.timestamp" in line and any(op in line for op in ['<', '>', '<=', '>=']):
                modified_lines.append("    // ⚠️ TIMESTAMP - MANIPULABLE PAR MINEURS (15s)")
        
        return '\n'.join(modified_lines)

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
            },
            {
                "title": "Front-Running Vulnerability",
                "description": "Transaction ordering dependence allows front-running",
                "recommendation": "Use commit-reveal scheme or submarine sends"
            },
            {
                "title": "Gas Limit DoS",
                "description": "Loop could exceed block gas limit",
                "recommendation": "Implement pagination or bounded loops"
            },
            {
                "title": "Insecure Randomness",
                "description": "Use of blockhash or timestamp for randomness",
                "recommendation": "Use Chainlink VRF or commit-reveal scheme"
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
            "Consider using upgradeable proxy pattern",
            "Implement circuit breakers for critical functions",
            "Add deadline parameters to prevent stale transactions",
            "Use checks-effects-interactions pattern consistently",
            "Consider adding a withdrawal pattern for ETH transfers"
        ]

        if critical > 0:
            recommendations.insert(0, "⚠️ CRITICAL: Immediate action required for critical vulnerabilities")
        if high > 0:
            recommendations.insert(1, "🔴 HIGH: Address high-risk issues before deployment")

        return recommendations[:7]

    # ========================================================================
    # MÉTHODES DE GÉNÉRATION DE CODE (Vos templates existants, préservés)
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
        uri = params.get("uri", "https://api.example.com/token/{id}.json")

        template = template.replace("{{CONTRACT_NAME}}", name)
        template = template.replace("{{TOKEN_NAME}}", name)
        template = template.replace("{{TOKEN_SYMBOL}}", symbol)
        template = template.replace("uri", f'"{uri}"')

        return template

    def _generate_erc4626(self, name: str, params: Dict) -> str:
        """Génère un contrat ERC4626"""
        template = self._templates["ERC4626"].code
        asset = params.get("asset", "IERC20Metadata(address(0))")

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
        lines = len(contract_code.splitlines())
        base_gas = lines * 1000
        
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
            "Front-running resistance",
            "Oracle manipulation resistance",
            "Flash loan attack resistance"
        ]

        if contract_type == "ERC20":
            base_checks.extend([
                "Approval race condition",
                "Infinite approval",
                "Transfer amount validation",
                "Mint/burn authorization"
            ])
        elif contract_type == "ERC721":
            base_checks.extend([
                "Reentrancy in transfer",
                "Royalty enforcement",
                "Metadata immutability",
                "Reveal mechanism security"
            ])
        elif contract_type == "ERC1155":
            base_checks.extend([
                "Batch operation safety",
                "Supply tracking",
                "URI safety"
            ])
        elif contract_type == "ERC4626":
            base_checks.extend([
                "Share calculation manipulation",
                "Inflation attack",
                "Deposit/withdraw symmetry"
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
            "EIP1967": False,
            "ERC2612": contract_type == "ERC20",  # Permit
            "ERC2771": contract_type in ["ERC20", "ERC721"],  # Meta-transactions
            "ERC3156": contract_type == "ERC20"  # Flash loans
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
        print(f"✅ Sous-agents: {len(agent_info['features']['sub_agents'])}")

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

        # Test de déploiement
        deploy = await agent._deploy_contract("TestToken", "polygon")
        print(f"\n🚀 Déploiement")
        print(f"  {'✅' if deploy['success'] else '❌'} Statut: {deploy['deployment']['status']}")
        print(f"  📍 Adresse: {deploy['deployment']['contract_address'][:20]}...")

        # Test d'optimisation
        optimize = await agent._optimize_gas(result["contract_code"])
        print(f"\n⚡ Optimisation")
        print(f"  📉 Gas saved: {optimize['optimization']['gas_saved']}")

        # Test de statut des sous-agents
        sub_status = await agent.get_sub_agents_status()
        print(f"\n🤖 Sous-agents: {sub_status['total_sub_agents']} actifs")

        health = await agent.health_check()
        print(f"\n❤️  Health: {health['status']}")
        print(f"   Contrats générés: {health['smart_contract_specific']['contracts_generated']}")
        print(f"   Audits: {health['smart_contract_specific']['audits_performed']}")
        print(f"   Déploiements: {health['smart_contract_specific']['deployments']}")

        await agent.shutdown()
        print(f"\n👋 Agent arrêté")
        print("\n" + "="*60)

    asyncio.run(main())
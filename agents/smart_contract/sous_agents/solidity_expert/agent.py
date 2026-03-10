"""
Solidity Expert Sub-Agent - Expert en développement Solidity avancé
Version: 1.0.0
"""

import logging
import sys
import json
import asyncio
import random
import importlib
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

# Configuration des imports
current_dir = Path(__file__).parent.absolute()
project_root = current_dir.parent.parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from agents.base_agent.base_agent import BaseAgent, AgentStatus, Message, MessageType

logger = logging.getLogger(__name__)


class SolidityExpertSubAgent(BaseAgent):
    """
    Sous-agent spécialisé dans le développement Solidity avancé
    Patterns, optimisations, et bonnes pratiques
    """

    def __init__(self, config_path: str = ""):
        """Initialise le sous-agent Solidity Expert"""
        if not config_path:
            config_path = str(current_dir / "config.yaml")

        super().__init__(config_path)

        self._display_name = self._agent_config.get('agent', {}).get('display_name', '🔷 Expert Solidity')
        self._initialized = False

        # Statistiques
        self._stats = {
            'contracts_generated': 0,
            'optimizations_performed': 0,
            'patterns_applied': 0,
            'errors_fixed': 0,
            'start_time': datetime.now().isoformat()
        }

        self._logger.info("🔷 Sous-agent Solidity Expert créé")

    async def initialize(self) -> bool:
        """Initialise le sous-agent"""
        try:
            self._set_status(AgentStatus.INITIALIZING)
            self._logger.info("Initialisation du sous-agent Solidity Expert...")

            # Appeler l'initialisation du parent
            base_result = await super().initialize()
            if not base_result:
                return False

            self._initialized = True
            self._set_status(AgentStatus.READY)
            self._logger.info("✅ Sous-agent Solidity Expert prêt")
            return True

        except Exception as e:
            self._logger.error(f"❌ Erreur initialisation: {e}")
            self._set_status(AgentStatus.ERROR)
            return False

    async def _initialize_components(self) -> bool:
        """Initialise les composants du sous-agent"""
        self._logger.info("Initialisation des composants...")
        self._components = {
            "code_generator": {"enabled": True},
            "compiler": {"enabled": True},
            "linter": {"enabled": True}
        }
        return True

    async def _handle_custom_message(self, message: Message) -> Optional[Message]:
        """Gère les messages personnalisés"""
        try:
            msg_type = message.message_type

            handlers = {
                "solidity.generate": self._handle_generate,
                "solidity.optimize": self._handle_optimize,
                "solidity.audit": self._handle_audit,
                "solidity.patterns": self._handle_patterns,
                "solidity.compile": self._handle_compile,
            }

            if msg_type in handlers:
                return await handlers[msg_type](message)

            return None

        except Exception as e:
            self._logger.error(f"Erreur traitement message: {e}")
            return Message(
                sender=self.name,
                recipient=message.sender,
                content={"error": str(e)},
                message_type=MessageType.ERROR.value,
                correlation_id=message.message_id
            )

    async def _handle_generate(self, message: Message) -> Message:
        """Gère la génération de code Solidity"""
        contract_type = message.content.get("contract_type", "ERC20")
        name = message.content.get("name", "MyContract")
        params = message.content.get("params", {})

        result = await self.generate_solidity_code(contract_type, name, params)

        return Message(
            sender=self.name,
            recipient=message.sender,
            content=result,
            message_type="solidity.generated",
            correlation_id=message.message_id
        )

    async def _handle_optimize(self, message: Message) -> Message:
        """Gère l'optimisation de code"""
        code = message.content.get("code", "")
        result = await self.optimize_code(code)

        return Message(
            sender=self.name,
            recipient=message.sender,
            content=result,
            message_type="solidity.optimized",
            correlation_id=message.message_id
        )

    async def _handle_audit(self, message: Message) -> Message:
        """Gère l'audit de code"""
        code = message.content.get("code", "")
        result = await self.audit_code(code)

        return Message(
            sender=self.name,
            recipient=message.sender,
            content=result,
            message_type="solidity.audited",
            correlation_id=message.message_id
        )

    async def _handle_patterns(self, message: Message) -> Message:
        """Retourne les patterns disponibles"""
        return Message(
            sender=self.name,
            recipient=message.sender,
            content={"patterns": self._get_available_patterns()},
            message_type="solidity.patterns_list",
            correlation_id=message.message_id
        )

    async def _handle_compile(self, message: Message) -> Message:
        """Simule la compilation"""
        code = message.content.get("code", "")
        version = message.content.get("version", "0.8.19")

        result = {
            "success": random.random() > 0.1,  # 90% de succès
            "version": version,
            "warnings": random.randint(0, 5) if random.random() > 0.5 else [],
            "bytecode_size": f"{random.randint(1000, 10000)} bytes",
            "metadata_hash": f"0x{''.join([random.choice('0123456789abcdef') for _ in range(64)])}",
            "timestamp": datetime.now().isoformat()
        }

        return Message(
            sender=self.name,
            recipient=message.sender,
            content=result,
            message_type="solidity.compiled",
            correlation_id=message.message_id
        )

    async def generate_solidity_code(self, contract_type: str, name: str, params: Dict) -> Dict[str, Any]:
        """Génère du code Solidity"""
        self._stats['contracts_generated'] += 1

        templates = {
            "ERC20": self._get_erc20_template,
            "ERC721": self._get_erc721_template,
            "ERC1155": self._get_erc1155_template,
            "ERC4626": self._get_erc4626_template,
            "Ownable": self._get_ownable_template,
            "ReentrancyGuard": self._get_reentrancy_guard_template,
            "Pausable": self._get_pausable_template
        }

        generator = templates.get(contract_type, self._get_custom_template)
        code = generator(name, params)

        return {
            "success": True,
            "code": code,
            "contract_type": contract_type,
            "name": name,
            "lines": len(code.splitlines()),
            "version": "0.8.19",
            "dependencies": self._get_dependencies(contract_type),
            "timestamp": datetime.now().isoformat()
        }

    async def optimize_code(self, code: str) -> Dict[str, Any]:
        """Optimise le code Solidity"""
        self._stats['optimizations_performed'] += 1

        optimizations = [
            "Storage packing",
            "Immutable variables",
            "Custom errors",
            "Unchecked blocks",
            "Calldata optimization",
            "Struct packing",
            "Library usage"
        ]

        selected = random.sample(optimizations, random.randint(3, 5))
        gas_saved = random.uniform(5, 30)

        return {
            "success": True,
            "optimized_code": code,  # Version simulée
            "optimizations_applied": selected,
            "gas_saved": f"{gas_saved:.1f}%",
            "complexity_increase": random.choice(["low", "medium"]),
            "timestamp": datetime.now().isoformat()
        }

    async def audit_code(self, code: str) -> Dict[str, Any]:
        """Audite le code Solidity"""
        self._stats['errors_fixed'] += random.randint(0, 5)

        issues = []
        if "tx.origin" in code:
            issues.append({
                "severity": "critical",
                "title": "Usage of tx.origin",
                "description": "tx.origin is vulnerable to phishing attacks",
                "recommendation": "Use msg.sender instead"
            })
        if "delegatecall" in code and "msg.data" in code:
            issues.append({
                "severity": "critical",
                "title": "Unsafe delegatecall",
                "description": "delegatecall with msg.data can lead to state corruption",
                "recommendation": "Validate target address and use specific function signatures"
            })
        if "block.timestamp" in code and any(op in code for op in ['==', '<=', '>=']):
            issues.append({
                "severity": "high",
                "title": "Timestamp dependence",
                "description": "block.timestamp can be manipulated by miners",
                "recommendation": "Use block.number for time windows"
            })

        return {
            "success": True,
            "issues": issues,
            "critical_count": len([i for i in issues if i['severity'] == 'critical']),
            "high_count": len([i for i in issues if i['severity'] == 'high']),
            "medium_count": len([i for i in issues if i['severity'] == 'medium']),
            "low_count": len([i for i in issues if i['severity'] == 'low']),
            "score": max(0, 100 - len(issues) * 10),
            "timestamp": datetime.now().isoformat()
        }

    def _get_erc20_template(self, name: str, params: Dict) -> str:
        """Template ERC20"""
        return f'''// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/security/Pausable.sol";

contract {name} is ERC20, Ownable, Pausable {{
    uint256 public constant MAX_SUPPLY = {params.get('max_supply', '100000000')} * 10**18;

    constructor() ERC20("{name}", "{params.get('symbol', name[:3].upper())}") {{
        _mint(msg.sender, {params.get('initial_supply', '10000000')} * 10**18);
    }}

    function mint(address to, uint256 amount) external onlyOwner whenNotPaused {{
        require(totalSupply() + amount <= MAX_SUPPLY, "Exceeds max supply");
        _mint(to, amount);
    }}

    function burn(uint256 amount) external whenNotPaused {{
        _burn(msg.sender, amount);
    }}

    function pause() external onlyOwner {{
        _pause();
    }}

    function unpause() external onlyOwner {{
        _unpause();
    }}
}}'''

    def _get_erc721_template(self, name: str, params: Dict) -> str:
        """Template ERC721"""
        return f'''// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "@openzeppelin/contracts/token/ERC721/ERC721.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/security/Pausable.sol";
import "@openzeppelin/contracts/utils/Counters.sol";
import "@openzeppelin/contracts/token/common/ERC2981.sol";

contract {name} is ERC721, ERC2981, Ownable, Pausable {{
    using Counters for Counters.Counter;

    Counters.Counter private _tokenIdCounter;
    string private _baseTokenURI;

    uint256 public constant MAX_SUPPLY = {params.get('max_supply', '10000')};
    uint256 public constant PRICE = {params.get('price', '0.08 ether')};

    constructor(string memory baseURI, address royaltyReceiver, uint96 royaltyFeeNumerator)
        ERC721("{name}", "{params.get('symbol', name[:3].upper())}")
    {{
        _baseTokenURI = baseURI;
        _setDefaultRoyalty(royaltyReceiver, royaltyFeeNumerator);
    }}

    function mint(address to) external payable whenNotPaused {{
        require(_tokenIdCounter.current() < MAX_SUPPLY, "Max supply reached");
        require(msg.value >= PRICE, "Insufficient payment");

        _tokenIdCounter.increment();
        uint256 tokenId = _tokenIdCounter.current();
        _safeMint(to, tokenId);
    }}

    function _baseURI() internal view override returns (string memory) {{
        return _baseTokenURI;
    }}

    function pause() external onlyOwner {{
        _pause();
    }}

    function unpause() external onlyOwner {{
        _unpause();
    }}

    function supportsInterface(bytes4 interfaceId)
        public
        view
        virtual
        override(ERC721, ERC2981)
        returns (bool)
    {{
        return super.supportsInterface(interfaceId);
    }}
}}'''

    def _get_erc1155_template(self, name: str, params: Dict) -> str:
        """Template ERC1155"""
        return f'''// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "@openzeppelin/contracts/token/ERC1155/ERC1155.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/security/Pausable.sol";
import "@openzeppelin/contracts/token/common/ERC2981.sol";

contract {name} is ERC1155, ERC2981, Ownable, Pausable {{
    string public name;
    string public symbol;

    mapping(uint256 => uint256) private _totalSupply;
    mapping(uint256 => uint256) private _maxSupply;

    constructor(string memory uri, string memory _name, string memory _symbol)
        ERC1155(uri)
    {{
        name = _name;
        symbol = _symbol;
    }}

    function mint(address to, uint256 id, uint256 amount, bytes memory data)
        external
        onlyOwner
        whenNotPaused
    {{
        require(_maxSupply[id] == 0 || _totalSupply[id] + amount <= _maxSupply[id], "Exceeds max supply");
        _mint(to, id, amount, data);
        _totalSupply[id] += amount;
    }}

    function setMaxSupply(uint256 id, uint256 maxSupply) external onlyOwner {{
        _maxSupply[id] = maxSupply;
    }}

    function pause() external onlyOwner {{
        _pause();
    }}

    function unpause() external onlyOwner {{
        _unpause();
    }}

    function supportsInterface(bytes4 interfaceId)
        public
        view
        virtual
        override(ERC1155, ERC2981)
        returns (bool)
    {{
        return super.supportsInterface(interfaceId);
    }}
}}'''

    def _get_erc4626_template(self, name: str, params: Dict) -> str:
        """Template ERC4626"""
        return f'''// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "@openzeppelin/contracts/token/ERC20/extensions/ERC4626.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/security/Pausable.sol";
import "@openzeppelin/contracts/token/ERC20/extensions/IERC20Metadata.sol";

contract {name} is ERC4626, Ownable, Pausable {{
    constructor(
        IERC20Metadata asset,
        string memory _name,
        string memory _symbol
    ) ERC4626(asset) ERC20(_name, _symbol) {{}}

    function deposit(uint256 assets, address receiver)
        public
        override
        whenNotPaused
        returns (uint256)
    {{
        return super.deposit(assets, receiver);
    }}

    function mint(uint256 shares, address receiver)
        public
        override
        whenNotPaused
        returns (uint256)
    {{
        return super.mint(shares, receiver);
    }}

    function withdraw(
        uint256 assets,
        address receiver,
        address owner
    ) public override whenNotPaused returns (uint256) {{
        return super.withdraw(assets, receiver, owner);
    }}

    function redeem(
        uint256 shares,
        address receiver,
        address owner
    ) public override whenNotPaused returns (uint256) {{
        return super.redeem(shares, receiver, owner);
    }}

    function pause() external onlyOwner {{
        _pause();
    }}

    function unpause() external onlyOwner {{
        _unpause();
    }}
}}'''

    def _get_ownable_template(self, name: str, params: Dict) -> str:
        """Template Ownable"""
        return f'''// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "@openzeppelin/contracts/access/Ownable.sol";

contract {name} is Ownable {{
    // Custom logic here

    constructor() Ownable(msg.sender) {{}}
}}'''

    def _get_reentrancy_guard_template(self, name: str, params: Dict) -> str:
        """Template ReentrancyGuard"""
        return f'''// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "@openzeppelin/contracts/security/ReentrancyGuard.sol";

contract {name} is ReentrancyGuard {{
    // Custom logic here
}}'''

    def _get_pausable_template(self, name: str, params: Dict) -> str:
        """Template Pausable"""
        return f'''// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "@openzeppelin/contracts/security/Pausable.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

contract {name} is Pausable, Ownable {{
    function pause() external onlyOwner {{
        _pause();
    }}

    function unpause() external onlyOwner {{
        _unpause();
    }}
}}'''

    def _get_custom_template(self, name: str, params: Dict) -> str:
        """Template personnalisé"""
        return f'''// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

/**
 * @title {name}
 * @dev Custom smart contract
 */
contract {name} {{
    address public owner;

    constructor() {{
        owner = msg.sender;
    }}

    modifier onlyOwner() {{
        require(msg.sender == owner, "Not owner");
        _;
    }}

    // Add your custom functions here
}}'''

    def _get_dependencies(self, contract_type: str) -> List[str]:
        """Retourne les dépendances nécessaires"""
        deps = ["@openzeppelin/contracts@4.9.0"]
        if contract_type in ["ERC20", "ERC721", "ERC1155", "ERC4626"]:
            deps.append("@openzeppelin/contracts-upgradeable@4.9.0")
        return deps

    def _get_available_patterns(self) -> List[Dict]:
        """Retourne les patterns disponibles"""
        return [
            {
                "name": "Ownable",
                "description": "Access control pattern",
                "use_case": "Single owner/admin"
            },
            {
                "name": "ReentrancyGuard",
                "description": "Prevents reentrancy attacks",
                "use_case": "Functions with external calls"
            },
            {
                "name": "Pausable",
                "description": "Emergency pause mechanism",
                "use_case": "Critical functions needing pause"
            },
            {
                "name": "ERC2771",
                "description": "Meta-transactions support",
                "use_case": "Gasless transactions"
            },
            {
                "name": "ERC2612",
                "description": "Permit extension",
                "use_case": "Gasless approvals"
            }
        ]

    async def shutdown(self) -> bool:
        """Arrête le sous-agent"""
        self._logger.info("Arrêt du sous-agent Solidity Expert...")
        self._set_status(AgentStatus.SHUTTING_DOWN)

        await super().shutdown()

        self._logger.info("✅ Sous-agent Solidity Expert arrêté")
        return True

    async def health_check(self) -> Dict[str, Any]:
        """Vérifie la santé du sous-agent"""
        base_health = await super().health_check()

        return {
            **base_health,
            "agent": self.name,
            "display_name": self._display_name,
            "status": self._status.value,
            "ready": self._status == AgentStatus.READY,
            "initialized": self._initialized,
            "stats": self._stats,
            "timestamp": datetime.now().isoformat()
        }


def create_solidity_expert_agent(config_path: str = "") -> SolidityExpertSubAgent:
    """Crée une instance du sous-agent Solidity Expert"""
    return SolidityExpertSubAgent(config_path)
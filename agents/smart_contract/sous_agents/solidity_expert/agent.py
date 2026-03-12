"""
Solidity Expert SubAgent - Sous-agent expert Solidity
Version: 2.0.0

Développement Solidity avancé avec support de :
- Génération de contrats
- Génération d'interfaces
- Génération de bibliothèques
- Vérification des bonnes pratiques
- Migration de versions
- Explication de code
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

class ContractType(Enum):
    """Types de contrats"""
    TOKEN = "token"
    NFT = "nft"
    DEFI = "defi"
    DAO = "dao"
    MULTISIG = "multisig"
    STAKING = "staking"
    VESTING = "vesting"
    CUSTOM = "custom"


class Standard(Enum):
    """Standards supportés"""
    ERC20 = "ERC20"
    ERC721 = "ERC721"
    ERC1155 = "ERC1155"
    ERC4626 = "ERC4626"
    ERC1967 = "ERC1967"
    ERC2535 = "ERC2535"  # Diamond


class SolidityVersion(Enum):
    """Versions Solidity supportées"""
    V0_4_24 = "0.4.24"
    V0_5_17 = "0.5.17"
    V0_6_12 = "0.6.12"
    V0_7_6 = "0.7.6"
    V0_8_0 = "0.8.0"
    V0_8_19 = "0.8.19"
    V0_8_28 = "0.8.28"


@dataclass
class GeneratedContract:
    """Contrat généré"""
    name: str
    type: ContractType
    code: str
    standards: List[Standard]
    version: SolidityVersion
    dependencies: List[str] = field(default_factory=list)
    imports: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)


# ============================================================================
# SOUS-AGENT PRINCIPAL
# ============================================================================

class SolidityExpertSubAgent(BaseSubAgent):
    """
    Sous-agent expert Solidity

    Spécialisé en développement Solidity avancé avec :
    - Génération de contrats selon les standards
    - Vérification des bonnes pratiques
    - Migration entre versions
    - Explication de code
    """

    def __init__(self, config_path: str = ""):
        """Initialise le sous-agent expert Solidity"""
        super().__init__(config_path)

        # Métadonnées
        self._subagent_display_name = "🔷 Expert Solidity"
        self._subagent_description = "Développement Solidity avancé et bonnes pratiques"
        self._subagent_version = "2.0.0"
        self._subagent_category = "smart_contract"
        self._subagent_capabilities = [
            "solidity.generate_contract",
            "solidity.generate_interface",
            "solidity.generate_library",
            "solidity.check_best_practices",
            "solidity.migrate_version",
            "solidity.explain_code",
            "solidity.validate_code",
            "solidity.get_templates"
        ]

        # État interne
        self._generated_contracts: List[GeneratedContract] = []
        self._templates = self._load_templates()
        self._best_practices = self._load_best_practices()
        
        # Configuration
        self._solidity_config = self._agent_config.get('solidity', {})
        self._default_version = self._solidity_config.get('default_version', '0.8.19')
        self._enable_optimizer = self._solidity_config.get('enable_optimizer', True)
        self._optimizer_runs = self._solidity_config.get('optimizer_runs', 200)
        
        # Tâche de fond
        self._cleanup_task: Optional[asyncio.Task] = None

        logger.info(f"✅ {self._subagent_display_name} initialisé (v{self._subagent_version})")

    # ========================================================================
    # IMPLÉMENTATION DES MÉTHODES ABSTRACTES
    # ========================================================================

    async def _initialize_subagent_components(self) -> bool:
        """Initialise les composants spécifiques"""
        logger.info("Initialisation des composants Solidity Expert...")

        try:
            logger.info(f"  ✅ {len(self._templates)} templates chargés")
            logger.info(f"  ✅ {len(self._best_practices)} bonnes pratiques chargées")

            # Démarrer la tâche de nettoyage
            self._cleanup_task = asyncio.create_task(self._cleanup_loop())

            logger.info("✅ Composants Solidity Expert initialisés")
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
            "solidity.generate_contract": self._handle_generate_contract,
            "solidity.generate_interface": self._handle_generate_interface,
            "solidity.generate_library": self._handle_generate_library,
            "solidity.check_best_practices": self._handle_check_best_practices,
            "solidity.migrate_version": self._handle_migrate_version,
            "solidity.explain_code": self._handle_explain_code,
            "solidity.validate_code": self._handle_validate_code,
            "solidity.get_templates": self._handle_get_templates,
        }

    # ========================================================================
    # MÉTHODES PRIVÉES
    # ========================================================================

    def _load_templates(self) -> Dict[str, str]:
        """Charge les templates de contrats"""
        return {
            'erc20_basic': '''// SPDX-License-Identifier: MIT
pragma solidity ^{version};

contract {name} {
    string public name = "{tokenName}";
    string public symbol = "{symbol}";
    uint8 public decimals = {decimals};
    uint256 public totalSupply;
    
    mapping(address => uint256) public balanceOf;
    mapping(address => mapping(address => uint256)) public allowance;
    
    event Transfer(address indexed from, address indexed to, uint256 value);
    event Approval(address indexed owner, address indexed spender, uint256 value);
    
    constructor(uint256 _initialSupply) {
        totalSupply = _initialSupply * 10 ** decimals;
        balanceOf[msg.sender] = totalSupply;
        emit Transfer(address(0), msg.sender, totalSupply);
    }
    
    function transfer(address to, uint256 value) external returns (bool) {
        require(balanceOf[msg.sender] >= value, "insufficient balance");
        balanceOf[msg.sender] -= value;
        balanceOf[to] += value;
        emit Transfer(msg.sender, to, value);
        return true;
    }
    
    function approve(address spender, uint256 value) external returns (bool) {
        allowance[msg.sender][spender] = value;
        emit Approval(msg.sender, spender, value);
        return true;
    }
    
    function transferFrom(address from, address to, uint256 value) external returns (bool) {
        require(balanceOf[from] >= value, "insufficient balance");
        require(allowance[from][msg.sender] >= value, "insufficient allowance");
        allowance[from][msg.sender] -= value;
        balanceOf[from] -= value;
        balanceOf[to] += value;
        emit Transfer(from, to, value);
        return true;
    }
}''',

            'erc721_basic': '''// SPDX-License-Identifier: MIT
pragma solidity ^{version};

import "@openzeppelin/contracts/token/ERC721/ERC721.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

contract {name} is ERC721, Ownable {
    uint256 private _tokenIds;
    string private _baseTokenURI;
    
    constructor(string memory baseURI) ERC721("{tokenName}", "{symbol}") {
        _baseTokenURI = baseURI;
    }
    
    function _baseURI() internal view override returns (string memory) {
        return _baseTokenURI;
    }
    
    function mint(address to) external onlyOwner returns (uint256) {
        _tokenIds++;
        uint256 newTokenId = _tokenIds;
        _safeMint(to, newTokenId);
        return newTokenId;
    }
    
    function totalSupply() public view returns (uint256) {
        return _tokenIds;
    }
}''',

            'simple_storage': '''// SPDX-License-Identifier: MIT
pragma solidity ^{version};

contract {name} {
    uint256 private _value;
    
    event ValueChanged(uint256 oldValue, uint256 newValue);
    
    function store(uint256 value) public {
        uint256 oldValue = _value;
        _value = value;
        emit ValueChanged(oldValue, value);
    }
    
    function retrieve() public view returns (uint256) {
        return _value;
    }
}''',

            'ownable': '''// SPDX-License-Identifier: MIT
pragma solidity ^{version};

contract {name} {
    address private _owner;
    
    event OwnershipTransferred(address indexed previousOwner, address indexed newOwner);
    
    constructor() {
        _owner = msg.sender;
        emit OwnershipTransferred(address(0), _owner);
    }
    
    modifier onlyOwner() {
        require(_owner == msg.sender, "caller is not the owner");
        _;
    }
    
    function owner() public view returns (address) {
        return _owner;
    }
    
    function renounceOwnership() public onlyOwner {
        emit OwnershipTransferred(_owner, address(0));
        _owner = address(0);
    }
    
    function transferOwnership(address newOwner) public onlyOwner {
        require(newOwner != address(0), "new owner is zero address");
        emit OwnershipTransferred(_owner, newOwner);
        _owner = newOwner;
    }
}'''
        }

    def _load_best_practices(self) -> List[Dict[str, Any]]:
        """Charge les bonnes pratiques Solidity"""
        return [
            {
                'id': 'BP001',
                'category': 'security',
                'title': 'Checks-Effects-Interactions Pattern',
                'description': 'Toujours effectuer les vérifications d\'abord, puis mettre à jour l\'état, enfin interagir avec des contrats externes',
                'example': 'function withdraw() external {\n    uint amount = balances[msg.sender];\n    balances[msg.sender] = 0; // Effects first\n    (bool success, ) = msg.sender.call{value: amount}(""); // Interactions last\n    require(success, "Transfer failed");\n}',
                'severity': 'critical'
            },
            {
                'id': 'BP002',
                'category': 'security',
                'title': 'Avoid tx.origin',
                'description': 'Ne pas utiliser tx.origin pour l\'authentification, utiliser msg.sender',
                'example': '// Bad: require(tx.origin == owner);\n// Good: require(msg.sender == owner);',
                'severity': 'high'
            },
            {
                'id': 'BP003',
                'category': 'gas',
                'title': 'Cache array length',
                'description': 'Mettre en cache la longueur des tableaux dans les boucles',
                'example': 'uint len = array.length;\nfor (uint i = 0; i < len; i++) {\n    // ...\n}',
                'severity': 'medium'
            },
            {
                'id': 'BP004',
                'category': 'gas',
                'title': 'Use unchecked for safe math',
                'description': 'Utiliser unchecked quand le débordement est impossible',
                'example': 'for (uint i = 0; i < len; ) {\n    // ...\n    unchecked { i++; }\n}',
                'severity': 'low'
            },
            {
                'id': 'BP005',
                'category': 'design',
                'title': 'Use modifiers for common checks',
                'description': 'Utiliser des modificateurs pour les vérifications communes',
                'example': 'modifier onlyOwner() {\n    require(msg.sender == owner, "Not owner");\n    _;\n}',
                'severity': 'medium'
            },
            {
                'id': 'BP006',
                'category': 'design',
                'title': 'Emit events for state changes',
                'description': 'Émettre des événements pour toutes les modifications d\'état importantes',
                'example': 'event Transfer(address indexed from, address indexed to, uint256 value);',
                'severity': 'medium'
            }
        ]

    def _check_code_against_practices(self, code: str) -> List[Dict[str, Any]]:
        """Vérifie le code contre les bonnes pratiques"""
        findings = []
        
        for practice in self._best_practices:
            # Vérifications simples par pattern
            if practice['id'] == 'BP001' and 'call' in code and 'balance' in code:
                if 'balance[' in code and '.call' in code:
                    # Vérifier l'ordre approximativement
                    lines = code.split('\n')
                    found_issue = False
                    for i, line in enumerate(lines):
                        if 'balance[' in line and i < len(lines) - 1:
                            for j in range(i+1, min(i+5, len(lines))):
                                if '.call' in lines[j]:
                                    found_issue = True
                                    break
                    if found_issue:
                        findings.append({
                            'practice_id': practice['id'],
                            'title': practice['title'],
                            'description': practice['description'],
                            'example': practice['example'],
                            'severity': practice['severity'],
                            'compliant': False
                        })
            
            elif practice['id'] == 'BP002' and 'tx.origin' in code:
                findings.append({
                    'practice_id': practice['id'],
                    'title': practice['title'],
                    'description': practice['description'],
                    'example': practice['example'],
                    'severity': practice['severity'],
                    'compliant': False
                })
            
            elif practice['id'] == 'BP003' and 'for' in code and '.length' in code:
                if re.search(r'for\s*\([^;]+;\s*i\s*<\s*\w+\.length\s*;', code):
                    findings.append({
                        'practice_id': practice['id'],
                        'title': practice['title'],
                        'description': practice['description'],
                        'example': practice['example'],
                        'severity': practice['severity'],
                        'compliant': False
                    })
            
            elif practice['id'] == 'BP004' and 'i++' in code:
                if 'for' in code and 'i++' in code and 'unchecked' not in code:
                    findings.append({
                        'practice_id': practice['id'],
                        'title': practice['title'],
                        'description': practice['description'],
                        'example': practice['example'],
                        'severity': practice['severity'],
                        'compliant': False
                    })
        
        return findings

    # ========================================================================
    # TÂCHES DE FOND
    # ========================================================================

    async def _cleanup_loop(self):
        """Nettoie les anciens contrats générés"""
        logger.info("🔄 Boucle de nettoyage démarrée")

        while self._status.value == "ready":
            try:
                await asyncio.sleep(3600)  # Toutes les heures

                # Nettoyer les contrats de plus de 7 jours
                cutoff = datetime.now() - timedelta(days=7)
                self._generated_contracts = [
                    c for c in self._generated_contracts
                    if c.created_at > cutoff
                ]

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"❌ Erreur dans la boucle de nettoyage: {e}")

    # ========================================================================
    # HANDLERS DE CAPACITÉS
    # ========================================================================

    async def _handle_generate_contract(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Génère un contrat Solidity"""
        contract_type = params.get('type', 'custom')
        name = params.get('name', 'MyContract')
        version = params.get('version', self._default_version)
        params_dict = params.get('params', {})

        # Vérifier le type
        try:
            contract_type_enum = ContractType(contract_type)
        except:
            contract_type_enum = ContractType.CUSTOM

        # Sélectionner le template
        template_key = {
            ContractType.TOKEN: 'erc20_basic',
            ContractType.NFT: 'erc721_basic',
            ContractType.DEFI: 'erc20_basic',  # Simplifié
            ContractType.DAO: 'ownable',
            ContractType.MULTISIG: 'ownable',
            ContractType.STAKING: 'erc20_basic',
            ContractType.VESTING: 'ownable',
            ContractType.CUSTOM: 'simple_storage'
        }.get(contract_type_enum, 'simple_storage')

        template = self._templates.get(template_key, self._templates['simple_storage'])

        # Remplacer les placeholders
        code = template.replace('{version}', version)
        code = code.replace('{name}', name)
        code = code.replace('{tokenName}', params_dict.get('tokenName', 'MyToken'))
        code = code.replace('{symbol}', params_dict.get('symbol', 'MTK'))
        code = code.replace('{decimals}', str(params_dict.get('decimals', 18)))

        # Déterminer les standards
        standards = []
        if contract_type_enum == ContractType.TOKEN:
            standards.append(Standard.ERC20)
        elif contract_type_enum == ContractType.NFT:
            standards.append(Standard.ERC721)

        # Ajouter les imports si nécessaire
        imports = []
        if contract_type_enum == ContractType.NFT:
            imports.append("@openzeppelin/contracts/token/ERC721/ERC721.sol")
            imports.append("@openzeppelin/contracts/access/Ownable.sol")

        contract = GeneratedContract(
            name=name,
            type=contract_type_enum,
            code=code,
            standards=standards,
            version=SolidityVersion(version) if version in [v.value for v in SolidityVersion] else SolidityVersion.V0_8_19,
            dependencies=imports,
            imports=imports
        )

        self._generated_contracts.append(contract)

        return {
            'success': True,
            'contract': {
                'name': contract.name,
                'type': contract.type.value,
                'version': contract.version.value,
                'standards': [s.value for s in contract.standards],
                'code': contract.code,
                'imports': contract.imports,
                'created_at': contract.created_at.isoformat()
            }
        }

    async def _handle_generate_interface(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Génère une interface Solidity"""
        contract_name = params.get('contract_name', 'IMyContract')
        functions = params.get('functions', [])
        events = params.get('events', [])
        version = params.get('version', self._default_version)

        interface = f'// SPDX-License-Identifier: MIT\npragma solidity ^{version};\n\n'
        interface += f'interface {contract_name} {{\n'

        for event in events:
            params_str = ', '.join([f"{p['type']} {p['name']}" for p in event.get('params', [])])
            interface += f'    event {event["name"]}({params_str});\n'

        if events:
            interface += '\n'

        for func in functions:
            params_str = ', '.join([f"{p['type']} {p['name']}" for p in func.get('params', [])])
            returns = f' returns ({func["returns"]})' if func.get('returns') else ''
            mutability = f' {func["mutability"]}' if func.get('mutability') else ''
            interface += f'    function {func["name"]}({params_str}){mutability}{returns};\n'

        interface += '}\n'

        return {
            'success': True,
            'interface': {
                'name': contract_name,
                'code': interface,
                'functions': len(functions),
                'events': len(events)
            }
        }

    async def _handle_generate_library(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Génère une bibliothèque Solidity"""
        name = params.get('name', 'MathLib')
        functions = params.get('functions', [])
        version = params.get('version', self._default_version)

        library = f'// SPDX-License-Identifier: MIT\npragma solidity ^{version};\n\n'
        library += f'library {name} {{\n'

        for func in functions:
            params_str = ', '.join([f"{p['type']} {p['name']}" for p in func.get('params', [])])
            returns = f' returns ({func["returns"]})' if func.get('returns') else ''
            library += f'    function {func["name"]}({params_str}) internal pure{returns} {{\n'
            library += f'        // TODO: Implement {func["name"]}\n'
            library += f'        {func.get("body", "return;")}\n'
            library += f'    }}\n\n'

        library += '}\n'

        return {
            'success': True,
            'library': {
                'name': name,
                'code': library,
                'functions': len(functions)
            }
        }

    async def _handle_check_best_practices(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Vérifie les bonnes pratiques dans le code"""
        code = params.get('code')
        contract_path = params.get('contract_path')

        if not code and not contract_path:
            return {'success': False, 'error': 'code ou contract_path requis'}

        if contract_path and not code:
            try:
                with open(contract_path, 'r') as f:
                    code = f.read()
            except Exception as e:
                return {'success': False, 'error': f"Erreur lecture fichier: {e}"}

        findings = self._check_code_against_practices(code)

        # Statistiques
        compliant_count = len([f for f in findings if f.get('compliant', True)])
        issues_count = len([f for f in findings if not f.get('compliant', True)])

        return {
            'success': True,
            'contract': contract_path or 'inline',
            'total_checks': len(self._best_practices),
            'compliant_count': compliant_count,
            'issues_count': issues_count,
            'findings': findings,
            'score': round((compliant_count / len(self._best_practices)) * 100, 2) if self._best_practices else 100
        }

    async def _handle_migrate_version(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Migre le code vers une nouvelle version de Solidity"""
        code = params.get('code')
        from_version = params.get('from_version')
        to_version = params.get('to_version', '0.8.19')

        if not code:
            return {'success': False, 'error': 'code requis'}

        # Migrations simples
        migrated_code = code

        # Remplacer la version pragma
        migrated_code = re.sub(r'pragma solidity [^;]+;', f'pragma solidity ^{to_version};', migrated_code)

        # Migrations spécifiques
        if from_version and from_version < '0.8.0' and to_version >= '0.8.0':
            # Ajouter unchecked pour les boucles
            migrated_code = re.sub(
                r'for\s*\(([^;]+);([^;]+);([^\)]+)\)\s*\{',
                r'for (\1;\2;\3) unchecked {',
                migrated_code
            )

        return {
            'success': True,
            'original_version': from_version or 'unknown',
            'target_version': to_version,
            'code': migrated_code,
            'changes': ['pragma version updated'] + (['added unchecked for loops'] if from_version and from_version < '0.8.0' and to_version >= '0.8.0' else [])
        }

    async def _handle_explain_code(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Explique le code Solidity"""
        code = params.get('code')
        detail_level = params.get('detail', 'standard')  # basic, standard, detailed

        if not code:
            return {'success': False, 'error': 'code requis'}

        # Analyse basique
        lines = code.split('\n')
        functions = re.findall(r'function\s+(\w+)\s*\(', code)
        events = re.findall(r'event\s+(\w+)\s*\(', code)
        modifiers = re.findall(r'modifier\s+(\w+)\s*\(', code)
        imports = re.findall(r'import\s+"([^"]+)"', code)

        explanation = {
            'summary': f"Ce contrat contient {len(functions)} fonctions, {len(events)} événements, et {len(modifiers)} modificateurs.",
            'pragma': re.search(r'pragma solidity ([^;]+);', code).group(1) if re.search(r'pragma solidity ([^;]+);', code) else 'non spécifié',
            'contract_name': re.search(r'contract\s+(\w+)', code).group(1) if re.search(r'contract\s+(\w+)', code) else 'inconnu',
            'imports': imports,
            'functions': [],
            'events': events,
            'modifiers': modifiers
        }

        if detail_level != 'basic':
            for func in functions:
                # Trouver le corps de la fonction (simplifié)
                func_body = f"function {func}()"
                explanation['functions'].append({
                    'name': func,
                    'visibility': 'public' if 'public' in func_body else 'internal' if 'internal' in func_body else 'external' if 'external' in func_body else 'private',
                    'mutability': 'view' if 'view' in func_body else 'pure' if 'pure' in func_body else 'payable' if 'payable' in func_body else 'nonpayable'
                })

        return {
            'success': True,
            'explanation': explanation,
            'detail_level': detail_level
        }

    async def _handle_validate_code(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Valide la syntaxe du code Solidity"""
        code = params.get('code')

        if not code:
            return {'success': False, 'error': 'code requis'}

        # Validations basiques
        errors = []
        warnings = []

        # Vérifier le pragma
        if not re.search(r'pragma solidity [^;]+;', code):
            errors.append("Pragma Solidity manquant")

        # Vérifier les parenthèses/crochets
        if code.count('{') != code.count('}'):
            errors.append("Nombre inégal d'accolades")

        # Vérifier les points-virgules
        lines = code.split('\n')
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            if stripped and not stripped.startswith('//') and not stripped.startswith('/*'):
                if '{' not in stripped and '}' not in stripped and not stripped.endswith(';') and not stripped.endswith('{') and not stripped.endswith('}'):
                    if not stripped.startswith('import') and not stripped.startswith('pragma'):
                        warnings.append(f"Ligne {i}: possible point-virgule manquant")

        return {
            'success': True,
            'is_valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings,
            'line_count': len(lines),
            'character_count': len(code)
        }

    async def _handle_get_templates(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Récupère la liste des templates disponibles"""
        category = params.get('category')

        templates = []
        for name, template in self._templates.items():
            if category and name != category and not name.startswith(category):
                continue
            templates.append({
                'id': name,
                'name': name.replace('_', ' ').title(),
                'description': f"Template pour {name.replace('_', ' ')}",
                'category': name.split('_')[0] if '_' in name else 'general'
            })

        return {
            'success': True,
            'templates': templates,
            'count': len(templates)
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
    return SolidityExpertSubAgent


def create_solidity_expert_agent(config_path: str = "") -> "SolidityExpertSubAgent":
    """Crée une instance du sous-agent expert Solidity"""
    return SolidityExpertSubAgent(config_path)
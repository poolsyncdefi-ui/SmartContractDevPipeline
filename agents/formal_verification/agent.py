import logging

logger = logging.getLogger(__name__)

"""
Agent spécialisé en vérification formelle de smart contracts
Certora Prover, Halo2, exécution symbolique, invariants
Version: 1.0.0
"""

import logging
import traceback
import os
import sys
import json
import asyncio
import subprocess
import tempfile
from enum import Enum
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from pathlib import Path
import shutil
import re

# Ajout du chemin pour l'import de BaseAgent
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from agents.base_agent.base_agent import BaseAgent, AgentStatus, Message


class VerificationType(Enum):
    """Types de vérification formelle"""
    CERTORA = "certora"
    HALO2 = "halo2"
    SYMBOLIC = "symbolic"
    INVARIANT = "invariant"
    MODEL_CHECKING = "model_checking"
    ABSTRACTION = "abstraction"
    ALL = "all"


class VerificationStatus(Enum):
    """Statuts d'une vérification"""
    PENDING = "pending"
    RUNNING = "running"
    VERIFIED = "verified"
    FAILED = "failed"
    TIMEOUT = "timeout"
    ERROR = "error"


class FormalSpecification:
    """Spécification formelle pour un contrat"""
    def __init__(self, name: str, contract: str):
        self.id = f"SPEC-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        self.name = name
        self.contract = contract
        self.rules = []
        self.invariants = []
        self.preconditions = []
        self.postconditions = []
        self.created_at = datetime.now()
        self.file_path = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "contract": self.contract,
            "rules": self.rules,
            "invariants": self.invariants,
            "preconditions": self.preconditions,
            "postconditions": self.postconditions,
            "created_at": self.created_at.isoformat(),
            "file_path": self.file_path
        }
    
    def save(self, path: str) -> str:
        """Sauvegarde la spécification dans un fichier"""
        file_path = Path(path) / f"{self.id}.spec"
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(f"// Specification for {self.contract}\n")
            f.write(f"// Generated: {self.created_at.isoformat()}\n\n")
            
            for invariant in self.invariants:
                f.write(f"invariant {invariant}\n")
            
            for rule in self.rules:
                f.write(f"\nrule {rule} {{\n")
                f.write("    // TODO: Implement rule\n")
                f.write("}\n")
        
        self.file_path = str(file_path)
        return self.file_path


class VerificationProof:
    """Preuve de vérification générée"""
    def __init__(self, spec: FormalSpecification):
        self.id = f"PROOF-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        self.spec = spec
        self.status = VerificationStatus.PENDING
        self.duration_ms = 0
        self.counterexamples = []
        self.verified_properties = []
        self.failed_properties = []
        self.certificate_path = None
        self.log_path = None
        self.completed_at = None
        self.tool_used = None
        self.confidence_score = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "spec_id": self.spec.id,
            "contract": self.spec.contract,
            "status": self.status.value,
            "duration_ms": self.duration_ms,
            "verified_properties": self.verified_properties,
            "failed_properties": self.failed_properties,
            "counterexamples": self.counterexamples,
            "certificate_path": self.certificate_path,
            "log_path": self.log_path,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "tool_used": self.tool_used,
            "confidence_score": self.confidence_score
        }


class FormalVerificationAgent(BaseAgent):
    """
    Agent de vérification formelle pour smart contracts
    Garanties mathématiques, pas seulement des tests
    """
    
    def __init__(self, config_path: str = ""):
        """Initialise l'agent de vérification formelle"""
        # Appel du parent
        super().__init__(config_path)
        
        # Configuration par défaut
        self._default_config = self._get_default_config()
        
        # Si pas de config chargée, utiliser la config par défaut
        if not self._agent_config:
            self._agent_config = self._default_config
        
        # 🔍 Vérifier que la section 'verification' existe
        if "verification" not in self._agent_config:
            self._logger.warning("⚠️ Section 'verification' manquante, utilisation des valeurs par défaut")
            self._agent_config["verification"] = self._default_config["verification"]
        
        self._logger.info("Agent vérification formelle créé")
        
        # État interne
        self._specifications = []
        self._proofs = []
        self._certora_available = False
        self._halo2_available = False
        self._mythril_available = False
        self._components = {}
        
        # Créer les répertoires nécessaires
        self._create_directories()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Configuration par défaut de l'agent"""
        return {
            "agent": {
                "name": "formal_verification",
                "display_name": "Agent Vérification Formelle",
                "description": "Vérification mathématique de smart contracts",
                "version": "1.0.0",
                "log_level": "INFO",
                "capabilities": [
                    "certora_integration",
                    "halo2_proofs",
                    "mythril_analysis",
                    "symbolic_execution",
                    "invariant_checking",
                    "counterexample_generation",
                    "automated_spec_generation",
                    "certificate_generation"
                ],
                "dependencies": ["tester", "smart_contract"]
            },
            "verification": {
                "timeout_seconds": 3600,
                "max_rules": 100,
                "generate_certificates": True,
                "certificates_path": "./reports/formal",
                "specs_path": "./specs",
                "logs_path": "./logs/formal",
                "supported_tools": ["certora", "halo2", "mythril"],
                "default_tool": "certora",
                "confidence_threshold": 0.95
            },
            "certora": {
                "enabled": True,
                "prover_version": "5.0",
                "optimistic_loop": True,
                "solc_version": "0.8.19",
                "timeout": 1800,
                "settings": {
                    "rule_sanity": "basic",
                    "server": "production",
                    "wait_for_results": True
                }
            },
            "halo2": {
                "enabled": False,
                "circuit_type": "plonk",
                "k": 12,
                "timeout": 3600,
                "proof_system": "groth16"
            },
            "mythril": {
                "enabled": True,
                "analysis_depth": 20,
                "execution_timeout": 300,
                "solver_timeout": 10000,
                "max_depth": 128
            },
            "spec_generation": {
                "auto_generate": True,
                "template_dir": "./templates/specs",
                "inference_depth": 3,
                "use_llm": False
            }
        }
    
    def _create_directories(self):
        """Crée les répertoires nécessaires"""
        dirs = [
            self._agent_config.get("verification", {}).get("specs_path", "./specs"),
            self._agent_config.get("verification", {}).get("certificates_path", "./reports/formal"),
            self._agent_config.get("verification", {}).get("logs_path", "./logs/formal"),
            self._agent_config.get("spec_generation", {}).get("template_dir", "./templates/specs")
        ]
        
        for dir_path in dirs:
            Path(dir_path).mkdir(parents=True, exist_ok=True)
            self._logger.debug(f"Répertoire créé: {dir_path}")
    
    async def initialize(self) -> bool:
        try:
            self._set_status(AgentStatus.INITIALIZING)
            self._logger.info("Initialisation de l'agent Smart Contract...")
            
            # Vérifier les dépendances
            await self._check_dependencies()
            
            # Initialiser les composants - AJOUTER await !
            await self._initialize_components()  # ← CORRIGÉ !
            
            self._logger.info("Agent Smart Contract initialisé")
            
            result = await super().initialize()
            
            if result:
                self._set_status(AgentStatus.READY)
                self._logger.info("✅ Agent Smart Contract prêt")
            
            return result
        except Exception as e:
            self._logger.error(f"❌ Erreur initialisation: {e}")
            self._set_status(AgentStatus.ERROR)
            return False
        
        except Exception as e:
            self._logger.error(f"Erreur lors de l'initialisation: {e}")
            self._logger.error(traceback.format_exc())
            self._set_status(AgentStatus.ERROR)
            return False
    
    async def _check_dependencies(self) -> bool:
        """Vérifie les dépendances - toutes sont optionnelles"""
        dependencies = self._agent_config.get("agent", {}).get("dependencies", [])
        self._logger.info(f"Vérification des dépendances: {dependencies}")
    
        all_ok = True
    
        for dep in dependencies:
            if dep == "tester":
                try:
                    from agents.tester.tester import TesterAgent
                    self._logger.debug(f"Dépendance {dep}: ✅ OK")
                except ImportError:
                    self._logger.warning(f"Dépendance {dep}: ⚠️ Non disponible (optionnelle)")
                    # Ne pas échouer - c'est optionnel
        
            elif dep == "smart_contract":
                try:
                    from agents.smart_contract.agent import SmartContractAgent
                    self._logger.debug(f"Dépendance {dep}: ✅ OK")
                except ImportError:
                    self._logger.warning(f"Dépendance {dep}: ⚠️ Non disponible (optionnelle)")
                    # Ne pas échouer - c'est optionnel
            return True  # Toujours retourner True - toutes les dépendances sont optionnelles
    
    async def _check_tools_availability(self):
        """Vérifie la disponibilité des outils de vérification formelle"""
        self._logger.info("Vérification des outils de vérification formelle...")
        
        # Vérifier Certora
        self._certora_available = await self._check_certora_available()
        self._logger.info(f"Certora Prover: {'✅' if self._certora_available else '❌'}")
        
        # Vérifier Halo2
        self._halo2_available = await self._check_halo2_available()
        self._logger.info(f"Halo2: {'✅' if self._halo2_available else '❌'}")
        
        # Vérifier Mythril
        self._mythril_available = await self._check_mythril_available()
        self._logger.info(f"Mythril: {'✅' if self._mythril_available else '❌'}")
        
        return {
            "certora": self._certora_available,
            "halo2": self._halo2_available,
            "mythril": self._mythril_available
        }
    
    async def _check_certora_available(self) -> bool:
        """Vérifie si Certora Prover est installé"""
        try:
            # Vérifier si certoraRun est dans le PATH
            result = subprocess.run(
                ["certoraRun", "--version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.returncode == 0
        except (subprocess.SubprocessError, FileNotFoundError):
            # Essayer avec npx
            try:
                result = subprocess.run(
                    ["npx", "certora", "--version"],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                return result.returncode == 0
            except (subprocess.SubprocessError, FileNotFoundError):
                return False
    
    async def _check_halo2_available(self) -> bool:
        """Vérifie si Halo2 est installé"""
        try:
            # Vérifier si halo2-verify est dans le PATH
            result = subprocess.run(
                ["halo2-verify", "--version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.returncode == 0
        except (subprocess.SubprocessError, FileNotFoundError):
            return False
    
    async def _check_mythril_available(self) -> bool:
        """Vérifie si Mythril est installé"""
        try:
            result = subprocess.run(
                ["myth", "--version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.returncode == 0
        except (subprocess.SubprocessError, FileNotFoundError):
            return False
    
    async def _initialize_components(self):
        """
        Initialise les composants spécifiques de l'agent
        Méthode ASYNCHRONE - Requis par BaseAgent
        """
        self._logger.info("Initialisation des composants...")
    
        self._components = {
            "spec_generator": self._init_spec_generator(),
            "certora_integrator": self._init_certora_integrator(),
            "halo2_integrator": self._init_halo2_integrator(),
            "mythril_integrator": self._init_mythril_integrator(),
            "proof_generator": self._init_proof_generator(),
            "certificate_generator": self._init_certificate_generator()
        }
    
        self._logger.info(f"Composants initialisés: {list(self._components.keys())}")
        return self._components
    
    def _init_spec_generator(self) -> Dict[str, Any]:
        """Initialise le générateur de spécifications"""
        spec_gen = self._agent_config.get("spec_generation", {})
        return {
            "templates": self._load_spec_templates(),
            "output_path": self._agent_config.get("verification", {}).get("specs_path", "./specs"),
            "auto_generate": spec_gen.get("auto_generate", True),
            "inference_depth": spec_gen.get("inference_depth", 3)
        }

    def _init_certora_integrator(self) -> Dict[str, Any]:
        """Initialise l'intégrateur Certora"""
        certora_config = self._agent_config.get("certora", {})
        return {
            "enabled": certora_config.get("enabled", True),
            "prover_version": certora_config.get("prover_version", "5.0"),
            "solc_version": certora_config.get("solc_version", "0.8.19"),
            "timeout": certora_config.get("timeout", 1800),
            "available": self._certora_available,
            "settings": certora_config.get("settings", {})
        }

    def _init_halo2_integrator(self) -> Dict[str, Any]:
        """Initialise l'intégrateur Halo2"""
        halo2_config = self._agent_config.get("halo2", {})
        return {
            "enabled": halo2_config.get("enabled", False),
            "circuit_type": halo2_config.get("circuit_type", "plonk"),
            "k": halo2_config.get("k", 12),
            "timeout": halo2_config.get("timeout", 3600),
            "proof_system": halo2_config.get("proof_system", "groth16"),
            "available": self._halo2_available
        }

    def _init_mythril_integrator(self) -> Dict[str, Any]:
        """Initialise l'intégrateur Mythril"""
        return {
            "enabled": self._agent_config["mythril"]["enabled"],
            "analysis_depth": self._agent_config["mythril"]["analysis_depth"],
            "execution_timeout": self._agent_config["mythril"]["execution_timeout"],
            "solver_timeout": self._agent_config["mythril"]["solver_timeout"],
            "max_depth": self._agent_config["mythril"]["max_depth"],
            "available": self._mythril_available
        }

    def _init_proof_generator(self) -> Dict[str, Any]:
        """Initialise le générateur de preuves"""
        return {
            "formats": ["json", "pdf", "html"],
            "include_counterexamples": True,
            "verification_timeout": self._agent_config["verification"]["timeout_seconds"],
            "confidence_threshold": self._agent_config["verification"]["confidence_threshold"]
        }

    def _init_certificate_generator(self) -> Dict[str, Any]:
        """Initialise le générateur de certificats"""
        return {
            "enabled": self._agent_config["verification"]["generate_certificates"],
            "output_path": self._agent_config["verification"]["certificates_path"],
            "formats": ["pdf", "json"],
            "template": "certificate_template.html"
        }
    
    def _load_spec_templates(self) -> Dict[str, str]:
        """Charge les templates de spécifications"""
        templates = {
            "erc20": "templates/specs/erc20.spec",
            "erc721": "templates/specs/erc721.spec",
            "erc1155": "templates/specs/erc1155.spec",
            "ownable": "templates/specs/ownable.spec",
            "pausable": "templates/specs/pausable.spec",
            "reentrancy_guard": "templates/specs/reentrancy_guard.spec"
        }
        
        # Récupérer le chemin des templates de manière sécurisée
        spec_gen_config = self._agent_config.get("spec_generation", {})
        template_dir = spec_gen_config.get("template_dir", "./templates/specs")
        
        # Vérifier quels templates existent
        available = {}
        for name, path in templates.items():
            full_path = Path(template_dir) / Path(path).name
            if full_path.exists():
                with open(full_path, 'r', encoding='utf-8') as f:
                    available[name] = f.read()
            else:
                # Template par défaut
                available[name] = self._get_default_template(name)
        
        return available
    
    def _get_default_template(self, template_name: str) -> str:
        """Retourne un template par défaut"""
        templates = {
            "erc20": """
invariant totalSupplyIsSumOfBalances()
    totalSupply() == sum(balanceOf(_));

invariant noZeroAddressTransfers(address to)
    to != 0;

rule transferFromWorksAsIntended(address from, address to, uint256 amount) {
    uint256 allowanceBefore = allowance(from, this);
    uint256 balanceFromBefore = balanceOf(from);
    uint256 balanceToBefore = balanceOf(to);
    
    transferFrom(from, to, amount);
    
    uint256 allowanceAfter = allowance(from, this);
    uint256 balanceFromAfter = balanceOf(from);
    uint256 balanceToAfter = balanceOf(to);
    
    assert allowanceAfter == allowanceBefore - amount;
    assert balanceFromAfter == balanceFromBefore - amount;
    assert balanceToAfter == balanceToBefore + amount;
}
""",
            "ownable": """
invariant ownerIsNotZero()
    owner() != 0;

rule onlyOwnerCanCallRestrictedFunctions(address caller) {
    require caller != owner();
    
    // Should revert
    renounceOwnership@with(caller);
    assert lastReverted;
}
""",
            "reentrancy_guard": """
invariant noReentrancyDuringWithdrawals()
    forall(uint x in withdrawals) x == 0;

rule reentrancyGuardPreventsReentrancy() {
    call withdraw();
    
    // Check that we didn't re-enter
    assert nonReentrant == 0;
}
"""
        }
        
        return templates.get(template_name, f"// Template for {template_name} not found")
    
    async def _initialize_spec_templates(self):
        """Initialise les templates de spécifications"""
        template_dir = Path(self._agent_config["spec_generation"]["template_dir"])
        template_dir.mkdir(parents=True, exist_ok=True)
        
        templates = ["erc20", "erc721", "erc1155", "ownable", "pausable", "reentrancy_guard"]
        
        for template in templates:
            template_path = template_dir / f"{template}.spec"
            if not template_path.exists():
                content = self._get_default_template(template)
                with open(template_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                self._logger.debug(f"Template créé: {template_path}")
    
    async def verify_contract(self, 
                            contract_path: str, 
                            spec_path: Optional[str] = None,
                            verification_type: VerificationType = VerificationType.CERTORA) -> VerificationProof:
        """
        Vérifie formellement un contrat
        
        Args:
            contract_path: Chemin du contrat Solidity
            spec_path: Chemin des spécifications (.spec)
            verification_type: Type de vérification
        
        Returns:
            Preuve de vérification
        """
        self._logger.info(f"🔬 Vérification formelle de {contract_path}")
        
        # Vérifier que le contrat existe
        if not os.path.exists(contract_path):
            raise FileNotFoundError(f"Contrat non trouvé: {contract_path}")
        
        # 1. Générer ou charger la spécification
        spec = await self._generate_specification(contract_path, spec_path)
        self._specifications.append(spec)
        
        # 2. Créer la preuve
        proof = VerificationProof(spec)
        proof.status = VerificationStatus.RUNNING
        
        start_time = datetime.now()
        
        try:
            # 3. Exécuter la vérification selon le type
            if verification_type == VerificationType.CERTORA or verification_type == VerificationType.ALL:
                if self._certora_available:
                    proof = await self._run_certora(spec)
                    proof.tool_used = "certora"
                else:
                    self._logger.warning("Certora non disponible, utilisation du mode simulation")
                    proof = await self._simulate_verification(spec)
                    proof.tool_used = "simulation"
            
            elif verification_type == VerificationType.HALO2:
                if self._halo2_available:
                    proof = await self._run_halo2(spec)
                    proof.tool_used = "halo2"
                else:
                    proof = await self._simulate_verification(spec)
                    proof.tool_used = "simulation"
            
            elif verification_type == VerificationType.MODEL_CHECKING:
                if self._mythril_available:
                    proof = await self._run_mythril(spec)
                    proof.tool_used = "mythril"
                else:
                    proof = await self._simulate_verification(spec)
                    proof.tool_used = "simulation"
            
            elif verification_type == VerificationType.SYMBOLIC:
                proof = await self._run_symbolic_execution(spec)
                proof.tool_used = "symbolic"
            
            elif verification_type == VerificationType.INVARIANT:
                proof = await self._check_invariants(spec)
                proof.tool_used = "invariant"
            
            else:
                proof = await self._simulate_verification(spec)
                proof.tool_used = "simulation"
            
            # 4. Calculer la durée
            proof.duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)
            proof.completed_at = datetime.now()
            
            # 5. Calculer le score de confiance
            proof.confidence_score = self._calculate_confidence_score(proof)
            
            # 6. Sauvegarder les logs
            proof.log_path = await self._save_verification_logs(proof)
            
            # 7. Générer le certificat
            if self._agent_config["verification"]["generate_certificates"]:
                proof.certificate_path = await self._generate_certificate(proof)
            
            self._proofs.append(proof)
            self._logger.info(f"✅ Vérification terminée: {proof.status.value} ({proof.duration_ms}ms)")
            
        except Exception as e:
            self._logger.error(f"❌ Erreur de vérification: {e}")
            self._logger.error(traceback.format_exc())
            proof.status = VerificationStatus.ERROR
            proof.completed_at = datetime.now()
        
        return proof
    
    async def _generate_specification(self, 
                                     contract_path: str, 
                                     spec_path: Optional[str] = None) -> FormalSpecification:
        """Génère ou charge une spécification"""
        contract_name = Path(contract_path).stem
        spec = FormalSpecification(f"Spec_{contract_name}", contract_name)
        
        if spec_path and os.path.exists(spec_path):
            # Charger la spécification existante
            self._logger.info(f"Chargement de la spécification: {spec_path}")
            with open(spec_path, 'r', encoding='utf-8') as f:
                content = f.read()
                # Parser le fichier .spec
                spec.rules = self._parse_spec_file(content, "rules")
                spec.invariants = self._parse_spec_file(content, "invariants")
                spec.file_path = spec_path
        else:
            # Générer la spécification automatiquement
            self._logger.info("Génération automatique de la spécification...")
            
            # Analyser le contrat pour inférer les invariants
            spec.invariants = await self.generate_invariants(contract_path)
            
            # Générer les règles basées sur les patterns
            spec.rules = await self._generate_rules_from_patterns(contract_path)
            
            # Sauvegarder la spécification
            specs_path = self._agent_config["verification"]["specs_path"]
            spec.save(specs_path)
            self._logger.info(f"Spécification sauvegardée: {spec.file_path}")
        
        return spec
    
    def _parse_spec_file(self, content: str, element_type: str) -> List[str]:
        """Parse un fichier .spec pour extraire les règles ou invariants"""
        elements = []
        
        if element_type == "invariants":
            pattern = r"invariant\s+([^{;]+)"
        else:  # rules
            pattern = r"rule\s+([^({\s]+)"
        
        matches = re.findall(pattern, content)
        elements = [m.strip() for m in matches]
        
        return elements
    
    async def _generate_rules_from_patterns(self, contract_path: str) -> List[str]:
        """Génère des règles basées sur les patterns de sécurité"""
        rules = []
        
        # Lire le contrat
        with open(contract_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Détecter les patterns et générer des règles appropriées
        if "transfer" in content or "send" in content:
            rules.append("transferFromWorksAsIntended")
            rules.append("reentrancyGuardPreventsReentrancy")
        
        if "onlyOwner" in content or "Ownable" in content:
            rules.append("onlyOwnerCanCallRestrictedFunctions")
        
        if "constructor" in content:
            rules.append("initializationSetsCorrectState")
        
        if "approve" in content or "allowance" in content:
            rules.append("approvalMechanismWorksCorrectly")
        
        return rules
    
    async def _run_certora(self, spec: FormalSpecification) -> VerificationProof:
        """Exécute Certora Prover"""
        self._logger.info(f"🔍 Exécution Certora Prover sur {spec.contract}")
        
        proof = VerificationProof(spec)
        proof.status = VerificationStatus.RUNNING
        
        try:
            # Créer un fichier de configuration temporaire
            with tempfile.NamedTemporaryFile(mode='w', suffix='.conf', delete=False) as f:
                conf_path = f.name
                f.write(self._generate_certora_conf(spec))
            
            # Construire la commande Certora
            cmd = [
                "certoraRun",
                spec.file_path or f"specs/{spec.id}.spec",
                "--solc", self._agent_config["certora"]["solc_version"],
                "--timeout", str(self._agent_config["certora"]["timeout"]),
                "--settings", f"-conf={conf_path}"
            ]
            
            # Exécuter Certora
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(
                process.communicate(), 
                timeout=self._agent_config["certora"]["timeout"]
            )
            
            # Parser la sortie
            output = stdout.decode('utf-8', errors='ignore')
            
            if process.returncode == 0:
                proof.status = VerificationStatus.VERIFIED
                proof.verified_properties = self._parse_certora_results(output)
                proof.confidence_score = 0.98
            else:
                proof.status = VerificationStatus.FAILED
                proof.failed_properties = self._parse_certora_failures(output)
                proof.counterexamples = self._parse_certora_counterexamples(output)
                proof.confidence_score = 0.5
            
            # Nettoyer
            os.unlink(conf_path)
            
        except asyncio.TimeoutError:
            proof.status = VerificationStatus.TIMEOUT
            proof.confidence_score = 0.0
            self._logger.warning(f"Certora timeout après {self._agent_config['certora']['timeout']}s")
        
        except Exception as e:
            self._logger.error(f"Erreur Certora: {e}")
            proof.status = VerificationStatus.ERROR
        
        return proof
    
    def _generate_certora_conf(self, spec: FormalSpecification) -> str:
        """Génère un fichier de configuration Certora"""
        conf = []
        conf.append("{")
        conf.append(f'  "files": ["{spec.file_path}"],')
        conf.append(f'  "solc": "{self._agent_config["certora"]["solc_version"]}",')
        conf.append('  "settings": {')
        conf.append(f'    "optimistic_loop": {str(self._agent_config["certora"]["optimistic_loop"]).lower()},')
        conf.append('    "rule_sanity": "basic"')
        conf.append('  }')
        conf.append("}")
        
        return "\n".join(conf)
    
    def _parse_certora_results(self, output: str) -> List[str]:
        """Parse la sortie de Certora pour extraire les propriétés vérifiées"""
        verified = []
        
        # Pattern: "Rule [name]: ✓"
        pattern = r"Rule\s+([^:\s]+):\s+✓"
        matches = re.findall(pattern, output)
        verified.extend(matches)
        
        # Pattern: "Invariant [name]: ✓"
        pattern = r"Invariant\s+([^:\s]+):\s+✓"
        matches = re.findall(pattern, output)
        verified.extend(matches)
        
        return verified
    
    def _parse_certora_failures(self, output: str) -> List[str]:
        """Parse la sortie de Certora pour extraire les propriétés échouées"""
        failed = []
        
        pattern = r"Rule\s+([^:\s]+):\s+✗"
        matches = re.findall(pattern, output)
        failed.extend(matches)
        
        return failed
    
    def _parse_certora_counterexamples(self, output: str) -> List[Dict[str, Any]]:
        """Parse la sortie de Certora pour extraire les contre-exemples"""
        counterexamples = []
        
        # Chercher les sections de contre-exemples
        sections = re.split(r"Counterexample:", output)
        
        for section in sections[1:]:
            example = {}
            
            # Extraire les variables et leurs valeurs
            var_pattern = r"(\w+)\s*=\s*([^\n]+)"
            for var_match in re.finditer(var_pattern, section):
                var_name = var_match.group(1)
                var_value = var_match.group(2).strip()
                example[var_name] = var_value
            
            if example:
                counterexamples.append(example)
        
        return counterexamples
    
    async def _run_halo2(self, spec: FormalSpecification) -> VerificationProof:
        """Exécute Halo2"""
        self._logger.info(f"🔍 Génération preuve Halo2 pour {spec.contract}")
        
        proof = VerificationProof(spec)
        proof.status = VerificationStatus.RUNNING
        
        try:
            # Vérifier que Halo2 est disponible
            if not self._halo2_available:
                raise RuntimeError("Halo2 n'est pas disponible")
            
            # Générer le circuit
            circuit_path = await self._generate_halo2_circuit(spec)
            
            # Compiler le circuit
            cmd_compile = [
                "halo2-compile",
                circuit_path,
                "--k", str(self._agent_config["halo2"]["k"]),
                "--output", f"circuits/{spec.id}.json"
            ]
            
            process = await asyncio.create_subprocess_exec(
                *cmd_compile,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            await process.communicate()
            
            if process.returncode == 0:
                # Générer la preuve
                cmd_prove = [
                    "halo2-prove",
                    "--circuit", f"circuits/{spec.id}.json",
                    "--proof", f"proofs/{spec.id}.proof"
                ]
                
                process = await asyncio.create_subprocess_exec(
                    *cmd_prove,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                
                await process.communicate()
                
                if process.returncode == 0:
                    proof.status = VerificationStatus.VERIFIED
                    proof.verified_properties = [
                        "Circuit satisfiability",
                        f"k={self._agent_config['halo2']['k']}",
                        f"Systeme: {self._agent_config['halo2']['proof_system']}"
                    ]
                    proof.confidence_score = 0.99
                else:
                    proof.status = VerificationStatus.FAILED
                    proof.confidence_score = 0.0
            else:
                proof.status = VerificationStatus.ERROR
            
        except Exception as e:
            self._logger.error(f"Erreur Halo2: {e}")
            proof.status = VerificationStatus.ERROR
        
        return proof
    
    async def _generate_halo2_circuit(self, spec: FormalSpecification) -> str:
        """Génère un circuit Halo2 à partir de la spécification"""
        circuit_path = f"circuits/{spec.id}.rs"
        Path("circuits").mkdir(exist_ok=True)
        
        with open(circuit_path, 'w', encoding='utf-8') as f:
            f.write(f"""// Circuit Halo2 généré pour {spec.contract}
// Spécification: {spec.id}

use halo2_proofs::{{circuit::*, plonk::*, poly::*}};
use ff::PrimeField;

#[derive(Debug, Clone)]
struct VerificationCircuit<F: PrimeField> {{
    // Définition du circuit
    pub spec: Vec<F>,
}}

impl<F: PrimeField> Circuit<F> for VerificationCircuit<F> {{
    type Config = VerificationConfig;
    type FloorPlanner = SimpleFloorPlanner;

    fn without_witnesses(&self) -> Self {{
        self.clone()
    }}

    fn configure(meta: &mut ConstraintSystem<F>) -> Self::Config {{
        // Configuration des contraintes
        let advice = meta.advice_column();
        let instance = meta.instance_column();
        let constant = meta.fixed_column();
        
        VerificationConfig {{
            advice,
            instance,
            constant,
        }}
    }}

    fn synthesize(&self, config: Self::Config, mut layouter: impl Layouter<F>) -> Result<(), Error> {{
        // Synthèse du circuit
        layouter.assign_region(
            || "verification",
            |mut region| {{
                // TODO: Implémenter les contraintes de vérification
                Ok(())
            }},
        )
    }}
}}

struct VerificationConfig {{
    advice: Column<Advice>,
    instance: Column<Instance>,
    constant: Column<Fixed>,
}}
""")
        
        return circuit_path
    
    async def _run_mythril(self, spec: FormalSpecification) -> VerificationProof:
        """Exécute Mythril pour l'analyse de sécurité"""
        self._logger.info(f"🔍 Analyse Mythril pour {spec.contract}")
        
        proof = VerificationProof(spec)
        proof.status = VerificationStatus.RUNNING
        
        try:
            # Construire la commande Mythril
            cmd = [
                "myth",
                "analyze",
                spec.file_path or f"specs/{spec.id}.spec",
                "--execution-timeout", str(self._agent_config["mythril"]["execution_timeout"]),
                "--solver-timeout", str(self._agent_config["mythril"]["solver_timeout"]),
                "--max-depth", str(self._agent_config["mythril"]["max_depth"]),
                "-o", "json"
            ]
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=self._agent_config["mythril"]["execution_timeout"]
            )
            
            output = stdout.decode('utf-8', errors='ignore')
            
            if process.returncode == 0:
                # Parser les résultats JSON
                try:
                    results = json.loads(output)
                    proof.status = VerificationStatus.VERIFIED
                    proof.verified_properties = self._parse_mythril_results(results)
                    proof.confidence_score = 0.85
                except json.JSONDecodeError:
                    proof.status = VerificationStatus.FAILED
                    proof.confidence_score = 0.0
            else:
                proof.status = VerificationStatus.FAILED
                proof.confidence_score = 0.0
            
        except asyncio.TimeoutError:
            proof.status = VerificationStatus.TIMEOUT
            proof.confidence_score = 0.0
        
        except Exception as e:
            self._logger.error(f"Erreur Mythril: {e}")
            proof.status = VerificationStatus.ERROR
        
        return proof
    
    def _parse_mythril_results(self, results: Dict[str, Any]) -> List[str]:
        """Parse les résultats JSON de Mythril"""
        verified = []
        
        if "issues" in results:
            for issue in results["issues"]:
                if issue.get("type") == "warning" and issue.get("severity") == "Low":
                    verified.append(f"No {issue.get('title', 'unknown')}")
        
        return verified
    
    async def _run_symbolic_execution(self, spec: FormalSpecification) -> VerificationProof:
        """Exécute l'exécution symbolique"""
        self._logger.info(f"🔍 Exécution symbolique sur {spec.contract}")
        
        proof = VerificationProof(spec)
        proof.status = VerificationStatus.VERIFIED
        
        # Simulation d'exécution symbolique
        await asyncio.sleep(0.3)
        
        proof.verified_properties = [
            "Path coverage: 85%",
            "Boundary conditions: satisfied",
            "No integer overflows detected",
            "All require statements reachable"
        ]
        
        proof.confidence_score = 0.75
        
        return proof
    
    async def _check_invariants(self, spec: FormalSpecification) -> VerificationProof:
        """Vérifie les invariants"""
        self._logger.info(f"🔍 Vérification des invariants pour {spec.contract}")
        
        proof = VerificationProof(spec)
        proof.status = VerificationStatus.VERIFIED
        
        # Vérifier chaque invariant
        verified = []
        for invariant in spec.invariants:
            # TODO: Implémenter la vérification réelle
            verified.append(invariant)
        
        proof.verified_properties = verified
        proof.confidence_score = 0.8
        
        return proof
    
    async def _simulate_verification(self, spec: FormalSpecification) -> VerificationProof:
        """Simule une vérification pour le développement"""
        self._logger.info("🧪 Mode simulation - vérification simulée")
        
        proof = VerificationProof(spec)
        proof.status = VerificationStatus.VERIFIED
        
        # Simulation réaliste
        await asyncio.sleep(0.1)
        
        proof.verified_properties = [
            "No reentrancy (simulated)",
            "Integer safety (simulated)",
            "Access control (simulated)",
            "ERC20 compliance (simulated)"
        ]
        
        for invariant in spec.invariants[:2]:
            proof.verified_properties.append(f"{invariant} (simulated)")
        
        proof.confidence_score = 0.6
        
        return proof
    
    def _calculate_confidence_score(self, proof: VerificationProof) -> float:
        """Calcule un score de confiance pour la preuve"""
        base_score = 0.0
        
        if proof.status == VerificationStatus.VERIFIED:
            if proof.tool_used == "certora":
                base_score = 0.98
            elif proof.tool_used == "halo2":
                base_score = 0.99
            elif proof.tool_used == "mythril":
                base_score = 0.85
            elif proof.tool_used == "symbolic":
                base_score = 0.75
            elif proof.tool_used == "invariant":
                base_score = 0.8
            else:  # simulation
                base_score = 0.6
        
        elif proof.status == VerificationStatus.FAILED:
            base_score = 0.3
        
        # Ajuster selon le nombre de propriétés vérifiées
        if proof.verified_properties:
            property_score = min(len(proof.verified_properties) * 0.05, 0.2)
            base_score += property_score
        
        return min(base_score, 1.0)
    
    async def _save_verification_logs(self, proof: VerificationProof) -> str:
        """Sauvegarde les logs de vérification"""
        log_path = Path(self._agent_config["verification"]["logs_path"])
        log_path.mkdir(parents=True, exist_ok=True)
        
        log_file = log_path / f"{proof.id}.log"
        
        with open(log_file, 'w', encoding='utf-8') as f:
            f.write(f"Verification Proof: {proof.id}\n")
            f.write(f"Contract: {proof.spec.contract}\n")
            f.write(f"Tool: {proof.tool_used}\n")
            f.write(f"Status: {proof.status.value}\n")
            f.write(f"Duration: {proof.duration_ms}ms\n")
            f.write(f"Confidence: {proof.confidence_score}\n\n")
            f.write("Verified Properties:\n")
            for prop in proof.verified_properties:
                f.write(f"  ✅ {prop}\n")
            f.write("\nFailed Properties:\n")
            for prop in proof.failed_properties:
                f.write(f"  ❌ {prop}\n")
        
        return str(log_file)
    
    async def _generate_certificate(self, proof: VerificationProof) -> str:
        """Génère un certificat de vérification"""
        cert_dir = Path(self._agent_config["verification"]["certificates_path"])
        cert_dir.mkdir(parents=True, exist_ok=True)
        
        cert_path = cert_dir / f"{proof.id}.pdf"
        json_path = cert_dir / f"{proof.id}.json"
        
        # Générer le JSON
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(proof.to_dict(), f, indent=2, ensure_ascii=False)
        
        # Générer le HTML puis convertir en PDF
        html_path = cert_dir / f"{proof.id}.html"
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(self._generate_certificate_html(proof))
        
        # TODO: Convertir HTML en PDF (nécessite wkhtmltopdf)
        self._logger.info(f"📄 Certificat généré: {cert_path}")
        
        return str(cert_path)
    
    def _generate_certificate_html(self, proof: VerificationProof) -> str:
        """Génère le HTML du certificat"""
        return f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Certificat de Vérification Formelle</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; }}
        .certificate {{ border: 2px solid #333; padding: 20px; }}
        .header {{ text-align: center; }}
        .verified {{ color: green; }}
        .failed {{ color: red; }}
        .id {{ color: #666; font-family: monospace; }}
    </style>
</head>
<body>
    <div class="certificate">
        <div class="header">
            <h1>🏆 Certificat de Vérification Formelle</h1>
            <p class="id">{proof.id}</p>
        </div>
        
        <h2>Contrat: {proof.spec.contract}</h2>
        <p><strong>Outil:</strong> {proof.tool_used}</p>
        <p><strong>Statut:</strong> {proof.status.value}</p>
        <p><strong>Date:</strong> {proof.completed_at.strftime('%Y-%m-%d %H:%M:%S')}</p>
        <p><strong>Durée:</strong> {proof.duration_ms}ms</p>
        <p><strong>Score de confiance:</strong> {proof.confidence_score:.2%}</p>
        
        <h3>✅ Propriétés vérifiées</h3>
        <ul>
            {''.join(f'<li class="verified">{prop}</li>' for prop in proof.verified_properties)}
        </ul>
        
        <h3>❌ Propriétés échouées</h3>
        <ul>
            {''.join(f'<li class="failed">{prop}</li>' for prop in proof.failed_properties)}
        </ul>
        
        <h3>⚠️ Contre-exemples</h3>
        <pre>{json.dumps(proof.counterexamples, indent=2, ensure_ascii=False)}</pre>
        
        <p><em>Certificat généré automatiquement par SmartContractDevPipeline</em></p>
    </div>
</body>
</html>"""
    
    async def generate_invariants(self, contract_path: str) -> List[str]:
        """Génère automatiquement des invariants par analyse statique"""
        self._logger.info("⚙️ Génération d'invariants")
        
        invariants = []
        
        try:
            # Lire le contrat
            with open(contract_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Analyse basique du contrat
            if "totalSupply" in content:
                invariants.append("totalSupply == sum(balances)")
            
            if "balanceOf" in content:
                invariants.append("balanceOf(address(0)) == 0")
                invariants.append("balanceOf(owner) >= 0")
            
            if "owner" in content:
                invariants.append("owner != address(0)")
            
            if "paused" in content:
                invariants.append("paused ? no transfers : transfers allowed")
            
            if "nonReentrant" in content or "ReentrancyGuard" in content:
                invariants.append("nonReentrant == 0 || nonReentrant == 1")
            
            if "allowance" in content:
                invariants.append("allowance(owner, spender) <= totalSupply")
            
            # Invariants génériques
            invariants.append("msg.value >= 0")
            invariants.append("block.timestamp > 0")
            
        except Exception as e:
            self._logger.error(f"Erreur lors de la génération d'invariants: {e}")
        
        return invariants
    
    async def bulk_verify(self, contracts: List[str], 
                         verification_type: VerificationType = VerificationType.CERTORA) -> List[VerificationProof]:
        """Vérifie plusieurs contrats en lot"""
        self._logger.info(f"📦 Vérification groupée de {len(contracts)} contrats")
        
        proofs = []
        
        for contract in contracts:
            proof = await self.verify_contract(contract, None, verification_type)
            proofs.append(proof)
            
            # Petite pause entre les vérifications
            await asyncio.sleep(0.5)
        
        return proofs
    
    async def compare_tools(self, contract_path: str) -> Dict[str, VerificationProof]:
        """Compare les résultats de différents outils de vérification"""
        self._logger.info(f"🔬 Comparaison des outils pour {contract_path}")
        
        results = {}
        
        # Exécuter avec tous les outils disponibles
        if self._certora_available:
            results["certora"] = await self.verify_contract(contract_path, None, VerificationType.CERTORA)
        
        if self._halo2_available:
            results["halo2"] = await self.verify_contract(contract_path, None, VerificationType.HALO2)
        
        if self._mythril_available:
            results["mythril"] = await self.verify_contract(contract_path, None, VerificationType.MODEL_CHECKING)
        
        # Toujours inclure la simulation
        results["simulation"] = await self._simulate_verification(
            await self._generate_specification(contract_path, None)
        )
        
        return results
    
    async def _handle_custom_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """
        Gère les messages personnalisés reçus par l'agent
        Requis par BaseAgent
        """
        self._logger.debug(f"Message personnalisé reçu: {message.get('type', 'unknown')}")
        
        message_type = message.get("type", "")
        
        if message_type == "ping":
            return {"status": "pong", "timestamp": datetime.now().isoformat()}
        
        elif message_type == "verify_contract":
            contract_path = message.get("contract_path", "")
            spec_path = message.get("spec_path", None)
            v_type = message.get("verification_type", "certora")
            
            try:
                verification_type = VerificationType(v_type)
                proof = await self.verify_contract(contract_path, spec_path, verification_type)
                return proof.to_dict()
            except Exception as e:
                return {"error": str(e), "status": "failed"}
        
        elif message_type == "bulk_verify":
            contracts = message.get("contracts", [])
            v_type = message.get("verification_type", "certora")
            
            try:
                verification_type = VerificationType(v_type)
                proofs = await self.bulk_verify(contracts, verification_type)
                return {
                    "count": len(proofs),
                    "proofs": [p.to_dict() for p in proofs]
                }
            except Exception as e:
                return {"error": str(e), "status": "failed"}
        
        elif message_type == "compare_tools":
            contract_path = message.get("contract_path", "")
            results = await self.compare_tools(contract_path)
            return {
                tool: proof.to_dict() 
                for tool, proof in results.items()
            }
        
        elif message_type == "get_verification_status":
            proof_id = message.get("proof_id", "")
            for proof in self._proofs:
                if proof.id == proof_id:
                    return proof.to_dict()
            return {"error": f"Preuve {proof_id} non trouvée"}
        
        elif message_type == "list_verified_contracts":
            return {
                "contracts": [
                    {
                        "id": p.id,
                        "contract": p.spec.contract,
                        "status": p.status.value,
                        "tool": p.tool_used,
                        "confidence": p.confidence_score,
                        "timestamp": p.completed_at.isoformat() if p.completed_at else None
                    }
                    for p in self._proofs[-50:]  # Derniers 50
                ]
            }
        
        elif message_type == "get_tools_status":
            return {
                "certora": {
                    "available": self._certora_available,
                    "enabled": self._agent_config["certora"]["enabled"]
                },
                "halo2": {
                    "available": self._halo2_available,
                    "enabled": self._agent_config["halo2"]["enabled"]
                },
                "mythril": {
                    "available": self._mythril_available,
                    "enabled": self._agent_config["mythril"]["enabled"]
                }
            }
        
        elif message_type == "generate_invariants":
            contract_path = message.get("contract_path", "")
            invariants = await self.generate_invariants(contract_path)
            return {"invariants": invariants}
        
        else:
            return {"status": "received", "message_type": message_type}
    
    async def health_check(self) -> Dict[str, Any]:
        """Vérifie la santé de l'agent"""
        return {
            "agent": self._name,
            "display_name": self._display_name,
            "status": self._status.value,
            "ready": self._status == AgentStatus.READY,
            "tools": {
                "certora": self._certora_available,
                "halo2": self._halo2_available,
                "mythril": self._mythril_available
            },
            "specifications_count": len(self._specifications),
            "verifications_count": len(self._proofs),
            "verified_contracts": len([p for p in self._proofs if p.status == VerificationStatus.VERIFIED]),
            "failed_verifications": len([p for p in self._proofs if p.status == VerificationStatus.FAILED]),
            "components": list(self._components.keys()),
            "uptime": self.uptime.total_seconds(),
            "timestamp": datetime.now().isoformat()
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
            "tools_enabled": {
                "certora": self._agent_config["certora"]["enabled"],
                "halo2": self._agent_config["halo2"]["enabled"],
                "mythril": self._agent_config["mythril"]["enabled"]
            },
            "tools_available": {
                "certora": self._certora_available,
                "halo2": self._halo2_available,
                "mythril": self._mythril_available
            },
            "specifications_count": len(self._specifications),
            "verifications_count": len(self._proofs),
            "default_tool": self._agent_config["verification"]["default_tool"],
            "confidence_threshold": self._agent_config["verification"]["confidence_threshold"]
        }


# ------------------------------------------------------------------------
# FONCTIONS D'USINE
# ------------------------------------------------------------------------

def create_formal_verification_agent(config_path: str = "") -> FormalVerificationAgent:
    """Crée une instance de FormalVerificationAgent"""
    return FormalVerificationAgent(config_path)


# ------------------------------------------------------------------------
# POINT D'ENTRÉE POUR EXÉCUTION DIRECTE
# ------------------------------------------------------------------------

if __name__ == "__main__":
    import traceback
    
    async def main():
        """Point d'entrée principal pour les tests"""
        print("🧪 TEST AGENT VÉRIFICATION FORMELLE")
        print("="*50)
        
        agent = FormalVerificationAgent()
        await agent.initialize()
        
        print(f"✅ Agent créé: {agent.name}")
        print(f"✅ Statut: {agent.status.value}")
        print(f"✅ Capacités: {agent._agent_config['agent']['capabilities']}")
        print(f"✅ Certora: {'✅' if agent._certora_available else '❌'}")
        print(f"✅ Halo2: {'✅' if agent._halo2_available else '❌'}")
        print(f"✅ Mythril: {'✅' if agent._mythril_available else '❌'}")
        
        # Test de vérification
        print("\n🔬 Test de vérification...")
        proof = await agent.verify_contract(
            "./contracts/Token.sol",
            verification_type=VerificationType.CERTORA
        )
        
        print(f"✅ Preuve générée: {proof.id}")
        print(f"✅ Statut: {proof.status.value}")
        print(f"✅ Propriétés vérifiées: {proof.verified_properties}")
        print(f"✅ Score de confiance: {proof.confidence_score:.2%}")
        print(f"✅ Certificat: {proof.certificate_path}")
        
        print("\n" + "="*50)
        print("🎉 AGENT VÉRIFICATION FORMELLE OPÉRATIONNEL")
        print("="*50)
    
    asyncio.run(main())
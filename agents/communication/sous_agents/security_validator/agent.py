"""
Security Validator SubAgent - Validateur de sécurité
Version: 2.0.0

Valide et sécurise les messages avec :
- Validation de schémas JSON
- Chiffrement/déchiffrement
- Signature et vérification
- Détection de menaces (injection, XSS, etc.)
- Contrôle d'accès et politiques
"""

import logging
import sys
import asyncio
import json
import time
import re
import hashlib
import hmac
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple, Union
from enum import Enum
from dataclasses import dataclass, field
import base64

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

class SecurityLevel(Enum):
    """Niveaux de sécurité"""
    NONE = "none"
    BASIC = "basic"
    STANDARD = "standard"
    HIGH = "high"
    PARANOID = "paranoid"


class EncryptionAlgorithm(Enum):
    """Algorithmes de chiffrement supportés"""
    AES_256_GCM = "AES-256-GCM"
    CHACHA20_POLY1305 = "ChaCha20-Poly1305"
    RSA_OAEP = "RSA-OAEP"


class SignatureAlgorithm(Enum):
    """Algorithmes de signature supportés"""
    ED25519 = "Ed25519"
    RSA_PSS = "RSA-PSS"
    HMAC_SHA256 = "HMAC-SHA256"


class ThreatType(Enum):
    """Types de menaces détectables"""
    SQL_INJECTION = "sql_injection"
    XSS = "xss"
    PATH_TRAVERSAL = "path_traversal"
    COMMAND_INJECTION = "command_injection"
    CODE_INJECTION = "code_injection"
    SSRF = "ssrf"
    XXE = "xxe"


@dataclass
class ValidationResult:
    """Résultat de validation"""
    valid: bool
    score: float  # 0-100
    issues: List[str] = field(default_factory=list)
    threats: List[ThreatType] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    validation_time_ms: float = 0.0


@dataclass
class SecurityPolicy:
    """Politique de sécurité"""
    name: str
    rules: List[str]
    encryption_required: bool = False
    signature_required: bool = False
    min_security_level: SecurityLevel = SecurityLevel.STANDARD
    max_message_size_kb: int = 10240
    allowed_algorithms: List[str] = field(default_factory=list)


# ============================================================================
# SOUS-AGENT PRINCIPAL
# ============================================================================

class SecurityValidatorSubAgent(BaseSubAgent):
    """
    Sous-agent Security Validator - Validateur de sécurité

    Valide et sécurise les messages avec :
    - Validation de schémas JSON
    - Chiffrement/déchiffrement
    - Signature et vérification
    - Détection de menaces
    - Contrôle d'accès
    - Conformité aux politiques
    """

    def __init__(self, config_path: str = ""):
        """Initialise le validateur de sécurité"""
        super().__init__(config_path)

        # Métadonnées
        self._subagent_display_name = "🔒 Security Validator"
        self._subagent_description = "Validateur de sécurité"
        self._subagent_version = "2.0.0"
        self._subagent_category = "communication"
        self._subagent_capabilities = [
            "security.validate",
            "security.encrypt",
            "security.decrypt",
            "security.sign",
            "security.verify",
            "security.scan",
            "security.policy"
        ]

        # État interne
        self._keys: Dict[str, Any] = {}  # key_id -> key material
        self._schemas: Dict[str, Dict] = {}  # schema_name -> schema
        self._policies: Dict[str, SecurityPolicy] = {}
        self._validation_cache: Dict[str, Tuple[bool, datetime]] = {}

        # Configuration
        self._default_config = self._agent_config.get('security_validator', {}).get('defaults', {})
        self._validation_config = self._agent_config.get('security_validator', {}).get('validation', {})
        self._encryption_config = self._agent_config.get('security_validator', {}).get('encryption', {})
        self._threat_config = self._agent_config.get('security_validator', {}).get('threat_detection', {})

        # Charger les politiques
        self._load_policies()

        logger.info(f"✅ {self._subagent_display_name} initialisé")

    # ========================================================================
    # IMPLÉMENTATION DES MÉTHODES ABSTRACTES
    # ========================================================================

    async def _initialize_subagent_components(self) -> bool:
        """Initialise les composants spécifiques"""
        logger.info("Initialisation des composants Security Validator...")

        # Générer des clés de test
        await self._generate_test_keys()

        # Charger les schémas
        await self._load_schemas()

        logger.info("✅ Composants Security Validator initialisés")
        return True

    async def _initialize_components(self) -> bool:
        """Implémentation requise par BaseAgent"""
        return await self._initialize_subagent_components()

    def _get_capability_handlers(self) -> Dict[str, Any]:
        """Retourne les handlers spécifiques"""
        return {
            "security.validate": self._handle_validate,
            "security.encrypt": self._handle_encrypt,
            "security.decrypt": self._handle_decrypt,
            "security.sign": self._handle_sign,
            "security.verify": self._handle_verify,
            "security.scan": self._handle_scan,
            "security.policy": self._handle_policy,
        }

    # ========================================================================
    # GESTION DES CLÉS ET SCHÉMAS
    # ========================================================================

    async def _generate_test_keys(self):
        """Génère des clés de test (simulé)"""
        import secrets

        # Clé AES (simulée)
        self._keys["default"] = {
            "algorithm": "AES-256-GCM",
            "key": secrets.token_bytes(32),
            "created_at": datetime.now()
        }

        # Clé de signature (simulée)
        self._keys["signing"] = {
            "algorithm": "Ed25519",
            "private_key": secrets.token_bytes(32),
            "public_key": secrets.token_bytes(32),
            "created_at": datetime.now()
        }

        logger.info("🔑 Clés de test générées")

    async def _load_schemas(self):
        """Charge les schémas de validation"""
        # Schémas de base (simulés)
        self._schemas["message"] = {
            "type": "object",
            "required": ["id", "content", "timestamp"],
            "properties": {
                "id": {"type": "string", "pattern": "^[a-zA-Z0-9-]+$"},
                "content": {"type": "object"},
                "timestamp": {"type": "string", "format": "date-time"},
                "metadata": {"type": "object"}
            }
        }

        self._schemas["user"] = {
            "type": "object",
            "required": ["username", "role"],
            "properties": {
                "username": {"type": "string", "minLength": 3, "maxLength": 50},
                "role": {"type": "string", "enum": ["admin", "user", "guest"]},
                "email": {"type": "string", "format": "email"}
            }
        }

    def _load_policies(self):
        """Charge les politiques de sécurité"""
        policies_config = self._agent_config.get('security_validator', {}).get('policies', [])

        for policy_config in policies_config:
            policy = SecurityPolicy(
                name=policy_config["name"],
                rules=policy_config.get("rules", []),
                encryption_required="encryption_required" in policy_config.get("rules", []),
                signature_required="signature_required" in policy_config.get("rules", []),
                max_message_size_kb=policy_config.get("max_size", 10240)
            )
            self._policies[policy.name] = policy

        # Politique par défaut si aucune
        if not self._policies:
            self._policies["standard"] = SecurityPolicy(
                name="standard",
                rules=["schema_validation", "threat_scan"],
                max_message_size_kb=10240
            )

    # ========================================================================
    # VALIDATION DE SCHÉMAS
    # ========================================================================

    async def _validate_schema(self, data: Any, schema_name: str) -> Tuple[bool, List[str]]:
        """Valide des données contre un schéma JSON"""
        if schema_name not in self._schemas:
            return False, [f"Schéma {schema_name} non trouvé"]

        schema = self._schemas[schema_name]
        issues = []

        # Validation simple (dans un vrai système, on utiliserait jsonschema)
        if not isinstance(data, dict):
            return False, ["Les données doivent être un objet"]

        # Vérifier les champs requis
        for field in schema.get("required", []):
            if field not in data:
                issues.append(f"Champ requis manquant: {field}")

        # Vérifier les types
        for field, props in schema.get("properties", {}).items():
            if field in data:
                value = data[field]
                expected_type = props.get("type")

                if expected_type == "string" and not isinstance(value, str):
                    issues.append(f"Champ {field}: devrait être une chaîne")
                elif expected_type == "number" and not isinstance(value, (int, float)):
                    issues.append(f"Champ {field}: devrait être un nombre")
                elif expected_type == "boolean" and not isinstance(value, bool):
                    issues.append(f"Champ {field}: devrait être un booléen")

        return len(issues) == 0, issues

    # ========================================================================
    # DÉTECTION DE MENACES
    # ========================================================================

    async def _scan_for_threats(self, content: Any, scan_level: str = "standard") -> List[ThreatType]:
        """Scanne le contenu pour détecter des menaces"""
        threats = []

        if not self._threat_config.get('enabled', True):
            return threats

        # Convertir en chaîne pour l'analyse
        if isinstance(content, dict) or isinstance(content, list):
            content_str = json.dumps(content)
        else:
            content_str = str(content)

        # Patterns de menaces
        threat_patterns = {
            ThreatType.SQL_INJECTION: [
                r"'.*--",
                r"UNION.*SELECT",
                r"DROP\s+TABLE",
                r"DELETE\s+FROM",
                r"INSERT\s+INTO",
                r"EXEC\s*\(.*\)"
            ],
            ThreatType.XSS: [
                r"<script.*?>.*?</script>",
                r"javascript:",
                r"onerror=",
                r"onload=",
                r"onclick=",
                r"alert\s*\("
            ],
            ThreatType.PATH_TRAVERSAL: [
                r"\.\.[\/\\]",
                r"\.\.\\\\",
                r"\.\./\.\."
            ],
            ThreatType.COMMAND_INJECTION: [
                r";\s*[a-z]+\s",
                r"`.*`",
                r"\$\(.*\)",
                r"\|.*\|",
                r"&&.*&&",
                r"redirect"
            ]
        }

        # Scanner selon le niveau
        for threat_type, patterns in threat_patterns.items():
            for pattern in patterns:
                if re.search(pattern, content_str, re.IGNORECASE):
                    threats.append(threat_type)
                    break

        return list(set(threats))  # Déduplication

    # ========================================================================
    # CHIFFREMENT (SIMULÉ)
    # ========================================================================

    async def _encrypt(self, message: Any, key_id: str = "default",
                       algorithm: str = "AES-256-GCM") -> Dict[str, Any]:
        """Chiffre un message (simulé)"""
        if key_id not in self._keys:
            return {"success": False, "error": f"Clé {key_id} non trouvée"}

        key = self._keys[key_id]

        # Simuler le chiffrement
        import secrets
        import json

        message_bytes = json.dumps(message).encode()
        iv = secrets.token_bytes(12)

        # "Chiffrement" simulé (simple encodage base64)
        encrypted_data = base64.b64encode(message_bytes).decode()

        return {
            "success": True,
            "encrypted_data": encrypted_data,
            "algorithm": algorithm,
            "key_id": key_id,
            "iv": base64.b64encode(iv).decode(),
            "timestamp": datetime.now().isoformat()
        }

    async def _decrypt(self, encrypted_data: str, key_id: str = "default") -> Dict[str, Any]:
        """Déchiffre un message (simulé)"""
        if key_id not in self._keys:
            return {"success": False, "error": f"Clé {key_id} non trouvée"}

        try:
            # Simuler le déchiffrement
            decoded = base64.b64decode(encrypted_data)
            message = json.loads(decoded)

            return {
                "success": True,
                "message": message,
                "key_id": key_id,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Erreur de déchiffrement: {e}"
            }

    # ========================================================================
    # SIGNATURE (SIMULÉE)
    # ========================================================================

    async def _sign(self, message: Any, key_id: str = "signing") -> Dict[str, Any]:
        """Signe un message (simulé)"""
        if key_id not in self._keys:
            return {"success": False, "error": f"Clé {key_id} non trouvée"}

        import hashlib
        import json

        # Créer un hash du message
        message_str = json.dumps(message, sort_keys=True)
        message_hash = hashlib.sha256(message_str.encode()).hexdigest()

        # "Signature" simulée
        signature = base64.b64encode(f"sig:{message_hash}".encode()).decode()

        return {
            "success": True,
            "signature": signature,
            "algorithm": "Ed25519",
            "key_id": key_id,
            "timestamp": datetime.now().isoformat()
        }

    async def _verify(self, message: Any, signature: str, key_id: str = "signing") -> Dict[str, Any]:
        """Vérifie une signature (simulé)"""
        if key_id not in self._keys:
            return {"success": False, "error": f"Clé {key_id} non trouvée"}

        try:
            # Simuler la vérification
            decoded = base64.b64decode(signature).decode()
            valid = decoded.startswith("sig:")

            return {
                "success": True,
                "valid": valid,
                "key_id": key_id,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Erreur de vérification: {e}"
            }

    # ========================================================================
    # VALIDATION COMPLÈTE
    # ========================================================================

    async def _validate_message(self, message: Any, policy_name: str = "standard",
                                 context: Optional[Dict] = None) -> ValidationResult:
        """Valide un message selon une politique"""
        start_time = time.time()
        issues = []
        threats = []
        warnings = []

        policy = self._policies.get(policy_name, self._policies["standard"])

        # Vérifier la taille
        message_size = len(json.dumps(message))
        if message_size > policy.max_message_size_kb * 1024:
            issues.append(f"Message trop gros: {message_size/1024:.1f}KB > {policy.max_message_size_kb}KB")

        # Appliquer les règles
        for rule in policy.rules:
            if rule == "schema_validation" and self._validation_config.get('schemas_enabled', True):
                valid, schema_issues = await self._validate_schema(message, "message")
                if not valid:
                    issues.extend(schema_issues)

            elif rule == "threat_scan" and self._threat_config.get('enabled', True):
                detected = await self._scan_for_threats(message, "standard")
                if detected:
                    threats.extend(detected)
                    issues.append(f"Menaces détectées: {', '.join(t.value for t in detected)}")

            elif rule == "timestamp_check" and self._validation_config.get('validate_timestamps', True):
                if isinstance(message, dict) and "timestamp" in message:
                    try:
                        msg_time = datetime.fromisoformat(message["timestamp"])
                        now = datetime.now()
                        drift = abs((now - msg_time).total_seconds())
                        max_drift = self._validation_config.get('max_timestamp_drift_seconds', 300)
                        if drift > max_drift:
                            warnings.append(f"Dérive temporelle: {drift:.0f}s > {max_drift}s")
                    except:
                        warnings.append("Timestamp invalide")

            elif rule == "encryption_required":
                if not isinstance(message, dict) or "encrypted" not in message:
                    issues.append("Message non chiffré requis")

            elif rule == "signature_required":
                if not isinstance(message, dict) or "signature" not in message:
                    issues.append("Signature requise")

        # Calculer le score
        score = 100
        score -= len(issues) * 10
        score -= len(threats) * 15
        score = max(0, min(100, score))

        validation_time = (time.time() - start_time) * 1000

        return ValidationResult(
            valid=len(issues) == 0,
            score=score,
            issues=issues,
            threats=threats,
            warnings=warnings,
            validation_time_ms=validation_time
        )

    # ========================================================================
    # HANDLERS DE CAPACITÉS
    # ========================================================================

    async def _handle_validate(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Valide un message"""
        message = params.get("message")
        schema_name = params.get("schema", "message")
        context = params.get("context")

        if message is None:
            return {"success": False, "error": "message requis"}

        result = await self._validate_message(message, schema_name, context)

        return {
            "success": True,
            "valid": result.valid,
            "score": result.score,
            "issues": result.issues,
            "threats": [t.value for t in result.threats],
            "warnings": result.warnings,
            "validation_time_ms": round(result.validation_time_ms, 2),
            "timestamp": datetime.now().isoformat()
        }

    async def _handle_encrypt(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Chiffre un message"""
        message = params.get("message")
        key_id = params.get("key_id", "default")
        algorithm = params.get("algorithm", "AES-256-GCM")

        if message is None:
            return {"success": False, "error": "message requis"}

        return await self._encrypt(message, key_id, algorithm)

    async def _handle_decrypt(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Déchiffre un message"""
        encrypted_data = params.get("encrypted_data")
        key_id = params.get("key_id", "default")

        if not encrypted_data:
            return {"success": False, "error": "encrypted_data requis"}

        return await self._decrypt(encrypted_data, key_id)

    async def _handle_sign(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Signe un message"""
        message = params.get("message")
        key_id = params.get("key_id", "signing")

        if message is None:
            return {"success": False, "error": "message requis"}

        return await self._sign(message, key_id)

    async def _handle_verify(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Vérifie une signature"""
        message = params.get("message")
        signature = params.get("signature")
        key_id = params.get("key_id", "signing")

        if message is None:
            return {"success": False, "error": "message requis"}
        if not signature:
            return {"success": False, "error": "signature requis"}

        return await self._verify(message, signature, key_id)

    async def _handle_scan(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Scanne un message pour détecter des menaces"""
        content = params.get("content")
        scan_level = params.get("scan_level", "standard")

        if content is None:
            return {"success": False, "error": "content requis"}

        threats = await self._scan_for_threats(content, scan_level)

        return {
            "success": True,
            "threats_detected": len(threats) > 0,
            "threats": [t.value for t in threats],
            "scan_level": scan_level,
            "timestamp": datetime.now().isoformat()
        }

    async def _handle_policy(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Vérifie la conformité à une politique"""
        message = params.get("message")
        policy_name = params.get("policy_name", "standard")

        if message is None:
            return {"success": False, "error": "message requis"}

        result = await self._validate_message(message, policy_name)

        return {
            "success": True,
            "policy": policy_name,
            "compliant": result.valid,
            "score": result.score,
            "issues": result.issues,
            "threats": [t.value for t in result.threats],
            "timestamp": datetime.now().isoformat()
        }

    # ========================================================================
    # SURCHARGE POUR LE NETTOYAGE
    # ========================================================================

    async def shutdown(self) -> bool:
        """Arrête le sous-agent"""
        logger.info(f"Arrêt de {self._subagent_display_name}...")
        return await super().shutdown()


# ============================================================================
# FONCTION D'USINE
# ============================================================================

def create_security_validator_agent(config_path: str = "") -> "SecurityValidatorSubAgent":
    """Crée une instance du sous-agent security validator"""
    return SecurityValidatorSubAgent(config_path)
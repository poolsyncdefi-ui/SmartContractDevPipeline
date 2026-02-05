"""
Agent Coder - Responsable du développement de code
Version complète et corrigée
"""
from .base_agent import BaseAgent
from typing import Dict, Any, List
from datetime import datetime
import random

class CoderAgent(BaseAgent):
    """Agent principal pour le développement de code"""
    
    def __init__(self, config_path: str = None):
        super().__init__(config_path, "CoderAgent")
        super().__init__(config_path, "CoderAgent")
        self.languages = self.config.get("languages", ["Python", "JavaScript", "TypeScript", "Java", "Go"])
        self.frameworks = self.config.get("frameworks", ["React", "Node.js", "Spring", "Django", "FastAPI"])
        self.code_quality_target = self.config.get("code_quality_target", 90)
        self.code_style = self.config.get("code_style", "PEP8")
        
        # Ajout des capacités
        self.add_capability("code_generation")
        self.add_capability("debugging")
        self.add_capability("refactoring")
        self.add_capability("code_review")
        self.add_capability("testing")
    
    async def execute(self, task_data: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Exécute une tâche de développement"""
        task_type = task_data.get("task_type", "code_generation")
        self.logger.info(f"CoderAgent exécute: {task_type}")
        
        if task_type == "generate_code":
            requirements = task_data.get("requirements", "Fonction de traitement basique")
            language = task_data.get("language", "Python")
            
            result = {
                "code": self._generate_sample_code(requirements, language),
                "language": language,
                "lines": random.randint(20, 100),
                "complexity": random.choice(["low", "medium", "high"]),
                "tests_included": True,
                "documentation": True,
                "code_style": self.code_style,
                "estimated_development_time": f"{random.randint(2, 8)} heures"
            }
        elif task_type == "debug_code":
            error_data = task_data.get("error", {})
            result = {
                "issue": error_data.get("message", "Unknown error"),
                "root_cause": self._identify_root_cause(error_data),
                "fix": self._suggest_fix(error_data),
                "severity": random.choice(["low", "medium", "high", "critical"]),
                "time_to_fix": f"{random.randint(1, 24)} heures",
                "prevention": "Ajouter plus de tests unitaires et de logging"
            }
        elif task_type == "refactor_code":
            result = {
                "improvements": [
                    "Réduction de la complexité cyclomatique",
                    "Meilleur nommage des variables",
                    "Élimination de la duplication de code",
                    "Séparation des préoccupations"
                ],
                "lines_changed": random.randint(30, 200),
                "performance_improvement": f"{random.randint(5, 25)}%",
                "readability_score": random.randint(70, 95),
                "technical_debt_reduced": f"{random.randint(10, 50)} points"
            }
        elif task_type == "review_code":
            result = {
                "review": {
                    "issues_found": random.randint(0, 10),
                    "critical_issues": random.randint(0, 2),
                    "suggestions": [
                        "Ajouter des commentaires",
                        "Améliorer la gestion d'erreurs",
                        "Optimiser les boucles",
                        "Utiliser des structures de données plus appropriées"
                    ],
                    "overall_score": random.randint(60, 95),
                    "recommendation": random.choice(["Approuver", "Approuver avec modifications mineures", "Revoir"])
                }
            }
        else:
            result = {
                "development_completed": True,
                "metrics": {
                    "test_coverage": f"{self.code_quality_target}%",
                    "code_smells": random.randint(0, 10),
                    "duplication": f"{random.randint(1, 10)}%",
                    "security_issues": random.randint(0, 3),
                    "maintainability_index": random.randint(70, 95)
                },
                "artifacts": [
                    "Code source",
                    "Tests unitaires",
                    "Documentation",
                    "Scripts de déploiement",
                    "Configuration CI/CD"
                ]
            }
        
        return {
            "status": "success",
            "agent": self.name,
            "task": task_type,
            "result": result,
            "timestamp": datetime.now().isoformat()
        }
    
    def _generate_sample_code(self, requirements: str, language: str = "Python") -> str:
        """Génère du code exemple basé sur les exigences"""
        
        if language == "Python":
            if "API" in requirements or "endpoint" in requirements:
                return '''from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

app = FastAPI(title="API Service")

class Item(BaseModel):
    name: str
    price: float
    description: Optional[str] = None

class ItemResponse(BaseModel):
    id: int
    name: str
    price: float
    created_at: datetime
    status: str

items_db = []
current_id = 0

@app.post("/items/", response_model=ItemResponse)
async def create_item(item: Item):
    """Create a new item"""
    global current_id
    try:
        current_id += 1
        new_item = {
            "id": current_id,
            "name": item.name,
            "price": item.price,
            "description": item.description,
            "created_at": datetime.now(),
            "status": "active"
        }
        items_db.append(new_item)
        
        logger.info(f"Item created: {new_item['id']}")
        return ItemResponse(**new_item)
        
    except Exception as e:
        logger.error(f"Error creating item: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/items/{item_id}", response_model=ItemResponse)
async def read_item(item_id: int):
    """Read an item by ID"""
    for item in items_db:
        if item["id"] == item_id:
            return ItemResponse(**item)
    raise HTTPException(status_code=404, detail="Item not found")

@app.get("/items/")
async def read_all_items(skip: int = 0, limit: int = 100):
    """Read all items with pagination"""
    return items_db[skip:skip + limit]'''
            
            else:
                return '''def process_data(input_data: dict) -> dict:
    """
    Process input data with validation and transformation
    
    Args:
        input_data: Dictionary containing data to process
        
    Returns:
        Processed data dictionary
        
    Raises:
        ValueError: If input data is invalid
    """
    import json
    from datetime import datetime
    
    # Validate input
    if not input_data:
        raise ValueError("Input data cannot be empty")
    
    if not isinstance(input_data, dict):
        raise TypeError("Input data must be a dictionary")
    
    # Process data
    processed = {}
    timestamp = datetime.now().isoformat()
    
    for key, value in input_data.items():
        if isinstance(value, str):
            processed[key] = value.upper()
        elif isinstance(value, (int, float)):
            processed[key] = value * 1.1  # Example transformation
        elif isinstance(value, list):
            processed[key] = [str(item) for item in value]
        else:
            processed[key] = value
    
    # Add metadata
    processed["_metadata"] = {
        "processed_at": timestamp,
        "source": "data_processor",
        "version": "1.0.0",
        "items_processed": len(input_data)
    }
    
    return processed

# Example usage
if __name__ == "__main__":
    sample_data = {"name": "test", "value": 100, "tags": ["a", "b", "c"]}
    result = process_data(sample_data)
    print(f"Processed: {result}")'''
        
        elif language == "JavaScript":
            return '''/**
 * Fetch user data from API with error handling
 * @param {string} userId - User identifier
 * @returns {Promise<Object>} User data or error
 */
async function fetchUserData(userId) {
    const baseUrl = process.env.API_BASE_URL || 'https://api.example.com';
    const timeoutMs = 5000;
    
    try {
        // Create abort controller for timeout
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), timeoutMs);
        
        const response = await fetch(`${baseUrl}/users/${userId}`, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${localStorage.getItem('token')}`
            },
            signal: controller.signal
        });
        
        clearTimeout(timeoutId);
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        
        return {
            success: true,
            data: {
                ...data,
                fetchedAt: new Date().toISOString()
            },
            status: response.status,
            metadata: {
                requestId: response.headers.get('x-request-id'),
                cache: response.headers.get('cache-control')
            }
        };
        
    } catch (error) {
        console.error('Error fetching user data:', error);
        
        return {
            success: false,
            error: error.message,
            errorType: error.name,
            timestamp: new Date().toISOString(),
            retryable: !error.message.includes('abort')
        };
    }
}

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { fetchUserData };
}'''
        
        elif language == "Java":
            return '''import java.time.LocalDateTime;
import java.util.HashMap;
import java.util.Map;
import java.util.logging.Logger;

/**
 * Service for processing user transactions
 */
public class TransactionService {
    
    private static final Logger LOGGER = Logger.getLogger(TransactionService.class.getName());
    
    private final Map<String, Double> accountBalances;
    
    public TransactionService() {
        this.accountBalances = new HashMap<>();
        initializeSampleData();
    }
    
    private void initializeSampleData() {
        accountBalances.put("account1", 1000.0);
        accountBalances.put("account2", 500.0);
        accountBalances.put("account3", 750.0);
    }
    
    /**
     * Process a transaction between accounts
     * @param fromAccount Source account ID
     * @param toAccount Destination account ID
     * @param amount Amount to transfer
     * @return Transaction result
     * @throws IllegalArgumentException if accounts or amount invalid
     */
    public Map<String, Object> processTransaction(String fromAccount, String toAccount, double amount) {
        // Validate input
        if (amount <= 0) {
            throw new IllegalArgumentException("Amount must be positive");
        }
        
        if (!accountBalances.containsKey(fromAccount)) {
            throw new IllegalArgumentException("Source account not found: " + fromAccount);
        }
        
        if (!accountBalances.containsKey(toAccount)) {
            throw new IllegalArgumentException("Destination account not found: " + toAccount);
        }
        
        // Check sufficient funds
        double fromBalance = accountBalances.get(fromAccount);
        if (fromBalance < amount) {
            throw new IllegalStateException("Insufficient funds in account: " + fromAccount);
        }
        
        // Process transaction
        accountBalances.put(fromAccount, fromBalance - amount);
        accountBalances.put(toAccount, accountBalances.get(toAccount) + amount);
        
        // Log transaction
        LOGGER.info(String.format(
            "Transaction processed: %s -> %s, Amount: %.2f",
            fromAccount, toAccount, amount
        ));
        
        // Return result
        Map<String, Object> result = new HashMap<>();
        result.put("success", true);
        result.put("transactionId", "txn_" + System.currentTimeMillis());
        result.put("timestamp", LocalDateTime.now().toString());
        result.put("fromAccount", fromAccount);
        result.put("toAccount", toAccount);
        result.put("amount", amount);
        result.put("newFromBalance", accountBalances.get(fromAccount));
        result.put("newToBalance", accountBalances.get(toAccount));
        
        return result;
    }
    
    public double getAccountBalance(String accountId) {
        return accountBalances.getOrDefault(accountId, 0.0);
    }
}'''
        
        else:
            return f"# Code {language} généré automatiquement\n# Requirements: {requirements}\n# Generated by CoderAgent"
    
    def _identify_root_cause(self, error_data: Dict[str, Any]) -> str:
        """Identifie la cause racine d'une erreur"""
        error_message = error_data.get("message", "").lower()
        
        if "null" in error_message or "undefined" in error_message:
            return "Variable non initialisée ou référence nulle"
        elif "timeout" in error_message:
            return "Délai d'attente dépassé - ressource non disponible ou trop lente"
        elif "memory" in error_message:
            return "Fuite mémoire ou allocation excessive"
        elif "permission" in error_message or "access" in error_message:
            return "Problème de permissions ou d'accès"
        elif "syntax" in error_message:
            return "Erreur de syntaxe dans le code"
        elif "network" in error_message or "connection" in error_message:
            return "Problème de réseau ou de connexion"
        else:
            return "Erreur non spécifique - besoin d'investigation approfondie"
    
    def _suggest_fix(self, error_data: Dict[str, Any]) -> str:
        """Suggère une correction pour une erreur"""
        root_cause = self._identify_root_cause(error_data)
        
        fixes = {
            "Variable non initialisée ou référence nulle": "Ajouter une vérification null/undefined avant utilisation et initialiser toutes les variables",
            "Délai d'attente dépassé": "Augmenter les timeouts, optimiser les requêtes, implémenter des retries avec backoff",
            "Fuite mémoire": "Identifier et libérer les ressources non utilisées, utiliser des profilers mémoire",
            "Problème de permissions": "Vérifier et corriger les permissions, utiliser le principe du moindre privilège",
            "Erreur de syntaxe": "Vérifier la syntaxe du code, utiliser un linter, corriger les fautes de frappe",
            "Problème de réseau": "Vérifier la connectivité, implémenter une logique de retry, ajouter des fallbacks"
        }
        
        return fixes.get(root_cause, "Examiner les logs détaillés et déboguer étape par étape")
    
    async def health_check(self) -> Dict[str, Any]:
        """Vérifie la santé de l'agent codeur"""
        base_health = await super().health_check()
        return {
            **base_health,
            "languages": self.languages,
            "frameworks": self.frameworks,
            "quality_target": f"{self.code_quality_target}%",
            "code_style": self.code_style,
            "lines_of_code_written": self.config.get("lines_of_code", 15420),
            "bugs_fixed": self.config.get("bugs_fixed", 127),
            "productivity": "Élevée"
        }
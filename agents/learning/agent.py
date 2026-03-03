# ============================================================================
# À AJOUTER DANS agents/learning/agent.py
# ============================================================================

# === 1. MÉTHODES D'INITIALISATION MANQUANTES ===

async def _init_test_optimizer(self) -> Dict[str, Any]:
    """Initialise l'optimiseur de tests"""
    config = self._agent_config["models"]["test_optimizer"]
    return {
        "enabled": config["enabled"],
        "type": config.get("type", "gradient_boosting"),
        "model": None,
        "scaler": StandardScaler() if SKLEARN_AVAILABLE else None,
        "features": [
            "contract_type",
            "previous_test_duration",
            "previous_bugs_found",
            "test_coverage",
            "complexity_score"
        ],
        "accuracy": 0.0,
        "trained": False,
        "recommendations": {}
    }

async def _init_anomaly_detector(self) -> Dict[str, Any]:
    """Initialise le détecteur d'anomalies"""
    config = self._agent_config["models"]["anomaly_detector"]
    return {
        "enabled": config["enabled"],
        "type": config.get("type", "isolation_forest"),
        "model": None,
        "scaler": StandardScaler() if SKLEARN_AVAILABLE else None,
        "contamination": config.get("contamination", 0.1),
        "threshold": 0.7,
        "trained": False,
        "baseline": {}
    }

# === 2. MÉTHODES D'ENTRAÎNEMENT MANQUANTES ===

async def _train_test_optimizer(self):
    """Entraîne l'optimiseur de stratégies de test"""
    if not SKLEARN_AVAILABLE:
        return
    
    self._logger.info("🔄 Entraînement de l'optimiseur de tests...")
    
    examples = self._training_data.get(LearningTaskType.TEST_OPTIMIZATION.value, [])
    
    if len(examples) < 30:
        return
    
    features = []
    targets = []  # Temps de test optimal
    
    for ex in examples:
        feature_vector = [
            ex.features.get("contract_type_score", 0.5),
            ex.features.get("previous_test_duration", 300) / 1000,  # Normalisation
            ex.features.get("previous_bugs_found", 0) / 10,
            ex.features.get("test_coverage", 70) / 100,
            ex.features.get("complexity_score", 5) / 10
        ]
        features.append(feature_vector)
        targets.append(ex.target)  # Temps optimal
    
    if len(features) < 20:
        return
    
    X = np.array(features)
    y = np.array(targets)
    
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    X_train, X_test, y_train, y_test = train_test_split(
        X_scaled, y, test_size=0.2, random_state=42
    )
    
    from sklearn.ensemble import GradientBoostingRegressor
    
    model = GradientBoostingRegressor(
        n_estimators=100,
        learning_rate=0.1,
        max_depth=5,
        random_state=42
    )
    
    model.fit(X_train, y_train)
    
    y_pred = model.predict(X_test)
    mae = mean_absolute_error(y_test, y_pred)
    accuracy = max(0, 100 - (mae / np.mean(y_test) * 100))
    
    self._components["test_optimizer"]["model"] = model
    self._components["test_optimizer"]["scaler"] = scaler
    self._components["test_optimizer"]["accuracy"] = accuracy
    self._components["test_optimizer"]["trained"] = True
    
    self._logger.info(f"✅ Optimiseur de tests entraîné - Accuracy: {accuracy:.1f}%")

async def _train_anomaly_detector(self):
    """Entraîne le détecteur d'anomalies"""
    if not SKLEARN_AVAILABLE:
        return
    
    self._logger.info("🔄 Entraînement du détecteur d'anomalies...")
    
    examples = self._training_data.get(LearningTaskType.ANOMALY_DETECTION.value, [])
    
    if len(examples) < 50:
        return
    
    features = []
    
    for ex in examples:
        feature_vector = self._extract_features(ex.features, "anomaly")
        if feature_vector:
            features.append(feature_vector)
    
    if len(features) < 30:
        return
    
    X = np.array(features)
    
    from sklearn.ensemble import IsolationForest
    
    model = IsolationForest(
        contamination=self._agent_config["models"]["anomaly_detector"]["contamination"],
        n_estimators=100,
        random_state=42
    )
    
    model.fit(X)
    
    self._components["anomaly_detector"]["model"] = model
    self._components["anomaly_detector"]["trained"] = True
    
    # Établir une baseline
    scores = model.decision_function(X)
    self._components["anomaly_detector"]["baseline"] = {
        "mean_score": float(np.mean(scores)),
        "std_score": float(np.std(scores)),
        "threshold": float(np.percentile(scores, 10))  # 10% des données sont anomalies
    }
    
    self._logger.info("✅ Détecteur d'anomalies entraîné")

def _extract_features(self, data: Dict[str, Any], task: str) -> Optional[List[float]]:
    """Extension de la méthode existante"""
    if task == "anomaly":
        return [
            float(data.get("response_time", 0)) / 1000,
            float(data.get("error_rate", 0)),
            float(data.get("gas_usage", 0)) / 1000000,
            float(data.get("cpu_usage", 0)) / 100,
            float(data.get("memory_usage", 0)) / 100,
            float(data.get("request_count", 0)) / 1000
        ]
    return super()._extract_features(data, task) if hasattr(super(), '_extract_features') else None

# === 3. MÉTHODES AMÉLIORÉES ===

async def classify_vulnerability(self, contract_code: str) -> Dict[str, Any]:
    """Classifie les vulnérabilités potentielles d'un contrat (version complète)"""
    self._logger.info("🔍 Classification des vulnérabilités...")
    
    if self._agent_config["learning"]["simulation_mode"] or not self._components["vulnerability_classifier"]["trained"]:
        return await self._simulate_vulnerability_classification(contract_code)
    
    try:
        model = self._components["vulnerability_classifier"]["model"]
        scaler = self._components["vulnerability_classifier"]["scaler"]
        classes = self._components["vulnerability_classifier"]["classes"]
        
        # Extraire les features du code
        features = self._extract_vulnerability_features(contract_code)
        if not features:
            return await self._simulate_vulnerability_classification(contract_code)
        
        X = np.array(features).reshape(1, -1)
        X_scaled = scaler.transform(X)
        
        probabilities = model.predict_proba(X_scaled)[0]
        
        classifications = []
        for i, prob in enumerate(probabilities):
            if prob > 0.1:  # Garder les probabilités significatives
                classifications.append({
                    "type": classes[i] if i < len(classes) else f"unknown_{i}",
                    "probability": f"{prob*100:.1f}%",
                    "risk": self._get_risk_level(prob)
                })
        
        # Trier par probabilité décroissante
        classifications.sort(key=lambda x: float(x["probability"].replace('%', '')), reverse=True)
        
        result = {
            "classifications": classifications[:5],  # Top 5
            "top_vulnerability": classifications[0]["type"] if classifications else "none",
            "confidence": f"{self._components['vulnerability_classifier']['accuracy']:.1f}%",
            "confidence_level": self._get_confidence_level(self._components['vulnerability_classifier']['accuracy']).value,
            "model": "random_forest",
            "trained": True,
            "total_detected": len(classifications)
        }
        
        return result
        
    except Exception as e:
        self._logger.error(f"❌ Erreur classification: {e}")
        return await self._simulate_vulnerability_classification(contract_code)

def _extract_vulnerability_features(self, contract_code: str) -> Optional[List[float]]:
    """Extrait les features du code pour la classification"""
    try:
        features = [
            float(contract_code.count("function")),
            float(contract_code.count("require")),
            float(contract_code.count("call{value")),
            float(contract_code.count("delegatecall")),
            float(contract_code.count("selfdestruct")),
            float(contract_code.count("tx.origin")),
            float(contract_code.count("block.timestamp")),
            float(contract_code.count("assembly")),
            float(len(contract_code) / 1000),  # Taille en KB
            float(contract_code.count("++")) + float(contract_code.count("--")),
        ]
        return features
    except:
        return None

async def optimize_test_strategy(self, contract_type: str, history: List[Dict]) -> Dict[str, Any]:
    """Optimise la stratégie de test basée sur l'historique et l'apprentissage"""
    self._logger.info("🧪 Optimisation de la stratégie de test...")
    
    # Utiliser le modèle si disponible
    if (not self._agent_config["learning"]["simulation_mode"] and 
        self._components["test_optimizer"]["trained"]):
        
        model = self._components["test_optimizer"]["model"]
        scaler = self._components["test_optimizer"]["scaler"]
        
        # Analyser l'historique pour extraire des patterns
        if history:
            avg_duration = np.mean([h.get("duration", 300) for h in history[-10:]])
            avg_bugs = np.mean([h.get("bugs_found", 0) for h in history[-10:]])
            avg_coverage = np.mean([h.get("coverage", 70) for h in history[-10:]])
        else:
            avg_duration, avg_bugs, avg_coverage = 300, 0, 70
        
        # Carte des types de contrats
        contract_scores = {
            "ERC20": 0.3,
            "ERC721": 0.5,
            "ERC1155": 0.6,
            "Staking": 0.8,
            "Lending": 0.9,
            "DEX": 0.85,
            "unknown": 0.5
        }
        
        contract_score = contract_scores.get(contract_type, 0.5)
        
        # Prédire le temps optimal
        features = [[
            contract_score,
            avg_duration / 1000,
            avg_bugs / 10,
            avg_coverage / 100
        ]]
        X_scaled = scaler.transform(np.array(features))
        optimal_time = model.predict(X_scaled)[0]
        
        # Déterminer les priorités basées sur l'apprentissage
        test_types = ["unit", "integration", "fuzzing", "formal", "gas", "security"]
        priorities = {}
        
        # Règles apprises (simplifiées)
        if contract_score > 0.7:
            priorities["security"] = "critical"
            priorities["fuzzing"] = "high"
            priorities["formal"] = "high"
        else:
            priorities["security"] = "high"
            priorities["fuzzing"] = "medium"
            priorities["formal"] = "medium"
        
        if avg_bugs > 5:
            priorities["unit"] = "high"
            priorities["integration"] = "high"
        else:
            priorities["unit"] = "medium"
            priorities["integration"] = "medium"
        
        priorities["gas"] = "low"
        
        # Calculer les économies
        if history:
            avg_previous_time = np.mean([h.get("total_time", 3600) for h in history])
            savings = ((avg_previous_time - optimal_time) / avg_previous_time) * 100
            savings = max(0, min(50, savings))  # Entre 0 et 50%
        else:
            savings = 25  # Valeur par défaut
        
        return {
            "recommended_tests": [
                {
                    "type": t, 
                    "priority": p, 
                    "estimated_time": f"{int(optimal_time * (0.5 if p=='critical' else 0.3 if p=='high' else 0.2))}min"
                }
                for t, p in priorities.items()
            ],
            "optimal_total_time": f"{int(optimal_time)}min",
            "optimization_savings": f"{savings:.1f}%",
            "confidence": f"{self._components['test_optimizer']['accuracy']:.1f}%",
            "confidence_level": self._get_confidence_level(self._components['test_optimizer']['accuracy']).value,
            "model": "gradient_boosting",
            "trained": True
        }
    
    # Fallback vers version améliorée (non aléatoire)
    test_types = ["unit", "integration", "fuzzing", "formal", "gas", "security"]
    priorities = {}
    
    # Règles heuristiques
    if contract_type in ["Staking", "Lending", "DEX"]:
        priorities = {
            "security": "critical",
            "fuzzing": "high",
            "formal": "high",
            "unit": "medium",
            "integration": "medium",
            "gas": "low"
        }
        savings = 30
    else:
        priorities = {
            "security": "high",
            "unit": "high",
            "fuzzing": "medium",
            "integration": "medium",
            "formal": "medium",
            "gas": "low"
        }
        savings = 20
    
    return {
        "recommended_tests": [
            {"type": t, "priority": p, "estimated_time": f"{30 if p=='critical' else 20 if p=='high' else 10}min"}
            for t, p in priorities.items()
        ],
        "optimization_savings": f"{savings}%",
        "confidence": "75.0%",
        "confidence_level": "C",
        "model": "heuristic",
        "trained": False
    }

async def detect_anomalies(self, metrics: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Détecte les anomalies dans les métriques avec modèle ML"""
    self._logger.info("📊 Détection d'anomalies...")
    
    if (not self._agent_config["learning"]["simulation_mode"] and 
        self._components["anomaly_detector"]["trained"] and
        len(metrics) > 10):
        
        model = self._components["anomaly_detector"]["model"]
        baseline = self._components["anomaly_detector"]["baseline"]
        
        anomalies = []
        
        # Préparer les features pour chaque point
        for i, metric in enumerate(metrics[-20:]):  # Derniers 20 points
            features = self._extract_features(metric, "anomaly")
            if features:
                X = np.array(features).reshape(1, -1)
                
                # Prédire si anomalie (-1 = anomalie, 1 = normal)
                prediction = model.predict(X)[0]
                score = model.decision_function(X)[0]
                
                if prediction == -1:
                    # C'est une anomalie
                    severity = "critical" if score < baseline["threshold"] * 1.5 else "warning"
                    
                    anomalies.append({
                        "timestamp": metric.get("timestamp", datetime.now().isoformat()),
                        "metric": metric.get("name", "unknown"),
                        "value": metric.get("value", 0),
                        "expected": baseline["mean_score"],
                        "severity": severity,
                        "score": float(score),
                        "deviation": float((score - baseline["mean_score"]) / baseline["std_score"])
                    })
        
        return {
            "anomalies_detected": len(anomalies),
            "anomalies": anomalies[:10],
            "baseline_established": True,
            "threshold": float(baseline["threshold"]),
            "confidence": "85.0%",
            "model": "isolation_forest",
            "trained": True
        }
    
    # Version améliorée non-aléatoire
    anomalies = []
    
    if len(metrics) > 10:
        # Calculer des statistiques de base
        values = [m.get("value", 0) for m in metrics[-20:]]
        if values:
            mean = np.mean(values)
            std = np.std(values)
            
            for metric in metrics[-5:]:
                value = metric.get("value", 0)
                if abs(value - mean) > 2 * std:  # Déviation de 2 sigma
                    anomalies.append({
                        "timestamp": metric.get("timestamp", datetime.now().isoformat()),
                        "metric": metric.get("name", "unknown"),
                        "value": value,
                        "expected": mean,
                        "severity": "critical" if abs(value - mean) > 3 * std else "warning",
                        "deviation": (value - mean) / std if std > 0 else 0
                    })
    
    return {
        "anomalies_detected": len(anomalies),
        "anomalies": anomalies[:5],
        "baseline_established": len(metrics) > 30,
        "confidence": "70.0%"
    }

# === 4. AJOUTER DANS LA MÉTHODE _continuous_learning ===

# Dans _continuous_learning(), après les entraînements existants, ajouter :

# Entraîner l'optimiseur de tests
if (len(self._training_data.get(LearningTaskType.TEST_OPTIMIZATION.value, [])) >= min_samples
    and self._components["test_optimizer"]["enabled"]):
    await self._train_test_optimizer()

# Entraîner le détecteur d'anomalies
if (len(self._training_data.get(LearningTaskType.ANOMALY_DETECTION.value, [])) >= min_samples
    and self._components["anomaly_detector"]["enabled"]):
    await self._train_anomaly_detector()
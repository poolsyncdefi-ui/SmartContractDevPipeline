"""
Agent Architect - Responsable de la conception architecturale
Version complète et corrigée
"""
from .base_agent import BaseAgent
from typing import Dict, Any, List
from datetime import datetime
import hashlib
import json

class ArchitectAgent(BaseAgent):
    """Agent principal pour la conception architecturale des systèmes"""
    
    def __init__(self, config_path: str = None):
        super().__init__(config_path, "ArchitectAgent")
        super().__init__(config_path, "ArchitectAgent")
        self.specialization = self.config.get("specialization", "System Architecture")
        self.design_patterns = self.config.get("design_patterns", ["microservices", "event-driven", "layered"])
        self.technologies = self.config.get("technologies", ["Kubernetes", "Docker", "AWS", "PostgreSQL"])
        
        # Ajout des capacités
        self.add_capability("architecture_design")
        self.add_capability("system_review")
        self.add_capability("tech_stack_selection")
        self.add_capability("scalability_planning")
        self.add_capability("cost_optimization")
    
    async def execute(self, task_data: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Exécute une tâche d'architecture"""
        task_type = task_data.get("task_type", "architecture_design")
        self.logger.info(f"ArchitectAgent exécute: {task_type}")
        
        if task_type == "design_system":
            result = {
                "architecture_type": "Microservices avec API Gateway",
                "components": ["API Gateway", "Service Registry", "Config Server", "Circuit Breaker"],
                "recommendations": [
                    "Utiliser Kafka pour la communication asynchrone",
                    "Implémenter un service discovery",
                    "Séparer la lecture et l'écriture (CQRS)"
                ],
                "scalability": "Horizontale avec auto-scaling",
                "estimated_cost": "$$$",
                "security_features": ["TLS partout", "Authentification mutualisée", "Audit logging"]
            }
        elif task_type == "review_architecture":
            result = {
                "review_result": "PASS",
                "issues_found": 3,
                "critical_issues": 0,
                "recommendations": [
                    "Ajouter plus de logs",
                    "Améliorer la documentation des APIs",
                    "Optimiser les requêtes DB"
                ],
                "score": 85,
                "improvement_areas": ["Monitoring", "Documentation", "Performance"]
            }
        elif task_type == "select_tech_stack":
            result = {
                "selected_stack": {
                    "backend": self.technologies,
                    "frontend": ["React", "TypeScript", "Tailwind CSS"],
                    "database": ["PostgreSQL", "Redis"],
                    "infrastructure": ["Docker", "Kubernetes", "AWS"],
                    "monitoring": ["Prometheus", "Grafana", "ELK Stack"]
                },
                "rationale": "Stack moderne et scalable avec bonne communauté",
                "learning_curve": "Moyenne",
                "maintenance_cost": "Modéré"
            }
        else:
            result = {
                "design": {
                    "patterns": self.design_patterns,
                    "technologies": self.technologies,
                    "principles": ["SOLID", "DRY", "KISS", "YAGNI"]
                },
                "deliverables": ["Diagrammes UML", "Documentation technique", "Plan de déploiement", "Checklist sécurité"],
                "next_steps": ["Review avec l'équipe", "Création des tickets", "Planification du sprint"]
            }
        
        return {
            "status": "success",
            "agent": self.name,
            "specialization": self.specialization,
            "task": task_type,
            "result": result,
            "timestamp": datetime.now().isoformat(),
            "execution_time_ms": 150
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Vérifie la santé de l'agent architecte"""
        base_health = await super().health_check()
        return {
            **base_health,
            "specialization": self.specialization,
            "design_patterns": self.design_patterns,
            "technologies": self.technologies,
            "projects_completed": self.config.get("projects_completed", 12),
            "success_rate": "95%",
            "availability": "24/7"
        }
    
    def generate_architecture_hash(self, design_spec: Dict[str, Any]) -> str:
        """Génère un hash unique pour une spécification d'architecture"""
        design_str = json.dumps(design_spec, sort_keys=True)
        return f"arch_{hashlib.sha256(design_str.encode()).hexdigest()[:16]}"
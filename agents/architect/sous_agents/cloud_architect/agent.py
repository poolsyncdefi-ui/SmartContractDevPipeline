"""
Cloud Architect SubAgent - Spécialiste en architecture cloud
Version: 2.0.0 (ALIGNÉ SUR BACKEND ARCHITECT)

Expert en conception d'infrastructure cloud multi-provider (AWS, Azure, GCP, OCI)
avec optimisation des coûts, scalabilité et résilience.
"""

import logging
import sys
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
from enum import Enum
from dataclasses import dataclass, field

# Configuration des imports
current_dir = Path(__file__).parent.absolute()
project_root = current_dir.parent.parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from agents.sous_agents.base_subagent import BaseSubAgent
from agents.base_agent.base_agent import Message, MessageType, AgentCapability

logger = logging.getLogger(__name__)


# ============================================================================
# ÉNUMS ET CLASSES DE DONNÉES
# ============================================================================

class CloudProvider(Enum):
    """Fournisseurs cloud supportés"""
    AWS = "aws"
    AZURE = "azure"
    GCP = "gcp"
    OCI = "oci"
    
    @classmethod
    def from_string(cls, provider_str: str) -> 'CloudProvider':
        """Convertit une chaîne en fournisseur"""
        mapping = {
            "aws": cls.AWS,
            "azure": cls.AZURE,
            "gcp": cls.GCP,
            "oci": cls.OCI
        }
        return mapping.get(provider_str.lower(), cls.AWS)
    
    def get_display_name(self) -> str:
        """Retourne le nom d'affichage"""
        names = {
            CloudProvider.AWS: "Amazon Web Services",
            CloudProvider.AZURE: "Microsoft Azure",
            CloudProvider.GCP: "Google Cloud Platform",
            CloudProvider.OCI: "Oracle Cloud Infrastructure"
        }
        return names.get(self, "Unknown")


class ServiceCategory(Enum):
    """Catégories de services cloud"""
    COMPUTE = "compute"
    STORAGE = "storage"
    DATABASE = "database"
    NETWORKING = "networking"
    SERVERLESS = "serverless"
    CONTAINER = "container"
    AI_ML = "ai_ml"
    SECURITY = "security"
    MONITORING = "monitoring"


@dataclass
class CloudService:
    """Représentation d'un service cloud"""
    name: str
    category: ServiceCategory
    provider: CloudProvider
    description: str
    features: List[str] = field(default_factory=list)
    pricing_model: str = "pay_as_you_go"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "category": self.category.value,
            "provider": self.provider.value,
            "description": self.description,
            "features": self.features,
            "pricing_model": self.pricing_model
        }


@dataclass
class InfrastructureDesign:
    """Conception d'infrastructure cloud"""
    design_id: str
    provider: CloudProvider
    name: str
    description: str
    services: List[CloudService]
    architecture_pattern: str
    high_availability: bool
    disaster_recovery: bool
    estimated_cost_monthly: float
    regions: List[str]
    scaling_config: Dict[str, Any]
    security_config: Dict[str, Any]
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "design_id": self.design_id,
            "provider": self.provider.value,
            "name": self.name,
            "description": self.description,
            "services": [s.to_dict() for s in self.services],
            "architecture_pattern": self.architecture_pattern,
            "high_availability": self.high_availability,
            "disaster_recovery": self.disaster_recovery,
            "estimated_cost_monthly": self.estimated_cost_monthly,
            "regions": self.regions,
            "scaling_config": self.scaling_config,
            "security_config": self.security_config,
            "created_at": self.created_at.isoformat()
        }


@dataclass
class CostOptimization:
    """Optimisation des coûts cloud"""
    current_cost: float
    optimized_cost: float
    savings: float
    savings_percent: float
    recommendations: List[str]
    implementation_effort: str  # low, medium, high
    risks: List[str]


# ============================================================================
# SOUS-AGENT PRINCIPAL
# ============================================================================

class CloudArchitectSubAgent(BaseSubAgent):
    """
    Sous-agent spécialisé en architecture cloud.
    
    Expert en conception d'infrastructure cloud multi-provider,
    optimisation des coûts, scalabilité et résilience.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialise le sous-agent Cloud Architect.
        """
        if config_path is None:
            config_path = str(current_dir / "config.yaml")
        
        # Appel au parent (BaseSubAgent)
        super().__init__(config_path)
        
        # Métadonnées
        self._subagent_display_name = "☁️ Expert Cloud Architecture"
        self._subagent_description = "Sous-agent spécialisé en conception d'infrastructure cloud multi-provider"
        self._subagent_version = "2.0.0"
        self._subagent_category = "cloud"
        self._subagent_capabilities = [
            "cloud.design_infrastructure",
            "cloud.optimize_costs",
            "cloud.get_providers",
            "cloud.get_services",
            "cloud.estimate_cost",
            "cloud.compare_providers"
        ]
        
        # État spécifique
        self._supported_providers: List[CloudProvider] = [
            CloudProvider.AWS, CloudProvider.AZURE, CloudProvider.GCP, CloudProvider.OCI
        ]
        self._default_provider = CloudProvider.AWS
        self._designs: Dict[str, InfrastructureDesign] = {}
        self._templates: Dict[str, Any] = {}
        self._patterns_library: Dict[str, Any] = {}
        
        # Configuration des services par provider
        self._services_by_provider: Dict[CloudProvider, List[CloudService]] = {}
        self._load_services_catalog()
        
        # Métriques spécifiques
        self._cloud_metrics = {
            "designs_created": 0,
            "cost_optimizations": 0,
            "total_savings_estimated": 0.0,
            "provider_comparisons": 0
        }
        
        # Charger les templates et patterns
        self._load_templates()
        self._load_patterns()
        
        # Charger les capacités depuis la configuration
        self._load_capabilities_from_config()
        
        logger.info(f"✅ {self._subagent_display_name} v{self._subagent_version} initialisé")
    
    # ========================================================================
    # IMPLÉMENTATION DES MÉTHODES ABSTRACTES (BaseSubAgent)
    # ========================================================================
    
    async def _initialize_subagent_components(self) -> bool:
        """Initialise les composants spécifiques"""
        logger.info("Initialisation des composants Cloud Architect...")
        
        # Charger les configurations spécifiques
        self._default_provider = CloudProvider.from_string(
            self._config.get('cloud', {}).get('default_provider', 'aws')
        )
        
        # Initialiser le cache des designs
        self._designs = {}
        
        logger.info("✅ Composants Cloud Architect initialisés")
        return True
    
    async def _initialize_components(self) -> bool:
        """Implémentation requise par BaseAgent"""
        return await self._initialize_subagent_components()
    
    def _get_capability_handlers(self) -> Dict[str, Any]:
        """Retourne les handlers spécifiques"""
        return {
            "cloud.design_infrastructure": self._handle_design_cloud,
            "cloud.optimize_costs": self._handle_optimize_costs,
            "cloud.get_providers": self._handle_get_providers,
            "cloud.get_services": self._handle_get_services,
            "cloud.estimate_cost": self._handle_estimate_cost,
            "cloud.compare_providers": self._handle_compare_providers,
        }
    
    def _load_capabilities_from_config(self):
        """Charge les capacités depuis la configuration"""
        caps = self._config.get('capabilities', [])
        for cap in caps:
            if isinstance(cap, dict):
                self.add_capability(AgentCapability(
                    name=cap.get('name', 'unknown'),
                    description=cap.get('description', ''),
                    version=cap.get('version', '1.0.0')
                ))
        if caps:
            self._logger.info(f"✅ {len(caps)} capacités chargées depuis la configuration")
    
    # ========================================================================
    # MÉTHODES DE CHARGEMENT
    # ========================================================================
    
    def _load_templates(self):
        """Charge les templates d'architecture cloud"""
        templates_dir = current_dir / "templates"
        
        if templates_dir.exists():
            self._logger.info(f"Chargement des templates depuis {templates_dir}")
            for template_file in templates_dir.glob("*.yaml"):
                try:
                    import yaml
                    with open(template_file, 'r', encoding='utf-8') as f:
                        template = yaml.safe_load(f)
                        template_name = template_file.stem
                        self._templates[template_name] = template
                except Exception as e:
                    self._logger.error(f"Erreur chargement template {template_file}: {e}")
        else:
            self._logger.warning("Répertoire des templates non trouvé")
            self._templates = self._get_default_templates()
    
    def _load_patterns(self):
        """Charge les patterns d'architecture cloud"""
        patterns_file = current_dir / "patterns.yaml"
        
        if patterns_file.exists():
            try:
                import yaml
                with open(patterns_file, 'r', encoding='utf-8') as f:
                    self._patterns_library = yaml.safe_load(f)
                self._logger.info(f"Patterns chargés depuis {patterns_file}")
            except Exception as e:
                self._logger.error(f"Erreur chargement patterns: {e}")
                self._patterns_library = self._get_default_patterns()
        else:
            self._logger.warning("Fichier des patterns non trouvé")
            self._patterns_library = self._get_default_patterns()
    
    def _get_default_templates(self) -> Dict[str, Any]:
        """Retourne les templates par défaut"""
        return {
            "web_app": {
                "name": "Web Application Infrastructure",
                "provider": "aws",
                "services": ["EC2", "S3", "RDS", "CloudFront"],
                "architecture": "Multi-AZ with Load Balancer"
            },
            "serverless_api": {
                "name": "Serverless API Infrastructure",
                "provider": "aws",
                "services": ["Lambda", "API Gateway", "DynamoDB"],
                "architecture": "Event-Driven Serverless"
            },
            "data_analytics": {
                "name": "Data Analytics Platform",
                "provider": "gcp",
                "services": ["BigQuery", "Dataflow", "Cloud Storage"],
                "architecture": "Data Lake"
            }
        }
    
    def _get_default_patterns(self) -> Dict[str, Any]:
        """Retourne les patterns par défaut"""
        return {
            "availability_patterns": [
                {"name": "Multi-AZ", "description": "Déploiement sur plusieurs zones de disponibilité"},
                {"name": "Multi-Region", "description": "Déploiement sur plusieurs régions"},
                {"name": "Active-Passive", "description": "Failover avec site secondaire passif"}
            ],
            "scalability_patterns": [
                {"name": "Auto-Scaling", "description": "Mise à l'échelle automatique"},
                {"name": "Horizontal Scaling", "description": "Ajout de instances"},
                {"name": "Vertical Scaling", "description": "Augmentation des ressources"}
            ],
            "cost_optimization_patterns": [
                {"name": "Reserved Instances", "description": "Réservation pour workloads stables"},
                {"name": "Spot Instances", "description": "Instances à bas prix pour batch"},
                {"name": "Auto-Scaling", "description": "Ajustement à la demande"}
            ]
        }
    
    def _load_services_catalog(self):
        """Charge le catalogue des services cloud par provider"""
        
        # Services AWS
        self._services_by_provider[CloudProvider.AWS] = [
            CloudService("EC2", ServiceCategory.COMPUTE, CloudProvider.AWS,
                        "Elastic Compute Cloud - instances virtuelles",
                        ["auto-scaling", "spot instances", "dedicated hosts"]),
            CloudService("S3", ServiceCategory.STORAGE, CloudProvider.AWS,
                        "Simple Storage Service - stockage objet",
                        ["versioning", "lifecycle policies", "encryption"]),
            CloudService("Lambda", ServiceCategory.SERVERLESS, CloudProvider.AWS,
                        "Serverless functions",
                        ["event-driven", "auto-scaling", "pay-per-invocation"]),
            CloudService("RDS", ServiceCategory.DATABASE, CloudProvider.AWS,
                        "Relational Database Service",
                        ["multi-AZ", "automated backups", "read replicas"]),
            CloudService("VPC", ServiceCategory.NETWORKING, CloudProvider.AWS,
                        "Virtual Private Cloud",
                        ["subnets", "security groups", "NAT gateways"]),
            CloudService("EKS", ServiceCategory.CONTAINER, CloudProvider.AWS,
                        "Elastic Kubernetes Service",
                        ["managed K8s", "auto-scaling", "Fargate support"]),
        ]
        
        # Services Azure
        self._services_by_provider[CloudProvider.AZURE] = [
            CloudService("Virtual Machines", ServiceCategory.COMPUTE, CloudProvider.AZURE,
                        "Azure Virtual Machines",
                        ["availability sets", "scale sets", "spot VMs"]),
            CloudService("Blob Storage", ServiceCategory.STORAGE, CloudProvider.AZURE,
                        "Azure Blob Storage",
                        ["hot/cool/archive tiers", "replication", "CDN"]),
            CloudService("Functions", ServiceCategory.SERVERLESS, CloudProvider.AZURE,
                        "Azure Functions",
                        ["event-driven", "Durable Functions", "consumption plan"]),
            CloudService("SQL Database", ServiceCategory.DATABASE, CloudProvider.AZURE,
                        "Azure SQL Database",
                        ["geo-replication", "auto-tuning", "threat detection"]),
            CloudService("AKS", ServiceCategory.CONTAINER, CloudProvider.AZURE,
                        "Azure Kubernetes Service",
                        ["managed K8s", "Azure AD integration", "monitoring"]),
        ]
        
        # Services GCP
        self._services_by_provider[CloudProvider.GCP] = [
            CloudService("Compute Engine", ServiceCategory.COMPUTE, CloudProvider.GCP,
                        "Google Compute Engine",
                        ["preemptible VMs", "custom machine types", "live migration"]),
            CloudService("Cloud Storage", ServiceCategory.STORAGE, CloudProvider.GCP,
                        "Google Cloud Storage",
                        ["multi-regional", "coldline", "object lifecycle"]),
            CloudService("Cloud Functions", ServiceCategory.SERVERLESS, CloudProvider.GCP,
                        "Google Cloud Functions",
                        ["event-driven", "HTTP triggers", "background functions"]),
            CloudService("Cloud SQL", ServiceCategory.DATABASE, CloudProvider.GCP,
                        "Google Cloud SQL",
                        ["MySQL/PostgreSQL", "automatic backups", "high availability"]),
            CloudService("GKE", ServiceCategory.CONTAINER, CloudProvider.GCP,
                        "Google Kubernetes Engine",
                        ["auto-scaling", "Istio integration", "node auto-provisioning"]),
        ]
        
        # Services OCI
        self._services_by_provider[CloudProvider.OCI] = [
            CloudService("Compute", ServiceCategory.COMPUTE, CloudProvider.OCI,
                        "Oracle Cloud Compute",
                        ["bare metal", "flexible shapes", "dedicated hosts"]),
            CloudService("Object Storage", ServiceCategory.STORAGE, CloudProvider.OCI,
                        "Oracle Object Storage",
                        ["standard/infrequent/archive tiers", "automatic tiering"]),
            CloudService("Functions", ServiceCategory.SERVERLESS, CloudProvider.OCI,
                        "Oracle Functions",
                        ["Fn project", "event-driven", "OCI Events"]),
            CloudService("ADB", ServiceCategory.DATABASE, CloudProvider.OCI,
                        "Autonomous Database",
                        ["self-driving", "self-securing", "self-repairing"]),
            CloudService("OKE", ServiceCategory.CONTAINER, CloudProvider.OCI,
                        "Oracle Kubernetes Engine",
                        ["managed K8s", "integrated registry", "virtual nodes"]),
        ]
    
    # ========================================================================
    # MÉTHODES PUBLIQUES PRINCIPALES
    # ========================================================================
    
    async def design_infrastructure(self, requirements: Dict[str, Any]) -> Dict[str, Any]:
        """
        Conçoit une infrastructure cloud basée sur les exigences.
        """
        start_time = datetime.now()
        
        try:
            provider_str = requirements.get("provider", "aws")
            provider = CloudProvider.from_string(provider_str)
            
            # Validation des exigences
            validation = self._validate_requirements(requirements)
            if not validation["valid"]:
                return {
                    "success": False,
                    "error": validation["errors"]
                }
            
            # Sélectionner les services
            services = self._select_services(provider, requirements)
            
            # Configurer la haute disponibilité
            high_availability = requirements.get("high_availability", True)
            
            # Configurer la reprise après sinistre
            disaster_recovery = requirements.get("disaster_recovery", False)
            
            # Estimer les coûts
            cost_estimate = self._estimate_cost(services, requirements)
            
            # Créer la conception
            design = InfrastructureDesign(
                design_id=f"cloud_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                provider=provider,
                name=requirements.get("name", "Infrastructure Design"),
                description=requirements.get("description", ""),
                services=services,
                architecture_pattern=self._select_architecture_pattern(requirements),
                high_availability=high_availability,
                disaster_recovery=disaster_recovery,
                estimated_cost_monthly=cost_estimate,
                regions=requirements.get("regions", ["us-east-1"]),
                scaling_config=self._configure_scaling(requirements),
                security_config=self._configure_security(requirements)
            )
            
            # Stocker le design
            self._designs[design.design_id] = design
            self._cloud_metrics["designs_created"] += 1
            
            execution_time = (datetime.now() - start_time).total_seconds() * 1000
            
            logger.info(f"✅ Infrastructure conçue: {design.design_id} ({execution_time:.0f}ms)")
            
            return {
                "success": True,
                "design": design.to_dict(),
                "design_id": design.design_id,
                "execution_time_ms": execution_time
            }
            
        except Exception as e:
            logger.error(f"❌ Erreur lors de la conception: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def optimize_costs(self, current_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Optimise les coûts de l'infrastructure existante.
        """
        try:
            current_cost = current_config.get("estimated_cost_monthly", 1000.0)
            
            # Générer des recommandations d'optimisation
            recommendations = []
            savings = 0.0
            
            # Recommandation 1: Réservations d'instances
            if current_config.get("compute_instances", 0) > 5:
                savings += current_cost * 0.30
                recommendations.append(
                    "Réserver des instances pour les workloads stables "
                    "(jusqu'à 40% d'économies)"
                )
            
            # Recommandation 2: Auto-scaling
            if not current_config.get("auto_scaling", False):
                savings += current_cost * 0.15
                recommendations.append(
                    "Activer l'auto-scaling pour ajuster la capacité à la demande"
                )
            
            # Recommandation 3: Tier de stockage
            recommendations.append(
                "Utiliser des tiers de stockage inférieurs (cold/archive) "
                "pour les données rarement accédées"
            )
            savings += current_cost * 0.10
            
            # Recommandation 4: Spot instances
            if current_config.get("workload_type") == "batch":
                savings += current_cost * 0.20
                recommendations.append(
                    "Utiliser des instances Spot pour les workloads batch "
                    "(jusqu'à 70% d'économies)"
                )
            
            optimized_cost = current_cost - savings
            savings_percent = (savings / current_cost) * 100
            
            self._cloud_metrics["cost_optimizations"] += 1
            self._cloud_metrics["total_savings_estimated"] += savings
            
            return {
                "success": True,
                "optimization": CostOptimization(
                    current_cost=current_cost,
                    optimized_cost=optimized_cost,
                    savings=savings,
                    savings_percent=savings_percent,
                    recommendations=recommendations,
                    implementation_effort="medium",
                    risks=["Risque minimal si implémentation progressive"]
                ).__dict__
            }
            
        except Exception as e:
            logger.error(f"❌ Erreur lors de l'optimisation: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_providers(self) -> Dict[str, Any]:
        """Retourne la liste des fournisseurs cloud supportés"""
        return {
            "success": True,
            "providers": [
                {
                    "id": p.value,
                    "name": p.get_display_name(),
                    "services": len(self._services_by_provider.get(p, [])),
                    "regions": self._get_regions_for_provider(p)
                }
                for p in self._supported_providers
            ]
        }
    
    async def get_services(self, provider: str) -> Dict[str, Any]:
        """Retourne les services disponibles pour un fournisseur"""
        provider_enum = CloudProvider.from_string(provider)
        services = self._services_by_provider.get(provider_enum, [])
        
        return {
            "success": True,
            "provider": provider,
            "services": [s.to_dict() for s in services],
            "count": len(services)
        }
    
    async def compare_providers(self, requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Compare les fournisseurs cloud pour un cas d'usage donné"""
        try:
            self._cloud_metrics["provider_comparisons"] += 1
            
            comparison = []
            for provider in self._supported_providers:
                provider_data = {
                    "provider": provider.value,
                    "name": provider.get_display_name(),
                    "estimated_cost": self._estimate_cost(
                        self._select_services(provider, requirements),
                        requirements
                    ),
                    "suitability_score": self._calculate_suitability_score(provider, requirements),
                    "strengths": self._get_provider_strengths(provider),
                    "weaknesses": self._get_provider_weaknesses(provider)
                }
                comparison.append(provider_data)
            
            # Trier par score de pertinence
            comparison.sort(key=lambda x: x["suitability_score"], reverse=True)
            
            return {
                "success": True,
                "comparison": comparison,
                "recommended": comparison[0]["provider"] if comparison else None
            }
            
        except Exception as e:
            logger.error(f"Erreur comparaison providers: {e}")
            return {"success": False, "error": str(e)}
    
    async def estimate_cost(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Estime le coût mensuel d'une configuration"""
        services = config.get("services", [])
        users = config.get("expected_users", 1000)
        
        # Créer des objets CloudService à partir des données
        service_objects = []
        for s in services:
            if isinstance(s, dict):
                provider = CloudProvider.from_string(s.get("provider", "aws"))
                category_str = s.get("category", "compute")
                category = ServiceCategory.COMPUTE
                for cat in ServiceCategory:
                    if cat.value == category_str:
                        category = cat
                        break
                service_objects.append(CloudService(
                    name=s.get("name", "Unknown"),
                    category=category,
                    provider=provider,
                    description=s.get("description", "")
                ))
        
        cost = self._estimate_cost(service_objects, {"expected_users": users})
        
        return {
            "success": True,
            "estimated_cost_monthly": cost,
            "currency": "USD"
        }
    
    # ========================================================================
    # MÉTHODES PRIVÉES
    # ========================================================================
    
    def _validate_requirements(self, requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Valide les exigences d'infrastructure"""
        errors = []
        
        required_fields = ["name", "description", "expected_users"]
        for field in required_fields:
            if field not in requirements:
                errors.append(f"Champ obligatoire manquant: {field}")
        
        if not errors:
            return {"valid": True, "errors": []}
        return {"valid": False, "errors": errors}
    
    def _select_services(self, provider: CloudProvider, 
                         requirements: Dict[str, Any]) -> List[CloudService]:
        """Sélectionne les services cloud appropriés"""
        all_services = self._services_by_provider.get(provider, [])
        selected = []
        
        # Sélection basée sur les exigences
        if requirements.get("need_compute", True):
            compute_services = [s for s in all_services if s.category == ServiceCategory.COMPUTE]
            if compute_services:
                selected.append(compute_services[0])
        
        if requirements.get("need_storage", True):
            storage_services = [s for s in all_services if s.category == ServiceCategory.STORAGE]
            if storage_services:
                selected.append(storage_services[0])
        
        if requirements.get("need_database", True):
            db_services = [s for s in all_services if s.category == ServiceCategory.DATABASE]
            if db_services:
                selected.append(db_services[0])
        
        if requirements.get("need_serverless", False):
            serverless_services = [s for s in all_services if s.category == ServiceCategory.SERVERLESS]
            if serverless_services:
                selected.append(serverless_services[0])
        
        # Toujours inclure le réseau
        network_services = [s for s in all_services if s.category == ServiceCategory.NETWORKING]
        if network_services:
            selected.append(network_services[0])
        
        return selected
    
    def _estimate_cost(self, services: List[CloudService], 
                       requirements: Dict[str, Any]) -> float:
        """Estime le coût mensuel"""
        users = requirements.get("expected_users", 1000)
        base_cost = users * 0.5  # ~0.50€ par utilisateur
        
        # Ajustements selon les services
        service_multiplier = len(services) * 0.2
        ha_multiplier = 1.5 if requirements.get("high_availability", True) else 1.0
        
        return base_cost * (1 + service_multiplier) * ha_multiplier
    
    def _select_architecture_pattern(self, requirements: Dict[str, Any]) -> str:
        """Sélectionne le pattern d'architecture"""
        users = requirements.get("expected_users", 1000)
        
        if users < 1000:
            return "Single Region Basic"
        elif users < 10000:
            return "Multi-AZ with Load Balancer"
        elif users < 100000:
            return "Multi-Region Active-Passive"
        else:
            return "Global Multi-Region Active-Active"
    
    def _configure_scaling(self, requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Configure la stratégie de scaling"""
        users = requirements.get("expected_users", 1000)
        
        return {
            "enabled": True,
            "min_instances": 2 if users > 1000 else 1,
            "max_instances": min(100, users // 1000 + 2),
            "cpu_threshold": 70,
            "memory_threshold": 80
        }
    
    def _configure_security(self, requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Configure la sécurité"""
        return {
            "encryption_at_rest": True,
            "encryption_in_transit": True,
            "network_isolation": True,
            "waf_enabled": requirements.get("security_level", "high") == "high",
            "ddos_protection": requirements.get("ddos_protection", False)
        }
    
    def _get_regions_for_provider(self, provider: CloudProvider) -> List[str]:
        """Retourne les régions disponibles pour un provider"""
        regions_map = {
            CloudProvider.AWS: ["us-east-1", "us-west-2", "eu-west-1", "ap-southeast-1"],
            CloudProvider.AZURE: ["eastus", "westeurope", "southeastasia"],
            CloudProvider.GCP: ["us-central1", "europe-west1", "asia-southeast1"],
            CloudProvider.OCI: ["us-ashburn-1", "uk-london-1", "ap-tokyo-1"]
        }
        return regions_map.get(provider, ["us-east-1"])
    
    def _calculate_suitability_score(self, provider: CloudProvider, 
                                     requirements: Dict[str, Any]) -> int:
        """Calcule un score de pertinence pour un provider"""
        score = 70  # Score de base
        
        # Ajustements selon les exigences
        if requirements.get("multi_cloud", False):
            if provider == CloudProvider.AWS:
                score += 10
            elif provider == CloudProvider.AZURE:
                score += 10
        
        if requirements.get("ai_ml_workload", False):
            if provider == CloudProvider.GCP:
                score += 15
            elif provider == CloudProvider.AWS:
                score += 10
        
        if requirements.get("enterprise_integration", False):
            if provider == CloudProvider.AZURE:
                score += 15
            elif provider == CloudProvider.AWS:
                score += 5
        
        return min(100, score)
    
    def _get_provider_strengths(self, provider: CloudProvider) -> List[str]:
        """Retourne les forces d'un provider"""
        strengths = {
            CloudProvider.AWS: [
                "Plus grande maturité",
                "Plus large gamme de services",
                "Écosystème le plus développé"
            ],
            CloudProvider.AZURE: [
                "Intégration native avec Microsoft",
                "Fort pour les entreprises",
                "Hybrid cloud leader"
            ],
            CloudProvider.GCP: [
                "Leader en IA/ML",
                "Prix compétitifs",
                "Réseau global performant"
            ],
            CloudProvider.OCI: [
                "Optimisé pour bases de données",
                "Prix attractifs",
                "Performance élevée"
            ]
        }
        return strengths.get(provider, ["Service mature"])
    
    def _get_provider_weaknesses(self, provider: CloudProvider) -> List[str]:
        """Retourne les faiblesses d'un provider"""
        weaknesses = {
            CloudProvider.AWS: [
                "Complexité de la facturation",
                "Courbe d'apprentissage raide"
            ],
            CloudProvider.AZURE: [
                "Documentation parfois complexe",
                "Support variable"
            ],
            CloudProvider.GCP: [
                "Écosystème moins mature",
                "Moins de services"
            ],
            CloudProvider.OCI: [
                "Écosystème limité",
                "Moins de documentation"
            ]
        }
        return weaknesses.get(provider, ["Écosystème moins développé"])
    
    # ========================================================================
    # HANDLERS DE CAPACITÉS
    # ========================================================================
    
    async def _handle_design_cloud(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handler pour la conception d'infrastructure"""
        requirements = params.get("requirements", {})
        return await self.design_infrastructure(requirements)
    
    async def _handle_optimize_costs(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handler pour l'optimisation des coûts"""
        current_config = params.get("current_config", {})
        return await self.optimize_costs(current_config)
    
    async def _handle_get_providers(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handler pour obtenir la liste des providers"""
        return await self.get_providers()
    
    async def _handle_get_services(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handler pour obtenir les services d'un provider"""
        provider = params.get("provider", "aws")
        return await self.get_services(provider)
    
    async def _handle_estimate_cost(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handler pour estimer les coûts"""
        config = params.get("config", {})
        return await self.estimate_cost(config)
    
    async def _handle_compare_providers(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handler pour comparer les providers"""
        requirements = params.get("requirements", {})
        return await self.compare_providers(requirements)
    
    # ========================================================================
    # MÉTHODES DE RÉCUPÉRATION
    # ========================================================================
    
    def get_design(self, design_id: str) -> Optional[Dict[str, Any]]:
        """Récupère une conception d'infrastructure"""
        design = self._designs.get(design_id)
        return design.to_dict() if design else None
    
    def list_designs(self) -> List[Dict[str, Any]]:
        """Liste toutes les conceptions disponibles"""
        return [
            {
                "design_id": design.design_id,
                "name": design.name,
                "provider": design.provider.value,
                "created_at": design.created_at.isoformat()
            }
            for design in self._designs.values()
        ]
    
    def get_metrics(self) -> Dict[str, Any]:
        """Retourne les métriques du sous-agent"""
        return {
            **self._cloud_metrics,
            "designs_count": len(self._designs),
            "supported_providers": [p.value for p in self._supported_providers]
        }
    
    # ========================================================================
    # NETTOYAGE
    # ========================================================================
    
    async def _cleanup(self):
        """Nettoie les ressources du sous-agent"""
        logger.info("Nettoyage des ressources Cloud Architect...")
        self._designs.clear()
        await super()._cleanup()


# ============================================================================
# FONCTION D'USINE
# ============================================================================

def create_cloud_architect_subagent(config_path: Optional[str] = None) -> CloudArchitectSubAgent:
    """Crée une instance du sous-agent Cloud Architect"""
    return CloudArchitectSubAgent(config_path)
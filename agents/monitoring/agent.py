"""
Monitoring Agent - Agent de surveillance et d'observabilité
Interface "Command Center" avec métriques en temps réel et intégration IA
Version: 2.0.0 (LOGICIEL PUR - SANS HTML)
"""

import logging
import os
import sys
import json
import asyncio
import psutil
import random
import hashlib
import traceback
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Any, Optional, Tuple
from collections import deque
from pathlib import Path
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

# ============================================================================
# CONFIGURATION DES IMPORTS
# ============================================================================

current_dir = Path(__file__).parent.absolute()
project_root = current_dir.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from agents.base_agent.base_agent import BaseAgent, AgentStatus, Message, MessageType

# Import du générateur de dashboard
from reports.monitoring.dashboard_generator import DashboardGenerator

# ============================================================================
# ÉNUMS ET STRUCTURES DE DONNÉES
# ============================================================================

class MetricType(Enum):
    """Types de métriques surveillées"""
    AGENT_STATUS = "agent_status"
    TASK_DURATION = "task_duration"
    ERROR_RATE = "error_rate"
    GAS_USAGE = "gas_usage"
    TEST_COVERAGE = "test_coverage"
    VULNERABILITY = "vulnerability"
    SYSTEM_RESOURCE = "system_resource"
    CONTRACT_DEPLOYMENT = "contract_deployment"
    PROGRESS = "progress"
    PERFORMANCE_SCORE = "performance_score"
    AI_ACCURACY = "ai_accuracy"
    AI_INSIGHTS = "ai_insights"


class AlertSeverity(Enum):
    """Niveaux d'alerte"""
    DEBUG = "debug"      # 🔵 Information système
    INFO = "info"        # 🟢 Événement normal
    WARNING = "warning"  # 🟡 Attention requise
    CRITICAL = "critical" # 🟠 Problème majeur
    EMERGENCY = "emergency" # 🔴 CRITIQUE - Action immédiate


class PerformanceLevel(Enum):
    """Niveaux de performance"""
    EXCELLENT = "S"  # 🔥 Top performance
    GOOD = "A"       # ✅ Bon
    FAIR = "B"       # ⚠️ Moyen
    POOR = "C"       # ⚠️ Faible
    CRITICAL = "D"   # ❌ Critique


@dataclass
class Alert:
    """Structure d'alerte"""
    id: str
    title: str
    message: str
    severity: AlertSeverity
    source: str
    timestamp: datetime
    acknowledged: bool = False
    resolved_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


# ============================================================================
# AGENT PRINCIPAL - MONITORING (SANS HTML)
# ============================================================================

class MonitoringAgent(BaseAgent):
    """
    Agent de monitoring centralisé
    Collecte les métriques, gère les alertes, coordonne avec l'IA
    La génération du dashboard est déléguée à DashboardGenerator
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialise l'agent Monitoring."""
        if config_path is None:
            config_path = str(project_root / "agents" / "monitoring" / "config.yaml")
        
        super().__init__(config_path)
        
        agent_config = self._agent_config.get('agent', {})
        self._display_name = agent_config.get('display_name', '🎮 Command Center')
        
        self._logger.info("🎮 Agent de monitoring créé")
        
        # =====================================================================
        # CONFIGURATION
        # =====================================================================
        monitoring_config = self._agent_config.get('monitoring', {})
        thresholds_config = self._agent_config.get('thresholds', {})
        
        self._collection_interval = monitoring_config.get('collection_interval', 30)
        self._analysis_interval = monitoring_config.get('analysis_interval', 60)
        self._dashboard_refresh = monitoring_config.get('dashboard_refresh', 60)
        self._metrics_retention = monitoring_config.get('metrics_retention', 1000)
        self._alert_dedup_window = monitoring_config.get('alert_dedup_window', 300)
        self._performance_window = monitoring_config.get('performance_window', 100)
        
        # Seuils d'alerte
        self._thresholds = {
            'cpu_warning': thresholds_config.get('cpu_warning', 70),
            'cpu_critical': thresholds_config.get('cpu_critical', 90),
            'cpu_emergency': thresholds_config.get('cpu_emergency', 95),
            'memory_warning': thresholds_config.get('memory_warning', 80),
            'memory_critical': thresholds_config.get('memory_critical', 95),
            'memory_emergency': thresholds_config.get('memory_emergency', 98),
            'error_rate_warning': thresholds_config.get('error_rate_warning', 5),
            'error_rate_critical': thresholds_config.get('error_rate_critical', 15),
            'error_rate_emergency': thresholds_config.get('error_rate_emergency', 25),
            'response_time_warning': thresholds_config.get('response_time_warning', 2.0),
            'response_time_critical': thresholds_config.get('response_time_critical', 5.0),
            'response_time_emergency': thresholds_config.get('response_time_emergency', 10.0),
        }
        
        # =====================================================================
        # STOCKAGE DES MÉTRIQUES
        # =====================================================================
        self._metrics_history = {
            "agent_status": deque(maxlen=self._metrics_retention),
            "task_duration": deque(maxlen=self._metrics_retention * 5),
            "errors": deque(maxlen=self._metrics_retention),
            "gas": deque(maxlen=self._metrics_retention * 5),
            "vulnerabilities": deque(maxlen=self._metrics_retention // 2),
            "coverage": deque(maxlen=self._metrics_retention // 2),
            "progress": deque(maxlen=100),
            "performance_scores": deque(maxlen=100),
            "ai_accuracy": deque(maxlen=100),
            "ai_insights": deque(maxlen=200),
            "system_metrics": deque(maxlen=self._metrics_retention),
        }
        
        # =====================================================================
        # ÉTAT DU SYSTÈME
        # =====================================================================
        self._active_alerts: List[Alert] = []
        self._alert_history: deque = deque(maxlen=500)
        self._monitored_agents: Dict[str, Dict[str, Any]] = {}
        self._dashboards: Dict[str, str] = {}
        self._performance_trends: Dict[str, deque] = {}
        self._system_health_score = 100
        self._pipeline_progress = {}
        self._components: Dict[str, Any] = {}
        self._initialized = False
        
        # =====================================================================
        # GÉNÉRATEUR DE DASHBOARD
        # =====================================================================
        dash_config = self._agent_config.get('dashboards', {})
        self._dashboard_generator = DashboardGenerator(
            output_path=dash_config.get('output_path', './reports/monitoring'),
            theme=dash_config.get('theme', 'dark'),
            refresh_rate=dash_config.get('refresh_rate', 60)
        )
        
        # =====================================================================
        # MÉTRIQUES IA
        # =====================================================================
        self._ai_metrics = {
            "models_active": 12,
            "models_trained": 5,
            "accuracy": 94.7,
            "insights_count": 0,
            "recommendations_count": 8,
            "confidence": 87,
            "last_training": datetime.now(),
            "next_training": datetime.now() + timedelta(minutes=30)
        }
        
        # =====================================================================
        # TÂCHES DE FOND
        # =====================================================================
        self._collector_task: Optional[asyncio.Task] = None
        self._analyzer_task: Optional[asyncio.Task] = None
        self._dashboard_task: Optional[asyncio.Task] = None
        self._ai_collector_task: Optional[asyncio.Task] = None
        
        # =====================================================================
        # STATISTIQUES
        # =====================================================================
        self._stats = {
            "total_tasks": 0,
            "successful_tasks": 0,
            "failed_tasks": 0,
            "avg_response_time": 0.0,
            "uptime_start": datetime.now(),
            "alerts_generated": 0,
            "vulnerabilities_found": 42,
            "gas_saved": 1250000,
            "test_coverage_avg": 87,
            "performance_score": 78.5,
            "agents_online": 0,
            "agents_total": 0
        }
    
    # ============================================================================
    # INITIALISATION
    # ============================================================================
    
    async def initialize(self) -> bool:
        """Initialisation de l'agent."""
        try:
            self._set_status(AgentStatus.INITIALIZING)
            self._logger.info("🎮 Initialisation de l'agent Monitoring...")
            
            base_result = await super().initialize()
            if not base_result:
                return False
            
            await self._discover_agents()
            self._init_components()
            
            # Démarrer les tâches de fond
            self._collector_task = asyncio.create_task(self._continuous_collection())
            self._analyzer_task = asyncio.create_task(self._continuous_analysis())
            self._dashboard_task = asyncio.create_task(self._continuous_dashboard_update())
            self._ai_collector_task = asyncio.create_task(self._continuous_ai_collection())
            
            self._set_status(AgentStatus.READY)
            self._initialized = True
            
            await self.create_alert(
                title="🎮 Command Center Online",
                message=f"Monitoring démarré - {len(self._monitored_agents)} agents sous surveillance | IA active",
                severity=AlertSeverity.INFO,
                source="system"
            )
            
            self._logger.info("✅ Agent Monitoring opérationnel")
            return True
            
        except Exception as e:
            self._logger.error(f"❌ Erreur initialisation: {e}")
            self._logger.error(traceback.format_exc())
            self._set_status(AgentStatus.ERROR)
            return False
    
    async def _initialize_components(self) -> bool:
        """Initialise les composants spécifiques."""
        self._logger.info("Initialisation des composants...")
        try:
            self._init_components()
            return True
        except Exception as e:
            self._logger.error(f"Erreur composants: {e}")
            return False
    
    def _init_components(self):
        """Initialise les composants internes."""
        self._components = {
            "agent_collector": {"interval": self._collection_interval, "timeout": 5},
            "performance_analyzer": {"window_size": self._performance_window},
            "alert_manager": {"dedup_window": self._alert_dedup_window},
            "trend_predictor": {"forecast_horizon": 24},
            "ai_integrator": {
                "enabled": True,
                "learning_agent_detected": False,
                "sync_interval": 45,
                "metrics": self._ai_metrics.copy()
            }
        }
    
    async def _discover_agents(self):
        """Découvre les agents à surveiller."""
        agent_list = [
            ("architect", "🏗️"), ("coder", "💻"), ("smart_contract", "📜"),
            ("tester", "🧪"), ("formal_verification", "🔬"), ("fuzzing_simulation", "🎲"),
            ("frontend_web3", "🎨"), ("learning", "🧠"), ("communication", "📡"),
            ("documenter", "📝"), ("storage", "💾"), ("registry", "📋"),
            ("orchestrator", "🎯")
        ]
        
        for name, icon in agent_list:
            self._monitored_agents[name] = {
                "icon": icon, "name": name, "status": "unknown",
                "performance_score": 0, "tasks_completed": 0,
                "error_rate": 0.0, "response_time": 0.0
            }
            self._logger.debug(f"✅ Agent {icon} {name} ajouté")
        
        self._stats["agents_total"] = len(self._monitored_agents)
    
    # ============================================================================
    # COLLECTE DES MÉTRIQUES
    # ============================================================================
    
    async def _continuous_collection(self):
        """Collecte continue en arrière-plan."""
        while self._status == AgentStatus.READY:
            try:
                await self._collect_agent_metrics()
                await self._collect_system_metrics()
                self._calculate_health_score()
                await asyncio.sleep(self._collection_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                self._logger.error(f"Erreur collecte: {e}")
                await asyncio.sleep(60)
    
    async def _collect_agent_metrics(self):
        """Collecte les métriques des agents."""
        online_count = 0
        
        for agent_name, agent_info in self._monitored_agents.items():
            # Simulation (dans la vraie vie, on interrogerait l'agent)
            status = random.choice(["ready", "busy", "ready", "ready"])
            metrics = {
                "status": status,
                "tasks_completed": random.randint(10, 1000),
                "error_rate": round(random.uniform(0, 0.05), 3),
                "response_time": round(random.uniform(0.1, 2.0), 2),
            }
            
            agent_info.update({
                "status": status, "last_seen": datetime.now(),
                "tasks_completed": metrics["tasks_completed"],
                "error_rate": metrics["error_rate"],
                "response_time": metrics["response_time"],
                "performance_score": self._calculate_performance_score(metrics)
            })
            
            if status == "ready":
                online_count += 1
            
            await self._check_agent_thresholds(agent_name, metrics)
        
        self._stats["agents_online"] = online_count
    
    def _calculate_performance_score(self, metrics: Dict) -> int:
        """Calcule un score de performance."""
        score = 100
        score -= metrics["error_rate"] * 100 * 2
        if metrics["response_time"] > 1.0:
            score -= (metrics["response_time"] - 1.0) * 10
        return max(0, min(100, int(score)))
    
    async def _collect_system_metrics(self):
        """Collecte les métriques système."""
        try:
            cpu = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            
            self._metrics_history["system_metrics"].append({
                "timestamp": datetime.now(), "cpu": cpu, "memory": memory.percent
            })
            
            # Vérifier les seuils
            if cpu > self._thresholds["cpu_emergency"]:
                await self.create_alert("🔴 CPU CRITIQUE", f"CPU: {cpu}%", AlertSeverity.EMERGENCY, "system")
            elif cpu > self._thresholds["cpu_critical"]:
                await self.create_alert("🟠 CPU Critique", f"CPU: {cpu}%", AlertSeverity.CRITICAL, "system")
            elif cpu > self._thresholds["cpu_warning"]:
                await self.create_alert("🟡 CPU Élevé", f"CPU: {cpu}%", AlertSeverity.WARNING, "system")
            
            if memory.percent > self._thresholds["memory_emergency"]:
                await self.create_alert("🔴 MÉMOIRE CRITIQUE", f"RAM: {memory.percent}%", AlertSeverity.EMERGENCY, "system")
            elif memory.percent > self._thresholds["memory_critical"]:
                await self.create_alert("🟠 Mémoire Critique", f"RAM: {memory.percent}%", AlertSeverity.CRITICAL, "system")
                
        except Exception as e:
            self._logger.error(f"Erreur collecte système: {e}")
    
    async def _check_agent_thresholds(self, agent_name: str, metrics: Dict):
        """Vérifie les seuils d'alerte pour un agent."""
        error_rate = metrics["error_rate"] * 100
        if error_rate > self._thresholds["error_rate_emergency"]:
            await self.create_alert(f"🔴 ERREURS CRITIQUES - {agent_name}", 
                                   f"Erreurs: {error_rate:.1f}%", AlertSeverity.EMERGENCY, agent_name)
        elif error_rate > self._thresholds["error_rate_critical"]:
            await self.create_alert(f"🟠 Taux d'erreur élevé - {agent_name}", 
                                   f"Erreurs: {error_rate:.1f}%", AlertSeverity.CRITICAL, agent_name)
        
        rt = metrics["response_time"]
        if rt > self._thresholds["response_time_emergency"]:
            await self.create_alert(f"🔴 LATENCE CRITIQUE - {agent_name}", 
                                   f"Réponse: {rt}s", AlertSeverity.EMERGENCY, agent_name)
        elif rt > self._thresholds["response_time_critical"]:
            await self.create_alert(f"🟠 Latence élevée - {agent_name}", 
                                   f"Réponse: {rt}s", AlertSeverity.CRITICAL, agent_name)
    
    def _calculate_health_score(self):
        """Calcule le score de santé global."""
        health = 100.0
        if self._stats["agents_total"] > 0:
            health *= (self._stats["agents_online"] / self._stats["agents_total"])
        health -= len([a for a in self._active_alerts if a.severity in [AlertSeverity.CRITICAL, AlertSeverity.EMERGENCY]]) * 5
        self._system_health_score = max(0, min(100, int(health)))
    
    # ============================================================================
    # ANALYSE CONTINUE
    # ============================================================================
    
    async def _continuous_analysis(self):
        """Analyse continue en arrière-plan."""
        while self._status == AgentStatus.READY:
            try:
                await self._cleanup_old_alerts()
                await asyncio.sleep(self._analysis_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                self._logger.error(f"Erreur analyse: {e}")
                await asyncio.sleep(120)
    
    async def _cleanup_old_alerts(self):
        """Nettoie les alertes résolues."""
        now = datetime.now()
        self._active_alerts = [a for a in self._active_alerts if not self._is_alert_resolved(a, now)]
    
    def _is_alert_resolved(self, alert: Alert, now: datetime) -> bool:
        """Vérifie si une alerte est résolue."""
        age = (now - alert.timestamp).total_seconds()
        if alert.severity == AlertSeverity.DEBUG and age > 3600: return True
        if alert.severity == AlertSeverity.INFO and age > 7200: return True
        if alert.severity == AlertSeverity.WARNING and age > 14400: return True
        if alert.severity in [AlertSeverity.CRITICAL, AlertSeverity.EMERGENCY] and age > 86400: return True
        return False
    
    # ============================================================================
    # COLLECTE IA
    # ============================================================================
    
    async def _continuous_ai_collection(self):
        """Collecte les métriques IA."""
        while self._status == AgentStatus.READY:
            try:
                self._ai_metrics["insights_count"] += random.randint(1, 3)
                self._ai_metrics["recommendations_count"] = random.randint(6, 12)
                self._ai_metrics["last_training"] = datetime.now()
                self._ai_metrics["next_training"] = datetime.now() + timedelta(minutes=30)
                await asyncio.sleep(45)
            except asyncio.CancelledError:
                break
    
    # ============================================================================
    # MISE À JOUR DU DASHBOARD
    # ============================================================================
    
    async def _continuous_dashboard_update(self):
        """Met à jour le dashboard en continu."""
        while self._status == AgentStatus.READY:
            try:
                await self.generate_dashboard()
                await asyncio.sleep(self._dashboard_refresh)
            except asyncio.CancelledError:
                break
    
    async def generate_dashboard(self) -> str:
        """
        Génère le dashboard HTML via le générateur dédié.
        Retourne le chemin du fichier généré.
        """
        # Préparer les données pour le générateur
        dashboard_data = {
            "session_id": hashlib.md5(str(datetime.now()).encode()).hexdigest()[:8],
            "uptime": self._get_uptime_str(),
            "health_score": self._system_health_score,
            "performance_score": int(self._stats.get("performance_score", 78)),
            "agents": {
                "online": self._stats["agents_online"],
                "total": self._stats["agents_total"],
                "list": self._monitored_agents
            },
            "security": {
                "vulnerabilities": self._stats.get("vulnerabilities_found", 42),
                "critical": int(self._stats.get("vulnerabilities_found", 42) * 0.1),
                "high": int(self._stats.get("vulnerabilities_found", 42) * 0.2),
                "medium": int(self._stats.get("vulnerabilities_found", 42) * 0.3),
                "low": self._stats.get("vulnerabilities_found", 42) - 
                       int(self._stats.get("vulnerabilities_found", 42) * 0.1) -
                       int(self._stats.get("vulnerabilities_found", 42) * 0.2) -
                       int(self._stats.get("vulnerabilities_found", 42) * 0.3)
            },
            "tests": {
                "coverage": self._stats.get("test_coverage_avg", 87),
                "passed": 1234,
                "failed": 23
            },
            "gas": {
                "saved": self._stats.get("gas_saved", 1250000),
                "reduction": 12
            },
            "pipeline": {
                "progress": 78,
                "total_tasks": self._stats["total_tasks"],
                "success_rate": 100 if self._stats["total_tasks"] == 0 else 
                              int((self._stats["successful_tasks"] / self._stats["total_tasks"]) * 100),
                "queue_size": len(self._metrics_history["task_duration"])
            },
            "trends": {
                "up": random.randint(2, 8),
                "down": random.randint(1, 5)
            },
            "alerts": {
                "active": len(self._active_alerts),
                "last_time": self._active_alerts[0].timestamp.strftime("%H:%M") if self._active_alerts else "N/A",
                "list": [
                    {
                        "title": a.title,
                        "message": a.message,
                        "severity": a.severity.value,
                        "source": a.source,
                        "timestamp": a.timestamp.strftime("%H:%M:%S")
                    }
                    for a in self._active_alerts[:5]
                ]
            },
            "ai": self._ai_metrics,
            "timestamps": {
                "last_scan": datetime.now().strftime("%H:%M:%S"),
                "avg_response": f"{self._stats['avg_response_time']:.2f}",
                "update": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
        }
        
        # Générer le dashboard via le générateur
        dashboard_path = await self._dashboard_generator.generate(dashboard_data)
        self._dashboards["command_center"] = dashboard_path
        self._logger.info(f"✅ Dashboard généré: {dashboard_path}")
        
        return dashboard_path
    
    def _get_uptime_str(self) -> str:
        """Retourne l'uptime formaté."""
        delta = datetime.now() - self._stats["uptime_start"]
        hours = int(delta.total_seconds() / 3600)
        minutes = int((delta.total_seconds() % 3600) / 60)
        return f"{hours}h {minutes}m"
    
    # ============================================================================
    # API PUBLIQUE
    # ============================================================================
    
    async def create_alert(self, title: str, message: str, 
                          severity: AlertSeverity, source: str,
                          metadata: Optional[Dict] = None) -> Alert:
        """Crée une nouvelle alerte."""
        for alert in self._active_alerts:
            if (alert.title == title and alert.source == source and 
                (datetime.now() - alert.timestamp).total_seconds() < self._alert_dedup_window):
                return alert
        
        alert = Alert(
            id=f"ALERT-{datetime.now().strftime('%Y%m%d%H%M%S')}-{random.randint(1000,9999)}",
            title=title, message=message, severity=severity,
            source=source, timestamp=datetime.now(), metadata=metadata or {}
        )
        
        self._active_alerts.append(alert)
        self._alert_history.append(alert)
        self._stats["alerts_generated"] += 1
        
        log_map = {
            AlertSeverity.DEBUG: self._logger.debug, AlertSeverity.INFO: self._logger.info,
            AlertSeverity.WARNING: self._logger.warning, AlertSeverity.CRITICAL: self._logger.error,
            AlertSeverity.EMERGENCY: self._logger.critical
        }
        log_map.get(severity, self._logger.info)(f"🚨 {severity.value.upper()}: {title}")
        
        return alert
    
    async def get_agent_status(self, agent_name: Optional[str] = None) -> Dict:
        """Récupère le statut des agents."""
        if agent_name:
            return self._monitored_agents.get(agent_name, {})
        return {
            "agents": self._monitored_agents,
            "summary": {
                "total": len(self._monitored_agents),
                "online": self._stats["agents_online"],
                "performance_avg": self._stats.get("performance_score", 0)
            }
        }
    
    async def get_dashboard_url(self) -> str:
        """Retourne l'URL du dernier dashboard."""
        return self._dashboards.get("command_center", "")
    
    # ============================================================================
    # GESTION DES MESSAGES
    # ============================================================================
    
    async def _handle_custom_message(self, message: Message) -> Optional[Message]:
        """Gère les messages personnalisés."""
        try:
            handlers = {
                "monitoring.get_dashboard": self._handle_get_dashboard,
                "monitoring.get_agent_status": self._handle_get_agent_status,
                "monitoring.create_alert": self._handle_create_alert,
                "monitoring.ack_alert": self._handle_ack_alert,
            }
            
            if message.message_type in handlers:
                return await handlers[message.message_type](message)
            return None
            
        except Exception as e:
            return Message(
                sender=self.name, recipient=message.sender,
                content={"error": str(e)}, message_type=MessageType.ERROR.value,
                correlation_id=message.message_id
            )
    
    async def _handle_get_dashboard(self, message: Message) -> Message:
        url = await self.get_dashboard_url()
        return Message(sender=self.name, recipient=message.sender,
                      content={"dashboard_url": url}, message_type="monitoring.dashboard_response",
                      correlation_id=message.message_id)
    
    async def _handle_get_agent_status(self, message: Message) -> Message:
        status = await self.get_agent_status(message.content.get("agent_name"))
        return Message(sender=self.name, recipient=message.sender, content=status,
                      message_type="monitoring.agent_status_response", correlation_id=message.message_id)
    
    async def _handle_create_alert(self, message: Message) -> Message:
        content = message.content
        alert = await self.create_alert(
            title=content.get("title", "Alerte"), message=content.get("message", ""),
            severity=AlertSeverity(content.get("severity", "info")),
            source=content.get("source", "external"), metadata=content.get("metadata")
        )
        return Message(sender=self.name, recipient=message.sender,
                      content={"alert_id": alert.id}, message_type="monitoring.alert_created",
                      correlation_id=message.message_id)
    
    async def _handle_ack_alert(self, message: Message) -> Message:
        alert_id = message.content.get("alert_id")
        for alert in self._active_alerts:
            if alert.id == alert_id:
                alert.acknowledged = True
                self._active_alerts.remove(alert)
                return Message(sender=self.name, recipient=message.sender,
                              content={"status": "acknowledged"}, message_type="monitoring.alert_acknowledged",
                              correlation_id=message.message_id)
        return Message(sender=self.name, recipient=message.sender,
                      content={"error": "Alert not found"}, message_type=MessageType.ERROR.value,
                      correlation_id=message.message_id)
    
    # ============================================================================
    # CYCLE DE VIE
    # ============================================================================
    
    async def shutdown(self) -> bool:
        """Arrête l'agent."""
        self._logger.info("Arrêt de l'agent Monitoring...")
        self._set_status(AgentStatus.SHUTTING_DOWN)
        
        for task in [self._collector_task, self._analyzer_task, 
                    self._dashboard_task, self._ai_collector_task]:
            if task and not task.done():
                task.cancel()
                try: await task
                except asyncio.CancelledError: pass
        
        await self.generate_dashboard()
        await super().shutdown()
        self._logger.info("✅ Agent Monitoring arrêté")
        return True
    
    async def pause(self) -> bool:
        self._logger.info("Pause...")
        self._set_status(AgentStatus.PAUSED)
        return True
    
    async def resume(self) -> bool:
        self._logger.info("Reprise...")
        self._set_status(AgentStatus.READY)
        return True
    
    # ============================================================================
    # MÉTRIQUES DE SANTÉ
    # ============================================================================
    
    async def health_check(self) -> Dict[str, Any]:
        base = await super().health_check()
        return {
            **base,
            "agent": self.name, "display_name": self._display_name,
            "status": self._status.value, "ready": self._status == AgentStatus.READY,
            "initialized": self._initialized,
            "monitoring_specific": {
                "agents_monitored": len(self._monitored_agents),
                "agents_online": self._stats["agents_online"],
                "active_alerts": len(self._active_alerts),
                "system_health": self._system_health_score,
                "ai_integrated": self._components["ai_integrator"]["learning_agent_detected"],
                "ai_accuracy": self._ai_metrics["accuracy"]
            },
            "stats": self._stats,
            "timestamp": datetime.now().isoformat()
        }
    
    def get_agent_info(self) -> Dict[str, Any]:
        return {
            "id": self.name, "name": "🎮 Command Center", "display_name": self._display_name,
            "version": "2.0.0", "status": self._status.value,
            "capabilities": [
                "metric_collection", "anomaly_detection", "alerting",
                "dashboard_generation", "trend_analysis", "performance_scoring",
                "system_health", "ai_integration"
            ],
            "features": {
                "terminal_style": True, "grading_system": "S/A/B/C/D",
                "alert_levels": ["debug", "info", "warning", "critical", "emergency"],
                "ai_core": "SUPERLEARNER 2.0",
                "ai_detected": self._components["ai_integrator"]["learning_agent_detected"]
            },
            "monitored_agents": len(self._monitored_agents),
            "active_alerts": len(self._active_alerts)
        }


# ============================================================================
# FONCTION D'USINE
# ============================================================================

def create_monitoring_agent(config_path: Optional[str] = None) -> MonitoringAgent:
    return MonitoringAgent(config_path)